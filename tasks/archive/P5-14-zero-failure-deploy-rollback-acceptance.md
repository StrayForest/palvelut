# P5-14 — Zero-failure deploy and safe rollback acceptance

Completed the active P5 acceptance step: an app-only blue/green deployment produces no failed synthetic request during the upstream switch, and an unsafe rollback stops before traffic cutover for operator action instead of attempting a database downgrade.

## Verification

- Added `infra/scripts/zero-failure-deploy-acceptance.sh`, which exercises the real `infra/scripts/deploy-production.sh` against isolated deterministic command, Nginx and release-state fixtures.
- During deployment, 240 synthetic probes run across the upstream change and observe both the old blue upstream (`8081`) and new green upstream (`8082`) with zero invalid/failed observations.
- The drill verifies that the Nginx reload path is actually reached and that deployment state advances only after the switch.
- Rollback is then simulated with the previous application failing readiness against the current database schema.
- The unsafe rollback exits non-zero before traffic cutover, leaves active slot/upstream/current release unchanged, emits explicit operator-action guidance, and never invokes `manage.py migrate` or any reverse database migration.
- `tests/test_p5_zero_failure_deploy_acceptance.py` executes the drill in the canonical non-browser gate and asserts its machine-readable PASS evidence.
- Exact implementation head `5786b3da8c5d34e46d690b3852b85c3f565aa2bc` passed full `Compose stack` run `34008034525`, including browser and disposable smoke gates.

## Evidence

The drill emits only non-secret acceptance status fields:

- `synthetic_requests=240`
- `synthetic_failures=0`
- `upstream_switch_observed=pass`
- `unsafe_database_rollback=operator_action_required`
- `database_reverse_migration=not_attempted`

## Deviations

- The switch is exercised with deterministic isolated command/Nginx fixtures rather than changing the live production upstream. This keeps the acceptance repeatable and prevents intentional production disruption while still executing the production deploy script and its traffic-switch path.
- Previously archived P5 rollback/readiness-incident coverage remains historical evidence and is not duplicated here.
