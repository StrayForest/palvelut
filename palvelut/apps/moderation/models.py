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
        null=True,
        blank=True,
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
        null=True,
        blank=True,
    )
    note = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")


class ContentReport(UuidV7Model):
    case = models.OneToOneField(
        ModerationCase,
        on_delete=models.CASCADE,
        related_name="content_report",
    )
    public_token_hash = models.CharField(max_length=64, unique=True)
    details = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")


class ProviderNotice(UuidV7Model):
    case = models.ForeignKey(
        ModerationCase,
        on_delete=models.CASCADE,
        related_name="provider_notices",
    )
    message = models.TextField(max_length=4000)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_provider_notices",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")


class ModerationAppeal(UuidV7Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        UPHELD = "upheld", "Upheld"
        DENIED = "denied", "Denied"

    case = models.ForeignKey(
        ModerationCase,
        on_delete=models.CASCADE,
        related_name="appeals",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="moderation_appeals",
    )
    message = models.TextField(max_length=4000)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

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
