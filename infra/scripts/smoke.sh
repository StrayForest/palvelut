#!/usr/bin/env bash
set -euo pipefail

compose=(docker compose --project-name palvelut)
cleanup() {
  "${compose[@]}" down -v --remove-orphans
}
trap cleanup EXIT

"${compose[@]}" config >/tmp/palvelut-compose.yml
"${compose[@]}" build web
"${compose[@]}" up -d postgres valkey mailpit minio

ready=0
for _ in $(seq 1 60); do
  if "${compose[@]}" exec -T postgres pg_isready -U palvelut -d palvelut >/dev/null \
    && test "$("${compose[@]}" exec -T valkey valkey-cli ping | tr -d '\r')" = "PONG" \
    && curl -fsS http://127.0.0.1:8025/ >/dev/null \
    && curl -fsS http://127.0.0.1:9000/minio/health/live >/dev/null; then
    ready=1
    break
  fi
  sleep 2
done
test "$ready" = "1"

"${compose[@]}" run --rm web python manage.py migrate --noinput
"${compose[@]}" run --rm web python manage.py check
"${compose[@]}" run --rm web gunicorn --check-config -k uvicorn_worker.UvicornWorker --bind 0.0.0.0:8000 --workers 2 palvelut.asgi:application
"${compose[@]}" run --rm web python -c "from django.core.cache import cache; cache.set('p0-smoke','ok',30); assert cache.get('p0-smoke') == 'ok'"
"${compose[@]}" run --rm web python -c "from django.core.mail import send_mail; assert send_mail('P0 smoke probe','ok',None,['dev@local.invalid']) == 1"
curl -fsS http://127.0.0.1:8025/api/v1/messages | grep -q "P0 smoke probe"

"${compose[@]}" up -d web
web_id="$("${compose[@]}" ps -q web)"
web_ready=0
for _ in $(seq 1 30); do
  if test "$(docker inspect -f '{{.State.Running}}' "$web_id" 2>/dev/null || true)" != "true"; then
    "${compose[@]}" logs --no-color web
    exit 1
  fi
  if test "$(docker inspect -f '{{.State.Health.Status}}' "$web_id" 2>/dev/null || true)" = "healthy"; then
    web_ready=1
    break
  fi
  sleep 2
done
if test "$web_ready" != "1"; then
  "${compose[@]}" logs --no-color web
  exit 1
fi

"${compose[@]}" up -d worker
sleep 3
if ! "${compose[@]}" ps worker --status running --services | grep -x worker; then
  "${compose[@]}" logs --no-color worker
  exit 1
fi

"${compose[@]}" up -d nginx
nginx_ready=0
for _ in $(seq 1 30); do
  status="$(curl -sS -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/ || true)"
  case "$status" in
    2??|3??|404)
      nginx_ready=1
      break
      ;;
  esac
  sleep 2
done
if test "$nginx_ready" != "1"; then
  "${compose[@]}" logs --no-color web nginx
  exit 1
fi

live_headers="$(mktemp)"
live_body="$(mktemp)"
ready_headers="$(mktemp)"
ready_body="$(mktemp)"
curl -fsS -D "$live_headers" -o "$live_body" http://127.0.0.1:8000/palvelut/health/live
curl -fsS -D "$ready_headers" -o "$ready_body" http://127.0.0.1:8000/palvelut/health/ready
grep -q '"status": "ok"' "$live_body"
grep -q '"status": "ok"' "$ready_body"
grep -qi '^Cache-Control: no-store' "$live_headers"
grep -qi '^Cache-Control: no-store' "$ready_headers"
rm -f "$live_headers" "$live_body" "$ready_headers" "$ready_body"

"${compose[@]}" exec -T postgres psql -U palvelut -d palvelut -Atc "show server_version;" | grep -E '^18\.'
"${compose[@]}" exec -T valkey valkey-cli INFO server | tr -d '\r' | grep -E '^valkey_version:8\.'
"${compose[@]}" ps
