from django.conf import settings
from django.db import models

from palvelut.apps.providers.models import Provider
from palvelut.apps.taxonomy.models import UuidV7Model


class ModerationCase(UuidV7Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="moderation_cases",
    )
    reason = models.CharField(max_length=120)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
    )
    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="opened_moderation_cases",
    )
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-opened_at", "-id")


class ModerationEvent(UuidV7Model):
    case = models.ForeignKey(
        ModerationCase,
        on_delete=models.CASCADE,
        related_name="events",
    )
    event_type = models.CharField(max_length=80)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="moderation_events",
    )
    note = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")


class AuditEvent(UuidV7Model):
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="audit_events",
    )
    action = models.CharField(max_length=120)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
