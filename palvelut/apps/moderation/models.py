from django.conf import settings
from django.db import models

from palvelut.apps.providers.models import Provider
from palvelut.apps.taxonomy.models import UuidV7Model


class ModerationCase(UuidV7Model):
    class Kind(models.TextChoices):
        PROVIDER_REVIEW = "provider_review", "Provider review"
        CONTENT_REPORT = "content_report", "Content report"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        RESOLVED = "resolved", "Resolved"
        DISMISSED = "dismissed", "Dismissed"

    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="moderation_cases",
    )
    kind = models.CharField(
        max_length=24,
        choices=Kind.choices,
        default=Kind.PROVIDER_REVIEW,
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
    status_token_hash = models.CharField(max_length=64, blank=True, db_index=True)
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-opened_at", "-id")


class ContentReport(UuidV7Model):
    case = models.OneToOneField(
        ModerationCase,
        on_delete=models.CASCADE,
        related_name="content_report",
    )
    category = models.CharField(max_length=40)
    details = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")


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
    visible_to_provider = models.BooleanField(default=False)
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


class DataSubjectRequest(UuidV7Model):
    class Kind(models.TextChoices):
        ACCESS = "access", "Access"
        EXPORT = "export", "Export"
        DELETE = "delete", "Delete"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        REJECTED = "rejected", "Rejected"

    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="data_subject_requests",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.OPEN,
    )
    request_note = models.TextField(blank=True, max_length=1000)
    staff_note = models.TextField(blank=True, max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")


class DataSubjectRequestEvent(UuidV7Model):
    request = models.ForeignKey(
        DataSubjectRequest,
        on_delete=models.CASCADE,
        related_name="events",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="data_subject_request_events",
    )
    action = models.CharField(max_length=80)
    note = models.TextField(blank=True, max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
