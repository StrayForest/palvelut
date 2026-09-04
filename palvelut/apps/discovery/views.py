from __future__ import annotations

import json
from dataclasses import dataclass
from difflib import get_close_matches
from xml.sax.saxutils import escape

from django.conf import settings
from django.db.models import Q, QuerySet
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils import translation

from palvelut.apps.discovery.models import ProviderReadDocument
from palvelut.apps.providers.models import Provider, ServiceArea
from palvelut.apps.publishing.models import ProviderSlug
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
    mode_query = (
        request.GET.get("mode", "").strip()
        or request.GET.get("service_mode", "").strip()
    )

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


def _localized_urls(path_suffix: str) -> tuple[list[tuple[str, str]], str]:
    links = [
        (code, f"{settings.PUBLIC_BASE_URL}/{code}/{path_suffix}")
        for code, _name in settings.LANGUAGES
    ]
    return links, f"{settings.PUBLIC_BASE_URL}/{settings.LANGUAGE_CODE}/{path_suffix}"


def _base_context(locale: str, path_suffix: str = "") -> dict[str, object]:
    links, x_default = _localized_urls(path_suffix)
    return {
        "locale": locale,
        "canonical_url": f"{settings.PUBLIC_BASE_URL}/{locale}/{path_suffix}",
        "hreflang_links": links,
        "x_default_url": x_default,
        "robots_meta": "index,follow",
        "meta_description": "Find verified service providers and contact them directly.",
        "structured_data_json": "",
    }


def _safe_json(value: dict[str, object]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace(
        "<", "\\u003c"
    )


def home(request: HttpRequest, locale: str) -> HttpResponse:
    _require_locale(locale)
    context = _base_context(locale)
    context["launch_cities"] = LAUNCH_CITIES
    with translation.override(locale):
        return render(request, "discovery/home.html", context)


def search(request: HttpRequest, locale: str) -> HttpResponse:
    _require_locale(locale)
    state = _search_state(request, locale)
    with translation.override(locale):
        context = _base_context(locale, "search/")
        context.update(
            {
                "robots_meta": "noindex,follow",
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
    documents = _filtered_documents(state)
    with translation.override(locale):
        context = _base_context(locale, f"{city}/{category}/")
        context.update(
            {
                "robots_meta": (
                    "index,follow" if documents.count() >= 3 else "noindex,follow"
                ),
                "meta_description": (
                    f"Find {category_obj.name} professionals in {municipality.name}."
                ),
                "state": state,
                "documents": documents,
                "empty_alternatives": [],
                "service_modes": ServiceArea.Mode.choices,
            }
        )
        return render(request, "discovery/results.html", context)


def provider_profile(request: HttpRequest, locale: str, slug: str) -> HttpResponse:
    _require_locale(locale)
    slug_record = (
        ProviderSlug.objects.filter(slug=slug).select_related("provider").first()
    )
    if slug_record is None:
        raise Http404("Provider not found")
    if not slug_record.is_current:
        current_slug = (
            ProviderSlug.objects.filter(provider=slug_record.provider, is_current=True)
            .values_list("slug", flat=True)
            .first()
        )
        if current_slug is None:
            raise Http404("Provider not found")
        return redirect(
            f"/palvelut/{locale}/professionals/{current_slug}/", permanent=True
        )

    document = (
        _public_documents()
        .filter(provider=slug_record.provider)
        .distinct()
        .first()
    )
    if document is None:
        raise Http404("Provider not found")
    display_name = document.document.get("display_name") or document.provider.display_name
    profile_url = f"{settings.PUBLIC_BASE_URL}/{locale}/professionals/{slug}/"
    structured_data = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": display_name,
        "url": profile_url,
    }
    with translation.override(locale):
        context = _base_context(locale, f"professionals/{slug}/")
        context.update(
            {
                "document": document,
                "meta_description": document.document.get("about")
                or f"Contact {display_name} directly through Finrix Palvelut.",
                "structured_data_json": _safe_json(structured_data),
            }
        )
        return render(request, "discovery/provider_profile.html", context)


def robots_txt(request: HttpRequest) -> HttpResponse:
    body = "\n".join(
        (
            "User-agent: *",
            "Disallow: /palvelut/*/search/",
            "Disallow: /admin/",
            f"Sitemap: {settings.PUBLIC_BASE_URL}/sitemap.xml",
            "",
        )
    )
    return HttpResponse(body, content_type="text/plain; charset=utf-8")


def sitemap_xml(request: HttpRequest) -> HttpResponse:
    documents = list(_public_documents())
    entries: dict[str, str] = {}
    for code, _name in settings.LANGUAGES:
        entries[f"{settings.PUBLIC_BASE_URL}/{code}/"] = ""

    landing_providers: dict[tuple[str, str], set[object]] = {}
    landing_lastmod: dict[tuple[str, str], str] = {}
    for document in documents:
        current_slug = next(
            (slug.slug for slug in document.provider.slugs.all() if slug.is_current), None
        )
        if current_slug:
            lastmod = document.generated_at.date().isoformat()
            for code, _name in settings.LANGUAGES:
                entries[
                    f"{settings.PUBLIC_BASE_URL}/{code}/professionals/{current_slug}/"
                ] = lastmod
        categories = {
            service.category.slug
            for service in document.provider.services.all()
            if service.is_active
        }
        cities = {
            area.municipality.name
            for area in document.provider.service_areas.all()
        }
        for city_name in cities:
            city_slug = city_name.casefold().replace(" ", "-")
            for category_slug in categories:
                key = (city_slug, category_slug)
                landing_providers.setdefault(key, set()).add(document.provider_id)
                landing_lastmod[key] = max(
                    landing_lastmod.get(key, ""),
                    document.generated_at.date().isoformat(),
                )

    for (city_slug, category_slug), provider_ids in landing_providers.items():
        if len(provider_ids) < 3:
            continue
        for code, _name in settings.LANGUAGES:
            entries[
                f"{settings.PUBLIC_BASE_URL}/{code}/{city_slug}/{category_slug}/"
            ] = landing_lastmod[(city_slug, category_slug)]

    urls = []
    for location, lastmod in sorted(entries.items()):
        lastmod_xml = f"<lastmod>{lastmod}</lastmod>" if lastmod else ""
        urls.append(f"<url><loc>{escape(location)}</loc>{lastmod_xml}</url>")
    body = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(urls)
        + "</urlset>"
    )
    return HttpResponse(body, content_type="application/xml; charset=utf-8")
