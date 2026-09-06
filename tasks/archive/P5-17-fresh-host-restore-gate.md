# P5-17 — Fresh-host restore gate

Completed the next active P5 gate: the production Ansible path recreates a disposable Ubuntu host and completes the existing isolated encrypted restore fixture without undocumented manual repair steps.

## Verification

- This gate reuses the implementation already archived in `P5-09-fresh-host-rehearsal.md` and the backup/restore implementation archived in `P5-05-backup-restore.md`; no duplicate implementation was added.
- Exact PR head `5c725147e2a98594b4b68d7902c973ec6c88a29f` passed `Ansible baseline` run `34010546449`.
- The successful job explicitly completed `Bootstrap disposable Ubuntu host`, `Provision disposable host with production Ansible`, `Verify Ansible convergence and host services`, and `Run isolated encrypted restore fixture`.
- The same exact head also passed `Compose stack` run `34010546462` and `P5 load acceptance` run `34010546460`.
- This archive-only documentation change intentionally re-runs repository CI before merge.

## Deviations

None.
