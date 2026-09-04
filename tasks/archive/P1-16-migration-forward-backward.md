# P1-16 — Migration forward/backward test

## Scope

Close only the remaining P1 gate requiring a migration forward/backward regression test. Do not expand into query-count limits, admin-permission tests, public browse, or provider self-service.

## Completed

- Added a PostgreSQL-backed migration round-trip test for `providers.0004_membership_requires_approved_claim`.
- The test migrates back to `0003_provider_claim_state`, verifies the trigger/function are absent, migrates forward to `0004`, verifies both are installed, then migrates backward again and verifies both are removed.
- Test teardown restores the latest providers migration so the test database remains compatible with the rest of the suite.

## Verification

- `palvelut/apps/providers/test_migrations.py::ProviderMigrationRoundTripTests::test_membership_claim_trigger_migrates_forward_and_backward` covers both forward and reverse operations against PostgreSQL catalogs.
- Canonical exact-head Compose stack CI must pass before merge.

## Remaining

The active P1 gates are query-count limits and admin permission tests.
