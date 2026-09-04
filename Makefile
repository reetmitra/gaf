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
EXAMPLE_DIR := examples/demo-run

.PHONY: help install test lint typecheck check-all scrub demo check analyse example provenance

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
	@echo "make example    — regenerate examples/demo-run/ from a fresh make demo + make analyse"
	@echo "make provenance — scan every tracked file for real respondent text (needs the real corpus on this machine)"

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

# -- the example snapshot -------------------------------------------------- #
#
# examples/demo-run/ is a committed, browsable copy of a demo run's output, so that
# nobody has to build this project to see what it produces. It is generated from a
# fresh `make demo` + `make analyse`, never hand-edited. The occurrence matrix ships
# only as JSON: *.csv is gitignored repo-wide to keep any real corpus out of history,
# and the CSV carries nothing the JSON matrix doesn't already have. gaf.sqlite and
# audit.jsonl are excluded too — one is binary, the other timestamped, and neither
# is needed to read the run.
example: demo analyse
	@mkdir -p $(EXAMPLE_DIR)
	@rm -rf $(EXAMPLE_DIR)/analysis
	@mkdir -p $(EXAMPLE_DIR)/analysis
	@cp $(DEMO_DIR)/report.txt $(DEMO_DIR)/codebook.json $(DEMO_DIR)/codebook.html \
		$(DEMO_DIR)/assignments.json $(DEMO_DIR)/findings.json $(DEMO_DIR)/stats.json \
		$(DEMO_DIR)/corpus.json $(EXAMPLE_DIR)/
	@cp $(DEMO_ANALYSIS)/occurrence_matrix.json $(DEMO_ANALYSIS)/clusters.json \
		$(DEMO_ANALYSIS)/clusters.md $(DEMO_ANALYSIS)/dendrogram.svg \
		$(DEMO_ANALYSIS)/saturation.json $(DEMO_ANALYSIS)/saturation.md \
		$(DEMO_ANALYSIS)/saturation.svg $(EXAMPLE_DIR)/analysis/
	@echo "examples/demo-run/ regenerated from a fresh $(DEMO_DIR)"

# Run outputs and the LLM cache contain the corpus you coded, verbatim, with codes and
# findings attached. They are gitignored, so they never reach a commit — but .gitignore
# does not protect a zip, a backup, an rsync or a directory copy. Run this before this
# directory leaves your machine.
scrub:
	@echo "removing run outputs and the response cache..."
	@rm -rf runs/ .gaf_cache/
	@echo "done. runs/ and .gaf_cache/ removed; re-create them with: make demo"

# tests/test_golden.py::test_no_tracked_file_contains_real_respondent_text reads the
# real corpus in place (../Grounded AI Futures/data/) and fails if any tracked file
# shares a 30-character run with a real response. It skips — silently, under plain
# `make test` — when the real file is absent, which is the common case on CI and on
# any machine other than the researcher's own. Run this target on a machine that has
# the real corpus before sharing or publishing the repository.
provenance:
	uv run pytest tests/test_golden.py::test_no_tracked_file_contains_real_respondent_text -q -rs
