import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

from django.conf import settings
from django.core.cache import cache


def rate_limit(scope: str, identity: str, limit: int, window: int) -> bool:
    digest = hmac.new(
        settings.SECRET_KEY.encode(),
        identity.encode(),
        hashlib.sha256,
    ).hexdigest()
    key = f"accounts:rate:{scope}:{digest}"
    if cache.add(key, 1, timeout=window):
        return True
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=window)
        count = 1
    return count <= limit


def generate_totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def _totp_at(secret: str, timestamp: int) -> str:
    padded = secret + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded, casefold=True)
    counter = timestamp // 30
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{value:06d}"


def totp_code(secret: str, timestamp: int | None = None) -> str:
    return _totp_at(secret, int(time.time()) if timestamp is None else timestamp)


def verify_totp(secret: str, code: str, timestamp: int | None = None) -> bool:
    now = int(time.time()) if timestamp is None else timestamp
    return any(
        secrets.compare_digest(_totp_at(secret, now + offset), code)
        for offset in (-30, 0, 30)
    )


def totp_uri(email: str, secret: str) -> str:
    label = quote(f"Finrix Palvelut:{email}")
    issuer = quote("Finrix Palvelut")
    return f"otpauth://totp/{label}?secret={secret}&issuer={issuer}"
