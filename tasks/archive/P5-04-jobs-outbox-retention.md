# P5-04 — Jobs, outbox and retention

Completed the active P5 build step: idempotent jobs/outbox, queue failure/dead-letter handling and data-retention jobs.

## Verification

- Durable database-backed outbox jobs use stable idempotency keys so duplicate enqueue requests resolve to the same job instead of creating duplicate work.
- Worker claiming is bounded and lock-aware, with stale-lock recovery and bounded retry/backoff before terminal dead-letter state.
- Queue failures record bounded error metadata without task payloads, and dead-lettered jobs remain queryable for operator recovery.
- Queue age/failure/dead-letter metrics are emitted through the existing observability metrics path.
- Existing 90-day raw analytics retention is reused and scheduled; completed/dead-letter job rows also have scheduled retention cleanup.
- The scheduler configuration defines maintenance tasks without adding a second scheduler process; singleton scheduler deployment remains in the later P5 deploy step.

## Evidence

- Implementation verification head: `1a67e71933517ca42ad3c9d32011eae275b8a3c8`.
- GitHub Actions `Compose stack` run `33988441859`: PASS on the exact implementation head, including migration checks, lint/format, type checks, dependency/secret checks, non-browser/browser gates and disposable smoke.

## Deviations

None.
