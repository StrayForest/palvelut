#!/usr/bin/env bash
set -euo pipefail

ACTION=${1:-deploy}
COMPOSE_FILE=${COMPOSE_FILE:-compose.production.yml}
STATE_DIR=${PALVELUT_DEPLOY_STATE_DIR:-/opt/palvelut/deploy-state}
NGINX_SITE=${PALVELUT_NGINX_SITE:-/etc/nginx/sites-available/palvelut.conf}
READINESS_ATTEMPTS=${PALVELUT_READINESS_ATTEMPTS:-30}
READINESS_DELAY=${PALVELUT_READINESS_DELAY:-2}

mkdir -p "$STATE_DIR"

require_release() {
  : "${PALVELUT_IMAGE:?set PALVELUT_IMAGE to an immutable ghcr.io image digest}"
  : "${PALVELUT_RELEASE:?set PALVELUT_RELEASE to the tested commit SHA}"
  [[ "$PALVELUT_IMAGE" =~ ^ghcr\.io/strayforest/palvelut@sha256:[0-9a-f]{64}$ ]] || {
    echo "PALVELUT_IMAGE must be an exact ghcr.io/strayforest/palvelut@sha256:<digest> reference" >&2
    exit 2
  }
  [[ "$PALVELUT_RELEASE" =~ ^[0-9a-f]{40}$ ]] || {
    echo "PALVELUT_RELEASE must be a full 40-character commit SHA" >&2
    exit 2
  }
}

slot_port() {
  case "$1" in
    blue) echo 8081 ;;
    green) echo 8082 ;;
    *) echo "unknown slot: $1" >&2; exit 2 ;;
  esac
}

inactive_slot() {
  if [[ "$1" == blue ]]; then echo green; else echo blue; fi
}

current_slot() {
  if [[ -f "$STATE_DIR/active-slot" ]]; then
    cat "$STATE_DIR/active-slot"
  else
    # Ansible bootstraps nginx to blue. Treat green as active so the first deploy
    # starts and validates blue before recording state.
    echo green
  fi
}

wait_ready() {
  local port=$1
  local attempt
  for ((attempt=1; attempt<=READINESS_ATTEMPTS; attempt++)); do
    if curl --fail --silent --show-error --max-time 3 \
      "http://127.0.0.1:${port}/palvelut/health/ready" >/dev/null; then
      return 0
    fi
    sleep "$READINESS_DELAY"
  done
  echo "inactive web slot failed readiness on port ${port}" >&2
  return 1
}

switch_nginx() {
  local port=$1
  local candidate backup
  candidate=$(mktemp)
  backup=$(mktemp)
  trap 'rm -f "$candidate" "$backup"' RETURN

  grep -Eq 'proxy_pass http://127\.0\.0\.1:808[12];' "$NGINX_SITE" || {
    echo "nginx site does not contain a managed blue/green upstream" >&2
    return 1
  }
  cat "$NGINX_SITE" >"$backup"
  sed -E "s#proxy_pass http://127\.0\.0\.1:808[12];#proxy_pass http://127.0.0.1:${port};#" \
    "$NGINX_SITE" >"$candidate"

  sudo install -m 0644 "$candidate" "$NGINX_SITE"
  if ! sudo nginx -t -c /etc/nginx/nginx.conf >/dev/null; then
    sudo install -m 0644 "$backup" "$NGINX_SITE"
    echo "new nginx configuration is invalid; restored previous upstream" >&2
    return 1
  fi
  sudo systemctl reload nginx
}

write_release_state() {
  local old_slot=$1
  if [[ -f "$STATE_DIR/current-release.env" ]]; then
    cp "$STATE_DIR/current-release.env" "$STATE_DIR/previous-release.env"
    printf '%s\n' "$old_slot" >"$STATE_DIR/previous-slot"
  fi
  {
    printf 'PALVELUT_IMAGE=%q\n' "$PALVELUT_IMAGE"
    printf 'PALVELUT_RELEASE=%q\n' "$PALVELUT_RELEASE"
  } >"$STATE_DIR/current-release.env"
}

deploy_release() {
  local skip_migrations=${1:-0}
  local active inactive port
  active=$(current_slot)
  inactive=$(inactive_slot "$active")
  port=$(slot_port "$inactive")

  require_release
  echo "Preparing ${PALVELUT_RELEASE} in ${inactive} using ${PALVELUT_IMAGE}"
  docker compose -f "$COMPOSE_FILE" pull "web_${inactive}" "worker_${inactive}" scheduler

  if [[ "$skip_migrations" != 1 ]]; then
    # Production migrations must follow expand/backfill/contract discipline. We
    # never reverse migrations during rollback.
    docker compose -f "$COMPOSE_FILE" run --rm "web_${inactive}" \
      python manage.py migrate --noinput
  fi

  docker compose -f "$COMPOSE_FILE" up -d --no-deps "web_${inactive}"
  wait_ready "$port"

  # The upstream change is the only request-path switch; nginx reload is graceful.
  switch_nginx "$port"

  # Replace background consumers only after web traffic is safely on the new slot.
  docker compose -f "$COMPOSE_FILE" up -d --no-deps "worker_${inactive}"
  if docker compose -f "$COMPOSE_FILE" ps --status running --services | grep -qx "worker_${active}"; then
    # Celery handles SIGTERM as a warm shutdown; the compose grace period bounds drain.
    docker compose -f "$COMPOSE_FILE" stop -t 60 "worker_${active}"
  fi

  # There is deliberately one un-slotted scheduler. Recreate it only after the
  # worker cutover so two beat instances are never started by this workflow.
  docker compose -f "$COMPOSE_FILE" up -d --no-deps --force-recreate scheduler

  write_release_state "$active"
  printf '%s\n' "$inactive" >"$STATE_DIR/active-slot"
  echo "Deployment complete: ${inactive} is active; ${active} web is retained for rollback."
}

case "$ACTION" in
  deploy)
    deploy_release 0
    ;;
  rollback)
    [[ -f "$STATE_DIR/previous-release.env" && -f "$STATE_DIR/previous-slot" ]] || {
      echo "no previous release is recorded; rollback cannot proceed" >&2
      exit 2
    }
    # shellcheck disable=SC1090
    source "$STATE_DIR/previous-release.env"
    export PALVELUT_IMAGE PALVELUT_RELEASE
    echo "App-only rollback to ${PALVELUT_RELEASE}; database migrations will not be reversed."
    deploy_release 1
    ;;
  *)
    echo "usage: $0 [deploy|rollback]" >&2
    exit 2
    ;;
esac
