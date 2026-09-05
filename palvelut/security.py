from __future__ import annotations

import secrets

from django.http import HttpRequest, HttpResponse


class SecurityHeadersMiddleware:
    """Apply the P4 browser-security header baseline without a runtime dependency."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        nonce = secrets.token_urlsafe(18)
        request.csp_nonce = nonce
        response = self.get_response(request)

        response.headers.setdefault(
            "Content-Security-Policy",
            "; ".join(
                (
                    "default-src 'self'",
                    "base-uri 'self'",
                    "form-action 'self'",
                    "frame-ancestors 'none'",
                    "object-src 'none'",
                    f"script-src 'self' 'nonce-{nonce}'",
                    "style-src 'self'",
                    "style-src-elem 'self'",
                    "style-src-attr 'unsafe-inline'",
                    "img-src 'self' data:",
                    "font-src 'self'",
                    "connect-src 'self'",
                    "manifest-src 'self'",
                    "media-src 'self'",
                    "worker-src 'self'",
                )
            ),
        )
        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), geolocation=(), microphone=(), payment=(), usb=()",
        )
        return response
