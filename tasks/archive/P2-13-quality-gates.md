# P2-13 — Public discovery quality gates

## Scope

Close only the remaining P2 Gates requirement from `tasks/P2-discovery.md`. Do not start P3 or perform the separate stage-transition step.

## Completed

- Kept the existing search relevance fixtures, cache isolation, metadata/schema coverage, required-width Playwright checks and retained visual evidence in the canonical gates.
- Added an explicit PostgreSQL `EXPLAIN` query-plan check for the public discovery queryset.
- Added axe coverage for the public home, populated-search and empty-search surfaces, blocking serious and critical accessibility violations.
- Added Lighthouse checks for the documented performance, accessibility and SEO quality categories.
- Added anonymous cold/warm discovery browser smoke against the documented response budgets: cold ≤800ms and warm ≤300ms.
- Pinned the browser-gate tooling in the existing E2E image so the checks run inside the canonical Compose workflow.

## Verification

- Initial implementation run `33931841718` proved the SQL/query-plan, axe and cold/warm checks but exposed an invented, undocumented Lighthouse best-practices threshold; that extra threshold was removed rather than weakening a documented contract.
- Implementation exact-head `b6ea922153045c9ae0c09685d7d33fae2267c79e` passed Compose CI `33932235632`, including lint/format, type/dependency/secret checks, reproducible build, migrations/deploy checks, canonical non-browser tests, all browser gates, retained evidence upload and disposable smoke.
- Final closeout exact-head must pass the same Compose workflow before merge.

## Remaining

- `tasks/P2-discovery.md` has no active Build, Accept or Gates items. Stage completion/roadmap transition is intentionally left for the next documented step.
