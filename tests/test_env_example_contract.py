from pathlib import Path

from django.test import SimpleTestCase


class EnvExampleContractTests(SimpleTestCase):
    def test_example_contains_runtime_settings_without_real_credentials(self):
        path = Path(__file__).resolve().parent.parent / ".env.example"
        values = {}
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            key, value = line.split("=", 1)
            values[key] = value

        expected_keys = {
            "PALVELUT_ENVIRONMENT",
            "DJANGO_SECRET_KEY",
            "DJANGO_DEBUG",
            "DJANGO_ALLOWED_HOSTS",
            "PUBLIC_BASE_URL",
            "SYNTHETIC_MONITOR_TOKEN",
            "POSTGRES_DB",
            "POSTGRES_USER",
            "POSTGRES_PASSWORD",
            "POSTGRES_HOST",
            "POSTGRES_PORT",
            "VALKEY_URL",
            "CELERY_BROKER_URL",
            "CELERY_RESULT_BACKEND",
            "EMAIL_HOST",
            "EMAIL_PORT",
            "DEFAULT_FROM_EMAIL",
            "S3_ENDPOINT_URL",
            "S3_ACCESS_KEY_ID",
            "S3_SECRET_ACCESS_KEY",
            "S3_BUCKET_NAME",
        }
        self.assertEqual(set(values), expected_keys)

        for key in {
            "DJANGO_SECRET_KEY",
            "SYNTHETIC_MONITOR_TOKEN",
            "POSTGRES_PASSWORD",
            "S3_ACCESS_KEY_ID",
            "S3_SECRET_ACCESS_KEY",
            "S3_BUCKET_NAME",
        }:
            self.assertTrue(values[key].startswith("replace-me-"), key)

        content = path.read_text(encoding="utf-8")
        self.assertNotIn("palvelut-local-only", content)
        self.assertNotIn("https://finrix.fi", content)
        self.assertIn("example.invalid", content)
