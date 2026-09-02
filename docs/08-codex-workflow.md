# Codex workflow

## Start a stage

Use this prompt, replacing the stage:

> Implement the next unfinished step in `tasks/P0-foundation.md` in `StrayForest/palvelut`. Follow `AGENTS.md`. Work only on that bounded step, run its relevant checks, archive it only after they pass, and leave a reviewable PR. Do not start the following step in the same implementation pass.

## Review a stage

Start a fresh Codex session without the implementer's rationale:

> Use `$palvelut-review` to review exact PR head `<SHA>` against its active `tasks/Px-*.md`, applicable archived step record, `DECISIONS.md`, security, privacy, SEO, accessibility, cache safety, migrations and rollback. Inspect the diff first and reproduce every relevant gate. Report blockers with evidence; do not fix or add features.

A self-review may catch defects but does not count as independent approval. Review is stale after any new commit and must be rerun on the new head.

## Correct foundation contracts

Use only when the user explicitly requests a bounded correction:

> Correct the named foundation contract in one PR. Change only affected decisions/docs/tasks/skills, validate all links and skills, then review the exact diff in a fresh session. Do not start product implementation.

## Close an atomic step

After the relevant checks pass on the exact head:

1. Remove the completed step from the active `tasks/Px-*.md` file.
2. Add `tasks/archive/Px-NN-<slug>.md` with the completed scope, exact commit/PR when available, checks run and any intentional deviation.
3. Keep acceptance criteria and gates that still apply to unfinished stage work in the active task.
4. Do not use archive records as an excuse to skip stage-level acceptance or gates.

If a required check fails or was not run, the step stays active and must not be archived.

## Close a stage

Codex must report: exact head SHA, changed contracts, commands and results, remaining risks, rollback, and next task path. When all active work is gone and every stage acceptance/gate passes, advance `ROADMAP.md` to the next stage. If a gate fails, the stage remains in progress.

## Context budget

Read the current task, decisions and only docs linked by that task. Search code by symbol/path. Read archived step records only when needed to understand already-completed work or review the current diff. Do not paste research or entire docs into prompts. Record a new durable decision once in `DECISIONS.md`; link to it elsewhere.

Repository skills:

- `$palvelut-build` implements one bounded unfinished step or explicitly requested foundation correction.
- `$palvelut-review` independently evaluates a step/stage PR.
