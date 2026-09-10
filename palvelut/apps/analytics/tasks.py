from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from palvelut.apps.analytics.beta import reconcile_beta_snapshot
from palvelut.apps.analytics.models import AnalyticsEvent, BetaFunnelEvent
from palvelut.observability import set_metric

ANALYTICS_RETENTION_DAYS = 90


@shared_task(name="palvelut.analytics.purge_expired")
def purge_expired_analytics() -> int:
    """Delete raw analytics events older than the privacy retention window."""
    cutoff = timezone.now() - timedelta(days=ANALYTICS_RETENTION_DAYS)
    provider_deleted, _ = AnalyticsEvent.objects.filter(occurred_at__lt=cutoff).delete()
    beta_deleted, _ = BetaFunnelEvent.objects.filter(occurred_at__lt=cutoff).delete()
    return provider_deleted + beta_deleted


@shared_task(name="palvelut.analytics.reconcile_beta_funnel")
def reconcile_beta_funnel() -> str:
    """Freeze a 30-day beta snapshot and refresh the Prometheus dashboard gauges."""
    snapshot = reconcile_beta_snapshot()
    set_metric("palvelut_beta_raw_events", snapshot.raw_event_count)
    set_metric(
        "palvelut_beta_finland_discovery_sessions",
        snapshot.finland_discovery_sessions,
    )
    set_metric("palvelut_beta_search_sessions", snapshot.search_sessions)
    set_metric(
        "palvelut_beta_contact_conversion_ratio",
        snapshot.contact_conversion_basis_points / 10_000,
    )
    set_metric(
        "palvelut_beta_zero_result_ratio",
        snapshot.zero_result_basis_points / 10_000,
    )
    return str(snapshot.id)
