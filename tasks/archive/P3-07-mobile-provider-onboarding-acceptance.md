# P3-07 — Mobile provider onboarding acceptance

## Scope

Prove that an existing claimed provider can complete the editable onboarding flow on a mobile viewport without staff editing, while preserving the existing staff moderation boundary before publication.

## Completed

- Replaced provider-facing raw JSON/UUID entry for primary service, municipality, mode, language and contact data with normal structured form controls backed by the existing moderated `ProfileRevision` payload.
- Kept the existing structured JSON fields hidden for compatibility while making visible edits update the corresponding first structured item rather than silently preserving stale hidden values.
- Made provider form controls mobile-safe at a 360 px viewport without horizontal overflow.
- Kept image upload with alt text inside the draft/revision flow and preserved exact profile preview before submission.
- Added a disposable claimed-provider browser fixture and Playwright coverage for login → workspace → edit/save → image upload → preview → submit for review on a 360×800 viewport.
- Submission still produces a pending revision for staff review; this step does not bypass moderation or publish provider edits directly.

## Verification

- Implementation exact-head `754c9bc99ca295f287c298b2c98e6b64428b0527` passed Compose CI `33945558208`, all 24 steps including lint/format, mypy, dependency/secret checks, reproducible builds, migrations, Django tests, the mobile browser gate, evidence upload and disposable smoke.
- Final closeout exact-head must pass the same Compose workflow after this archive/update commit.

## Remaining

- Next active P3 item is acceptance: cross-provider read/write attempts fail and are audited.
