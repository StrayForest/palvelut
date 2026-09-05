from __future__ import annotations

import json
import logging
import threading
import time
import uuid
from collections import defaultdict
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from django.conf import settings
from django.core.cache import cache
from django.core.mail.backends.smtp import EmailBackend as SMTPEmailBackend
from django.db import connection
from django.http import HttpRequest, HttpResponse

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_access_logger = logging.getLogger("palvelut.request")
_observability_logger = logging.getLogger("palvelut.observability")
_metrics_lock = threading.Lock()
_counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
_histograms: dict[tuple[str, tuple[tuple[str, str], ...]], list[float]] = defaultdict(
    list
)

REQUEST_BUCKETS = (0.05, 0.1, 0.3, 0.8, 1.5, 3.0, 10.0)
DB_BUCKETS = (0.01, 0.05, 0.1, 0.3, 1.0, 3.0)
_SHARED_SIGNAL_KEYS = {
    "queue_failure": "obs:queue_failure_total",
    "queue_age": "obs:queue_age_seconds",
    "email_success": "obs:email_success_total",
    "email_failure": "obs:email_failure_total",
    "media_failure": "obs:media_failure_total",
    "backup_success": "obs:backup_success_total",
    "backup_failure": "obs:backup_failure_total",
}


def current_request_id() -> str | None:
    return _request_id.get()


def _labels(**labels: object) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((key, str(value)) for key, value in labels.items()))


def metric_inc(name: str, amount: float = 1.0, **labels: object) -> None:
    key = (name, _labels(**labels))
    with _metrics_lock:
        _counters[key] += amount


def metric_observe(name: str, value: float, **labels: object) -> None:
    key = (name, _labels(**labels))
    with _metrics_lock:
        values = _histograms[key]
        values.append(value)
        if len(values) > 5000:
            del values[: len(values) - 5000]


def _shared_increment(signal: str, amount: int = 1) -> None:
    key = _SHARED_SIGNAL_KEYS[signal]
    try:
        cache.add(key, 0, timeout=None)
        cache.incr(key, amount)
    except Exception:
        _observability_logger.warning(
            "shared_metric_increment_failed", extra={"signal": signal}
        )


def _shared_set(signal: str, value: float) -> None:
    try:
        cache.set(_SHARED_SIGNAL_KEYS[signal], value, timeout=None)
    except Exception:
        _observability_logger.warning(
            "shared_metric_set_failed", extra={"signal": signal}
        )


def observe_queue_age(seconds: float) -> None:
    _shared_set("queue_age", max(0.0, seconds))


def observe_queue_failure() -> None:
    _shared_increment("queue_failure")


def observe_media_failure() -> None:
    _shared_increment("media_failure")


def observe_backup(*, success: bool) -> None:
    _shared_increment("backup_success" if success else "backup_failure")


def _sentry_endpoint() -> tuple[str, str] | None:
    dsn = getattr(settings, "SENTRY_DSN", "")
    if not dsn:
        return None
    parsed = urllib_parse.urlsplit(dsn)
    project_id = parsed.path.strip("/")
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or not parsed.username
        or not project_id
    ):
        return None
    host = parsed.hostname
    if parsed.port:
        host = f"{host}:{parsed.port}"
    endpoint = f"{parsed.scheme}://{host}/api/{project_id}/envelope/"
    return endpoint, parsed.username


def capture_exception(exc: BaseException, *, request_id: str | None = None) -> None:
    target = _sentry_endpoint()
    if target is None:
        return
    endpoint, public_key = target
    event_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    event = {
        "event_id": event_id,
        "timestamp": now,
        "platform": "python",
        "level": "error",
        "environment": getattr(
            settings, "SENTRY_ENVIRONMENT", settings.ENVIRONMENT
        ),
        "release": getattr(settings, "SENTRY_RELEASE", "") or None,
        "tags": {"request_id": request_id or "none"},
        "exception": {
            "values": [
                {
                    "type": type(exc).__name__,
                    "value": str(exc)[:500],
                    "module": type(exc).__module__,
                }
            ]
        },
    }
    envelope = "\n".join(
        (
            json.dumps(
                {"event_id": event_id, "sent_at": now}, separators=(",", ":")
            ),
            json.dumps(
                {"type": "event", "content_type": "application/json"},
                separators=(",", ":"),
            ),
            json.dumps(event, separators=(",", ":")),
        )
    ).encode()
    req = urllib_request.Request(
        endpoint,
        data=envelope,
        headers={
            "Content-Type": "application/x-sentry-envelope",
            "X-Sentry-Auth": (
                "Sentry sentry_version=7, "
                f"sentry_key={public_key}, sentry_client=palvelut/1"
            ),
        },
        method="POST",
    )
    try:
        urllib_request.urlopen(req, timeout=1).close()
    except (OSError, urllib_error.URLError):
        _observability_logger.warning("sentry_delivery_failed")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = current_request_id()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }
        for field in ("method", "path", "status", "duration_ms", "signal"):
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def _db_execute_observer(execute, sql, params, many, context):
    started = time.monotonic()
    try:
        return execute(sql, params, many, context)
    finally:
        duration = time.monotonic() - started
        metric_observe("palvelut_db_query_duration_seconds", duration)
        slow_threshold = (
            getattr(settings, "OBSERVABILITY_SLOW_QUERY_MS", 300) / 1000
        )
        if duration >= slow_threshold:
            metric_inc("palvelut_db_slow_query_total")


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
                with connection.execute_wrapper(_db_execute_observer):
                    response = self.get_response(request)
            except Exception as exc:
                capture_exception(exc, request_id=request_id)
                raise
            response["X-Request-ID"] = request_id
            duration = time.monotonic() - started
            duration_ms = round(duration * 1000, 2)
            resolver_match = getattr(request, "resolver_match", None)
            route_name = getattr(resolver_match, "url_name", None) or "unmatched"
            route_class = (
                "health"
                if route_name.startswith("health-")
                else "staff"
                if request.path.startswith("/palvelut/staff/")
                else "account"
                if request.path.startswith("/palvelut/account/")
                else "public"
            )
            status_class = f"{response.status_code // 100}xx"
            metric_inc(
                "palvelut_http_requests_total",
                method=request.method,
                route=route_name,
                route_class=route_class,
                status_class=status_class,
            )
            metric_observe(
                "palvelut_http_request_duration_seconds",
                duration,
                route_class=route_class,
            )
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


