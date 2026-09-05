# P4-12 — Security headers and CSP

Archived from `tasks/P4-trust.md` after exact-head verification.

## Completed

- Added a restrictive first-party Content Security Policy with frame/object blocking and explicit resource directives.
- Dynamic JSON-LD uses a per-request CSP nonce instead of allowing inline scripts globally.
- Added a restrictive Permissions-Policy while retaining MIME-sniffing, frame-denial, and referrer protections.
- Disabled HTMX's automatic inline indicator stylesheet so the browser remains clean under the restrictive `style-src` policy.
- Deterministic tests cover the security-header contract and nonce matching.

## Verification

Implementation/verification exact head `139698c465967bcaf08bef372a667c60feb8675f` passed Compose stack run `33985700836`, including canonical browser and disposable smoke gates. Verification PR #125 was squash-merged as `b6576488717fc690e1c30596f7a238894bf6c7ee`.
