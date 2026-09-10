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


class BetaFunnelEvent(UuidV7Model):
    """Privacy-safe raw event used only for the frozen P6 beta decision funnel."""

    class Kind(models.TextChoices):
        DISCOVERY_VIEW = "discovery_view", "Discovery view"
        SEARCH = "search", "Search"
        CONTACT = "contact", "Contact"

    session_id = models.UUIDField()
    kind = models.CharField(max_length=24, choices=Kind.choices)
    provider = models.ForeignKey(
        Provider,
        on_delete=models.SET_NULL,
        related_name="beta_funnel_events",
        null=True,
        blank=True,
    )
    channel = models.CharField(max_length=16, blank=True, default="")
    country_code = models.CharField(max_length=2)
    search_had_results = models.BooleanField(null=True, blank=True)
    schema_version = models.CharField(max_length=32)
    metric_version = models.CharField(max_length=32)
    bot_rule_version = models.CharField(max_length=32)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("occurred_at", "id")
        indexes = (
            models.Index(fields=("occurred_at", "country_code"), name="beta_evt_time_country"),
            models.Index(fields=("session_id", "occurred_at"), name="beta_evt_session_time"),
            models.Index(fields=("kind", "occurred_at"), name="beta_evt_kind_time"),
        )
        constraints = (
            models.CheckConstraint(
                condition=models.Q(kind__in=("discovery_view", "search", "contact")),
                name="beta_funnel_event_kind_valid",
            ),
            models.CheckConstraint(
                condition=models.Q(country_code__regex=r"^[A-Z]{2}$"),
                name="beta_funnel_country_code_shape",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        kind="search",
                        provider__isnull=True,
                        channel="",
                        search_had_results__isnull=False,
                    )
                    | models.Q(
                        kind="contact",
                        provider__isnull=False,
                        channel__gt="",
                        search_had_results__isnull=True,
                    )
                    | models.Q(
                        kind="discovery_view",
                        channel="",
                        search_had_results__isnull=True,
                    )
                ),
                name="beta_funnel_event_payload_matches_kind",
            ),
        )


class BetaDecisionSnapshot(UuidV7Model):
    """Reconciled 30-day snapshot exported to the production beta dashboard."""

    window_start = models.DateTimeField()
    window_end = models.DateTimeField()
    schema_version = models.CharField(max_length=32)
    metric_version = models.CharField(max_length=32)
    bot_rule_version = models.CharField(max_length=32)
    raw_event_count = models.PositiveIntegerField()
    finland_discovery_sessions = models.PositiveIntegerField()
    search_sessions = models.PositiveIntegerField()
    search_sessions_with_contact = models.PositiveIntegerField()
    search_events = models.PositiveIntegerField()
    zero_result_searches = models.PositiveIntegerField()
    contact_conversion_basis_points = models.PositiveIntegerField()
    zero_result_basis_points = models.PositiveIntegerField()
    source_checksum = models.CharField(max_length=64)
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-generated_at", "-id")
