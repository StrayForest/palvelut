# P0-03 — Local Make gates

Completed: 2026-09-03
Commit/PR: implementation `0e47eec4706ac69201007aec381dfc8eedd8186c`; PR #6

## Scope

- Added project-scoped `make bootstrap`, `make dev`, `make reset`, `make test` and `make smoke` targets.
- `bootstrap` validates Docker/Compose, validates the Compose model and builds the application image without requiring project-global Python tooling.
- `reset` is limited to the `palvelut` Compose project and refuses production/staging-like environment markers or `DJANGO_DEBUG != 1`.
- `test` runs the repository test suite inside the pinned application image against a read-only checkout mount.
- `smoke` owns the disposable PostgreSQL/Valkey/Mailpit/MinIO/web/worker/Nginx verification and always removes containers and volumes on exit.
- GitHub Actions now exercises the canonical `make test` and `make smoke` gates rather than maintaining a second inline implementation.
- Added focused static contract tests for the Make/reset/smoke command surface.

## Checks

- GitHub Actions run `33686905952` on implementation head `0e47eec4706ac69201007aec381dfc8eedd8186c` — PASS.
- Dependency and command contract tests — PASS.
- `make test` — PASS.
- `make smoke` — PASS, including clean migrations, `manage.py check`, cache round-trip, Mailpit delivery, web/worker/Nginx reachability, PostgreSQL 18 and Valkey 8.x probes, and disposable cleanup.

## Remaining active work

- `make e2e` is intentionally not claimed yet; it remains active until the Playwright browser gate exists.
- The stage-level requirement that CI use `make test`, `make e2e` and `make smoke` as its non-interactive gates remains active until `make e2e` is implemented.

## Deviations

- None.
