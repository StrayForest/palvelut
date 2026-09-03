# P1-07 — Staff provider administration

Completed: 2026-09-04

## Scope

- Added staff-only provider administration for non-public create and import workflows.
- Added revision diff and moderation actions for approve and request changes.
- Added provider suspension and deterministic duplicate-merge handling.
- Added audit events for staff moderation and verification actions.
- Added admin permission coverage while keeping public browse and provider self-service out of scope.

## Checks

- Exact implementation head `4b3d771ad2993d2892f3e126e68ca839f5679185` passed the full Compose stack workflow in run `33812301772`.
- Passed bootstrap and command contracts, Ruff lint/format, mypy, dependency audit, secret scan, reproducible frontend/static build, application build, development startup, reset contract, clean PostgreSQL start and migrations, Django deploy checks, canonical non-browser tests, browser/Playwright evidence and disposable smoke.

## Deviations

- None.
