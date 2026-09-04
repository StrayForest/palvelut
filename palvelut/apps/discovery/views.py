from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings
from django.db.models import Q, QuerySet
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import translation

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.providers.models import Provider
from palvelut.apps.taxonomy.models import Category, Municipality

SUPPORTED_LOCALES = {code for code, _name in settings.LANGUAGES}
LAUNCH_CITIES = ("Helsinki", "Espoo", "Vantaa")


@dataclass(frozen=True)
class SearchState:
    query: str
    category: Category | None
    municipality: Municipality | None


def _require_locale(locale: str) -> None:
    if locale not in SUPPORTED_LOCALES:
        raise Http404("Unsupported locale")


def _public_documents() -> QuerySet[ProviderReadDocument]:
    return (
        ProviderReadDocument.objects.filter(
            provider__lifecycle=Provider.Lifecycle.PUBLISHED
        )
        .select_related("provider", "source_revision")
        .prefetch_related(
            "provider__services__category",
            "provider__service_areas__municipality",
            "provider__languages__language",
            "provider__slugs",
        )
        .order_by("provider__display_name", "provider_id")
    )


def _category_for_query(query: str, locale: str) -> Category | None:
    if not query:
        return None
    normalized = " ".join(query.lower().split())
    return (
        Category.objects.filter(
            Q(slug=normalized)
            | Q(name__iexact=normalized)
            | Q(labels__locale=locale, labels__label__iexact=normalized)
            | Q(synonyms__locale=locale, synonyms__value__iexact=normalized)
        )
        .distinct()
        .order_by("slug")
        .first()
    )


def _municipality_for_query(query: str) -> Municipality | None:
    if not query:
        return None
    normalized = " ".join(query.split())
    return (
        Municipality.objects.filter(
            region__country__code="FI",
            name__iexact=normalized,
        )
        .order_by("code")
        .first()
    )


def _search_state(request: HttpRequest, locale: str) -> SearchState:
    query = " ".join(request.GET.get("q", "").split())
    category_query = request.GET.get("category", "").strip() or query
    city_query = request.GET.get("city", "").strip()
    return SearchState(
        query=query,
        category=_category_for_query(category_query, locale),
        municipality=_municipality_for_query(city_query),
    )


def _filtered_documents(state: SearchState) -> QuerySet[ProviderReadDocument]:
    documents = _public_documents()
    if state.category is not None:
        documents = documents.filter(
            provider__services__category=state.category,
            provider__services__is_active=True,
        )
    elif state.query:
        documents = documents.filter(
            Q(provider__display_name__icontains=state.query)
            | Q(provider__legal_name__icontains=state.query)
        )
    if state.municipality is not None:
        documents = documents.filter(
            provider__service_areas__municipality=state.municipality
        )
    return documents.distinct()


def _base_context(locale: str) -> dict[str, object]:
    return {
        "locale": locale,
        "canonical_url": None,
        "hreflang_links": [],
        "x_default_url": None,
    }


def home(request: HttpRequest, locale: str) -> HttpResponse:
    _require_locale(locale)
    context = _base_context(locale)
    context.update(
        {
            "canonical_url": f"{settings.PUBLIC_BASE_URL}/{locale}/",
            "hreflang_links": [
                (code, f"{settings.PUBLIC_BASE_URL}/{code}/")
                for code, _name in settings.LANGUAGES
            ],
            "x_default_url": f"{settings.PUBLIC_BASE_URL}/{settings.LANGUAGE_CODE}/",
            "launch_cities": LAUNCH_CITIES,
        }
    )
    with translation.override(locale):
        return render(request, "discovery/home.html", context)


def search(request: HttpRequest, locale: str) -> HttpResponse:
    _require_locale(locale)
    state = _search_state(request, locale)
    with translation.override(locale):
        context = _base_context(locale)
        context.update({"state": state, "documents": _filtered_documents(state)})
        return render(request, "discovery/results.html", context)


def city_category(
    request: HttpRequest, locale: str, city: str, category: str
) -> HttpResponse:
    _require_locale(locale)
    municipality = _municipality_for_query(city.replace("-", " "))
    category_obj = Category.objects.filter(slug=category).first()
    if municipality is None or category_obj is None:
        raise Http404("Unknown city/category")
    state = SearchState(query="", category=category_obj, municipality=municipality)
    with translation.override(locale):
        context = _base_context(locale)
        context.update({"state": state, "documents": _filtered_documents(state)})
        return render(request, "discovery/results.html", context)


def provider_profile(request: HttpRequest, locale: str, slug: str) -> HttpResponse:
    _require_locale(locale)
    document = (
        _public_documents()
        .filter(provider__slugs__slug=slug, provider__slugs__is_current=True)
        .distinct()
        .first()
    )
    if document is None:
        raise Http404("Provider not found")
    with translation.override(locale):
        context = _base_context(locale)
        context["document"] = document
        return render(request, "discovery/provider_profile.html", context)
