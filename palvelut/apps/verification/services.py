from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from palvelut.apps.moderation.services import record_audit
from palvelut.apps.providers.models import Provider
from palvelut.apps.providers.services import (
    activate_owner_membership,
    set_provider_lifecycle,
)
from palvelut.apps.verification.models import ProviderClaim


@transaction.atomic
def approve_claim(*, claim: ProviderClaim, actor: AbstractBaseUser) -> ProviderClaim:
    claim = (
        ProviderClaim.objects.select_for_update()
        .select_related("provider", "claimant")
        .get(pk=claim.pk)
    )
    if claim.status != ProviderClaim.Status.PENDING:
        raise ValidationError("Only pending claims can be approved")
    if claim.provider.lifecycle != Provider.Lifecycle.UNCLAIMED:
        raise ValidationError("Only unclaimed providers need a claim transition")
    if not claim.evidence_metadata:
        raise ValidationError("Claim evidence metadata is required")

    activate_owner_membership(provider=claim.provider, account=claim.claimant)

    claim.status = ProviderClaim.Status.APPROVED
    claim.reviewed_by = actor
    claim.reviewed_at = timezone.now()
    claim.save(update_fields=("status", "reviewed_by", "reviewed_at"))

    provider, _ = set_provider_lifecycle(
        provider=claim.provider, lifecycle=Provider.Lifecycle.DRAFT
    )
    record_audit(
        actor=actor,
        provider=provider,
        action="claim.approved",
        metadata={
            "claim_id": str(claim.pk),
            "claimant_id": str(claim.claimant_id),
            "evidence_type": claim.evidence_type,
        },
    )
    return claim


@transaction.atomic
def reject_claim(*, claim: ProviderClaim, actor: AbstractBaseUser) -> ProviderClaim:
    claim = (
        ProviderClaim.objects.select_for_update()
        .select_related("provider")
        .get(pk=claim.pk)
    )
    if claim.status != ProviderClaim.Status.PENDING:
        raise ValidationError("Only pending claims can be rejected")

    claim.status = ProviderClaim.Status.REJECTED
    claim.reviewed_by = actor
    claim.reviewed_at = timezone.now()
    claim.save(update_fields=("status", "reviewed_by", "reviewed_at"))
    record_audit(
        actor=actor,
        provider=claim.provider,
        action="claim.rejected",
        metadata={"claim_id": str(claim.pk), "evidence_type": claim.evidence_type},
    )
    return claim
