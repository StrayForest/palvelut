# P3 — Provider workspace

Depends: P2. Read: provider sections of `docs/01-product.md` and `docs/03-experience.md`; security/privacy sections of `docs/06-quality.md`.

## Build

## Accept

- Cross-provider read/write attempts fail and are audited.
- Claim, reject, transfer and membership changes are atomic, staff-audited and cannot expose an unapproved profile.
- Live approved state remains visible while edits await moderation.
- Untrusted/bomb/spoofed images fail; accepted images are re-encoded and metadata-free.
- Analytics reveal no visitor identity and definitions are visible.

## Gates

Auth/CSRF/IDOR/rate-limit tests, upload corpus, email flow, revision concurrency, Playwright mobile/desktop, accessibility smoke.

Do not add user accounts, reviews, billing or chat.
