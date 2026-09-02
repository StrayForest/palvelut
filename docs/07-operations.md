# Operations

## Environments

- Local: disposable data, Mailpit, local object storage emulator.
- Staging: production configuration, synthetic/non-personal data, protected from indexing.
- Production: EU region, least-privilege credentials, Cloudflare proxy, off-site backups.

Each environment has separate databases, buckets, secrets and domains. Production data is never copied to local/staging.

## Delivery

PR gates: format/lint/type → unit/integration → migration check → security/secret scan → browser/accessibility → image build. Main produces an immutable image tagged with commit SHA. Production deploy requires a database backup, migration plan, health checks and tested rollback command.

Use backward-compatible migrations: expand → deploy → backfill → switch reads → contract later. A failed health/readiness check stops rollout.

## Backups

- PostgreSQL: nightly logical backup plus continuous/regular physical strategy as volume warrants.
- R2: versioning/lifecycle policy for originals.
- Encrypt, store off-server, retain daily 14 days + weekly 8 weeks.
- Automated integrity check; monthly restore into isolated environment with recorded RTO/RPO.

Initial targets: RPO ≤24h, RTO ≤4h. Tighten after revenue or sensitive workflows justify it.

## Runbooks required before beta

Deploy/rollback, database restore, leaked secret, provider impersonation, illegal-content report, account takeover, object-storage outage, email outage and cache purge.

## Capacity decisions

Scale only from dashboards. First actions: fix query plans/N+1, increase cache hit rate, resize bounded pools, then add replicas. Never raise database connections without CPU/memory evidence.
