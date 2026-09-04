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

- Exact implementation head `e094092275f2b6120f84355cb495657114841ff0` passed the full Compose stack workflow in run `33838830295`.
- Passed bootstrap/contracts, Ruff lint/format, mypy, dependency audit, secret scan, reproducible build, migrations, Django deploy checks, canonical non-browser tests, browser/Playwright evidence and smoke.

## Remaining

The remaining active P1 acceptance criteria and gates stay in `tasks/P1-domain.md`.
