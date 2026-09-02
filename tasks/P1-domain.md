# P1 — Domain and back office

Depends: P0. Read: `docs/01-product.md`, `docs/03-experience.md`, `docs/05-architecture.md`.

## Build

- Implement taxonomy, provider, membership, service, area, language, contact, media metadata, revision, verification, moderation and audit models.
- Enforce lifecycle/uniqueness/ownership with database constraints.
- Seed Finnish municipalities and the 8 launch categories with RU/FI/EN labels and synonyms.
- Add idempotent `make seed-demo` with clearly synthetic providers covering launch cities, both provider types and representative lifecycle states; refuse production-like settings.
- Build staff admin for create/import, revision diff, approve/request changes, suspend and merge duplicates.
- Generate public read/search document only from approved state.

## Accept

- A staff member can import/create and publish a complete provider without SQL/manual code.
- A fresh local database becomes useful for admin and later browser testing through `make seed-demo` without manual entry.
- Re-running `make seed-demo` is deterministic and does not duplicate records; production-like execution is rejected.
- Pending edits never leak into the live read model.
- Duplicate Y-tunnus/contact/slug cases are deterministic.
- Every moderation/verification change has an actor and timestamp.
- Seed/import commands are idempotent.

## Gates

Model/service tests, constraints under concurrency, migration forward/backward test, query-count limits, admin permission tests, demo-seed idempotency and production-refusal tests.

Do not build public browse or provider self-service.
