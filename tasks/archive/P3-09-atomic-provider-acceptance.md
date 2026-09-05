# P3-09 — Atomic provider acceptance

## Scope

Prove that claim approval/rejection, membership acceptance and ownership transfer are transactional with their audit writes, and that none of these ownership operations can expose an unapproved provider through the public read model.

## Completed

- Added focused regression coverage that forces audit persistence failures during claim approval and rejection and proves provider claim/lifecycle/membership changes roll back completely.
- Added rollback coverage for membership acceptance and ownership transfer, including preservation of the pending invitation and exactly one active owner.
- Verified successful claim approval, membership acceptance and ownership transfer produce the expected staff/provider audit events.
- Verified claim approval leaves the provider in `draft`, and even an approved profile revision cannot build a public read document until the provider is explicitly `published`.
- Reused the existing transactional service boundaries and public read-model lifecycle guard; no new product behavior or roles were added.

## Verification

- Implementation exact-head `477b881f134e766d4ed674d5695b760f4d033e3f` passed Compose CI `33948884372`, all 24 steps including lint/format, mypy, dependency/secret checks, reproducible builds, canonical startup, migrations, Django tests, browser gate, evidence upload and disposable smoke.
- Final closeout exact-head must pass the same Compose workflow after this archive/update commit.

## Remaining

- Next active P3 item is acceptance: live approved state remains visible while edits await moderation.
