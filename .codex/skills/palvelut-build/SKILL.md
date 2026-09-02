---
name: palvelut-build
description: Implement one bounded roadmap task in the Finrix Palvelut repository. Use for feature, infrastructure, or delivery work in this project; not for broad product ideation or independent review.
---

# Palvelut build

Implement exactly one named `tasks/Px-*.md` stage.

1. Read repository `AGENTS.md`, the task, `DECISIONS.md`, and only docs linked by the task.
2. Inspect the affected code/tests and current git state. Preserve unrelated changes.
3. Restate the task boundary and identify the riskiest invariant before editing.
4. Implement the smallest complete vertical result. Keep domain writes behind module service functions.
5. Add tests for observable behaviour, authorization, cache/SEO impact and failure paths relevant to the change.
6. Run every gate named in the task on the exact final head. Fix failures within scope; stop on missing authority or a product-boundary conflict.
7. Report head SHA, changed contracts, exact gate results, rollback and remaining risks. Do not start the next stage.

Never add marketplace flows, user accounts, public ratings, billing or new launch regions unless `DECISIONS.md` and the current task explicitly authorize them.
