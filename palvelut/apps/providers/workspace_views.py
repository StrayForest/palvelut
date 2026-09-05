from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from palvelut.apps.analytics.services import aggregate_provider_metrics
from palvelut.apps.providers.models import ProviderMembership
from palvelut.apps.providers.workspace_forms import ProviderProfileForm
from palvelut.apps.providers.workspace_services import (
    autosave_revision,
    editable_revision,
    stage_media_upload,
    submit_revision,
)
from palvelut.apps.publishing.models import ProfileRevision


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


def _dashboard_payload(provider):
    revision = (
        ProfileRevision.objects.filter(
            provider=provider,
            status__in=(
                ProfileRevision.Status.DRAFT,
                ProfileRevision.Status.PENDING,
                ProfileRevision.Status.CHANGES_REQUESTED,
            ),
        )
        .order_by("-created_at", "-id")
        .first()
    )
    if revision is not None:
        return dict(revision.payload), revision
    return (
        {
            "provider_type": provider.provider_type,
            "legal_name": provider.legal_name,
            "display_name": provider.display_name,
            "contacts": [
                {"value": contact.value, "is_public": contact.is_public}
                for contact in provider.contacts.all()
            ],
            "services": [
                {"is_active": service.is_active} for service in provider.services.all()
            ],
            "service_areas": [{} for _area in provider.service_areas.all()],
            "languages": [{} for _language in provider.languages.all()],
            "media": [{} for _media in provider.media_assets.all()],
        },
        None,
    )


def _completion_checklist(payload):
    contacts = payload.get("contacts") or []
    services = payload.get("services") or []
    checks = (
        (
            "Identity",
            all(
                payload.get(field)
                for field in ("provider_type", "legal_name", "display_name")
            ),
        ),
        ("Service", any(item.get("is_active", True) for item in services)),
        ("Service area", bool(payload.get("service_areas"))),
        ("Language", bool(payload.get("languages"))),
        (
            "Public contact",
            any(item.get("is_public", True) and item.get("value") for item in contacts),
        ),
        ("Image", bool(payload.get("media"))),
    )
    return checks, sum(1 for _label, complete in checks if complete)


@login_required
@require_http_methods(["GET"])
def workspace(request):
    memberships = list(
        ProviderMembership.objects.filter(
            account=request.user,
            is_active=True,
        )
        .select_related("provider")
        .prefetch_related(
            "provider__contacts",
            "provider__services",
            "provider__service_areas",
            "provider__languages",
            "provider__media_assets",
        )
    )
    metrics = aggregate_provider_metrics(
        membership.provider_id for membership in memberships
    )
    dashboard_rows = []
    for membership in memberships:
        payload, revision = _dashboard_payload(membership.provider)
        checklist, completed = _completion_checklist(payload)
        provider_metrics = metrics[str(membership.provider_id)]
        dashboard_rows.append(
            {
                "membership": membership,
                "revision": revision,
                "checklist": checklist,
                "completed": completed,
                "total": len(checklist),
                "impressions": provider_metrics["impression"],
                "profile_views": provider_metrics["profile_view"],
                "contact_clicks": provider_metrics["contact_click"],
            }
        )
    response = render(
        request,
        "providers/workspace.html",
        {"dashboard_rows": dashboard_rows},
    )
    response["Cache-Control"] = "private, no-store"
    return response


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
                {"provider": membership.provider, "revision": revision, "form": form},
                status=400,
            )
        revision = autosave_revision(
            provider_id=provider_id,
            account=request.user,
            payload=form.cleaned_payload(),
        )
        if request.headers.get("HX-Request") == "true":
            return HttpResponse("Saved", headers={"HX-Trigger": "providerDraftSaved"})
        return redirect("provider-workspace-edit", provider_id=provider_id)
    return render(
        request,
        "providers/edit_profile.html",
        {"provider": membership.provider, "revision": revision, "form": form},
    )


@login_required
@require_POST
def upload_profile_media(request, provider_id):
    _membership_for_request(request, provider_id)
    uploaded_file = request.FILES.get("image")
    if uploaded_file is None:
        return HttpResponseBadRequest("image is required")
    try:
        stage_media_upload(
            provider_id=provider_id,
            account=request.user,
            uploaded_file=uploaded_file,
            alt_text=request.POST.get("alt_text", ""),
        )
    except ValidationError as exc:
        return HttpResponseBadRequest(str(exc))
    return redirect("provider-workspace-edit", provider_id=provider_id)


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
