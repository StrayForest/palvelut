# P1-11 — Owner-confirmed staff publish flow

## Scope

Close the P1 acceptance criterion that a staff member can create and publish an owner-confirmed provider without SQL or manual code, without adding public browse or provider self-service.

## Completed

- Staff-created providers now receive an initial draft `ProfileRevision` automatically from the back-office create flow.
- The initial revision records the creating staff actor and the provider's core identity payload.
- An approved owner claim can be saved together with the owner membership through the provider admin.
- The existing staff `approve_selected` moderation action can publish that draft and rebuild the approved-only public read document.
- Added an admin regression test that exercises the complete create -> owner membership -> approve/publish flow through Django admin HTTP endpoints.

## Verification

- Pending exact-head CI for branch `codex/p1-owner-confirmed-staff-publish`; this archive entry is complete only after the required workflow passes.

## Remaining

The remaining active P1 acceptance criteria and gates stay in `tasks/P1-domain.md`.
