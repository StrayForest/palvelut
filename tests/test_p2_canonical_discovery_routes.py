import os
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "palvelut.settings")

import django

django.setup()

from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse


LOCAL_MEMORY_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "canonical-discovery-routes",
    }
}


@override_settings(ALLOWED_HOSTS=["testserver"], CACHES=LOCAL_MEMORY_CACHE)
class CanonicalDiscoveryRouteTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_discovery_routes_keep_public_mount_and_russian_prefix(self):
        routes = (
            reverse("localized-home", kwargs={"locale": "ru"}),
            reverse("discovery-search", kwargs={"locale": "ru"}),
            reverse(
                "provider-profile",
                kwargs={"locale": "ru", "slug": "example-provider"},
            ),
            reverse(
                "city-category",
                kwargs={
                    "locale": "ru",
                    "city": "helsinki",
                    "category": "accounting",
                },
            ),
        )
        self.assertEqual(
            routes,
            (
                "/palvelut/ru/",
                "/palvelut/ru/search/",
                "/palvelut/ru/professionals/example-provider/",
                "/palvelut/ru/helsinki/accounting/",
            ),
        )

    def test_public_mount_redirects_to_russian_home(self):
        response = self.client.get("/palvelut/")
        self.assertRedirects(response, "/palvelut/ru/", fetch_redirect_response=False)

    def test_finnish_and_english_ui_routes_are_unsupported(self):
        for locale in ("fi", "en"):
            paths = (
                f"/palvelut/{locale}/",
                f"/palvelut/{locale}/search/",
                f"/palvelut/{locale}/for-professionals/",
            )
            for path in paths:
                with self.subTest(path=path):
                    self.assertEqual(self.client.get(path).status_code, 404)

    def test_unmounted_discovery_paths_are_not_public_routes(self):
        paths = (
            "/ru/",
            "/ru/search/",
            "/ru/professionals/example-provider/",
            "/ru/helsinki/accounting/",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_proxy_preserves_public_mount_prefix(self):
        config = Path("infra/nginx/default.conf").read_text()
        self.assertIn("proxy_pass http://web:8000;", config)
        self.assertNotIn("rewrite ", config)
        self.assertNotIn("proxy_pass http://web:8000/;", config)
