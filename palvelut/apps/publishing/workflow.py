from __future__ import annotations

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision

PROFILE_FIELDS = ("provider_type", "legal_name", "display_name", "y_tunnus")


def _require_staff(actor) -> None:
    if not actor.is_staff:
        raise PermissionDenied("staff required")


@transaction.atomic
def request_revision_changes(
    *, revision_id: object, actor, note: str
) -> ProfileRevision:
    _require_staff(actor)
    revision = (
        ProfileRevision.objects.select_for_update()
        .select_related("provider")
        .get(pk=revision_id)
    )
    if revision.status != ProfileRevision.Status.PENDING:
        raise ValidationError("only pending revisions can request changes")
    revision.status = ProfileRevision.Status.CHANGES_REQUESTED
    revision.reviewed_at = timezone.now()
    revision.save(update_fields=("status", "reviewed_at"))
    if revision.provider.lifecycle != Provider.Lifecycle.PUBLISHED:
        revision.provider.lifecycle = Provider.Lifecycle.CHANGES_REQUESTED
        revision.provider.save(update_fields=("lifecycle", "updated_at"))
    AuditEvent.objects.create(
        provider=revision.provider,
        actor=actor,
        action="provider_revision_changes_requested",
        metadata={"revision_id": str(revision.pk), "note": note.strip()},
    )
    return revision


@transaction.atomic
def approve_revision(*, revision_id: object, actor) -> ProfileRevision:
    _require_staff(actor)
    revision = (
        ProfileRevision.objects.select_for_update()
        .select_related("provider")
        .get(pk=revision_id)
    )
    if revision.status != ProfileRevision.Status.PENDING:
        raise ValidationError("only pending revisions can be approved")
    provider = Provider.objects.select_for_update().get(pk=revision.provider_id)
    if provider.claim_status != Provider.ClaimStatus.APPROVED:
        raise ValidationError("provider claim must be approved before publication")
    for field in PROFILE_FIELDS:
        if field in revision.payload:
            setattr(provider, field, revision.payload[field])
    provider.lifecycle = Provider.Lifecycle.PUBLISHED
    provider.save(update_fields=(*PROFILE_FIELDS, "lifecycle", "updated_at"))
    (
        ProfileRevision.objects.filter(
            provider=provider,
            status=ProfileRevision.Status.APPROVED,
        )
        .exclude(pk=revision.pk)
        .update(status=ProfileRevision.Status.SUPERSEDED)
    )
    revision.status = ProfileRevision.Status.APPROVED
    revision.reviewed_at = timezone.now()
    revision.save(update_fields=("status", "reviewed_at"))
    AuditEvent.objects.create(
        provider=provider,
        actor=actor,
        action="provider_revision_approved",
        metadata={"revision_id": str(revision.pk)},
    )
    return revision
