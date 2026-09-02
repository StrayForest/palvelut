# P0 — Foundation

Read: `DECISIONS.md`, `docs/05-architecture.md`, `docs/06-quality.md`, `docs/07-operations.md`.

## Build

- Bootstrap Python 3.13/Django 5.2 LTS with `uv` lock and apps matching domain modules.
- Add PostgreSQL 18, Valkey 8.x, worker, Nginx and local mail/object-storage substitutes through Compose.
- Add project-scoped `make dev`, `make test`, `make e2e` and `make reset`; CI must call the same targets.
- Add Tailwind build, HTMX, minimal Alpine.js, RU/FI/EN i18n skeleton and accessible base layout.
- Add environment validation, `/health/live`, `/health/ready`, JSON logs and request IDs.
- Add Playwright coverage for the base page at 360px and 1440px, keyboard focus and browser-console errors.
- Add CI for lint, format, types, tests, migrations, `check --deploy`, dependency/secret scan, frontend build, container build and Playwright.
- Run CI with fresh pinned PostgreSQL 18 and Valkey 8.x services; it must not access staging, production, SSH or persistent external infrastructure.
- Retain the Playwright HTML report and failure screenshots, traces and console logs as GitHub Actions artifacts.
- Add `.env.example`; no real credentials.

## Accept

- `make dev` starts the complete clean local environment without a separately provisioned server.
- `make test` runs every non-browser P0 gate; `make e2e` runs the browser gate.
- `make reset` rebuilds only this project's disposable local state and refuses production-like settings.
- The same targets pass in GitHub Actions with no persistent external dependency.
- A clean database migrates; static build is reproducible.
- Readiness fails when required database/cache dependencies fail; liveness does not.
- Production settings fail closed for missing secrets/hosts/HTTPS assumptions.
- Base page works at 360px and 1440px with keyboard focus and no console error.

## Gates

`make test`, `make e2e`, clean-state Compose smoke, migration drift check, `manage.py check --deploy`, secret/dependency scan and artifact-presence check.

Do not build business features.
