from django.conf import settings
from django.db import models

from palvelut.apps.providers.models import Provider
from palvelut.apps.taxonomy.models import UuidV7Model


class ProfileRevision(UuidV7Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        CHANGES_REQUESTED = "changes_requested", "Changes requested"
        SUPERSEDED = "superseded", "Superseded"

    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="profile_revisions",
    )
    status = models.CharField(
        max_length=24,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    payload = models.JSONField(default=dict)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_profile_revisions",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
