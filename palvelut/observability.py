import json
import logging
import os
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from hmac import compare_digest
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_access_logger = logging.getLogger("palvelut.request")
_observability_logger = logging.getLogger("palvelut.observability")

COUNTER_METRICS = {
    "palvelut_http_requests_total",
    "palvelut_http_5xx_total",
    "palvelut_cache_hits_total",
    "palvelut_cache_misses_total",
    "palvelut_db_slow_queries_total",
    "palvelut_queue_failures_total",
    "palvelut_email_delivery_failures_total",
    "palvelut_media_failures_total",
    "palvelut_backup_failures_total",
}
GAUGE_METRICS = {
    "palvelut_db_pool_in_use",
    "palvelut_queue_oldest_age_seconds",
    "palvelut_backup_age_seconds",
}
OBSERVATION_METRICS = {"palvelut_http_request_duration_seconds"}


def current_request_id() -> str | None:
    return _request_id.get()


def _metric_key(name: str, suffix: str = "value") -> str:
    return f"observability:{name}:{suffix}"


def increment_metric(name: str, value: int = 1) -> None:
    if name not in COUNTER_METRICS:
        raise ValueError(f"unknown counter metric: {name}")
    key = _metric_key(name)
    try:
        cache.incr(key, value)
    except ValueError:
        cache.add(key, value, timeout=None)
    except Exception:
        _observability_logger.warning(
            "metric_counter_write_failed", extra={"metric": name}
        )


def set_metric(name: str, value: float) -> None:
    if name not in GAUGE_METRICS:
        raise ValueError(f"unknown gauge metric: {name}")
    try:
        cache.set(_metric_key(name), float(value), timeout=None)
    except Exception:
        _observability_logger.warning(
            "metric_gauge_write_failed", extra={"metric": name}
        )


def observe_metric(name: str, value: float) -> None:
    if name not in OBSERVATION_METRICS:
        raise ValueError(f"unknown observation metric: {name}")
    try:
        count_key = _metric_key(name, "count")
        sum_key = _metric_key(name, "sum_us")
        try:
            cache.incr(count_key, 1)
        except ValueError:
            cache.add(count_key, 1, timeout=None)
        microseconds = max(0, round(value * 1_000_000))
        try:
            cache.incr(sum_key, microseconds)
        except ValueError:
            cache.add(sum_key, microseconds, timeout=None)
    except Exception:
        _observability_logger.warning(
            "metric_observation_write_failed", extra={"metric": name}
        )


def _metric_value(name: str, suffix: str = "value") -> float:
    try:
        value = cache.get(_metric_key(name, suffix), 0)
        return float(value or 0)
    except Exception:
        return 0.0


def render_prometheus_metrics() -> str:
    lines: list[str] = []
    for name in sorted(COUNTER_METRICS):
        lines.extend((f"# TYPE {name} counter", f"{name} {_metric_value(name):g}"))
    for name in sorted(GAUGE_METRICS):
        lines.extend((f"# TYPE {name} gauge", f"{name} {_metric_value(name):g}"))
    for name in sorted(OBSERVATION_METRICS):
        count = _metric_value(name, "count")
        total = _metric_value(name, "sum_us") / 1_000_000
        lines.extend(
            (
                f"# TYPE {name} summary",
                f"{name}_sum {total:g}",
                f"{name}_count {count:g}",
            )
        )
    return "\n".join(lines) + "\n"


def metrics(request: HttpRequest) -> HttpResponse:
    token = os.getenv("METRICS_TOKEN", "")
    if not token:
        return HttpResponse(status=404)
    supplied = request.headers.get("Authorization", "")
    expected = f"Bearer {token}"
    if not compare_digest(supplied, expected):
        return HttpResponse(status=403)
    response = HttpResponse(
        render_prometheus_metrics(),
        content_type="text/plain; version=0.0.4; charset=utf-8",
    )
    response["Cache-Control"] = "no-store"
    return response


def _sentry_envelope_url(dsn: str) -> tuple[str, str] | None:
    parsed = urlsplit(dsn)
    project_id = parsed.path.strip("/")
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or not project_id:
        return None
    public_key = parsed.username or ""
    if not public_key:
        return None
    port = f":{parsed.port}" if parsed.port else ""
    base = f"{parsed.scheme}://{parsed.hostname}{port}"
    return f"{base}/api/{project_id}/envelope/", public_key


def capture_exception(exc: BaseException) -> None:
    dsn = os.getenv("SENTRY_DSN", "")
    if not dsn:
        return
    endpoint = _sentry_envelope_url(dsn)
    if endpoint is None:
        _observability_logger.error("sentry_dsn_invalid")
        return
    envelope_url, public_key = endpoint
    event_id = uuid.uuid4().hex
    header = {"event_id": event_id, "dsn": dsn}
    event = {
        "event_id": event_id,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "level": "error",
        "platform": "python",
        "environment": settings.ENVIRONMENT,
        "release": os.getenv("PALVELUT_RELEASE", "unknown"),
        "tags": {"request_id": current_request_id() or "none"},
        "exception": {
            "values": [
                {
                    "type": type(exc).__name__,
                    "value": str(exc)[:500],
                }
            ]
        },
    }
    body = (
        json.dumps(header, separators=(",", ":"))
        + "\n"
        + json.dumps({"type": "event"}, separators=(",", ":"))
        + "\n"
        + json.dumps(event, separators=(",", ":"))
        + "\n"
    ).encode()
    request = Request(
        envelope_url,
        data=body,
        headers={
            "Content-Type": "application/x-sentry-envelope",
            "X-Sentry-Auth": f"Sentry sentry_version=7, sentry_key={public_key}",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=1) as response:
            response.read(1)
    except Exception:
        _observability_logger.warning("sentry_delivery_failed")


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
        for field in ("method", "path", "status", "duration_ms", "metric"):
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
            try:
                response = self.get_response(request)
            except Exception as exc:
                increment_metric("palvelut_http_5xx_total")
                capture_exception(exc)
                raise
            response["X-Request-ID"] = request_id
            elapsed = time.monotonic() - started
            increment_metric("palvelut_http_requests_total")
            observe_metric("palvelut_http_request_duration_seconds", elapsed)
            if response.status_code >= 500:
                increment_metric("palvelut_http_5xx_total")
            duration_ms = round(elapsed * 1000, 2)
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
