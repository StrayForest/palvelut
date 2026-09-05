from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_GET

LEGAL_DOCUMENTS = {
    "privacy": "Privacy notice",
    "terms": "Provider terms",
    "cookies": "Cookie policy",
    "accessibility": "Accessibility statement",
}


@cache_control(public=True, max_age=3600)
@require_GET
def legal_document(request: HttpRequest, locale: str, document: str) -> HttpResponse:
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
