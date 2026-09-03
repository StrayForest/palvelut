# P0-11 — Environment validation and health probes

Completed: 2026-09-03
Commit/PR: implementation `a1100a36983797ad8c05c3f1e6b68535641c9a28`; PR #14

## Scope

- Added explicit `PALVELUT_ENVIRONMENT` validation with local/test defaults and fail-closed staging/production requirements.
- Production-like settings now require debug off, an explicit secret key, explicit allowed hosts and an HTTPS `PUBLIC_BASE_URL`; secure cookies and HTTPS redirect are enabled there.
- Added dependency-free `/palvelut/health/live` and dependency-aware `/palvelut/health/ready` endpoints.
- Readiness checks PostgreSQL and Valkey, returns only generic status, and fails with HTTP 503 when either required dependency is unavailable.
- Both health responses use `Cache-Control: no-store`; the Compose web healthcheck now calls liveness directly.
- `make smoke` verifies liveness/readiness through Nginx against live disposable PostgreSQL and Valkey services.
- Added focused tests for dependency isolation/failure and production-like configuration validation.

## Checks

- GitHub Actions run `33720401075` on implementation head `a1100a36983797ad8c05c3f1e6b68535641c9a28` — PASS.
- Dependency/command contract step — PASS.
- `make test` — PASS.
- `make e2e` — PASS.
- `make smoke` — PASS, including live and ready HTTP probes with `no-store` headers.

## Deviations

- JSON structured logging and request IDs remain active P0 work; they were intentionally not bundled into this bounded step.
