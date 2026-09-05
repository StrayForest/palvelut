from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from palvelut.apps.jobs.models import OutboxJob
from palvelut.apps.jobs.services import enqueue_job
from palvelut.apps.jobs.tasks import (
    MAX_ATTEMPTS,
    _claim_jobs,
    _execute_job,
    _handle_outbox_retention,
    dispatch_outbox,
    enqueue_daily_maintenance,
)


class OutboxJobTests(TestCase):
    def test_enqueue_is_idempotent_by_dedupe_key(self) -> None:
        first, first_created = enqueue_job(
            kind="test.noop",
            dedupe_key="same-key",
            payload={"value": 1},
        )
        second, second_created = enqueue_job(
            kind="test.noop",
            dedupe_key="same-key",
            payload={"value": 1},
        )

        self.assertTrue(first_created)
        self.assertFalse(second_created)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(OutboxJob.objects.count(), 1)

    def test_dedupe_key_rejects_conflicting_job(self) -> None:
        enqueue_job(kind="test.noop", dedupe_key="same-key", payload={"value": 1})

        with self.assertRaises(ValueError):
            enqueue_job(
                kind="test.noop",
                dedupe_key="same-key",
                payload={"value": 2},
            )

    def test_dispatch_completes_job_once(self) -> None:
        job, _created = enqueue_job(kind="test.noop", dedupe_key="complete-once")
        calls: list[dict[str, object]] = []

        with patch.dict(
            "palvelut.apps.jobs.tasks.HANDLERS",
            {"test.noop": lambda payload: calls.append(payload)},
            clear=False,
        ):
            first = dispatch_outbox.run()
            second = dispatch_outbox.run()

        job.refresh_from_db()
        self.assertEqual(first, {"claimed": 1, "completed": 1})
        self.assertEqual(second, {"claimed": 0, "completed": 0})
        self.assertEqual(job.status, OutboxJob.Status.COMPLETED)
        self.assertEqual(job.attempts, 1)
        self.assertEqual(calls, [{}])

    def test_failure_retries_then_dead_letters(self) -> None:
        job, _created = enqueue_job(kind="missing.handler", dedupe_key="dead-letter")

        for attempt in range(MAX_ATTEMPTS):
            job.status = OutboxJob.Status.PROCESSING
            job.locked_at = timezone.now()
            job.available_at = timezone.now()
            job.save(
                update_fields=(
                    "status",
                    "locked_at",
                    "available_at",
                    "updated_at",
                )
            )
            self.assertFalse(_execute_job(job.pk))
            job.refresh_from_db()
            self.assertEqual(job.attempts, attempt + 1)

        self.assertEqual(job.status, OutboxJob.Status.DEAD)
        self.assertIn("unknown outbox job kind", job.last_error)

    def test_stale_processing_job_is_reclaimed(self) -> None:
        job, _created = enqueue_job(kind="test.noop", dedupe_key="stale-lock")
        OutboxJob.objects.filter(pk=job.pk).update(
            status=OutboxJob.Status.PROCESSING,
            locked_at=timezone.now() - timedelta(minutes=16),
        )

        claimed = _claim_jobs(10)

        job.refresh_from_db()
        self.assertEqual(claimed, [job.pk])
        self.assertEqual(job.status, OutboxJob.Status.PROCESSING)
        self.assertIsNotNone(job.locked_at)

    def test_daily_maintenance_enqueues_each_job_once(self) -> None:
        self.assertEqual(enqueue_daily_maintenance.run(), 2)
        self.assertEqual(enqueue_daily_maintenance.run(), 0)
        self.assertEqual(OutboxJob.objects.count(), 2)

    def test_history_retention_removes_only_terminal_old_jobs(self) -> None:
        old_completed, _created = enqueue_job(
            kind="test.noop",
            dedupe_key="old-completed",
        )
        old_pending, _created = enqueue_job(
            kind="test.noop",
            dedupe_key="old-pending",
        )
        recent_completed, _created = enqueue_job(
            kind="test.noop",
            dedupe_key="recent-completed",
        )
        OutboxJob.objects.filter(pk=old_completed.pk).update(
            status=OutboxJob.Status.COMPLETED,
            updated_at=timezone.now() - timedelta(days=31),
        )
        OutboxJob.objects.filter(pk=old_pending.pk).update(
            updated_at=timezone.now() - timedelta(days=31),
        )
        OutboxJob.objects.filter(pk=recent_completed.pk).update(
            status=OutboxJob.Status.COMPLETED,
        )

        self.assertEqual(_handle_outbox_retention({}), 1)
        self.assertFalse(OutboxJob.objects.filter(pk=old_completed.pk).exists())
        self.assertTrue(OutboxJob.objects.filter(pk=old_pending.pk).exists())
        self.assertTrue(OutboxJob.objects.filter(pk=recent_completed.pk).exists())
