# P3-06 — Provider team ownership foundation

## Scope

Add the business-team invitation and ownership-transfer foundation while keeping provider membership roles limited to owner/editor.

## Completed

- Added persistent provider invitations with pending/accepted/revoked lifecycle and database constraints for valid owner/editor roles and one pending invitation per provider/account.
- Restricted team invitations and ownership transfers to business providers and the active owner.
- Invitations grant no membership until the invited account explicitly accepts; accepted invitations create/restore only an editor membership.
- Ownership can be transferred only to an existing active team member; the operation locks the relevant rows and demotes the previous owner while promoting the target, preserving the existing single-active-owner invariant.
- Added audit events for invite, acceptance and ownership transfer without introducing additional provider roles.
- Added regression coverage for authorization, duplicate pending invites, invitation acceptance and ownership transfer invariants.

## Verification

- Implementation exact-head `28a42619977fb8b625f50c5f34664e1f0bba087e` passed Compose CI `33943683189`, including lint/format, mypy, dependency/secret checks, reproducible builds, migrations, Django tests, browser evidence and disposable smoke.
- Final closeout exact-head must pass the same Compose workflow after this archive/update commit.

## Remaining

- Next active P3 item is acceptance: provider completes onboarding on mobile without staff edits.
