# Palvelut observability runbook

Do not paste personal data, credentials, message bodies, uploaded media or full request query strings into incident notes. Correlate application logs and Sentry with `request_id`.

## Traffic

Confirm Cloudflare/origin reachability, `web` health and Prometheus scrape health. A quiet pre-launch service may legitimately have no traffic; silence the warning only with a dated reason.

## Latency, errors and cache

Check HTTP p95, 5xx ratio and cache hit ratio together. Use request IDs to inspect structured logs/Sentry. Fix query/N+1 or cache regressions before increasing capacity. Do not make authenticated responses cacheable.

## Database

Inspect query concurrency and queries over 300 ms, then PostgreSQL CPU, locks and query plans. Do not increase connection capacity without CPU/memory evidence.

## Queue

Check worker health, queue age and failed task logs. Retry only idempotent work. Persistent poison work must be isolated rather than retried indefinitely.

## Email

Check SMTP provider status and delivery failures. Do not log recipient addresses or message bodies in monitoring systems.

## Media

Check object-storage reachability and image validation/processing errors. Never copy production uploads into local or staging environments.

## Backups

A missing success heartbeat after 26 hours or any backup failure is critical. Verify the off-site backup job, storage destination and integrity check. Do not mark resolved until a successful backup has completed. Restore validation is handled by the dedicated backup/restore procedure.
