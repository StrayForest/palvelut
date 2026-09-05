#!/usr/bin/env bash
set -euo pipefail

: "${PALVELUT_IMAGE:?PALVELUT_IMAGE is required}"
env_file="${PALVELUT_ENV_FILE:-/etc/palvelut/production.env}"

if [[ ! "$PALVELUT_IMAGE" =~ ^ghcr\.io/strayforest/palvelut@sha256:[0-9a-f]{64}$ ]]; then
  echo "PALVELUT_IMAGE must be the immutable ghcr.io/strayforest/palvelut@sha256:<digest> reference" >&2
  exit 2
fi
if [[ ! -r "$env_file" ]]; then
  echo "Production env file is not readable: $env_file" >&2
  exit 2
fi

exec docker compose \
  --project-name palvelut-production \
  --env-file "$env_file" \
  -f compose.production.yml \
  "$@"
