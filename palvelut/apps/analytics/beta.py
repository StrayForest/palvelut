from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections import defaultdict
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core import signing
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.utils import timezone

from palvelut.apps.analytics.models import BetaDecisionSnapshot, BetaFunnelEvent
from palvelut.apps.providers.models import Provider

BETA_SCHEMA_VERSION = "p6-beta-schema-v1"
BETA_METRIC_VERSION = "p6-beta-metrics-v1"
BETA_BOT_RULE_VERSION = "p6-beta-bots-v1"
BETA_DISCOVERY_KIND = "discovery_view"
BETA_SEARCH_KIND = "search"
BETA_CONTACT_KIND = "contact"
BETA_SESSION_COOKIE = "palvelut_beta_session"
BETA_SESSION_SECONDS = 30 * 60
BETA_WINDOW_DAYS = 30
_TOKEN_SALT = "palvelut.beta.analytics.v1"
_BOT_UA_PATTERNS = (
    re.compile(r"\b(bot|crawler|spider|slurp)\b", re.IGNORECASE),
    re.compile(r"(googlebot|bingbot|duckduckbot|yandexbot|baiduspider)", re.IGNORECASE),
)


def signed_event_token(
    kind: str,
    *,
    provider_id: object | None = None,
    search_had_results: bool | None = None,
) -> str:
    payload: dict[str, Any] = {"kind": kind}
    if provider_id is not None:
        payload["provider_id"] = str(provider_id)
    if search_had_results is not None:
        payload["search_had_results"] = bool(search_had_results)
    return signing.dumps(payload, salt=_TOKEN_SALT, compress=True)


def _country_code(request: HttpRequest) -> str:
    value = request.headers.get("CF-IPCountry", "").strip().upper()
    if re.fullmatch(r"[A-Z]{2}", value):
        return value
    if settings.ENVIRONMENT in {"local", "test"}:
        return "FI"
    return "ZZ"


def _is_bot(request: HttpRequest) -> bool:
    verified = request.headers.get("X-Palvelut-Verified-Bot", "").strip().lower()
    if verified in {"1", "true", "yes"}:
        return True
    user_agent = request.headers.get("User-Agent", "")[:512]
    return any(pattern.search(user_agent) for pattern in _BOT_UA_PATTERNS)


def _session_id(request: HttpRequest) -> uuid.UUID:
    raw = request.COOKIES.get(BETA_SESSION_COOKIE, "")
    try:
        return uuid.UUID(raw)
    except (ValueError, TypeError, AttributeError):
        return uuid.uuid4()


def _refresh_session_cookie(response: HttpResponse, session_id: uuid.UUID) -> None:
    response.set_cookie(
        BETA_SESSION_COOKIE,
        str(session_id),
        max_age=BETA_SESSION_SECONDS,
        path=settings.PUBLIC_MOUNT_PATH,
        secure=settings.ENVIRONMENT in {"staging", "production"},
        httponly=True,
        samesite="Lax",
    )


def collect_beta_event(request: HttpRequest, token: str) -> HttpResponse:
    response = HttpResponse(status=204)
    response["Cache-Control"] = "private, no-store"
    if request.method != "GET" or request.user.is_authenticated or _is_bot(request):
        return response

    try:
        payload = signing.loads(token, salt=_TOKEN_SALT, max_age=24 * 60 * 60)
    except signing.BadSignature:
        return response

    kind = payload.get("kind")
    if kind not in {BETA_DISCOVERY_KIND, BETA_SEARCH_KIND}:
        return response

    provider = None
    provider_id = payload.get("provider_id")
    if provider_id:
        provider = Provider.objects.filter(pk=provider_id).first()
        if provider is None:
            return response

    search_had_results = payload.get("search_had_results")
    if kind == BETA_SEARCH_KIND:
        if not isinstance(search_had_results, bool):
            return response
    else:
        search_had_results = None

    session_id = _session_id(request)
    BetaFunnelEvent.objects.create(
        session_id=session_id,
        kind=kind,
        provider=provider,
        country_code=_country_code(request),
        search_had_results=search_had_results,
        schema_version=BETA_SCHEMA_VERSION,
        metric_version=BETA_METRIC_VERSION,
        bot_rule_version=BETA_BOT_RULE_VERSION,
    )
    _refresh_session_cookie(response, session_id)
    return response


