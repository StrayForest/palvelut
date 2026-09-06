# P5-10 — Authenticated CDN cache acceptance

Status: completed.

## Scope

Accept that authenticated/stateful traffic cannot become CDN-cache eligible while anonymous public GET/HEAD traffic may still follow origin cache policy.

## Implemented

- Hardened `infra/cloudflare/rules.json` so any request carrying an `Authorization` header explicitly matches the higher-priority cache-bypass rule.
- Kept the existing cookie-based bypass, which covers Django session authentication and any other stateful cookie traffic.
- Tightened the anonymous cache-eligible rule so it requires both an empty `Authorization` header and no cookies.
- Protected account, staff and report paths remain excluded independently of authentication state.
- Added `tests/test_p5_authenticated_cache_contract.py` to lock rule priority, bypass action, authorization/cookie predicates and protected-path exclusions.

## Verification

- The repository contract test proves authenticated request markers are present only on the bypass side and explicitly absent from the cache-eligible side.
- Full Compose-stack CI is required before merge.

This acceptance is intentionally configuration-level: applying the Cloudflare rules to the production zone remains part of the production-config gate. The repository can prove the deployed rule contract, but it does not embed Cloudflare API credentials or mutate the live zone from pull-request CI.
