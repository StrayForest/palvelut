from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

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
