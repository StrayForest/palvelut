#!/usr/bin/env bash
set -euo pipefail

: "${CODESPACE_NAME:?CODESPACE_NAME is required in GitHub Codespaces}"
export GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"

compose=(
  docker compose
  --project-name palvelut
  -f compose.yml
  -f .devcontainer/compose.codespaces.yml
)

"${compose[@]}" up -d --build postgres valkey mailpit minio
"${compose[@]}" run --rm web python manage.py migrate --noinput
"${compose[@]}" up -d --build web worker nginx
"${compose[@]}" run --rm web python manage.py seed_demo

wait_for_url() {
  local url="$1"
  local attempts="${2:-60}"
  local delay="${3:-1}"

  for _ in $(seq 1 "$attempts"); do
    if curl --fail --silent --show-error --max-time 2 "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$delay"
  done

  printf 'Timed out waiting for %s\n' "$url" >&2
  "${compose[@]}" ps >&2
  return 1
}

wait_for_url "http://127.0.0.1:8000/palvelut/health/live"
wait_for_url "http://127.0.0.1:8025/"

# Printing localhost URLs is intentional: GitHub Codespaces detects these patterns,
# registers the forwarded ports and turns them into authenticated browser links.
printf '\nPalvelut preview: http://localhost:8000/palvelut/ru/\n'
printf 'Mailpit:          http://localhost:8025/\n'
printf '\nIf the browser link is not opened automatically, use the Codespaces PORTS tab and open port 8000.\n\n'