class MetricsSMTPEmailBackend(SMTPEmailBackend):
    def send_messages(self, email_messages):
        try:
            sent = super().send_messages(email_messages)
        except Exception:
            _shared_increment("email_failure")
            raise
        _shared_increment("email_success", int(sent or 0))
        return sent


def _metric_line(
    name: str,
    value: float,
    labels: tuple[tuple[str, str], ...] = (),
) -> str:
    label_text = ""
    if labels:
        rendered = ",".join(
            f'{key}="{value.replace(chr(92), chr(92) * 2).replace(chr(34), chr(92) + chr(34))}"'
            for key, value in labels
        )
        label_text = "{" + rendered + "}"
    return f"{name}{label_text} {value}"


def _histogram_lines(
    name: str,
    values: list[float],
    labels: tuple[tuple[str, str], ...],
    buckets: tuple[float, ...],
) -> list[str]:
    lines: list[str] = []
    for bucket in buckets:
        bucket_labels = labels + (("le", str(bucket)),)
        lines.append(
            _metric_line(
                f"{name}_bucket",
                sum(value <= bucket for value in values),
                bucket_labels,
            )
        )
    lines.append(
        _metric_line(
            f"{name}_bucket", len(values), labels + (("le", "+Inf"),)
        )
    )
    lines.append(_metric_line(f"{name}_count", len(values), labels))
    lines.append(_metric_line(f"{name}_sum", sum(values), labels))
    return lines


def _shared_value(signal: str) -> float:
    try:
        return float(cache.get(_SHARED_SIGNAL_KEYS[signal], 0) or 0)
    except Exception:
        return 0.0


def _db_connection_gauges() -> tuple[float, float]:
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT count(*), count(*) FILTER (WHERE wait_event IS NOT NULL) "
                "FROM pg_stat_activity WHERE datname = current_database()"
            )
            total, waiting = cursor.fetchone()
        return float(total), float(waiting)
    except Exception:
        return 0.0, 0.0


def _queue_depth() -> float:
    try:
        from redis import Redis

        client = Redis.from_url(
            settings.CELERY_BROKER_URL,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        return float(client.llen("celery"))
    except Exception:
        return 0.0


def prometheus_payload() -> str:
    with _metrics_lock:
        counters = list(_counters.items())
        histograms = [
            (key, list(values)) for key, values in _histograms.items()
        ]
    lines = [
        "# HELP palvelut_build_info Static build metadata.",
        "# TYPE palvelut_build_info gauge",
    ]
    build_labels = _labels(
        environment=settings.ENVIRONMENT,
        release=getattr(settings, "SENTRY_RELEASE", "") or "unknown",
        schema="quality-v1",
    )
    lines.append(_metric_line("palvelut_build_info", 1, build_labels))
    for (name, labels), value in sorted(counters):
        lines.append(_metric_line(name, value, labels))
    for (name, labels), values in sorted(histograms):
        buckets = (
            DB_BUCKETS if name.startswith("palvelut_db_") else REQUEST_BUCKETS
        )
        lines.extend(_histogram_lines(name, values, labels, buckets))
    total_connections, waiting_connections = _db_connection_gauges()
    lines.append(_metric_line("palvelut_db_connections", total_connections))
    lines.append(
        _metric_line("palvelut_db_waiting_connections", waiting_connections)
    )
    lines.append(_metric_line("palvelut_queue_depth", _queue_depth()))
    lines.append(
        _metric_line("palvelut_queue_age_seconds", _shared_value("queue_age"))
    )
    lines.append(
        _metric_line(
            "palvelut_queue_failures_total", _shared_value("queue_failure")
        )
    )
    lines.append(
        _metric_line(
            "palvelut_email_delivery_total",
            _shared_value("email_success"),
            _labels(result="success"),
        )
    )
    lines.append(
        _metric_line(
            "palvelut_email_delivery_total",
            _shared_value("email_failure"),
            _labels(result="failure"),
        )
    )
    lines.append(
        _metric_line(
            "palvelut_media_failures_total", _shared_value("media_failure")
        )
    )
    lines.append(
        _metric_line(
            "palvelut_backup_runs_total",
            _shared_value("backup_success"),
            _labels(result="success"),
        )
    )
    lines.append(
        _metric_line(
            "palvelut_backup_runs_total",
            _shared_value("backup_failure"),
            _labels(result="failure"),
        )
    )
    return "\n".join(lines) + "\n"
