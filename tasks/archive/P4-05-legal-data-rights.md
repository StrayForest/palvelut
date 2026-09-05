# P4-05 — Legal templates and data rights workflow

Completed the active P4 build step: public privacy/terms/cookies/accessibility draft surfaces exist and signed-in providers can submit access/export/delete requests into an MFA-protected, auditable staff workflow.

## What changed

- Added public `/palvelut/{locale}/legal/{privacy,terms,cookies,accessibility}/` surfaces and shared footer links.
- Legal surfaces are explicitly draft and `noindex` until the separate owner/legal acceptance review completes; controller/contact placeholders are not presented as approved facts.
- Added `DataSubjectRequest` for access, export and delete requests with explicit open/in-progress/completed/rejected states.
- Added append-only `DataSubjectRequestEvent` history for requester submission and staff processing actions.
- Added authenticated provider submission/history at `/palvelut/account/data-rights/` with private/no-store caching.
- Added MFA-protected staff queue/detail processing at `/palvelut/staff/data-rights/`.
- Completion records a reviewed workflow outcome and deliberately does not automatically delete the account; destructive deletion remains a controlled action after retention/legal checks.
- Added deterministic regression coverage for public draft legal pages, request creation/history, staff isolation, MFA-protected transitions, closed-request immutability and cache policy.

## Evidence

- Implementation exact head: `5badf621d92ef9df3e7a8acefb9ff4e5184f08fc`.
- GitHub Actions `Compose stack` run `33963880292`: PASS on the exact implementation head, including bootstrap/contracts, lint/format, type check, dependency/secret scans, reproducible frontend/application builds, clean migrations, Django deploy checks, provider security/integration gate, canonical non-browser/browser gates, evidence upload and disposable smoke.

## Deviations

- Local clone-based checks were unavailable in the automation execution container because outbound DNS to GitHub was unavailable. The repository's canonical GitHub Actions Compose gate ran and passed on the exact implementation head.
