from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "infra/scripts/rehearsal-host.sh").read_text()
WORKFLOW = (ROOT / ".github/workflows/p5-ansible.yml").read_text()


def test_rehearsal_uses_disposable_ubuntu_host_and_ansible_twice():
    assert "FROM ubuntu:24.04" in SCRIPT
    assert "--privileged" in SCRIPT
    assert "ansible-playbook" in SCRIPT
    assert SCRIPT.count('ansible-playbook -i "$inventory"') == 2
    assert "changed=0" in SCRIPT
    assert "trap cleanup EXIT" in SCRIPT


def test_rehearsal_runs_existing_isolated_restore_without_production_data():
    assert "infra/scripts/restore-drill.sh" in SCRIPT
    assert "palvelut-rehearsal-restic" in SCRIPT
    assert "fixture-only" in SCRIPT
    assert "rehearsal-restic-password" in SCRIPT
    assert "production.env" in SCRIPT
    assert "old-sparky.com" not in SCRIPT
    assert "95.217." not in SCRIPT


def test_ansible_workflow_executes_fresh_host_rehearsal():
    assert "fresh-host-rehearsal:" in WORKFLOW
    assert "bash infra/scripts/rehearsal-host.sh" in WORKFLOW
    assert "runs-on: ubuntu-24.04" in WORKFLOW
