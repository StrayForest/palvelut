# P5-08 — Exact image promotion acceptance

Status: completed.

## Scope

Accept the production delivery contract that the exact tested application image is promoted from staging to production without rebuilding or retagging it between environments.

## Implemented

- Added `.github/workflows/p5-promote.yml` as the manual release-promotion entry point.
- Promotion requires an immutable `ghcr.io/strayforest/palvelut@sha256:<digest>` and the full 40-character source commit SHA.
- Staging deploys first through the existing blue/green deploy script; production is blocked on successful staging and receives the same workflow inputs.
- Staging and production use separate GitHub environments and environment-scoped SSH credentials.
- Promotion concurrency is serialized and cannot cancel an in-flight release.
- The promotion workflow contains no image build, tag, push, or `latest` path.
- Added `tests/test_p5_release_promotion_contract.py` to lock the same-digest/no-rebuild contract.

## Verification

Implementation head `bbfb8aed975ba45fb4f6610c4e023dc03f1287c6`:

- GitHub Actions `Compose stack` run `33999025062`: PASS.
- Dependency/command contracts, lint/format, type check, dependency audit, secret scan, reproducible static build, application container build, migrations, Django deploy checks, provider security/integration, canonical non-browser tests, browser gate and disposable smoke all passed.

The workflow itself is intentionally `workflow_dispatch`: a real release needs configured `staging` and `production` GitHub environments and their deployment secrets. The acceptance proven here is that one already-built immutable digest/source SHA pair is the only release coordinate carried through both deployment jobs; no rebuild exists in the promotion path.
