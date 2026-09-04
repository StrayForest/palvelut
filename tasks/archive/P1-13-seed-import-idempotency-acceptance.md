# P1-13 — Seed/import idempotency acceptance

## Scope

Close the remaining P1 acceptance criterion requiring seed/import commands to be idempotent, without duplicating implementation already archived in earlier P1 steps.

## Completed

- Confirmed `seed_demo` uses deterministic update/get-or-create operations and retains provider identities across repeated runs.
- Confirmed the staff provider JSON import deterministically updates an existing provider by Y-tunnus and does not create a duplicate on repeated identical imports.
- Confirmed focused tests execute both operations twice and assert stable provider identity/counts.
- Reused the already-completed implementation from `P1-06-demo-seed.md` and `P1-07-staff-back-office.md`; no duplicate product code was added.

## Verification

- `SeedDemoCommandTests.test_seed_demo_is_idempotent_and_covers_launch_shape` covers repeated demo seeding.
- `StaffBackOfficeCompletionTests.test_import_is_idempotent_and_audited` covers repeated staff imports.
- Canonical CI gates must pass on the exact archival PR head before merge.

## Remaining

Only the still-active P1 gates remain in `tasks/P1-domain.md`.
