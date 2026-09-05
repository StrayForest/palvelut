# P3-01 — Provider authentication and staff MFA

## Scope

Close only the first P3 Build requirement from `tasks/P3-provider.md`: email-verified provider authentication, secure sessions/password reset and mandatory staff MFA. Do not start the claim flow or any later P3 work.

## Completed

- Added provider registration by normalized email with accounts inactive until a one-time, expiring email-verification token is redeemed; only a SHA-256 token digest is stored.
- Added Argon2 as the primary password hasher with the dependency locked reproducibly.
- Added login and password-reset flows with generic reset responses, cache-backed rate limits and session-key rotation around authentication-sensitive transitions.
- Hardened session/CSRF cookie settings for the `/palvelut/` mount and retained secure-cookie enforcement in staging/production.
- Added TOTP MFA enrollment/verification for staff and middleware that blocks the `/palvelut/staff/` surface until MFA succeeds; external `next` redirects are rejected.
- Added regression coverage for verification activation/replay, Argon2, login throttling/session rotation, password-reset non-enumeration/rate limiting, staff MFA enforcement and non-staff isolation.

## Verification

- Intermediate exact-head runs exposed and fixed only gate issues: formatting, a mypy narrowing issue and secret-scan false positives on test-only password fixtures.
- Implementation exact-head `19318e5897886b40621d406eedd3ea5a5b3572ac` passed Compose CI `33935669225`, including bootstrap/contracts, lint/format, mypy, dependency audit, secret scan, reproducible builds, development/reset contracts, migrations, deploy checks, canonical non-browser tests, browser gates with retained evidence and disposable smoke.
- Final closeout exact-head must pass the same Compose workflow before merge.

## Remaining

- The next active P3 Build item is the existing-unclaimed-draft claim flow with independent business-control evidence and staff approval; it is intentionally not started here.
