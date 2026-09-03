import re
import unittest
from pathlib import Path


class WorkflowSecurityContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        workflow_path = self.root / ".github/workflows/p0-compose.yml"
        self.workflow = workflow_path.read_text()
        self.compose = (self.root / "compose.yml").read_text()
        self.playwright = (self.root / "playwright.config.js").read_text()
        self.dockerfiles = []
        self.dockerfiles.append((self.root / "Dockerfile").read_text())
        self.dockerfiles.append((self.root / "Dockerfile.e2e").read_text())

    def test_workflow_default_permissions_are_read_only(self) -> None:
        lines = self.workflow.splitlines()
        permissions_index = lines.index("permissions:")
        jobs_index = lines.index("jobs:")
        permission_lines = []
        for line in lines[permissions_index + 1 : jobs_index]:
            if line.strip():
                permission_lines.append(line.strip())
        self.assertEqual(permission_lines, ["contents: read"])

    def test_third_party_actions_use_full_commit_shas(self) -> None:
        pattern = r"(?m)^\s*-?\s*uses:\s*([^\s#]+)"
        uses = re.findall(pattern, self.workflow)
        for action in uses:
            self.assertRegex(action, r"^[^@]+@[0-9a-f]{40}$")

    def test_playwright_evidence_is_retained_as_an_artifact(self) -> None:
        self.assertIn("- name: Upload Playwright evidence", self.workflow)
        self.assertIn("if: always()", self.workflow)
        self.assertRegex(
            self.workflow,
            r"uses: actions/upload-artifact@[0-9a-f]{40}",
        )
        self.assertIn("repo/playwright-report/", self.workflow)
        self.assertIn("repo/test-results/", self.workflow)
        self.assertIn("if-no-files-found: error", self.workflow)
        self.assertIn('outputDir: "test-results"', self.playwright)
        self.assertIn(
            '["html", { outputFolder: "playwright-report", open: "never" }]',
            self.playwright,
        )
        self.assertIn('screenshot: "only-on-failure"', self.playwright)
        self.assertIn('trace: "retain-on-failure"', self.playwright)

    def test_compose_images_are_immutable_and_version_documented(self) -> None:
        lines = self.compose.splitlines()
        image_indexes = []
        for index, line in enumerate(lines):
            if re.match(r"^\s+image:\s+", line):
                image_indexes.append(index)
        self.assertGreater(len(image_indexes), 0)

        for index in image_indexes:
            image = lines[index].split("image:", 1)[1].strip()
            self.assertRegex(image, r"^[^\s]+@sha256:[0-9a-f]{64}$")
            previous = lines[index - 1].strip() if index else ""
            self.assertTrue(previous.startswith("# "))

    def test_all_dockerfile_base_images_are_digest_pinned(self) -> None:
        pattern = r"(?m)^FROM\s+(\S+)(?:\s+AS\s+\S+)?$"
        for dockerfile in self.dockerfiles:
            images = re.findall(pattern, dockerfile)
            self.assertGreater(len(images), 0)
            for image in images:
                self.assertRegex(image, r"^[^\s]+@sha256:[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
