import re
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import identify_hasher
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import EmailVerification, StaffMFADevice
from .services import totp_code

TEST_PASSWORD = "Strong-passphrase-2026!"  # test-only
WRONG_PASSWORD = "wrong-password"  # test-only


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class ProviderAccountSecurityTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_registration_requires_email_verification_and_uses_argon2(self):
        response = self.client.post(
            reverse("account-register"),
            {
                "email": "Provider@Example.com",
                "password1": TEST_PASSWORD,
                "password2": TEST_PASSWORD,
            },
        )
        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(email="provider@example.com")
        self.assertFalse(user.is_active)
        self.assertEqual(identify_hasher(user.password).algorithm, "argon2")
        verification = EmailVerification.objects.get(user=user)
        self.assertEqual(len(verification.token_hash), 64)
        self.assertNotIn(verification.token_hash, mail.outbox[0].body)

        token_match = re.search(r"/verify/([^/]+)/", mail.outbox[0].body)
        assert token_match is not None
        token = token_match.group(1)
        verified = self.client.get(
            reverse("account-verify-email", kwargs={"token": token})
        )
        self.assertRedirects(verified, reverse("account-login"))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertEqual(
            self.client.get(
                reverse("account-verify-email", kwargs={"token": token})
            ).status_code,
            400,
        )

    def test_login_is_rate_limited_and_rotates_session(self):
        user = get_user_model().objects.create_user(
            username="provider@example.com",
            email="provider@example.com",
            password=TEST_PASSWORD,
        )
        self.client.get(reverse("account-login"))
        old_key = self.client.session.session_key
        for _ in range(5):
            response = self.client.post(
                reverse("account-login"),
                {"username": user.email, "password": WRONG_PASSWORD},
            )
            self.assertEqual(response.status_code, 200)
        blocked = self.client.post(
            reverse("account-login"),
            {"username": user.email, "password": TEST_PASSWORD},
        )
        self.assertContains(blocked, "Too many attempts", status_code=200)
        self.assertNotIn("_auth_user_id", self.client.session)

        cache.clear()
        success = self.client.post(
            reverse("account-login"),
            {"username": user.email, "password": TEST_PASSWORD},
        )
        self.assertRedirects(
            success, reverse("localized-home", kwargs={"locale": "fi"})
        )
        self.assertNotEqual(old_key, self.client.session.session_key)

    def test_login_throttle_cannot_be_bypassed_by_identity_variants(self):
        user = get_user_model().objects.create_user(
            username="provider@example.com",
            email="provider@example.com",
            password=TEST_PASSWORD,
        )
        variants = (
            "provider@example.com",
            "Provider@Example.com",
            " PROVIDER@example.com ",
            "provider@EXAMPLE.com",
            " provider@example.com",
        )
        for identity in variants:
            response = self.client.post(
                reverse("account-login"),
                {"username": identity, "password": WRONG_PASSWORD},
                REMOTE_ADDR="203.0.113.21",
            )
            self.assertEqual(response.status_code, 200)

        blocked = self.client.post(
            reverse("account-login"),
            {"username": user.email, "password": TEST_PASSWORD},
            REMOTE_ADDR="203.0.113.21",
        )
        self.assertContains(blocked, "Too many attempts", status_code=200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_password_reset_does_not_reveal_account_and_is_rate_limited(self):
        get_user_model().objects.create_user(
            username="provider@example.com",
            email="provider@example.com",
            password=TEST_PASSWORD,
        )
        existing = self.client.post(
            reverse("account-password-reset"), {"email": "provider@example.com"}
        )
        missing = self.client.post(
            reverse("account-password-reset"), {"email": "missing@example.com"}
        )
        self.assertEqual(existing.status_code, 302)
        self.assertEqual(missing.status_code, 302)
        self.assertEqual(existing.url, missing.url)
        self.assertEqual(len(mail.outbox), 1)

        with patch("palvelut.apps.accounts.views.rate_limited", return_value=True):
            limited = self.client.post(
                reverse("account-password-reset"), {"email": "provider@example.com"}
            )
        self.assertRedirects(limited, reverse("account-password-reset-done"))
        self.assertEqual(len(mail.outbox), 1)

    def test_staff_admin_requires_mfa_and_rejects_external_next(self):
        staff = get_user_model().objects.create_user(
            username="staff@example.com",
            email="staff@example.com",
            password=TEST_PASSWORD,
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(staff)
        blocked = self.client.get(reverse("admin:index"))
        self.assertEqual(blocked.status_code, 302)
        self.assertTrue(blocked.url.startswith(reverse("staff-mfa")))

        setup = self.client.get(reverse("staff-mfa"))
        self.assertEqual(setup.status_code, 200)
        device = StaffMFADevice.objects.get(user=staff)
        verified = self.client.post(
            f"{reverse('staff-mfa')}?next=https://attacker.invalid/",
            {"code": totp_code(device.secret)},
        )
        self.assertRedirects(verified, reverse("admin:index"))
        self.assertTrue(self.client.session["staff_mfa_verified"])
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)

    def test_staff_mfa_bruteforce_is_rate_limited(self):
        staff = get_user_model().objects.create_user(
            username="staff-abuse@example.com",
            email="staff-abuse@example.com",
            password=TEST_PASSWORD,
            is_staff=True,
            is_superuser=True,
        )
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("staff-mfa")).status_code, 200)
        device = StaffMFADevice.objects.get(user=staff)

        for _ in range(8):
            response = self.client.post(
                reverse("staff-mfa"),
                {"code": "000000"},
                REMOTE_ADDR="203.0.113.22",
            )
            self.assertContains(response, "Invalid code", status_code=200)

        blocked = self.client.post(
            reverse("staff-mfa"),
            {"code": totp_code(device.secret)},
            REMOTE_ADDR="203.0.113.22",
        )
        self.assertContains(blocked, "Too many attempts", status_code=200)
        self.assertFalse(self.client.session.get("staff_mfa_verified", False))

    def test_nonstaff_cannot_enter_staff_mfa(self):
        provider = get_user_model().objects.create_user(
            username="provider@example.com",
            email="provider@example.com",
            password=TEST_PASSWORD,
        )
        self.client.force_login(provider)
        response = self.client.get(reverse("staff-mfa"))
        self.assertRedirects(
            response, reverse("localized-home", kwargs={"locale": "fi"})
        )
        self.assertFalse(StaffMFADevice.objects.filter(user=provider).exists())
