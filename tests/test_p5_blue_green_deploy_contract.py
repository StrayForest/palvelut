from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def test_production_compose_has_two_web_and_worker_slots_and_one_scheduler():
    compose = yaml.safe_load((ROOT / "compose.production.yml").read_text())
    services = compose["services"]

    assert {
        "web_blue",
        "web_green",
        "worker_blue",
        "worker_green",
        "scheduler",
    } <= set(services)
    assert services["web_blue"]["ports"] == ["127.0.0.1:8081:8000"]
    assert services["web_green"]["ports"] == ["127.0.0.1:8082:8000"]
    assert services["worker_blue"]["stop_grace_period"] == "60s"
    assert services["worker_green"]["stop_grace_period"] == "60s"
    assert "beat" in services["scheduler"]["command"]

    for name in ("web_blue", "web_green", "worker_blue", "worker_green", "scheduler"):
        assert services[name]["image"].startswith("${PALVELUT_IMAGE:")


def test_deploy_script_enforces_digest_health_switch_drain_and_safe_rollback():
    script = (ROOT / "infra/scripts/deploy-production.sh").read_text()

    assert "ghcr\\.io/strayforest/palvelut@sha256:" in script
    assert "python manage.py migrate --noinput" in script
    assert "/palvelut/health/ready" in script
    assert "systemctl reload nginx" in script
    assert 'stop -t 60 "worker_${active}"' in script
    assert "--force-recreate scheduler" in script
    assert "database migrations will not be reversed" in script
    assert "previous-release.env" in script


def test_ansible_bootstrap_upstream_matches_blue_slot():
    vars_text = (ROOT / "infra/ansible/group_vars/all.yml").read_text()
    assert "palvelut_upstream: http://127.0.0.1:8081" in vars_text
