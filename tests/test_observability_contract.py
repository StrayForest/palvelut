import json
import logging
from io import StringIO

import pytest
from django.test import Client

from palvelut.observability import JsonFormatter, RequestIdFilter


@pytest.mark.django_db
def test_response_has_request_id_header():
    response = Client().get("/palvelut/en/")

    request_id = response.headers["X-Request-ID"]
    assert len(request_id) == 32
    int(request_id, 16)


@pytest.mark.django_db
def test_request_ids_are_unique_per_request():
    client = Client()

    first = client.get("/palvelut/en/").headers["X-Request-ID"]
    second = client.get("/palvelut/en/").headers["X-Request-ID"]

    assert first != second


def test_json_formatter_emits_machine_readable_core_fields():
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("tests.observability")
    logger.handlers = [handler]
    logger.propagate = False
    logger.setLevel(logging.INFO)

    logger.info("structured_event", extra={"status": 204})

    payload = json.loads(stream.getvalue())
    assert payload["level"] == "INFO"
    assert payload["logger"] == "tests.observability"
    assert payload["message"] == "structured_event"
    assert payload["request_id"] is None
    assert payload["status"] == 204
    assert payload["timestamp"].endswith("+00:00")


def test_settings_use_request_id_middleware_and_json_console_logging():
    from django.conf import settings

    assert settings.MIDDLEWARE[0] == "palvelut.observability.RequestIdMiddleware"
    assert settings.LOGGING["formatters"]["json"]["()"] == "palvelut.observability.JsonFormatter"
    assert settings.LOGGING["handlers"]["console"]["filters"] == ["request_id"]
