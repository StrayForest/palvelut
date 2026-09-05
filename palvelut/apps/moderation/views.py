from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from palvelut.apps.moderation.models import ModerationCase
from palvelut.apps.moderation.services import (
    create_anonymous_report,
    create_provider_notice,
    get_public_report_case,
    staff_update_case,
    submit_appeal,
)
from palvelut.apps.providers.models import Provider, ProviderMembership


@require_http_methods(["GET", "POST"])
def report_provider(request, provider_id):
    provider = get_object_or_404(Provider, pk=provider_id)
    if request.method == "POST":
        try:
            _, token = create_anonymous_report(
                provider=provider,
                reason=request.POST.get("reason", ""),
                details=request.POST.get("details", ""),
            )
        except ValidationError as exc:
            return render(
                request,
                "moderation/report_provider.html",
                {"provider": provider, "errors": exc.messages},
                status=400,
            )
        return redirect("report-status", token=token)
    return render(request, "moderation/report_provider.html", {"provider": provider})


@require_http_methods(["GET"])
def report_status(request, token):
    try:
        case = get_public_report_case(token=token)
    except ObjectDoesNotExist as exc:
        raise Http404 from exc
    return render(request, "moderation/report_status.html", {"case": case})


@login_required
@require_http_methods(["GET", "POST"])
def provider_case(request, case_id):
    case = get_object_or_404(ModerationCase.objects.select_related("provider"), pk=case_id)
    if not ProviderMembership.objects.filter(
        provider=case.provider, account=request.user, is_active=True
    ).exists():
        raise PermissionDenied
    if request.method == "POST":
        try:
            submit_appeal(
                case_id=case.pk,
                actor=request.user,
                message=request.POST.get("message", ""),
            )
        except ValidationError as exc:
            return render(
                request,
                "moderation/provider_case.html",
                {"case": case, "errors": exc.messages},
                status=400,
            )
        return redirect("provider-moderation-case", case_id=case.pk)
    return render(request, "moderation/provider_case.html", {"case": case})


@login_required
@require_http_methods(["GET"])
def staff_case_list(request):
    if not request.user.is_staff:
        raise PermissionDenied
    cases = ModerationCase.objects.select_related("provider").all()
    return render(request, "moderation/staff_case_list.html", {"cases": cases})


@login_required
@require_http_methods(["GET", "POST"])
def staff_case(request, case_id):
    if not request.user.is_staff:
        raise PermissionDenied
    case = get_object_or_404(ModerationCase.objects.select_related("provider"), pk=case_id)
    if request.method == "POST":
        operation = request.POST.get("operation", "")
        try:
            if operation == "notice":
                create_provider_notice(
                    case_id=case.pk,
                    actor=request.user,
                    message=request.POST.get("message", ""),
                )
            elif operation in ("resolve", "dismiss"):
                staff_update_case(
                    case_id=case.pk,
                    actor=request.user,
                    action=operation,
                    note=request.POST.get("note", ""),
                )
            else:
                raise ValidationError("Unsupported staff case operation")
        except ValidationError as exc:
            return render(
                request,
                "moderation/staff_case.html",
                {"case": case, "errors": exc.messages},
                status=400,
            )
        return redirect("staff-moderation-case", case_id=case.pk)
    return render(request, "moderation/staff_case.html", {"case": case})
