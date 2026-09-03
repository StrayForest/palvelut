# P0-24 — Local reset safety

Completed: 2026-09-03
Commit/PR: implementation head `2eb19daabe5ec8e1b035e547764fc1c0ce118486`; PR #27

## Scope

- Made `make reset` pass the selected `COMPOSE_PROJECT_NAME` explicitly into the reset script.
- Removed the hard-coded Compose project from `infra/scripts/reset-local.sh`; reset operations now target only the selected project.
- Added refusal for production/staging environment markers, disabled Django debug, and production-like Compose project names.
- Extended Make contract tests to cover project scoping and reset guardrails.

## Checks

- GitHub Actions run `33773186935` on implementation head `2eb19daabe5ec8e1b035e547764fc1c0ce118486` — PASS.
- Canonical bootstrap from clean checkout — PASS.
- Dependency/command contracts, lint/format, types, dependency audit and secret scan — PASS.
- Frontend/application builds and canonical development startup — PASS.
- Fresh database services, migrations and Django deploy checks — PASS.
- Canonical `make test`, `make e2e`, Playwright evidence upload and disposable `make smoke` — PASS.

## Deviations

- None. Remaining P0 acceptance and stage-level gates stay active.
