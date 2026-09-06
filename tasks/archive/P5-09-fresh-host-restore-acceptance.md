# P5-09 — Fresh-host restore acceptance

Status: completed.

## Scope

Accept that a fresh disposable rehearsal host can be provisioned by Ansible and restored from encrypted off-site backups without undocumented manual steps.

## Implemented

- Added `infra/scripts/rehearsal-host-restore.sh` as the single provision-and-restore entry point.
- The wrapper requires an explicit private inventory, host limit and SSH target, applies `infra/ansible/site.yml`, then streams the exact repository `restore-drill.sh` to the same disposable host.
- Ansible now requires `palvelut_backup_environment_file` and installs it root-only at `/etc/palvelut/backup.env` with mode `0600` and `no_log: true`.
- Restore credentials are sourced on the host and are never passed through command-line arguments.
- `docs/runbooks/database-restore.md` documents the complete fresh-host rehearsal command and evidence contract.
- Added `tests/test_p5_fresh_host_rehearsal_contract.py` to prevent the Ansible/restore path from drifting apart.

## Verification

- Repository contract test covers the exact Ansible playbook, required rehearsal coordinates, root-only backup environment and restore-drill invocation.
- Ansible syntax/lint remains covered by `.github/workflows/p5-ansible.yml` on this change because both `infra/ansible/**` and `tasks/archive/P5-*.md` trigger that gate.
- Full Compose-stack CI is required before merge.

A live destructive rehearsal still requires a real disposable Ubuntu host and real off-site backup credentials. Those values are intentionally external to Git; the accepted repository contract contains every operational step once those external coordinates exist.
