# P5-02 — Production image and edge cache contract

Completed the next P5 build item: production images/Compose, Cloudflare/Nginx cache contract, WAF/rate-limit rules and a safe purge workflow.

## Delivered

- `main` now builds a commit-tagged GHCR application image and reports the pushed immutable repository digest without publishing a `latest` tag.
- `compose.production.yml` runs PostgreSQL, Valkey, web and worker with no public database/cache ports; the web origin binds only to `127.0.0.1:8080` for host Nginx.
- Production Compose requires the external `/etc/palvelut/production.env` contract and an exact `ghcr.io/strayforest/palvelut@sha256:<digest>` application reference via `infra/scripts/production-compose.sh`.
- Cloudflare cache rules bypass state-changing, cookie-bearing, account, staff, report and health traffic; anonymous public GET/HEAD traffic remains eligible only while respecting origin `Cache-Control` TTLs.
- Host Nginx remains a non-caching reverse proxy, so the application is the cache-policy source of truth and Cloudflare is the only shared edge cache layer.
- Cloudflare managed/OWASP WAF baselines plus bounded per-IP login, password-reset, registration and content-report rate-limit contracts are recorded in `infra/cloudflare/rules.json`.
- Cache invalidation is exact-URL only under `https://finrix.fi/palvelut/`, capped at 30 URLs per request; there is deliberately no purge-everything mode.
- Regression tests pin image immutability, network exposure, cache/auth separation, WAF/rate-limit coverage and purge safety.

## Verification

- `Compose stack` run `33978332579`: PASS on implementation head `b150165d360ae13596318b81eafb60bec8ce34b4`.
- The exact-head run passed bootstrap, dependency/command contracts, lint/format, type check, dependency and secret scans, frontend/application builds, migrations, Django deploy checks, provider security/integration, canonical non-browser/browser gates, Playwright evidence and disposable smoke.
- `tests/test_p5_production_cache_contract.py` is part of the canonical non-browser gate and passed in that run.

## Deviations

- Live Cloudflare rule application is intentionally credential/environment-specific; this step establishes the versioned contract and safe API purge workflow without storing zone credentials in Git.
- Stage-level acceptance still separately requires a live cache/auth probe and exact staging→production digest promotion; those acceptance criteria remain active and were not archived here.
