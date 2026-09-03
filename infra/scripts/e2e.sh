#!/usr/bin/env bash
set -euo pipefail

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-palvelut}"
COMPOSE=(docker compose --project-name "$COMPOSE_PROJECT_NAME")

cleanup() {
  "${COMPOSE[@]}" down -v --remove-orphans
}
trap cleanup EXIT

rm -rf playwright-report test-results
mkdir -p playwright-report test-results

"${COMPOSE[@]}" build web e2e
"${COMPOSE[@]}" up -d postgres valkey web nginx

ready=0
for _ in $(seq 1 30); do
  status="$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/ || true)"
  case "$status" in
    2??|3??|404)
      ready=1
      break
      ;;
  esac
  sleep 2
done

if test "$ready" != "1"; then
  "${COMPOSE[@]}" logs --no-color web nginx
  exit 1
fi

"${COMPOSE[@]}" run --rm e2e
