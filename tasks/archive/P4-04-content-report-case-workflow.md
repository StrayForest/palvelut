# P4-04 — Anonymous content report case workflow

Completed the active P4 build step: anonymous visitors can report public provider content, staff process the report through the existing moderation case system, and providers receive an explicit notice/appeal/status trail without exposing reporter identity.

## What changed

- Added anonymous content-report cases on top of the existing moderation subsystem instead of creating a parallel case model.
- Reports store category/details but no reporter account; a random status secret is shown once and only its hash is persisted for later status checks.
- Added a public report surface from provider profiles, acknowledgement receipt and protected report-status lookup.
- Added staff content-report queue/detail actions for provider notice, resolve and dismiss, with append-only moderation events and staff audit records.
- Provider members see only explicitly provider-visible case events and can append an appeal/response; internal report-received metadata remains hidden from the provider surface.
- Added per-provider/client rate limiting for public report submission and restricted reporting to currently published providers.
- Added deterministic regression coverage for anonymous case creation, status-secret protection, provider notice/audit, appeal/resolve trail and cross-provider isolation.

## Evidence

- Implementation exact head: `8cc81791a3328a7397683ffda67140acf0e71535`.
- GitHub Actions `Compose stack` run `33962615364`: PASS on the exact implementation head, including lint/format, type check, dependency/secret scans, clean migrations, provider security/integration gate, canonical non-browser/browser gates, evidence upload and disposable smoke.

## Deviations

None.
