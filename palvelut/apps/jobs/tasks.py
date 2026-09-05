from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from typing import Any

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from palvelut.apps.analytics.tasks import purge_expired_analytics
from palvelut.observability import increment_metric, set_metric

from .models import OutboxJob
from .services import enqueue_job

MAX_ATTEMPTS = 5
LOCK_TIMEOUT = timedelta(minutes=15)
OUTBOX_RETENTION_DAYS = 30
MAX_BATCH_SIZE = 200

JobHandler = Callable[[dict[str, Any]], object]


def _handle_analytics_retention(payload: dict[str, Any]) -> int:
    del payload
    return purge_expired_analytics.run()


def _handle_outbox_retention(payload: dict[str, Any]) -> int:
    del payload
    cutoff = timezone.now() - timedelta(days=OUTBOX_RETENTION_DAYS)
    deleted, _ = OutboxJob.objects.filter(
        status__in=(OutboxJob.Status.COMPLETED, OutboxJob.Status.DEAD),
        updated_at__lt=cutoff,
    ).delete()
    return deleted


HANDLERS: dict[str, JobHandler] = {
    "analytics.purge_expired": _handle_analytics_retention,
    "jobs.purge_history": _handle_outbox_retention,
}


def _record_queue_age() -> None:
    oldest = (
        OutboxJob.objects.filter(status=OutboxJob.Status.PENDING)
        .order_by("created_at")
        .values_list("created_at", flat=True)
        .first()
    )
    age = 0.0 if oldest is None else max(0.0, (timezone.now() - oldest).total_seconds())
    set_metric("palvelut_queue_oldest_age_seconds", age)


def _claim_jobs(batch_size: int) -> list[object]:
    now = timezone.now()
    stale_before = now - LOCK_TIMEOUT
    with transaction.atomic():
        OutboxJob.objects.filter(
            status=OutboxJob.Status.PROCESSING,
            locked_at__lt=stale_before,
        ).update(
            status=OutboxJob.Status.PENDING,
            locked_at=None,
            available_at=now,
        )
        jobs = list(
            OutboxJob.objects.select_for_update(skip_locked=True)
            .filter(
                status=OutboxJob.Status.PENDING,
                available_at__lte=now,
            )
            .order_by("created_at")[:batch_size]
        )
        job_ids = [job.pk for job in jobs]
        if job_ids:
            OutboxJob.objects.filter(pk__in=job_ids).update(
                status=OutboxJob.Status.PROCESSING,
                locked_at=now,
            )
        return job_ids


def _execute_job(job_id: object) -> bool:
    job = OutboxJob.objects.get(pk=job_id)
    handler = HANDLERS.get(job.kind)
    try:
        if handler is None:
            raise LookupError(f"unknown outbox job kind: {job.kind}")
        handler(job.payload)
    except Exception as exc:
        increment_metric("palvelut_queue_failures_total")
        now = timezone.now()
        with transaction.atomic():
            locked_job = OutboxJob.objects.select_for_update().get(pk=job_id)
            attempts = locked_job.attempts + 1
            locked_job.attempts = attempts
            locked_job.locked_at = None
            locked_job.last_error = f"{type(exc).__name__}: {exc}"[:500]
            if attempts >= MAX_ATTEMPTS:
                locked_job.status = OutboxJob.Status.DEAD
                locked_job.available_at = now
            else:
                locked_job.status = OutboxJob.Status.PENDING
                delay_seconds = min(3600, (2**attempts) * 60)
                locked_job.available_at = now + timedelta(seconds=delay_seconds)
            locked_job.save(
                update_fields=(
                    "attempts",
                    "locked_at",
                    "last_error",
                    "status",
                    "available_at",
                    "updated_at",
                )
            )
        return False

    now = timezone.now()
    with transaction.atomic():
        locked_job = OutboxJob.objects.select_for_update().get(pk=job_id)
        locked_job.status = OutboxJob.Status.COMPLETED
        locked_job.attempts += 1
        locked_job.locked_at = None
        locked_job.completed_at = now
        locked_job.last_error = ""
        locked_job.save(
            update_fields=(
                "status",
                "attempts",
                "locked_at",
                "completed_at",
                "last_error",
                "updated_at",
            )
        )
    return True


@shared_task(name="palvelut.jobs.dispatch_outbox")
def dispatch_outbox(batch_size: int = 50) -> dict[str, int]:
    bounded_batch_size = max(1, min(batch_size, MAX_BATCH_SIZE))
    job_ids = _claim_jobs(bounded_batch_size)
    completed = sum(1 for job_id in job_ids if _execute_job(job_id))
    _record_queue_age()
    return {"claimed": len(job_ids), "completed": completed}


@shared_task(name="palvelut.jobs.enqueue_daily_maintenance")
def enqueue_daily_maintenance() -> int:
    day = timezone.localdate().isoformat()
    created = 0
    for kind, prefix in (
        ("analytics.purge_expired", "analytics-retention"),
        ("jobs.purge_history", "outbox-retention"),
    ):
        _job, was_created = enqueue_job(
            kind=kind,
            dedupe_key=f"{prefix}:{day}",
        )
        created += int(was_created)
    return created
