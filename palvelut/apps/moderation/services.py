from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from palvelut.apps.discovery.services import refresh_public_provider_document
from palvelut.apps.moderation.models import AuditEvent
from palvelut.apps.providers.models import Provider
from palvelut.apps.publishing.models import ProfileRevision

ModerationAction = Literal["approve", "request_changes", "suspend"]


@dataclass(frozen=True)
class ModerationResult:
    provider_id: object
    action: ModerationAction
    revision_id: object | None = None


def _require_staff(actor: AbstractBaseUser) -> None:
    if not actor.is_authenticated or not actor.is_staff:
        raise PermissionDenied("Staff access is required for moderation actions")


def _latest_reviewable_revision(provider: Provider) -> ProfileRevision:
    revision = (
        ProfileRevision.objects.select_for_update()
        .filter(
            provider=provider,
            status__in=(ProfileRevision.Status.DRAFT, ProfileRevision.Status.PENDING),
        )
        .order_by("-created_at", "-id")
        .first()
    )
    if revision is None:
        raise ValidationError("Provider has no draft or pending revision to review")
    return revision


@transaction.atomic
def moderate_provider(
    *,
    provider_id: object,
    actor: AbstractBaseUser,
    action: ModerationAction,
) -> ModerationResult:
    _require_staff(actor)
    provider = Provider.objects.select_for_update().get(pk=provider_id)

    if action == "suspend":
        previous = provider.lifecycle
        provider.lifecycle = Provider.Lifecycle.SUSPENDED
        provider.save(update_fields=("lifecycle", "updated_at"))
        refresh_public_provider_document(provider_id=provider.pk)
        AuditEvent.objects.create(
            provider=provider,
            actor=actor,
            action="provider.suspended",
            metadata={"previous_lifecycle": previous},
        )
        return ModerationResult(provider_id=provider.pk, action=action)

    revision = _latest_reviewable_revision(provider)
    now = timezone.now()

    if action == "request_changes":
        revision.status = ProfileRevision.Status.CHANGES_REQUESTED
        revision.reviewed_at = now
        revision.save(update_fields=("status", "reviewed_at"))
        provider.lifecycle = Provider.Lifecycle.CHANGES_REQUESTED
        provider.save(update_fields=("lifecycle", "updated_at"))
        AuditEvent.objects.create(
            provider=provider,
            actor=actor,
            action="provider.changes_requested",
            metadata={"revision_id": str(revision.pk)},
        )
        return ModerationResult(
            provider_id=provider.pk,
            action=action,
            revision_id=revision.pk,
        )

    if action != "approve":
        raise ValidationError(f"Unsupported moderation action: {action}")
    if provider.claim_status != Provider.ClaimStatus.APPROVED:
        raise ValidationError("Only an approved claim can be published")

    ProfileRevision.objects.filter(
        provider=provider,
        status=ProfileRevision.Status.APPROVED,
    ).exclude(pk=revision.pk).update(status=ProfileRevision.Status.SUPERSEDED)
    revision.status = ProfileRevision.Status.APPROVED
    revision.reviewed_at = now
    revision.save(update_fields=("status", "reviewed_at"))
    provider.lifecycle = Provider.Lifecycle.PUBLISHED
    provider.save(update_fields=("lifecycle", "updated_at"))
    refresh_public_provider_document(provider_id=provider.pk)
    AuditEvent.objects.create(
        provider=provider,
        actor=actor,
        action="provider.approved",
        metadata={"revision_id": str(revision.pk)},
    )
    return ModerationResult(
        provider_id=provider.pk,
        action=action,
        revision_id=revision.pk,
    )
