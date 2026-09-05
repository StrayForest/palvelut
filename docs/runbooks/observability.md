# Observability runbook

Applies to Sentry errors and the Prometheus alerts in `infra/observability/alerts.yml`. Do not copy request bodies, email addresses, user identifiers, tokens or other personal data into dashboards, alerts or incident notes. Correlate using the request ID and deployed release SHA.

## Availability and 5xx

Check Sentry for the matching release/request ID, then compare 5xx rate with traffic. Roll back only through the documented deploy workflow; do not bypass readiness checks.

## Latency

Separate cached from uncached traffic, then inspect database and queue panels. Prefer query/cache fixes and bounded-pool evidence before increasing capacity.

## Cache

Confirm the public anonymous cache path is receiving traffic and authenticated/staff/report routes remain bypassed. Never solve a low hit ratio by caching authenticated content.

## Database

Inspect pool pressure and slow-query rate. Check query plans/N+1 and host CPU/memory before changing connection limits.

## Queue

Inspect oldest job age and failure count, then worker health. Preserve idempotency and do not replay unknown jobs manually.

## Email

Check provider status and application failures. Do not log message bodies or recipient addresses.

## Media

Check object-storage availability and image validation/re-encode failures. Do not expose uploaded media or object credentials in incident evidence.

## Backups

A backup older than 25 hours or any backup failure is actionable. Follow the database restore runbook; evidence records timestamps, revision and pass/fail only, never backup contents or secrets.

## Sentry

`SENTRY_DSN` is optional outside production and stored outside Git. Events contain exception type/value, environment, release SHA and request ID only; request/user payloads are intentionally omitted. `PALVELUT_RELEASE` must equal the deployed commit SHA.

## Metrics endpoint

Prometheus scrapes `/palvelut/metrics` with `Authorization: Bearer <METRICS_TOKEN>`. The token is external configuration. Missing token makes the endpoint return 404; a wrong token returns 403. The endpoint is `no-store` and must never be exposed through CDN caching.
