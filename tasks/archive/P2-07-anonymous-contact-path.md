# P2-07 — Anonymous discovery-to-contact path

Status: complete.

## Scope

Close the first unfinished P2 acceptance item only: prove that an anonymous user reaches a relevant provider and contact in no more than three actions.

## Completed

- Added a focused acceptance regression for the server-rendered anonymous journey.
- The path is fixed at three user actions after entering the discovery home: submit search → open the relevant provider profile → activate the structured contact link.
- The test verifies that each preceding response exposes the next actionable URL and that the final internal contact redirect resolves to the provider's stored public email destination.
- No later P2 acceptance/gate work and no P3 functionality was started.

## Verification

Implementation head `296d4e88fc6e0a8db84f1d63bfb8874ccc585ca7` passed Compose CI `33913995339` with all 24 job steps successful, including lint/format, mypy, dependency audit, secret scan, builds, migrations, canonical non-browser tests, browser gate, retained Playwright evidence and disposable smoke.

PR: #78.
