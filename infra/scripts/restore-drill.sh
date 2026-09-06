#!/usr/bin/env bash
set -euo pipefail

: "${RESTIC_REPOSITORY:?set RESTIC_REPOSITORY}"
: "${RESTIC_PASSWORD_FILE:?set RESTIC_PASSWORD_FILE outside Git}"

for command in docker restic sha256sum python3; do
  command -v "$command" >/dev/null || { echo "$command is required" >&2; exit 1; }
done

work="$(mktemp -d)"
container="palvelut-restore-drill-${RANDOM}-$$"
trap 'docker rm -f "$container" >/dev/null 2>&1 || true; rm -rf "$work"' EXIT

started_epoch="$(date +%s)"
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
snapshot_time="$(
  restic snapshots --latest 1 --tag production --host palvelut-production --json \
    | python3 -c 'import datetime, json, sys; data=json.load(sys.stdin); assert len(data)==1, "expected one latest snapshot"; value=data[0]["time"]; dt=datetime.datetime.fromisoformat(value.replace("Z", "+00:00")); print(int(dt.timestamp()))'
)"
snapshot_age_seconds="$((started_epoch - snapshot_time))"
(( snapshot_age_seconds >= 0 )) || { echo "latest snapshot timestamp is in the future" >&2; exit 1; }
(( snapshot_age_seconds <= 86400 )) || { echo "latest production snapshot exceeds 24h RPO target" >&2; exit 1; }

restic restore latest --target "$work" --tag production --host palvelut-production --quiet

snapshot_root="$work"
if [[ -d "$work/tmp" ]]; then
  snapshot_root="$(find "$work" -type f -name palvelut.dump -printf '%h\n' | head -n1 | xargs dirname)"
fi

dump_path="$(find "$work" -type f -path '*/database/palvelut.dump' -print -quit)"
[[ -n "$dump_path" ]] || { echo "database dump missing from snapshot" >&2; exit 1; }
root="$(dirname "$(dirname "$dump_path")")"

if [[ -f "$root/media.sha256" ]]; then
  (cd "$root" && sha256sum -c media.sha256 >/dev/null)
fi

# Restore into an isolated, non-published PostgreSQL container. No production
# database endpoint is reachable from this container.
docker run -d --rm --name "$container" \
  -e POSTGRES_DB=palvelut_restore \
  -e POSTGRES_USER=palvelut_restore \
  -e POSTGRES_PASSWORD=restore-drill-only \
  postgres:18-alpine@sha256:d3e1620b530c944afa6e887d22eb899824da68e19c52024bf98f5220c88a65b2 \
  >/dev/null

for _ in $(seq 1 60); do
  if docker exec "$container" pg_isready -U palvelut_restore -d palvelut_restore >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
docker exec "$container" pg_isready -U palvelut_restore -d palvelut_restore >/dev/null

docker cp "$dump_path" "$container:/tmp/palvelut.dump"
docker exec "$container" pg_restore \
  -U palvelut_restore -d palvelut_restore --no-owner --no-acl /tmp/palvelut.dump

docker exec "$container" psql -U palvelut_restore -d palvelut_restore \
  -v ON_ERROR_STOP=1 -Atqc "SELECT count(*) >= 1 FROM django_migrations;" \
  | grep -qx t

finished_epoch="$(date +%s)"
finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
duration="$((finished_epoch - started_epoch))"
printf 'restore_status=ok command=infra/scripts/restore-drill.sh started_at=%s finished_at=%s snapshot_age_seconds=%s rpo_target_seconds=86400 duration_seconds=%s rto_target_seconds=14400\n' \
  "$started_at" "$finished_at" "$snapshot_age_seconds" "$duration"
(( duration <= 14400 )) || { echo "restore exceeded 4h RTO target" >&2; exit 1; }
