# P2-12 — Visual acceptance

## Scope

Close only the responsive visual-evidence acceptance requirement from `tasks/P2-discovery.md`. The remaining P2 gates stay active.

## Completed

- Added the documented provider CTA state to the public home surface without inventing a live onboarding destination before that flow exists.
- Materialized deterministic synthetic browser evidence through the normal publishing contract: approved revision → current slug → `ProviderReadDocument`.
- Retained full-page home, results, empty, profile and provider-CTA screenshots at 360, 768 and 1440px.
- Browser acceptance checks horizontal overflow at every required width, keeps the mobile search surface above the initial fold and verifies visible keyboard focus on the real search action.
- Fresh review of all retained screenshots confirmed stable hierarchy, responsive layout, readable text and visible focus treatment.

## Verification

- Implementation exact-head `17e770d7603eba0c22f6aa37909892beb4ebd0a6` passed Compose CI `33930524351`, including the canonical browser gate, Playwright evidence upload and disposable smoke gate.
- Evidence artifact `playwright-evidence-33930524351-1` contains the 15 named P2 screenshots and is retained by the existing CI artifact policy.
- Final closeout exact-head must pass the same Compose workflow before merge.

## Remaining

- The P2 Gates section remains active in `tasks/P2-discovery.md`; this closeout does not claim those gates complete.
