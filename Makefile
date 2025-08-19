# --- repo-scoped caches & env (confine tools to this repo) ---
ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
export UV_LINK_MODE=copy
export UV_CACHE_DIR := $(ROOT)/.uv_cache
export XDG_CACHE_HOME := $(ROOT)/.cache
export PLAYWRIGHT_BROWSERS_PATH := $(ROOT)/.ms-playwright
export MPLCONFIGDIR := $(ROOT)/.mplconfig

PY=uv run

.PHONY: setup install browsers precommit lint format type test run run-cli check-cua clean clean-pyc lint-fix verify doctor

setup: install browsers precommit ## Install deps and browsers

install: ## Sync dependencies with uv
	uv sync --all-extras

browsers: ## Install Playwright Chromium
	$(PY) python -m playwright install chromium

precommit: ## Install pre-commit hooks
	$(PY) pre-commit install

lint: ## Run ruff lints
	$(PY) ruff check .

lint-fix: ## Auto-fix lints and format
	$(PY) ruff check --fix .
	$(PY) ruff format .

format: ## Apply ruff formatting
	$(PY) ruff format .

type: ## Run mypy
	$(PY) mypy src

test: ## Run tests
	PYTHONPATH=src $(PY) pytest -q

test-int: ## Run integration tests
	PYTHONPATH=src $(PY) pytest -q -m integration

verify: ## Run lint, type, tests
	make lint
	make type
	make test

doctor: ## Print env/caches to verify repo-scoped setup
	@echo "ROOT=$(ROOT)"
	@echo "UV_CACHE_DIR=$(UV_CACHE_DIR)"
	@echo "XDG_CACHE_HOME=$(XDG_CACHE_HOME)"
	@echo "PLAYWRIGHT_BROWSERS_PATH=$(PLAYWRIGHT_BROWSERS_PATH)"
	@echo "MPLCONFIGDIR=$(MPLCONFIGDIR)"
	@echo "Using PY=$(PY)"
	@ls -ld .uv_cache .cache .ms-playwright .mplconfig .venv .runs || true

run: ## Run Streamlit UI
	$(PY) streamlit run -m yc_matcher.interface.web.ui_streamlit

run-cli: ## Run CLI
	$(PY) python -m yc_matcher.interface.cli.run --help

check-cua: ## Probe access to OpenAI Computer Use model
	$(PY) python -m yc_matcher.interface.cli.check_cua

clean:
	rm -rf .mypy_cache .ruff_cache .pytest_cache dist build *.egg-info

clean-pyc:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
