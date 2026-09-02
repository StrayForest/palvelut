import re
import unittest
from pathlib import Path


class MakeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.makefile = (self.root / "Makefile").read_text()
        self.reset_script = (self.root / "infra/scripts/reset-local.sh").read_text()
        self.smoke_script = (self.root / "infra/scripts/smoke.sh").read_text()

    def test_current_local_targets_are_declared(self) -> None:
        for target in ("bootstrap", "dev", "reset", "test", "smoke"):
            self.assertRegex(self.makefile, rf"(?m)^{target}:\s*$")

    def test_compose_commands_are_project_scoped(self) -> None:
        self.assertIn("docker compose --project-name palvelut", self.makefile)
        self.assertIn("docker compose --project-name palvelut", self.reset_script)
        self.assertIn("docker compose --project-name palvelut", self.smoke_script)

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

    def test_makefile_does_not_claim_browser_gate_yet(self) -> None:
        self.assertIsNone(re.search(r"(?m)^e2e:\s*$", self.makefile))


if __name__ == "__main__":
    unittest.main()
