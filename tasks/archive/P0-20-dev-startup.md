# P0-20 — Clean local `make dev` startup

Completed: 2026-09-03
Commit/PR: implementation `cbba77764735e4d415d1bcd75b4a57a8e7c52808`; PR #23

## Scope

- Updated `make dev` so a fresh local Compose project starts PostgreSQL, Valkey, Mailpit and MinIO, applies Django migrations, then starts the complete attached application stack.
- Added an exact-head CI proof that launches the real `make dev` command from a clean isolated Compose namespace.
- The proof requires PostgreSQL, Valkey, Mailpit, MinIO, web, worker and Nginx to be running, verifies `/palvelut/en/` through Nginx and confirms the fresh database contains applied Django migrations.
- Added regression coverage for the command and CI contract.

## Checks

- GitHub Actions run `33764231034` on implementation head `cbba77764735e4d415d1bcd75b4a57a8e7c52808` — PASS.
- Canonical development startup proof — PASS.
- Dependency/command contracts, lint/format, types, dependency audit and secret scan — PASS.
- Frontend/application builds, fresh PostgreSQL/Valkey, migration drift/apply and Django deploy checks — PASS.
- `make test`, `make e2e`, Playwright evidence upload and `make smoke` — PASS.

## Deviations

- None. Other P0 acceptance and stage-level gates remain active.
