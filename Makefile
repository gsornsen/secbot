VENV := .venv
PYTHON := $(VENV)/bin/python3
UV := $(shell which uv)
CHAINLIT := $(VENV)/bin/chainlit

.PHONY: env run uv clean

uv:
	@command -v uv >/dev/null 2>&1 || { echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }
	@echo "uv is installed"

env: uv
	@uv add pyproject.toml

run:
	# $(CHAINLIT) run src/<script>.py -h
	@echo "App would start running"

clean:
	@rm -rf $(VENV)
	@echo "Removing venv..."
