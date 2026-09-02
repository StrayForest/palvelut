# Product

## Verdict

**GO as a narrow directory; NO-GO as a broad marketplace.** The idea has a clear language/trust niche and an owned Finrix distribution channel. Its ceiling is limited if it remains Russian-only Finland, so the MVP must prove a profitable directory, not imitate a venture-scale marketplace.

## Problem

A person currently combines Google, Facebook, Telegram and recommendations to answer one question: _who nearby provides this service in Russian and can be checked?_ Existing sources trade structure for reach or language relevance for trust.

## Promise

> Найдите специалиста в Финляндии, с которым можно говорить по-русски.

The product shortens `need → compare → direct contact`. It does not participate after contact.

## Initial market

- Geography: Helsinki, Espoo, Vantaa.
- Supply target: 8 high-intent categories first—accounting, legal, car repair, renovation, electrical, plumbing, psychology, massage/physiotherapy.
- Demand: Russian-speaking residents; Finnish-speaking relatives/employers may use FI pages later.
- Supply: owner-confirmed solo professionals and companies legally offering services in Finland under the eligibility contract below.

## Provider eligibility

- A commercial provider needs an active Finnish Y-tunnus and a public legal identity matching YTJ/PRH.
- Russian must be a provider-declared service language; the UI labels it as declared unless separately evidenced.
- An employed regulated professional may list only with verified identity, applicable official professional right, and employer authorization.
- Regulated services publish only after the applicable register/source is reviewed; an unavailable source produces no positive label.
- Staff-created/imported records stay non-public and `unclaimed` until a provider proves control and staff approves the claim.
- Informal, anonymous, prohibited, suspended, or unverifiable providers are not published. Policy/legal uncertainty blocks publication.

## Value

### User

- search by service, city, language and service mode;
- compare clear prices, areas, availability, photos and exact verified facts;
- call, message or open the provider's own booking site;
- report stale, misleading or illegal content without registration.

### Provider

- one editable public profile with several services and service areas;
- verified registry/licence facts where an official source exists;
- direct contacts remain theirs;
- aggregate impressions, profile views and contact clicks;
- profile-expiry reminders and a clear moderation status.

### Staff

- review queue with revision diff;
- duplicate detection/merge, verification history and audit log;
- taxonomy, locality and SEO-page controls;
- reports, stale-profile queue and funnel/zero-result dashboards.

## MVP includes

Anonymous discovery, public provider pages, direct tracked contacts, provider onboarding/editing, staff moderation, factual verification, media, i18n-ready URLs, SEO, accessibility, metrics, backups and incident-ready operations.

## Explicitly deferred

Reviews/ratings, user accounts, favourites, chat, leads, requests, quotes, booking, payments, subscriptions, native app, national rollout and automated AI moderation.

## Critical risks

| Risk | Countermeasure |
|---|---|
| Empty results | Recruit manually; do not index a landing page below its supply threshold. |
| Stale/fake profiles | Moderation, official-source checks, owner re-confirmation, reports. |
| Weak attribution | Track aggregate contact clicks and ask providers about genuine enquiries. |
| Commodity directory | Win on language + verified facts + local density + Finrix distribution. |
| Trust liability | Describe exact checks; never endorse quality or licensing implicitly. |
| Small ceiling | Prove the niche first; keep locale/taxonomy architecture expandable. |

## Beta gates

Before public launch:

- 50 published providers;
- at least 5 providers in each of the 8 priority categories across the Helsinki–Espoo–Vantaa launch metro, with each category serving at least two launch cities;
- 100% published profiles manually reviewed and owner-confirmed;
- no indexed zero-result/thin page.

Thirty days after launch, continue only if:

- at least 300 Finland-based discovery sessions;
- at least 10% of search sessions produce a contact click;
- no more than 20% of searches return zero results;
- at least 20 enquiries are confirmed as genuine by providers;
- at least 60% of sampled users say the catalog reduced search effort.

If traffic is low, test distribution before changing product. If traffic is adequate but contacts are low, fix density/trust/UX before adding features.

### Metric definitions

- `Discovery session`: non-bot public visit containing home, results, or profile view; an opaque first-party ID expires after 30 minutes of inactivity and is never joined to an account or fingerprint.
- `Finland-based`: Cloudflare country signal equals `FI`; retain only event/aggregate country, never IP. Local/CI use a deterministic fixture.
- `Search session`: a discovery session with at least one normalized search; contact conversion deduplicates `(session, provider, channel)` for 30 minutes.
- `Genuine enquiry`: distinct provider-confirmed customer enquiry attributable to a tracked contact, not a completed job.
- `Sampled users`: at least 20 non-provider, non-staff respondents recruited through more than one channel.
- Bot exclusion uses Cloudflare verified-bot data plus a versioned user-agent list; the applied rule version is recorded with aggregates.
