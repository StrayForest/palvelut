# Codex workflow

## Start a stage

Use this prompt, replacing the stage:

> Implement `tasks/P0-foundation.md` in `StrayForest/palvelut`. Follow `AGENTS.md`. Work only on this stage, run every listed gate, and leave a reviewable PR. Do not start the next stage.

## Review a stage

> Review the current PR against its `tasks/Px-*.md`, `DECISIONS.md`, security, privacy, SEO, accessibility, cache safety, migrations and rollback. Reproduce the gates. Report blockers with evidence; do not add features.

## Close a stage

Codex must report: exact head SHA, changed contracts, commands and results, remaining risks, rollback, and next task path. If a gate fails, the stage remains in progress.

## Context budget

Read the current task, decisions and only docs linked by that task. Search code by symbol/path. Do not paste research or entire docs into prompts. Record a new durable decision once in `DECISIONS.md`; link to it elsewhere.

Repository skills:

- `$palvelut-build` implements one bounded stage.
- `$palvelut-review` independently evaluates a stage/PR.
