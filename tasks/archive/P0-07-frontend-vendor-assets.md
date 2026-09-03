# P0-07 — Frontend vendor assets

Completed: 2026-09-03
Commit/PR: implementation `39e8d55ca3419dce177d2c1f82247402335c8720`; PR #10

## Scope

- Added exact pinned frontend package declarations for HTMX `2.0.4` and Alpine.js `3.14.8`.
- Added an immutable Node-capable frontend builder stage by reusing the already digest-pinned Playwright image.
- The app image now copies HTMX and Alpine distributables into first-party `static/vendor/` assets instead of depending on a runtime CDN.
- Added Django staticfiles discovery for the generated static directory.
- Added focused frontend-vendor contract tests.
- Generalized the existing image-pin contract so every `FROM` image in a multi-stage Dockerfile must be digest pinned.

## Checks

- Initial CI run `33705021947` correctly failed because the old Dockerfile pin test assumed a single-stage image.
- The contract was corrected to validate every Dockerfile `FROM` image independently.
- Exact implementation head `39e8d55ca3419dce177d2c1f82247402335c8720`, run `33705078321` — PASS.
- Dependency/command contract verification — PASS.
- `make test` — PASS.
- `make e2e` — PASS.
- `make smoke` — PASS.

## Deviations

- Tailwind build and loading the vendored HTMX/Alpine assets from the base layout remain active P0 work; this step only establishes deterministic first-party vendor artifacts in the application image.
