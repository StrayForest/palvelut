# P0-01 — Django bootstrap

Completed: 2026-09-02
Commit/PR: implementation `5f1248dbc11d333629743b251919c24ab1920a80`; PR #4

## Scope

- Added the Python 3.13 project contract and `.python-version`.
- Added Django 5.2 LTS dependency management with `uv`; the `uv`-generated universal lock resolves Django 5.2.17, asgiref 3.12.1, sqlparse 0.6.0 and Windows-only tzdata 2026.3 with artifact hashes.
- Added the Django project skeleton with ASGI/WSGI entry points and bootstrap settings.
- Added app packages matching all nine domain modules in `docs/05-architecture.md`: accounts, taxonomy, providers, publishing, verification, moderation, discovery, analytics and content.
- Added bootstrap contract tests. PostgreSQL/database wiring remains active in the next P0 step.

## Checks

- `python -m compileall -q manage.py palvelut tests` — PASS.
- `python -m unittest -v tests.test_bootstrap_contract` — PASS (2 tests).
- GitHub Actions run `33682493702` on commit `5193b610eb04afb0607c8f1f86c2f7c1968ac930` — PASS on Ubuntu 24.04 / CPython 3.13.12 / uv 0.10.0.
- Runner `uv lock --refresh` generated the retained lock, then `uv sync --locked` installed Django 5.2.17 and runtime dependencies — PASS.
- Runner `.venv/bin/python manage.py check` — PASS, no issues.
- Runner `.venv/bin/python -m unittest -v tests.test_bootstrap_contract` — PASS (2 tests).

## Deviations

- None for this scoped bootstrap step. The local execution sandbox lacked PyPI DNS, so the networked install/runtime proof was reproduced on GitHub Actions instead. Stage-level database, migration, deploy, browser and production gates remain active in `tasks/P0-foundation.md`.
