# P1-07 — Staff admin and claim workflow

Completed: 2026-09-04

## Scope

- Added staff-only Django admin under `/palvelut/admin/` for provider create/import, related provider data, revision review, verification and claim moderation.
- Added revision diff plus approve/request-changes actions, provider suspension and deterministic duplicate merge-to-oldest action through explicit service functions.
- Added `ProviderClaim` with claim status, evidence metadata, reviewer and timestamps, including a database constraint allowing only one approved claim per provider.
- Added claim transition services that grant active owner membership only after approval and audit claim approvals/rejections.
- Blocked revision publication until the provider has an approved claim; approved publication, requested changes, suspension and duplicate merge are audited.
- Added workflow and staff-permission tests covering unclaimed publish refusal, claim-to-owner-to-publish transition, moderation audit events and staff-only admin access.

## Checks

- Exact implementation head `ef346eae334dc03e9fde25663bcb498d8fa8af10` passed the full Compose stack workflow in run `33809870439`.
- Passed bootstrap and command contracts, Ruff lint/format, mypy, dependency audit, secret scan, reproducible frontend/static build, application build, development startup, reset contract, clean PostgreSQL 18 start and migrations, taxonomy tests, Django deploy checks, canonical non-browser tests, browser/Playwright evidence and disposable smoke.

## Deviations

- None.
