# P1-07 — Staff admin workflow

Completed: 2026-09-04

## Scope

- Added the staff-only Django back office under `/palvelut/staff/` for provider create/import state, memberships, revision review, verification/claim review and moderation records.
- Added revision diff plus explicit approve/request-changes services; publication requires an active owner and rejects `unclaimed` providers.
- Added `ProviderClaim` state and evidence (`registry_signatory`, `business_domain_email`, `staff_equivalent`) with review actor/timestamp and one-pending-claim-per-provider constraint.
- Added claim approval/rejection services so an approved claim is the only implemented transition that gives an imported unclaimed provider an active owner and moves it to `draft`.
- Added audited staff actions for provider suspension and deterministic two-record duplicate merge.
- Added database-backed workflow tests covering staff-only/no-store admin access, owner-confirmed publication, unclaimed publication refusal, claim transition, revision diff/request-changes and audited suspend/merge behavior.

## Checks

- Exact implementation head `0915ac6cac658feb6b619423c15c0022812fbefb` passed the full Compose stack workflow in run `33807012141`.
- Passed bootstrap and command contracts, Ruff lint/format, mypy, dependency audit, secret scan, reproducible frontend/static build, application build, development startup, reset contract, clean PostgreSQL start and migrations, taxonomy tests, staff admin workflow tests, Django deploy checks, canonical non-browser tests, browser/Playwright evidence and disposable smoke.

## Deviations

- None.
