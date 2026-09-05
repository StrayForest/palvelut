from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.signing import salted_hmac
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from palvelut.apps.providers.models import Provider, ProviderMembership
from palvelut.apps.publishing.models import ProviderSlug

from .forms import (
    ContentReportForm,
    ProviderAppealForm,
    ReportStatusForm,
    StaffContentCaseForm,
)
from .models import ModerationCase
from .services import (
    appeal_content_case,
    content_report_status,
    provider_case_timeline,
    staff_update_content_case,
    submit_content_report,
)

REPORT_RATE_LIMIT = 5
REPORT_RATE_WINDOW_SECONDS = 3600


def _report_rate_key(request: HttpRequest, provider_id: object) -> str:
    client_address = request.META.get("HTTP_CF_CONNECTING_IP") or request.META.get(
        "REMOTE_ADDR", "unknown"
    )
    client_hash = salted_hmac(
        "palvelut.content-report-rate",
        str(client_address),
        secret=settings.SECRET_KEY,
    ).hexdigest()
    return f"moderation:content-report:{provider_id}:{client_hash}"


def _consume_report_rate_limit(request: HttpRequest, provider_id: object) -> bool:
    key = _report_rate_key(request, provider_id)
    if cache.add(key, 1, timeout=REPORT_RATE_WINDOW_SECONDS):
        return True
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=REPORT_RATE_WINDOW_SECONDS)
        count = 1
    return count <= REPORT_RATE_LIMIT


@never_cache
@require_http_methods(["GET", "POST"])
def report_provider(request: HttpRequest, locale: str, slug: str) -> HttpResponse:
    slug_row = get_object_or_404(
        ProviderSlug.objects.select_related("provider"),
        slug=slug,
        is_current=True,
        provider__lifecycle=Provider.Lifecycle.PUBLISHED,
    )
    provider = slug_row.provider
    if request.method == "POST" and not _consume_report_rate_limit(
        request, provider.pk
    ):
        response = HttpResponse("Too many reports", status=429)
        response["Retry-After"] = str(REPORT_RATE_WINDOW_SECONDS)
        return response
    form = ContentReportForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            receipt = submit_content_report(
                provider_id=provider.pk,
                category=form.cleaned_data["category"],
                details=form.cleaned_data["details"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            return render(
                request,
                "moderation/report_receipt.html",
                {
                    "provider": provider,
                    "locale": locale,
                    "case_id": receipt.case_id,
                    "status_token": receipt.status_token,
                    "robots_meta": "noindex,nofollow",
                },
                status=202,
            )
    return render(
        request,
        "moderation/report_provider.html",
        {
            "provider": provider,
            "locale": locale,
            "form": form,
            "robots_meta": "noindex,nofollow",
        },
    )


@never_cache
@require_http_methods(["GET", "POST"])
def report_status(request: HttpRequest, case_id) -> HttpResponse:
    form = ReportStatusForm(request.POST or None)
    case = None
    if request.method == "POST" and form.is_valid():
        try:
            case = content_report_status(
                case_id=case_id,
                status_token=form.cleaned_data["status_token"],
            )
        except (PermissionDenied, ModerationCase.DoesNotExist):
            form.add_error("status_token", "Invalid case or status code")
    return render(
        request,
        "moderation/report_status.html",
        {"form": form, "case": case, "robots_meta": "noindex,nofollow"},
    )


@never_cache
@login_required
@require_http_methods(["GET"])
def provider_case_list(request: HttpRequest) -> HttpResponse:
    provider_ids = ProviderMembership.objects.filter(
        account=request.user,
        is_active=True,
    ).values_list("provider_id", flat=True)
    cases = ModerationCase.objects.filter(
        provider_id__in=provider_ids,
        kind=ModerationCase.Kind.CONTENT_REPORT,
        events__visible_to_provider=True,
    ).select_related("provider").distinct()
    return render(
        request,
        "moderation/provider_case_list.html",
        {"cases": cases, "robots_meta": "noindex,nofollow"},
    )


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def provider_case_detail(request: HttpRequest, case_id) -> HttpResponse:
    try:
        case, events = provider_case_timeline(case_id=case_id, actor=request.user)
    except (PermissionDenied, ModerationCase.DoesNotExist) as exc:
        raise Http404 from exc
    if not events:
        raise Http404
    form = ProviderAppealForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            appeal_content_case(
                case_id=case.pk,
                actor=request.user,
                note=form.cleaned_data["note"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            return redirect("provider-content-case-detail", case_id=case.pk)
    return render(
        request,
        "moderation/provider_case_detail.html",
        {
            "case": case,
            "events": events,
            "form": form,
            "robots_meta": "noindex,nofollow",
        },
    )


@never_cache
@login_required
@require_http_methods(["GET"])
def staff_case_list(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        raise PermissionDenied
    cases = ModerationCase.objects.filter(
        kind=ModerationCase.Kind.CONTENT_REPORT,
    ).select_related("provider", "opened_by")
    return render(
        request,
        "moderation/staff_case_list.html",
        {"cases": cases, "robots_meta": "noindex,nofollow"},
    )


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def staff_case_detail(request: HttpRequest, case_id) -> HttpResponse:
    if not request.user.is_staff:
        raise PermissionDenied
    case = get_object_or_404(
        ModerationCase.objects.select_related("provider").prefetch_related("events"),
        pk=case_id,
        kind=ModerationCase.Kind.CONTENT_REPORT,
    )
    form = StaffContentCaseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            staff_update_content_case(
                case_id=case.pk,
                actor=request.user,
                action=form.cleaned_data["action"],
                note=form.cleaned_data["note"],
            )
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            return redirect("staff-content-case-detail", case_id=case.pk)
    return render(
        request,
        "moderation/staff_case_detail.html",
        {
            "case": case,
            "events": case.events.select_related("actor"),
            "form": form,
            "robots_meta": "noindex,nofollow",
        },
    )
