# P5 — Production readiness

Depends: P4. Read: `docs/06-quality.md`, `docs/07-operations.md`.

## Build

## Accept

- Backup restore meets RPO/RTO target; evidence records commands/times, not secrets/data.
- Load test meets every SLO and shows bounded pools/queues under overload.
- Rollback and one simulated incident are executed successfully.
- App-only deployment produces no failed synthetic request during upstream switch; unsafe database rollback stops for operator action.

## Gates

Full CI, Ansible lint/idempotence, fresh-host restore, production-config check, image/SBOM scan, cache/auth probe, warm/cold load test, backup restore, zero-failure deploy/rollback smoke and synthetic checks.
