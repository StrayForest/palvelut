---
name: palvelut-build
description: Implement one bounded roadmap task or an explicitly requested foundation-contract correction in Finrix Palvelut. Use for feature, infrastructure, delivery, or corrective repository work; not for broad ideation or independent review.
---

# Palvelut build

Implement exactly one named `tasks/Px-*.md` stage, or one foundation correction explicitly requested by the user. A correction changes only affected decisions, docs, tasks and skills; it does not start product code.

1. Identify the exact stage or correction acceptance contract. Read `AGENTS.md`, `DECISIONS.md`, and only linked/affected files.
2. Inspect the affected code/tests and current git state. Preserve unrelated changes.
3. Restate the task boundary and identify the riskiest invariant before editing.
4. Implement the smallest complete result. For product code, keep domain writes behind module service functions.
5. For product code, add tests for observable behaviour, authorization, cache/SEO impact and relevant failure paths.
6. Run every named gate on the exact final head. For foundation corrections validate Markdown links, contradictions and changed skills. Fix failures within scope; stop on missing authority or a product-boundary conflict.
7. Report head SHA, changed contracts, exact gate results, rollback and remaining risks. Do not start the next stage.

Never add marketplace flows, user accounts, public ratings, billing or new launch regions unless `DECISIONS.md` and the current task explicitly authorize them.
