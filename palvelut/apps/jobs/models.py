import uuid

from django.db import models
from django.utils import timezone


class OutboxJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        DEAD = "dead", "Dead"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dedupe_key = models.CharField(max_length=200, unique=True)
    kind = models.CharField(max_length=100)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    available_at = models.DateTimeField(default=timezone.now, db_index=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_error = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["status", "available_at"],
                name="jobs_outbox_ready_idx",
            )
        ]
