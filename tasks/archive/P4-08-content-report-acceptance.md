# P4-08 — Content report acceptance

Completed the active P4 acceptance criterion: reports are rate-limited, acknowledged and auditable without exposing reporter data.

## Verification

- Anonymous public report submissions are acknowledged with `202` while accepted.
- The per-provider/client limiter accepts five reports per hour and returns `429` with `Retry-After: 3600` for the sixth.
- Reporter identity is absent from the moderation case and report-received event; the one-time status token is stored only as a hash.
- Staff moderation remains auditable, and the acceptance regression pins audit metadata to the moderation `case_id` only, without reporter identity.
- Existing P4-04 content-report implementation is reused; no duplicate workflow, model or public surface was added.

## Evidence

- Acceptance verification exact head: `5772584a28ee7f67b27d7ad6464295d8199cd13d`.
- GitHub Actions `Compose stack` run `33967722920`: PASS on the exact verification head, including lint/format, type check, dependency/secret checks, builds, migrations, provider security/integration, canonical non-browser/browser gates, Playwright evidence and disposable smoke.

## Deviations

None.
