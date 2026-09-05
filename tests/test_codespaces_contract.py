import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CodespacesContractTests(unittest.TestCase):
    def test_devcontainer_forwards_preview_and_mailpit(self) -> None:
        config = json.loads((ROOT / ".devcontainer" / "devcontainer.json").read_text())

        self.assertEqual(config["forwardPorts"], [8000, 8025])
        self.assertEqual(
            config["postStartCommand"],
            "bash .devcontainer/start-codespace.sh",
        )
        self.assertTrue(
            any("docker-in-docker" in feature for feature in config["features"])
        )

    def test_codespaces_overlay_uses_forwarded_https_origin(self) -> None:
        overlay = (ROOT / ".devcontainer" / "compose.codespaces.yml").read_text()

        self.assertIn("PUBLIC_BASE_URL", overlay)
        self.assertIn("CODESPACE_NAME", overlay)
        self.assertIn("DJANGO_ALLOWED_HOSTS", overlay)
        self.assertIn("DJANGO_CSRF_TRUSTED_ORIGINS", overlay)
        self.assertIn("app.github.dev", overlay)

    def test_codespaces_start_script_waits_and_emits_localhost_forward_links(
        self,
    ) -> None:
        script = ROOT / ".devcontainer" / "start-codespace.sh"
        subprocess.run(["bash", "-n", str(script)], check=True)
        content = script.read_text()

        self.assertIn("manage.py migrate --noinput", content)
        self.assertIn("manage.py seed_demo", content)
        self.assertIn("compose.codespaces.yml", content)
        self.assertIn("http://127.0.0.1:8000/palvelut/health/live", content)
        self.assertIn("http://127.0.0.1:8025/", content)
        self.assertIn("http://localhost:8000/palvelut/ru/", content)
        self.assertIn("http://localhost:8025/", content)
        self.assertIn("PORTS tab", content)


if __name__ == "__main__":
    unittest.main()
