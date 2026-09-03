# P1 — Domain and back office

Depends: P0. Read: `docs/01-product.md`, `docs/03-experience.md`, `docs/05-architecture.md`.

## Build

- Enforce lifecycle/uniqueness/ownership with database constraints.
- Generate IDs through PostgreSQL 18 native `uuidv7()` and test database defaults.
- Seed Finnish municipalities and the 8 launch categories with RU/FI/EN labels and synonyms.
- Add idempotent `make seed-demo` with clearly synthetic providers covering launch cities, both provider types and representative lifecycle states; refuse production-like settings.
- Build staff admin for non-public create/import, revision diff, approve/request changes, suspend and merge duplicates. Model claim state/evidence so unclaimed imports cannot publish.
- Generate public read/search document only from approved state.

## Accept

- A staff member can create and publish an owner-confirmed provider without SQL/manual code; an imported unclaimed record cannot publish.
- A fresh local database becomes useful for admin and later browser testing through `make seed-demo` without manual entry.
- Re-running `make seed-demo` is deterministic and does not duplicate records; production-like execution is rejected.
- Pending edits never leak into the live read model.
- Unclaimed/imported records cannot publish or gain membership without an approved claim transition.
- Duplicate Y-tunnus/contact/slug cases are deterministic.
- Every moderation/verification change has an actor and timestamp.
- Seed/import commands are idempotent.

## Gates

Model/service tests, constraints under concurrency, migration forward/backward test, query-count limits, admin permission tests, demo-seed idempotency and production-refusal tests.

Do not build public browse or provider self-service.
