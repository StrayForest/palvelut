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
    ModerationAppeal,
    ModerationCase,
    ModerationEvent,
    ProviderNotice,
)
from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.publishing.models import ProfileRevision
from palvelut.apps.publishing.services import ensure_provider_slug

ModerationAction = Literal["approve", "request_changes", "suspend"]
CaseAction = Literal["resolve", "dismiss"]


@dataclass(frozen=True)
class ModerationResult:
    provider_id: object
    action: ModerationAction
    revision_id: object | None = None


def _require_staff(actor: AbstractBaseUser) -> None:
    if not actor.is_authenticated or not actor.is_staff:
        raise PermissionDenied("Staff access is required for moderation actions")


def _require_provider_member(*, actor: AbstractBaseUser, provider: Provider) -> None:
    if not actor.is_authenticated:
        raise PermissionDenied("Provider access is required")
    if not ProviderMembership.objects.filter(
        provider=provider,
        account=actor,
        is_active=True,
    ).exists():
        raise PermissionDenied("Provider access is required")


def _hash_public_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@transaction.atomic
def create_anonymous_report(
    *,
    provider: Provider,
    reason: str,
    details: str,
) -> tuple[ContentReport, str]:
    clean_reason = reason.strip()[:120]
    clean_details = details.strip()[:2000]
    if not clean_reason or not clean_details:
        raise ValidationError("Reason and details are required")
    token = secrets.token_urlsafe(32)
    case = ModerationCase.objects.create(
        provider=provider,
        reason=clean_reason,
        opened_by=None,
    )
    report = ContentReport.objects.create(
        case=case,
        public_token_hash=_hash_public_token(token),
        details=clean_details,
    )
    ModerationEvent.objects.create(
        case=case,
        event_type="report.received",
        actor=None,
        metadata={"source": "anonymous"},
    )
    return report, token


def get_public_report_case(*, token: str) -> ModerationCase:
    return ContentReport.objects.select_related("case", "case__provider").get(
        public_token_hash=_hash_public_token(token)
    ).case


@transaction.atomic
def staff_update_case(
    *,
    case_id: object,
    actor: AbstractBaseUser,
    action: CaseAction,
    note: str = "",
) -> ModerationCase:
    _require_staff(actor)
    case = ModerationCase.objects.select_for_update().get(pk=case_id)
    if action not in ("resolve", "dismiss"):
        raise ValidationError("Unsupported case action")
    case.status = (
        ModerationCase.Status.RESOLVED
        if action == "resolve"
        else ModerationCase.Status.DISMISSED
    )
    case.closed_at = timezone.now()
    case.save(update_fields=("status", "closed_at"))
    ModerationEvent.objects.create(
        case=case,
        event_type=f"case.{case.status}",
        actor=actor,
        note=note.strip()[:4000],
    )
    AuditEvent.objects.create(
        provider=case.provider,
        actor=actor,
        action=f"moderation_case.{case.status}",
        metadata={"case_id": str(case.pk)},
    )
    return case


@transaction.atomic
def create_provider_notice(
    *,
    case_id: object,
    actor: AbstractBaseUser,
    message: str,
) -> ProviderNotice:
    _require_staff(actor)
    case = ModerationCase.objects.select_for_update().get(pk=case_id)
    clean_message = message.strip()[:4000]
    if not clean_message:
        raise ValidationError("Notice message is required")
    notice = ProviderNotice.objects.create(
        case=case,
        created_by=actor,
        message=clean_message,
    )
    ModerationEvent.objects.create(
        case=case,
        event_type="provider.notice_sent",
        actor=actor,
        metadata={"notice_id": str(notice.pk)},
    )
    return notice


@transaction.atomic
def submit_appeal(
    *,
    case_id: object,
    actor: AbstractBaseUser,
    message: str,
) -> ModerationAppeal:
    case = (
        ModerationCase.objects.select_for_update()
        .select_related("provider")
        .get(pk=case_id)
    )
    _require_provider_member(actor=actor, provider=case.provider)
    clean_message = message.strip()[:4000]
    if not clean_message:
        raise ValidationError("Appeal message is required")
    if case.appeals.filter(status=ModerationAppeal.Status.PENDING).exists():
        raise ValidationError("A pending appeal already exists")
    appeal = ModerationAppeal.objects.create(
        case=case,
        submitted_by=actor,
        message=clean_message,
    )
    ModerationEvent.objects.create(
        case=case,
        event_type="provider.appeal_submitted",
        actor=actor,
        metadata={"appeal_id": str(appeal.pk)},
    )
    return appeal


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
