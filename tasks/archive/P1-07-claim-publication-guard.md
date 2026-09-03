# P1-07 — Claim publication guard

## Scope

Model provider claim state/evidence and prevent unclaimed/imported providers from entering the published lifecycle.

## Completed

- Added explicit provider claim states: `unclaimed`, `pending`, `approved`, `rejected`.
- Added structured `claim_evidence` storage on providers.
- Added PostgreSQL constraints for valid claim states and `published => approved claim`.
- Updated deterministic demo seed so its synthetic published record carries an approved synthetic claim/evidence marker.
- Added database tests proving invalid claim states and publishing without approval fail with `IntegrityError`, while an approved claim can publish.

## Verification

- `makemigrations --check --dry-run` must report no drift.
- Provider database constraint tests cover the publication guard.
- Canonical CI gates must pass on the exact PR head before merge.

## Remaining

Staff create/import/review workflows, membership claim transition enforcement, public read-model generation, moderation audit completeness and remaining P1 gates stay active in `tasks/P1-domain.md`.
