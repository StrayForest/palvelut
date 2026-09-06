#!/usr/bin/env bash
set -euo pipefail

: "${REHEARSAL_INVENTORY:?set REHEARSAL_INVENTORY to the disposable-host inventory}"
: "${REHEARSAL_LIMIT:?set REHEARSAL_LIMIT to the disposable host name/group}"
: "${REHEARSAL_SSH_TARGET:?set REHEARSAL_SSH_TARGET to user@host for the same disposable host}"

for command in ansible-playbook ssh; do
  command -v "$command" >/dev/null || { echo "$command is required" >&2; exit 1; }
done

started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

ANSIBLE_CONFIG="infra/ansible/ansible.cfg" \
  ansible-playbook \
  -i "$REHEARSAL_INVENTORY" \
  --limit "$REHEARSAL_LIMIT" \
  infra/ansible/site.yml

# The restore script is streamed from this exact checkout. Backup credentials are
# provisioned by Ansible at /etc/palvelut/backup.env and never cross the command line.
ssh -o BatchMode=yes "$REHEARSAL_SSH_TARGET" \
  "sudo bash -c 'set -a; source /etc/palvelut/backup.env; set +a; bash -s'" \
  < infra/scripts/restore-drill.sh

finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'rehearsal_status=ok started_at=%s finished_at=%s host=%s\n' \
  "$started_at" "$finished_at" "$REHEARSAL_LIMIT"
