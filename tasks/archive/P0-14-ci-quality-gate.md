# P0-14 — CI quality gate

Completed: 2026-09-03
Commit/PR: implementation `9f666553c58784d380790ee6618ca824fb0c9316`; PR #17

## Scope

- Expanded the pull-request CI workflow with pinned Ruff, mypy, pip-audit and detect-secrets tooling.
- Added full-tree Python linting, changed-file formatting checks and application type checking.
- Added locked runtime dependency auditing and tracked-file secret scanning with narrow exclusions for explicit test-only fixtures.
- Added explicit frontend-stage and application-container builds.
- Added fresh database startup, migration drift/apply checks and production-like `manage.py check --deploy` validation.
- Kept the canonical `make test`, `make e2e` and `make smoke` gates in the same exact-head workflow.

## Checks

- Earlier CI iterations correctly exposed pre-existing Django test import ordering, formatter baseline and a test-only secret fixture; the gate was narrowed only where necessary rather than suppressing production-code checks.
- GitHub Actions run `33735733374` on implementation head `9f666553c58784d380790ee6618ca824fb0c9316` — PASS.
- Lint/format — PASS.
- Type check — PASS.
- Dependency audit — PASS, no known vulnerabilities found.
- Secret scan — PASS.
- Frontend and application container builds — PASS.
- Migration drift/apply and `manage.py check --deploy` — PASS.
- `make test`, `make e2e`, `make smoke` — PASS.

## Deviations

- The repository already contains eight Python files that predate this step and are not normalized by the selected Ruff formatter. To avoid mixing this CI step with unrelated mass reformatting, formatting is enforced on Python files changed by the pull request; linting remains repository-wide for application and test Python code.
