# P3-03 — Provider onboarding and revision flow

## Scope

Add the provider workspace profile lifecycle around the existing `ProfileRevision`: draft autosave, preview, submit for moderation, corrections and approval while preserving the currently approved live profile until replacement is approved.

## Completed

- Added an authenticated provider workspace scoped by active `ProviderMembership`; cross-provider workspace access returns 404.
- Added provider profile draft editing with normal POST saves and HTMX autosave support.
- Drafts are seeded from the most recent approved revision, or from current provider state when no approved revision exists.
- Added provider preview and explicit submit-for-review flow with required-field validation.
- Submission makes the revision `pending`; published providers remain published with their existing live state while edits await moderation.
- Added staff correction requests and approval workflow over the existing `ProfileRevision` model.
- Correction requests preserve the approved live profile; non-live onboarding providers move to `changes_requested`.
- Approval atomically applies the revision to the provider, publishes it, supersedes the previous approved revision and records review metadata.
- Staff correction/approval actions create provider audit events.
- Added admin actions and revision diff support for staff review.
- Added regression coverage for autosave → preview → submit → approve, live-state preservation during pending/corrections, workspace isolation and HTTP submission.

## Verification

- Implementation exact-head `37dcf5b6794a67360b56e8df9ebf4eefc0ec74d9` passed Compose CI `33938531092`, including lint/format, type check, dependency/secret scans, migrations, canonical non-browser tests, browser gate and disposable smoke gate.
- Final closeout exact-head must pass the same Compose workflow after this archive/update commit.

## Remaining

- Next active P3 build item is structured contacts, services/prices, areas/modes, languages and image upload pipeline.
