from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import EmailVerification


ORIGINAL_PASSWORD = "Original-passphrase-2026!"  # test-only
REPLACEMENT_PASSWORD = "Replacement-passphrase-2026!"  # test-only


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class VerificationResendTests(TestCase):
    def setUp(self) -> None:
        cache.clear()

    def test_repeat_registration_resends_for_inactive_account_without_password_change(
        self,
    ) -> None:
        user = get_user_model().objects.create_user(
            username="provider@example.com",
            email="provider@example.com",
            password=ORIGINAL_PASSWORD,
            is_active=False,
        )
        original_password_hash = user.password
        verification = EmailVerification.objects.create(
            user=user,
            token_hash="a" * 64,
            expires_at=timezone.now() + timedelta(hours=1),
        )

        response = self.client.post(
            reverse("account-register"),
            {
                "email": "Provider@Example.com",
                "password1": REPLACEMENT_PASSWORD,
                "password2": REPLACEMENT_PASSWORD,
            },
            REMOTE_ADDR="203.0.113.30",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            get_user_model().objects.filter(email="provider@example.com").count(), 1
        )
        user.refresh_from_db()
        self.assertEqual(user.password, original_password_hash)
        self.assertTrue(user.check_password(ORIGINAL_PASSWORD))
        self.assertFalse(user.check_password(REPLACEMENT_PASSWORD))

        verification.refresh_from_db()
        self.assertNotEqual(verification.token_hash, "a" * 64)
        self.assertIsNone(verification.verified_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("/palvelut/account/verify/", mail.outbox[0].body)
