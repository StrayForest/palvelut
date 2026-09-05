# P5-01 — Reproducible Ansible host baseline

Completed the first P5 build item: idempotent Ansible for a fresh Ubuntu LTS VPS baseline.

## Delivered

- Non-root `palvelut` deploy user with SSH public-key access and controlled sudo policy.
- SSH hardening, UFW default-deny inbound policy, and explicit SSH/HTTP/HTTPS ingress.
- Automatic security updates via `unattended-upgrades`.
- Docker's official Ubuntu 24.04 stable repository with exact package pins for Docker Engine/CLI, containerd, Buildx and Compose, plus package holds.
- Reproducible application, shared and backup directories with explicit ownership/modes.
- Nginx reverse-proxy site owned by Ansible.
- Application environment secret placement under `/etc/palvelut/production.env`, supplied only as an external Ansible variable and written with `no_log`.
- Pinned Ansible collections and a dedicated PR syntax/lint workflow.

## Verification

- `Ansible baseline` run `33975098083`: PASS on implementation head `a531ec28d903831e7e82a148dc43ddbb3c6587b9`.
- The gate installs `ansible-core==2.21.3` and `ansible-lint==26.8.0`, installs the pinned collections, then passes `ansible-playbook --syntax-check` and `ansible-lint` for `infra/ansible/site.yml`.
- Runtime idempotence on a fresh disposable host remains an explicit P5 acceptance/gate criterion and is not duplicated as an active build item.

## Deviations

None.
