# Repository instructions

## Read order

1. Read the current file in `tasks/`.
2. Read `DECISIONS.md`.
3. Read only the docs linked by the current task.
4. Inspect relevant code and tests; do not preload the whole repository.

## Product boundaries

- This is a directory with direct contact. Do not add requests, chat, booking, escrow, service payments, commissions, leads, or native apps.
- Public search is anonymous. Accounts are for providers and staff only.
- Do not publish star ratings in MVP.
- A verification badge states the exact fact checked, source, and date. It never means service quality.
- Launch scope is Helsinki, Espoo, and Vantaa. New regions require a product decision.

## Engineering rules

- Build a modular monolith. Modules communicate through explicit service functions, not cross-module model writes.
- Server-render useful HTML first; HTMX may enhance it. Core browse/contact flows must work without JavaScript.
- Keep public URLs, structured data, cache policy, analytics events, and authorization covered by tests.
- Public content is cacheable; authenticated and staff responses are `private, no-store`.
- Normalize and validate all external contact targets server-side; never implement an open redirect.
- Uploads are untrusted: constrain type/size, decode and re-encode images, strip metadata, and store outside the app origin.
- New runtime dependencies or changes to product boundaries need a short entry in `DECISIONS.md`.
- UI text is localized; code, identifiers, logs, and technical docs are English. Product docs may be Russian.
- Never claim completion without running the gates in the current task and reporting exact failures.

## Local and CI contract

- Canonical targets are `make dev`, `make test`, `make e2e`, `make reset`, and, from P1 onward, `make seed-demo`; document them and make CI call the same targets.
- Every P0–P4 completion gate must run locally and in GitHub Actions without staging, production, SSH, or persistent external infrastructure. Use pinned disposable services and deterministic fakes/fixtures.
- CI starts fresh PostgreSQL 18 and Valkey 8.x state for each run; no shared database, cache, credentials, or production data.
- Browser CI retains its HTML report and failure screenshots, traces, and console logs as GitHub Actions artifacts.
- Local reset/seed commands must be project-scoped and refuse production-like settings.

## Change discipline

- One roadmap stage per branch/PR.
- Preserve unrelated changes.
- Update docs only when a decision or contract changed.
- Prefer deletion or deferral over speculative abstractions.
