# P0 — Foundation

Read: `DECISIONS.md`, `docs/05-architecture.md`, `docs/06-quality.md`, `docs/07-operations.md`.

## Build

## Accept

- `make test` runs every non-browser P0 gate; `make e2e` runs the browser gate.
- `make smoke` starts disposable services, verifies liveness/readiness and shuts them down.
- `make reset` rebuilds only this project's disposable local state and refuses production-like settings.
- A clean database migrates; static build is reproducible.

## Gates

`make test`, `make e2e`, `make smoke`, migration drift check, `manage.py check --deploy`, dependency/configuration scan, workflow pin/permission check and artifact-presence check.

Do not build business features.
