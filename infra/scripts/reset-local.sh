#!/usr/bin/env bash
set -euo pipefail

case "${PALVELUT_ENVIRONMENT:-local}" in
  prod|production|stage|staging)
    echo "Refusing to reset production-like environment: ${PALVELUT_ENVIRONMENT}" >&2
    exit 2
    ;;
esac

if [[ "${DJANGO_DEBUG:-1}" != "1" ]]; then
  echo "Refusing to reset while DJANGO_DEBUG is not 1" >&2
  exit 2
fi

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-palvelut}"
case "$COMPOSE_PROJECT_NAME" in
  ""|prod|production|stage|staging|palvelut-prod|palvelut-production|palvelut-stage|palvelut-staging)
    echo "Refusing to reset production-like Compose project: ${COMPOSE_PROJECT_NAME:-<empty>}" >&2
    exit 2
    ;;
esac

compose=(docker compose --project-name "$COMPOSE_PROJECT_NAME")
"${compose[@]}" down -v --remove-orphans
"${compose[@]}" build web
