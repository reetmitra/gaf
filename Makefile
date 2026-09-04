# Offline-first: every target below runs with no API keys and no network.
#
# `make demo` is the acceptance criterion. It codes the synthetic corpus with mock
# clients, prints a run report with a CHECKS section, and writes the codebook, the
# assignments, every finding and the append-only audit log. Running it twice produces
# a byte-identical codebook JSON and an identical snapshot-id sequence — asserted in
# tests/test_cli.py, not merely claimed here.
#
# The synthetic corpus lives in tests/fixtures/corpus.py, which is the only corpus in
# this repository: no human survey response is ever committed. The demo materialises
# it into the run directory rather than shipping a second copy of it.

DEMO_DIR ?= runs/demo
DEMO_CORPUS := $(DEMO_DIR)/corpus.json
DEMO_ANALYSIS := $(DEMO_DIR)/analysis

.PHONY: help install test lint typecheck check-all scrub demo check analyse

help:
	@echo "make install    — uv sync (core + dev)"
	@echo "make test       — offline pytest suite"
	@echo "make lint       — ruff"
	@echo "make typecheck  — mypy on gaf/"
	@echo "make check-all  — lint + typecheck + test"
	@echo "make scrub      — delete run outputs and the cache; run before sharing this directory"
	@echo "make demo       — code the synthetic corpus offline; run report + codebook explorer"
	@echo "make check      — run every check over the demo codebook (exit 1 iff an ERROR)"
	@echo "make analyse    — occurrence matrix, Ward's HCA and the saturation curve"

install:
	uv sync --all-groups

test:
	uv run pytest

lint:
	uv run ruff check .

typecheck:
	uv run mypy

check-all: lint typecheck test

# -- the demo ------------------------------------------------------------- #

$(DEMO_CORPUS):
	@mkdir -p $(DEMO_DIR)
	@uv run python -c "import sys; sys.path.insert(0, '.'); from tests.fixtures.corpus import synthetic_corpus; from gaf.ingest.corpus import write_corpus_json; write_corpus_json(synthetic_corpus(), '$(DEMO_CORPUS)')"
	@echo "synthetic corpus written to $(DEMO_CORPUS)"

demo: $(DEMO_CORPUS)
	uv run gaf run --corpus $(DEMO_CORPUS) --run-id demo --offline --out $(DEMO_DIR)
	uv run gaf report --run $(DEMO_DIR)

check: $(DEMO_CORPUS)
	@test -f $(DEMO_DIR)/codebook.json || $(MAKE) demo
	uv run gaf check all --codebook $(DEMO_DIR)/codebook.json --data $(DEMO_CORPUS)

analyse: $(DEMO_CORPUS)
	@test -f $(DEMO_DIR)/assignments.json || $(MAKE) demo
	uv run gaf analyse --assignments $(DEMO_DIR)/assignments.json --data $(DEMO_CORPUS) --out $(DEMO_ANALYSIS)

# Run outputs and the LLM cache contain the corpus you coded, verbatim, with codes and
# findings attached. They are gitignored, so they never reach a commit — but .gitignore
# does not protect a zip, a backup, an rsync or a directory copy. Run this before this
# directory leaves your machine.
scrub:
	@echo "removing run outputs and the response cache..."
	@rm -rf runs/ .gaf_cache/
	@echo "done. runs/ and .gaf_cache/ removed; re-create them with: make demo"
