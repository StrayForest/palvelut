# P1-09 — Approved-only public read model

## Scope

Generate the denormalized public read/search document only from approved provider state, without building public browse or provider self-service.

## Completed

- Added `discovery.ProviderReadDocument` as a one-to-one public read model for a provider, tied to the exact source `ProfileRevision`.
- Added transactional read-model generation that requires a published provider and an approved revision.
- Wired staff approve/publish to rebuild the public document from the approved revision payload.
- Kept later draft/pending revisions out of the existing live document until they are approved.
- Wired suspension to remove the provider public read document.
- Added tests covering approved generation, pending-edit isolation, refusal without an approved revision and suspension cleanup.

## Verification

- Implementation exact-head CI `33830424874` passes Ruff lint/format, mypy, dependency audit and secret scan.
- Migration checks, Django deploy checks, canonical non-browser tests, browser evidence and disposable smoke gate pass.
- Canonical CI gates must pass on the exact archival PR head before merge.

## Remaining

Staff create/import completion, claim-to-membership enforcement, deterministic duplicate handling and the remaining P1 acceptance/gates stay active in `tasks/P1-domain.md`.
