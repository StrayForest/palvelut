# P1-11 — Staff create-to-publish flow

## Scope

Close the first P1 acceptance criterion by allowing staff to create a reviewable provider profile revision in Django admin and publish an owner-confirmed provider without SQL/manual code, without adding provider self-service.

## Completed

- Enabled permission-controlled staff creation of `ProfileRevision` in Django admin.
- Staff-created revisions are forced to `pending` and record the authenticated staff actor.
- Existing revisions remain immutable in admin.
- Added regression coverage for owner-confirmed provider → staff-created pending revision → moderation approval → published lifecycle → approved-only public read document.
- Verified the actual admin add page exposes `provider` and `payload` fields before exercising the publish flow.

## Verification

- Exact implementation PR head `0889cab11b64cad37d64baf9f63a549ba66d7884` passed the full Compose stack workflow in run `33837435791`.
- Passed bootstrap/contracts, Ruff lint/format, mypy, dependency audit, secret scan, reproducible build, migrations, Django deploy checks, canonical non-browser tests, browser/Playwright evidence and smoke.

## Remaining

Only the still-active P1 acceptance criteria and gates remain in `tasks/P1-domain.md`.
