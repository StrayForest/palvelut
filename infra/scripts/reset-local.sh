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

compose=(docker compose --project-name palvelut)
"${compose[@]}" down -v --remove-orphans
"${compose[@]}" build web
