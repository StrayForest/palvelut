# P0-13 — Base-page browser coverage

Completed: 2026-09-03
Commit/PR: implementation `393afd0690c5f4260663b89b632ce991725878ee`; PR #16

## Scope

- Expanded the canonical Playwright browser gate to exercise the localized base page at 360px and 1440px.
- Verified keyboard navigation by focusing the skip link with Tab and moving focus to `#main-content` after activation.
- Failed the browser gate on console errors or uncaught page errors.
- Fixed the local/debug stack exposed by the stricter gate: generated CSS/HTMX/Alpine assets are served through Django staticfiles in debug mode, while staging/production remain outside that debug-only path.
- Disabled the COOP response header only for local/test HTTP so Chromium does not emit an untrustworthy-origin console error; staging/production retain `same-origin` under required HTTPS.

## Checks

- Initial GitHub Actions run `33729851293` correctly failed the new browser gate and exposed missing static assets plus the local HTTP COOP console error.
- GitHub Actions run `33730089679` on implementation head `393afd0690c5f4260663b89b632ce991725878ee` — PASS.
- Dependency/command contract step — PASS.
- `make test` — PASS.
- `make e2e` — PASS at both 360px and 1440px with keyboard focus and no console/page errors.
- `make smoke` — PASS.

## Deviations

- The stricter browser gate exposed pre-existing local-stack defects, so the step includes the minimum runtime fixes required to make the documented browser contract true rather than suppressing the errors in the test.
