# Experience and structure

## Information architecture

```text
/palvelut/ru/
├── services/{category}/
├── {city}/{category}/
├── professionals/{provider-slug}/
├── for-professionals/
├── trust/
├── legal/{privacy,terms,cookies,accessibility}/
├── report/{provider}/
└── account/{login,onboarding,profile,analytics}/
```

Canonical origin is `https://finrix.fi`; the Django app is mounted at `/palvelut`. `/palvelut/ru/` is the only supported public UI prefix in the MVP. FI/EN UI routes are unsupported. Only `/{city}/{category}/` pages inside the Russian public mount meeting the supply/content threshold are indexed. Arbitrary search/filter URLs are canonicalized or `noindex,follow`.

## Public journey

1. Home asks only `What service?` and `Where?`; Russian is implicit in the promise.
2. Results expose provider count, active filters and honest empty states.
3. Cards make comparison possible without opening every profile.
4. Profile explains services, price model, areas, provider spoken languages, exact checks and recency.
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

## Provider acquisition

The Russian home header and provider CTA expose a primary `Разместить карточку` action. It leads directly to provider registration. A specialist must not need to infer that an English `For professionals` or workspace link is the registration entry point.

## Provider onboarding

1. Register an account, verify email and explicitly accept the current provider terms.
2. Enter the minimum private legal identity needed to start: individual/company type, legal/display name and Y-tunnus when applicable.
3. For a new provider, create a non-public `unclaimed` provider record and submit independent control evidence. For an imported provider, select the existing non-public draft and submit the same claim evidence.
4. Staff reviews legal identity/control evidence. Only an approved ownership claim creates the active owner membership and unlocks the provider workspace; claim approval does not publish the profile.
5. Add category, cities, remote/on-site mode and provider spoken languages.
6. Add public description, prices, photos and contacts.
7. Preview the exact public page.
8. Submit an immutable profile revision for staff content/verification review.
9. Publish or return structured corrections. Edits to a live profile create a pending revision while the current approved version remains public.

All user-facing provider acquisition, registration, verification, claim, workspace, editing, preview and moderation-state surfaces are Russian-only.

A brand-new provider must be able to complete steps 1–3 without a staff-preseeded `Provider` row or direct database membership creation.

## Claim an existing draft

Imported records are never public. A provider signs in, selects the draft, and proves control through registry signatory evidence, a matching business-domain email, or staff-reviewed equivalent. Staff compares legal identity, records evidence metadata, approves/rejects, and audits every transition. Email possession alone never transfers ownership.

## Empty states

- Offer nearby city/category alternatives that actually have supply.
- Offer a simple optional search-gap form; never promise a provider response.
- Record `zero_results` with normalized category/city, not free-text personal data.

## Staff workflow

Queue → ownership/revision diff → official-source checks → preview → approve/reject with reason → audit event → cache/SEO invalidation. Reports and stale profiles use the same case system.
