# Experience and structure

## Information architecture

```text
/{locale}/
├── services/{category}/
├── {city}/{category}/
├── professionals/{provider-slug}/
├── for-professionals/
├── trust/
├── legal/{privacy,terms,cookies,accessibility}/
├── report/{provider}/
└── account/{login,onboarding,profile,analytics}/
```

Only `/{city}/{category}/` pages meeting the supply/content threshold are indexed. Arbitrary search/filter URLs are canonicalized or `noindex,follow`.

## Public journey

1. Home asks only `What service?` and `Where?`; Russian is implicit in the promise.
2. Results expose provider count, active filters and honest empty states.
3. Cards make comparison possible without opening every profile.
4. Profile explains services, price model, areas, languages, exact checks and recency.
5. Contact buttons open the provider's phone, WhatsApp, Telegram, email, site or booking page.

No public action requires an account.

## Result card

- portrait/logo and provider name;
- category and city/service area;
- spoken languages;
- price from/range or `price on request`;
- up to two factual verification labels;
- last owner confirmation date;
- short differentiator;
- primary `View profile` and direct contact action.

Default ranking: category/city relevance → language match → verified facts → profile completeness → freshness → stable rotation. Paid placement is absent from MVP and must later be labelled `Sponsored` without removing organic alternatives.

## Provider profile

Header: identity, main service, service area, languages, last checked. Sticky mobile contact bar. Sections: services/prices, about, work photos, availability, service areas/modes, verification facts, company details, contacts, report link.

Never show a generic `Verified professional` badge. Examples: `Y-tunnus found in YTJ · checked 2026-09-02` or `Professional right found in JulkiTerhikki · checked …`.

## Provider onboarding

1. Verify email and accept provider terms.
2. Choose individual/company; enter Y-tunnus when applicable.
3. Add category, cities, remote/on-site mode and languages.
4. Add public identity, description, prices, photos and contacts.
5. Preview exact public page.
6. Submit immutable revision for staff review.
7. Publish or return structured corrections.

Edits to a live profile create a pending revision; the current approved version remains public.

## Empty states

- Offer nearby city/category alternatives that actually have supply.
- Offer a simple optional search-gap form; never promise a provider response.
- Record `zero_results` with normalized category/city, not free-text personal data.

## Staff workflow

Queue → revision diff → official-source checks → preview → approve/reject with reason → audit event → cache/SEO invalidation. Reports and stale profiles use the same case system.
