# P4-06 — Upstream failure acceptance

Completed the first active P4 acceptance criterion: an upstream registry failure never changes an existing valid verification fact into a false fact.

## What was verified

- The previously completed P4-01 YTJ/PRH adapter records registry outcomes as new immutable `VerificationCheck` rows rather than overwriting earlier checks.
- A transient/upstream failure is represented by a new `pending` check with `manual_fallback_required=true` after bounded retries.
- An earlier `verified` business-identity check remains `verified` after that failed lookup.
- This behavior is pinned by the deterministic regression `YtjPrhVerificationServiceTests.test_upstream_failure_records_pending_manual_fallback_without_mutating_valid_fact`.
- No new verification implementation was added for this acceptance closeout, avoiding duplication of the already archived P4-01 work.

## Evidence

- P4-01 implementation exact head: `c33db79209a1fd08691219b5f07f98ebd3a56133`.
- GitHub Actions `Compose stack` run `33957239855`: PASS on that exact implementation head.
- P4-01 archive: `tasks/archive/P4-01-ytj-prh-verification-adapter.md` documents the same immutable-history/manual-fallback implementation and test coverage.
- This documentation closeout must pass the repository Compose workflow on its exact PR head before merge.

## Remaining

- The next active P4 acceptance criterion is badge wording: public verification wording must not imply service quality or an unchecked licence.
