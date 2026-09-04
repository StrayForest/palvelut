# P2-01 — Public discovery surfaces

Status: complete.

## Scope

Implement the first P2 build step only: home, city/category landing, normalized search, result cards and provider profile.

## Completed

- Added a server-rendered home surface with two-field service/location search.
- Added normalized search with category label/synonym resolution and published-provider filtering.
- Added city/category landing pages and provider result cards.
- Added server-rendered provider profiles backed by `ProviderReadDocument`.
- Public discovery excludes suspended providers from search results and provider profiles.
- Preserved the existing localized `/palvelut/{locale}/` route contract with canonical and hreflang metadata.
- Added regression coverage for anonymous home access, synonym search, city/category landing, provider profile rendering and suspended-provider exclusion.

## Verification

Exact-head Compose CI `33890007504` passed all 24 steps for `d6dd93b69c66a1c747c402e6a0c352b013df22d5`, including lint/format, mypy, dependency audit, secret scan, frontend/application builds, migrations, non-browser tests, browser gate, retained Playwright evidence and disposable smoke.
