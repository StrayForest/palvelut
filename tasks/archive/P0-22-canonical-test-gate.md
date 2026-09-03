# P0-22 — Canonical non-browser and browser gates

Completed: 2026-09-03
Commit/PR: implementation `be5ba038e425729bfd33e29e00a403d5cd88b2ee`; PR #25

## Scope

- Changed `make test` from unit tests only into the canonical non-browser P0 gate while keeping host requirements limited to Git, Make and Docker/Compose.
- Added a digest-pinned Python 3.13 quality container that runs lock validation, Ruff lint, changed-file formatting, mypy, dependency audit, secret scan, migration drift, Django deploy checks and the complete unit/contract test suite.
- Kept source mounted read-only and redirected tool caches and generated audit files to `/tmp`.
- Kept `make e2e` as the canonical Playwright browser gate and retained the existing disposable `make smoke` gate.
- Added regression coverage for the quality service, command coverage and immutable quality-container base image.

## Checks

- GitHub Actions run `33769602781` on implementation head `be5ba038e425729bfd33e29e00a403d5cd88b2ee` — PASS.
- Canonical `make test` — PASS.
- Canonical `make e2e` and Playwright evidence upload — PASS.
- Canonical `make smoke` — PASS.
- Bootstrap, dependency/command contracts, lint/format, types, dependency audit, secret scan, frontend/application builds, development startup, PostgreSQL 18/Valkey 8 verification, migration apply and Django deploy checks — PASS.

## Verification history

- Earlier implementation runs exposed two runner integration issues: Ruff attempted to write cache data into the read-only source mount, and a full-repository format check surfaced pre-existing formatting debt outside this step.
- The runner now writes caches to `/tmp` and mirrors the existing P0 changed-file formatting contract rather than rewriting unrelated source files.

## Deviations

- None. Remaining P0 acceptance and stage-level gates stay active.
