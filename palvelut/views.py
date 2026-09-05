from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import translation

from palvelut.observability import prometheus_payload

SUPPORTED_LOCALES = {code for code, _name in settings.LANGUAGES}


def public_mount_root(request):
    return redirect("localized-home", locale=settings.LANGUAGE_CODE)


def localized_home(request, locale: str):
    if locale not in SUPPORTED_LOCALES:
        raise Http404("Unsupported locale")

    canonical_url = f"{settings.PUBLIC_BASE_URL}/{locale}/"
    hreflang_links = [
        (code, f"{settings.PUBLIC_BASE_URL}/{code}/")
        for code, _name in settings.LANGUAGES
    ]
    x_default_url = f"{settings.PUBLIC_BASE_URL}/{settings.LANGUAGE_CODE}/"

    with translation.override(locale):
        return render(
            request,
            "home.html",
            {
                "locale": locale,
                "canonical_url": canonical_url,
                "hreflang_links": hreflang_links,
                "x_default_url": x_default_url,
            },
        )


def _health_response(status: str, *, http_status: int = 200) -> JsonResponse:
    response = JsonResponse({"status": status}, status=http_status)
    response["Cache-Control"] = "no-store"
    return response


def health_live(request):
    return _health_response("ok")


def health_ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        cache.set("health-ready", "ok", timeout=5)
        if cache.get("health-ready") != "ok":
            raise RuntimeError("cache readiness probe failed")
    except Exception:
        return _health_response("unavailable", http_status=503)
    return _health_response("ok")


def internal_metrics(request):
    response = HttpResponse(
        prometheus_payload(),
        content_type="text/plain; version=0.0.4; charset=utf-8",
    )
    response["Cache-Control"] = "private, no-store"
    return response
