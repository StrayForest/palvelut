# P1-15 — Concurrency constraints

## Scope

Close only the remaining P1 gate requiring database constraints to hold under concurrent writes. Do not expand into migration forward/backward testing, query-count limits, admin-permission tests, public browse, or provider self-service.

## Completed

- Added PostgreSQL-backed concurrent-write regression coverage for duplicate nonblank Y-tunnus creation.
- Added PostgreSQL-backed concurrent-write regression coverage for the single-active-owner invariant.
- Each race uses independent database connections and concurrent transactions; exactly one contender must commit while the competing write is rejected by the database constraint.
- No production-code change was required because the existing database constraints already enforce both invariants correctly under concurrency.

## Verification

- `palvelut/apps/providers/test_concurrency_constraints.py::ProviderConcurrencyConstraintTests::test_duplicate_y_tunnus_race_commits_only_one_provider` verifies two concurrent inserts cannot commit the same nonblank Y-tunnus.
- `palvelut/apps/providers/test_concurrency_constraints.py::ProviderConcurrencyConstraintTests::test_active_owner_race_commits_only_one_membership` verifies two concurrent active-owner inserts cannot both commit for one provider.
- Canonical exact-head Compose stack CI must pass before merge.

## Remaining

The active P1 gates are migration forward/backward testing, query-count limits, and admin permission tests.
