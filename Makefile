SHELL := /bin/sh

UV_RUN := uv run --frozen
PYTHON_FILES := src tests examples

.PHONY: default help format format-check ruff-check lint test coverage build clean \
	pre-commit-install pre-commit pre-commit-all ci

default: help

help: ## Show available commands.
	@awk 'BEGIN {FS = ":.*##"; printf "fastmcp-dishka commands:\n\n"} /^[a-zA-Z0-9_-]+:.*##/ {printf "  %-22s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

format: ## Format Python files with Ruff.
	$(UV_RUN) ruff format $(PYTHON_FILES)

format-check: ## Check Ruff formatting without writing changes.
	$(UV_RUN) ruff format --check $(PYTHON_FILES)

ruff-check: ## Run Ruff lint checks.
	$(UV_RUN) ruff check --exit-non-zero-on-fix $(PYTHON_FILES)

lint: format-check ruff-check ## Run all lint checks.

test: ## Run tests with coverage.
	$(UV_RUN) python -m pytest

coverage: test ## Alias for coverage-enabled tests.

build: ## Build source distribution and wheel.
	uv build

pre-commit-install: ## Install pre-commit hooks.
	$(UV_RUN) pre-commit install

pre-commit: ## Run pre-commit on modified files.
	$(UV_RUN) pre-commit run

pre-commit-all: ## Run pre-commit on all files.
	$(UV_RUN) pre-commit run --all-files

clean: ## Remove local build, cache, and coverage artifacts.
	rm -rf .coverage coverage.xml dist htmlcov .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +

ci: lint test build ## Run the same checks expected in CI.
