#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: purge-cloudflare-cache.sh [--dry-run] /palvelut/path/ [...]

Purges only exact https://finrix.fi/palvelut/... URLs. The script intentionally
has no purge-everything mode.

Required environment for a real purge:
  CLOUDFLARE_ZONE_ID
  CLOUDFLARE_API_TOKEN
EOF
}

dry_run=0
if [[ "${1:-}" == "--dry-run" ]]; then
  dry_run=1
  shift
fi

if (($# == 0)); then
  usage >&2
  exit 2
fi
if (($# > 30)); then
  echo "Refusing more than 30 exact URLs in one purge request" >&2
  exit 2
fi

urls=()
for path in "$@"; do
  if [[ "$path" != /palvelut/* ]]; then
    echo "Refusing path outside /palvelut/: $path" >&2
    exit 2
  fi
  if [[ "$path" == *$'\n'* || "$path" == *$'\r'* ]]; then
    echo "Refusing path containing a newline" >&2
    exit 2
  fi
  urls+=("https://finrix.fi${path}")
done

payload="$({ printf '%s\n' "${urls[@]}"; } | python3 -c '
import json, sys
urls = [line.rstrip("\n") for line in sys.stdin if line.rstrip("\n")]
print(json.dumps({"files": urls}, separators=(",", ":")))
')"

if ((dry_run)); then
  printf '%s\n' "$payload"
  exit 0
fi

: "${CLOUDFLARE_ZONE_ID:?CLOUDFLARE_ZONE_ID is required}"
: "${CLOUDFLARE_API_TOKEN:?CLOUDFLARE_API_TOKEN is required}"

response_file="$(mktemp)"
trap 'rm -f "$response_file"' EXIT

http_status="$({
  curl --silent --show-error \
    --output "$response_file" \
    --write-out '%{http_code}' \
    --request POST \
    --url "https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE_ID}/purge_cache" \
    --header "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
    --header 'Content-Type: application/json' \
    --data "$payload"
})"

if [[ "$http_status" != "200" ]]; then
  echo "Cloudflare purge failed with HTTP ${http_status}" >&2
  cat "$response_file" >&2
  exit 1
fi

python3 - "$response_file" <<'PY'
import json
import sys
from pathlib import Path

result = json.loads(Path(sys.argv[1]).read_text())
if result.get("success") is not True:
    raise SystemExit("Cloudflare returned success=false")
print("Cloudflare exact-URL purge accepted")
PY
