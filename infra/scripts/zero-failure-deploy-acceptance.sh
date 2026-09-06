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
SYNTHETIC_LOG="$WORKDIR/synthetic.log"
RELOAD_MARKER="$WORKDIR/reload.marker"
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
  nginx)
    exit 0
    ;;
  systemctl)
    if [[ "${2:-}" == "reload" && "${3:-}" == "nginx" ]]; then
      printf 'reload\n' >"${ACCEPTANCE_RELOAD_MARKER:?}"
      sleep 0.15
    fi
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
OLD_RELEASE=$(printf '1%.0s' {1..40})
NEW_RELEASE=$(printf '2%.0s' {1..40})
OLD_IMAGE="ghcr.io/strayforest/palvelut@sha256:${OLD_DIGEST}"
NEW_IMAGE="ghcr.io/strayforest/palvelut@sha256:${NEW_DIGEST}"

cat >"$NGINX_SITE" <<'EOF'
server {
    location / {
        proxy_pass http://127.0.0.1:8081;
    }
}
EOF
printf '%s\n' blue >"$STATE_DIR/active-slot"
cat >"$STATE_DIR/current-release.env" <<EOF
PALVELUT_IMAGE=${OLD_IMAGE}
PALVELUT_RELEASE=${OLD_RELEASE}
EOF

COMMON_ENV=(
  "PATH=$BIN_DIR:$PATH"
  "PALVELUT_DEPLOY_STATE_DIR=$STATE_DIR"
  "PALVELUT_NGINX_SITE=$NGINX_SITE"
  "PALVELUT_READINESS_ATTEMPTS=1"
  "PALVELUT_READINESS_DELAY=0"
  "ACCEPTANCE_DOCKER_LOG=$DOCKER_LOG"
  "ACCEPTANCE_RELOAD_MARKER=$RELOAD_MARKER"
  "COMPOSE_FILE=$ROOT/compose.production.yml"
)

synthetic_probe_loop() {
  local request upstream
  local failures=0
  local old_seen=0
  local new_seen=0
  : >"$SYNTHETIC_LOG"

  for request in $(seq 1 240); do
    upstream=$(sed -nE 's#.*proxy_pass http://127\.0\.0\.1:(808[12]);.*#\1#p' "$NGINX_SITE" | head -n1)
    case "$upstream" in
      8081) old_seen=1 ;;
      8082) new_seen=1 ;;
      *) failures=$((failures + 1)) ;;
    esac
    printf '%s %s\n' "$request" "${upstream:-invalid}" >>"$SYNTHETIC_LOG"
    sleep 0.002
  done

  printf '%s\n' "$failures" >"$WORKDIR/synthetic-failures"
  printf '%s\n' "$old_seen" >"$WORKDIR/old-seen"
  printf '%s\n' "$new_seen" >"$WORKDIR/new-seen"
}

synthetic_probe_loop &
monitor_pid=$!

env "${COMMON_ENV[@]}" \
  ACCEPTANCE_READINESS_MODE=pass \
  PALVELUT_IMAGE="$NEW_IMAGE" \
  PALVELUT_RELEASE="$NEW_RELEASE" \
  bash "$DEPLOY_SCRIPT" deploy >/dev/null
wait "$monitor_pid"

test -f "$RELOAD_MARKER"
grep -q '^green$' "$STATE_DIR/active-slot"
grep -q 'proxy_pass http://127.0.0.1:8082;' "$NGINX_SITE"
grep -q '^0$' "$WORKDIR/synthetic-failures"
grep -q '^1$' "$WORKDIR/old-seen"
grep -q '^1$' "$WORKDIR/new-seen"

cp "$STATE_DIR/current-release.env" "$WORKDIR/state-before-unsafe-rollback.env"
: >"$DOCKER_LOG"
set +e
rollback_output=$(env "${COMMON_ENV[@]}" \
  ACCEPTANCE_READINESS_MODE=fail \
  bash "$DEPLOY_SCRIPT" rollback 2>&1)
rollback_status=$?
set -e

if [[ $rollback_status -eq 0 ]]; then
  echo "unsafe rollback unexpectedly switched traffic" >&2
  exit 1
fi
grep -q 'operator action required' <<<"$rollback_output"
grep -q 'current database schema' <<<"$rollback_output"
grep -q '^green$' "$STATE_DIR/active-slot"
grep -q 'proxy_pass http://127.0.0.1:8082;' "$NGINX_SITE"
cmp -s "$WORKDIR/state-before-unsafe-rollback.env" "$STATE_DIR/current-release.env"
if grep -q 'manage.py migrate' "$DOCKER_LOG"; then
  echo "unsafe rollback unexpectedly attempted a database migration" >&2
  exit 1
fi

synthetic_requests=$(wc -l <"$SYNTHETIC_LOG" | tr -d ' ')
printf '%s\n' \
  "synthetic_requests=${synthetic_requests}" \
  'synthetic_failures=0' \
  'upstream_switch_observed=pass' \
  'unsafe_database_rollback=operator_action_required' \
  'database_reverse_migration=not_attempted'
