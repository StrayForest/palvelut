# P3-12 — Provider quality gates

## Scope

Close the final active P3 Gates requirement: auth/CSRF/IDOR/rate-limit tests, upload safety corpus, email flow, revision concurrency, Playwright mobile/desktop coverage and accessibility smoke.

## Completed

- Added an explicit P3 provider security/integration CI gate over the stable provider acceptance/security suites.
- Covered account auth/rate limiting, email verification and staff MFA; provider claim/atomicity; cross-provider IDOR; image upload safety; team ownership; revision/workspace flows; analytics and concurrency constraints.
- Added an explicit provider CSRF regression: an authenticated workspace write without a CSRF token returns `403` and creates no revision.
- Kept the existing mobile onboarding browser acceptance and added a desktop keyboard/accessibility smoke using Axe, blocking serious/critical violations.
- Kept the canonical full non-browser, browser evidence and disposable smoke gates mandatory after the focused P3 gate.

## Verification

- Implementation exact-head `ba36d6eb5ae0e689ac905bb95aa339a4efab173d` passed Compose CI `33954630103`, including the focused P3 security/integration gate, canonical non-browser tests, Playwright browser gate, evidence upload and disposable smoke gate.
- The documentation closeout head must pass the same Compose workflow before merge.

## Remaining

- P3 has no remaining active Build, Accept or Gates items after this closeout.
- P4 is not started by this step.
