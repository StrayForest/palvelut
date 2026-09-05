# P5-06 — Blue/green deploy and rollback

Completed the active P5 build step: blue/green web deploy/rollback plus worker drain/replace and singleton scheduler workflows using the exact tested image digest and backward-compatible migrations.

## Verification

- `compose.production.yml` provides blue/green web slots on loopback ports `8081`/`8082`, matching worker slots, and one un-slotted Celery beat scheduler; application processes use the exact `PALVELUT_IMAGE` digest supplied for the release.
- `infra/scripts/deploy-production.sh` validates the GHCR SHA-256 image digest and full release commit SHA, migrates forward before traffic switch, starts the inactive web slot, requires `/palvelut/health/ready`, validates and gracefully reloads Nginx, then starts the matching worker and warm-stops the previous worker with a bounded grace period.
- The workflow keeps the previous web slot available for app rollback and records only non-secret current/previous release state. Rollback reuses the previous immutable image and deliberately does not reverse database migrations.
- A single scheduler is force-recreated only after the web/worker cutover, preventing the deploy workflow from running two beat schedulers concurrently.
- The Ansible bootstrap upstream points at the blue slot, while subsequent switches are limited to the managed blue/green loopback upstreams.
- `docs/runbooks/deploy-rollback.md` documents immutable promotion, expand/backfill/switch/contract-later migration compatibility, deploy/rollback commands, verification and operational evidence requirements.
- Regression contracts verify slot topology, immutable-image use, readiness-before-switch, worker drain, singleton scheduler, safe app rollback and the Ansible bootstrap upstream.

## Evidence

- Implementation verification head: `169cfb0b27809402a0037fb82b82f6f3e210ce6e`.
- GitHub Actions `Compose stack` run `33993645904`: PASS on the exact implementation head, including lint/format, type check, dependency/secret checks, builds, migrations, provider security/integration, canonical non-browser/browser gates, Playwright evidence and disposable smoke.
- GitHub Actions `Ansible baseline` run `33993645902`: PASS on the exact implementation head.

## Deviations

- CI validates the deterministic deployment contract, Nginx/Compose configuration and application gates without production credentials or a production host. The first live zero-failure switch/rollback remains an acceptance exercise on the production/rehearsal environment and is still represented by the active P5 acceptance criteria rather than being claimed by this build step.
