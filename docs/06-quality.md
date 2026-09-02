# Quality contracts

## Security baseline

Use OWASP ASVS Level 2 as the release checklist.

- HTTPS only; HSTS after domain validation; strict allowed hosts and origin checks.
- HttpOnly, Secure, SameSite cookies; CSRF on every state change; session rotation on auth changes.
- Argon2 password hashing, verified email, rate-limited login/reset; staff MFA required.
- Server-side authorization for every provider/staff object; ownership tests mandatory.
- CSP without broad `unsafe-inline`, frame denial, MIME sniffing denial and restrictive permissions policy.
- Allowlisted contact schemes/hosts; SSRF-safe integrations; secrets outside Git and logs.
- Images only: byte-signature check, decode/re-encode, metadata removal, pixel/size limits.
- Append-only security/moderation audit trail with actor, target, action, time and request ID.
- Daily database backups, encrypted off-site copies, monthly restore test.

Run `manage.py check --deploy` in CI against production-like settings.

## Privacy/legal gate

Before public beta, owner review is required for privacy notice, provider terms, cookie policy, content-report process and controller identity. Record purpose, legal basis, retention, processor and deletion/export route for each personal-data field. Check DSA applicability with Finnish/EU counsel; do not treat this document as legal advice.

Public profile data must be provider-supplied or clearly sourced. Collect no user account, precise location, message body or cross-site identifier in MVP analytics. Raw analytics expire after 90 days; daily aggregates retain no visitor identity.

## SEO contract

- Server-render unique title, H1, description, canonical and social metadata.
- `LocalBusiness`/most-specific schema only when page facts support it; no fabricated ratings.
- XML sitemap contains canonical, published, indexable URLs and accurate `lastmod`.
- `hreflang` sets are reciprocal; locale routes never auto-redirect crawlers by IP.
- Index city/category page only with ≥3 active providers and useful localized copy.
- Filter/search/account/admin/report pages are not indexed.
- Preserve slug redirects and return real 404/410 status for removed content.
- Search Console and Bing Webmaster Tools are release dependencies.

## Performance/SLO

| Measure | Gate |
|---|---:|
| Availability | 99.9% monthly after beta |
| Public cached TTFB p95 | ≤300 ms |
| Public uncached response p95 | ≤800 ms |
| Search query p95 at beta dataset | ≤300 ms |
| LCP p75 | ≤2.5 s |
| INP p75 | ≤200 ms |
| CLS p75 | ≤0.1 |
| Initial first-party JS gzip | ≤75 KB |
| 5xx | <0.1% of requests |

Budgets are CI/release gates, not aspirations. Test with production-like images and taxonomy.

## Test layers

- Unit: domain rules, normalization, ranking, verification labels.
- Database: constraints, migrations, query count and indexes.
- Integration: auth/ownership, revision publish, cache invalidation, contact redirect, outbox idempotency.
- Browser: public search/profile/contact and provider onboarding at required viewports, keyboard and reduced motion.
- Security: dependency/secret scan, headers, CSRF, IDOR, upload corpus, rate limits.
- SEO/accessibility: rendered metadata/schema/sitemap, axe plus manual keyboard/screen-reader smoke.
- Load: anonymous browse/search mix; include cache cold/warm and database saturation metrics.

## Observability

Every request has a request ID and structured log. Dashboards cover traffic, latency, errors, cache hit ratio, DB pool/slow queries, queue age/failures, email delivery, media failures and backups. Alerts must point to a runbook and avoid personal data.

Business funnel: `search_submitted → results_viewed → profile_viewed → contact_clicked`. Also track `zero_results`, onboarding completion, moderation time, profile freshness and provider-reported genuine enquiries.

## References

- [Django deployment checklist](https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
- [Google page experience](https://developers.google.com/search/docs/appearance/page-experience)
- [Google LocalBusiness data](https://developers.google.com/search/docs/appearance/structured-data/local-business)
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [Finnish Data Protection Ombudsman principles](https://tietosuoja.fi/en/data-protection-principles)
- [EU Digital Services Act overview](https://digital-strategy.ec.europa.eu/en/policies/digital-services-act)
