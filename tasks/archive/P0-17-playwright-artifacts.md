# P0-17 — Playwright evidence artifacts

Completed: 2026-09-03
Commit/PR: implementation `1940d273272ebbd45e2391a88cdbec10127f22bc`; PR #20

## Scope

- Generate a Playwright HTML report for the canonical browser gate.
- Persist Playwright output outside the disposable e2e container so CI can retain it after teardown.
- Capture screenshots and traces on browser-test failure.
- Persist browser console and page-error output as `console.log` on failed tests and attach it to Playwright results.
- Upload `playwright-report` and `test-results` from GitHub Actions even when the browser gate fails.
- Pin `actions/upload-artifact` to a full commit SHA and add a repository contract for the artifact configuration.

## Checks

- Workflow/security artifact contract — PASS.
- GitHub Actions run `33752010180` on implementation head `1940d273272ebbd45e2391a88cdbec10127f22bc` — PASS.
- Lint/format, type check, dependency audit and secret scan — PASS.
- Frontend and application container builds — PASS.
- Fresh PostgreSQL/Valkey startup, migrations and `manage.py check --deploy` — PASS.
- `make test`, `make e2e`, `make smoke` — PASS.
- Retained artifact `9891990747`, `playwright-evidence-33752010180-1`, digest `sha256:1758adacb0835b7ceff01c0522a68e8b3387b7b1a4e1945d753c082bee12ba94` — PASS.

## Deviations

- Failure-only screenshots, traces and console logs are naturally absent from a successful browser run; the HTML report is retained on every run and the same artifact collects failure evidence when present.
