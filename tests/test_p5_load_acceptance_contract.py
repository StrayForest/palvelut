from pathlib import Path


DOCKERFILE = Path("Dockerfile")
LOAD_SCRIPT = Path("infra/scripts/load-acceptance.py")
SETTINGS = Path("palvelut/settings.py")
WORKER = Path("palvelut/worker.py")
WORKFLOW = Path(".github/workflows/p5-load.yml")


def test_web_queue_and_request_concurrency_are_explicitly_bounded() -> None:
    dockerfile = DOCKERFILE.read_text()
    worker = WORKER.read_text()

    assert '"--workers", "2"' in dockerfile
    assert '"--backlog", "128"' in dockerfile
    assert "palvelut.worker.BoundedUvicornWorker" in dockerfile
    assert '"limit_concurrency": 16' in worker


def test_valkey_cache_pool_is_explicitly_bounded() -> None:
    settings = SETTINGS.read_text()

    assert '"OPTIONS": {"max_connections": 16}' in settings


def test_load_probe_enforces_server_side_slos_and_overload() -> None:
    script = LOAD_SCRIPT.read_text()

    assert '"--normal-concurrency", type=int, default=8' in script
    assert '"--overload-concurrency", type=int, default=128' in script
    assert '"warm_p95_ms": 300' in script
    assert '"cold_p95_ms": 800' in script
    assert '"normal_server_error_rate": 0.001' in script
    assert 'server_error_rate"]) >= 0.001' in script


def test_workflow_records_bounded_database_and_cache_clients() -> None:
    workflow = WORKFLOW.read_text()

    assert "test_beta_sized_discovery_stays_within_latency_budgets" in workflow
    assert "infra/scripts/load-acceptance.py" in workflow
    assert "pg_stat_activity" in workflow
    assert "connected_clients" in workflow
    assert 'test "$max_db_connections" -le 40' in workflow
    assert 'test "$max_valkey_clients" -le 36' in workflow
    assert "asgi_concurrency_per_worker=16" in workflow
    assert "p5-load-report.json" in workflow
    assert "p5-load-pools.txt" in workflow
