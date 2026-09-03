# P0-08 — Tailwind build and base frontend assets

Completed: 2026-09-03
Commit/PR: implementation `3fd603be33b4a47b29c1bbf6e5d6c25a3dd7c75e`; PR #11

## Scope

- Added exact Tailwind CSS and Tailwind CLI 4.3.3 dependencies to the existing frontend build stage.
- Added `frontend/app.css` and compile it to minified `static/css/app.css` while scanning Django templates.
- Wired the built stylesheet and the already vendored HTMX/Alpine.js files into `templates/base.html` through Django static URLs.
- Kept browser dependencies first-party at runtime; no CDN was introduced.
- Added minimal Tailwind utility classes to the accessible base layout without changing its existing landmarks or i18n contract.
- Extended frontend contract tests for dependency pins, Tailwind compilation and base-template asset wiring.

## Checks

- GitHub Actions run `33708830847` on implementation head `3fd603be33b4a47b29c1bbf6e5d6c25a3dd7c75e` — PASS.
- Dependency/command contract verification — PASS.
- `make test` — PASS.
- `make e2e` — PASS.
- `make smoke` — PASS.

## Corrected during verification

- The first exact-head run `33708743850` failed because the existing frontend `npm install --omit=optional` removed Tailwind's platform-specific Lightning CSS binary. The frontend build now retains optional dependencies; the corrected exact head passed all gates.

## Deviations

- None. Public prefix routing, environment/health/logging, expanded Playwright coverage and the remaining full P0 CI/security gates stay active in `tasks/P0-foundation.md`.
