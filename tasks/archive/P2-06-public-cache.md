# P2-06 — Public discovery cache policy

Status: complete.

## Scope

Complete the next P2 build step only: public cache headers/read-through cache with an explicit authenticated bypass.

## Completed

- Added Django-cache/Valkey-backed read-through caching for anonymous public discovery GET/HEAD responses.
- Added the documented shared-cache policy: home uses a 1-hour shared TTL, while city/category and provider-profile pages use a 5-minute shared TTL with 24-hour stale-while-revalidate.
- Normalized search uses a short 2-minute application cache while explicitly disabling shared/CDN caching.
- Cache keys include the complete request path and query string so filter/search variants cannot collide.
- Authenticated and non-GET requests bypass the public cache, execute the view directly and return `private, no-store` with `Vary: Cookie`.
- Authenticated bypasses do not overwrite anonymous cache entries.
- Added regression coverage for cache headers, read-through behavior, query-string isolation and authenticated cache bypass.

## Verification

Exact-head Compose CI `33912031299` passed all 24 steps for implementation head `31f4b449eecc3519423a0c498b21a26dcf880b53`, including lint/format, mypy, dependency audit, secret scan, frontend/application builds, migrations, non-browser tests, browser gate, retained Playwright evidence and disposable smoke.
