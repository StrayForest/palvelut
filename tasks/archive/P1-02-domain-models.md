# P1-02 — Domain model foundation

Completed: 2026-09-03
PR: #32

## Scope

- Added `Category` and `Language` taxonomy models alongside the existing geography foundation.
- Added provider, membership, service, service-area, provider-language, contact-channel and media metadata models.
- Added profile revision, verification check, moderation case/event and audit event models with explicit actor/timestamp metadata where required by their role.
- Added PostgreSQL migrations using native `uuidv7()` database defaults for the new domain records.
- Kept lifecycle/uniqueness/ownership constraint hardening, seed data, staff admin and public read/search generation out of scope for later P1 steps.

## Checks

- GitHub Actions run `33791842992` on implementation head `ffda169ab26e50ce1bd6c7cd3375e7af44be04bd` — PASS.
- Fresh PostgreSQL 18 startup, migration drift/apply, Django deploy checks and existing taxonomy model tests — PASS.
- Lint/format, type check, dependency/secret audits, canonical non-browser tests, browser gate, Playwright evidence and disposable smoke gate — PASS.

## Deviations

- None.
