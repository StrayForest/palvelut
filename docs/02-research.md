# Research basis

Snapshot: 2026-09-02. Facts can age; verify them before changing strategy.

## What strong MVPs did

| Example | Verified early implementation/structure | Rule for Palvelut |
|---|---|---|
| Airbnb | Constrained event launch; company timeline records 80 bookings in 2008. The cited source does not establish an exact early stack. | Prove one geography/use case; do not repeat unsupported stack folklore. |
| DoorDash | Founders were the delivery operation, using Google Voice, Find My Friends and their cars. | Manual provider recruitment/moderation is valid until demand repeats. |
| YC guidance | Founders recruit and delight early users with work that does not scale. | Personally onboard the first 50 providers and interview users. |
| Shopify | Public engineering history shows a Rails monolith later divided into explicit components. | One deployable modular monolith; enforce domain boundaries in code. |
| GitHub | Public engineering history shows a long-lived Rails monolith at very large team/code scale. | Microservices are not a prerequisite for growth. |
| Basecamp | Bounded scopes, fixed time and variable optional scope. | Each roadmap stage has exclusions and a hard acceptance gate. |

The evidence supports narrow demand, manual learning, simple deploys, explicit boundaries and measurement. Historical framework versions are not selection criteria. Palvelut uses current supported Django/PostgreSQL releases because they fit server-rendered discovery, admin-heavy moderation, SEO and a solo team.

## Competitive audit

| Alternative | Strength | Gap/opportunity |
|---|---|---|
| Google Maps/Search | Reach, maps, reviews, SEO | No reliable Russian-language/service-mode filter. |
| Facebook/Telegram | Existing Russian-speaking supply | Poor structured comparison, freshness and verification. |
| ServiceMap | Closest product: city/category/language, profiles and booking | Snapshot: 16 businesses/8 cities/25 used categories; adds requests/booking, while Free hides direct contacts and Pro costs €15/month. |
| Yelp | Mature directory and provider-claim model | Reuse clear profile ownership/editing patterns; defer its review/advertising complexity. |
| Remppatori/Urakkamaailma | Rich profiles and social proof | Focused on renovation and marketplace workflows, not language-first discovery. |
| Thumbtack/Teot | Mature trust and transaction patterns | Their lead/order model is outside our scope; reuse only profile/trust UX lessons. |

## Product conclusions

1. Density beats category count.
2. Direct contact is the core conversion; do not hide it merely to imitate competitor pricing.
3. A `verified` badge must be atomic: business registry, licence, or email ownership—not a general seal.
4. Search landing pages need real local supply and original explanatory copy.
5. Provider analytics must prove visibility without claiming completed sales.
6. Reviews wait until the product has a defensible evidence/moderation model.

## Primary sources

- [Airbnb company timeline](https://news.airbnb.com/about-us/)
- [DoorDash: the early years](https://about.doordash.com/en-us/news/four-years-in-and-just-getting-started)
- [YC: Do Things That Don't Scale](https://www.paulgraham.com/ds.html)
- [Shopify: Deconstructing the Monolith](https://shopify.engineering/deconstructing-monolith-designing-software-maximizes-developer-productivity)
- [GitHub: Building GitHub with Ruby and Rails](https://github.blog/engineering/architecture-optimization/building-github-with-ruby-and-rails/)
- [Basecamp Shape Up](https://basecamp.com/shapeup)
- [ServiceMap product](https://servicemap.fi/) and [pricing](https://servicemap.fi/pricing/)
- [Yelp business resources](https://business.yelp.com/resources/)
- [Urakkamaailma provider fee](https://www.urakkamaailma.fi/palvelumaksu-urakoitsijalle)
- [PRH/YTJ open data](https://www.ytj.fi/en/index/opendata.html)
- [YTJ company search fields](https://www.ytj.fi/en/index/companysearch.html)
- [Valvira JulkiTerhikki](https://julkiterhikki.valvira.fi/)
- [Django 5.2 deployment documentation](https://docs.djangoproject.com/en/5.2/howto/deployment/)
- [PostgreSQL 18 UUID functions](https://www.postgresql.org/docs/18/functions-uuid.html)
