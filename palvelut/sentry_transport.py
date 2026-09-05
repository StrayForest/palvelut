from __future__ import annotations

import json
import threading
import time
import uuid
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from django.conf import settings


def _endpoint_and_auth(dsn: str) -> tuple[str, str] | None:
    parsed = urlsplit(dsn)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or not parsed.username:
        return None
    project_id = parsed.path.strip("/")
    if not project_id.isdigit():
        return None
    port = f":{parsed.port}" if parsed.port else ""
    endpoint = f"{parsed.scheme}://{parsed.hostname}{port}/api/{project_id}/envelope/"
    auth = (
        "Sentry sentry_version=7,"
        f"sentry_key={parsed.username},"
        "sentry_client=palvelut-stdlib/1"
    )
    return endpoint, auth


def _send(payload: bytes, endpoint: str, auth: str) -> None:
    request = Request(
        endpoint,
        data=payload,
        method="POST",
        headers={
            "Content-Type": "application/x-sentry-envelope",
            "X-Sentry-Auth": auth,
        },
    )
    try:
        with urlopen(request, timeout=1.0) as response:
            response.read(1)
    except Exception:
        # Error reporting must never alter request handling or recursively log secrets.
        return


def capture_exception(exc: BaseException, *, request_id: str | None = None) -> None:
    dsn = getattr(settings, "SENTRY_DSN", "")
    target = _endpoint_and_auth(dsn) if dsn else None
    if target is None:
        return

    event_id = uuid.uuid4().hex
    event = {
        "event_id": event_id,
        "timestamp": time.time(),
        "platform": "python",
        "environment": settings.ENVIRONMENT,
        "release": getattr(settings, "SENTRY_RELEASE", "") or None,
        "level": "error",
        "exception": {
            "values": [
                {
                    "type": type(exc).__name__,
                    "value": "Unhandled exception; correlate by request_id in private logs",
                }
            ]
        },
        "tags": {"request_id": request_id or "none"},
    }
    envelope = (
        json.dumps({"event_id": event_id}, separators=(",", ":"))
        + "\n"
        + json.dumps({"type": "event"}, separators=(",", ":"))
        + "\n"
        + json.dumps(event, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    endpoint, auth = target
    threading.Thread(
        target=_send,
        args=(envelope, endpoint, auth),
        name="sentry-envelope",
        daemon=True,
    ).start()
