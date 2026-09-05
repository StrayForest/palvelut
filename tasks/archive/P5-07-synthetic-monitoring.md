# P5-07 — Synthetic monitoring

Completed the active P5 build step: external synthetic monitoring for the public home, search, provider profile and contact redirect journey.

## Verification

- `infra/scripts/synthetic-monitor.sh` probes the public HTTPS origin with bounded connect/total timeouts and validates home, search and profile HTML plus the contact redirect status/location contract.
- `.github/workflows/p5-synthetic.yml` runs the production journey every five minutes and on manual dispatch after `SYNTHETIC_MONITOR_ENABLED=true`; production URL/provider identifiers and the monitor token remain outside Git.
- Synthetic requests authenticate with `X-Palvelut-Synthetic` using a shared runtime secret. Application analytics exclude authenticated synthetic impressions, profile views and contact clicks so monitoring does not contaminate provider funnel metrics.
- Production Compose requires the synthetic monitor token in the external production environment, while `.env.example` documents only a replace-me placeholder.
- `docs/runbooks/synthetic-monitoring.md` documents setup, the dedicated synthetic provider, enablement, probe coverage and failure handling.
- Regression contracts verify required journey coverage, HTTPS/timeouts, runtime-secret authentication and analytics exclusion.

## Evidence

- Implementation verification head: `900e59c613da288f45224c1a432a4f4b73553cd3`.
- GitHub Actions `Compose stack` run `33996495964`: PASS on the exact implementation head, including lint/format, type check, dependency/secret checks, builds, migrations, provider security/integration, canonical non-browser/browser gates, Playwright evidence and disposable smoke.

## Deviations

- The scheduled production job is deliberately disabled until production secrets and a dedicated published synthetic provider are configured and one manual probe has passed. This prevents an unconfigured monitor from generating false availability incidents; live production synthetic evidence remains part of the active P5 acceptance/gate criteria.
