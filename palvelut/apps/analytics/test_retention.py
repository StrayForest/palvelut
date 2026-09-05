from datetime import datetime, timedelta, timezone as dt_timezone
from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase

from palvelut.apps.analytics.tasks import (
    ANALYTICS_RETENTION_DAYS,
    purge_expired_analytics,
)


class AnalyticsRetentionTests(SimpleTestCase):
    @patch("palvelut.apps.analytics.tasks.AnalyticsEvent.objects.filter")
    def test_purge_deletes_only_events_older_than_ninety_days(self, filter_mock):
        now = datetime(2026, 9, 5, 12, 0, tzinfo=dt_timezone.utc)
        queryset = filter_mock.return_value
        queryset.delete.return_value = (3, {"analytics.AnalyticsEvent": 3})

        with patch("palvelut.apps.analytics.tasks.timezone.now", return_value=now):
            deleted = purge_expired_analytics.run()

        filter_mock.assert_called_once_with(
            occurred_at__lt=now - timedelta(days=ANALYTICS_RETENTION_DAYS)
        )
        queryset.delete.assert_called_once_with()
        self.assertEqual(deleted, 3)
        self.assertEqual(ANALYTICS_RETENTION_DAYS, 90)

    def test_retention_task_is_scheduled_daily(self):
        job = settings.CELERY_BEAT_SCHEDULE["purge-expired-analytics"]
        self.assertEqual(job["task"], "palvelut.analytics.purge_expired")
        self.assertEqual(str(job["schedule"]), "<crontab: 20 3 * * * (m/h/dM/MY/d)>")
