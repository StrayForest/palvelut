from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from palvelut.apps.verification.models import VerificationCheck, VerificationEvent


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
    valid_statuses = {value for value, _label in VerificationCheck.Status.choices}
    if status not in valid_statuses:
        raise ValidationError(f"Unsupported verification status: {status}")

    check = VerificationCheck.objects.select_for_update().get(pk=check_id)
    previous_status = check.status
    if previous_status == status:
        return check

    check.status = status
    check.save(update_fields=("status",))
    VerificationEvent.objects.create(
        check=check,
        actor=actor,
        previous_status=previous_status,
        status=status,
        metadata=metadata or {},
    )
    return check
