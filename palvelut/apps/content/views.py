from django.conf import settings
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

LEGAL_DOCUMENTS = {
    "privacy": "Конфиденциальность",
    "terms": "Условия для специалистов",
    "cookies": "Политика файлов cookie",
    "accessibility": "Заявление о доступности",
}
SUPPORTED_LOCALES = {code for code, _name in settings.LANGUAGES}


@cache_control(public=True, max_age=3600)
@require_GET
def legal_document(request: HttpRequest, locale: str, document: str) -> HttpResponse:
    if locale not in SUPPORTED_LOCALES:
        raise Http404("Unsupported locale")
    title = LEGAL_DOCUMENTS.get(document)
    if title is None:
        raise Http404
    return render(
        request,
        "legal/document.html",
        {
            "document": document,
            "document_title": title,
            "locale": locale,
            "robots_meta": "index,follow",
        },
    )
