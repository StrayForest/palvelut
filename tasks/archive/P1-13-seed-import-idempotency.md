# P1-13 — Seed/import idempotency

## Scope

Close the remaining P1 acceptance criterion requiring seed/import operations to be idempotent, without expanding into public browse or provider self-service.

## Completed

- Confirmed `seed_demo` is idempotent: running it twice preserves the same provider IDs and does not create duplicate demo providers.
- Confirmed staff provider import is idempotent by `Y-tunnus`: submitting the same import twice leaves exactly one provider in the domain state.
- Kept import audit history intact; repeated staff actions remain auditable without duplicating provider records.
- No production-code change was required because both guarantees and their regression tests were already present on `main`.

## Verification

- `palvelut/apps/providers/test_seed_demo.py::SeedDemoCommandTests::test_seed_demo_is_idempotent_and_covers_launch_shape` covers repeated demo seeding.
- `palvelut/apps/providers/test_admin_completion.py::StaffBackOfficeCompletionTests::test_import_is_idempotent_and_audited` covers repeated provider import.
- Both tests were present on exact implementation head `c08e59aff92ac09615ad7bf885deec82b227b8da`, which passed the full Compose stack workflow in run `33844602413`.

## Remaining

Only the still-active P1 gates remain in `tasks/P1-domain.md`.
