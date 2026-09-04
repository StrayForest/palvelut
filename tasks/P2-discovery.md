# P2 — Public discovery

Depends: P1. Read: `docs/03-experience.md`, `docs/04-design.md`, `docs/05-architecture.md`, SEO/performance sections of `docs/06-quality.md`.

## Build

- Serve every surface at canonical `/palvelut/{locale}/...` routes with the same prefix in local/proxy tests.
- Category/city/language/service-mode filters, typo-tolerant synonyms and honest empty alternatives.
- Structured contact redirect with server-side destination resolution and minimal event.
- Canonicals, hreflang, sitemap, robots, structured data, old-slug redirects and thin-page noindex rule.
- Public cache headers/read-through cache with explicit authenticated bypass.

## Accept

- Anonymous user reaches a relevant provider and contact in ≤3 actions.
- Core flow works without JavaScript; HTMX preserves URL/history/focus.
- No unpublished/suspended provider appears in HTML, schema, sitemap or cache.
- Ranking is deterministic/tested; arbitrary filter pages are not indexed.
- Meets performance budgets with beta-sized fixtures.
- PR evidence includes the required home/results/empty/profile screenshots at 360, 768 and 1440px and passes the design review checklist.

## Gates

Search relevance fixtures, SQL/query-plan checks, cache isolation tests, metadata/schema tests, Playwright at required widths, retained visual evidence, axe, Lighthouse and warm/cold load smoke.
