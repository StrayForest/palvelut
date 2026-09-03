# P0-16 — Fresh isolated CI services

Completed: 2026-09-03
Commit/PR: implementation `ff1009bc27c0ed9937fe02e4953e3ac1ba6b9fe2`; PR #19

## Scope

- Gave every GitHub Actions run a unique Compose project namespace derived from its run ID and attempt.
- Kept `palvelut` as the local default while allowing `make test`, `make e2e` and `make smoke` to inherit the isolated CI project name.
- Pull and force-recreate the digest-pinned PostgreSQL 18 and Valkey 8.x services inside the disposable CI project.
- Wait for both services to become healthy before using them and verify their runtime major versions.
- Remove CI containers, networks and volumes after the run so no persistent or deployed environment is reused.
- Added regression coverage for the CI isolation and service-version contract.

## Checks

- CI service-isolation contract — PASS.
- GitHub Actions run `33746822206` on implementation head `ff1009bc27c0ed9937fe02e4953e3ac1ba6b9fe2` — PASS.
- Lint/format, type check, dependency audit and secret scan — PASS.
- Frontend and application container builds — PASS.
- Fresh PostgreSQL/Valkey startup, health wait and runtime version checks — PASS.
- Migration drift/apply and `manage.py check --deploy` — PASS.
- `make test`, `make e2e`, `make smoke` — PASS.

## Deviations

- Local development continues to use the stable `palvelut` Compose project name; only CI overrides the namespace per run.
- CI uses the same digest-pinned Compose service definitions as local development rather than a separate database/cache configuration.
