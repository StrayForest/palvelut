import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKUP = ROOT / "infra" / "scripts" / "backup-production.sh"
RESTORE = ROOT / "infra" / "scripts" / "restore-drill.sh"
RUNBOOK = ROOT / "docs" / "runbooks" / "database-restore.md"


class BackupRestoreContractTests(unittest.TestCase):
    def test_shell_scripts_are_valid(self) -> None:
        subprocess.run(["bash", "-n", str(BACKUP)], check=True)
        subprocess.run(["bash", "-n", str(RESTORE)], check=True)

    def test_backup_is_encrypted_offsite_and_retained(self) -> None:
        content = BACKUP.read_text()
        self.assertIn("RESTIC_REPOSITORY", content)
        self.assertIn("RESTIC_PASSWORD_FILE", content)
        self.assertIn("pg_dump", content)
        self.assertIn("rclone sync", content)
        self.assertIn("media.sha256", content)
        self.assertIn("restic backup", content)
        self.assertIn("restic check", content)
        self.assertIn("--keep-daily 14", content)
        self.assertIn("--keep-weekly 8", content)
        self.assertNotIn("set -x", content)

    def test_restore_uses_isolated_unpublished_database(self) -> None:
        content = RESTORE.read_text()
        self.assertIn("restic restore latest", content)
        self.assertIn("sha256sum -c media.sha256", content)
        self.assertIn("postgres:18-alpine@sha256:", content)
        self.assertIn("pg_restore", content)
        self.assertIn("django_migrations", content)
        self.assertNotIn("-p 5432", content)
        self.assertNotIn("--network host", content)

    def test_restore_proves_rpo_and_rto_with_safe_evidence(self) -> None:
        content = RESTORE.read_text()
        self.assertIn(
            "restic snapshots --latest 1 --tag production --host "
            "palvelut-production --json",
            content,
        )
        self.assertIn("snapshot_age_seconds <= 86400", content)
        self.assertIn("rpo_target_seconds=86400", content)
        self.assertIn("duration <= 14400", content)
        self.assertIn("rto_target_seconds=14400", content)
        self.assertIn("command=infra/scripts/restore-drill.sh", content)
        self.assertNotIn("set -x", content)

    def test_runbook_pins_rpo_rto_and_no_sensitive_evidence(self) -> None:
        content = RUNBOOK.read_text()
        self.assertIn("RPO <= 24h", content)
        self.assertIn("RTO <= 4h", content)
        self.assertIn("Do not record backup credentials", content)
        self.assertIn("monthly isolated restore drill", content.casefold())
        self.assertIn("snapshot_age_seconds", content)
        self.assertIn("duration_seconds", content)


if __name__ == "__main__":
    unittest.main()
