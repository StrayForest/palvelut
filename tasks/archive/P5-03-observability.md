# P5-03 — Observability baseline

Completed the active P5 build step: Sentry, metrics, dashboards and alerts for every signal named in `docs/06-quality.md`.

## Verification

- Request traffic, duration and 5xx counters are emitted through the shared Valkey-backed metric registry.
- Public read-through cache hits and misses feed the cache-ratio signal.
- The registry defines database pool/slow-query, queue age/failure, email delivery, media failure and backup age/failure signals for operational producers.
- `/palvelut/metrics` is bearer-token protected, disabled when the external token is absent and marked `no-store`.
- Sentry envelope reporting is optional through external `SENTRY_DSN`, tags events with environment/release/request ID and intentionally omits request/user payloads.
- Grafana-compatible dashboard JSON covers every quality-doc signal.
- Prometheus alert rules cover availability/5xx, latency, cache, database, queue, email, media and backups; every alert links to the observability runbook.
- Production Compose requires the release SHA and metrics token outside Git and accepts the Sentry DSN outside Git.
- Contract tests pin signal coverage, endpoint authorization and privacy/runbook requirements.

## Evidence

- Implementation is verified by the repository `Compose stack` gate on the exact PR head before merge.

## Deviations

- Database, queue, email, media and backup producers are registered now; their concrete job/exporter hooks are completed by the corresponding later P5 build steps rather than duplicating those workflows here.
