# P0-05 — Windows 11 WSL2 development setup

Completed: 2026-09-03
Commit/PR: implementation head `32dd34639df00138ca118ee7e04cffd68d2f891f`; PR #8

## Scope

- Added `docs/09-development.md` as the local development guide for Linux and Windows 11.
- Defined Windows 11 development as WSL2 + Docker Desktop WSL integration.
- Kept the project command surface identical on Linux and Windows/WSL2: `make bootstrap`, `make dev`, `make test`, `make e2e`, `make smoke`, and guarded `make reset`.
- Documented that native PowerShell/CMD are not supported project execution environments and that Docker Desktop owns the daemon for the WSL workflow.
- Recommended cloning inside the WSL Linux filesystem rather than `/mnt/c/`.
- Linked the development guide from the repository README.
- Removed only the completed Windows setup item from the active P0 task.

## Checks

- GitHub Actions run `33696665563` on implementation head `32dd34639df00138ca118ee7e04cffd68d2f891f` — PASS.
- Dependency and command contract verification — PASS.
- `make test` — PASS.
- `make e2e` — PASS.
- `make smoke` — PASS.
- Compose cleanup — PASS.
- Documentation command names were checked against the repository `Makefile`; no Windows-specific alternate command path was introduced.

## Deviations

- None. Tailwind/HTMX/Alpine/i18n and the accessible base layout remain the next active P0 implementation work.
