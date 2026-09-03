# P0-10 — Routing metadata contract

Completed: 2026-09-03
Commit/PR: implementation `3e497e4dd95907e4870a76f7b0fb699e020a467b`; PR #13

## Scope

- Added a `/palvelut/` mount-root redirect to the configured default locale without leaving the product prefix.
- Added a validated `PUBLIC_BASE_URL` that must be an absolute HTTP(S) URL ending exactly at `/palvelut`.
- Scoped language, session and CSRF cookies to `/palvelut/`.
- Added absolute canonical URLs plus reciprocal RU/FI/EN hreflang links and `x-default` on localized root pages.
- Kept static URLs and the Nginx proxy prefix-preserving.
- Added focused routing contract tests for redirects, cookie paths, public-base validation and rendered SEO links.

## Checks

- GitHub Actions run `33716207701` on implementation head `3e497e4dd95907e4870a76f7b0fb699e020a467b` — PASS.
- Dependency/command contract verification — PASS.
- `make test` — PASS.
- `make e2e` — PASS.
- `make smoke` — PASS.
- Compose cleanup — PASS.

## Deviations

- None. Broader production environment validation, health endpoints, structured logging and request IDs remain active later P0 work.
