# Decisions

Last reviewed: 2026-09-10.

| ID | Decision | Reason |
|---|---|---|
| D01 | Product is a directory with direct external contact. | Lowest-friction user value; avoids marketplace operations. |
| D02 | No leads, requests, chat, booking, service payments, commissions, or native app in MVP. | They do not validate directory demand and multiply legal/support work. |
| D03 | Launch only in Helsinki, Espoo, and Vantaa. | Marketplace value depends on local supply density. |
| D04 | Anonymous public search; accounts only for providers/staff. | Removes conversion friction and personal-data load. |
| D05 | No public star ratings in MVP. | Off-platform work cannot be reliably verified yet. |
| D06 | Verification badges describe facts, source, and check date. | `Y-tunnus found` is not `trusted professional`. |
| D07 | Django 5.2 LTS modular monolith, Python 3.13, PostgreSQL 18. | Mature security/admin/SEO path with low solo-team complexity. |
| D08 | Django templates + HTMX + minimal Alpine.js + Tailwind CSS. | Server HTML, small JS, progressive enhancement, modern UI. |
| D09 | PostgreSQL full-text + `pg_trgm`; no external search engine. Russian category labels/synonyms drive launch search, while provider spoken-language filtering remains domain data. | Enough for MVP scale and typo-tolerant Russian discovery without coupling UI locale to languages a provider speaks. |
| D10 | Valkey 8.x for cache/rate limits; R2-compatible object storage for media. | Stateless web processes and cheap media delivery. |
| D11 | Docker Compose on one EU VPS behind Cloudflare; off-site backups. | Simple operations with an extraction path when load proves it. |
| D12 | Free supply first. Monetization is gated by measured provider value. | Charging before liquidity suppresses the scarce side. |
| D13 | Product and staff UI are Russian-only for the MVP. There is no UI language switcher and no FI/EN UI translation surface. | The launch audience and acquisition channel are Russian-speaking; unused pseudo-localization made the actual provider flow harder to understand and test. |
| D14 | Index curated city/category pages and published profiles only. | Prevents thin/filter-page SEO spam. |
| D15 | Product analytics are first-party, minimal, and aggregate. | Needed for provider value without building user profiles. |
| D16 | Canonical product base URL is `https://finrix.fi/palvelut`; `/palvelut/ru/` is the sole supported public UI prefix for the MVP. FI/EN public UI routes are unsupported and there are no alternate-locale hreflang targets. | Preserves the already-established Russian URL shape without a second route migration while enforcing one real product language. |
| D17 | Publish only owner-confirmed, legally identifiable providers; imported records remain non-public until claimed and approved. | Prevents impersonation, stale scraped profiles, and ambiguous accountability. |
| D18 | PostgreSQL 18 generates model UUIDv7 values with native `uuidv7()`. | One ordered-ID implementation; no extra runtime UUID package. |
| D19 | Provision the production VPS with idempotent Ansible; switch web containers blue/green and drain/replace workers through Compose. | Makes a fresh-host rebuild and low-downtime rollback reproducible without Kubernetes or duplicate schedulers. |

Add or revise a row only when the underlying decision changes.
