from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import translation

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
