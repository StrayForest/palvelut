# P4-13 — Adapter contract/failure tests

Closed the first remaining P4 gate by verifying the existing YTJ/PRH adapter contract and deterministic failure coverage without duplicating already archived implementation work.

## What was verified

- Found responses preserve the upstream source snapshot and evidence metadata.
- Successful empty responses are treated as factual `not_found` results rather than upstream failures.
- Transient 503 failures retry only to the configured bound and then require manual review.
- Retry and timeout configuration cannot exceed the adapter safety bounds.
- A failed recheck creates a new pending/manual-fallback fact and does not mutate an earlier verified fact.
- The coverage uses a deterministic fake transport and requires no live PRH/YTJ dependency.

## Evidence

- Contract/failure regression suite: `palvelut/apps/verification/test_ytj_prh_adapter.py`.
- Original adapter implementation exact head: `c33db79209a1fd08691219b5f07f98ebd3a56133`.
- GitHub Actions `Compose stack` run `33957239855`: PASS on that exact implementation head.
- P4-01 and P4-06 archives already document the implementation and upstream-failure acceptance behavior; this record closes only the remaining stage gate and adds no duplicate implementation.

## Remaining

- Label snapshots.
- Abuse tests.
- Keyboard and screen-reader smoke.
