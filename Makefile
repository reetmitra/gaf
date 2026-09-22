# Offline-first: every target below runs with no API keys and no network.
#
# `make demo` is the acceptance criterion. It codes the synthetic corpus with mock
# clients and renders every reading artefact the run supports: the run report with a
# CHECKS section, the codebook explorer, the timeline, the reorganisation trail, the
# decision matrix and the shareable views page — plus the codebook, the assignments,
# every finding and the append-only audit log. Running it twice produces a
# byte-identical codebook JSON and an identical snapshot-id sequence — asserted in
# tests/test_cli.py, not merely claimed here.
#
# The synthetic corpus lives in tests/fixtures/corpus.py, which is the only corpus in
# this repository: no human survey response is ever committed. The demo materialises
# it into the run directory rather than shipping a second copy of it.

DEMO_DIR ?= runs/demo
DEMO_CORPUS := $(DEMO_DIR)/corpus.json
DEMO_ANALYSIS := $(DEMO_DIR)/analysis
EXAMPLE_DIR := examples/demo-run
RESULTS_RUN ?= runs/process
RESULTS_OUT ?= results/india-process-1-20
RESULTS_LABEL ?= India Process sample, responses 1-20

# `make results-full` — the whole real-data sequence, raw inputs to shareable results,
# in one command. Every variable below is overridable; the defaults are where the real
# files sit on the researcher's machine. Nothing here runs live.
FULL_CORPUS_CSV ?= ../Grounded AI Futures/data/IndiaProcess(1-200)-FinalCleaned.csv
FULL_TAGGED_CSV ?= ../Grounded AI Futures/data/CodebookIndiaProcess(1-20)CodesExamples.csv
FULL_DEFINITIONS_MD ?= ../Grounded AI Futures/codebook/AI_Perceptions_Codebook1.md
FULL_QUESTION_VARIANT ?= v2
FULL_RUN_DIR ?= runs/process200
FULL_HUMAN_DIR ?= runs/human200
FULL_SEEDED_DIR ?= runs/process200-seeded
FULL_HALTED_DIR ?= runs/process200-halted
FULL_RESUMED_DIR ?= runs/process200-resumed
FULL_RESULTS_OUT ?= results/india-process-1-200
FULL_RESULTS_LABEL ?= India Process, responses 1-200
FULL_GUARD_SHINGLE ?= 20

.PHONY: help install test lint typecheck check-all scrub demo check analyse views example provenance results

help:
	@echo "make install    — uv sync (core + dev)"
	@echo "make test       — offline pytest suite"
	@echo "make lint       — ruff"
	@echo "make typecheck  — mypy on gaf/"
	@echo "make check-all  — lint + typecheck + test"
	@echo "make scrub      — delete run outputs and the cache; run before sharing this directory"
	@echo "make demo       — code the synthetic corpus offline; report, explorer, timeline, trail, decision matrix, views.html"
	@echo "make check      — run every check over the demo codebook (exit 1 iff an ERROR)"
	@echo "make analyse    — occurrence matrix, Ward's HCA, saturation, patterns, affinity, growth"
	@echo "make views      — views.html alone, from whatever of the demo and its analysis already exists"
	@echo "make example    — regenerate examples/demo-run/ from a fresh make demo + make analyse"
	@echo "make provenance — scan every tracked file for real respondent text (needs the real corpus on this machine)"
	@echo "make results    — export a real run as Markdown with no respondent text (RESULTS_RUN=runs/process RESULTS_OUT=results/<name>)"
	@echo "make results-full — the whole real-data sequence, raw inputs to results/, offline, one command"

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
	uv run gaf analyse --assignments $(DEMO_DIR)/assignments.json --data $(DEMO_CORPUS) \
		--run $(DEMO_DIR)/run.json \
		--codebook $(DEMO_DIR)/codebook.json --out $(DEMO_ANALYSIS)

# `gaf report` already writes views.html as part of `make demo`. This target is for
# rebuilding it alone — after analysing a run further, or over a coding that never went
# through `gaf run` at all — without repeating the coding or the report.
views: $(DEMO_CORPUS)
	@test -f $(DEMO_DIR)/codebook.json || $(MAKE) demo
	uv run gaf views --run $(DEMO_DIR)

