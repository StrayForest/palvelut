# P1-14 — Model/service tests

## Scope

Close the first remaining P1 gate requiring model/service test coverage, without expanding into concurrency, migration, query-count, admin-permission, public browse, or provider self-service work.

## Completed

- Confirmed the P1 domain model graph has direct regression coverage for providers, memberships, services, service areas, languages, contacts, media, publishing revisions, verification, moderation events, and audit events.
- Confirmed lifecycle and database invariants are exercised through the existing P1 test suite rather than being documentation-only guarantees.
- Confirmed the completed P1 service flows added in earlier steps are covered by regression tests and are part of the canonical Compose test run.
- No production-code change was required for this gate because the required model/service regression coverage already exists on `main`.

## Verification

- `palvelut/apps/providers/tests.py::DomainModelFoundationTests` persists the complete core provider graph and verifies actor/timestamp-bearing related state.
- `palvelut/apps/providers/tests.py::ProviderDatabaseConstraintTests` exercises P1 lifecycle, claim, membership, uniqueness, and relation invariants.
- The canonical full Compose stack workflow run `33844602413` completed successfully on implementation head `c08e59aff92ac09615ad7bf885deec82b227b8da`, including the non-browser Django test suite containing these tests.

## Remaining

The active P1 gates are concurrency constraints, migration forward/backward testing, query-count limits, and admin permission tests.
