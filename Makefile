# MetricTide — developer shortcuts
# Usage: make <target>

COMPOSE := docker compose

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------
.PHONY: up
up: ## Build and start the full stack
	$(COMPOSE) up --build

.PHONY: up-d
up-d: ## Start the full stack in the background
	$(COMPOSE) up --build -d

.PHONY: down
down: ## Stop and remove containers
	$(COMPOSE) down

.PHONY: down-v
down-v: ## Stop containers and remove named volumes (DESTROYS data)
	$(COMPOSE) down -v

.PHONY: logs
logs: ## Tail logs for all services
	$(COMPOSE) logs -f

.PHONY: ps
ps: ## Show running services
	$(COMPOSE) ps

# ---------------------------------------------------------------------------
# Local development
# ---------------------------------------------------------------------------
.PHONY: web-dev
web-dev: ## Run the Next.js dev server locally
	pnpm --filter web dev

.PHONY: api-dev
api-dev: ## Run the FastAPI dev server locally
	cd services/api && uv run uvicorn app.main:app --reload

# ---------------------------------------------------------------------------
# Quality
# ---------------------------------------------------------------------------
.PHONY: test
test: ## Run all tests (web + api)
	pnpm --filter web test
	cd services/api && uv run pytest

.PHONY: lint
lint: ## Lint everything
	pnpm --filter web lint
	cd services/api && uv run ruff check .

.PHONY: fmt
fmt: ## Format everything
	pnpm --filter web format
	cd services/api && uv run ruff format .
