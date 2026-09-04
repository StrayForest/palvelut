from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

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
TYPO_MATCH_THRESHOLD = 0.78


@dataclass(frozen=True)
class SearchState:
    query: str
    category: Category | None
    municipality: Municipality | None
    language: Language | None
    mode: str
    invalid_filter: bool = False


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


def _normalize_query(value: str) -> str:
    return " ".join(value.lower().split())


def _category_for_query(query: str, locale: str) -> Category | None:
    if not query:
        return None
    normalized = _normalize_query(query)
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
    if exact is not None:
        return exact

    candidates = Category.objects.prefetch_related("labels", "synonyms").order_by(
        "slug"
    )
    best_category: Category | None = None
    best_score = 0.0
    for category in candidates:
        values = {category.slug, category.name}
        values.update(
            label.label for label in category.labels.all() if label.locale == locale
        )
        values.update(
            synonym.value
            for synonym in category.synonyms.all()
            if synonym.locale == locale
        )
        score = max(
            (
                SequenceMatcher(None, normalized, _normalize_query(value)).ratio()
                for value in values
            ),
            default=0.0,
        )
        if score > best_score:
            best_category = category
            best_score = score
    if best_score >= TYPO_MATCH_THRESHOLD:
        return best_category
    return None


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


def _language_for_query(query: str) -> Language | None:
    if not query:
        return None
    normalized = _normalize_query(query)
    return (
        Language.objects.filter(
            Q(code__iexact=normalized) | Q(name__iexact=normalized)
        )
        .order_by("code")
        .first()
    )


def _search_state(request: HttpRequest, locale: str) -> SearchState:
    query = " ".join(request.GET.get("q", "").split())
    explicit_category = request.GET.get("category", "").strip()
    category_query = explicit_category or query
    city_query = request.GET.get("city", "").strip()
    language_query = request.GET.get("language", "").strip()
    mode_query = request.GET.get("mode", "").strip().lower()
    category = _category_for_query(category_query, locale)
    municipality = _municipality_for_query(city_query)
    language = _language_for_query(language_query)
    valid_modes = {choice for choice, _label in ServiceArea.Mode.choices}
    invalid_filter = bool(
        (explicit_category and category is None)
        or (city_query and municipality is None)
        or (language_query and language is None)
        or (mode_query and mode_query not in valid_modes)
    )
    return SearchState(
        query=query,
        category=category,
        municipality=municipality,
        language=language,
        mode=mode_query if mode_query in valid_modes else "",
        invalid_filter=invalid_filter,
    )


def _filtered_documents(state: SearchState) -> QuerySet[ProviderReadDocument]:
    documents = _public_documents()
    if state.invalid_filter:
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
    if state.municipality is not None:
        documents = documents.filter(
            provider__service_areas__municipality=state.municipality
        )
    if state.language is not None:
        documents = documents.filter(
            provider__languages__language=state.language,
            provider__languages__declared=True,
        )
    if state.mode:
        documents = documents.filter(provider__service_areas__mode=state.mode)
    return documents.distinct()


def _alternative_cities(state: SearchState) -> list[str]:
    if state.invalid_filter:
        return []
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
    if state.language is not None:
        documents = documents.filter(
            provider__languages__language=state.language,
            provider__languages__declared=True,
        )
    if state.mode:
        documents = documents.filter(provider__service_areas__mode=state.mode)
    return list(
        documents.values_list(
            "provider__service_areas__municipality__name", flat=True
        )
        .exclude(provider__service_areas__municipality__isnull=True)
        .distinct()
        .order_by("provider__service_areas__municipality__name")[:5]
    )


def _base_context(locale: str) -> dict[str, object]:
    return {
        "locale": locale,
        "canonical_url": None,
        "hreflang_links": [],
        "x_default_url": None,
    }


def _filter_context() -> dict[str, object]:
    return {
        "filter_categories": Category.objects.all().order_by("name"),
        "filter_languages": Language.objects.all().order_by("name"),
        "service_modes": ServiceArea.Mode.choices,
        "launch_cities": LAUNCH_CITIES,
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
    documents = _filtered_documents(state)
    with translation.override(locale):
        context = _base_context(locale)
        context.update(_filter_context())
        context.update(
            {
                "state": state,
                "documents": documents,
                "alternative_cities": (
                    _alternative_cities(state) if not documents.exists() else []
                ),
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
        language=None,
        mode="",
    )
    with translation.override(locale):
        context = _base_context(locale)
        context.update(_filter_context())
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
