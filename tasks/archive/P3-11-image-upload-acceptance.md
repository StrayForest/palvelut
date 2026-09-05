# P3-11 — Image upload safety acceptance

## Scope

Close the active P3 acceptance requirement that untrusted, bomb and spoofed images fail while accepted images are re-encoded and metadata-free, following the image security contract in `docs/06-quality.md`.

## Completed

- Added byte-signature and PNG structure validation before any provider image is staged.
- PNG critical chunks and CRCs are validated; malformed, trailing/polyglot and unsupported critical data is rejected.
- Added a 25,000,000-pixel limit and a 100 MiB decoded-size ceiling before inflation, with bounded decompression to reject image bombs.
- Accepted PNG image data is inflated and canonically re-encoded before storage rather than preserving uploaded bytes.
- Ancillary metadata is discarded during re-encoding; only image-semantic palette/transparency data is retained where required.
- Decoded width and height are recorded in the moderated media payload instead of trusting client metadata.
- Spoofed image uploads fail before a `ProfileRevision` or staged media object is created.
- Added regression coverage for metadata removal/re-encoding, spoofed/trailing payloads, pixel bombs and sanitized staged bytes.
- The existing structured-provider media test now uses a valid decoded PNG fixture.

## Verification

- Implementation exact-head `aca6d23f6d412957dbeeebe8fb4a3214e7694b6f` passed Compose CI `33951740537`, including lint/format, type check, dependency/secret checks, build/bootstrap, migrations/deploy checks, canonical non-browser tests, browser gate, Playwright evidence and disposable smoke gate.
- Final closeout exact-head must pass the same Compose workflow after this archive/update commit.

## Remaining

- Next active P3 acceptance item is analytics privacy/definition visibility.
