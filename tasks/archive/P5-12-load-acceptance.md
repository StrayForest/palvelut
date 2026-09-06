# P5-12 — Load SLO and overload acceptance

Completed the active P5 acceptance step: production-like anonymous warm/cold load meets the documented server-side SLOs and overload demonstrates bounded request/cache pools and the web accept queue.

## Verification

- Added a dedicated `P5 load acceptance` workflow against a disposable local Compose stack behind nginx.
- Reused the beta-sized discovery performance acceptance to keep search-query p95 within 300 ms.
- Warm public load: 400 requests at concurrency 8, p95 33.56 ms against the 300 ms SLO, with zero failures and zero 5xx responses.
- Cold public/search load: 400 requests at concurrency 8, p95 95.49 ms against the 800 ms SLO, with zero failures and zero 5xx responses.
- Overload probe: 600 requests at concurrency 128 exercised controlled load shedding while keeping request concurrency explicitly bounded at 16 per ASGI worker.
- Gunicorn uses 2 workers with backlog 128; the Django Valkey cache pool is explicitly capped at 16 connections per pool.
- PostgreSQL peaked at 5 observed connections during the run and remained below the acceptance ceiling of 40.
- Exact implementation head `170249222e2846e472ca593fafdb251518333830` passed `P5 load acceptance` run `34005937399` and full `Compose stack` run `34005937408`.

## Evidence

- Machine-readable warm/cold/overload timings and resource observations are uploaded by the load workflow as `p5-load-evidence-*` artifacts.
- Existing P2 performance acceptance remains the query-level regression baseline; this P5 closeout adds production-like concurrency and overload evidence rather than duplicating P2.

## Deviations

- The load workflow exercises the local nginx/origin stack, not an external CDN. CDN cache/auth behavior was already closed separately in P5 and is not duplicated here.
- Browser rendering/Web Vitals remain covered by the existing browser gates; this step closes the documented server-side load SLO and overload pool/queue acceptance only.
