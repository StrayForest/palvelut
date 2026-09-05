from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from .models import DataSubjectRequest, DataSubjectRequestEvent


@transaction.atomic
def create_data_subject_request(*, account, kind: str, note: str = "") -> DataSubjectRequest:
    if kind not in DataSubjectRequest.Kind.values:
        raise ValidationError("Unsupported data request type")
    request = DataSubjectRequest.objects.create(
        account=account,
        kind=kind,
        request_note=note,
    )
    DataSubjectRequestEvent.objects.create(
        request=request,
        actor=account,
        action="requested",
        note=note,
    )
    return request


@transaction.atomic
def update_data_subject_request(
    *,
    request_id,
    actor,
    action: str,
    note: str,
) -> DataSubjectRequest:
    if not actor.is_staff:
        raise PermissionDenied

    request = DataSubjectRequest.objects.select_for_update().get(pk=request_id)
    if request.status not in {
        DataSubjectRequest.Status.OPEN,
        DataSubjectRequest.Status.IN_PROGRESS,
    }:
        raise ValidationError("This data request is already closed")

    if action == "start":
        if request.status != DataSubjectRequest.Status.OPEN:
            raise ValidationError("Only open requests can be started")
        request.status = DataSubjectRequest.Status.IN_PROGRESS
        event_action = "processing_started"
    elif action == "complete":
        request.status = DataSubjectRequest.Status.COMPLETED
        request.completed_at = timezone.now()
        event_action = "completed"
    elif action == "reject":
        request.status = DataSubjectRequest.Status.REJECTED
        request.completed_at = timezone.now()
        event_action = "rejected"
    else:
        raise ValidationError("Unsupported data request action")

    request.staff_note = note
    request.save(update_fields=("status", "staff_note", "completed_at", "updated_at"))
    DataSubjectRequestEvent.objects.create(
        request=request,
        actor=actor,
        action=event_action,
        note=note,
    )
    return request
