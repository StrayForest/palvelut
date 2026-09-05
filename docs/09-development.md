# Local development

The project supports Linux and Windows 11 through one command path. Project commands are always run from a Linux shell and are defined by the repository `Makefile`.

## Required host tools

- Git
- Make
- Docker with Docker Compose v2

Do not install project Python, PostgreSQL, Valkey, Node.js or browser dependencies globally. They run inside the project containers.

## Linux

1. Install Git, Make and Docker Engine with the Compose v2 plugin.
2. Clone the repository and enter its directory.
3. Run `make bootstrap`.
4. Run `make dev` for the local stack.

Use the same repository gates before pushing changes:

```bash
make test
make e2e
make smoke
```

Use `make reset` only when disposable local project state must be rebuilt.

## Windows 11

Windows development uses WSL2 plus Docker Desktop WSL integration. Native PowerShell and Windows CMD are not supported project execution environments.

1. Enable/install WSL2 and install an Ubuntu distribution.
2. Install Git and Make inside the Ubuntu WSL distribution.
3. Install Docker Desktop on Windows and enable **Use the WSL 2 based engine**.
4. In Docker Desktop, enable WSL integration for the Ubuntu distribution used for development.
5. Open the Ubuntu WSL shell and verify Docker is available:

```bash
docker version
docker compose version
```

6. Clone the repository inside the WSL Linux filesystem, for example under `~/src/`, rather than under `/mnt/c/`.
7. From the repository directory run exactly the same commands as on Linux:

```bash
make bootstrap
make dev
make test
make e2e
make smoke
```

Use `make reset` when disposable local state must be rebuilt. It is project-scoped and refuses production-like settings.

Docker Desktop owns the Docker daemon; do not install or start a second Docker daemon inside WSL for this workflow.

## GitHub Codespaces preview

Codespaces is an optional disposable preview environment for manually opening and testing the application without a separate VPS or local Docker installation. It is not a production deployment target.

1. In GitHub, open **Code → Codespaces → Create codespace on main**.
2. The repository devcontainer installs Docker-in-Docker, runs `make bootstrap`, starts the normal Compose services, applies migrations and runs `make seed-demo` equivalent setup automatically.
3. Open forwarded port `8000` to view `/palvelut/ru/`.
4. Open forwarded port `8025` for Mailpit when testing registration, verification and password-reset emails.

The Codespaces overlay only changes the externally visible preview origin so Django accepts the GitHub forwarded HTTPS host and generates canonical URLs for that temporary environment. PostgreSQL, Valkey, Mailpit, MinIO, web, worker and nginx remain the same project services used by local development.

Stopping or deleting a Codespace does not affect production or any persistent external environment.

## Command contract

| Command | Purpose |
|---|---|
| `make bootstrap` | Validate the local Docker/Compose contract and build the application image. |
| `make dev` | Start the complete local Compose environment. |
| `make test` | Run the non-browser automated test gate. |
| `make e2e` | Run the disposable browser gate. |
| `make smoke` | Start disposable dependencies/app services, verify the current smoke contract and clean up. |
| `make reset` | Remove and rebuild only this project's disposable local state; refuse production-like settings. |

There is no Windows-specific replacement command for any target above. If a command path diverges between Linux and Windows/WSL2, treat that as a project defect rather than documenting a second workflow.
