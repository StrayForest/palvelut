# P1 — Domain and back office

Depends: P0. Read: `docs/01-product.md`, `docs/03-experience.md`, `docs/05-architecture.md`.

## Build

- Generate public read/search document only from approved state.

## Accept

- Pending edits never leak into the live read model.
- Duplicate Y-tunnus/contact/slug cases are deterministic.
- Every moderation/verification change has an actor and timestamp.
- Seed/import commands are idempotent.

## Gates

Model/service tests, constraints under concurrency, migration forward/backward test, query-count limits, admin permission tests.

Do not build public browse or provider self-service.
