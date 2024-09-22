VENV := .venv
PYTHON := $(VENV)/bin/python3
UV := $(shell which uv)
CHAINLIT := $(VENV)/bin/chainlit
SUPERVISOR := $(VENV)/bin/supervisord

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
	@if [ ! -f ~/.aws/config ]; then \
		echo "[default]\nregion = us-west-2" > ~/.aws/config; \
		echo "Created ~/.aws/config file"; \
	fi
	@$(PYTHON) hacks/patch_socket.py

run:
	@echo "Starting application..."
	@PYTHONPATH=$(shell pwd) $(SUPERVISOR) -c supervisord.conf

test:
	@echo "Running tests..."
	@$(PYTHON) -m pytest

clean:
	@rm -rf $(VENV)
	@echo "Removing venv..."
