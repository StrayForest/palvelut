# P0-24 — Isolated local reset proof

Completed: 2026-09-03
Commit/PR: implementation `5aaa557edb119da015bd3efbf6c62df0f146529c`; PR #28

## Scope

- Made `make reset` honor `COMPOSE_PROJECT_NAME` instead of hard-coding the default `palvelut` Compose project.
- Preserved the production-like safety guards for `PALVELUT_ENVIRONMENT` and `DJANGO_DEBUG`.
- Added an exact-head CI proof that both production guards refuse before destroying target state.
- Added an isolation proof that a successful reset removes the selected project's disposable containers and volumes while a separate sentinel Compose project remains running.
- Extended the Make contract tests to lock the selected-project behavior and CI reset proof.

## Checks

- GitHub Actions run `33776132602` on implementation head `5aaa557edb119da015bd3efbf6c62df0f146529c` — PASS.
- Isolated local reset contract — PASS, including production-like refusals, target cleanup and sentinel preservation.
- Bootstrap, contracts, lint/format, types, dependency audit, secret scan, frontend/application builds and canonical development startup — PASS.
- Fresh database services, migration drift/apply, Django deploy checks and canonical `make test` — PASS.
- Canonical `make e2e`, Playwright evidence upload and canonical `make smoke` — PASS.

## Deviations

- None. Remaining P0 acceptance and stage-level gates stay active.
