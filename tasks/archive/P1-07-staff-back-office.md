# P1-07 — Staff back office

Completed: 2026-09-04

## Scope

- Completed the staff-only provider back office for non-public create/import workflows.
- Added idempotent provider JSON import with deterministic updates for existing business identity data.
- Added deterministic duplicate merge behavior that preserves a canonical provider, moves related state and archives the duplicate.
- Added audit events for staff create/import/merge actions and permission coverage for the admin workflows.
- Kept public read/search generation and provider self-service out of scope.

## Checks

- Exact implementation head `0b42980c508ab03e1c640578f96538336dbc09e0` passed the full Compose stack workflow in run `33818029830`.
- Passed bootstrap/contracts, Ruff lint/format, mypy, dependency audit, secret scan, reproducible frontend/static build, application build, startup/reset checks, migrations, Django deploy checks, canonical non-browser tests, browser/Playwright evidence and smoke.

## Deviations

- None.
