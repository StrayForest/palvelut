# P1-04 — UUIDv7 database defaults

Completed: 2026-09-03

## Scope

- Confirmed that all concrete domain models inheriting `UuidV7Model` use PostgreSQL 18 native `uuidv7()` as the database-side primary-key default.
- Added database-backed coverage that enumerates every concrete `UuidV7Model`, inspects the PostgreSQL catalog default for its `id` column and requires `uuidv7()`.
- Added an explicit PostgreSQL 18+ assertion so the contract cannot silently pass on a server without native UUIDv7 support.
- Kept ID generation in the database rather than adding an application-side UUID fallback.

## Checks

- Existing UUIDv7 primary-key creation coverage retained.
- Full required repository gates must pass on the exact implementation head before merge.

## Deviations

- The shared `UuidV7Model` and migrations already used native `uuidv7()` from P1-01/P1-02; this step closes the remaining active requirement by adding comprehensive database-default verification rather than duplicating the implementation.
