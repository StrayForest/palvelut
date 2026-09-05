import base64
import hashlib
import hmac
import secrets
import struct
import time
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.urls import reverse
from django.utils import timezone

from .models import EmailVerification, StaffMFADevice


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def issue_email_verification(user, request) -> None:
    token = secrets.token_urlsafe(32)
    EmailVerification.objects.update_or_create(
        user=user,
        defaults={
            "token_hash": _digest(token),
            "expires_at": timezone.now() + timedelta(hours=24),
            "verified_at": None,
        },
    )
    url = request.build_absolute_uri(
        reverse("account-verify-email", kwargs={"token": token})
    )
    send_mail(
        "Verify your Finrix Palvelut email",
        f"Verify your email: {url}",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )


def verify_email_token(token: str) -> bool:
    verification = (
        EmailVerification.objects.select_related("user")
        .filter(token_hash=_digest(token))
        .first()
    )
    if (
        verification is None
        or verification.verified_at
        or verification.expires_at <= timezone.now()
    ):
        return False
    verification.verified_at = timezone.now()
    verification.save(update_fields=["verified_at"])
    verification.user.is_active = True
    verification.user.save(update_fields=["is_active"])
    return True


def throttle_key(scope: str, identity: str) -> str:
    return f"account-throttle:{scope}:{_digest(identity.lower().strip())}"


def rate_limited(
    scope: str, identity: str, *, limit: int = 5, window: int = 300
) -> bool:
    key = throttle_key(scope, identity)
    if cache.add(key, 1, timeout=window):
        return False
    try:
        attempts = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=window)
        attempts = 1
    return attempts > limit


def new_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def totp_code(secret: str, *, at: int | None = None) -> str:
    moment = int(time.time() if at is None else at)
    counter = moment // 30
    padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded, casefold=True)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{value % 1_000_000:06d}"


def valid_totp(secret: str, code: str) -> bool:
    if len(code) != 6 or not code.isdigit():
        return False
    now = int(time.time())
    return any(
        hmac.compare_digest(totp_code(secret, at=now + drift * 30), code)
        for drift in (-1, 0, 1)
    )


def get_or_create_staff_device(user) -> StaffMFADevice:
    device, _ = StaffMFADevice.objects.get_or_create(
        user=user, defaults={"secret": new_totp_secret()}
    )
    return device
