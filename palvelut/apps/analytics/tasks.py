from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from palvelut.apps.analytics.models import AnalyticsEvent

ANALYTICS_RETENTION_DAYS = 90


@shared_task(name="palvelut.analytics.purge_expired")
def purge_expired_analytics() -> int:
    """Delete raw analytics events older than the privacy retention window."""
    cutoff = timezone.now() - timedelta(days=ANALYTICS_RETENTION_DAYS)
    deleted, _ = AnalyticsEvent.objects.filter(occurred_at__lt=cutoff).delete()
    return deleted
