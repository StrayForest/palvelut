from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_rollback_and_readiness_incident_drill_passes():
    result = subprocess.run(
        ["bash", str(ROOT / "infra/scripts/deploy-rollback-acceptance.sh")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "rollback_acceptance=pass" in result.stdout
    assert "simulated_incident=readiness_failure" in result.stdout
    assert "incident_containment=pass" in result.stdout
    assert "database_reverse_migration=not_attempted" in result.stdout
