# P1-12 — Deterministic duplicate identity cases

Completed: 2026-09-04

## Scope

- Kept nonblank Y-tunnus uniqueness database-enforced and covered it with focused duplicate behavior tests.
- Kept exact provider contact duplicates deterministic through the existing provider/kind/value uniqueness constraint and focused tests.
- Added publishing-owned provider slug history with globally unique slugs and at most one current slug per provider.
- Allowed historical slugs to remain attached to a provider for future redirect preservation without creating a second current slug.
- Kept public browse and provider self-service out of scope.

## Checks

- Exact implementation head `3303cd351be5cd6dee5f8728becc3d9af12a4928` passed the full Compose stack workflow in run `33840766607`.
- Passed bootstrap/contracts, Ruff lint/format, mypy, dependency audit, secret scan, reproducible frontend/static build, application build, startup/reset checks, migrations, Django deploy checks, canonical non-browser tests, browser/Playwright evidence and disposable smoke.

## Deviations

- None.
