# P1-06 — Demo seed

Completed: 2026-09-03

## Scope

- Added idempotent `make seed-demo` backed by the `seed_demo` Django management command.
- Seeded clearly synthetic provider records across Helsinki, Espoo and Vantaa, covering both individual and business provider types and representative unclaimed, draft, published and suspended lifecycle states.
- Seeded related service, service-area, Russian-language and synthetic contact data from the existing Finland/launch-category taxonomy.
- Restricted demo seeding to `local` and `test`; staging and production-like environments are rejected.
- Added database-backed tests for idempotency, launch-city/type/lifecycle coverage and production/staging refusal.

## Checks

- Exact implementation head `0875d9b4686f752d7daf99fad64dfc28f3c7c735` passed the full Compose stack workflow in run `33803374681`.
- Passed bootstrap and command contracts, Ruff lint/format, mypy, dependency audit, secret scan, reproducible frontend/static build, application build, development startup, reset contract, clean PostgreSQL start and migrations, taxonomy tests, Django deploy checks, canonical non-browser tests, browser/Playwright evidence and disposable smoke.

## Deviations

- None.
