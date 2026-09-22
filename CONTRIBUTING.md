# Contributing

Notes for someone changing this code, not for someone using it. Read
`docs/ARCHITECTURE.md` first if you have not; this file assumes it.

## The offline rule

Tests and CI never touch a model or a key. `RunConfig.offline` defaults to `True`
everywhere — mock model clients, the lexical embedding fallback, no API key, no
network — and that is the only path the test suite or CI ever takes. `--live` (CLI) or
`offline=False` (`RunConfig`) is opt-in, builds real provider clients from
`RunConfig.models`, and nothing in `tests/` or `.github/workflows/ci.yml` sets it.

CI enforces this as a claim, not a convention: before linting or testing anything, it
asserts that no provider SDK (`openai`, `google.genai`, `anthropic`) is importable and
that none of `OPENAI_API_KEY` / `GOOGLE_API_KEY` / `ANTHROPIC_API_KEY` is set in the
environment. A workflow step needing a secret does not belong in `ci.yml` — see the
comment at its top.

If you add a code path that can reach a provider SDK or a network call, gate it behind
`offline=False` / `--live` explicitly, and do not exercise that path from a test.

## The frozen contracts

These modules are fixed by Wave 0 of the build and may not be changed without a
recorded decision:

- `gaf/models.py`
- `gaf/config.py`
- `gaf/checks/contracts.py`
- `gaf/llm/base.py`
- `gaf/embed/protocol.py`
- `gaf/store/schema.py`
- `gaf/textnorm.py`

A change to any of these goes through an ADR (see "Recording a decision" below) before
the edit lands, not after. They have been amended — ADR-0015 added a field to
`config.py`, ADR-0026 corrected a docstring in `contracts.py` — and each time the
reasoning was recorded first and the change was additive. A pull request that touches
one of these files without a corresponding ADR should be rejected on that basis alone.

## No real data, and `make provenance`

No human survey response may ever enter git history. The only corpus that may be
committed is the synthetic one in `tests/fixtures/corpus.py`; `data/synthetic/` is the
only path under `data/` that is not gitignored. `.gitignore` also blocks `*.xlsx`,
`*.xlsm`, `*.docx`, `*.csv` and `*.tsv` repository-wide, `runs/` and `.gaf_cache/`
outright, for the same reason.

`tests/test_golden.py::test_no_tracked_file_contains_real_respondent_text` scans every
tracked file for a 20-character run shared with a real response — the number is loaded
from `scripts/export_results.py`, not copied, so the two guards cannot drift
(ADR-0047) — reading the real
corpus from `../Grounded AI Futures/data/` on the machine that has it. It **skips
silently** when that file is absent — which is the normal case on CI and on any
machine but the researcher's own — so it will not tell you anything is wrong unless
you run it deliberately:

```
make provenance
```

Run this before pushing anything that touches ingest, fixtures, docs or example
output, and always before sharing the repository, on a machine where the real corpus
is present. `-rs` in the target makes a skip visible rather than silent, so you can
tell whether it actually ran.

## `make scrub` before sharing the directory

`runs/` and `.gaf_cache/` hold the corpus you coded, verbatim, with codes and findings
attached. They are gitignored, so a commit cannot leak them — but `.gitignore` does
not protect a zip, a backup, an `rsync`, or a directory copied by hand. Run

```
make scrub
```

before this directory leaves your machine by any path other than `git push`. It
deletes `runs/` and `.gaf_cache/`; re-create them with `make demo`.

## The golden-set regression

`tests/test_golden.py` is the project's regression safety net — read its module
docstring in full before touching it; this is a summary, not a substitute.

It has two independent jobs:

1. **Concurrent validation** against a human coding, via
   `gaf.analysis.agreement.concurrent_validation` — never reimplemented, only loaded
   into the row-oriented assignments shape a coding spreadsheet produces.
2. **Pipeline regression** — the offline fast loop is run over
   `tests.fixtures.corpus.synthetic_corpus()` and compared byte-for-byte against the
   artefacts committed under `tests/fixtures/golden/` (`codebook.json`,
   `assignments.json`, `snapshots.json`, `findings.json`, `manifest.json`). A prompt
   edit, a threshold change, a mock-persona rewrite or an accidental reordering shows
   up here as a named failure rather than something a reader notices three weeks
   later.

**Regenerating the fixture is deliberate, never incidental:**

```
uv run python -m tests.test_golden --regenerate
```

The flag is required — running the module without it exits with a usage error, and no
environment variable can substitute for it — so the fixture cannot be rewritten by
accident. Only run this when you intend the pipeline's output to change and have
checked why; do not run it to make a red test green without understanding the diff
first.

**`human_coding.json` is never regenerated.** It is the drop-in slot the PI's real
hand-coding replaces at the path named by `GAF_GOLDEN_HUMAN_CODING`; regeneration must
never overwrite a human coding, so the flag does not touch that file under any
circumstance.

## The three gates

```
make check-all
```

runs lint (`ruff check .`), type-check (`uv run mypy`) and the full offline test suite
(`uv run pytest`), in that order. All three must be green before a change lands; CI
runs the same three plus a coverage floor (`--cov=gaf`, currently gated at 93%, set
just under the measured number — see the comment beside `COVERAGE_FLOOR` in
`.github/workflows/ci.yml` for how and when to move it).

Run `make check-all` locally before opening a pull request. A red gate in CI that was
green locally usually means an uncommitted file, not an environment difference — check
`git status` first.

## Recording a decision

Append an entry to `docs/DECISIONS.md`, immediately before the next unused `ADR-NNNN`
number, in the existing format:

```
## ADR-NNNN — <short, specific title>

**Status:** accepted (<wave or context>)

**Context.** <the situation that forced a choice>

**Decision.** <what was chosen>

**Consequences.** <what this costs, and what it buys>
```

Do not delete or renumber an existing ADR, including a superseded one — the log is
part of the audit trail, and a superseded entry stays in place with a pointer to what
replaced it. Add a row to the index table at the top of the file for any ADR you add
(`| [ADR-NNNN](#anchor) | Title | Status |`); the anchor is the heading's GitHub
slug (lowercase, spaces to hyphens, punctuation stripped).

Any change to a frozen contract, any threshold moved, any rule in
`docs/CODING_RULES.md` reinterpreted, or any non-obvious structural choice gets an
ADR. If you are unsure whether something is "non-obvious" enough to warrant one, it
almost certainly is — the cost of a short entry nobody re-reads is far lower than the
cost of a choice nobody can reconstruct the reasoning for.
