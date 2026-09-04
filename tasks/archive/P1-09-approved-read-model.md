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

- Exact archival PR head `08f4e7bbc7c5df5d95d0c73bff90506426c012ee` passed the full Compose stack workflow in run `33831183602`.
- Passed bootstrap/contracts, Ruff lint/format, mypy, dependency audit, secret scan, reproducible build, migrations, Django deploy checks, canonical non-browser tests, browser/Playwright evidence and smoke.

## Remaining

Only the still-active P1 acceptance criteria and gates remain in `tasks/P1-domain.md`.
