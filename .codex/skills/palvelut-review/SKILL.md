---
name: palvelut-review
description: Independently audit a Finrix Palvelut change or PR against its roadmap task and production contracts. Use for review, release gates, regressions, or readiness decisions; do not use to invent new scope.
---

# Palvelut review

Review read-only unless the user explicitly asks for fixes.

1. Identify the task/acceptance contract and exact commit under review.
2. Read `AGENTS.md`, `DECISIONS.md`, the task, and only relevant linked sections.
3. Inspect the diff before surrounding code. Trace public data, authorization, cache, SEO and analytics paths end-to-end where affected.
4. Reproduce task gates; add focused diagnostic checks when evidence is missing.
5. Prioritize findings: data/security/privacy loss, false trust claims, cache leakage, unpublished-content exposure, broken discovery, then maintainability.
6. Cite file/symbol and observable impact. Separate confirmed defect, risk, and optional improvement.
7. Mark PASS only when every task gate passes on the exact commit. Otherwise remain BLOCKED and state the smallest corrective action.

Do not reward extra features. Treat scope expansion, generic verification wording and unproven completion claims as defects.
