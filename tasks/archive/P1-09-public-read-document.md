# P1-09 — Approved public read document

## Scope

Generate the public provider read/search document only from approved revision state, without exposing pending edits or building public browse/provider self-service.

## Completed

- Added a dedicated `PublicProviderDocument` with one live document per provider and an explicit source revision.
- Generate/update the live document only after moderation approves a revision and the provider enters published state.
- Keep pending revisions isolated from the live document until a later approval replaces it.
- Supersede the previous approved revision when a newer revision becomes live.
- Remove the live public document when the provider is suspended.
- Added focused tests for first publication, pending-edit isolation, replacement on re-approval and suspension cleanup.

## Verification

- Ruff lint/format, mypy, dependency audit and secret scan pass.
- Migration checks and canonical non-browser tests pass.
- Canonical browser evidence and disposable smoke gate pass.
- Implementation exact-head CI run `33824385955` passed before archival.
- Canonical CI gates must pass again on the exact archival PR head before merge.

## Remaining

The remaining P1 acceptance criteria and gates stay active in `tasks/P1-domain.md`.
