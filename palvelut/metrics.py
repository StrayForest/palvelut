from __future__ import annotations

import math
import threading
import time
from collections import defaultdict
from collections.abc import Iterable

_LOCK = threading.Lock()
_COUNTERS: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
_GAUGES: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
_HISTOGRAMS: dict[tuple[str, tuple[tuple[str, str], ...]], list[float]] = defaultdict(list)

REQUEST_LATENCY_BUCKETS = (0.05, 0.1, 0.3, 0.8, 1.5, 3.0)
DB_QUERY_BUCKETS = (0.005, 0.01, 0.05, 0.1, 0.3, 1.0)
QUEUE_AGE_BUCKETS = (1.0, 5.0, 30.0, 120.0, 600.0, 3600.0)


def _labels(labels: dict[str, str] | None) -> tuple[tuple[str, str], ...]:
    if not labels:
        return ()
    return tuple(sorted((str(key), str(value)) for key, value in labels.items()))


def inc(
    name: str, *, labels: dict[str, str] | None = None, amount: float = 1.0
) -> None:
    with _LOCK:
        _COUNTERS[(name, _labels(labels))] += amount


def set_gauge(
    name: str, value: float, *, labels: dict[str, str] | None = None
) -> None:
    with _LOCK:
        _GAUGES[(name, _labels(labels))] = value


def adjust_gauge(
    name: str, amount: float, *, labels: dict[str, str] | None = None
) -> None:
    with _LOCK:
        key = (name, _labels(labels))
        _GAUGES[key] = max(0.0, _GAUGES[key] + amount)


def observe(
    name: str, value: float, *, labels: dict[str, str] | None = None
) -> None:
    with _LOCK:
        _HISTOGRAMS[(name, _labels(labels))].append(value)


def record_request(method: str, status: int, duration_seconds: float) -> None:
    status_class = f"{status // 100}xx"
    labels = {"method": method.upper(), "status_class": status_class}
    inc("palvelut_http_requests_total", labels=labels)
    observe("palvelut_http_request_duration_seconds", duration_seconds, labels=labels)
    if status >= 500:
        inc("palvelut_http_5xx_total", labels={"method": method.upper()})


def record_cache(result: str) -> None:
    if result not in {"hit", "miss", "bypass"}:
        raise ValueError("cache result must be hit, miss or bypass")
    inc("palvelut_cache_requests_total", labels={"result": result})


def record_db_query(duration_seconds: float) -> None:
    observe("palvelut_db_query_duration_seconds", duration_seconds)
    if duration_seconds >= 0.3:
        inc("palvelut_db_slow_queries_total")


def record_queue(*, age_seconds: float | None = None, failed: bool = False) -> None:
    if age_seconds is not None:
        observe("palvelut_queue_age_seconds", max(0.0, age_seconds))
    if failed:
        inc("palvelut_queue_failures_total")


def record_email(*, delivered: bool) -> None:
    inc(
        "palvelut_email_delivery_total",
        labels={"result": "delivered" if delivered else "failed"},
    )


def record_media_failure() -> None:
    inc("palvelut_media_failures_total")


def record_backup(*, succeeded: bool, completed_at: float | None = None) -> None:
    if succeeded:
        set_gauge(
            "palvelut_backup_last_success_timestamp_seconds",
            completed_at if completed_at is not None else time.time(),
        )
    else:
        inc("palvelut_backup_failures_total")


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _format_labels(
    labels: tuple[tuple[str, str], ...],
    extra: Iterable[tuple[str, str]] = (),
) -> str:
    pairs = [*labels, *extra]
    if not pairs:
        return ""
    return "{" + ",".join(f'{key}="{_escape(value)}"' for key, value in pairs) + "}"


def _histogram_buckets(name: str) -> tuple[float, ...]:
    if name == "palvelut_http_request_duration_seconds":
        return REQUEST_LATENCY_BUCKETS
    if name == "palvelut_db_query_duration_seconds":
        return DB_QUERY_BUCKETS
    if name == "palvelut_queue_age_seconds":
        return QUEUE_AGE_BUCKETS
    return (0.1, 0.5, 1.0, 5.0)


def render_prometheus() -> str:
    lines: list[str] = []
    with _LOCK:
        counters = list(_COUNTERS.items())
        gauges = list(_GAUGES.items())
        histograms = [(key, values[:]) for key, values in _HISTOGRAMS.items()]

    for (name, labels), value in sorted(counters):
        lines.append(f"# TYPE {name} counter")
        lines.append(f"{name}{_format_labels(labels)} {value:g}")
    for (name, labels), value in sorted(gauges):
        lines.append(f"# TYPE {name} gauge")
        lines.append(f"{name}{_format_labels(labels)} {value:g}")
    for (name, labels), values in sorted(histograms):
        lines.append(f"# TYPE {name} histogram")
        for upper in _histogram_buckets(name):
            count = sum(1 for value in values if value <= upper)
            lines.append(
                f'{name}_bucket{_format_labels(labels, (("le", f"{upper:g}"),))} {count}'
            )
        lines.append(
            f'{name}_bucket{_format_labels(labels, (("le", "+Inf"),))} {len(values)}'
        )
        lines.append(f"{name}_count{_format_labels(labels)} {len(values)}")
        lines.append(f"{name}_sum{_format_labels(labels)} {math.fsum(values):g}")
    return "\n".join(lines) + ("\n" if lines else "")
