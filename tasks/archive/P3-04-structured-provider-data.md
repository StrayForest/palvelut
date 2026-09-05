# P3-04 — Structured provider data

## Scope

Extend the existing moderated provider revision flow with structured contacts, services/prices, service areas/modes, languages and an image upload pipeline without exposing draft changes before staff approval.

## Completed

- Added structured provider workspace fields for contacts, services/prices, service areas/modes and languages with server-side validation against the existing enums and taxonomy records.
- Draft autosave now keeps those structured values inside `ProfileRevision` while preserving staged media.
- Drafts can be seeded from the current live relational provider state, so existing approved data remains the basis for later edits.
- Staff approval atomically replaces the live `ContactChannel`, `ProviderService`, `ServiceArea`, `ProviderLanguage` and `MediaAsset` state from the approved revision.
- Pending structured edits remain non-live until staff approval, preserving the existing approved public profile.
- Added authenticated image upload staging through Django storage with JPEG/PNG/WebP MIME allowlisting, a 10 MiB size limit and extension/content-type consistency checks.
- Uploaded image metadata is stored in the moderated revision and no live `MediaAsset` is created until staff approval.
- Added the provider workspace media upload route and UI with alt-text input and an explicit staged-moderation notice.
- Added regression coverage for structured form normalization, non-live draft state, atomic promotion on approval and staged media publication.

## Verification

- Implementation exact-head `5a2d17415a1af6268e4ac80a0c2a4b74dbcddfbd` passed Compose CI `33940049209`, including lint/format, type check, dependency/secret scans, migrations, canonical non-browser tests, browser gate, Playwright evidence and disposable smoke gate.
- Final closeout exact-head must pass the same Compose workflow after this archive/update commit.

## Remaining

- Next active P3 build item is status/checklist dashboard and aggregate impressions/views/contact-clicks.
