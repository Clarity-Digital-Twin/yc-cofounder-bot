PY=uv run

.PHONY: setup install browsers precommit lint format type test run run-cli check-cua clean

setup: install browsers precommit ## Install deps and browsers

install: ## Sync dependencies with uv
	uv sync --all-extras

browsers: ## Install Playwright Chromium
	$(PY) python -m playwright install chromium

precommit: ## Install pre-commit hooks
	$(PY) pre-commit install

lint: ## Run ruff lints
	$(PY) ruff check .

format: ## Apply ruff formatting
	$(PY) ruff format .

type: ## Run mypy
	$(PY) mypy src

test: ## Run tests
	$(PY) pytest

run: ## Run Streamlit UI
	$(PY) streamlit run -m yc_matcher.ui_streamlit

run-cli: ## Run CLI
	$(PY) python -m yc_matcher.run_cli --help

check-cua: ## Probe access to OpenAI Computer Use model
	$(PY) python -m yc_matcher.check_cua

clean:
	rm -rf .mypy_cache .ruff_cache .pytest_cache dist build *.egg-info
