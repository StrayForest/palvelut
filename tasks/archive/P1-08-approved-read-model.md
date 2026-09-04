# P1-08 — Approved public read model

Completed: 2026-09-04

## Scope

- Added a provider public read/search snapshot owned by the discovery module.
- Generate the public document and searchable text only from an approved profile revision payload.
- Refresh the public snapshot when staff approves a new revision and remove it when the provider is suspended.
- Added regression coverage proving pending edits cannot create or replace the live read model.
- Kept public browse/search UI and provider self-service out of scope.

## Checks

- Exact implementation head `0447cd594e56115b83834b29fa8eed40b145df9b` passed the full Compose stack workflow in run `33829926188`.
- Passed bootstrap/contracts, Ruff lint/format, mypy, dependency audit, secret scan, reproducible frontend/static build, application build, startup/reset checks, fresh migrations, taxonomy model tests, Django deploy checks, canonical non-browser tests, browser/Playwright evidence and smoke.

## Deviations

- None.
