from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_rehearsal_gate_uses_fresh_host_ansible_and_real_restore():
    workflow = (ROOT / ".github/workflows/p5-ansible.yml").read_text()
    script = (ROOT / "infra/scripts/rehearsal-host-ci.sh").read_text()

    assert "infra/scripts/rehearsal-host-ci.sh" in workflow
    assert "bash infra/scripts/rehearsal-host-ci.sh" in workflow
    assert "FROM ubuntu:24.04" in script
    assert "ansible-playbook" in script
    assert "infra/ansible/site.yml" in script
    assert "changed=0" in script
    assert "restore-drill.sh" in script
    assert "restore_status=ok" in script
    assert "RESTIC_REPOSITORY=/tmp/restic-repo" in script
    assert "palvelut-production" in script


def test_rehearsal_gate_does_not_require_production_credentials():
    script = (ROOT / "infra/scripts/rehearsal-host-ci.sh").read_text()

    forbidden = (
        "CLOUDFLARE_API_TOKEN",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "PRODUCTION_DATABASE_URL",
        "PRODUCTION_HOST",
    )
    for name in forbidden:
        assert name not in script
