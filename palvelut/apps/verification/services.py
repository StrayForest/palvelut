from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from palvelut.apps.providers.models import Provider

from .adapters import RegistryOutcome, YtjPrhAdapter
from .models import VerificationCheck, VerificationEvent


def _require_staff(actor: AbstractBaseUser) -> None:
    if not actor.is_authenticated or not actor.is_staff:
        raise PermissionDenied("Staff access is required for verification changes")


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
def run_ytj_business_identity_check(
    *,
    provider_id: object,
    actor: AbstractBaseUser,
    adapter: YtjPrhAdapter | None = None,
) -> VerificationCheck:
    """Record one immutable-source PRH/YTJ lookup without overwriting prior facts."""

    _require_staff(actor)
    provider = Provider.objects.select_for_update().get(pk=provider_id)
    if not provider.y_tunnus:
        raise ValidationError("Provider must have a Y-tunnus before a YTJ check")

    result = (adapter or YtjPrhAdapter()).lookup_business_id(provider.y_tunnus)
    if result.outcome == RegistryOutcome.FOUND:
        status = VerificationCheck.Status.VERIFIED
    elif result.outcome == RegistryOutcome.NOT_FOUND:
        status = VerificationCheck.Status.REJECTED
    else:
        status = VerificationCheck.Status.PENDING

    metadata = result.evidence_metadata()
    check = VerificationCheck.objects.create(
        provider=provider,
        kind="business_identity",
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
        },
    )
    return check
