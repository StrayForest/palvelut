COMPOSE_PROJECT_NAME ?= palvelut
COMPOSE := docker compose --project-name $(COMPOSE_PROJECT_NAME)

.PHONY: bootstrap dev reset test e2e smoke

bootstrap:
	@command -v docker >/dev/null || { echo "Docker is required" >&2; exit 1; }
	@docker compose version >/dev/null || { echo "Docker Compose v2 is required" >&2; exit 1; }
	$(COMPOSE) config >/dev/null
	$(COMPOSE) build web

dev:
	$(COMPOSE) up --build

reset:
	bash infra/scripts/reset-local.sh

test:
	$(COMPOSE) build web
	$(COMPOSE) run --rm --no-deps -v "$(CURDIR):/workspace:ro" -w /workspace web python -m unittest discover -s tests -p 'test_*.py' -v

e2e:
	bash infra/scripts/e2e.sh

smoke:
	bash infra/scripts/smoke.sh
