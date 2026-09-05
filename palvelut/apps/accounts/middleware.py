from django.shortcuts import redirect
from django.urls import reverse


class StaffMFAMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if path.startswith("/palvelut/staff/") and request.user.is_authenticated and request.user.is_staff:
            if not request.session.get("staff_mfa_verified"):
                target = reverse("staff-mfa")
                return redirect(f"{target}?next={path}")
        return self.get_response(request)
