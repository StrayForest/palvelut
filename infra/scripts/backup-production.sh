#!/usr/bin/env bash
set -euo pipefail

: "${RESTIC_REPOSITORY:?set encrypted off-site RESTIC_REPOSITORY}"
: "${RESTIC_PASSWORD_FILE:?set RESTIC_PASSWORD_FILE outside Git}"
: "${RCLONE_CONFIG_SOURCE_TYPE:?configure rclone source remote outside Git}"
: "${S3_BUCKET_NAME:?set the production media bucket}"

for command in docker restic rclone sha256sum; do
  command -v "$command" >/dev/null || { echo "$command is required" >&2; exit 1; }
done

stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/database" "$stage/media"

compose=(bash infra/scripts/production-compose.sh)
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Produce a consistent logical database backup from the running production database.
"${compose[@]}" exec -T postgres sh -ec \
  'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner --no-acl' \
  > "$stage/database/palvelut.dump"

# Copy media originals from the primary object store into the encrypted backup snapshot.
# Credentials are supplied through RCLONE_CONFIG_SOURCE_* environment variables.
rclone sync --checksum --metadata "source:${S3_BUCKET_NAME}" "$stage/media" --quiet

(
  cd "$stage"
  find media -type f -print0 | sort -z | xargs -0 -r sha256sum > media.sha256
)

if ! restic snapshots --json >/dev/null 2>&1; then
  restic init >/dev/null
fi

restic backup "$stage" \
  --tag production \
  --tag nightly \
  --host palvelut-production \
  --quiet
restic check --read-data-subset=5% >/dev/null
restic forget --keep-daily 14 --keep-weekly 8 --prune --quiet

finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'backup_status=ok started_at=%s finished_at=%s\n' "$started_at" "$finished_at"
