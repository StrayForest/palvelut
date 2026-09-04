# P1-13 — Seed/import idempotency

## Scope

Close the remaining P1 acceptance criterion requiring seed/import operations to be idempotent, without expanding into public browse or provider self-service.

## Completed

- `seed_demo` is idempotent: repeating the command preserves the same synthetic provider identities and does not create duplicate providers.
- Staff provider import is idempotent for the same source record: repeated import with the same Y-tunnus updates the existing provider instead of creating another row.
- Both behaviors already have dedicated regression coverage in the provider test suite.

## Verification

- `SeedDemoCommandTests.test_seed_demo_is_idempotent_and_covers_launch_shape` exercises repeated `seed_demo` execution and asserts stable provider IDs/counts.
- `StaffBackOfficeCompletionTests.test_import_is_idempotent_and_audited` exercises repeated staff import and asserts a single provider for the imported Y-tunnus.
- Final exact-head verification is the full Compose stack workflow for the archival PR.

## Remaining

Only the P1 gates remain in `tasks/P1-domain.md`.
