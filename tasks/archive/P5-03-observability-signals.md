# P5-03 — Production observability signals

Completed the next P5 build item: Sentry, metrics, dashboards and alerts for every signal named in the quality docs.

## Delivered

- Unhandled web and Celery task exceptions can be delivered to Sentry with environment, release and request-ID context while excluding request bodies, headers and user identity.
- `/palvelut/internal/metrics` exposes a Prometheus-compatible contract; staging/production require a configured bearer token and otherwise return `404`.
- Request middleware records traffic, status class, request latency, database query latency and slow-query counts; PostgreSQL connection/wait gauges are collected at scrape time.
- Discovery cache instrumentation records hit/miss/bypass counters, and Celery instrumentation records queue depth, observed queue age and task failures.
- SMTP delivery and media-processing failures are instrumented; a backup result hook is provided for the later dedicated backup step without implementing that later step early.
- `infra/observability/dashboard.json` covers traffic, latency, 5xx, cache hit ratio, database queries/connections/waits, queue health, email, media and backup signals.
- `infra/observability/alerts.json` covers availability/latency, database, queue, email, media, backup and cache regressions and points to `docs/runbooks/observability.md`.
- Metrics include environment/release plus `schema="quality-v1"` build metadata for operational correlation.

## Verification

- `Compose stack` run `33982078924`: PASS on implementation head `b27f286fbf1ed6b37cc70c317ff490e976bc98a2`.
- The exact-head run passed bootstrap, dependency/command contracts, lint/format, type check, dependency and secret scans, frontend/application builds, migrations, Django deploy checks, provider security/integration, canonical non-browser/browser gates, Playwright evidence and disposable smoke.
- `tests/test_observability_contract.py` pins the dashboard/alert signal coverage, runtime settings and Prometheus build/cross-process signal contract.

## Deviations

- Live Sentry and Prometheus/Grafana credentials/endpoints are environment-specific and remain outside Git; this step establishes the application instrumentation and versioned dashboard/alert contracts.
- Backup production and restore behavior remains a later active P5 build item; this step only provides the observability hook needed for its future signal.
