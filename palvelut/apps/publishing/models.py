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


class ProviderSlug(UuidV7Model):
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="slugs",
    )
    slug = models.SlugField(max_length=220, unique=True)
    is_current = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-is_current", "-created_at", "-id")
        constraints = (
            models.UniqueConstraint(
                fields=("provider",),
                condition=models.Q(is_current=True),
                name="publishing_slug_one_current_per_provider",
            ),
        )

    def __str__(self) -> str:
        return self.slug
