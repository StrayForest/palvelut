from django.db import transaction
from django.utils import timezone

from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.models import Provider, ProviderMembership

from .models import ProviderClaim


@transaction.atomic
def approve_claim(
    *,
    claim: ProviderClaim,
    actor,
) -> ProviderClaim:  # type: ignore[no-untyped-def]
    claim = ProviderClaim.objects.select_for_update().select_related("provider", "claimed_by").get(pk=claim.pk)
    provider = Provider.objects.select_for_update().get(pk=claim.provider_id)

    ProviderClaim.objects.filter(
        provider=provider,
        status=ProviderClaim.Status.APPROVED,
    ).exclude(pk=claim.pk).update(
        status=ProviderClaim.Status.REJECTED,
        reviewed_by=actor,
        reviewed_at=timezone.now(),
    )

    claim.status = ProviderClaim.Status.APPROVED
    claim.reviewed_by = actor
    claim.reviewed_at = timezone.now()
    claim.save(update_fields=("status", "reviewed_by", "reviewed_at"))

    ProviderMembership.objects.update_or_create(
        provider=provider,
        account=claim.claimed_by,
        defaults={"role": ProviderMembership.Role.OWNER, "is_active": True},
    )
    if provider.lifecycle == Provider.Lifecycle.UNCLAIMED:
        provider.lifecycle = Provider.Lifecycle.DRAFT
        provider.save(update_fields=("lifecycle", "updated_at"))

    AuditEvent.objects.create(
        provider=provider,
        actor=actor,
        action="provider.claim.approved",
        metadata={"claim_id": str(claim.pk), "account_id": claim.claimed_by_id},
    )
    return claim


@transaction.atomic
def reject_claim(
    *,
    claim: ProviderClaim,
    actor,
) -> ProviderClaim:  # type: ignore[no-untyped-def]
    claim = ProviderClaim.objects.select_for_update().select_related("provider").get(pk=claim.pk)
    claim.status = ProviderClaim.Status.REJECTED
    claim.reviewed_by = actor
    claim.reviewed_at = timezone.now()
    claim.save(update_fields=("status", "reviewed_by", "reviewed_at"))
    AuditEvent.objects.create(
        provider=claim.provider,
        actor=actor,
        action="provider.claim.rejected",
        metadata={"claim_id": str(claim.pk)},
    )
    return claim
