import os
from pathlib import Path
from unittest import mock

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "palvelut.settings")

import django

django.setup()

from django.conf import settings
from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse

from palvelut.settings import _public_base_url


@override_settings(ALLOWED_HOSTS=["testserver"])
class RoutingContractTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_supported_locale_roots_are_owned_by_django(self):
        for locale in ("ru", "fi", "en"):
            response = self.client.get(f"/palvelut/{locale}/")
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, f'<html lang="{locale}">', html=False)

    def test_unsupported_locale_returns_real_404(self):
        response = self.client.get("/palvelut/sv/")
        self.assertEqual(response.status_code, 404)

    def test_public_mount_root_redirect_stays_inside_prefix(self):
        response = self.client.get("/palvelut/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/palvelut/en/")

    def test_every_public_discovery_route_keeps_mount_and_locale_prefix(self):
        routes = {
            "localized-home": reverse("localized-home", kwargs={"locale": "en"}),
            "discovery-search": reverse("discovery-search", kwargs={"locale": "en"}),
            "provider-profile": reverse(
                "provider-profile",
                kwargs={"locale": "en", "slug": "example-provider"},
            ),
            "city-category": reverse(
                "city-category",
                kwargs={"locale": "en", "city": "helsinki", "category": "accounting"},
            ),
        }
        self.assertEqual(
            routes,
            {
                "localized-home": "/palvelut/en/",
                "discovery-search": "/palvelut/en/search/",
                "provider-profile": "/palvelut/en/professionals/example-provider/",
                "city-category": "/palvelut/en/helsinki/accounting/",
            },
        )
        for route in routes.values():
            self.assertTrue(route.startswith("/palvelut/en/"), route)

    def test_unmounted_discovery_paths_are_not_public_routes(self):
        for path in (
            "/en/",
            "/en/search/",
            "/en/professionals/example-provider/",
            "/en/helsinki/accounting/",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_static_and_cookie_paths_keep_public_mount_prefix(self):
        self.assertEqual(settings.STATIC_URL, "/palvelut/static/")
        self.assertEqual(settings.LANGUAGE_COOKIE_PATH, "/palvelut/")
        self.assertEqual(settings.SESSION_COOKIE_PATH, "/palvelut/")
        self.assertEqual(settings.CSRF_COOKIE_PATH, "/palvelut/")
        response = self.client.get("/palvelut/en/")
        self.assertContains(response, "/palvelut/static/css/app.css")
        self.assertContains(response, "/palvelut/static/vendor/htmx.min.js")
        self.assertContains(response, "/palvelut/static/vendor/alpine.min.js")

    @override_settings(PUBLIC_BASE_URL="https://finrix.fi/palvelut")
    def test_canonical_and_hreflang_are_absolute_and_locale_specific(self):
        response = self.client.get("/palvelut/fi/")
        self.assertContains(
            response,
            '<link rel="canonical" href="https://finrix.fi/palvelut/fi/">',
            html=False,
        )
        for locale in ("ru", "fi", "en"):
            self.assertContains(
                response,
                f'<link rel="alternate" hreflang="{locale}" href="https://finrix.fi/palvelut/{locale}/">',
                html=False,
            )
        self.assertContains(
            response,
            '<link rel="alternate" hreflang="x-default" href="https://finrix.fi/palvelut/en/">',
            html=False,
        )

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
            with self.subTest(value=value), mock.patch.dict(os.environ, {"PUBLIC_BASE_URL": value}, clear=False):
                with self.assertRaises(RuntimeError):
                    _public_base_url()

    def test_nginx_proxy_does_not_rewrite_public_prefix(self):
        config = Path("infra/nginx/default.conf").read_text()
        self.assertIn("proxy_pass http://web:8000;", config)
        self.assertNotIn("rewrite ", config)
        self.assertNotIn("proxy_pass http://web:8000/;", config)
