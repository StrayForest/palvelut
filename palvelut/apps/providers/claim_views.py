from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .claim_forms import ProviderClaimForm, StaffClaimDecisionForm
from .claim_services import resolve_provider_claim, submit_provider_claim
from .models import Provider


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
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            return redirect("account-claim-list")
    return render(
        request,
        "providers/claim_provider.html",
        {"provider": provider, "form": form},
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
