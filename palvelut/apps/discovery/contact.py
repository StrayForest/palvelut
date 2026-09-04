from __future__ import annotations

import re
from urllib.parse import urlsplit

from django.conf import settings
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import Http404, HttpRequest, HttpResponse

from palvelut.apps.analytics.models import AnalyticsEvent
from palvelut.apps.providers.models import ContactChannel, Provider

_PHONE_RE = re.compile(r"^[+0-9().\-\s]{3,40}$")
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,64}$")


def _validated_http_url(value: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise Http404("Invalid contact destination")
    return value


def _contact_destination(contact: ContactChannel) -> str:
    value = contact.value.strip()
    if not value:
        raise Http404("Invalid contact destination")

    if contact.kind == ContactChannel.Kind.PHONE:
        if not _PHONE_RE.fullmatch(value):
            raise Http404("Invalid contact destination")
        return f"tel:{value}"

    if contact.kind == ContactChannel.Kind.EMAIL:
        try:
            validate_email(value)
        except ValidationError as exc:
            raise Http404("Invalid contact destination") from exc
        return f"mailto:{value}"

    if contact.kind in {ContactChannel.Kind.WEBSITE, ContactChannel.Kind.BOOKING}:
        return _validated_http_url(value)

    if contact.kind == ContactChannel.Kind.TELEGRAM:
        if value.startswith(("http://", "https://")):
            return _validated_http_url(value)
        username = value.removeprefix("@")
        if not _USERNAME_RE.fullmatch(username):
            raise Http404("Invalid contact destination")
        return f"https://t.me/{username}"

    if contact.kind == ContactChannel.Kind.WHATSAPP:
        if value.startswith(("http://", "https://")):
            return _validated_http_url(value)
        digits = re.sub(r"\D", "", value)
        if len(digits) < 6 or len(digits) > 15:
            raise Http404("Invalid contact destination")
        return f"https://wa.me/{digits}"

    raise Http404("Unsupported contact channel")


def contact_redirect(
    request: HttpRequest,
    locale: str,
    provider_id: str,
    channel: str,
) -> HttpResponse:
    if locale not in {code for code, _name in settings.LANGUAGES}:
        raise Http404("Unsupported locale")

    contact = (
        ContactChannel.objects.select_related("provider")
        .filter(
            provider_id=provider_id,
            provider__lifecycle=Provider.Lifecycle.PUBLISHED,
            is_public=True,
            kind=channel,
        )
        .order_by("sort_order", "id")
        .first()
    )
    if contact is None:
        raise Http404("Contact channel not found")

    destination = _contact_destination(contact)
    AnalyticsEvent.objects.create(
        kind=AnalyticsEvent.Kind.CONTACT_CLICK,
        provider=contact.provider,
        channel=contact.kind,
    )
    response = HttpResponse(status=302)
    response.headers["Location"] = destination
    response.headers["Cache-Control"] = "private, no-store"
    return response
