from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_zero_failure_switch_and_unsafe_rollback_stop():
    result = subprocess.run(
        ["bash", str(ROOT / "infra/scripts/zero-failure-deploy-acceptance.sh")],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "synthetic_requests=240" in result.stdout
    assert "synthetic_failures=0" in result.stdout
    assert "upstream_switch_observed=pass" in result.stdout
    assert "unsafe_database_rollback=operator_action_required" in result.stdout
    assert "database_reverse_migration=not_attempted" in result.stdout
