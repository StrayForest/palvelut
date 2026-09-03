# P1-03 — Domain database constraints

Completed: 2026-09-03
PR: #33

## Scope

- Enforced provider type and lifecycle values with PostgreSQL check constraints.
- Enforced nonblank Y-tunnus uniqueness and deterministic uniqueness for memberships, services, service areas, languages, contacts and media metadata.
- Enforced one active owner per provider and one membership per provider/account.
- Added PostgreSQL-backed regression tests that exercise lifecycle, ownership and uniqueness failures at the database layer.
- Kept UUIDv7 default proof, seed data, staff admin, claims and public read/search generation out of scope for later P1 steps.

## Checks

- GitHub Actions run `33793957978` on implementation head `0681fad1ec4a9e64730206932214254878abe7de` — PASS.
- Fresh PostgreSQL 18 startup, migration drift/apply, provider database-constraint tests and Django deploy checks — PASS.
- Lint/format, type check, dependency/secret audits, canonical non-browser tests, browser gate, Playwright evidence and disposable smoke gate — PASS.

## Deviations

- None.
