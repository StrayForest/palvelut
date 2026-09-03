# P1-08 — Staff moderation admin

## Scope

Add the bounded staff moderation back office for revision review, moderation actions and audit visibility without building public browse or provider self-service.

## Completed

- Registered providers in Django staff admin with related membership, service, area, language, contact and media inlines.
- Added staff-only moderation service actions for approve/publish, request changes and suspend with transactional row locking.
- Enforced approved claim state before the moderation service can publish a provider.
- Added revision diff display for staff and kept profile revisions non-addable/non-deletable from the revision admin.
- Exposed moderation/audit records as read-only staff admin views.
- Recorded moderation actor, timestamp and action metadata for approve, request-changes and suspend transitions.
- Added service/admin tests covering approved publication, unclaimed rejection, request changes, suspension, audit creation and non-staff denial.

## Verification

- Ruff lint/format, mypy, dependency audit and secret scan pass.
- Canonical non-browser tests, browser evidence and disposable smoke gate pass.
- Canonical CI gates must pass on the exact archival PR head before merge.

## Remaining

Staff create/import completion, duplicate merge handling, public read-model generation and the remaining P1 acceptance/gates stay active in `tasks/P1-domain.md`.
