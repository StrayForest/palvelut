#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
DEPLOY_SCRIPT="$ROOT/infra/scripts/deploy-production.sh"
WORKDIR=$(mktemp -d)
trap 'rm -rf "$WORKDIR"' EXIT

BIN_DIR="$WORKDIR/bin"
STATE_DIR="$WORKDIR/state"
NGINX_SITE="$WORKDIR/palvelut.conf"
DOCKER_LOG="$WORKDIR/docker.log"
mkdir -p "$BIN_DIR" "$STATE_DIR"

cat >"$BIN_DIR/docker" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%q ' "$@" >>"${ACCEPTANCE_DOCKER_LOG:?}"
printf '\n' >>"${ACCEPTANCE_DOCKER_LOG:?}"
exit 0
EOF

cat >"$BIN_DIR/curl" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "${ACCEPTANCE_READINESS_MODE:-pass}" == "fail" ]]; then
  exit 22
fi
exit 0
EOF

cat >"$BIN_DIR/sudo" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
case "${1:-}" in
  install)
    shift
    exec /usr/bin/install "$@"
    ;;
  nginx|systemctl)
    exit 0
    ;;
  *)
    echo "unexpected sudo command: $*" >&2
    exit 2
    ;;
esac
EOF
chmod +x "$BIN_DIR/docker" "$BIN_DIR/curl" "$BIN_DIR/sudo"

OLD_DIGEST=$(printf 'a%.0s' {1..64})
NEW_DIGEST=$(printf 'b%.0s' {1..64})
NEXT_DIGEST=$(printf 'c%.0s' {1..64})
OLD_RELEASE=$(printf '1%.0s' {1..40})
NEW_RELEASE=$(printf '2%.0s' {1..40})
NEXT_RELEASE=$(printf '3%.0s' {1..40})
OLD_IMAGE="ghcr.io/strayforest/palvelut@sha256:${OLD_DIGEST}"
NEW_IMAGE="ghcr.io/strayforest/palvelut@sha256:${NEW_DIGEST}"
NEXT_IMAGE="ghcr.io/strayforest/palvelut@sha256:${NEXT_DIGEST}"

cat >"$NGINX_SITE" <<'EOF'
server {
    location / {
        proxy_pass http://127.0.0.1:8082;
    }
}
EOF
printf '%s\n' green >"$STATE_DIR/active-slot"
cat >"$STATE_DIR/current-release.env" <<EOF
PALVELUT_IMAGE=${NEW_IMAGE}
PALVELUT_RELEASE=${NEW_RELEASE}
EOF
cat >"$STATE_DIR/previous-release.env" <<EOF
PALVELUT_IMAGE=${OLD_IMAGE}
PALVELUT_RELEASE=${OLD_RELEASE}
EOF
printf '%s\n' blue >"$STATE_DIR/previous-slot"

COMMON_ENV=(
  "PATH=$BIN_DIR:$PATH"
  "PALVELUT_DEPLOY_STATE_DIR=$STATE_DIR"
  "PALVELUT_NGINX_SITE=$NGINX_SITE"
  "PALVELUT_READINESS_ATTEMPTS=1"
  "PALVELUT_READINESS_DELAY=0"
  "ACCEPTANCE_DOCKER_LOG=$DOCKER_LOG"
  "COMPOSE_FILE=$ROOT/compose.production.yml"
)

rollback_output=$(env "${COMMON_ENV[@]}" ACCEPTANCE_READINESS_MODE=pass \
  bash "$DEPLOY_SCRIPT" rollback)

grep -q '^blue$' "$STATE_DIR/active-slot"
grep -q 'proxy_pass http://127.0.0.1:8081;' "$NGINX_SITE"
grep -Fq "PALVELUT_IMAGE=${OLD_IMAGE}" "$STATE_DIR/current-release.env"
grep -Fq "PALVELUT_RELEASE=${OLD_RELEASE}" "$STATE_DIR/current-release.env"
if grep -q 'manage.py migrate' "$DOCKER_LOG"; then
  echo "rollback unexpectedly attempted a database migration" >&2
  exit 1
fi
grep -q 'App-only rollback' <<<"$rollback_output"

cp "$STATE_DIR/current-release.env" "$WORKDIR/state-before-incident.env"
: >"$DOCKER_LOG"
set +e
incident_output=$(env "${COMMON_ENV[@]}" \
  ACCEPTANCE_READINESS_MODE=fail \
  PALVELUT_IMAGE="$NEXT_IMAGE" \
  PALVELUT_RELEASE="$NEXT_RELEASE" \
  bash "$DEPLOY_SCRIPT" deploy 2>&1)
incident_status=$?
set -e

if [[ $incident_status -eq 0 ]]; then
  echo "simulated readiness incident unexpectedly completed deployment" >&2
  exit 1
fi
grep -q 'inactive web slot failed readiness' <<<"$incident_output"
grep -q '^blue$' "$STATE_DIR/active-slot"
grep -q 'proxy_pass http://127.0.0.1:8081;' "$NGINX_SITE"
cmp -s "$WORKDIR/state-before-incident.env" "$STATE_DIR/current-release.env"
if grep -q 'systemctl reload nginx' "$DOCKER_LOG"; then
  echo "incident unexpectedly switched nginx" >&2
  exit 1
fi

printf '%s\n' \
  'rollback_acceptance=pass' \
  'simulated_incident=readiness_failure' \
  'incident_containment=pass' \
  'database_reverse_migration=not_attempted'
