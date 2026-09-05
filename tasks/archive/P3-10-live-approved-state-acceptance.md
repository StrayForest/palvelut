# P3-10 — Live approved state acceptance

## Scope

Prove that a published provider keeps exposing the last approved public read state while a newer profile revision is pending moderation.

## Completed

- Verified the existing revision flow leaves the published provider state unchanged while newer edits are pending moderation.
- Added public-boundary regression coverage proving `ProviderReadDocument` remains bound to the approved revision instead of the pending revision.
- Verified public search and the public provider profile continue to render the approved display name and approved copy while the pending payload remains private.
- Reused the existing moderated revision/read-model architecture; no new product behavior or publication bypass was added.

## Verification

- Implementation exact-head `3d8fbcea6eb3c558e2a9e2920c877e55e6e358e0` passed Compose CI `33950130580`, all 24 steps including lint/format, mypy, dependency/secret checks, reproducible builds, canonical startup, migrations, Django tests, browser gate, evidence upload and disposable smoke.
- Final closeout exact-head must pass the same Compose workflow after this archive/update commit.

## Remaining

- Next active P3 item is acceptance: untrusted/bomb/spoofed images fail; accepted images are re-encoded and metadata-free.
