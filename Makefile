# Offline-first: every target below runs with no API keys and no network.
# Wave 3 (agent C2) owns this file from that point and adds demo/check/analyse.

.PHONY: help install test lint typecheck check-all

help:
	@echo "make install    — uv sync (core + dev)"
	@echo "make test       — offline pytest suite"
	@echo "make lint       — ruff"
	@echo "make typecheck  — mypy on gaf/"
	@echo "make check-all  — lint + typecheck + test"

install:
	uv sync --all-groups

test:
	uv run pytest

lint:
	uv run ruff check .

typecheck:
	uv run mypy

check-all: lint typecheck test
