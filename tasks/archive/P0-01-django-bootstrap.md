# P0-01 — Django bootstrap

Completed: 2026-09-02
Commit/PR: implementation `5f1248dbc11d333629743b251919c24ab1920a80`; PR #4

## Scope

- Added the Python 3.13 project contract and `.python-version`.
- Added Django 5.2 LTS dependency management with `uv`; the lock resolves Django 5.2.17 plus its Linux runtime dependencies.
- Added the Django project skeleton with ASGI/WSGI entry points and bootstrap settings.
- Added app packages matching all nine domain modules in `docs/05-architecture.md`: accounts, taxonomy, providers, publishing, verification, moderation, discovery, analytics and content.
- Added bootstrap contract tests. PostgreSQL/database wiring remains active in the next P0 step.

## Checks

- `python -m compileall -q manage.py palvelut tests` — PASS.
- `python -m unittest -v tests.test_bootstrap_contract` — PASS (2 tests).
- `uv lock --offline --locked` — PASS on Python 3.13.5 / uv 0.10.0.

## Deviations

- The execution sandbox had no DNS access to PyPI, so package download/runtime Django checks were not used as a scoped completion gate. Stage-level runtime, migration and deploy checks remain active in `tasks/P0-foundation.md` and are not claimed complete here.
