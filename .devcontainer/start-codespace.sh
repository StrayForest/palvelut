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

preview_url="https://${CODESPACE_NAME}-8000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/palvelut/ru/"
mailpit_url="https://${CODESPACE_NAME}-8025.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}/"

printf '\nPalvelut preview: %s\n' "$preview_url"
printf 'Mailpit:          %s\n\n' "$mailpit_url"
