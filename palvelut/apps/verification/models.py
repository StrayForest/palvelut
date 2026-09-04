from django.conf import settings
from django.db import models

from palvelut.apps.providers.models import Provider
from palvelut.apps.taxonomy.models import UuidV7Model


class VerificationCheck(UuidV7Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"
        EXPIRED = "expired", "Expired"

    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="verification_checks",
    )
    kind = models.CharField(max_length=80)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    source_url = models.URLField(max_length=500, blank=True)
    evidence_metadata = models.JSONField(default=dict)
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="verification_checks",
    )
    checked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-checked_at", "-id")


class VerificationEvent(UuidV7Model):
    check = models.ForeignKey(
        VerificationCheck,
        on_delete=models.CASCADE,
        related_name="events",
    )
    status = models.CharField(max_length=16, choices=VerificationCheck.Status.choices)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="verification_events",
    )
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
