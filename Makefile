smoke:
	uv run python scripts/smoke.py
UV ?= uv
DAPR ?= dapr

.PHONY: dev fmt lint test run-agent run-workflow clean docker-build docker-up docker-down docker-logs docker-test docker-init-ollama docker-quick-start

help:
	@printf "Available targets:\n"
	@printf "  dev               Format, lint, and test\n"
	@printf "  fmt               Auto-fix style issues with ruff\n"
	@printf "  lint              Run ruff in check-only mode\n"
	@printf "  test              Execute pytest suite\n"
	@printf "  run-agent         Launch FastAPI agent-shell via Dapr\n"
	@printf "  run-workflow      Launch workflow-host via Dapr\n"
	@printf "  docker-quick-start Interactive setup script (recommended)\n"
	@printf "  docker-build      Build Docker images\n"
	@printf "  docker-up         Start all services with Docker Compose\n"
	@printf "  docker-down       Stop all services\n"
	@printf "  docker-logs       Follow logs from all services\n"
	@printf "  docker-test       Run end-to-end tests against Docker services\n"
	@printf "  docker-init-ollama Initialize Ollama with model\n"
	@printf "  clean             Remove .pyc/__pycache__ artifacts\n"

DEV_TARGETS := fmt lint test

dev: $(DEV_TARGETS)

fmt:
	$(UV) run ruff check --fix

lint:
	$(UV) run ruff check

test:
	$(UV) run pytest

run-agent:
	$(DAPR) run \
		--app-id agent-shell \
		--app-port 8000 \
		-- uv run uvicorn src.agent_shell.main:app --reload

run-workflow:
	$(DAPR) run \
		--app-id workflow-host \
		--app-port 7000 \
		-- uv run python src/workflow_host/main.py

clean:
	find . -name '__pycache__' -prune -exec rm -rf {} +
	find . -name '*.pyc' -delete

# Docker Compose targets
docker-quick-start:
	./scripts/quick-start-docker.sh

docker-build:
	docker compose build

docker-up:
	docker compose up -d
	@echo "Services are starting. Run 'make docker-logs' to follow logs."
	@echo "Run 'make docker-init-ollama' to pull the Ollama model."
	@echo "Run 'make docker-test' to verify the deployment."

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-test:
	python3 tests/e2e_docker_test.py

docker-init-ollama:
	./scripts/init-ollama.sh
