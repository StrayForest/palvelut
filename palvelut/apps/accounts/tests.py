from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import AccountSecurity
from .services import totp_code

User = get_user_model()


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class ProviderAuthTests(TestCase):
    def setUp(self):
        self.client = Client()

    def _verified_user(self, email="provider@example.com", password="Safe-password-938!"):
        user = User.objects.create_user(username=email, email=email, password=password, is_active=True)
        AccountSecurity.objects.create(user=user, email_verified_at=timezone.now())
        return user

    def test_registration_requires_email_verification_before_login(self):
        response = self.client.post(
            reverse("account-register", kwargs={"locale": "en"}),
            {
                "email": "new@example.com",
                "password": "Safe-password-938!",
                "password_confirm": "Safe-password-938!",
                "accept_terms": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(username="new@example.com")
        self.assertFalse(user.is_active)
        self.assertFalse(user.security.email_verified)
        self.assertEqual(len(mail.outbox), 1)

        login_response = self.client.post(
            reverse("account-login", kwargs={"locale": "en"}),
            {"email": "new@example.com", "password": "Safe-password-938!"},
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertContains(login_response, "Invalid email or password")

        verify_url = mail.outbox[0].body.split("Verify your email: ", 1)[1]
        verify_response = self.client.get(verify_url)
        self.assertEqual(verify_response.status_code, 302)
        user.refresh_from_db()
        user.security.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertTrue(user.security.email_verified)

    def test_verified_provider_login_rotates_session_and_is_private(self):
        user = self._verified_user()
        session = self.client.session
        session["before"] = True
        session.save()
        previous_key = session.session_key

        response = self.client.post(
            reverse("account-login", kwargs={"locale": "en"}),
            {"email": user.email, "password": "Safe-password-938!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
        self.assertNotEqual(self.client.session.session_key, previous_key)
        self.assertEqual(response["Cache-Control"], "private, no-store")

    def test_password_reset_is_generic_and_changes_password(self):
        user = self._verified_user()
        response = self.client.post(
            reverse("account-password-reset", kwargs={"locale": "en"}),
            {"email": user.email},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "If the account exists")
        self.assertEqual(len(mail.outbox), 1)
        reset_url = mail.outbox[0].body.split("Reset password: ", 1)[1]
        response = self.client.post(
            reset_url,
            {"new_password1": "New-safe-password-552!", "new_password2": "New-safe-password-552!"},
        )
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.check_password("New-safe-password-552!"))
        self.assertFalse(user.check_password("Safe-password-938!"))

    def test_login_and_reset_are_rate_limited(self):
        self._verified_user()
        login_url = reverse("account-login", kwargs={"locale": "en"})
        for _ in range(5):
            response = self.client.post(
                login_url,
                {"email": "provider@example.com", "password": "wrong-password"},
            )
            self.assertEqual(response.status_code, 200)
        response = self.client.post(
            login_url,
            {"email": "provider@example.com", "password": "wrong-password"},
        )
        self.assertEqual(response.status_code, 429)

        reset_url = reverse("account-password-reset", kwargs={"locale": "en"})
        for _ in range(3):
            self.assertEqual(self.client.post(reset_url, {"email": "missing@example.com"}).status_code, 200)
        self.assertEqual(
            self.client.post(reset_url, {"email": "missing@example.com"}).status_code,
            429,
        )

    def test_staff_password_never_creates_authenticated_session_before_mfa(self):
        user = self._verified_user(email="staff@example.com")
        user.is_staff = True
        user.save(update_fields=["is_staff"])
        response = self.client.post(
            reverse("account-login", kwargs={"locale": "en"}),
            {"email": user.email, "password": "Safe-password-938!"},
        )
        self.assertRedirects(
            response,
            reverse("account-mfa-setup", kwargs={"locale": "en"}),
            fetch_redirect_response=False,
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.session["pending_staff_user_id"], user.pk)

        setup_url = reverse("account-mfa-setup", kwargs={"locale": "en"})
        self.client.get(setup_url)
        user.security.refresh_from_db()
        code = totp_code(user.security.mfa_secret)
        response = self.client.post(setup_url, {"code": code})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
        self.assertTrue(self.client.session["staff_mfa_verified"])
        user.security.refresh_from_db()
        self.assertTrue(user.security.staff_mfa_enabled)

    def test_staff_subsequent_login_requires_totp_challenge(self):
        user = self._verified_user(email="staff2@example.com")
        user.is_staff = True
        user.save(update_fields=["is_staff"])
        user.security.mfa_secret = "JBSWY3DPEHPK3PXP"
        user.security.mfa_confirmed_at = timezone.now()
        user.security.save()

        response = self.client.post(
            reverse("account-login", kwargs={"locale": "en"}),
            {"email": user.email, "password": "Safe-password-938!"},
        )
        self.assertRedirects(
            response,
            reverse("account-mfa", kwargs={"locale": "en"}),
            fetch_redirect_response=False,
        )
        self.assertNotIn("_auth_user_id", self.client.session)
        response = self.client.post(
            reverse("account-mfa", kwargs={"locale": "en"}),
            {"code": totp_code(user.security.mfa_secret)},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

    def test_csrf_rejects_login_without_token(self):
        csrf_client = Client(enforce_csrf_checks=True)
        response = csrf_client.post(
            reverse("account-login", kwargs={"locale": "en"}),
            {"email": "provider@example.com", "password": "anything"},
        )
        self.assertEqual(response.status_code, 403)
