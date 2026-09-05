# P3 — Provider workspace

Depends: P2. Read: provider sections of `docs/01-product.md` and `docs/03-experience.md`; security/privacy sections of `docs/06-quality.md`.

## Build

- Claim flow for an existing unclaimed draft using independent business-control evidence and staff approval; email possession alone is insufficient.
- Onboarding, draft autosave, preview, submit, corrections and live-profile revision flow.
- Structured contacts, services/prices, areas/modes, languages and image upload pipeline.
- Status/checklist dashboard and aggregate impressions/views/contact-clicks.
- Ownership transfer/invite foundation for business teams; only owner/editor roles now.

## Accept

- Provider completes onboarding on mobile without staff edits.
- Cross-provider read/write attempts fail and are audited.
- Claim, reject, transfer and membership changes are atomic, staff-audited and cannot expose an unapproved profile.
- Live approved state remains visible while edits await moderation.
- Untrusted/bomb/spoofed images fail; accepted images are re-encoded and metadata-free.
- Analytics reveal no visitor identity and definitions are visible.

## Gates

Auth/CSRF/IDOR/rate-limit tests, upload corpus, email flow, revision concurrency, Playwright mobile/desktop, accessibility smoke.

Do not add user accounts, reviews, billing or chat.
