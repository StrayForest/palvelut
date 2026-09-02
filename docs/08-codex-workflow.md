# Codex workflow

## Start a stage

Use this prompt, replacing the stage:

> Implement `tasks/P0-foundation.md` in `StrayForest/palvelut`. Follow `AGENTS.md`. Work only on this stage, run every listed gate, and leave a reviewable PR. Do not start the next stage.

## Review a stage

Start a fresh Codex session without the implementer's rationale:

> Use `$palvelut-review` to review exact PR head `<SHA>` against its `tasks/Px-*.md`, `DECISIONS.md`, security, privacy, SEO, accessibility, cache safety, migrations and rollback. Inspect the diff first and reproduce every gate. Report blockers with evidence; do not fix or add features.

A self-review may catch defects but does not count as independent approval. Review is stale after any new commit and must be rerun on the new head.

## Correct foundation contracts

Use only when the user explicitly requests a bounded correction:

> Correct the named foundation contract in one PR. Change only affected decisions/docs/tasks/skills, validate all links and skills, then review the exact diff in a fresh session. Do not start product implementation.

## Close a stage

Codex must report: exact head SHA, changed contracts, commands and results, remaining risks, rollback, and next task path. If a gate fails, the stage remains in progress.

## Context budget

Read the current task, decisions and only docs linked by that task. Search code by symbol/path. Do not paste research or entire docs into prompts. Record a new durable decision once in `DECISIONS.md`; link to it elsewhere.

Repository skills:

- `$palvelut-build` implements one bounded stage or explicitly requested foundation correction.
- `$palvelut-review` independently evaluates a stage/PR.
