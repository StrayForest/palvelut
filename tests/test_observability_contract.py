import json
import logging
import os
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.test import Client, RequestFactory, SimpleTestCase

from palvelut.observability import (
    COUNTER_METRICS,
    GAUGE_METRICS,
    JsonFormatter,
    RequestIdFilter,
    metrics,
)

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

    def test_quality_signals_are_covered_by_dashboard_and_alerts(self):
        dashboard = json.loads(
            (ROOT / "infra" / "observability" / "dashboard.json").read_text()
        )
        alerts = (ROOT / "infra" / "observability" / "alerts.yml").read_text()
        rendered = json.dumps(dashboard)
        required = {
            "palvelut_http_requests_total",
            "palvelut_http_request_duration_seconds",
            "palvelut_http_5xx_total",
            "palvelut_cache_hits_total",
            "palvelut_cache_misses_total",
            "palvelut_db_pool_in_use",
            "palvelut_db_slow_queries_total",
            "palvelut_queue_oldest_age_seconds",
            "palvelut_queue_failures_total",
            "palvelut_email_delivery_failures_total",
            "palvelut_media_failures_total",
            "palvelut_backup_age_seconds",
            "palvelut_backup_failures_total",
        }
        for metric_name in required:
            self.assertTrue(metric_name in rendered or metric_name in alerts, metric_name)
        for alert_block in alerts.split("- alert:")[1:]:
            self.assertIn("runbook:", alert_block)

    def test_metric_registry_declares_operational_signals(self):
        self.assertIn("palvelut_http_requests_total", COUNTER_METRICS)
        self.assertIn("palvelut_queue_failures_total", COUNTER_METRICS)
        self.assertIn("palvelut_backup_failures_total", COUNTER_METRICS)
        self.assertIn("palvelut_db_pool_in_use", GAUGE_METRICS)
        self.assertIn("palvelut_queue_oldest_age_seconds", GAUGE_METRICS)
        self.assertIn("palvelut_backup_age_seconds", GAUGE_METRICS)

    def test_metrics_endpoint_requires_external_bearer_token(self):
        request = RequestFactory().get("/palvelut/metrics")
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("METRICS_TOKEN", None)
            self.assertEqual(metrics(request).status_code, 404)
        with patch.dict(os.environ, {"METRICS_TOKEN": "metric-secret"}):
            self.assertEqual(metrics(request).status_code, 403)
            authorized = RequestFactory().get(
                "/palvelut/metrics", HTTP_AUTHORIZATION="Bearer metric-secret"
            )
            response = metrics(authorized)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Cache-Control"], "no-store")

    def test_sentry_runbook_forbids_personal_payloads(self):
        runbook = (ROOT / "docs" / "runbooks" / "observability.md").read_text()
        self.assertIn("request/user payloads are intentionally omitted", runbook)
        self.assertIn("PALVELUT_RELEASE", runbook)
        self.assertIn("METRICS_TOKEN", runbook)
