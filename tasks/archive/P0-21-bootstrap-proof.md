# P0-21 — Clean `make bootstrap` contract

Completed: 2026-09-03
Commit/PR: implementation `3400ff389f093d776f26c0992f6d44fa7c0f1453`; PR #24

## Scope

- Added an exact-head CI proof for `make bootstrap` immediately after checkout and before project/CI dependency installation.
- The proof starts with no host `.venv` or `frontend/node_modules` and runs the real bootstrap command with a cleared environment and a `PATH` exposing only Git, Make and Docker.
- Verified bootstrap can validate Compose and build the application container without installing project dependencies on the host checkout.
- Added regression coverage for the bootstrap CI ordering and dependency boundary.

## Checks

- GitHub Actions run `33765816837` on implementation head `3400ff389f093d776f26c0992f6d44fa7c0f1453` — PASS.
- Clean-checkout canonical bootstrap proof — PASS.
- Dependency/command contracts, lint/format, types, dependency audit and secret scan — PASS.
- Frontend/application builds, canonical development startup, fresh PostgreSQL/Valkey, migration drift/apply and Django deploy checks — PASS.
- `make test`, `make e2e`, Playwright evidence upload and `make smoke` — PASS.

## Verification history

- Runs `33765347823` and `33765491103` proved bootstrap itself successfully but stopped later on formatting of the newly added regression test; no bootstrap defect was found.

## Deviations

- None. Other P0 acceptance and stage-level gates remain active.
