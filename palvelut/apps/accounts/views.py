from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .forms import LoginForm, MFAForm, RegistrationForm, ResetRequestForm
from .models import AccountSecurity
from .services import generate_totp_secret, rate_limit, totp_uri, verify_totp

User = get_user_model()


def _valid_locale(locale: str) -> None:
    if locale not in {"ru", "fi", "en"}:
        raise Http404


def _private(response: HttpResponse) -> HttpResponse:
    response["Cache-Control"] = "private, no-store"
    return response


def private_view(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        return _private(view(*args, **kwargs))

    return wrapped


def _identity(request, email: str) -> str:
    return f"{request.META.get('REMOTE_ADDR', '')}|{email}"


def _verification_url(request, locale: str, user) -> str:
    return request.build_absolute_uri(
        reverse(
            "account-verify",
            kwargs={
                "locale": locale,
                "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": default_token_generator.make_token(user),
            },
        )
    )


@private_view
def register(request, locale: str):
    _valid_locale(locale)
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        if User.objects.filter(username__iexact=email).exists():
            form.add_error("email", "An account with this email already exists.")
        else:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=form.cleaned_data["password"],
                is_active=False,
            )
            AccountSecurity.objects.create(user=user)
            send_mail(
                "Verify your Finrix Palvelut email",
                f"Verify your email: {_verification_url(request, locale, user)}",
                None,
                [email],
            )
            return render(
                request,
                "accounts/form.html",
                {
                    "title": "Check your email",
                    "message": "A verification link has been sent if delivery is available.",
                },
            )
    return render(
        request,
        "accounts/form.html",
        {"title": "Create provider account", "form": form, "submit_label": "Create account"},
    )


@private_view
def verify_email(request, locale: str, uidb64: str, token: str):
    _valid_locale(locale)
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)))
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None
    if user is None or not default_token_generator.check_token(user, token):
        return HttpResponse("Invalid or expired verification link.", status=400)
    security, _ = AccountSecurity.objects.get_or_create(user=user)
    security.email_verified_at = timezone.now()
    security.save(update_fields=["email_verified_at", "updated_at"])
    if not user.is_active:
        user.is_active = True
        user.save(update_fields=["is_active"])
    return HttpResponseRedirect(reverse("account-login", kwargs={"locale": locale}))


@private_view
def account_login(request, locale: str):
    _valid_locale(locale)
    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        if not rate_limit("login", _identity(request, email), 5, 15 * 60):
            return HttpResponse("Too many attempts.", status=429)
        user = authenticate(request, username=email, password=form.cleaned_data["password"])
        security = AccountSecurity.objects.filter(user=user).first() if user else None
        if user and security and security.email_verified:
            request.session.cycle_key()
            if user.is_staff:
                request.session["pending_staff_user_id"] = user.pk
                destination = "account-mfa" if security.staff_mfa_enabled else "account-mfa-setup"
                return HttpResponseRedirect(reverse(destination, kwargs={"locale": locale}))
            login(request, user)
            request.session.set_expiry(12 * 60 * 60)
            return HttpResponseRedirect(reverse("account-home", kwargs={"locale": locale}))
        form.add_error(None, "Invalid email or password.")
    return render(
        request,
        "accounts/form.html",
        {"title": "Sign in", "form": form, "submit_label": "Sign in"},
    )


def _pending_staff(request):
    user_id = request.session.get("pending_staff_user_id")
    if not user_id:
        return None
    return User.objects.filter(pk=user_id, is_active=True, is_staff=True).first()


def _complete_staff_login(request, user) -> None:
    request.session.pop("pending_staff_user_id", None)
    login(request, user)
    request.session["staff_mfa_verified"] = True
    request.session.set_expiry(8 * 60 * 60)


