#!/usr/bin/env bash
set -euo pipefail

for command in ansible-playbook docker ssh ssh-keygen; do
  command -v "$command" >/dev/null || { echo "$command is required" >&2; exit 1; }
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
work="$(mktemp -d)"
host_name="palvelut-rehearsal-${RANDOM}-$$"
image_name="palvelut-rehearsal-host:${RANDOM}-$$"
key_path="$work/rehearsal_ed25519"
password_file="$work/restic-password"
inventory="$work/inventory.yml"
second_run="$work/ansible-second.log"
bootstrap_user="rehearsal"

cleanup() {
  docker rm -f "$host_name" >/dev/null 2>&1 || true
  docker image rm -f "$image_name" >/dev/null 2>&1 || true
  rm -rf "$work"
}
trap cleanup EXIT

ssh-keygen -q -t ed25519 -N '' -f "$key_path"
printf 'rehearsal-restic-password\n' > "$password_file"
chmod 0600 "$password_file"

cat > "$work/Dockerfile" <<'EOF'
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
 && apt-get install -y --no-install-recommends systemd systemd-sysv openssh-server python3 sudo \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && mkdir -p /run/sshd
STOPSIGNAL SIGRTMIN+3
CMD ["/sbin/init"]
EOF

docker build --quiet -t "$image_name" "$work" >/dev/null
docker run -d --privileged --cgroupns=host \
  -v /sys/fs/cgroup:/sys/fs/cgroup:rw \
  -p 127.0.0.1::22 \
  --name "$host_name" "$image_name" >/dev/null

# The bootstrap account exists only on the disposable rehearsal host. The
# production playbook still creates and hardens the real deploy account.
docker exec "$host_name" useradd --create-home --shell /bin/bash "$bootstrap_user"
docker exec "$host_name" mkdir -p "/home/$bootstrap_user/.ssh"
docker cp "${key_path}.pub" "$host_name:/home/$bootstrap_user/.ssh/authorized_keys"
docker exec "$host_name" chown -R "$bootstrap_user:$bootstrap_user" "/home/$bootstrap_user/.ssh"
docker exec "$host_name" chmod 0700 "/home/$bootstrap_user/.ssh"
docker exec "$host_name" chmod 0600 "/home/$bootstrap_user/.ssh/authorized_keys"
docker exec "$host_name" bash -c "printf '%s ALL=(ALL) NOPASSWD:ALL\\n' '$bootstrap_user' > /etc/sudoers.d/rehearsal"
docker exec "$host_name" chmod 0440 /etc/sudoers.d/rehearsal
docker exec "$host_name" systemctl enable --now ssh >/dev/null

host_port="$(docker port "$host_name" 22/tcp | awk -F: 'NR == 1 {print $NF}')"
[[ "$host_port" =~ ^[0-9]+$ ]] || { echo "failed to discover rehearsal SSH port" >&2; exit 1; }

ssh_opts=(
  -i "$key_path"
  -p "$host_port"
  -o BatchMode=yes
  -o StrictHostKeyChecking=no
  -o UserKnownHostsFile=/dev/null
  -o ConnectTimeout=5
)
for _ in $(seq 1 60); do
  if ssh "${ssh_opts[@]}" "$bootstrap_user"@127.0.0.1 true >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
ssh "${ssh_opts[@]}" "$bootstrap_user"@127.0.0.1 true >/dev/null

cat > "$inventory" <<EOF
all:
  hosts:
    rehearsal:
      ansible_host: 127.0.0.1
      ansible_port: ${host_port}
      ansible_user: ${bootstrap_user}
      ansible_ssh_private_key_file: ${key_path}
      ansible_ssh_common_args: >-
        -o StrictHostKeyChecking=no
        -o UserKnownHostsFile=/dev/null
  vars:
    deploy_authorized_key: "$(cat "${key_path}.pub")"
    palvelut_environment_file: |
      DJANGO_SECRET_KEY=rehearsal-only
      DJANGO_DEBUG=0
EOF

export ANSIBLE_CONFIG="$repo_root/infra/ansible/ansible.cfg"
ansible-playbook -i "$inventory" "$repo_root/infra/ansible/site.yml"
ansible-playbook -i "$inventory" "$repo_root/infra/ansible/site.yml" | tee "$second_run"
grep -Eq 'changed=0[[:space:]]' "$second_run" || {
  echo "Ansible rehearsal is not idempotent on the second run" >&2
  exit 1
}

ssh "${ssh_opts[@]}" "$bootstrap_user"@127.0.0.1 \
  'sudo sh -c "command -v docker >/dev/null && command -v restic >/dev/null && command -v rclone >/dev/null && test -f /etc/palvelut/production.env && test -d /opt/palvelut/backups"'

# Build a non-sensitive backup fixture on the disposable host. This proves the
# production restore script from encrypted restic storage without touching a
# real database, media bucket, or production credential.
docker cp "$repo_root/infra/scripts/restore-drill.sh" "$host_name:/tmp/restore-drill.sh"
docker cp "$password_file" "$host_name:/tmp/restic-password"
docker exec "$host_name" chmod 0700 /tmp/restore-drill.sh
docker exec "$host_name" chmod 0600 /tmp/restic-password

docker exec "$host_name" bash -se <<'EOF'
set -euo pipefail
fixture=/tmp/palvelut-rehearsal-fixture
repo=/tmp/palvelut-rehearsal-restic
source_container=palvelut-rehearsal-source
mkdir -p "$fixture/database"
trap 'docker rm -f "$source_container" >/dev/null 2>&1 || true' EXIT

docker run -d --rm --name "$source_container" \
  -e POSTGRES_DB=palvelut_fixture \
  -e POSTGRES_USER=palvelut_fixture \
  -e POSTGRES_PASSWORD=fixture-only \
  postgres:18-alpine@sha256:d3e1620b530c944afa6e887d22eb899824da68e19c52024bf98f5220c88a65b2 >/dev/null
for _ in $(seq 1 60); do
  if docker exec "$source_container" pg_isready -U palvelut_fixture -d palvelut_fixture >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
docker exec "$source_container" pg_isready -U palvelut_fixture -d palvelut_fixture >/dev/null
docker exec "$source_container" psql -U palvelut_fixture -d palvelut_fixture -v ON_ERROR_STOP=1 <<'SQL'
CREATE TABLE django_migrations (
  id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  app varchar(255) NOT NULL,
  name varchar(255) NOT NULL,
  applied timestamptz NOT NULL DEFAULT now()
);
INSERT INTO django_migrations (app, name) VALUES ('rehearsal', '0001_fixture');
SQL
docker exec "$source_container" pg_dump -U palvelut_fixture -d palvelut_fixture -Fc > "$fixture/database/palvelut.dump"
docker rm -f "$source_container" >/dev/null
trap - EXIT

export RESTIC_REPOSITORY="$repo"
export RESTIC_PASSWORD_FILE=/tmp/restic-password
restic init --quiet
restic backup "$fixture" --tag production --host palvelut-production --quiet
/tmp/restore-drill.sh
EOF

printf 'rehearsal_status=ok host=ubuntu-24.04 provision=ansible restore=isolated\n'
