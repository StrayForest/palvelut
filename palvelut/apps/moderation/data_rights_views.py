from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_control, never_cache
from django.views.decorators.http import require_http_methods

from .data_rights import create_data_subject_request, update_data_subject_request
from .forms import DataSubjectRequestForm, StaffDataSubjectRequestForm
from .models import DataSubjectRequest


@never_cache
@cache_control(private=True, no_store=True)
@login_required
@require_http_methods(["GET", "POST"])
def data_subject_requests(request: HttpRequest) -> HttpResponse:
    form = DataSubjectRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        create_data_subject_request(
            account=request.user,
            kind=form.cleaned_data["kind"],
            note=form.cleaned_data["note"],
        )
        return redirect("data-subject-requests")
    rows = DataSubjectRequest.objects.filter(account=request.user)
    return render(
        request,
        "moderation/data_subject_requests.html",
        {"form": form, "requests": rows, "robots_meta": "noindex,nofollow"},
    )


@never_cache
@cache_control(private=True, no_store=True)
@login_required
@require_http_methods(["GET"])
def staff_data_subject_request_list(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        raise PermissionDenied
    rows = DataSubjectRequest.objects.select_related("account").all()
    return render(
        request,
        "moderation/staff_data_subject_request_list.html",
        {"requests": rows, "robots_meta": "noindex,nofollow"},
    )


@never_cache
@cache_control(private=True, no_store=True)
@login_required
@require_http_methods(["GET", "POST"])
def staff_data_subject_request_detail(request: HttpRequest, request_id) -> HttpResponse:
    if not request.user.is_staff:
        raise PermissionDenied
    row = get_object_or_404(
        DataSubjectRequest.objects.select_related("account").prefetch_related("events"),
        pk=request_id,
    )
    form = StaffDataSubjectRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            update_data_subject_request(
                request_id=row.pk,
                actor=request.user,
                action=form.cleaned_data["action"],
                note=form.cleaned_data["note"],
            )
        except (ValidationError, DataSubjectRequest.DoesNotExist) as exc:
            if isinstance(exc, DataSubjectRequest.DoesNotExist):
                raise Http404 from exc
            form.add_error(None, exc)
        else:
            return redirect("staff-data-subject-request-detail", request_id=row.pk)
    return render(
        request,
        "moderation/staff_data_subject_request_detail.html",
        {
            "data_request": row,
            "events": row.events.select_related("actor"),
            "form": form,
            "robots_meta": "noindex,nofollow",
        },
    )
