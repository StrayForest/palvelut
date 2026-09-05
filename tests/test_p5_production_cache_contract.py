import json
import os
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProductionCacheContractTests(unittest.TestCase):
    def test_production_compose_requires_immutable_app_image(self) -> None:
        compose = (ROOT / "compose.production.yml").read_text()

        self.assertIn("PALVELUT_ENVIRONMENT: production", compose)
        self.assertIn("image: ${PALVELUT_IMAGE:?", compose)
        self.assertEqual(compose.count("image: ${PALVELUT_IMAGE:?"), 2)
        self.assertIn('"127.0.0.1:8080:8000"', compose)
        self.assertIn("internal: true", compose)
        self.assertNotIn("5432:5432", compose)
        self.assertNotIn("6379:6379", compose)
        self.assertNotIn("DJANGO_SECRET_KEY: p", compose)

    def test_production_compose_wrapper_refuses_tags(self) -> None:
        script = ROOT / "infra" / "scripts" / "production-compose.sh"
        subprocess.run(["bash", "-n", str(script)], check=True)
        content = script.read_text()

        self.assertIn("ghcr\\.io/strayforest/palvelut@sha256:", content)
        self.assertIn("/etc/palvelut/production.env", content)
        self.assertNotIn("latest", content)

    def test_cloudflare_contract_bypasses_state_and_respects_origin_ttl(self) -> None:
        contract = json.loads(
            (ROOT / "infra" / "cloudflare" / "rules.json").read_text()
        )
        rules = {rule["name"]: rule for rule in contract["cache_rules"]}
        bypass = rules["palvelut-bypass-sensitive-or-stateful"]
        public = rules["palvelut-anonymous-public-respect-origin"]

        self.assertEqual(bypass["action"], "bypass_cache")
        for marker in (
            'headers["cookie"]',
            "/palvelut/account/",
            "/palvelut/staff/",
            "/palvelut/report/",
            "/palvelut/health/ready",
        ):
            self.assertIn(marker, bypass["expression"])
        self.assertEqual(public["action"], "cache_eligible")
        self.assertEqual(public["edge_ttl_mode"], "respect_origin")
        self.assertEqual(public["browser_ttl_mode"], "respect_origin")

    def test_cloudflare_contract_has_waf_and_bounded_rate_limits(self) -> None:
        contract = json.loads(
            (ROOT / "infra" / "cloudflare" / "rules.json").read_text()
        )

        self.assertEqual(
            contract["waf"]["managed_rulesets"],
            ["cloudflare-managed-ruleset", "cloudflare-owasp-core-ruleset"],
        )
        names = {rule["name"] for rule in contract["rate_limits"]}
        self.assertEqual(
            names,
            {
                "palvelut-login",
                "palvelut-password-reset",
                "palvelut-register",
                "palvelut-content-report",
            },
        )
        for rule in contract["rate_limits"]:
            self.assertGreater(rule["requests"], 0)
            self.assertGreater(rule["period_seconds"], 0)
            self.assertGreater(rule["mitigation_timeout_seconds"], 0)

    def test_purge_workflow_is_exact_url_only(self) -> None:
        contract = json.loads(
            (ROOT / "infra" / "cloudflare" / "rules.json").read_text()
        )
        purge = contract["purge"]
        script = ROOT / purge["script"]
        subprocess.run(["bash", "-n", str(script)], check=True)

        self.assertEqual(purge["mode"], "exact_url_only")
        self.assertFalse(purge["purge_everything"])
        result = subprocess.run(
            ["bash", str(script), "--dry-run", "/palvelut/ru/"],
            check=True,
            text=True,
            capture_output=True,
            env={**os.environ, "CLOUDFLARE_API_TOKEN": "must-not-be-needed"},
        )
        self.assertEqual(
            json.loads(result.stdout),
            {"files": ["https://finrix.fi/palvelut/ru/"]},
        )
        rejected = subprocess.run(
            ["bash", str(script), "--dry-run", "/admin/"],
            text=True,
            capture_output=True,
        )
        self.assertNotEqual(rejected.returncode, 0)

    def test_host_nginx_does_not_create_a_second_cache(self) -> None:
        nginx = (
            ROOT / "infra" / "ansible" / "templates" / "palvelut-nginx.conf.j2"
        ).read_text()

        self.assertIn("proxy_pass {{ palvelut_upstream }};", nginx)
        self.assertNotIn("proxy_cache ", nginx)
        self.assertNotIn("proxy_ignore_headers", nginx)

    def test_main_builds_a_commit_tagged_ghcr_image(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "p5-image.yml").read_text()

        self.assertIn("branches: [main]", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("packages: write", workflow)
        self.assertIn('"${image}:${SHA}"', workflow)
        self.assertIn("RepoDigests", workflow)
        self.assertNotIn(":latest", workflow)


if __name__ == "__main__":
    unittest.main()
