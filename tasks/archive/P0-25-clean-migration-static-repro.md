# P0-25 — Clean migration and reproducible static build

Completed: 2026-09-03
PR: #29

## Scope

- Kept the existing fresh isolated PostgreSQL proof and explicit `makemigrations --check --dry-run` + `migrate --noinput` sequence.
- Added an exact-head CI gate that performs two independent `--no-cache` frontend builds.
- Exported `/frontend-dist` from each build and compared the resulting static trees byte-for-byte with `diff -ruN`.
- Added regression coverage requiring the fresh-database migration ordering and static reproducibility gate.

## Checks

- GitHub Actions run `33782049888` on implementation head `b230c8b6f9c80ed48670bf1225b622f16b72cc32` — PASS.
- Reproducible static build — PASS.
- Fresh isolated PostgreSQL/Valkey startup and migration drift/apply — PASS.
- Dependency contracts, lint/format, types, dependency audit, secret scan and deploy checks — PASS.
- `make test`, `make e2e`, Playwright evidence upload and `make smoke` — PASS.

## Deviations

- None.
