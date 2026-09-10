from django.http import HttpRequest, HttpResponse
from django.views.decorators.http import require_GET

from palvelut.apps.analytics.beta import collect_beta_event


@require_GET
def beta_collect(request: HttpRequest) -> HttpResponse:
    return collect_beta_event(request, request.GET.get("event", ""))
