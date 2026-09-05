import re
import unittest
from pathlib import Path
import tomllib

from palvelut import settings


class ComposeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.compose = (self.root / "compose.yml").read_text()
        self.dockerfile = (self.root / "Dockerfile").read_text()

    def test_required_services_are_declared(self) -> None:
        for service in (
            "postgres",
            "valkey",
            "mailpit",
            "minio",
            "web",
            "worker",
            "nginx",
        ):
            self.assertIn(f"\n  {service}:\n", self.compose)

    def test_database_and_cache_are_not_published_to_host(self) -> None:
        self.assertNotIn("5432:5432", self.compose)
        self.assertNotIn("6379:6379", self.compose)

    def test_runtime_images_are_digest_pinned(self) -> None:
        image_lines = re.findall(r"(?m)^\s+image:\s+(\S+)$", self.compose)
        self.assertEqual(len(image_lines), 5)
        for image in image_lines:
            self.assertRegex(image, r"@sha256:[0-9a-f]{64}$")

        from_images = re.findall(r"(?m)^FROM\s+(\S+)(?:\s+AS\s+\S+)?$", self.dockerfile)
        self.assertGreaterEqual(len(from_images), 1)
        for image in from_images:
            self.assertRegex(image, r"@sha256:[0-9a-f]{64}$")

    def test_postgres_18_uses_version_aware_volume_root(self) -> None:
        self.assertIn("postgres_data:/var/lib/postgresql", self.compose)
        self.assertNotIn("postgres_data:/var/lib/postgresql/data", self.compose)

    def test_runtime_dependencies_are_declared(self) -> None:
        project = tomllib.loads((self.root / "pyproject.toml").read_text())
        dependencies = project["project"]["dependencies"]
        deps = "\n".join(dependencies).lower()
        for dependency in ("celery", "gunicorn", "psycopg", "uvicorn-worker"):
            self.assertIn(dependency, deps)
        uvicorn_worker = next(
            dep for dep in dependencies if dep.lower().startswith("uvicorn-worker")
        )
        self.assertEqual(uvicorn_worker, "uvicorn-worker>=0.4,<0.5")

    def test_django_is_wired_to_postgres_valkey_mailpit_and_minio(self) -> None:
        self.assertEqual(
            settings.DATABASES["default"]["ENGINE"], "django.db.backends.postgresql"
        )
        self.assertEqual(
            settings.CACHES["default"]["BACKEND"],
            "django.core.cache.backends.redis.RedisCache",
        )
        self.assertTrue(settings.CELERY_BROKER_URL.startswith("redis://"))
        self.assertEqual(settings.EMAIL_HOST, "mailpit")
        self.assertEqual(settings.OBJECT_STORAGE_ENDPOINT_URL, "http://minio:9000")


if __name__ == "__main__":
    unittest.main()
