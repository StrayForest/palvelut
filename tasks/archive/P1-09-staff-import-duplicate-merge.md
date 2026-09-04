# P1-09 — Staff import and duplicate merge

Completed: 2026-09-04

## Scope

Complete the remaining bounded staff back-office work for non-public provider import and deterministic duplicate merging without starting public browse, public read/search generation or provider self-service.

## Completed

- Added a staff-only, idempotent provider import service keyed by nonblank Y-tunnus.
- Imported providers remain `unclaimed`, carry no membership and cannot become public until the existing approved-claim flow is completed.
- Added a staff-only management command for importing one provider through the service layer.
- Added deterministic two-provider merge handling with transactional row locks, conflict rejection for different nonblank Y-tunnus values and transfer/deduplication of provider services, areas, languages, contacts, media and memberships.
- Archived the duplicate provider instead of deleting it and recorded audit events for both the canonical and merged records.
- Added the merge action to staff admin.
- Added regression tests for staff permission enforcement, import idempotency/non-public state, related-row transfer, source archival, audit events and conflicting Y-tunnus rejection.

## Verification

- Exact implementation head `646e95a2c70513af28c405d032fe7fe2c904c902` passed the full `Compose stack` workflow in run `33821698086`.
- Bootstrap/command contracts, Ruff lint/format, mypy, dependency audit, secret scan, reproducible static build, application build, development/reset checks, fresh database migrations, taxonomy tests, Django deploy checks, canonical non-browser tests, browser/Playwright evidence and disposable smoke all passed.

## Remaining

Approved-state public read/search document generation and the still-unmet P1 acceptance/gates remain active in `tasks/P1-domain.md`.
