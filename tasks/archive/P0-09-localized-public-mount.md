# P0-09 — Localized public mount root

Completed: 2026-09-03
Commit/PR: implementation `07ef98ccdb8b1d5d1491f5686dc40a87c193022d`; PR #12

## Scope

- Django root URLconf now owns `/palvelut/{locale}/` for RU/FI/EN.
- Unsupported locale roots return a real 404.
- The localized root renders through the existing accessible/i18n base layout.
- Django static URLs are prefix-aware under `/palvelut/static/`.
- Nginx continues to proxy without rewriting the `/palvelut/` request prefix.
- The Playwright smoke route now targets the real localized public mount instead of `/`.
- Added focused routing contract coverage for locale ownership, static URL prefixing and proxy prefix preservation.

## Checks

- GitHub Actions run `33712668401` on implementation head `07ef98ccdb8b1d5d1491f5686dc40a87c193022d` — PASS.
- `make test` — PASS, including 24 discovered contract tests.
- `make e2e` — PASS against `/palvelut/en/` through Nginx.
- `make smoke` — PASS.

## Corrected during verification

- The first routing test used Django's default `testserver` host without an override and inherited from plain `unittest.TestCase`; the test harness was corrected without widening application `ALLOWED_HOSTS`.
- The existing Playwright gate still targeted `/`; after Django began intentionally returning 404 there, the gate was moved to the canonical localized mount.

## Deviations

- Redirect, cookie-path, canonical and hreflang contracts remain intentionally active as the next routing work; they were not included in this atomic step.
