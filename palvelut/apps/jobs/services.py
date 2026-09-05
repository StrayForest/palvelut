from __future__ import annotations

from datetime import datetime
from typing import Any

from django.db import transaction
from django.utils import timezone

from .models import OutboxJob


@transaction.atomic
def enqueue_job(
    *,
    kind: str,
    dedupe_key: str,
    payload: dict[str, Any] | None = None,
    available_at: datetime | None = None,
) -> tuple[OutboxJob, bool]:
    """Persist one durable job per dedupe key inside the caller transaction."""
    normalized_payload = payload or {}
    job, created = OutboxJob.objects.get_or_create(
        dedupe_key=dedupe_key,
        defaults={
            "kind": kind,
            "payload": normalized_payload,
            "available_at": available_at or timezone.now(),
        },
    )
    if not created and (job.kind != kind or job.payload != normalized_payload):
        raise ValueError("dedupe key already belongs to a different outbox job")
    return job, created
