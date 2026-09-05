# P4-14 — Label snapshots

Completed the next active P4 gate: deterministic snapshots now pin the exact public verification label text for every registered verification fact kind without changing verification behaviour.

## What changed

- Extended the existing public trust regression suite with fixed-date label snapshots for `business_identity` and `professional_right`.
- Snapshots pin the exact fact, official source name and `YYYY-MM-DD` check date required by the public trust contract.
- No registry type, adapter, public presentation logic or verification state transition was changed; this closes only the label-snapshot gate and does not duplicate P4-02/P4-03/P4-07.

## Evidence

- Implementation exact head: `19567480224316edeb15eb11ebb0b76bbf4c5d53`.
- GitHub Actions `Compose stack` run `33991968915`: PASS on that exact head, including lint/format, type check, dependency/secret scans, migrations, non-browser/browser gates and disposable smoke.
- PR: #129.

## Deviations

None.
