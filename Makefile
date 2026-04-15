# ==============================================================
#							FLY-IN
# ==============================================================

NAME = fly_in
PYTHON = python3
UV = $(shell command -v uv 2> /dev/null || echo $(HOME)/.local/bin/uv)
UV_PROJECT_ENVIRONMENT ?= .venv
MAP = "maps/test_map.txt"

SRC = src

DEPS =	flake8	\
		mypy

all: install

install:
	@if [ ! -e $(UV) ]; then \
		echo "installing uv..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh >/dev/null 2>&1; \
	fi
	@echo "Syncing dependencies..."
	@$(UV) sync

run:
	@$(UV) run python -m $(SRC) $(MAP)

debug:
	@$(UV) run python -m pdb -m $(SRC) $(MAP)

lint:
	@echo "Running flake8..."
	@$(UV) run flake8 $(SRC)
	@echo "Running mypy..."
	@$(UV) run mypy $(SRC)


lint-strict:
	@echo "Running flake8..."
	@$(UV) run flake8 $(SRC)
	@echo "Running mypy --strict..."
	@$(UV) run mypy $(SRC) --strict

clean:
	@echo "Cleaning cache files..."
	@$(RM) -r */.mypy_cache */.pytest_cache */.uv_cache */__pycache__

fclean: clean
	@echo "Removing virtual environment..."
	@$(RM) -r $(UV_PROJECT_ENVIRONMENT)

re: fclean all

.PHONY: all install run debug lint lint-strict clean fclean re
.DEFAULT_GOAL = all
