# P1-12 — Verification audit history

## Scope

Close the P1 acceptance criterion requiring every moderation/verification change to have an actor and timestamp, without expanding into public browse or provider self-service.

## Completed

- Added immutable `VerificationEvent` history for verification status transitions.
- Every verification event records the authenticated staff actor and creation timestamp.
- Added a transactional staff-only verification status-change service with row locking.
- Moderation changes continue to be recorded through the existing audit event path with actor/timestamp metadata.
- Added regression coverage for event actor/timestamp persistence and rejection of non-staff verification changes.
- Renamed the event relation to `verification_check` to avoid collision with Django's `Model.check()` system-check API.

## Verification

- Exact implementation PR head `c08e59aff92ac09615ad7bf885deec82b227b8da` passed the full Compose stack workflow in run `33844602413`.
- PR #57 was squash-merged into `main` as `c159093160a11a9296f13d0ef569ccb9b8ebac39`.

## Remaining

Only the still-active P1 acceptance criterion and gates remain in `tasks/P1-domain.md`.
