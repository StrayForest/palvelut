# P0-15 — Workflow permissions and immutable pins

Completed: 2026-09-03
Commit/PR: implementation `512b576c76abce98f1c572b9d2aa8ba0f72688e4`; PR #18

## Scope

- Kept workflow default permissions at `contents: read`.
- Added a repository contract requiring third-party workflow actions to use full commit SHAs.
- Added regression coverage requiring Compose service images to use immutable SHA-256 digests with adjacent version comments.
- Extended immutable base-image coverage to every `FROM` in both `Dockerfile` and `Dockerfile.e2e`.
- Added the security contract to the early CI contract gate.

## Checks

- Workflow security contract — PASS.
- GitHub Actions run `33740954730` on implementation head `512b576c76abce98f1c572b9d2aa8ba0f72688e4` — PASS.
- Lint/format, type check, dependency audit and secret scan — PASS.
- Frontend and application container builds — PASS.
- Migration drift/apply and `manage.py check --deploy` — PASS.
- `make test`, `make e2e`, `make smoke` — PASS.

## Deviations

- The current workflow uses no third-party `uses:` actions; the contract enforces full-SHA pinning if one is introduced later.
- Service and build images were already digest-pinned before this step; this step makes that requirement explicit and regression-tested.
