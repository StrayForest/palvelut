COMPOSE_PROJECT_NAME ?= palvelut
COMPOSE := docker compose --project-name $(COMPOSE_PROJECT_NAME)

.PHONY: bootstrap dev reset test e2e smoke

bootstrap:
	@command -v docker >/dev/null || { echo "Docker is required" >&2; exit 1; }
	@docker compose version >/dev/null || { echo "Docker Compose v2 is required" >&2; exit 1; }
	$(COMPOSE) config >/dev/null
	$(COMPOSE) build web

dev:
	$(COMPOSE) up -d --build postgres valkey mailpit minio
	$(COMPOSE) run --rm web python manage.py migrate --noinput
	$(COMPOSE) up --build

reset:
	bash infra/scripts/reset-local.sh

test:
	$(COMPOSE) --profile quality build quality
	$(COMPOSE) --profile quality run --rm --no-deps quality bash infra/scripts/test-in-container.sh

e2e:
	bash infra/scripts/e2e.sh

smoke:
	bash infra/scripts/smoke.sh
