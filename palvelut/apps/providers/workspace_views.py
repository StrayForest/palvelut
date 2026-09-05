from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from palvelut.apps.providers.models import ProviderMembership
from palvelut.apps.providers.workspace_forms import ProviderProfileForm
from palvelut.apps.providers.workspace_services import (
    autosave_revision,
    editable_revision,
    submit_revision,
)


def _membership_for_request(request, provider_id):
    membership = (
        ProviderMembership.objects.filter(
            provider_id=provider_id,
            account=request.user,
            is_active=True,
        )
        .select_related("provider")
        .first()
    )
    if membership is None:
        raise Http404
    return membership


@login_required
@require_http_methods(["GET"])
def workspace(request):
    memberships = ProviderMembership.objects.filter(
        account=request.user,
        is_active=True,
    ).select_related("provider")
    return render(request, "providers/workspace.html", {"memberships": memberships})


@login_required
@require_http_methods(["GET", "POST"])
def edit_profile(request, provider_id):
    membership = _membership_for_request(request, provider_id)
    revision = editable_revision(provider=membership.provider, account=request.user)
    form = ProviderProfileForm(
        request.POST or None,
        initial=revision.payload,
    )
    if request.method == "POST":
        if not form.is_valid():
            return render(
                request,
                "providers/edit_profile.html",
                {
                    "provider": membership.provider,
                    "revision": revision,
                    "form": form,
                },
                status=400,
            )
        revision = autosave_revision(
            provider_id=provider_id,
            account=request.user,
            payload=form.cleaned_payload(),
        )
        if request.headers.get("HX-Request") == "true":
            return HttpResponse(
                "Saved", headers={"HX-Trigger": "providerDraftSaved"}
            )
        return redirect("provider-workspace-edit", provider_id=provider_id)
    return render(
        request,
        "providers/edit_profile.html",
        {"provider": membership.provider, "revision": revision, "form": form},
    )


@login_required
@require_http_methods(["GET"])
def preview_profile(request, provider_id):
    membership = _membership_for_request(request, provider_id)
    revision = editable_revision(provider=membership.provider, account=request.user)
    return render(
        request,
        "providers/preview_profile.html",
        {
            "provider": membership.provider,
            "payload": revision.payload,
            "revision": revision,
        },
    )


@login_required
@require_POST
def submit_profile(request, provider_id):
    _membership_for_request(request, provider_id)
    try:
        submit_revision(provider_id=provider_id, account=request.user)
    except (PermissionDenied, ValidationError) as exc:
        return HttpResponseBadRequest(str(exc))
    return redirect(reverse("provider-workspace") + "?submitted=1")
