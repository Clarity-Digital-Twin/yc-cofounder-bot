PY=uv run

.PHONY: setup install browsers precommit lint format type test run run-cli check-cua clean clean-pyc lint-fix verify
.PHONY: lint-fix verify

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

verify: ## Run lint, type, tests
	make lint
	make type
	make test

run: ## Run Streamlit UI
	$(PY) streamlit run -m yc_matcher.interface.web.ui_streamlit

run-cli: ## Run CLI
	$(PY) python -m yc_matcher.interface.cli.run --help

check-cua: ## Probe access to OpenAI Computer Use model
	$(PY) python -m yc_matcher.interface.cli.check_cua

clean:
	rm -rf .mypy_cache .ruff_cache .pytest_cache dist build *.egg-info
export UV_LINK_MODE=copy

clean-pyc:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
