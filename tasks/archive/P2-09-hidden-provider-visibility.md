# P2-09 — Hidden provider visibility

Status: complete.

## Scope

Close the next unfinished P2 acceptance item only: prove that unpublished and suspended providers never appear in public HTML, structured schema, sitemap or application cache.

## Completed

- Added a focused regression fixture with both draft and suspended providers that deliberately have approved read documents, active services, launch geography and current public slugs.
- Verified search HTML and city/category landing HTML never expose either hidden provider.
- Verified repeated cached discovery responses still exclude hidden providers.
- Verified the sitemap never contains hidden provider slugs.
- Verified hidden profile routes return 404 and cannot emit `LocalBusiness` structured data, including repeated requests.
- No later P2 acceptance/gate work and no P3 functionality was started.

## Verification

Implementation head `825acc104d6a7e406cd39bbf2dd83acef21c6f90` passed Compose CI `33923939550` with all job steps successful, including lint/format, mypy, dependency audit, secret scan, builds, migrations, canonical non-browser tests, browser gate, retained Playwright evidence and disposable smoke.

PR: #82.
