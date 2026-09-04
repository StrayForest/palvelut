# P2-11 — Performance acceptance

## Scope

Close only the P2 acceptance requirement that public discovery meets the documented performance budgets with beta-sized fixtures. Do not expand into visual evidence/design review or later P2 gates.

## Completed

- Added `DiscoveryPerformanceAcceptanceTests` with the documented beta size of 50 published providers.
- The acceptance gate exercises the real anonymous discovery search route and the real discovery query path.
- Cached discovery p95 is enforced at `<= 300 ms`.
- Uncached discovery response p95 is enforced at `<= 800 ms`.
- Search database query p95 is enforced at `<= 300 ms`.
- The test warms imports/templates before sampling and measures repeated p95 samples rather than a single request.

## Verification

- `palvelut/apps/discovery/test_performance_acceptance.py::DiscoveryPerformanceAcceptanceTests::test_beta_sized_discovery_stays_within_latency_budgets` enforces the budgets.
- Implementation exact-head `702819038c41cb40744030377e2a9b54e3df9103` passed canonical Compose stack CI run `33927952725`.
- Final documentation exact-head must also pass canonical Compose stack CI before merge.

## Remaining

The next active P2 acceptance item is the required responsive screenshot evidence and design review checklist. P2 gates remain active after that.
