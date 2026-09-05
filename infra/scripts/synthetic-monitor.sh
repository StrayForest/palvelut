#!/usr/bin/env bash
set -euo pipefail

: "${SYNTHETIC_BASE_URL:?Set SYNTHETIC_BASE_URL, for example https://example.com/palvelut}"
: "${SYNTHETIC_PROFILE_SLUG:?Set SYNTHETIC_PROFILE_SLUG to a published synthetic provider slug}"
: "${SYNTHETIC_PROVIDER_ID:?Set SYNTHETIC_PROVIDER_ID to the published synthetic provider UUID}"

locale="${SYNTHETIC_LOCALE:-en}"
channel="${SYNTHETIC_CONTACT_CHANNEL:-website}"
timeout="${SYNTHETIC_TIMEOUT_SECONDS:-10}"
base="${SYNTHETIC_BASE_URL%/}"
user_agent="Finrix-Palvelut-Synthetic/1.0"

curl_common=(
  --silent
  --show-error
  --fail-with-body
  --connect-timeout "${timeout}"
  --max-time "${timeout}"
  --header "X-Palvelut-Synthetic: 1"
  --user-agent "${user_agent}"
)

check_html() {
  local name="$1"
  local url="$2"
  local expected="$3"
  local body
  body="$(curl "${curl_common[@]}" --location --proto '=https' --tlsv1.2 "${url}")"
  if [[ "${body}" != *"${expected}"* ]]; then
    printf 'synthetic %s failed: expected marker not found\n' "${name}" >&2
    return 1
  fi
  printf 'synthetic %s ok\n' "${name}"
}

check_contact_redirect() {
  local url="$1"
  local headers status location
  headers="$(curl "${curl_common[@]}" --head --proto '=https' --tlsv1.2 "${url}")"
  status="$(printf '%s\n' "${headers}" | awk 'toupper($1) ~ /^HTTP\// {code=$2} END {print code}')"
  location="$(printf '%s\n' "${headers}" | awk 'BEGIN{IGNORECASE=1} /^Location:/ {sub(/^[^:]+:[[:space:]]*/, ""); sub(/\r$/, ""); print; exit}')"
  if [[ "${status}" != "302" ]] || [[ -z "${location}" ]]; then
    printf 'synthetic contact failed: expected 302 with Location\n' >&2
    return 1
  fi
  case "${location}" in
    https://*|http://*|tel:*|mailto:*) ;;
    *)
      printf 'synthetic contact failed: unexpected redirect scheme\n' >&2
      return 1
      ;;
  esac
  printf 'synthetic contact ok\n'
}

check_html "home" "${base}/${locale}/" "<main"
check_html "search" "${base}/${locale}/search/?q=" "<main"
check_html "profile" "${base}/${locale}/professionals/${SYNTHETIC_PROFILE_SLUG}/" "<main"
check_contact_redirect "${base}/${locale}/go/${SYNTHETIC_PROVIDER_ID}/${channel}/"

printf 'synthetic monitoring pass\n'
