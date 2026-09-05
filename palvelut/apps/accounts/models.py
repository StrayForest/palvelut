from django.conf import settings
from django.db import models


class AccountSecurity(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="security",
    )
    email_verified_at = models.DateTimeField(null=True, blank=True)
    mfa_secret = models.CharField(max_length=64, blank=True)
    mfa_confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def email_verified(self) -> bool:
        return self.email_verified_at is not None

    @property
    def staff_mfa_enabled(self) -> bool:
        return bool(self.mfa_secret and self.mfa_confirmed_at)
