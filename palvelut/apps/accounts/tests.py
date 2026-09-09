from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .models import EmailVerification
from .services import make_totp

TEST_PASSWORD = "Strong-passphrase-2026!"  # test-only
WRONG_PASSWORD = "Wrong-passphrase-2026!"  # test-only


class ProviderAccountSecurityTests(TestCase):
    def setUp(self):
        cache.clear()
        mail.outbox.clear()

    def test_registration_requires_email_verification_and_uses_argon2(self):
        response = self.client.post(
            reverse("account-register"),
            {
                "email": "new-provider@example.com",
                "password1": TEST_PASSWORD,
                "password2": TEST_PASSWORD,
            },
        )
        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(username="new-provider@example.com")
        self.assertFalse(user.is_active)
        self.assertTrue(user.password.startswith("argon2$"))
        verification = EmailVerification.objects.get(user=user)
        self.assertIsNone(verification.verified_at)
        self.assertEqual(len(mail.outbox), 1)
        verify_url = mail.outbox[0].body.strip().splitlines()[-1]
        verify_path = verify_url.split("testserver", 1)[1]

        verified = self.client.get(verify_path)
        self.assertRedirects(verified, reverse("account-login"))
        user.refresh_from_db()
        verification.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertIsNotNone(verification.verified_at)

        replay = self.client.get(verify_path)
        self.assertEqual(replay.status_code, 400)

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
        self.assertRedirects(success, reverse("provider-workspace"))
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
        )
        for index in range(6):
            response = self.client.post(
                reverse("account-login"),
                {"username": variants[index % len(variants)], "password": WRONG_PASSWORD},
                REMOTE_ADDR="192.0.2.9",
            )
            self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Too many attempts", status_code=200)

    def test_password_reset_does_not_reveal_account_and_is_rate_limited(self):
        get_user_model().objects.create_user(
            username="known@example.com",
            email="known@example.com",
            password=TEST_PASSWORD,
        )
        known = self.client.post(
            reverse("account-password-reset"), {"email": "known@example.com"}
        )
        unknown = self.client.post(
            reverse("account-password-reset"), {"email": "unknown@example.com"}
        )
        limited = self.client.post(
            reverse("account-password-reset"), {"email": "known@example.com"}
        )
        self.assertEqual(known.status_code, 302)
        self.assertEqual(unknown.status_code, 302)
        self.assertEqual(limited.status_code, 302)
        self.assertEqual(known.url, unknown.url)
        self.assertEqual(unknown.url, limited.url)
        done = self.client.get(known.url)
        self.assertContains(done, "If an account exists")

    def test_staff_admin_requires_mfa_and_rejects_external_next(self):
        staff = get_user_model().objects.create_superuser(
            username="staff@example.com",
            email="staff@example.com",
            password=TEST_PASSWORD,
        )
        self.client.force_login(staff)
        admin_response = self.client.get(reverse("admin:index"))
        self.assertEqual(admin_response.status_code, 302)
        self.assertIn(reverse("staff-mfa"), admin_response.url)

        mfa_page = self.client.get(reverse("staff-mfa"))
        self.assertEqual(mfa_page.status_code, 200)
        device = staff.staff_mfa_device
        code = make_totp(device.secret)
        verified = self.client.post(
            reverse("staff-mfa") + "?next=https://evil.example/",
            {"code": code},
        )
        self.assertRedirects(verified, reverse("admin:index"))
        self.assertTrue(self.client.session["staff_mfa_verified"])
        self.assertEqual(self.client.get(reverse("admin:index")).status_code, 200)

    def test_nonstaff_cannot_enter_staff_mfa(self):
        provider = get_user_model().objects.create_user(
            username="provider@example.com",
            email="provider@example.com",
            password=TEST_PASSWORD,
        )
        self.client.force_login(provider)
        response = self.client.get(reverse("staff-mfa"))
        self.assertRedirects(response, reverse("localized-home", kwargs={"locale": "fi"}))

    def test_staff_mfa_bruteforce_is_rate_limited(self):
        staff = get_user_model().objects.create_superuser(
            username="staff@example.com",
            email="staff@example.com",
            password=TEST_PASSWORD,
        )
        self.client.force_login(staff)
        self.client.get(reverse("staff-mfa"))
        for _ in range(9):
            response = self.client.post(reverse("staff-mfa"), {"code": "000000"})
        self.assertContains(response, "Too many attempts", status_code=200)
        self.assertNotIn("staff_mfa_verified", self.client.session)
