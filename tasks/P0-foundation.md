# P0 — Foundation

Read: `DECISIONS.md`, `docs/05-architecture.md`, `docs/06-quality.md`, `docs/07-operations.md`.

## Build

- Add CI for lint, format, types, tests, migrations, `check --deploy`, dependency/secret scan, frontend build, container build and Playwright.
- Set workflow default permissions to `contents: read`; pin third-party actions to full commit SHAs and service/build images to immutable digests with version comments.
- Run CI with fresh pinned PostgreSQL 18 and Valkey 8.x services; it must not access staging, production, SSH or persistent external infrastructure.
- Retain the Playwright HTML report and failure screenshots, traces and console logs as GitHub Actions artifacts.
- Add `.env.example`; no real credentials.

## Accept

- `make dev` starts the complete clean local environment without a separately provisioned server.
- `make bootstrap` prepares a new Linux/WSL2 checkout without global project dependencies beyond Git, Make and Docker.
- `make test` runs every non-browser P0 gate; `make e2e` runs the browser gate.
- `make smoke` starts disposable services, verifies liveness/readiness and shuts them down.
- `make reset` rebuilds only this project's disposable local state and refuses production-like settings.
- `make test`, `make e2e` and `make smoke` pass in GitHub Actions with no persistent external dependency; CI never calls `dev`, `reset` or seed targets.
- A clean database migrates; static build is reproducible.
- GitHub check names are stable and `main` protection/ruleset is enabled after their first green run.

## Gates

`make test`, `make e2e`, `make smoke`, migration drift check, `manage.py check --deploy`, secret/dependency scan, workflow pin/permission check and artifact-presence check.

Do not build business features.
