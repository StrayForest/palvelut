# P5-13 — Rollback and incident acceptance

Completed the active P5 acceptance step: one application rollback and one simulated deployment incident are executed successfully against the production deployment workflow.

## Verification

- Added `infra/scripts/deploy-rollback-acceptance.sh`, which executes the real `infra/scripts/deploy-production.sh` against disposable command, Nginx and release-state fixtures.
- Rollback starts from the green slot and restores the recorded previous release on blue, verifies the Nginx upstream returns to `127.0.0.1:8081`, and verifies current release state matches the previous immutable image/release.
- The rollback drill verifies `manage.py migrate` is not invoked, preserving the documented app-only rollback contract rather than attempting reverse database migration.
- The simulated incident forces the inactive slot readiness probe to fail during a new deploy.
- The incident is contained before traffic cutover: the deploy exits non-zero while the active slot, Nginx upstream and recorded current release remain unchanged.
- `tests/test_p5_rollback_incident_acceptance.py` executes the drill in the canonical non-browser test gate and asserts its machine-readable PASS evidence.
- Exact implementation head `e958be82ca41c6c1d6a95653603fe2f7b45bf997` passed full `Compose stack` run `34006735146`.

## Evidence

The drill emits only non-secret acceptance status fields:

- `rollback_acceptance=pass`
- `simulated_incident=readiness_failure`
- `incident_containment=pass`
- `database_reverse_migration=not_attempted`

## Deviations

- This acceptance uses isolated deterministic fixtures rather than changing the live production upstream or intentionally breaking production readiness.
- The following P5 acceptance item remains separate: proving zero failed synthetic requests during the upstream switch and stopping unsafe database rollback for operator action.
