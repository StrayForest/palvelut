import json
import logging
from io import StringIO

from django.test import Client, SimpleTestCase

from palvelut.observability import JsonFormatter, RequestIdFilter


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
