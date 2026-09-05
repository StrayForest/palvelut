# P3-02 — Provider claim flow

## Scope

Claim an existing unclaimed provider draft using independent business-control evidence and staff approval. Possession of the provider account email alone is not sufficient proof of control.

## Completed

- Added authenticated provider claim discovery and submission routes for existing unclaimed drafts.
- Claims accept only explicit independent evidence classes: registry signatory evidence, matching business-domain email evidence, or an equivalent case requiring staff review.
- Claim submission moves only `claim_status` to `pending`; it does not create a membership and does not make the provider public.
- A competing claim cannot replace an already pending claim.
- Staff claim review is under the MFA-protected `/palvelut/staff/` surface.
- Staff approval is transactional: it records review metadata, sets the claim to approved, creates the claimant as the active owner, and moves the provider only to `draft`.
- Staff rejection records the decision and leaves the provider unclaimed with no membership.
- Claim submit/approve/reject actions create provider audit events.
- Added regression coverage for insufficient evidence, pending-claim contention, approval, rejection, staff authorization and MFA-protected review.

## Verification

- Implementation exact-head `a71c949d9cf8d3fec66179cd7cc2898831dc3f84` passed Compose CI `33936909340`, including lint/format, type check, dependency/secret scans, migrations, canonical non-browser tests, browser gate and disposable smoke gate.
- Final closeout exact-head must pass the same Compose workflow after this archive/update commit.

## Remaining

- Next active P3 build item is onboarding, draft autosave, preview, submit, corrections and live-profile revision flow.
