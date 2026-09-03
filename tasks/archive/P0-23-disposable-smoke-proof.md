# P0-23 — Disposable smoke lifecycle proof

Completed: 2026-09-03
Commit/PR: implementation `6dffe4a9b614d8e42a0e7b8759d0576968f4624f`; PR #26

## Scope

- Strengthened the canonical `make smoke` cleanup so it verifies that no Compose containers or named volumes for the project remain after shutdown.
- Kept the existing disposable lifecycle: PostgreSQL, Valkey, Mailpit and MinIO start first, migrations/checks run, then web, worker and Nginx are brought up for runtime verification.
- Retained explicit `/palvelut/health/live` and `/palvelut/health/ready` probes through Nginx, including `no-store` response checks.
- Extended the Make contract tests to require liveness/readiness coverage and explicit post-cleanup container/volume assertions.

## Checks

- GitHub Actions run `33770433666` on implementation head `6dffe4a9b614d8e42a0e7b8759d0576968f4624f` — PASS.
- Canonical `make smoke` — PASS, including lifecycle probes and verified cleanup.
- Canonical `make test` — PASS.
- Canonical `make e2e` and Playwright evidence upload — PASS.
- Bootstrap, contracts, lint/format, types, dependency audit, secret scan, builds, development startup, migrations and Django deploy checks — PASS.

## Deviations

- None. Remaining P0 acceptance and stage-level gates stay active.
