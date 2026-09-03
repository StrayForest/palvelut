# P0-12 — JSON logs and request IDs

Completed: 2026-09-03
Commit/PR: implementation `516c126d1471dad6fd43cbfe7656ed7291d8a01c`; PR #15

## Scope

- Added per-request IDs generated at the application boundary and exposed as `X-Request-ID` response headers.
- Bound the current request ID through a context variable so application log records can include request correlation without passing IDs through function signatures.
- Added a stdlib JSON formatter with UTC timestamp, level, logger, message, request ID and optional request fields.
- Added one structured request-completion event containing method, path, status and duration without query strings.
- Configured Django/application console logging to emit JSON and inject request IDs through a logging filter.
- Added focused contract tests for response IDs, uniqueness, formatter output and logging/middleware wiring.

## Checks

- GitHub Actions run `33725204403` on implementation head `516c126d1471dad6fd43cbfe7656ed7291d8a01c` — PASS.
- Dependency/command contract step — PASS.
- `make test` — PASS.
- `make e2e` — PASS.
- `make smoke` — PASS.

## Deviations

- No external structured-logging package was added; the implementation uses Python stdlib logging and JSON support.
