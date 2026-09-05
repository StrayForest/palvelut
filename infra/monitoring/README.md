# Production observability

The application exposes Prometheus text format at `127.0.0.1:8080/palvelut/internal/metrics`. The public host Nginx returns `404` for that path; scrape it only from the host/private monitoring plane. Import `dashboard.json` into Grafana and load `alerts.yml` into Prometheus-compatible alerting. Every alert links to `RUNBOOK.md`.

Sentry error delivery is enabled by `SENTRY_DSN`; `SENTRY_RELEASE` should be the exact deployed image/commit identifier. The transport sends exception type/message and `request_id` only. It deliberately does not attach request bodies, cookies, headers, user identity, query strings or uploaded data.

| Quality signal | Metric/source |
|---|---|
| traffic | `palvelut_http_requests_total` |
| latency | `palvelut_http_request_duration_seconds` |
| errors | `palvelut_http_5xx_total` + Sentry |
| cache hit ratio | `palvelut_cache_requests_total{result=...}` |
| DB concurrency | `palvelut_db_connections_in_use` |
| slow queries | `palvelut_db_slow_queries_total`, `palvelut_db_query_duration_seconds` |
| queue age | `palvelut_queue_age_seconds` stamped at Celery publish/run |
| queue failures | `palvelut_queue_failures_total` from Celery failure signal |
| email delivery | `palvelut_email_delivery_total` from the SMTP backend |
| media failures | `palvelut_media_failures_total` from upload processing |
| backups | `palvelut_backup_last_success_timestamp_seconds`, `palvelut_backup_failures_total`; the backup job owns calling `palvelut.metrics.record_backup` when that P5 job is implemented |

Metric labels are intentionally bounded to HTTP method/status class, cache result and email result. No provider, account, IP, URL/query, email address or other personal identifier is a metric label.

The dashboard is operational only. First-party business-funnel analytics remain in the analytics module and retain their separate schema/version/exclusion contract from `docs/06-quality.md`.
