# Database and media backup/restore

## Backup contract

Production uses `infra/scripts/backup-production.sh` to create one encrypted Restic snapshot containing:

- a PostgreSQL custom-format logical dump created inside the running production database container;
- a checksum-verified copy of the production object-storage bucket;
- `media.sha256` so restored media can be integrity-checked independently.

The Restic repository must be on a separate provider/account or otherwise outside the production host. Restic encryption is mandatory: `RESTIC_PASSWORD_FILE` points to a root-readable secret outside Git. Primary object-store credentials are supplied through `RCLONE_CONFIG_SOURCE_*`; backup credentials use Restic's backend environment and must be distinct where the provider supports it.

Retention is daily 14 days plus weekly 8 weeks. Each backup runs `restic check --read-data-subset=5%` before retention pruning. The script prints only start/end timestamps and status; credentials, database rows and object names are not logged.

Initial targets from `docs/07-operations.md` are RPO <= 24h and RTO <= 4h. Run the backup nightly from the production scheduler/host timer once the production release path is active.

## Required external variables

- `RESTIC_REPOSITORY`
- `RESTIC_PASSWORD_FILE`
- Restic backend credentials, for example `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and region/endpoint for S3-compatible storage
- `RCLONE_CONFIG_SOURCE_TYPE=s3` plus provider, endpoint and source access credentials
- `S3_BUCKET_NAME`
- the normal external production environment consumed by `infra/scripts/production-compose.sh`

Never put these values in Git or CI logs. The Ansible inventory/vars source must provide both `palvelut_environment_file` and `palvelut_backup_environment_file`; Ansible installs the latter root-only at `/etc/palvelut/backup.env`.

## Monthly isolated restore drill

Run:

```bash
bash infra/scripts/restore-drill.sh
```

The drill restores the latest production-tagged snapshot into a temporary directory, verifies every media checksum, starts a fresh PostgreSQL 18 container with no published ports, restores the logical dump, and verifies that the Django migration table is readable. The temporary database container and restored files are removed on exit.

Record only:

- UTC start/end time;
- deployed image/config revision;
- snapshot age (to prove RPO <= 24h);
- `duration_seconds` from the script (must be <= 14400);
- pass/fail and follow-up issue reference.

Do not record backup credentials, personal data, row contents or media names.

## Fresh disposable-host rehearsal

Create a new Ubuntu 24.04+ disposable host and a private Ansible inventory/vars file for it. The vars source supplies the deploy public key, application environment and backup environment; none of those values belong in Git.

Run the entire provision-and-restore path with one command from the repository root:

```bash
REHEARSAL_INVENTORY=/secure/rehearsal-inventory.yml \
REHEARSAL_LIMIT=palvelut-rehearsal \
REHEARSAL_SSH_TARGET=root@203.0.113.20 \
bash infra/scripts/rehearsal-host-restore.sh
```

`REHEARSAL_LIMIT` and `REHEARSAL_SSH_TARGET` must identify the same newly-created disposable host. The wrapper first applies `infra/ansible/site.yml`, then streams the repository's exact `restore-drill.sh` to that host. Restore credentials come only from `/etc/palvelut/backup.env`, which Ansible creates with mode `0600`; they are not passed as command-line arguments.

Success requires both `rehearsal_status=ok` and the nested `restore_status=ok`. Destroy the disposable host after recording the non-sensitive evidence listed above. No package installation, secret-file creation or restore command outside this path is part of the accepted procedure.

## Recovery use

For an actual recovery, first restore and verify in isolation using the drill. Do not point the drill at the production database. After integrity is proven, provision a replacement environment from Ansible and use the same verified dump/media snapshot as the recovery source. DNS/upstream cutover is a separate operator decision and is not performed by these scripts.
