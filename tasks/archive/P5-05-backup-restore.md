# P5-05 — Encrypted backup and isolated restore drill

Completed the active P5 build step: encrypted off-site database/media backup and isolated restore drill.

## Verification

- `infra/scripts/backup-production.sh` creates a PostgreSQL custom-format logical dump from the running production database, mirrors production media through an external rclone source, records media SHA-256 checksums, and stores the snapshot in an encrypted Restic repository.
- Backup retention is daily 14 days plus weekly 8 weeks, with a Restic integrity check before pruning.
- `infra/scripts/restore-drill.sh` restores the latest production snapshot to temporary storage, verifies media checksums, restores PostgreSQL into a fresh isolated container with no published ports, validates `django_migrations`, removes drill resources on exit, and fails if the four-hour RTO target is exceeded.
- The production Ansible baseline installs `restic` and `rclone`, so a freshly provisioned host has the required backup tooling.
- `docs/runbooks/database-restore.md` documents required external secrets, nightly backup expectations, monthly isolated restore evidence, RPO <= 24h, RTO <= 4h, and the prohibition on recording credentials or personal data.
- Regression contracts validate shell syntax, encryption/retention requirements, isolated restore safety, integrity checks and evidence rules.

## Evidence

- Implementation verification head: `77c31a66d822e0ba1cff2a276d33289a377be3bb`.
- GitHub Actions `Compose stack` run `33990762620`: PASS on the exact implementation head, including lint/format, type check, dependency/secret checks, builds, migrations, provider security/integration, canonical non-browser/browser gates, Playwright evidence and disposable smoke.
- GitHub Actions `Ansible baseline` run `33990762414`: PASS on the exact implementation head.

## Deviations

- The repository verifies the backup/restore implementation and isolated restore contract without production credentials or production data. The first real off-site snapshot and timed monthly restore use operator-supplied production backup credentials outside Git, as required by the runbook.