@private_view
def staff_mfa_setup(request, locale: str):
    _valid_locale(locale)
    user = _pending_staff(request)
    if user is None:
        return HttpResponseRedirect(reverse("account-login", kwargs={"locale": locale}))
    security, _ = AccountSecurity.objects.get_or_create(user=user)
    if security.staff_mfa_enabled:
        return HttpResponseRedirect(reverse("account-mfa", kwargs={"locale": locale}))
    if not security.mfa_secret:
        security.mfa_secret = generate_totp_secret()
        security.save(update_fields=["mfa_secret", "updated_at"])
    form = MFAForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if verify_totp(security.mfa_secret, form.cleaned_data["code"]):
            security.mfa_confirmed_at = timezone.now()
            security.save(update_fields=["mfa_confirmed_at", "updated_at"])
            _complete_staff_login(request, user)
            return HttpResponseRedirect(reverse("account-home", kwargs={"locale": locale}))
        form.add_error("code", "Invalid authentication code.")
    return render(
        request,
        "accounts/form.html",
        {
            "title": "Set up staff MFA",
            "form": form,
            "submit_label": "Confirm MFA",
            "mfa_secret": security.mfa_secret,
            "mfa_uri": totp_uri(user.email, security.mfa_secret),
        },
    )


@private_view
def staff_mfa(request, locale: str):
    _valid_locale(locale)
    user = _pending_staff(request)
    if user is None:
        return HttpResponseRedirect(reverse("account-login", kwargs={"locale": locale}))
    security = AccountSecurity.objects.filter(user=user).first()
    if security is None or not security.staff_mfa_enabled:
        return HttpResponseRedirect(reverse("account-mfa-setup", kwargs={"locale": locale}))
    form = MFAForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if verify_totp(security.mfa_secret, form.cleaned_data["code"]):
            _complete_staff_login(request, user)
            return HttpResponseRedirect(reverse("account-home", kwargs={"locale": locale}))
        form.add_error("code", "Invalid authentication code.")
    return render(
        request,
        "accounts/form.html",
        {"title": "Staff MFA", "form": form, "submit_label": "Verify"},
    )


@private_view
def password_reset_request(request, locale: str):
    _valid_locale(locale)
    form = ResetRequestForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        email = form.cleaned_data["email"]
        if not rate_limit("reset", _identity(request, email), 3, 60 * 60):
            return HttpResponse("Too many attempts.", status=429)
        user = User.objects.filter(username__iexact=email, is_active=True).first()
        security = AccountSecurity.objects.filter(user=user).first() if user else None
        if user and security and security.email_verified:
            url = request.build_absolute_uri(
                reverse(
                    "account-password-reset-confirm",
                    kwargs={
                        "locale": locale,
                        "uidb64": urlsafe_base64_encode(force_bytes(user.pk)),
                        "token": default_token_generator.make_token(user),
                    },
                )
            )
            send_mail("Reset your Finrix Palvelut password", f"Reset password: {url}", None, [user.email])
        return render(
            request,
            "accounts/form.html",
            {"title": "Check your email", "message": "If the account exists, reset instructions were sent."},
        )
    return render(
        request,
        "accounts/form.html",
        {"title": "Reset password", "form": form, "submit_label": "Send reset link"},
    )


@private_view
def password_reset_confirm(request, locale: str, uidb64: str, token: str):
    _valid_locale(locale)
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)))
    except (User.DoesNotExist, ValueError, TypeError, OverflowError):
        user = None
    if user is None or not default_token_generator.check_token(user, token):
        return HttpResponse("Invalid or expired reset link.", status=400)
    form = SetPasswordForm(user, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Password updated.")
        return HttpResponseRedirect(reverse("account-login", kwargs={"locale": locale}))
    return render(
        request,
        "accounts/form.html",
        {"title": "Choose a new password", "form": form, "submit_label": "Update password"},
    )


@private_view
@login_required
def account_home(request, locale: str):
    _valid_locale(locale)
    if request.user.is_staff and not request.session.get("staff_mfa_verified"):
        logout(request)
        return HttpResponseRedirect(reverse("account-login", kwargs={"locale": locale}))
    return render(
        request,
        "accounts/form.html",
        {"title": "Provider account", "message": f"Signed in as {request.user.email}."},
    )


@private_view
def account_logout(request, locale: str):
    _valid_locale(locale)
    if request.method != "POST":
        return HttpResponse(status=405)
    logout(request)
    return HttpResponseRedirect(reverse("account-login", kwargs={"locale": locale}))
