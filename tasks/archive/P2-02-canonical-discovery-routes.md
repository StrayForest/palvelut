# P2-02 — Canonical discovery routes

Status: complete.

## Scope

Complete the next P2 build step only: keep every public discovery surface under canonical `/palvelut/{locale}/...` routes and explicitly cover the same mount prefix in local/proxy routing tests.

## Completed

- Confirmed all existing public discovery routes are mounted under `/palvelut/{locale}/...`.
- Added an explicit route-reversal contract for localized home, search, provider profile and city/category landing surfaces.
- Added regression coverage proving equivalent unmounted `/en/...` discovery paths are not public routes.
- Kept the existing nginx proxy contract that forwards paths without rewriting or stripping the `/palvelut` mount prefix.
- No product/runtime routing changes were required because the canonical URL implementation was already correct.

## Verification

Exact-head Compose CI `33895967561` passed all 24 steps for `c0b2ccd198a4bcd2fd18337b5ad48f185b67d8ce`, including lint/format, mypy, dependency audit, secret scan, frontend/application builds, migrations, non-browser tests, browser gate, retained Playwright evidence and disposable smoke.
