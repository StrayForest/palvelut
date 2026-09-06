# P5-11 — Backup restore RPO/RTO acceptance

Completed the active P5 acceptance step: backup restore proves the RPO/RTO targets while emitting evidence without secrets or restored data.

## Verification

- `infra/scripts/restore-drill.sh` reads the latest production-tagged snapshot metadata before restore and fails when its age exceeds 24 hours (`86400` seconds).
- The isolated restore still verifies media checksums, restores PostgreSQL into a non-published container and validates `django_migrations`.
- The drill fails when total restore duration exceeds four hours (`14400` seconds).
- Successful evidence contains only the command identifier, UTC start/end timestamps, snapshot age, RPO/RTO targets, duration and pass status; snapshot IDs, credentials, rows and media/object names are excluded.
- `tests/test_backup_restore_contract.py` locks the RPO/RTO calculations and safe-evidence contract.
- `.github/workflows/p5-ansible.yml` exercises the encrypted restore fixture on a freshly provisioned disposable host.

## Evidence

- Verification is provided by the PR `Compose stack` and `Ansible baseline` runs on the exact final head.

## Deviations

- CI uses a disposable encrypted Restic fixture rather than production credentials or production data. Production monthly drills use the same script and record the same bounded evidence fields outside Git.
