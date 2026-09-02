import importlib.util
import unittest
from pathlib import Path
import tomllib

from palvelut import settings


EXPECTED_APPS = {
    "accounts",
    "taxonomy",
    "providers",
    "publishing",
    "verification",
    "moderation",
    "discovery",
    "analytics",
    "content",
}


class BootstrapContractTests(unittest.TestCase):
    def test_python_and_django_contract_is_locked(self) -> None:
        root = Path(__file__).resolve().parents[1]
        project = tomllib.loads((root / "pyproject.toml").read_text())
        lock = tomllib.loads((root / "uv.lock").read_text())

        self.assertEqual(project["project"]["requires-python"], ">=3.13,<3.14")
        django = next(pkg for pkg in lock["package"] if pkg["name"] == "django")
        self.assertTrue(django["version"].startswith("5.2."))

    def test_domain_apps_match_architecture_modules(self) -> None:
        configured = {entry.split(".")[2] for entry in settings.DOMAIN_APPS}
        self.assertEqual(configured, EXPECTED_APPS)
        for app in EXPECTED_APPS:
            self.assertIsNotNone(importlib.util.find_spec(f"palvelut.apps.{app}"))


if __name__ == "__main__":
    unittest.main()
