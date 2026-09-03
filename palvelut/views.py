from django.conf import settings
from django.http import Http404
from django.shortcuts import render
from django.utils import translation

SUPPORTED_LOCALES = {code for code, _name in settings.LANGUAGES}


def localized_home(request, locale: str):
    if locale not in SUPPORTED_LOCALES:
        raise Http404("Unsupported locale")
    with translation.override(locale):
        return render(request, "home.html", {"locale": locale})
