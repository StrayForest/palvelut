from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView, PasswordResetCompleteView, PasswordResetConfirmView, PasswordResetDoneView, PasswordResetView
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .forms import EmailAuthenticationForm, MFAForm, ProviderRegistrationForm, RateLimitedPasswordResetForm, SecureSetPasswordForm
from .services import get_or_create_staff_device, issue_email_verification, rate_limited, valid_totp, verify_email_token


@never_cache
@require_http_methods(["GET", "POST"])
def register(request: HttpRequest) -> HttpResponse:
    form = ProviderRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        if rate_limited("register", f"{request.META.get('REMOTE_ADDR', '')}:{email}"):
            form.add_error(None, "Too many attempts. Try again later.")
        else:
            user = form.save()
            issue_email_verification(user, request)
            return render(request, "accounts/check_email.html", status=201)
    return render(request, "accounts/register.html", {"form": form})


@never_cache
def verify_email(request: HttpRequest, token: str) -> HttpResponse:
    if not verify_email_token(token):
        return render(request, "accounts/verification_invalid.html", status=400)
    messages.success(request, "Email verified. You can now sign in.")
    return redirect("account-login")


class ProviderLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm

    def form_valid(self, form):
        identity = form.cleaned_data.get("username", "")
        if rate_limited("login", f"{self.request.META.get('REMOTE_ADDR', '')}:{identity}"):
            form.add_error(None, "Too many attempts. Try again later.")
            return self.form_invalid(form)
        response = super().form_valid(form)
        self.request.session.cycle_key()
        self.request.session.pop("staff_mfa_verified", None)
        return response

    def get_success_url(self):
        if self.request.user.is_staff:
            return reverse("staff-mfa")
        return reverse("localized-home", kwargs={"locale": "fi"})


class ProviderLogoutView(LogoutView):
    next_page = reverse_lazy("account-login")


class SecurePasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.txt"
    subject_template_name = "accounts/password_reset_subject.txt"
    form_class = RateLimitedPasswordResetForm
    success_url = reverse_lazy("account-password-reset-done")

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        if rate_limited("password-reset", f"{self.request.META.get('REMOTE_ADDR', '')}:{email}"):
            return redirect(self.success_url)
        return super().form_valid(form)


class SecurePasswordResetDoneView(PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class SecurePasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = SecureSetPasswordForm
    success_url = reverse_lazy("account-password-reset-complete")

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.user.is_authenticated:
            self.request.session.cycle_key()
        return response


class SecurePasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


@never_cache
@login_required
@require_http_methods(["GET", "POST"])
def staff_mfa(request: HttpRequest) -> HttpResponse:
    if not request.user.is_staff:
        return redirect("localized-home", locale="fi")
    device = get_or_create_staff_device(request.user)
    form = MFAForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if rate_limited("mfa", f"{request.user.pk}:{request.META.get('REMOTE_ADDR', '')}", limit=8):
            form.add_error(None, "Too many attempts. Try again later.")
        elif valid_totp(device.secret, form.cleaned_data["code"]):
            if device.confirmed_at is None:
                device.confirmed_at = timezone.now()
                device.save(update_fields=["confirmed_at"])
            request.session.cycle_key()
            request.session["staff_mfa_verified"] = True
            destination = request.GET.get("next") or reverse("admin:index")
            return redirect(destination)
        else:
            form.add_error("code", "Invalid code.")
    query = urlencode({"secret": device.secret})
    return render(request, "accounts/staff_mfa.html", {"form": form, "device": device, "provisioning_hint": query})
