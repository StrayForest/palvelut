import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "palvelut.settings")

import django

django.setup()

from django.test import Client, SimpleTestCase, override_settings


@override_settings(ALLOWED_HOSTS=["testserver"])
class SecurityHeadersTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_application_responses_enforce_restrictive_browser_security_headers(self):
        response = self.client.get("/palvelut/health/live")

        self.assertEqual(response.status_code, 200)
        policy = response["Content-Security-Policy"]
        self.assertIn("default-src 'self'", policy)
        self.assertIn("script-src 'self'", policy)
        self.assertIn("style-src 'self'", policy)
        self.assertIn("object-src 'none'", policy)
        self.assertIn("base-uri 'self'", policy)
        self.assertIn("form-action 'self'", policy)
        self.assertIn("frame-ancestors 'none'", policy)
        self.assertNotIn("'unsafe-inline'", policy)
        self.assertNotIn("'unsafe-eval'", policy)

        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["Referrer-Policy"], "strict-origin-when-cross-origin")
        self.assertEqual(
            response["Permissions-Policy"],
            "camera=(), geolocation=(), microphone=(), payment=(), usb=()",
        )
