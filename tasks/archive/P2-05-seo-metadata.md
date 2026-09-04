# P2-05 — Discovery SEO metadata

Status: complete.

## Scope

Complete the next P2 build step only: canonicals, hreflang, sitemap, robots, structured data, old-slug redirects and the thin-page noindex rule.

## Completed

- Added locale-specific canonical URLs, `hreflang` alternates and `x-default` metadata for public discovery pages.
- Added `noindex,follow` for arbitrary search/filter pages and for thin city/category landing pages; sufficiently populated landing pages remain indexable.
- Added provider `LocalBusiness` JSON-LD with safely serialized structured data.
- Added permanent redirects from historical provider slugs to the current slug.
- Added public `robots.txt` and `sitemap.xml`; sitemap output is limited to published provider profiles and sufficiently populated city/category landing pages.
- Added regression coverage for canonical/hreflang, robots, sitemap, structured data, old-slug redirects and thin-page indexing behavior.
- Updated the frontend vendor-script contract so it still requires exactly the two external HTMX/Alpine assets while allowing non-executable JSON-LD structured-data script blocks.

## Verification

Exact-head Compose CI `33910312117` passed all 24 steps for `f6252f450404c575d7564e0f874a68bc1a47bc46`, including lint/format, mypy, dependency audit, secret scan, frontend/application builds, migrations, non-browser tests, browser gate, retained Playwright evidence and disposable smoke.
