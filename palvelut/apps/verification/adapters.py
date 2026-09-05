from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Callable, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

PRH_YTJ_API_URL = "https://avoindata.prh.fi/opendata-ytj-api/v3/companies"
PRH_YTJ_SOURCE = "PRH YTJ Open Data API v3"
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_TIMEOUT_SECONDS = 4.0


class RegistryOutcome(StrEnum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    MANUAL_REVIEW = "manual_review"


@dataclass(frozen=True)
class TransportResponse:
    status_code: int
    payload: object


class RegistryTransport(Protocol):
    def get_json(self, url: str, *, timeout_seconds: float) -> TransportResponse: ...


class _NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


class UrlLibRegistryTransport:
    """Small HTTPS-only transport for the fixed PRH API origin."""

    def __init__(self) -> None:
        self._opener = build_opener(_NoRedirectHandler())

    def get_json(self, url: str, *, timeout_seconds: float) -> TransportResponse:
        if not url.startswith(f"{PRH_YTJ_API_URL}?"):
            raise ValueError(
                "Registry transport only permits the configured PRH YTJ endpoint"
            )
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "finrix-palvelut/1",
            },
        )
        with self._opener.open(request, timeout=timeout_seconds) as response:
            if response.geturl() != url:
                raise ValueError("Registry redirects are not permitted")
            body = response.read()
            return TransportResponse(
                status_code=response.status,
                payload=json.loads(body.decode("utf-8")),
            )


@dataclass(frozen=True)
class RegistryLookupResult:
    outcome: RegistryOutcome
    business_id: str
    source_url: str
    fetched_at: datetime
    attempts: int
    status_code: int | None
    source_snapshot: object | None
    error: str = ""

    def evidence_metadata(self) -> dict[str, object]:
        return {
            "source": PRH_YTJ_SOURCE,
            "business_id": self.business_id,
            "fetched_at": self.fetched_at.isoformat(),
            "attempts": self.attempts,
            "http_status": self.status_code,
            "outcome": self.outcome.value,
            "manual_fallback_required": self.outcome == RegistryOutcome.MANUAL_REVIEW,
            "source_snapshot": self.source_snapshot,
            "error": self.error,
        }


def _business_ids(payload: object) -> set[str]:
    found: set[str] = set()

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"businessId", "business_id"} and isinstance(child, str):
                    found.add(child.strip())
                else:
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(payload)
    return found


class YtjPrhAdapter:
    def __init__(
        self,
        *,
        transport: RegistryTransport | None = None,
        max_attempts: int = DEFAULT_MAX_ATTEMPTS,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if not 1 <= max_attempts <= DEFAULT_MAX_ATTEMPTS:
            raise ValueError(f"max_attempts must be between 1 and {DEFAULT_MAX_ATTEMPTS}")
        if not 0 < timeout_seconds <= DEFAULT_TIMEOUT_SECONDS:
            raise ValueError(
                f"timeout_seconds must be between 0 and {DEFAULT_TIMEOUT_SECONDS}"
            )
        self.transport = transport or UrlLibRegistryTransport()
        self.max_attempts = max_attempts
        self.timeout_seconds = timeout_seconds
        self.sleep = sleep

    def lookup_business_id(self, business_id: str) -> RegistryLookupResult:
        normalized = business_id.strip()
        if not normalized:
            raise ValueError("business_id is required")

        source_url = f"{PRH_YTJ_API_URL}?{urlencode({'businessId': normalized})}"
        last_status: int | None = None
        last_snapshot: object | None = None
        last_error = ""

        for attempt in range(1, self.max_attempts + 1):
            try:
                response = self.transport.get_json(
                    source_url,
                    timeout_seconds=self.timeout_seconds,
                )
                last_status = response.status_code
                last_snapshot = response.payload

                if response.status_code == 200:
                    outcome = (
                        RegistryOutcome.FOUND
                        if normalized in _business_ids(response.payload)
                        else RegistryOutcome.NOT_FOUND
                    )
                    return RegistryLookupResult(
                        outcome=outcome,
                        business_id=normalized,
                        source_url=source_url,
                        fetched_at=datetime.now(timezone.utc),
                        attempts=attempt,
                        status_code=response.status_code,
                        source_snapshot=response.payload,
                    )

                if response.status_code not in {429, 500, 502, 503, 504}:
                    last_error = (
                        f"Unexpected upstream HTTP status {response.status_code}"
                    )
                    break
                last_error = f"Transient upstream HTTP status {response.status_code}"
            except HTTPError as exc:
                last_status = exc.code
                last_error = f"Upstream HTTP error {exc.code}"
                if exc.code not in {429, 500, 502, 503, 504}:
                    break
            except (
                TimeoutError,
                URLError,
                OSError,
                ValueError,
                json.JSONDecodeError,
            ) as exc:
                last_error = f"Upstream request failed: {exc.__class__.__name__}"

            if attempt < self.max_attempts:
                self.sleep(0.1 * attempt)

        return RegistryLookupResult(
            outcome=RegistryOutcome.MANUAL_REVIEW,
            business_id=normalized,
            source_url=source_url,
            fetched_at=datetime.now(timezone.utc),
            attempts=min(self.max_attempts, attempt),
            status_code=last_status,
            source_snapshot=last_snapshot,
            error=last_error or "Registry lookup did not complete",
        )
