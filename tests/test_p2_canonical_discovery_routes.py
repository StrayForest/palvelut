import os
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "palvelut.settings")

import django

django.setup()

from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse


@override_settings(ALLOWED_HOSTS=["testserver"])
class CanonicalDiscoveryRouteTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_discovery_routes_keep_public_mount_and_locale_prefix(self):
        routes = (
            reverse("localized-home", kwargs={"locale": "en"}),
            reverse("discovery-search", kwargs={"locale": "en"}),
            reverse(
                "provider-profile",
                kwargs={"locale": "en", "slug": "example-provider"},
            ),
            reverse(
                "city-category",
                kwargs={
                    "locale": "en",
                    "city": "helsinki",
                    "category": "accounting",
                },
            ),
        )
        self.assertEqual(
            routes,
            (
                "/palvelut/en/",
                "/palvelut/en/search/",
                "/palvelut/en/professionals/example-provider/",
                "/palvelut/en/helsinki/accounting/",
            ),
        )

    def test_unmounted_discovery_paths_are_not_public_routes(self):
        paths = (
            "/en/",
            "/en/search/",
            "/en/professionals/example-provider/",
            "/en/helsinki/accounting/",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 404)

    def test_proxy_preserves_public_mount_prefix(self):
        config = Path("infra/nginx/default.conf").read_text()
        self.assertIn("proxy_pass http://web:8000;", config)
        self.assertNotIn("rewrite ", config)
        self.assertNotIn("proxy_pass http://web:8000/;", config)
