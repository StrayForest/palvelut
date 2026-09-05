from __future__ import annotations

from datetime import datetime

from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Exists, OuterRef, QuerySet
from django.utils import timezone

from palvelut.apps.providers.models import Provider

from .adapters import RegistryOutcome, YtjPrhAdapter
from .models import VerificationCheck, VerificationEvent
from .registry import get_registry_check_type


def _require_staff(actor: AbstractBaseUser) -> None:
    if not actor.is_authenticated or not actor.is_staff:
        raise PermissionDenied("Staff access is required for verification changes")


def recheck_expiry_queue(
    *, at: datetime | None = None
) -> QuerySet[VerificationCheck]:
    """Return expired latest verified facts that require a fresh registry check."""

    now = at or timezone.now()
    newer_check = VerificationCheck.objects.filter(
        provider_id=OuterRef("provider_id"),
        kind=OuterRef("kind"),
        checked_at__gt=OuterRef("checked_at"),
    )
    return (
        VerificationCheck.objects.filter(
            status=VerificationCheck.Status.VERIFIED,
            expires_at__isnull=False,
            expires_at__lte=now,
        )
        .annotate(has_newer_check=Exists(newer_check))
        .filter(has_newer_check=False)
        .select_related("provider")
        .order_by("expires_at", "checked_at", "id")
    )


@transaction.atomic
def change_verification_status(
    *,
    check_id: object,
    actor: AbstractBaseUser,
    status: str,
    metadata: dict[str, object] | None = None,
) -> VerificationCheck:
    _require_staff(actor)
    if status not in VerificationCheck.Status.values:
        raise ValidationError(f"Unsupported verification status: {status}")

    check = VerificationCheck.objects.select_for_update().get(pk=check_id)
    check.status = status
    check.save(update_fields=("status",))
    VerificationEvent.objects.create(
        verification_check=check,
        status=status,
        actor=actor,
        metadata=metadata or {},
    )
    return check


@transaction.atomic
def run_registry_check(
    *,
    provider_id: object,
    actor: AbstractBaseUser,
    kind: str,
    adapter: object | None = None,
) -> VerificationCheck:
    """Run one enabled official-source check without mutating older facts."""

    _require_staff(actor)
    definition = get_registry_check_type(kind)
    provider = Provider.objects.select_for_update().get(pk=provider_id)
    subject = getattr(provider, definition.subject_field, None)
    if not subject:
        raise ValidationError(
            f"Provider must have {definition.subject_field} before a {kind} check"
        )

    adapter_instance = adapter
    if adapter_instance is None:
        if definition.adapter_factory is None:  # guarded by registry validation
            raise RuntimeError(f"Verification kind {kind!r} has no adapter factory")
        adapter_instance = definition.adapter_factory()

    lookup = getattr(adapter_instance, definition.lookup_method, None)
    if not callable(lookup):
        raise ValidationError(
            f"Adapter for verification kind {kind!r} does not implement "
            f"{definition.lookup_method}"
        )
    result = lookup(subject)

    if result.outcome == RegistryOutcome.FOUND:
        status = VerificationCheck.Status.VERIFIED
    elif result.outcome == RegistryOutcome.NOT_FOUND:
        status = VerificationCheck.Status.REJECTED
    else:
        status = VerificationCheck.Status.PENDING

    metadata = result.evidence_metadata()
    metadata["verification_kind"] = definition.kind
    metadata["registry_source"] = definition.source_name
    check = VerificationCheck.objects.create(
        provider=provider,
        kind=definition.kind,
        status=status,
        source_url=result.source_url,
        evidence_metadata=metadata,
        checked_by=actor,
    )
    VerificationEvent.objects.create(
        verification_check=check,
        status=status,
        actor=actor,
        metadata={
            "adapter_outcome": result.outcome.value,
            "manual_fallback_required": result.outcome == RegistryOutcome.MANUAL_REVIEW,
            "attempts": result.attempts,
            "verification_kind": definition.kind,
            "registry_source": definition.source_name,
        },
    )
    return check


def run_ytj_business_identity_check(
    *,
    provider_id: object,
    actor: AbstractBaseUser,
    adapter: YtjPrhAdapter | None = None,
) -> VerificationCheck:
    """Backward-compatible entry point for the enabled PRH/YTJ check."""

    return run_registry_check(
        provider_id=provider_id,
        actor=actor,
        kind="business_identity",
        adapter=adapter,
    )
