from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_production_compose_has_two_web_and_worker_slots_and_one_scheduler():
    compose = (ROOT / "compose.production.yml").read_text()

    for service in (
        "web_blue:",
        "web_green:",
        "worker_blue:",
        "worker_green:",
        "scheduler:",
    ):
        assert service in compose
    assert '"127.0.0.1:8081:8000"' in compose
    assert '"127.0.0.1:8082:8000"' in compose
    assert compose.count("stop_grace_period: 60s") == 1
    assert 'command: ["celery", "-A", "palvelut.celery:app", "beat"' in compose
    assert compose.count("image: ${PALVELUT_IMAGE:?") == 3


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
