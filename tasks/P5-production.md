# P5 — Production readiness

Depends: P4. Read: `docs/06-quality.md`, `docs/07-operations.md`.

## Build

- Production images/Compose, Cloudflare/Nginx cache contract, WAF/rate-limit rules and safe purge workflow.
- Sentry, metrics, dashboards and alerts for every signal named in quality docs.
- Idempotent jobs/outbox, queue failure/dead-letter handling and data-retention jobs.
- Encrypted off-site database/media backup and isolated restore drill.
- Staging deploy, production deploy/rollback workflow and required runbooks.
- Synthetic monitoring for home, search, profile and contact redirect.

## Accept

- Exact image SHA promotes staging→production without rebuild.
- Authenticated content cannot enter CDN cache.
- Backup restore meets RPO/RTO target; evidence records commands/times, not secrets/data.
- Load test meets every SLO and shows bounded pools/queues under overload.
- Rollback and one simulated incident are executed successfully.

## Gates

Full CI, production-config check, image/SBOM scan, cache/auth probe, warm/cold load test, backup restore, deploy/rollback smoke, synthetic checks.
