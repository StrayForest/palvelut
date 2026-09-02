# P0-02 — Local Compose stack

Completed: 2026-09-03
Commit/PR: implementation `145a892d921cd58d18d8c61e1824cdd72546749a`; PR #5

## Scope

- Added a local Docker Compose stack with PostgreSQL 18, Valkey 8.x, Mailpit, MinIO, Django web, Celery worker and Nginx.
- Web and worker use the same Python 3.13 application image; Nginx proxies to the web service without rewriting the request path.
- PostgreSQL and Valkey remain internal to the Compose network; development HTTP, Mailpit and MinIO ports bind only to loopback.
- Wired Django to PostgreSQL, Valkey cache, Celery broker/result backend, Mailpit SMTP and the local S3-compatible endpoint.
- Added and committed the `uv`-generated runtime dependency lock, including `uvicorn-worker 0.4.x` compatibility with current Uvicorn.
- Pinned runtime and service images to immutable SHA-256 digests.
- Added a read-only GitHub Actions Compose gate and focused contract tests.

## Checks

- GitHub Actions run `33685960347` on implementation head `145a892d921cd58d18d8c61e1824cdd72546749a` — PASS.
- `uv lock --check` and `uv sync --locked` — PASS.
- Bootstrap + Compose contract tests — PASS (8 tests).
- `docker compose config` and application-image build — PASS.
- PostgreSQL 18 and Valkey 8.x readiness/version probes — PASS.
- Clean Django migrations and `manage.py check` against PostgreSQL — PASS.
- Valkey cache round-trip — PASS.
- Mailpit SMTP send and inbox verification — PASS.
- Django/Gunicorn/Uvicorn web container health — PASS.
- Celery worker starts against the Valkey broker — PASS.
- Nginx reaches the running application through the Compose network — PASS.
- Compose cleanup removes disposable containers and volumes — PASS.

## Corrected during verification

- PostgreSQL 18 requires its persistent volume at `/var/lib/postgresql` so its version-specific data directory can be managed correctly; the old direct `/var/lib/postgresql/data` mount failed and was removed.
- `uvicorn-worker 0.3.0` was incompatible with the resolved Uvicorn runtime; the dependency contract now requires `uvicorn-worker>=0.4,<0.5`.
- The proxy liveness gate no longer assumes a future application route must return exactly `404`; route semantics remain an active later P0 step.

## Deviations

- None. Production secrets, health endpoints, public prefix routing, Make targets and the full CI/release gates remain active later P0 work.
