# P1-10 — Membership claim guard

## Scope

Prevent unclaimed/imported provider records from gaining provider membership before an approved claim transition, without adding provider self-service.

## Completed

- Added a PostgreSQL trigger-backed invariant on `ProviderMembership` inserts and provider reassignment.
- Membership creation now requires the referenced provider to have `claim_status=approved`.
- Kept imported providers unclaimed and therefore unable to gain membership until claim approval.
- Added database-level regression tests for rejected unclaimed membership and allowed approved membership.
- Updated existing membership fixtures to use approved provider claims where membership is intentional.

## Verification

- Exact implementation PR head `a77dd425b7f0713acdb0fd25889a22487d7863f5` passed the full Compose stack workflow in run `33835264338`.
- Passed bootstrap/contracts, Ruff lint/format, mypy, dependency audit, secret scan, reproducible build, migrations, Django deploy checks, canonical non-browser tests, browser/Playwright evidence and smoke.

## Remaining

Only the still-active P1 acceptance criteria and gates remain in `tasks/P1-domain.md`.
