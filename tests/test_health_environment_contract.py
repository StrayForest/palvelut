import os
from unittest import mock

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "palvelut.settings")

import django

django.setup()

from django.test import Client, SimpleTestCase, override_settings

from palvelut import settings as app_settings


@override_settings(ALLOWED_HOSTS=["testserver"])
class HealthContractTests(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    def test_liveness_is_dependency_free_and_not_cacheable(self):
        with mock.patch("palvelut.views.connection") as database, mock.patch("palvelut.views.cache") as cache:
            response = self.client.get("/palvelut/health/live")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(response["Cache-Control"], "no-store")
        database.assert_not_called()
        cache.assert_not_called()

    def test_readiness_checks_database_and_cache_without_exposing_details(self):
        cursor = mock.MagicMock()
        context = mock.MagicMock()
        context.__enter__.return_value = cursor
        database = mock.MagicMock()
        database.cursor.return_value = context
        cache = mock.MagicMock()
        cache.get.return_value = "ok"

        with mock.patch("palvelut.views.connection", database), mock.patch("palvelut.views.cache", cache):
            response = self.client.get("/palvelut/health/ready")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(response["Cache-Control"], "no-store")
        cursor.execute.assert_called_once_with("SELECT 1")
        cache.set.assert_called_once_with("health-ready", "ok", timeout=5)
        cache.get.assert_called_once_with("health-ready")

    def test_readiness_fails_closed_when_database_or_cache_is_unavailable(self):
        cases = ("database", "cache")
        for failed_dependency in cases:
            with self.subTest(failed_dependency=failed_dependency):
                database = mock.MagicMock()
                context = mock.MagicMock()
                cursor = mock.MagicMock()
                context.__enter__.return_value = cursor
                database.cursor.return_value = context
                cache = mock.MagicMock()
                cache.get.return_value = "ok"
                if failed_dependency == "database":
                    database.cursor.side_effect = RuntimeError("database detail must not leak")
                else:
                    cache.get.return_value = None

                with mock.patch("palvelut.views.connection", database), mock.patch("palvelut.views.cache", cache):
                    response = self.client.get("/palvelut/health/ready")

                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json(), {"status": "unavailable"})
                self.assertEqual(response["Cache-Control"], "no-store")
                self.assertNotIn("database", response.content.decode())
                self.assertNotIn("cache", response.content.decode())


class EnvironmentValidationTests(SimpleTestCase):
    def test_local_defaults_remain_allowed(self):
        with mock.patch.object(app_settings, "ENVIRONMENT", "local"):
            app_settings._validate_environment()

    def test_production_like_environment_requires_safe_explicit_configuration(self):
        with (
            mock.patch.object(app_settings, "ENVIRONMENT", "production"),
            mock.patch.object(app_settings, "DEBUG", True),
            mock.patch.object(app_settings, "SECRET_KEY", "p0-bootstrap-only-not-for-production"),
            mock.patch.object(app_settings, "ALLOWED_HOSTS", ["localhost"]),
            mock.patch.object(app_settings, "PUBLIC_BASE_URL", "http://localhost:8000/palvelut"),
            mock.patch.dict(os.environ, {}, clear=True),
        ):
            with self.assertRaisesRegex(RuntimeError, "Unsafe production configuration"):
                app_settings._validate_environment()

    def test_production_like_environment_accepts_explicit_https_configuration(self):
        env = {
            "DJANGO_SECRET_KEY": "explicit-secret",
            "DJANGO_ALLOWED_HOSTS": "finrix.fi",
        }
        with (
            mock.patch.object(app_settings, "ENVIRONMENT", "staging"),
            mock.patch.object(app_settings, "DEBUG", False),
            mock.patch.object(app_settings, "SECRET_KEY", "explicit-secret"),
            mock.patch.object(app_settings, "ALLOWED_HOSTS", ["finrix.fi"]),
            mock.patch.object(app_settings, "PUBLIC_BASE_URL", "https://finrix.fi/palvelut"),
            mock.patch.dict(os.environ, env, clear=True),
        ):
            app_settings._validate_environment()
