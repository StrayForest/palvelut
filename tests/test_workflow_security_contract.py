import re
import unittest
from pathlib import Path


class WorkflowSecurityContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).resolve().parents[1]
        self.workflow = (self.root / ".github/workflows/p0-compose.yml").read_text()
        self.compose = (self.root / "compose.yml").read_text()
        self.dockerfiles = [
            (self.root / "Dockerfile").read_text(),
            (self.root / "Dockerfile.e2e").read_text(),
        ]

    def test_workflow_default_permissions_are_read_only(self) -> None:
        lines = self.workflow.splitlines()
        permissions_index = lines.index("permissions:")
        jobs_index = lines.index("jobs:")
        permission_lines = [line.strip() for line in lines[permissions_index + 1 : jobs_index] if line.strip()]
        self.assertEqual(permission_lines, ["contents: read"])

    def test_third_party_actions_use_full_commit_shas(self) -> None:
        uses = re.findall(r"(?m)^\s*-?\s*uses:\s*([^\s#]+)", self.workflow)
        for action in uses:
            self.assertRegex(
                action,
                r"^[^@]+@[0-9a-f]{40}$",
                msg=f"third-party action must use a full commit SHA: {action}",
            )

    def test_compose_images_are_immutable_and_version_documented(self) -> None:
        lines = self.compose.splitlines()
        image_indexes = [index for index, line in enumerate(lines) if re.match(r"^\s+image:\s+", line)]
        self.assertGreater(len(image_indexes), 0)

        for index in image_indexes:
            image = lines[index].split("image:", 1)[1].strip()
            self.assertRegex(image, r"^[^\s]+@sha256:[0-9a-f]{64}$")
            previous = lines[index - 1].strip() if index else ""
            self.assertTrue(previous.startswith("# "), msg=f"missing version comment for {image}")

    def test_all_dockerfile_base_images_are_digest_pinned(self) -> None:
        for dockerfile in self.dockerfiles:
            images = re.findall(r"(?m)^FROM\s+(\S+)(?:\s+AS\s+\S+)?$", dockerfile)
            self.assertGreater(len(images), 0)
            for image in images:
                self.assertRegex(image, r"^[^\s]+@sha256:[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