def record_beta_contact(
    request: HttpRequest,
    response: HttpResponse,
    *,
    provider: Provider,
    channel: str,
) -> None:
    if request.user.is_authenticated or _is_bot(request):
        return
    session_id = _session_id(request)
    cutoff = timezone.now() - timedelta(seconds=BETA_SESSION_SECONDS)
    duplicate = BetaFunnelEvent.objects.filter(
        session_id=session_id,
        kind=BETA_CONTACT_KIND,
        provider=provider,
        channel=channel,
        occurred_at__gte=cutoff,
        schema_version=BETA_SCHEMA_VERSION,
        metric_version=BETA_METRIC_VERSION,
        bot_rule_version=BETA_BOT_RULE_VERSION,
    ).exists()
    if not duplicate:
        BetaFunnelEvent.objects.create(
            session_id=session_id,
            kind=BETA_CONTACT_KIND,
            provider=provider,
            channel=channel,
            country_code=_country_code(request),
            schema_version=BETA_SCHEMA_VERSION,
            metric_version=BETA_METRIC_VERSION,
            bot_rule_version=BETA_BOT_RULE_VERSION,
        )
    _refresh_session_cookie(response, session_id)


def current_beta_events(*, window_end=None) -> QuerySet[BetaFunnelEvent]:
    window_end = window_end or timezone.now()
    window_start = window_end - timedelta(days=BETA_WINDOW_DAYS)
    return BetaFunnelEvent.objects.filter(
        occurred_at__gte=window_start,
        occurred_at__lte=window_end,
        country_code="FI",
        schema_version=BETA_SCHEMA_VERSION,
        metric_version=BETA_METRIC_VERSION,
        bot_rule_version=BETA_BOT_RULE_VERSION,
    ).order_by("occurred_at", "id")


def reconcile_beta_snapshot(*, window_end=None) -> BetaDecisionSnapshot:
    window_end = window_end or timezone.now()
    window_start = window_end - timedelta(days=BETA_WINDOW_DAYS)
    rows = list(
        current_beta_events(window_end=window_end).values(
            "id",
            "session_id",
            "kind",
            "provider_id",
            "channel",
            "search_had_results",
            "occurred_at",
        )
    )

    discovery_sessions: set[uuid.UUID] = set()
    search_sessions: set[uuid.UUID] = set()
    search_sessions_with_contact: set[uuid.UUID] = set()
    search_events = 0
    zero_result_searches = 0
    by_session: dict[uuid.UUID, list[dict[str, Any]]] = defaultdict(list)

    checksum_rows = []
    for row in rows:
        session_id = row["session_id"]
        by_session[session_id].append(row)
        if row["kind"] in {BETA_DISCOVERY_KIND, BETA_SEARCH_KIND}:
            discovery_sessions.add(session_id)
        if row["kind"] == BETA_SEARCH_KIND:
            search_sessions.add(session_id)
            search_events += 1
            if row["search_had_results"] is False:
                zero_result_searches += 1
        checksum_rows.append(
            (
                str(row["id"]),
                str(session_id),
                row["kind"],
                str(row["provider_id"] or ""),
                row["channel"],
                row["search_had_results"],
                row["occurred_at"].isoformat(),
            )
        )

    for session_id, events in by_session.items():
        first_search = next(
            (
                event["occurred_at"]
                for event in events
                if event["kind"] == BETA_SEARCH_KIND
            ),
            None,
        )
        if first_search is not None and any(
            event["kind"] == BETA_CONTACT_KIND and event["occurred_at"] >= first_search
            for event in events
        ):
            search_sessions_with_contact.add(session_id)

    contact_bps = (
        round(len(search_sessions_with_contact) * 10_000 / len(search_sessions))
        if search_sessions
        else 0
    )
    zero_bps = (
        round(zero_result_searches * 10_000 / search_events) if search_events else 0
    )
    checksum = hashlib.sha256(
        json.dumps(checksum_rows, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()

    return BetaDecisionSnapshot.objects.create(
        window_start=window_start,
        window_end=window_end,
        schema_version=BETA_SCHEMA_VERSION,
        metric_version=BETA_METRIC_VERSION,
        bot_rule_version=BETA_BOT_RULE_VERSION,
        raw_event_count=len(rows),
        finland_discovery_sessions=len(discovery_sessions),
        search_sessions=len(search_sessions),
        search_sessions_with_contact=len(search_sessions_with_contact),
        search_events=search_events,
        zero_result_searches=zero_result_searches,
        contact_conversion_basis_points=contact_bps,
        zero_result_basis_points=zero_bps,
        source_checksum=checksum,
    )
