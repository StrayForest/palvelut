import json
import logging
from io import StringIO
from pathlib import Path

from django.test import Client, SimpleTestCase

from palvelut import observability
from palvelut.observability import JsonFormatter, RequestIdFilter

ROOT = Path(__file__).resolve().parents[1]


class ObservabilityContractTests(SimpleTestCase):
    def test_response_has_request_id_header(self):
        response = Client().get("/palvelut/en/")

        request_id = response.headers["X-Request-ID"]
        self.assertEqual(len(request_id), 32)
        int(request_id, 16)

    def test_request_ids_are_unique_per_request(self):
        client = Client()

        first = client.get("/palvelut/en/").headers["X-Request-ID"]
        second = client.get("/palvelut/en/").headers["X-Request-ID"]

        self.assertNotEqual(first, second)

    def test_json_formatter_emits_machine_readable_core_fields(self):
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.addFilter(RequestIdFilter())
        handler.setFormatter(JsonFormatter())
        logger = logging.getLogger("tests.observability")
        old_handlers = logger.handlers[:]
        old_propagate = logger.propagate
        old_level = logger.level
        try:
            logger.handlers = [handler]
            logger.propagate = False
            logger.setLevel(logging.INFO)
            logger.info("structured_event", extra={"status": 204})
        finally:
            logger.handlers = old_handlers
            logger.propagate = old_propagate
            logger.setLevel(old_level)

        payload = json.loads(stream.getvalue())
        self.assertEqual(payload["level"], "INFO")
        self.assertEqual(payload["logger"], "tests.observability")
        self.assertEqual(payload["message"], "structured_event")
        self.assertIsNone(payload["request_id"])
        self.assertEqual(payload["status"], 204)
        self.assertTrue(payload["timestamp"].endswith("+00:00"))

    def test_settings_use_request_id_middleware_and_json_console_logging(self):
        from django.conf import settings

        self.assertEqual(
            settings.MIDDLEWARE[0], "palvelut.observability.RequestIdMiddleware"
        )
        self.assertEqual(
            settings.LOGGING["formatters"]["json"]["()"],
            "palvelut.observability.JsonFormatter",
        )
        self.assertEqual(
            settings.LOGGING["handlers"]["console"]["filters"], ["request_id"]
        )
        self.assertEqual(
            settings.EMAIL_BACKEND, "palvelut.observability.MetricsSMTPEmailBackend"
        )
        self.assertTrue(hasattr(settings, "SENTRY_DSN"))
        self.assertTrue(hasattr(settings, "SENTRY_RELEASE"))
        self.assertTrue(hasattr(settings, "OBSERVABILITY_METRICS_TOKEN"))

    def test_required_quality_signals_have_dashboard_panels(self):
        dashboard = json.loads(
            (ROOT / "infra" / "observability" / "dashboard.json").read_text()
        )
        expressions = "\n".join(panel["expr"] for panel in dashboard["panels"])
        required_metrics = (
            "palvelut_http_requests_total",
            "palvelut_http_request_duration_seconds_bucket",
            "palvelut_cache_requests_total",
            "palvelut_db_query_duration_seconds_bucket",
            "palvelut_db_connections",
            "palvelut_db_waiting_connections",
            "palvelut_queue_depth",
            "palvelut_queue_age_seconds",
            "palvelut_queue_failures_total",
            "palvelut_email_delivery_total",
            "palvelut_media_failures_total",
            "palvelut_backup_runs_total",
        )
        for metric in required_metrics:
            self.assertIn(metric, expressions)
        self.assertEqual(dashboard["quality_contract"], "quality-v1")

    def test_alerts_reference_runbook_and_cover_failure_domains(self):
        alerts = json.loads(
            (ROOT / "infra" / "observability" / "alerts.json").read_text()
        )
        self.assertEqual(alerts["runbook"], "docs/runbooks/observability.md")
        names = {alert["name"] for alert in alerts["alerts"]}
        self.assertTrue(
            {
                "AvailabilityBudgetBurn",
                "PublicLatencyHigh",
                "DatabaseWaiting",
                "SlowQueries",
                "QueueBacklog",
                "QueueFailures",
                "EmailDeliveryFailures",
                "MediaFailures",
                "BackupMissingOrFailed",
                "CacheHitRatioLow",
            }.issubset(names)
        )

    def test_prometheus_payload_exposes_build_and_cross_process_signals(self):
        original_db = observability._db_connection_gauges
        original_queue = observability._queue_depth
        original_shared = observability._shared_value
        try:
            observability._db_connection_gauges = lambda: (2.0, 1.0)
            observability._queue_depth = lambda: 3.0
            observability._shared_value = lambda signal: 4.0
            payload = observability.prometheus_payload()
        finally:
            observability._db_connection_gauges = original_db
            observability._queue_depth = original_queue
            observability._shared_value = original_shared

        self.assertIn("palvelut_build_info", payload)
        self.assertIn('schema="quality-v1"', payload)
        self.assertIn("palvelut_db_connections 2.0", payload)
        self.assertIn("palvelut_queue_depth 3.0", payload)
        self.assertIn(
            'palvelut_backup_runs_total{result="success"} 4.0', payload
        )
