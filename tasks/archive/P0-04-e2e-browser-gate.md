# P0-04 — Canonical browser gate

Completed: 2026-09-03
Commit/PR: implementation `8b967e5dd77e549f6f9e3a29459479ae0c47145d`; PR #7

## Scope

- Added project-scoped `make e2e` backed by disposable Docker Compose services.
- Added a digest-pinned Playwright 1.62.1 Noble image with an exact local `@playwright/test` dependency.
- Added a minimal Chromium reachability check through Nginx into the Django application.
- CI now calls `make test`, `make e2e` and `make smoke` as the three canonical non-interactive gates.
- The browser gate cleans up project containers and volumes after every run.

## Checks

- GitHub Actions run `33692480285` on implementation head `8b967e5dd77e549f6f9e3a29459479ae0c47145d` — PASS.
- Bootstrap, Compose and Make contract tests — PASS (13 tests).
- `make test` — PASS.
- `make e2e` — PASS; Chromium reached the application through Nginx.
- `make smoke` — PASS.
- Compose cleanup — PASS.

## Corrected during verification

- Installed `@playwright/test` locally in the e2e image so Node resolves it from the Playwright config.
- Allowed only the Compose-internal `nginx` hostname in local development `DJANGO_ALLOWED_HOSTS` for browser-to-proxy requests.
- Aligned the minimal reachability assertion with the current root response (`200`) instead of assuming an unfinished route would return `404`.

## Deviations

- None for this scoped browser-gate infrastructure step. Full 360px/1440px viewport, keyboard, accessibility, browser-console coverage and Playwright artifact retention remain active later P0 work.
