# Operations

## Environments

- Local: disposable data, Mailpit, local object storage emulator.
- Staging: production configuration, synthetic/non-personal data, protected from indexing.
- Production: EU region, least-privilege credentials, Cloudflare proxy, off-site backups.

Each environment has separate databases, buckets, secrets and domains. Production data is never copied to local/staging.

P0–P4 require no rented server: they run through Docker Compose locally and fresh GitHub Actions services. On Windows 11 the supported path is WSL2 + Docker Desktop WSL integration; commands run inside WSL2. P5 begins only when production infrastructure exists.

## Delivery

PR gates: format/lint/type → unit/integration → migration check → security/secret scan → browser/accessibility → image build. Main produces an immutable image tagged with commit SHA. Third-party actions are full-SHA pinned with read-only default token permissions.

`main` branch protection/rulesets are intentionally deferred by the owner and are not a P0 completion requirement. Continue using PRs and green CI as the working delivery discipline, but do not enable repository protection until the owner explicitly requests it.

Production deploy promotes the exact tested image digest. Start inactive web containers, run backward-compatible migrations, pass readiness/synthetic checks, switch Nginx upstream, then retain the prior web set for rollback. Drain and replace workers separately; run exactly one scheduler. Database rollback uses the migration/restore plan, never an automatic destructive downgrade.

Use backward-compatible migrations: expand → deploy → backfill → switch reads → contract later. A failed health/readiness check stops rollout.

## Reproducible host

Idempotent Ansible owns an Ubuntu LTS baseline, non-root deploy user, SSH/firewall policy, automatic security updates, pinned Docker packages, app directories/volumes, Nginx and secret-file placement. Secrets are supplied outside Git and never printed. A run against a fresh VPS plus documented restore must recreate staging/production; manual server tweaks are defects.

## Backups

- PostgreSQL: nightly logical backup plus continuous/regular physical strategy as volume warrants.
- R2: versioning/lifecycle policy for originals.
- Encrypt, store off-server, retain daily 14 days + weekly 8 weeks.
- Automated integrity check; monthly restore into isolated environment with recorded RTO/RPO.

Initial targets: RPO ≤24h, RTO ≤4h. Tighten after revenue or sensitive workflows justify it.

Quarterly, rebuild a fresh disposable rehearsal host from Ansible and restore current backups. Record duration, image/config revision and pass/fail without secrets or personal data.

## Runbooks required before beta

Deploy/rollback, database restore, leaked secret, provider impersonation, illegal-content report, account takeover, object-storage outage, email outage and cache purge.

## Capacity decisions

Scale only from dashboards. First actions: fix query plans/N+1, increase cache hit rate, resize bounded pools, then add replicas. Never raise database connections without CPU/memory evidence.
