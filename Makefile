smoke:
	uv run python scripts/smoke.py
UV ?= uv
DAPR ?= dapr

.PHONY: dev fmt lint test run-agent run-workflow clean

help:
	@printf "Available targets:\n"
	@printf "  dev            Format, lint, and test\n"
	@printf "  fmt            Auto-fix style issues with ruff\n"
	@printf "  lint           Run ruff in check-only mode\n"
	@printf "  test           Execute pytest suite\n"
	@printf "  run-agent      Launch FastAPI agent-shell via Dapr\n"
	@printf "  run-workflow   Launch workflow-host via Dapr\n"
	@printf "  clean          Remove .pyc/__pycache__ artifacts\n"

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
