# P4-07 — Badge wording acceptance

Completed the next active P4 acceptance criterion: public verification wording cannot imply service quality or an unchecked licence/professional right.

## What was verified

- P4-03 already introduced factual public labels in the form `fact in official source · checked YYYY-MM-DD` rather than a generic trust badge.
- The public trust explanation explicitly says verification labels do not rate service quality and do not imply an unchecked licence.
- The trust page separately states that a verification label does not prove any licence or professional right that is not named in the label.
- The existing regression `PublicTrustTests.test_public_fact_names_exact_fact_source_and_check_date` pins the exact factual Y-tunnus label and rejects the generic `Verified professional` wording.
- The existing regression `PublicTrustTests.test_profile_and_trust_page_explain_fact_only_semantics` verifies the public profile/trust surfaces expose the narrow fact-only semantics.
- The regulated `professional_right` registry type remains disabled pending its separate legal/source review, so an unchecked professional-right claim cannot become a public verification fact.
- No new verification implementation was added for this acceptance closeout, avoiding duplication of the already archived P4-02/P4-03 work.

## Evidence

- P4-03 implementation exact head: `744d90e4a759cdb841c3263042b559a43977cc99`.
- GitHub Actions `Compose stack` run `33960076779`: PASS on that exact implementation head.
- P4-03 archive: `tasks/archive/P4-03-public-trust-labels-recheck.md` documents the label semantics and deterministic public-surface tests.
- P4-02 archive: `tasks/archive/P4-02-registry-check-types.md` documents that regulated professional-right verification is disabled until legal/source review.
- This documentation closeout must pass the repository Compose workflow on its exact PR head before merge.

## Remaining

- The next active P4 acceptance criterion is the content-report acceptance: reports must be rate-limited, acknowledged and auditable without exposing reporter data.
