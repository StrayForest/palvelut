# P1-05 — Finland taxonomy seed

Completed: 2026-09-03

## Scope

- Seeded Finland with the 2026 municipality taxonomy: 19 regions and 308 municipalities using official three-digit municipality codes and municipality-to-region assignments.
- Added the 8 documented launch categories.
- Added dedicated RU/FI/EN category labels and per-locale synonyms without overloading the technical category name.
- Added database constraints for supported category-term locales and deterministic label/synonym uniqueness.
- Kept taxonomy seeding deterministic and migration-local; runtime migration does not depend on external network access.

## Checks

- Database-backed tests require 19 Finnish regions and 308 municipalities, and verify Espoo, Helsinki and Vantaa against Uusimaa mappings.
- All 8 launch categories must have RU/FI/EN labels and at least two synonyms per locale.
- Unsupported locales and duplicate category labels/synonyms are rejected by PostgreSQL constraints.
- Migration rollback deletes seeded municipalities and regions before Finland so existing `PROTECT` relationships remain valid.
- Exact implementation head `0f084c53337ea539b7c9776dff368a6b15f70c82` passed the full repository workflow in run `33800518515`, including migrations, taxonomy tests, lint/format, mypy, audits, browser evidence and smoke checks.

## Deviations

- `Category` previously had only a single technical `name`, so this step introduced `CategoryLabel` and `CategorySynonym` as explicit taxonomy-owned models for the documented multilingual labels and aliases instead of embedding locale-specific data in JSON or duplicating categories.
