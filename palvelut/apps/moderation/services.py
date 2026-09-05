from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from typing import Literal

from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from palvelut.apps.discovery.services import (
    rebuild_provider_read_document,
    remove_provider_read_document,
)
from palvelut.apps.moderation.models import (
    AuditEvent,
    ContentReport,
    ModerationCase,
    ModerationEvent,
)
from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.publishing.models import ProfileRevision
from palvelut.apps.publishing.services import ensure_provider_slug

ModerationAction = Literal["approve", "request_changes", "suspend"]
CaseAction = Literal["notice", "resolve", "dismiss"]


@dataclass(frozen=True)
class ModerationResult:
    provider_id: object
    action: ModerationAction
    revision_id: object | None = None


@dataclass(frozen=True)
class ContentReportReceipt:
    case_id: object
    status_token: str


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


def _hash_status_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@transaction.atomic
def submit_content_report(
    *,
    provider_id: object,
    category: str,
    details: str,
) -> ContentReportReceipt:
    """Create an anonymous content-report case without storing reporter identity."""

    category = category.strip().lower()
    details = details.strip()
    if not category or len(category) > 40:
        raise ValidationError("A valid report category is required")
    if not details or len(details) > 2000:
        raise ValidationError("Report details must contain 1-2000 characters")

    provider = Provider.objects.get(pk=provider_id)
    status_token = secrets.token_urlsafe(24)
    case = ModerationCase.objects.create(
        provider=provider,
        kind=ModerationCase.Kind.CONTENT_REPORT,
        reason=category,
        opened_by=None,
        status_token_hash=_hash_status_token(status_token),
    )
    ContentReport.objects.create(case=case, category=category, details=details)
    ModerationEvent.objects.create(
        case=case,
        event_type="report.received",
        actor=None,
        metadata={"category": category},
        visible_to_provider=False,
    )
    return ContentReportReceipt(case_id=case.pk, status_token=status_token)


def content_report_status(*, case_id: object, status_token: str) -> ModerationCase:
    case = ModerationCase.objects.prefetch_related("events").get(
        pk=case_id,
        kind=ModerationCase.Kind.CONTENT_REPORT,
    )
    if not secrets.compare_digest(
        case.status_token_hash,
        _hash_status_token(status_token),
    ):
        raise PermissionDenied("Invalid report status token")
    return case


def _require_provider_member(*, provider: Provider, actor: AbstractBaseUser) -> None:
    if not actor.is_authenticated:
        raise PermissionDenied("Provider access is required")
    if not ProviderMembership.objects.filter(
        provider=provider,
        account=actor,
        is_active=True,
    ).exists():
        raise PermissionDenied("Provider access is required")


@transaction.atomic
def staff_update_content_case(
    *,
    case_id: object,
    actor: AbstractBaseUser,
    action: CaseAction,
    note: str,
) -> ModerationCase:
    _require_staff(actor)
    case = ModerationCase.objects.select_for_update().get(
        pk=case_id,
        kind=ModerationCase.Kind.CONTENT_REPORT,
    )
    note = note.strip()
    if not note:
        raise ValidationError("A moderation note is required")

    if action == "notice":
        event_type = "provider.notice"
    elif action in {"resolve", "dismiss"}:
        case.status = (
            ModerationCase.Status.RESOLVED
            if action == "resolve"
            else ModerationCase.Status.DISMISSED
        )
        case.closed_at = timezone.now()
        case.save(update_fields=("status", "closed_at"))
        event_type = f"case.{action}d" if action == "resolve" else "case.dismissed"
    else:
        raise ValidationError(f"Unsupported case action: {action}")

    ModerationEvent.objects.create(
        case=case,
        event_type=event_type,
        actor=actor,
        note=note,
        visible_to_provider=True,
    )
    AuditEvent.objects.create(
        provider=case.provider,
        actor=actor,
        action=f"content_report.{action}",
        metadata={"case_id": str(case.pk)},
    )
    return case


@transaction.atomic
def appeal_content_case(
    *,
    case_id: object,
    actor: AbstractBaseUser,
    note: str,
) -> ModerationEvent:
    case = ModerationCase.objects.select_related("provider").get(
        pk=case_id,
        kind=ModerationCase.Kind.CONTENT_REPORT,
    )
    _require_provider_member(provider=case.provider, actor=actor)
    note = note.strip()
    if not note:
        raise ValidationError("An appeal note is required")
    return ModerationEvent.objects.create(
        case=case,
        event_type="provider.appeal",
        actor=actor,
        note=note,
        visible_to_provider=True,
    )


def provider_case_timeline(
    *,
    case_id: object,
    actor: AbstractBaseUser,
) -> tuple[ModerationCase, list[ModerationEvent]]:
    case = ModerationCase.objects.select_related("provider").get(
        pk=case_id,
        kind=ModerationCase.Kind.CONTENT_REPORT,
    )
    _require_provider_member(provider=case.provider, actor=actor)
    events = list(case.events.filter(visible_to_provider=True).select_related("actor"))
    return case, events


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
        remove_provider_read_document(provider_id=provider.pk)
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
    ensure_provider_slug(provider_id=provider.pk)
    rebuild_provider_read_document(provider_id=provider.pk)
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
