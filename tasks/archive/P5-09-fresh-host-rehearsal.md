# P5-09 — Fresh-host Ansible restore rehearsal

Completed the first active P5 acceptance item: recreate a fresh disposable Ubuntu 24.04 rehearsal host with the production Ansible baseline and restore an encrypted backup fixture without undocumented manual steps.

## Scope

This closes the runtime acceptance left intentionally open by P5-01 and P5-05. It does not duplicate the Ansible baseline or production backup/restore implementation records.

## Verification

Implementation head `f33e06d4a4d7d3e3582e734dc580754ea2165691`:

- GitHub Actions `Ansible baseline` run `34002430501`: PASS.
- The fresh-host job bootstrapped a disposable Ubuntu 24.04 host, applied the production Ansible playbook, verified convergence/idempotence and required services, then ran the existing isolated restore path against a non-sensitive encrypted Restic fixture.
- GitHub Actions `Compose stack` run `34002430467`: PASS on the same exact head.
- No production database, media, endpoint or credential was used by the rehearsal fixture.

## Deviations

None.
