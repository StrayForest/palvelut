from __future__ import annotations

from dataclasses import dataclass
from difflib import get_close_matches

from django.conf import settings
from django.db.models import Q, QuerySet
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import translation

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.providers.models import Provider, ServiceArea
from palvelut.apps.taxonomy.models import Category, Language, Municipality

SUPPORTED_LOCALES = {code for code, _name in settings.LANGUAGES}
LAUNCH_CITIES = ("Helsinki", "Espoo", "Vantaa")


@dataclass(frozen=True)
class SearchState:
    query: str
    category: Category | None
    municipality: Municipality | None
    language_code: str
    mode: str
    invalid_explicit_filter: bool = False


def _normalize(value: str) -> str:
    return " ".join(value.casefold().split())


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
    normalized = _normalize(query)
    exact = (
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
    if exact is not None or len(normalized) < 4:
        return exact

    terms: dict[str, Category] = {}
    categories = Category.objects.prefetch_related("labels", "synonyms").order_by(
        "slug"
    )
    for category in categories:
        values = {category.slug, category.name}
        values.update(
            label.label for label in category.labels.all() if label.locale == locale
        )
        values.update(
            synonym.value
            for synonym in category.synonyms.all()
            if synonym.locale == locale
        )
        for value in values:
            term = _normalize(value)
            if len(term) >= 4:
                terms.setdefault(term, category)

    match = get_close_matches(normalized, terms.keys(), n=1, cutoff=0.82)
    return terms[match[0]] if match else None


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


def _language_code_for_query(query: str) -> str:
    if not query:
        return ""
    return (
        Language.objects.filter(code__iexact=query.strip())
        .values_list("code", flat=True)
        .first()
        or ""
    )


def _mode_for_query(query: str) -> str:
    normalized = query.strip().casefold()
    valid_modes = {choice for choice, _label in ServiceArea.Mode.choices}
    return normalized if normalized in valid_modes else ""


def _search_state(request: HttpRequest, locale: str) -> SearchState:
    query = " ".join(request.GET.get("q", "").split())
    explicit_category = request.GET.get("category", "").strip()
    category_query = explicit_category or query
    city_query = request.GET.get("city", "").strip()
    language_query = request.GET.get("language", "").strip()
    mode_query = request.GET.get("mode", "").strip() or request.GET.get(
        "service_mode", ""
    ).strip()

    category = _category_for_query(category_query, locale)
    municipality = _municipality_for_query(city_query)
    language_code = _language_code_for_query(language_query)
    mode = _mode_for_query(mode_query)
    invalid_explicit_filter = bool(
        (explicit_category and category is None)
        or (city_query and municipality is None)
        or (language_query and not language_code)
        or (mode_query and not mode)
    )
    return SearchState(
        query=query,
        category=category,
        municipality=municipality,
        language_code=language_code,
        mode=mode,
        invalid_explicit_filter=invalid_explicit_filter,
    )


def _filtered_documents(state: SearchState) -> QuerySet[ProviderReadDocument]:
    documents = _public_documents()
    if state.invalid_explicit_filter:
        return documents.none()
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

    service_area_filters: dict[str, object] = {}
    if state.municipality is not None:
        service_area_filters["provider__service_areas__municipality"] = (
            state.municipality
        )
    if state.mode:
        service_area_filters["provider__service_areas__mode"] = state.mode
    if service_area_filters:
        documents = documents.filter(**service_area_filters)

    if state.language_code:
        documents = documents.filter(
            provider__languages__language__code=state.language_code
        )
    return documents.distinct()


def _empty_alternatives(request: HttpRequest) -> list[dict[str, str]]:
    alternatives: list[dict[str, str]] = []
    labels = (
        ("mode", "Show all service modes"),
        ("service_mode", "Show all service modes"),
        ("language", "Show all languages"),
        ("city", "Search all cities"),
        ("category", "Search all categories"),
        ("q", "Browse all services"),
    )
    seen_labels: set[str] = set()
    for key, label in labels:
        if not request.GET.get(key) or label in seen_labels:
            continue
        params = request.GET.copy()
        params.pop(key, None)
        query_string = params.urlencode()
        alternatives.append(
            {
                "label": label,
                "url": request.path + (f"?{query_string}" if query_string else ""),
            }
        )
        seen_labels.add(label)
    return alternatives


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
        context.update(
            {
                "state": state,
                "documents": _filtered_documents(state),
                "empty_alternatives": _empty_alternatives(request),
                "service_modes": ServiceArea.Mode.choices,
            }
        )
        return render(request, "discovery/results.html", context)


def city_category(
    request: HttpRequest, locale: str, city: str, category: str
) -> HttpResponse:
    _require_locale(locale)
    municipality = _municipality_for_query(city.replace("-", " "))
    category_obj = Category.objects.filter(slug=category).first()
    if municipality is None or category_obj is None:
        raise Http404("Unknown city/category")
    state = SearchState(
        query="",
        category=category_obj,
        municipality=municipality,
        language_code="",
        mode="",
    )
    with translation.override(locale):
        context = _base_context(locale)
        context.update(
            {
                "state": state,
                "documents": _filtered_documents(state),
                "empty_alternatives": [],
                "service_modes": ServiceArea.Mode.choices,
            }
        )
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
