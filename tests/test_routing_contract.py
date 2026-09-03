import os
import unittest
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "palvelut.settings")

import django

django.setup()

from django.conf import settings
from django.test import Client


class RoutingContractTests(unittest.TestCase):
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

    def test_static_url_keeps_public_mount_prefix(self):
        self.assertEqual(settings.STATIC_URL, "/palvelut/static/")
        response = self.client.get("/palvelut/en/")
        self.assertContains(response, '/palvelut/static/css/app.css')
        self.assertContains(response, '/palvelut/static/vendor/htmx.min.js')
        self.assertContains(response, '/palvelut/static/vendor/alpine.min.js')

    def test_nginx_proxy_does_not_rewrite_public_prefix(self):
        config = Path("infra/nginx/default.conf").read_text()
        self.assertIn("proxy_pass http://web:8000;", config)
        self.assertNotIn("rewrite ", config)
        self.assertNotIn("proxy_pass http://web:8000/;", config)


if __name__ == "__main__":
    unittest.main()
