import json
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone

from django.db import connection
from django.http import HttpRequest, HttpResponse

from palvelut.metrics import adjust_gauge, record_db_query, record_request
from palvelut.sentry_transport import capture_exception

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


class _DatabaseMetricsWrapper:
    def __call__(self, execute, sql, params, many, context):
        started = time.monotonic()
        adjust_gauge("palvelut_db_connections_in_use", 1)
        try:
            return execute(sql, params, many, context)
        finally:
            adjust_gauge("palvelut_db_connections_in_use", -1)
            record_db_query(time.monotonic() - started)


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = uuid.uuid4().hex
        request.request_id = request_id
        token = _request_id.set(request_id)
        started = time.monotonic()
        status = 500
        try:
            with connection.execute_wrapper(_DatabaseMetricsWrapper()):
                response = self.get_response(request)
            status = response.status_code
            response["X-Request-ID"] = request_id
            return response
        except Exception as exc:
            capture_exception(exc, request_id=request_id)
            raise
        finally:
            duration_seconds = time.monotonic() - started
            record_request(request.method, status, duration_seconds)
            _access_logger.info(
                "request_complete",
                extra={
                    "method": request.method,
                    "path": request.path,
                    "status": status,
                    "duration_ms": round(duration_seconds * 1000, 2),
                },
            )
            _request_id.reset(token)
