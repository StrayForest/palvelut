import unittest
from pathlib import Path


class MakeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.makefile = (self.root / "Makefile").read_text()
        self.reset_script = (self.root / "infra/scripts/reset-local.sh").read_text()
        self.smoke_script = (self.root / "infra/scripts/smoke.sh").read_text()
        self.e2e_script = (self.root / "infra/scripts/e2e.sh").read_text()
        self.compose = (self.root / "compose.yml").read_text()
        self.e2e_dockerfile = (self.root / "Dockerfile.e2e").read_text()

    def test_current_local_targets_are_declared(self) -> None:
        for target in ("bootstrap", "dev", "reset", "test", "e2e", "smoke"):
            self.assertRegex(self.makefile, rf"(?m)^{target}:\s*$")

    def test_compose_commands_are_project_scoped(self) -> None:
        self.assertIn("docker compose --project-name palvelut", self.makefile)
        self.assertIn("docker compose --project-name palvelut", self.reset_script)
        self.assertIn("docker compose --project-name palvelut", self.smoke_script)
        self.assertIn("docker compose --project-name palvelut", self.e2e_script)

    def test_reset_refuses_production_like_contexts(self) -> None:
        for value in ("prod", "production", "stage", "staging"):
            self.assertIn(value, self.reset_script)
        self.assertIn('DJANGO_DEBUG:-1', self.reset_script)
        self.assertIn("down -v --remove-orphans", self.reset_script)

    def test_smoke_is_disposable_and_cleans_up(self) -> None:
        self.assertIn("trap cleanup EXIT", self.smoke_script)
        self.assertIn("down -v --remove-orphans", self.smoke_script)
        self.assertIn("manage.py migrate --noinput", self.smoke_script)
        self.assertIn("manage.py check", self.smoke_script)

    def test_e2e_is_disposable_and_runs_playwright_in_compose(self) -> None:
        self.assertIn("trap cleanup EXIT", self.e2e_script)
        self.assertIn("down -v --remove-orphans", self.e2e_script)
        self.assertIn('run --rm e2e', self.e2e_script)
        self.assertIn('dockerfile: Dockerfile.e2e', self.compose)
        self.assertIn('profiles: ["e2e"]', self.compose)
        self.assertIn("mcr.microsoft.com/playwright:v1.62.1-noble@sha256:", self.e2e_dockerfile)
        self.assertIn('"@playwright/test@1.62.1"', self.e2e_dockerfile)


if __name__ == "__main__":
    unittest.main()
