# P4-15 — Abuse tests

Completed the next active P4 gate: abuse regressions now prove authentication throttles resist normalized-identity bypasses and staff MFA brute-force attempts without duplicating already archived report, IDOR, upload, or baseline authentication acceptance work.

## What changed

- Added a login abuse regression that varies email case and surrounding whitespace from one client address and requires the shared throttle to block the next otherwise-valid login.
- The regression exposed an internal-whitespace throttle-key bypass; login throttle identity is now stripped before IP/identity key composition, while the existing hashed throttle-key and rate-limit behavior remains unchanged.
- Added staff MFA brute-force regression coverage: eight invalid codes consume the configured allowance and the following valid TOTP is still blocked.
- Existing content-report rate limiting, cross-provider access/IDOR coverage, upload safety regressions, and baseline account-security acceptance are reused rather than duplicated.

## Evidence

- Implementation exact head: `fa8325abe8f49dc8ad16d7117c4ae6cac185fb73`.
- GitHub Actions `Compose stack` run `33995006890`: PASS on that exact head, including lint/format, type check, dependency/secret scans, migrations, provider security/integration, canonical non-browser/browser gates, Playwright evidence upload, and disposable smoke.
- PR: #131.

## Deviations

None.
