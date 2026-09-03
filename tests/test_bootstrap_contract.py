import importlib.util
from pathlib import Path
import tomllib
import unittest

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
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.workflow = (self.root / ".github/workflows/p0-compose.yml").read_text()

    def test_python_and_django_contract_is_locked(self) -> None:
        project = tomllib.loads((self.root / "pyproject.toml").read_text())
        lock = tomllib.loads((self.root / "uv.lock").read_text())

        self.assertEqual(project["project"]["requires-python"], ">=3.13,<3.14")
        django = next(pkg for pkg in lock["package"] if pkg["name"] == "django")
        self.assertTrue(django["version"].startswith("5.2."))

    def test_domain_apps_match_architecture_modules(self) -> None:
        configured = {entry.split(".")[2] for entry in settings.DOMAIN_APPS}
        self.assertEqual(configured, EXPECTED_APPS)
        for app in EXPECTED_APPS:
            self.assertIsNotNone(importlib.util.find_spec(f"palvelut.apps.{app}"))

    def test_ci_proves_bootstrap_before_project_dependencies_are_installed(self) -> None:
        bootstrap_step = "- name: Verify canonical bootstrap from clean checkout"
        install_step = "- name: Install pinned CI tools"
        self.assertIn(bootstrap_step, self.workflow)
        self.assertLess(
            self.workflow.index(bootstrap_step), self.workflow.index(install_step)
        )
        self.assertIn("test ! -e .venv", self.workflow)
        self.assertIn("test ! -d frontend/node_modules", self.workflow)
        self.assertIn('PATH="$bootstrap_bin"', self.workflow)
        self.assertIn('"$bootstrap_bin/make" bootstrap', self.workflow)
        for command in ("git", "make", "docker"):
            self.assertIn(
                f'ln -s "$(command -v {command})" "$bootstrap_bin/{command}"',
                self.workflow,
            )


if __name__ == "__main__":
    unittest.main()
