import os
from pathlib import Path
from unittest import mock

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "palvelut.settings")

import django

django.setup()

from django.conf import settings
from django.test import Client, SimpleTestCase, override_settings

from palvelut.settings import _public_base_url


LOCAL_MEMORY_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "routing-contract",
    }
}


@override_settings(ALLOWED_HOSTS=["testserver"], CACHES=LOCAL_MEMORY_CACHE)
class RoutingContractTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_only_russian_locale_root_is_owned_by_django(self):
        response = self.client.get("/palvelut/ru/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<html lang="ru">', html=False)

        for locale in ("fi", "en"):
            with self.subTest(locale=locale):
                unsupported = self.client.get(f"/palvelut/{locale}/")
                self.assertEqual(unsupported.status_code, 404)

    def test_unsupported_locale_returns_real_404(self):
        response = self.client.get("/palvelut/sv/")
        self.assertEqual(response.status_code, 404)

    def test_public_mount_root_redirect_stays_inside_prefix(self):
        response = self.client.get("/palvelut/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/palvelut/ru/")

    def test_static_and_cookie_paths_keep_public_mount_prefix(self):
        self.assertEqual(settings.STATIC_URL, "/palvelut/static/")
        self.assertEqual(settings.SESSION_COOKIE_PATH, "/palvelut/")
        self.assertEqual(settings.CSRF_COOKIE_PATH, "/palvelut/")
        self.assertFalse(settings.is_overridden("LANGUAGE_COOKIE_PATH"))
        response = self.client.get("/palvelut/ru/")
        self.assertContains(response, "/palvelut/static/css/app.css")
        self.assertContains(response, "/palvelut/static/vendor/htmx.min.js")
        self.assertContains(response, "/palvelut/static/vendor/alpine.min.js")

    @override_settings(PUBLIC_BASE_URL="https://finrix.fi/palvelut")
    def test_canonical_is_absolute_and_no_multilingual_hreflang_remains(self):
        response = self.client.get("/palvelut/ru/")
        self.assertContains(
            response,
            '<link rel="canonical" href="https://finrix.fi/palvelut/ru/">',
            html=False,
        )
        self.assertNotContains(response, 'hreflang="fi"', html=False)
        self.assertNotContains(response, 'hreflang="en"', html=False)
        self.assertNotContains(response, 'hreflang="x-default"', html=False)

    def test_public_base_url_is_mount_scoped_and_absolute(self):
        valid = {
            "PUBLIC_BASE_URL": "https://finrix.fi/palvelut/",
        }
        with mock.patch.dict(os.environ, valid, clear=False):
            self.assertEqual(_public_base_url(), "https://finrix.fi/palvelut")

        for value in (
            "/palvelut",
            "https://finrix.fi/",
            "https://finrix.fi/palvelut/en",
            "https://finrix.fi/palvelut?x=1",
        ):
            with (
                self.subTest(value=value),
                mock.patch.dict(os.environ, {"PUBLIC_BASE_URL": value}, clear=False),
            ):
                with self.assertRaises(RuntimeError):
                    _public_base_url()

    def test_nginx_proxy_does_not_rewrite_public_prefix(self):
        config = Path("infra/nginx/default.conf").read_text()
        self.assertIn("proxy_pass http://web:8000;", config)
        self.assertNotIn("rewrite ", config)
        self.assertNotIn("proxy_pass http://web:8000/;", config)
