# P4-04 — Anonymous content report workflow

Completed the active P4 build step: anonymous content reports now enter a staff moderation case workflow with provider notices plus a provider-visible appeal/status trail.

## What changed

- Added an anonymous public report form from provider profiles; the flow does not require or persist reporter account identity.
- Added opaque public report-status tokens and persist only their SHA-256 hashes, so the raw status token is not stored in the database.
- Extended the existing moderation case/event model rather than creating a parallel moderation system; anonymous report intake can use null actors while staff/provider actions retain real actors.
- Added staff moderation case list/detail surfaces with provider notices plus resolve/dismiss actions and auditable case events.
- Added provider-scoped case/status surfaces and appeal submission; active membership is required and cross-provider access is denied.
- Added regression coverage for anonymous intake/status, token hashing, staff notice/resolution audit, provider appeal authorization and the public/provider/staff surfaces.
- Kept report rate limiting and the remaining P4 acceptance/gate work active; this closeout covers only the completed Build item and does not duplicate P4-01/P4-02/P4-03.

## Evidence

- Implementation exact head: `6b2a65f117c2515f3cba7c7f6a82be41a807a75f`.
- GitHub Actions `Compose stack` run `33961678350`: PASS on the exact implementation head, including lint/format, type check, dependency/secret scans, migrations, P3 security/integration, non-browser/browser gates, Playwright evidence and disposable smoke.

## Deviations

None.
