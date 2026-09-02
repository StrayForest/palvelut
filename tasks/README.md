# Delivery tasks

Run in numeric order. A task is complete only when every acceptance item and gate passes on its exact head. Keep evidence in the PR/check output; do not add long status documents to the repository.

Each task may reduce optional scope to protect quality. It may not cross the exclusions in `DECISIONS.md`.

## Active-step discipline

- Active `tasks/Px-*.md` files contain only unfinished work.
- Execute one bounded atomic step at a time when a stage is too large for one reviewable change.
- After that step passes its relevant checks, remove it from the active task and create a short record under `tasks/archive/`.
- Archive records state what changed, exact commit/PR when available, checks run, and any intentional deviation. They are historical evidence, not a second roadmap.
- Never archive a step that has failing or unrun required checks.
- When the active task has no remaining steps and every stage acceptance/gate passes, close the stage and advance `ROADMAP.md`.
