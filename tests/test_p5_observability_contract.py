import json
import unittest
from pathlib import Path

from django.test import Client, SimpleTestCase

from palvelut.metrics import (
    record_backup,
    record_email,
    record_media_failure,
    record_queue,
    render_prometheus,
)

ROOT = Path(__file__).resolve().parents[1]


class P5ObservabilityRuntimeTests(SimpleTestCase):
    def test_metrics_endpoint_is_no_store_and_exposes_request_metrics(self):
        client = Client()
        client.get("/palvelut/en/")
        response = client.get("/palvelut/internal/metrics")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        body = response.content.decode()
        self.assertIn("palvelut_http_requests_total", body)
        self.assertIn("palvelut_http_request_duration_seconds", body)

    def test_operational_signal_helpers_have_prometheus_series(self):
        record_queue(age_seconds=2.0, failed=True)
        record_email(delivered=False)
        record_media_failure()
        record_backup(succeeded=True, completed_at=1_700_000_000.0)
        record_backup(succeeded=False)

        body = render_prometheus()
        for metric in (
            "palvelut_queue_age_seconds",
            "palvelut_queue_failures_total",
            "palvelut_email_delivery_total",
            "palvelut_media_failures_total",
            "palvelut_backup_last_success_timestamp_seconds",
            "palvelut_backup_failures_total",
        ):
            self.assertIn(metric, body)


class P5ObservabilityConfigTests(unittest.TestCase):
    def test_dashboard_covers_every_quality_signal(self):
        dashboard = json.loads((ROOT / "infra/monitoring/dashboard.json").read_text())
        serialized = json.dumps(dashboard)
        for metric in (
            "palvelut_http_requests_total",
            "palvelut_http_request_duration_seconds",
            "palvelut_http_5xx_total",
            "palvelut_cache_requests_total",
            "palvelut_db_connections_in_use",
            "palvelut_db_slow_queries_total",
            "palvelut_queue_age_seconds",
            "palvelut_queue_failures_total",
            "palvelut_email_delivery_total",
            "palvelut_media_failures_total",
            "palvelut_backup_last_success_timestamp_seconds",
            "palvelut_backup_failures_total",
        ):
            self.assertIn(metric, serialized)

    def test_alerts_link_to_runbook_and_cover_every_quality_signal(self):
        alerts = (ROOT / "infra/monitoring/alerts.yml").read_text()
        self.assertEqual(alerts.count("runbook_url:"), 12)
        for marker in (
            "palvelut_http_requests_total",
            "palvelut_http_request_duration_seconds_bucket",
            "palvelut_http_5xx_total",
            "palvelut_cache_requests_total",
            "palvelut_db_connections_in_use",
            "palvelut_db_slow_queries_total",
            "palvelut_queue_age_seconds_bucket",
            "palvelut_queue_failures_total",
            "palvelut_email_delivery_total",
            "palvelut_media_failures_total",
            "palvelut_backup_last_success_timestamp_seconds",
            "palvelut_backup_failures_total",
        ):
            self.assertIn(marker, alerts)

    def test_metrics_are_private_and_sentry_payload_avoids_request_pii(self):
        nginx = (ROOT / "infra/ansible/templates/palvelut-nginx.conf.j2").read_text()
        sentry = (ROOT / "palvelut/sentry_transport.py").read_text()
        self.assertIn("location = /palvelut/internal/metrics", nginx)
        self.assertIn("return 404", nginx)
        self.assertNotIn('"cookies"', sentry)
        self.assertNotIn('"headers"', sentry)
        self.assertNotIn('"user"', sentry)
        self.assertNotIn('"request"', sentry)
        self.assertIn('"request_id"', sentry)


if __name__ == "__main__":
    unittest.main()
