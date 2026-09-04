from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from hashlib import sha256
from typing import ParamSpec

from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.utils.cache import patch_vary_headers

P = ParamSpec("P")

CachedPayload = tuple[int, bytes, str]


def _cache_key(request: HttpRequest, namespace: str) -> str:
    digest = sha256(request.get_full_path().encode("utf-8")).hexdigest()
    return f"discovery:{namespace}:{digest}"


def _cache_control(*, shared_max_age: int | None, stale_while_revalidate: int) -> str:
    if shared_max_age is None:
        return "public, max-age=0, s-maxage=0"
    directives = ["public", "max-age=0", f"s-maxage={shared_max_age}"]
    if stale_while_revalidate:
        directives.append(f"stale-while-revalidate={stale_while_revalidate}")
    return ", ".join(directives)


def _private_response(response: HttpResponse) -> HttpResponse:
    response["Cache-Control"] = "private, no-store"
    patch_vary_headers(response, ("Cookie",))
    return response


def public_read_through_cache(
    *,
    namespace: str,
    application_ttl: int,
    shared_max_age: int | None,
    stale_while_revalidate: int = 0,
) -> Callable[[Callable[P, HttpResponse]], Callable[P, HttpResponse]]:
    """Cache anonymous GET responses while bypassing cache for authenticated users."""

    def decorator(view: Callable[P, HttpResponse]) -> Callable[P, HttpResponse]:
        @wraps(view)
        def wrapped(*args: P.args, **kwargs: P.kwargs) -> HttpResponse:
            request = args[0]
            if not isinstance(request, HttpRequest):
                raise TypeError("cached discovery views must receive HttpRequest first")

            if request.method not in {"GET", "HEAD"} or request.user.is_authenticated:
                return _private_response(view(*args, **kwargs))

            key = _cache_key(request, namespace)
            payload = cache.get(key)
            if payload is None:
                response = view(*args, **kwargs)
                if response.status_code != 200:
                    return response
                payload = (
                    response.status_code,
                    bytes(response.content),
                    response.get("Content-Type", "text/html; charset=utf-8"),
                )
                cache.set(key, payload, timeout=application_ttl)
            else:
                status, content, content_type = payload
                response = HttpResponse(content, status=status, content_type=content_type)

            response["Cache-Control"] = _cache_control(
                shared_max_age=shared_max_age,
                stale_while_revalidate=stale_while_revalidate,
            )
            return response

        return wrapped

    return decorator
