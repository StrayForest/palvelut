import json
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone

from django.http import HttpRequest, HttpResponse

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_access_logger = logging.getLogger("palvelut.request")


def current_request_id() -> str | None:
    return _request_id.get()


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = current_request_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }
        for field in ("method", "path", "status", "duration_ms"):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = uuid.uuid4().hex
        request.request_id = request_id
        token = _request_id.set(request_id)
        started = time.monotonic()
        try:
            response = self.get_response(request)
            response["X-Request-ID"] = request_id
            duration_ms = round((time.monotonic() - started) * 1000, 2)
            _access_logger.info(
                "request_complete",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "duration_ms": duration_ms,
                },
            )
            return response
        finally:
            _request_id.reset(token)
