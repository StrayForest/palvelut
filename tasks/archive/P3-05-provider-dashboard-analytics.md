# P3-05 — Provider dashboard analytics

## Scope

Add provider workspace status/checklist visibility and aggregate impressions, profile views and contact clicks while keeping public analytics anonymous/minimal and counting cached anonymous discovery responses.

## Completed

- Added provider workspace dashboard cards with lifecycle/revision status and a six-part onboarding checklist covering identity, service, service area, language, public contact and image.
- Added provider-level `impression` and `profile_view` analytics events alongside the existing structured contact-click event; non-contact events carry no channel value.
- Instrumented anonymous search/city-category result cards and provider profiles after cache resolution, so cache hits are counted while authenticated reads are excluded.
- Kept events limited to provider, event kind, optional contact channel and timestamp; no visitor ID, IP, search text or cross-site identifier is stored.
- Added provider-scoped aggregate counts for impressions, profile views and contact clicks to the authenticated workspace, which remains `private, no-store`.
- Added regression coverage for cached anonymous event counting, authenticated exclusion, checklist completion and cross-provider metric isolation.

## Verification

- Implementation exact-head `785402de1b5a2990e5746548b800b6ca090c2bf7` passed Compose CI `33941526438`, including lint/format, mypy, dependency/secret checks, reproducible builds, migrations, Django tests, browser evidence and disposable smoke.
- Final closeout exact-head must pass the same Compose workflow after this archive/update commit.

## Remaining

- Next active P3 build item is ownership transfer/invite foundation for business teams; only owner/editor roles now.