# -- the example snapshot -------------------------------------------------- #
#
# examples/demo-run/ is a committed, browsable copy of a demo run's output, so that
# nobody has to build this project to see what it produces. It is generated from a
# fresh `make demo` + `make analyse`, never hand-edited. The occurrence matrix ships
# only as JSON: *.csv is gitignored repo-wide to keep any real corpus out of history,
# and the CSV carries nothing the JSON matrix doesn't already have. gaf.sqlite and
# audit.jsonl are excluded too — one is binary, the other timestamped, and neither
# is needed to read the run.
# `gaf report` (inside `make demo`) writes views.html BEFORE `make analyse` runs, so on
# a tree with no pre-existing analysis directory the page it writes has no dendrogram,
# no saturation curve and no co-occurrence figures at all. Rebuilding it here, after
# the prerequisites, is what makes this target reproducible from a clean clone rather
# than dependent on what an earlier run happened to leave behind (R2 I-2).
example: demo analyse
	@$(MAKE) views DEMO_DIR=$(DEMO_DIR)
	@mkdir -p $(EXAMPLE_DIR)
	@rm -rf $(EXAMPLE_DIR)/analysis
	@mkdir -p $(EXAMPLE_DIR)/analysis
	@cp $(DEMO_DIR)/report.txt $(DEMO_DIR)/codebook.json $(DEMO_DIR)/codebook.html \
		$(DEMO_DIR)/assignments.json $(DEMO_DIR)/findings.json $(DEMO_DIR)/stats.json \
		$(DEMO_DIR)/corpus.json $(DEMO_DIR)/views.html $(DEMO_DIR)/tree.mmd \
		$(DEMO_DIR)/timeline.json $(DEMO_DIR)/timeline.md $(DEMO_DIR)/timeline.svg \
		$(DEMO_DIR)/reorganisation_trail.json $(DEMO_DIR)/reorganisation_trail.md \
		$(DEMO_DIR)/decision_matrix.md $(EXAMPLE_DIR)/
	@cp $(DEMO_ANALYSIS)/occurrence_matrix.json $(DEMO_ANALYSIS)/clusters.json \
		$(DEMO_ANALYSIS)/clusters.md $(DEMO_ANALYSIS)/dendrogram.svg \
		$(DEMO_ANALYSIS)/saturation.json $(DEMO_ANALYSIS)/saturation.md \
		$(DEMO_ANALYSIS)/saturation.svg $(DEMO_ANALYSIS)/patterns.json \
		$(DEMO_ANALYSIS)/patterns.md $(DEMO_ANALYSIS)/affinity.json \
		$(DEMO_ANALYSIS)/affinity.md $(DEMO_ANALYSIS)/growth.json \
		$(DEMO_ANALYSIS)/growth.md $(EXAMPLE_DIR)/analysis/
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
# real workbooks in place (../data, ../codebook, ../Grounded AI Futures/data) and fails if any tracked file
# shares a 20-character run with a real response — the results exporter's own shingle,
# loaded from it rather than copied, so the two cannot drift (ADR-0047). It skips —
# silently, under plain
# `make test` — when the real file is absent, which is the common case on CI and on
# any machine other than the researcher's own. Run this target on a machine that has
# the real corpus before sharing or publishing the repository.
provenance:
	uv run pytest tests/test_golden.py::test_no_tracked_file_contains_real_respondent_text -q -rs

# -- results for sharing ---------------------------------------------------- #
#
# A real run holds the coded corpus verbatim and never enters git. What CAN be shared
# is everything about the coding that is not the respondents' words: counts, code
# names, response numbers, metrics, cluster structure, threshold curves. The exporter
# writes exactly that, then re-reads what it wrote and fails - deleting its output -
# if any file shares a 20-character run with any text it was told to withhold.
# results/ is tracked; make provenance covers it like every other tracked file.
# README.md is opt-in (--readme). An existing results directory may carry a
# hand-written README that is the record of a meeting; re-exporting into it must not
# replace that document by accident. `make results-full` passes the flag because the
# directory it writes is generated end to end.
results:
	uv run python scripts/export_results.py --run $(RESULTS_RUN) --out $(RESULTS_OUT) --label "$(RESULTS_LABEL)"

# Ingest, organise, check, analyse, run, report, crosswalk, agreement both ways,
# calibrate, seed, halt, resume, views, export, provenance — in that order, failing at
# the first error. The run directories it writes hold respondents' words and are
# gitignored; the one directory it writes outside runs/ is $(FULL_RESULTS_OUT), and the
# exporter's guard is what decides whether a file may land there.
results-full:
	CORPUS_CSV="$(FULL_CORPUS_CSV)" \
	TAGGED_CSV="$(FULL_TAGGED_CSV)" \
	DEFINITIONS_MD="$(FULL_DEFINITIONS_MD)" \
	QUESTION_VARIANT="$(FULL_QUESTION_VARIANT)" \
	RUN_DIR="$(FULL_RUN_DIR)" \
	HUMAN_DIR="$(FULL_HUMAN_DIR)" \
	SEEDED_DIR="$(FULL_SEEDED_DIR)" \
	HALTED_DIR="$(FULL_HALTED_DIR)" \
	RESUMED_DIR="$(FULL_RESUMED_DIR)" \
	RESULTS_OUT="$(FULL_RESULTS_OUT)" \
	RESULTS_LABEL="$(FULL_RESULTS_LABEL)" \
	GUARD_SHINGLE="$(FULL_GUARD_SHINGLE)" \
	bash scripts/run_full_results.sh
