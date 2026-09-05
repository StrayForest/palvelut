# P4-01 — YTJ/PRH verification adapter

Completed the first P4 build step: YTJ/PRH verification adapter with source snapshots/metadata, bounded retries/timeouts and manual fallback.

## What changed

- Added a fixed-origin HTTPS adapter for the PRH YTJ Open Data API v3 business-ID lookup.
- Persisted the queried Y-tunnus, source, retrieval timestamp, HTTP status, attempt count, outcome and raw source snapshot in verification evidence metadata.
- Bounded upstream work to at most 3 attempts and a 4-second timeout per attempt; redirects are rejected.
- Transient/upstream failures produce a new pending check that explicitly requires manual review instead of mutating an earlier valid verification fact.
- Added deterministic fake-transport tests for found/not-found results, source snapshots, retry bounds, manual fallback and preservation of an existing verified check.

## Evidence

- Implementation exact head: `c33db79209a1fd08691219b5f07f98ebd3a56133`.
- GitHub Actions `Compose stack` run `33957239855`: PASS on the exact implementation head.
- No production, staging or external PRH dependency was required by the tests; the adapter contract is verified with deterministic fakes.

## Deviations

None.
