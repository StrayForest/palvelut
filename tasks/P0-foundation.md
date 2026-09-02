# P0 — Foundation

Read: `DECISIONS.md`, `docs/05-architecture.md`, `docs/06-quality.md`, `docs/07-operations.md`.

## Build

- Document Windows 11 setup through WSL2 + Docker Desktop integration; keep the command path identical to Linux.
- Add Tailwind build, HTMX, minimal Alpine.js, RU/FI/EN i18n skeleton and accessible base layout.
- Own local and production routes under `/palvelut/{locale}/` in Django's root URLconf; test prefix-preserving proxy behaviour, static URLs, redirects, cookies, canonical and hreflang generation.
- Add environment validation, `/palvelut/health/live`, `/palvelut/health/ready`, JSON logs and request IDs.
- Add Playwright coverage for the base page at 360px and 1440px, keyboard focus and browser-console errors.
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
- Readiness fails when required database/cache dependencies fail; liveness does not.
- Health responses expose no dependency detail, use `no-store`, and bypass CDN caching.
- Production settings fail closed for missing secrets/hosts/HTTPS assumptions.
- Base page works at 360px and 1440px with keyboard focus and no console error.
- GitHub check names are stable and `main` protection/ruleset is enabled after their first green run.

## Gates

`make test`, `make e2e`, `make smoke`, migration drift check, `manage.py check --deploy`, secret/dependency scan, workflow pin/permission check and artifact-presence check.

Do not build business features.
