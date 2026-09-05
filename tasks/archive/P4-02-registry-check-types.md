# P4-02 — Extensible registry-check types

Completed the active P4 build step: verification checks now use an extensible registry contract, while regulated-category sources remain disabled until an explicit legal/source review exists.

## What changed

- Added a registry definition for verification kind, official source, provider subject field, adapter lookup method and enablement state.
- Routed the existing YTJ/PRH `business_identity` check through the generic registry contract without changing its bounded adapter or immutable-history behavior.
- Registered the future `professional_right` category as regulated and explicitly disabled; it cannot run or create a verification fact before a recorded legal/source review enables it.
- Added configuration guards preventing regulated checks from being enabled without a recorded review and preventing enabled checks without an adapter/subject/lookup contract.
- Added deterministic tests for the enabled business-identity path, unknown kinds, the disabled regulated path and the legal/source-review safeguard.
- Kept the already completed YTJ/PRH adapter work in `P4-01-ytj-prh-verification-adapter.md`; this closeout does not duplicate that earlier step.

## Evidence

- Implementation exact head: `1ceda5c425a8f583cc4fdc5235f6b6b6f7414971`.
- GitHub Actions `Compose stack` run `33958342835`: PASS on the exact implementation head, including lint/format, type check, security scans, migrations, non-browser tests, browser evidence and disposable smoke.

## Deviations

None.
