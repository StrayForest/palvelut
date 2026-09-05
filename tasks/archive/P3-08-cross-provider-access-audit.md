# P3-08 — Cross-provider access audit acceptance

## Scope

Prove that an authenticated provider account cannot read or mutate another provider's workspace state and that every denied cross-provider workspace attempt leaves a minimal server-side audit trail without exposing the target provider.

## Completed

- Preserved the existing IDOR-safe `404` response for provider workspace access without an active membership.
- Added `ProviderAccessAudit` records for denied workspace access with actor, target provider UUID, HTTP method, request path, denied outcome and timestamp.
- Kept the denial audit minimal: no IP address, visitor identifier, query string or request body is stored.
- Applied the same membership/audit boundary to edit, preview, media-upload and submit endpoints.
- Added regression coverage proving cross-provider reads and writes return `404`, do not create a `ProfileRevision`, do not mutate the protected provider and independently audit sensitive denied actions.

## Verification

- Implementation exact-head `5eb4363769b717b8ecb628acd729f491ce8184a5` passed Compose CI `33947684155`, all 24 steps including lint/format, mypy, dependency/secret checks, reproducible builds, canonical startup, migrations, Django tests, browser gate, evidence upload and disposable smoke.
- Final closeout exact-head must pass the same Compose workflow after this archive/update commit.

## Remaining

- Next active P3 item is acceptance: claim, reject, transfer and membership changes are atomic, staff-audited and cannot expose an unapproved profile.
