# P1-12 — Duplicate identity determinism

## Scope

Close the P1 acceptance criterion that duplicate Y-tunnus/contact/slug cases are deterministic without adding public browse or provider self-service.

## Completed

- Kept Y-tunnus import deterministic and idempotent through the existing nonblank database uniqueness constraint and `update_or_create` import path.
- Verified duplicate-provider merge always chooses the oldest provider by `created_at`, then `id`, as canonical.
- Added regression coverage proving an identical contact on both duplicate providers collapses to one canonical contact during merge.
- Added `ProviderSlug` under the publishing module with globally unique slugs and at most one current slug per provider.
- Added transactional stable-slug creation using normalized display name plus provider UUID, so equal display names never depend on race/order for uniqueness.
- Publish now creates the provider slug once; repeated slug resolution returns the existing current slug.

## Verification

- Exact implementation head `ce794029031ea65ccbfa1c86ff57b16c5ec0629f` passed Compose stack run `33841377704`.
- Passed bootstrap/contracts, Ruff lint/format, mypy, dependency audit, secret scan, reproducible build, migrations, Django deploy checks, canonical non-browser tests, browser/Playwright evidence and disposable smoke.

## Remaining

Only the still-active P1 acceptance criteria and gates remain in `tasks/P1-domain.md`.
