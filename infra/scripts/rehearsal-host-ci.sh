#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
state_root="${RUNNER_TEMP:-/tmp}/palvelut-rehearsal-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}"
host="palvelut-rehearsal-${GITHUB_RUN_ID:-local}-${GITHUB_RUN_ATTEMPT:-1}"
source_db="palvelut-rehearsal-source"
postgres_image="postgres:18-alpine@sha256:d3e1620b530c944afa6e887d22eb899824da68e19c52024bf98f5220c88a65b2"

bootstrap() {
  rm -rf "$state_root"
  mkdir -p "$state_root"
  docker rm -f "$host" >/dev/null 2>&1 || true

  cat >"$state_root/Dockerfile" <<'EOF'
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends systemd systemd-sysv python3 openssh-server sudo \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /run/sshd
STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]
EOF

  docker build --quiet -t "${host}:fixture" "$state_root" >/dev/null
  docker run --privileged --cgroupns=host -d --name "$host" \
    -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
    "${host}:fixture" >/dev/null

  for _ in $(seq 1 60); do
    state="$(docker exec "$host" systemctl is-system-running 2>/dev/null || true)"
    if [[ "$state" == "running" || "$state" == "degraded" ]]; then
      break
    fi
    sleep 1
  done

  # Cloud images initialize these during first boot. The minimal CI image must
  # do the same before the production SSH policy is syntax-validated.
  docker exec "$host" ssh-keygen -A >/dev/null

  # Nested Docker is a CI-only property of this disposable host. vfs avoids
  # depending on the outer runner's overlay filesystem while leaving the
  # production Ansible playbook unchanged.
  docker exec "$host" sh -c 'mkdir -p /etc/docker && printf "%s\n" "{\"storage-driver\":\"vfs\"}" > /etc/docker/daemon.json'

  ssh-keygen -q -t ed25519 -N '' -f "$state_root/id_ed25519"
  pubkey="$(cat "$state_root/id_ed25519.pub")"
  cat >"$state_root/inventory.yml" <<EOF
all:
  hosts:
    rehearsal:
      ansible_host: ${host}
      ansible_connection: community.docker.docker
EOF
  cat >"$state_root/vars.yml" <<EOF
deploy_authorized_key: ${pubkey}
palvelut_environment_file: |
  PALVELUT_ENV=rehearsal
  DJANGO_SETTINGS_MODULE=palvelut.settings
EOF
}

provision() {
  export ANSIBLE_CONFIG="${repo_root}/infra/ansible/ansible.cfg"
  ansible-playbook -i "$state_root/inventory.yml" "$repo_root/infra/ansible/site.yml" -e "@$state_root/vars.yml"
}

converge() {
  export ANSIBLE_CONFIG="${repo_root}/infra/ansible/ansible.cfg"
  second_apply="$state_root/second-apply.log"
  ansible-playbook -i "$state_root/inventory.yml" "$repo_root/infra/ansible/site.yml" -e "@$state_root/vars.yml" | tee "$second_apply"
  grep -Eq 'rehearsal[[:space:]]+: ok=[0-9]+[[:space:]]+changed=0[[:space:]]+' "$second_apply"

  docker exec "$host" nginx -t
  docker exec "$host" test -d /opt/palvelut/releases
  docker exec "$host" test -f /etc/palvelut/production.env
  docker exec "$host" docker version >/dev/null
}

restore_fixture() {
  docker exec "$host" sh -c 'printf "%s\n" rehearsal-restic-password > /tmp/restic-password && chmod 0600 /tmp/restic-password'
  docker exec "$host" env RESTIC_REPOSITORY=/tmp/restic-repo RESTIC_PASSWORD_FILE=/tmp/restic-password restic init >/dev/null

  docker exec "$host" docker run -d --rm --name "$source_db" \
    -e POSTGRES_DB=palvelut \
    -e POSTGRES_USER=palvelut \
    -e POSTGRES_PASSWORD=rehearsal-only \
    "$postgres_image" >/dev/null
  for _ in $(seq 1 60); do
    if docker exec "$host" docker exec "$source_db" pg_isready -U palvelut -d palvelut >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  docker exec "$host" docker exec "$source_db" pg_isready -U palvelut -d palvelut >/dev/null
  docker exec "$host" docker exec "$source_db" psql -U palvelut -d palvelut -v ON_ERROR_STOP=1 -c \
    'CREATE TABLE django_migrations (id bigint PRIMARY KEY, app varchar(255) NOT NULL, name varchar(255) NOT NULL, applied timestamptz NOT NULL); INSERT INTO django_migrations VALUES (1, '\''rehearsal'\'', '\''0001_fixture'\'', now());' >/dev/null

  docker exec "$host" mkdir -p /tmp/rehearsal-fixture/database
  docker exec "$host" sh -c "docker exec '$source_db' pg_dump -Fc -U palvelut -d palvelut > /tmp/rehearsal-fixture/database/palvelut.dump"
  docker exec "$host" env RESTIC_REPOSITORY=/tmp/restic-repo RESTIC_PASSWORD_FILE=/tmp/restic-password \
    restic backup /tmp/rehearsal-fixture --tag production --host palvelut-production --quiet

  docker cp "$repo_root/infra/scripts/restore-drill.sh" "$host:/tmp/restore-drill.sh"
  docker exec "$host" chmod 0755 /tmp/restore-drill.sh
  restore_output="$state_root/restore.log"
  docker exec "$host" env RESTIC_REPOSITORY=/tmp/restic-repo RESTIC_PASSWORD_FILE=/tmp/restic-password \
    /tmp/restore-drill.sh | tee "$restore_output"
  grep -q '^restore_status=ok ' "$restore_output"
  docker exec "$host" docker rm -f "$source_db" >/dev/null 2>&1 || true
  printf 'rehearsal_status=ok host=ubuntu-24.04 ansible=converged restore=ok\n'
}

cleanup() {
  docker rm -f "$host" >/dev/null 2>&1 || true
  docker image rm -f "${host}:fixture" >/dev/null 2>&1 || true
  rm -rf "$state_root"
}

for command in ansible-playbook docker ssh-keygen; do
  command -v "$command" >/dev/null || { echo "$command is required" >&2; exit 1; }
done

case "${1:-all}" in
  bootstrap) bootstrap ;;
  provision) provision ;;
  converge) converge ;;
  restore) restore_fixture ;;
  cleanup) cleanup ;;
  all)
    trap cleanup EXIT
    bootstrap
    provision
    converge
    restore_fixture
    ;;
  *) echo "usage: $0 [bootstrap|provision|converge|restore|cleanup|all]" >&2; exit 2 ;;
esac
