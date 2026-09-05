# Observability runbook

## Scope

The production dashboard and alerts cover the signals required by `docs/06-quality.md`: traffic, latency, errors, cache hit ratio, database connections/slow queries, queue depth/age/failures, email delivery, media failures and backups.

## Runtime wiring

- Set `SENTRY_DSN`, `SENTRY_ENVIRONMENT` and `SENTRY_RELEASE` to send sanitized unhandled exception envelopes to Sentry. Events contain exception type/value, environment, release and request ID only; request bodies, user identity and headers are not sent.
- Set a strong `OBSERVABILITY_METRICS_TOKEN`. Prometheus scrapes `/palvelut/internal/metrics` with `Authorization: Bearer <token>`; staging/production return 404 without the configured token.
- The metrics payload includes `palvelut_build_info{environment,release,schema="quality-v1"}` so dashboards retain the environment/release/schema context.
- `infra/observability/dashboard.json` is the canonical dashboard query contract. `infra/observability/alerts.json` is the canonical alert contract.

## Alert response

1. Confirm environment/release in `palvelut_build_info` and inspect Sentry using the correlated request ID. Do not paste personal data into incident notes.
2. For 5xx/latency, compare public request rate, p95 latency, DB waiters/slow queries and cache hit ratio before scaling.
3. For queue alerts, stop adding concurrency blindly; inspect queue depth, latest queue age and task failures first.
4. For email/media alerts, check the relevant upstream service and retry only idempotent operations.
5. For backup alerts, treat a failed or missing daily success as release-blocking and follow the database/media restore runbook once the backup step is implemented.
6. Record incident start/end, release, metric/alert name and remediation. Do not record secrets, message bodies, uploaded media or user identifiers.

## Signal producers

- Request middleware: traffic, status class, request latency and DB query duration/slow-query count.
- Discovery cache wrapper: hit/miss/bypass counters.
- PostgreSQL scrape collector: active and waiting connections.
- Valkey/Celery collectors and signals: queue depth, last observed age and task failures.
- SMTP backend wrapper: successful/failed deliveries.
- Media upload path: infrastructure/processing failures; validation failures are excluded.
- Backup jobs call `palvelut.observability.observe_backup(success=...)` when the backup implementation is added in the dedicated P5 backup step.
