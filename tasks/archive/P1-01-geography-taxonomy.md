# P1-01 — Geography taxonomy foundation

Completed: 2026-09-03
PR: #31

## Scope

- Added `Country`, `Region` and `Municipality` taxonomy models matching the documented Country → Region → Municipality hierarchy.
- Added PostgreSQL 18 native `uuidv7()` database defaults for the new model IDs.
- Added ISO alpha-2 country-code validation, parent deletion protection and deterministic region/municipality code uniqueness constraints.
- Added the initial taxonomy migration and database-backed tests on fresh PostgreSQL.

## Checks

- GitHub Actions run `33788811253` on implementation head `5c38921f786542550566f47df32e1602100dfbd6` — PASS.
- Fresh PostgreSQL startup, migration drift/apply and geography taxonomy model tests — PASS.
- Lint/format, type check, dependency/secret audits, deploy checks, `make test`, `make e2e`, Playwright evidence and `make smoke` — PASS.

## Deviations

- None.
