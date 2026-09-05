from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from functools import wraps

from django.db.models import Count
from django.http import HttpRequest, HttpResponse

from palvelut.apps.analytics.models import AnalyticsEvent

_PROVIDER_MARKER_RE = re.compile(rb'data-analytics-provider="([0-9a-f-]{36})"')


def _provider_ids_from_response(response: HttpResponse) -> tuple[str, ...]:
    if not response.get("Content-Type", "").startswith("text/html"):
        return ()
    return tuple(
        dict.fromkeys(
            match.decode("ascii")
            for match in _PROVIDER_MARKER_RE.findall(response.content)
        )
    )


def track_provider_events(kind: str) -> Callable:
    """Record provider-level anonymous page events after cache resolution."""

    def decorator(view: Callable) -> Callable:
        @wraps(view)
        def wrapped(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            response = view(request, *args, **kwargs)
            if (
                request.method == "GET"
                and not request.user.is_authenticated
                and response.status_code == 200
            ):
                provider_ids = _provider_ids_from_response(response)
                AnalyticsEvent.objects.bulk_create(
                    [
                        AnalyticsEvent(kind=kind, provider_id=provider_id)
                        for provider_id in provider_ids
                    ]
                )
            return response

        return wrapped

    return decorator


def aggregate_provider_metrics(
    provider_ids: Iterable[object],
) -> dict[str, dict[str, int]]:
    ids = [str(provider_id) for provider_id in provider_ids]
    metrics = {
        provider_id: {
            AnalyticsEvent.Kind.IMPRESSION: 0,
            AnalyticsEvent.Kind.PROFILE_VIEW: 0,
            AnalyticsEvent.Kind.CONTACT_CLICK: 0,
        }
        for provider_id in ids
    }
    rows = (
        AnalyticsEvent.objects.filter(provider_id__in=ids)
        .values("provider_id", "kind")
        .annotate(total=Count("id"))
    )
    for row in rows:
        provider_id = str(row["provider_id"])
        if provider_id in metrics:
            metrics[provider_id][str(row["kind"])] = int(row["total"])
    return metrics
