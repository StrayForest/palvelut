from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import redirect


def public_mount_root(request):
    return redirect("localized-home", locale=settings.LANGUAGE_CODE)


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
