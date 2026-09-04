# P2-08 — Progressive discovery flow

Status: complete.

## Scope

Close the next unfinished P2 acceptance item only: prove that the core discovery flow works without JavaScript and that HTMX preserves URL/history/focus.

## Completed

- Kept discovery filters as a normal GET form so search/filter submission remains usable with JavaScript disabled.
- Progressively enhanced the same form with HTMX so only the discovery results region is replaced and the submitted query is pushed into browser history.
- Added stable IDs to discovery controls so HTMX restores keyboard focus after a swap without pinning stale form values across history restoration.
- Added Playwright regressions for both JavaScript-disabled discovery and HTMX URL/history/focus behavior, including Back navigation restoring the prior query state.
- No later P2 acceptance/gate work and no P3 functionality was started.

## Verification

Implementation head `29a29242a67982f411a0a5f643aca8d05143ff7d` passed Compose CI `33921016917` with all job steps successful, including lint/format, mypy, dependency audit, secret scan, builds, migrations, canonical non-browser tests, browser gate, retained Playwright evidence and disposable smoke.

PR: #81.
