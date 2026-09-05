from django.db import models

from palvelut.apps.providers.models import Provider
from palvelut.apps.taxonomy.models import UuidV7Model


class AnalyticsEvent(UuidV7Model):
    class Kind(models.TextChoices):
        IMPRESSION = "impression", "Impression"
        PROFILE_VIEW = "profile_view", "Profile view"
        CONTACT_CLICK = "contact_click", "Contact click"

    kind = models.CharField(max_length=32, choices=Kind.choices)
    provider = models.ForeignKey(
        Provider,
        on_delete=models.CASCADE,
        related_name="analytics_events",
    )
    channel = models.CharField(max_length=16, blank=True, default="")
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("occurred_at", "id")
        constraints = (
            models.CheckConstraint(
                condition=models.Q(
                    kind__in=("impression", "profile_view", "contact_click")
                ),
                name="analytics_event_kind_valid",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(kind="contact_click", channel__gt="")
                    | models.Q(kind__in=("impression", "profile_view"), channel="")
                ),
                name="analytics_event_channel_matches_kind",
            ),
        )
