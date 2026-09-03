# P0 — Foundation

Read: `DECISIONS.md`, `docs/05-architecture.md`, `docs/06-quality.md`, `docs/07-operations.md`.

## Build

- Retain the Playwright HTML report and failure screenshots, traces and console logs as GitHub Actions artifacts.
- Add `.env.example` containing placeholder configuration only.

## Accept

- `make dev` starts the complete clean local environment without a separately provisioned server.
- `make bootstrap` prepares a new Linux/WSL2 checkout without global project dependencies beyond Git, Make and Docker.
- `make test` runs every non-browser P0 gate; `make e2e` runs the browser gate.
- `make smoke` starts disposable services, verifies liveness/readiness and shuts them down.
- `make reset` rebuilds only this project's disposable local state and refuses production-like settings.
- A clean database migrates; static build is reproducible.
- GitHub check names are stable and `main` protection/ruleset is enabled after their first green run.

## Gates

`make test`, `make e2e`, `make smoke`, migration drift check, `manage.py check --deploy`, dependency/configuration scan, workflow pin/permission check and artifact-presence check.

Do not build business features.
