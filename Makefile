VENV := .venv
PYTHON := $(VENV)/bin/python3
UV := $(shell which uv)
CHAINLIT := $(VENV)/bin/chainlit
SUPERVISOR := $(VENV)/bin/supervisord

.PHONY: env run uv clean test install-multitail stream-logs

uv:
	@echo "Installing uv..."
	@command -v uv >/dev/null 2>&1 || { echo "uv not found, installing..."; curl -LsSf https://astral.sh/uv/install.sh | sh; }
	@echo "uv is installed"

install-multitail:
	@if command -v multitail >/dev/null 2>&1; then \
		echo "multitail is already installed."; \
	else \
		echo "Installing multitail..."; \
		if [ "$(shell uname)" = "Darwin" ]; then \
			if command -v brew >/dev/null 2>&1; then \
				brew install multitail; \
			else \
				echo "Homebrew is not installed. Please install Homebrew first."; \
				exit 1; \
			fi \
		elif [ "$(shell uname)" = "Linux" ]; then \
			if command -v apt-get >/dev/null 2>&1; then \
				sudo apt-get update && sudo apt-get install -y multitail; \
			elif command -v yum >/dev/null 2>&1; then \
				sudo yum install -y epel-release && sudo yum install -y multitail; \
			elif command -v dnf >/dev/null 2>&1; then \
				sudo dnf install -y epel-release && sudo dnf install -y multitail; \
			elif command -v pacman >/dev/null 2>&1; then \
				sudo pacman -Sy multitail; \
			else \
				echo "Unsupported Linux distribution. Please install multitail manually."; \
				exit 1; \
			fi \
		else \
			echo "Unsupported operating system. Please install multitail manually."; \
			exit 1; \
		fi; \
		echo "multitail installed successfully."; \
	fi

env: uv install-multitail
	@echo "Installing python dependencies..."
	@uv add pyproject.toml
	@echo "Installing git hooks..."
	@mkdir -p .log
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
	@$(PYTHON) -m pytest --cov=./ --cov-report=xml

stream-logs:
	@multitail -Q 2 '.log/*.log'

clean:
	@echo "Removing venv..."
	@rm -rf $(VENV)
	@echo "Removing .log directory..."
	@rm -rf .log
