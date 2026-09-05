# P3-12 — Analytics privacy acceptance

## Scope

Close the provider analytics acceptance criterion by making aggregate metric definitions visible in the provider workspace and pinning the storage contract so provider analytics cannot silently grow visitor-identity fields.

## Completed

- Expanded the provider workspace analytics note to state that visitor identity, IP address, search text and cross-site identifiers are neither stored nor shown.
- Added visible definitions for impressions, profile views and contact clicks next to the aggregate provider totals.
- Added a regression test that pins the concrete `AnalyticsEvent` schema to provider, event kind, optional contact channel, timestamp and UUID only.
- Preserved the existing provider-scoped aggregate analytics flow; no visitor profiling, new analytics identifiers or product-scope changes were introduced.

## Verification

- Implementation exact-head `7973eccb813a4184722825d9b4fb89405bada395` passed Compose CI `33953018879`, including bootstrap, dependency contracts, lint/format, mypy, dependency/secret checks, reproducible builds, migrations, Django tests, browser evidence and disposable smoke.
- Final closeout exact-head must pass the same Compose workflow after this archive/task-state commit.

## Remaining

- P3 stage-level Gates remain active; no later P3 step was started.
