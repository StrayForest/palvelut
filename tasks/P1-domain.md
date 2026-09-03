# P1 — Domain and back office

Depends: P0. Read: `docs/01-product.md`, `docs/03-experience.md`, `docs/05-architecture.md`.

## Build

- Build staff admin for non-public create/import, revision diff, approve/request changes, suspend and merge duplicates. Model claim state/evidence so unclaimed imports cannot publish.
- Generate public read/search document only from approved state.

## Accept

- A staff member can create and publish an owner-confirmed provider without SQL/manual code; an imported unclaimed record cannot publish.
- Pending edits never leak into the live read model.
- Unclaimed/imported records cannot publish or gain membership without an approved claim transition.
- Duplicate Y-tunnus/contact/slug cases are deterministic.
- Every moderation/verification change has an actor and timestamp.
- Seed/import commands are idempotent.

## Gates

Model/service tests, constraints under concurrency, migration forward/backward test, query-count limits, admin permission tests.

Do not build public browse or provider self-service.
