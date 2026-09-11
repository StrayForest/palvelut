from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import translation
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .claim_forms import NewProviderClaimForm, ProviderClaimForm, StaffClaimDecisionForm
from .claim_services import (
    CURRENT_PROVIDER_TERMS_VERSION,
    resolve_provider_claim,
    start_new_provider_claim,
    submit_provider_claim,
)
from .models import Provider

SUPPORTED_LOCALES = {code for code, _name in settings.LANGUAGES}


def for_professionals(request: HttpRequest, locale: str) -> HttpResponse:
    if locale not in SUPPORTED_LOCALES:
        raise Http404("Unsupported locale")
    hreflang_links = [
        (code, f"{settings.PUBLIC_BASE_URL}/{code}/for-professionals/")
        for code, _name in settings.LANGUAGES
    ]
    context = {
        "locale": locale,
        "canonical_url": f"{settings.PUBLIC_BASE_URL}/{locale}/for-professionals/",
        "hreflang_links": hreflang_links,
        "x_default_url": (
            f"{settings.PUBLIC_BASE_URL}/{settings.LANGUAGE_CODE}/for-professionals/"
        ),
        "robots_meta": "index,follow",
        "meta_description": "Создайте новую карточку специалиста или подтвердите существующую в Finrix Palvelut.",
    }
    with translation.override(locale):
        return render(request, "providers/for_professionals.html", context)


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def start_provider(request: HttpRequest) -> HttpResponse:
    form = NewProviderClaimForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            start_new_provider_claim(
                actor=request.user,
                provider_type=form.cleaned_data["provider_type"],
                legal_name=form.cleaned_data["legal_name"],
                display_name=form.cleaned_data["display_name"],
                y_tunnus=form.cleaned_data["y_tunnus"],
                evidence_kind=form.cleaned_data["evidence_kind"],
                evidence_reference=form.cleaned_data["evidence_reference"],
                provider_terms_accepted=form.cleaned_data["provider_terms_accepted"],
                professional_right_reference=form.cleaned_data.get(
                    "professional_right_reference", ""
                ),
                employer_authorization_reference=form.cleaned_data.get(
                    "employer_authorization_reference", ""
                ),
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            return redirect("provider-workspace")
    response = render(
        request,
        "providers/start_provider.html",
        {"form": form, "provider_terms_version": CURRENT_PROVIDER_TERMS_VERSION},
    )
    response["Cache-Control"] = "private, no-store"
    return response


@never_cache
@login_required
@require_http_methods(["GET"])
def claim_candidates(request: HttpRequest) -> HttpResponse:
    providers = Provider.objects.filter(
        lifecycle=Provider.Lifecycle.UNCLAIMED,
        claim_status__in=(
            Provider.ClaimStatus.UNCLAIMED,
            Provider.ClaimStatus.REJECTED,
        ),
    ).order_by("display_name", "id")
    return render(request, "providers/claim_candidates.html", {"providers": providers})


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def claim_provider(request: HttpRequest, provider_id) -> HttpResponse:
    provider = get_object_or_404(Provider, pk=provider_id)
    form = ProviderClaimForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            submit_provider_claim(
                provider_id=provider.pk,
                actor=request.user,
                evidence_kind=form.cleaned_data["evidence_kind"],
                evidence_reference=form.cleaned_data["evidence_reference"],
                provider_terms_accepted=form.cleaned_data["provider_terms_accepted"],
                professional_right_reference=form.cleaned_data.get(
                    "professional_right_reference", ""
                ),
                employer_authorization_reference=form.cleaned_data.get(
                    "employer_authorization_reference", ""
                ),
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            return redirect("account-claim-list")
    return render(
        request,
        "providers/claim_provider.html",
        {
            "provider": provider,
            "form": form,
            "provider_terms_version": CURRENT_PROVIDER_TERMS_VERSION,
        },
    )


@never_cache
@login_required
@require_http_methods(["GET"])
def staff_claim_list(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        raise PermissionDenied
    claims = Provider.objects.filter(
        claim_status=Provider.ClaimStatus.PENDING
    ).order_by("created_at", "id")
    return render(request, "providers/staff_claim_list.html", {"claims": claims})


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def staff_claim_review(request: HttpRequest, provider_id) -> HttpResponse:
    if not request.user.is_staff:
        raise PermissionDenied
    provider = get_object_or_404(
        Provider,
        pk=provider_id,
        claim_status=Provider.ClaimStatus.PENDING,
    )
    form = StaffClaimDecisionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            resolve_provider_claim(
                provider_id=provider.pk,
                actor=request.user,
                decision=form.cleaned_data["decision"],
                review_note=form.cleaned_data["review_note"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            return redirect("staff-claim-list")
    return render(
        request,
        "providers/staff_claim_review.html",
        {"provider": provider, "form": form},
    )
