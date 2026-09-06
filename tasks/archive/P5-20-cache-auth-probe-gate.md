# P5-20 — Cache/auth probe gate

Status: completed.

## Scope

Close the P5 cache/auth probe gate without duplicating the already-completed authenticated CDN cache acceptance.

## Evidence

- `P5-10` already hardened `infra/cloudflare/rules.json` so requests carrying `Authorization` or cookies hit the higher-priority cache-bypass rule, while anonymous public GET/HEAD traffic may remain cache eligible.
- `tests/test_p5_authenticated_cache_contract.py` deterministically checks rule priority, bypass action, authenticated/cookie predicates, anonymous eligibility and protected account/staff/report paths.
- The canonical Compose-stack CI runs the repository test suite against the exact PR head, so this gate is satisfied by re-running that existing contract rather than adding a duplicate probe implementation.

## Verification

- Full `Compose stack` CI must pass on the exact documentation head before merge.
