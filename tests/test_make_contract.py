import unittest
from pathlib import Path


class MakeContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.makefile = (self.root / "Makefile").read_text()
        self.reset_script = (self.root / "infra/scripts/reset-local.sh").read_text()
        self.smoke_script = (self.root / "infra/scripts/smoke.sh").read_text()
        self.e2e_script = (self.root / "infra/scripts/e2e.sh").read_text()
        self.test_script = (
            self.root / "infra/scripts/test-in-container.sh"
        ).read_text()
        self.compose = (self.root / "compose.yml").read_text()
        self.workflow = (self.root / ".github/workflows/p0-compose.yml").read_text()
        self.e2e_dockerfile = (self.root / "Dockerfile.e2e").read_text()
        self.quality_dockerfile = (self.root / "Dockerfile.quality").read_text()

    def test_current_local_targets_are_declared(self) -> None:
        for target in ("bootstrap", "dev", "reset", "test", "e2e", "smoke"):
            self.assertRegex(self.makefile, rf"(?m)^{target}:\s*$")

    def test_compose_commands_are_project_scoped_and_overridable(self) -> None:
        self.assertIn("COMPOSE_PROJECT_NAME ?= palvelut", self.makefile)
        self.assertIn(
            "docker compose --project-name $(COMPOSE_PROJECT_NAME)", self.makefile
        )
        self.assertIn("docker compose --project-name palvelut", self.reset_script)
        for script in (self.smoke_script, self.e2e_script):
            self.assertIn(
                'COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-palvelut}"', script
            )
            self.assertIn(
                'docker compose --project-name "$COMPOSE_PROJECT_NAME"', script
            )

    def test_dev_prepares_clean_database_before_attached_stack(self) -> None:
        dev_block = self.makefile.split("\ndev:\n", 1)[1].split("\nreset:\n", 1)[0]
        self.assertIn("up -d --build postgres valkey mailpit minio", dev_block)
        self.assertIn("run --rm web python manage.py migrate --noinput", dev_block)
        self.assertTrue(dev_block.rstrip().endswith("$(COMPOSE) up --build"))

    def test_ci_proves_make_dev_starts_complete_stack(self) -> None:
        self.assertIn("Verify canonical development startup", self.workflow)
        self.assertIn("setsid make dev", self.workflow)
        for service in (
            "postgres",
            "valkey",
            "mailpit",
            "minio",
            "web",
            "worker",
            "nginx",
        ):
            self.assertIn(service, self.workflow)
        self.assertIn("http://127.0.0.1:8000/palvelut/en/", self.workflow)

    def test_ci_uses_fresh_isolated_postgres_and_valkey(self) -> None:
        self.assertIn(
            "COMPOSE_PROJECT_NAME: palvelut-ci-${{ github.run_id }}-${{ github.run_attempt }}",
            self.workflow,
        )
        self.assertIn('case "$COMPOSE_PROJECT_NAME" in', self.workflow)
        self.assertIn("palvelut-ci-*)", self.workflow)
        self.assertIn("down -v --remove-orphans || true", self.workflow)
        self.assertIn("pull postgres valkey", self.workflow)
        self.assertIn("up -d --force-recreate --wait postgres valkey", self.workflow)
        self.assertIn("show server_version;", self.workflow)
        self.assertIn("grep -E '^18\\.'", self.workflow)
        self.assertIn("valkey-cli INFO server", self.workflow)
        self.assertIn("grep -E '^valkey_version:8\\.'", self.workflow)
        self.assertNotIn("--project-name palvelut up -d postgres valkey", self.workflow)

    def test_reset_refuses_production_like_contexts(self) -> None:
        for value in ("prod", "production", "stage", "staging"):
            self.assertIn(value, self.reset_script)
        self.assertIn("DJANGO_DEBUG:-1", self.reset_script)
        self.assertIn("down -v --remove-orphans", self.reset_script)

    def test_make_test_runs_every_non_browser_gate_in_container(self) -> None:
        test_block = self.makefile.split("\ntest:\n", 1)[1].split("\ne2e:\n", 1)[0]
        self.assertIn("--profile quality build quality", test_block)
        self.assertIn(
            "--profile quality run --rm --no-deps quality ",
            test_block,
        )
        self.assertIn("bash infra/scripts/test-in-container.sh", test_block)
        self.assertIn("dockerfile: Dockerfile.quality", self.compose)
        self.assertIn('profiles: ["quality"]', self.compose)
        self.assertIn("python:3.13-slim@sha256:", self.quality_dockerfile)

        required_commands = (
            "uv lock --check",
            "ruff check",
            "ruff format --check",
            "mypy ",
            "pip-audit --disable-pip",
            "detect-secrets scan",
            "makemigrations --check --dry-run",
            "check --deploy --fail-level ERROR",
            "unittest discover",
        )
        for command in required_commands:
            self.assertIn(command, self.test_script)

    def test_smoke_is_disposable_and_cleans_up(self) -> None:
        self.assertIn("trap cleanup EXIT", self.smoke_script)
        self.assertIn("down -v --remove-orphans", self.smoke_script)
        self.assertIn("manage.py migrate --noinput", self.smoke_script)
        self.assertIn("manage.py check", self.smoke_script)

    def test_e2e_is_disposable_and_runs_playwright_in_compose(self) -> None:
        self.assertIn("trap cleanup EXIT", self.e2e_script)
        self.assertIn("down -v --remove-orphans", self.e2e_script)
        self.assertIn("run --rm e2e", self.e2e_script)
        self.assertIn("dockerfile: Dockerfile.e2e", self.compose)
        self.assertIn('profiles: ["e2e"]', self.compose)
        self.assertIn(
            "mcr.microsoft.com/playwright:v1.62.1-noble@sha256:", self.e2e_dockerfile
        )
        self.assertIn('"@playwright/test@1.62.1"', self.e2e_dockerfile)


if __name__ == "__main__":
    unittest.main()
