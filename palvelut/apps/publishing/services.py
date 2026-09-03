from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.models import Provider
from palvelut.apps.verification.models import ProviderClaim

from .models import ProfileRevision


def _has_approved_claim(provider: Provider) -> bool:
    return ProviderClaim.objects.filter(
        provider=provider,
        status=ProviderClaim.Status.APPROVED,
    ).exists()


@transaction.atomic
def approve_revision(*, revision: ProfileRevision, actor) -> ProfileRevision:  # type: ignore[no-untyped-def]
    revision = ProfileRevision.objects.select_for_update().select_related("provider").get(pk=revision.pk)
    provider = Provider.objects.select_for_update().get(pk=revision.provider_id)
    if not _has_approved_claim(provider):
        raise ValidationError("Provider requires an approved claim before publishing.")

    ProfileRevision.objects.filter(
        provider=provider,
        status=ProfileRevision.Status.APPROVED,
    ).exclude(pk=revision.pk).update(status=ProfileRevision.Status.SUPERSEDED)

    revision.status = ProfileRevision.Status.APPROVED
    revision.reviewed_at = timezone.now()
    revision.save(update_fields=("status", "reviewed_at"))
    provider.lifecycle = Provider.Lifecycle.PUBLISHED
    provider.save(update_fields=("lifecycle", "updated_at"))
    AuditEvent.objects.create(
        provider=provider,
        actor=actor,
        action="provider.revision.approved",
        metadata={"revision_id": str(revision.pk)},
    )
    return revision


@transaction.atomic
def request_revision_changes(*, revision: ProfileRevision, actor) -> ProfileRevision:  # type: ignore[no-untyped-def]
    revision = ProfileRevision.objects.select_for_update().select_related("provider").get(pk=revision.pk)
    revision.status = ProfileRevision.Status.CHANGES_REQUESTED
    revision.reviewed_at = timezone.now()
    revision.save(update_fields=("status", "reviewed_at"))
    if revision.provider.lifecycle == Provider.Lifecycle.PENDING:
        revision.provider.lifecycle = Provider.Lifecycle.CHANGES_REQUESTED
        revision.provider.save(update_fields=("lifecycle", "updated_at"))
    AuditEvent.objects.create(
        provider=revision.provider,
        actor=actor,
        action="provider.revision.changes_requested",
        metadata={"revision_id": str(revision.pk)},
    )
    return revision


@transaction.atomic
def suspend_provider(*, provider: Provider, actor) -> Provider:  # type: ignore[no-untyped-def]
    provider = Provider.objects.select_for_update().get(pk=provider.pk)
    provider.lifecycle = Provider.Lifecycle.SUSPENDED
    provider.save(update_fields=("lifecycle", "updated_at"))
    AuditEvent.objects.create(
        provider=provider,
        actor=actor,
        action="provider.suspended",
    )
    return provider


@transaction.atomic
def merge_duplicate(*, source: Provider, target: Provider, actor) -> Provider:  # type: ignore[no-untyped-def]
    if source.pk == target.pk:
        raise ValidationError("Duplicate source and target must differ.")
    source = Provider.objects.select_for_update().get(pk=source.pk)
    target = Provider.objects.select_for_update().get(pk=target.pk)
    source.lifecycle = Provider.Lifecycle.ARCHIVED
    source.save(update_fields=("lifecycle", "updated_at"))
    AuditEvent.objects.create(
        provider=source,
        actor=actor,
        action="provider.duplicate.merged",
        metadata={"target_provider_id": str(target.pk)},
    )
    return source
