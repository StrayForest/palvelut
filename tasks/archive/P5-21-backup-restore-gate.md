# P5-21 — Backup restore gate

Status: completed.

## Scope

Close the P5 backup restore gate without duplicating the already-completed backup/restore implementation or its RPO/RTO and fresh-host acceptance work.

## Evidence

- `P5-05` implemented encrypted off-site PostgreSQL/media backup and isolated restore.
- `P5-11` verifies production-tagged snapshot age against the 24-hour RPO, full restore duration against the 4-hour RTO, media checksums, PostgreSQL restore and safe evidence output.
- `P5-17` verifies the restore path on a freshly provisioned disposable host through the production Ansible baseline.
- `.github/workflows/p5-ansible.yml` exercises the encrypted restore fixture on the exact PR head, so the gate is satisfied by re-running the canonical Ansible baseline rather than adding another restore implementation.

## Verification

- `Ansible baseline` must pass on the exact documentation head before merge.
