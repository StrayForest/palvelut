# P0-19 — Main branch protection requirement deferred

Completed: 2026-09-03
Commit/PR: contract head `b19f20643c35ec45b70181bb2f84c854f8c7d052`; PR #22

## Scope

- Removed `main` branch protection/ruleset from P0 acceptance because the repository owner explicitly chose not to enable protection yet.
- Updated repository instructions and operations documentation so future sessions do not treat protection as a P0 completion gate.
- Kept PRs and green CI as the working delivery discipline.
- Did not enable or modify any GitHub branch protection/ruleset.

## Checks

- GitHub Actions run `33763220155` on contract head `b19f20643c35ec45b70181bb2f84c854f8c7d052` — PASS.
- Dependency/command contracts, lint/format, types, dependency audit and secret scan — PASS.
- Frontend/application builds, fresh PostgreSQL/Valkey, migrations and Django deploy checks — PASS.
- `make test`, `make e2e`, Playwright evidence upload and `make smoke` — PASS.

## Deviation

`main` protection/rulesets remain disabled by explicit owner decision. They may be enabled later only when the owner requests it; this is not a P0 blocker.
