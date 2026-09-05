from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import translation

from .presentation import TRUST_EXPLANATION

SUPPORTED_LOCALES = {code for code, _name in settings.LANGUAGES}


def trust(request: HttpRequest, locale: str) -> HttpResponse:
    if locale not in SUPPORTED_LOCALES:
        raise Http404("Unsupported locale")
    with translation.override(locale):
        return render(
            request,
            "verification/trust.html",
            {
                "locale": locale,
                "trust_explanation": TRUST_EXPLANATION,
                "canonical_url": f"{settings.PUBLIC_BASE_URL}/{locale}/trust/",
                "robots_meta": "index,follow",
                "meta_description": "How Finrix Palvelut verification facts are checked and displayed.",
            },
        )
