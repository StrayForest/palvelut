# P0-18 — Placeholder environment example

Completed: 2026-09-03
Commit/PR: implementation `c1ab9abca7ef8e7514ef7b2d46f00bfe33eabc39`; PR #21

## Scope

- Add `.env.example` covering the runtime configuration consumed by the current Django settings.
- Keep secret-bearing values explicit placeholders rather than usable credentials.
- Use reserved `example.invalid` hosts instead of the production domain.
- Add a repository contract that checks the expected variable set and rejects known local credentials or the production base URL.

## Checks

- `.env.example` configuration contract — PASS.
- GitHub Actions run `33756990404` on implementation head `c1ab9abca7ef8e7514ef7b2d46f00bfe33eabc39` — PASS.
- Lint/format, type check, dependency audit and secret scan — PASS.
- Frontend and application container builds — PASS.
- Fresh PostgreSQL/Valkey startup, migrations and `manage.py check --deploy` — PASS.
- `make test`, `make e2e`, `make smoke` — PASS.

## Deviations

- None.
