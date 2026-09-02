# P0 — Foundation

Read: `DECISIONS.md`, `docs/05-architecture.md`, `docs/06-quality.md`, `docs/07-operations.md`.

## Build

- Bootstrap Python 3.13/Django 5.2 LTS with `uv` lock and apps matching domain modules.
- Add PostgreSQL 18, Valkey 8.x, worker, Nginx and local mail/object-storage substitutes through Compose.
- Add Tailwind build, HTMX, minimal Alpine.js, RU/FI/EN i18n skeleton and accessible base layout.
- Add environment validation, `/health/live`, `/health/ready`, JSON logs and request IDs.
- Add CI for lint, format, types, tests, migrations, `check --deploy`, dependency/secret scan, frontend build and container build.
- Add `.env.example`; no real credentials.

## Accept

- One command starts a clean local environment.
- A clean database migrates; static build is reproducible.
- Readiness fails when required database/cache dependencies fail; liveness does not.
- Production settings fail closed for missing secrets/hosts/HTTPS assumptions.
- Base page works at 360 and 1440px with keyboard focus and no console error.

## Gates

`ruff`, type check, `pytest`, migration drift check, `manage.py check --deploy`, asset build, Compose smoke, secret/dependency scan.

Do not build business features.
