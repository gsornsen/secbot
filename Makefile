VENV := .venv
PYTHON := $(VENV)/bin/python3
UV := $(shell which uv)
CHAINLIT := $(VENV)/bin/chainlit

.PHONY: env run uv clean test

uv:
	@echo "Installing uv..."
	@command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }
	@echo "uv is installed"

env: uv
	@echo "Installing python dependencies..."
	@uv add pyproject.toml
	@echo "Installing git hooks..."
	@uv run pre-commit install
	@uv run pre-commit install --hook-type pre-push

run:
	# $(CHAINLIT) run src/<script>.py -h
	@echo "App would start running"

test:
	@echo "Running tests..."
	@$(PYTHON) -m pytest tests/

clean:
	@rm -rf $(VENV)
	@echo "Removing venv..."
