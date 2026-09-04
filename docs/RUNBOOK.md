# Runbook

*Operator guide. Everything below runs offline by default — mock model clients, the
lexical embedding fallback, no API key, no network.*

## Sixty seconds from a clean clone

```bash
uv sync --all-groups
```

```bash
make demo
```

That codes the synthetic corpus end to end, writes a run directory under `runs/demo/`,
prints a run report with a CHECKS section, and renders the HTML codebook explorer. Run
it twice and the codebook JSON and snapshot-id sequence are byte-identical.

```bash
make check-all
```

Ruff, mypy and the full offline suite.

---

## The commands

```
gaf ingest      --xlsx PATH [--question-variant v2|v3] --out corpus.json
gaf run         --corpus PATH [--out DIR] [--run-id ID] [--batch-size N] [--seed N]
gaf check       structural|semantic|all
                (--codebook X.json | --assignments A.json) [--data corpus.json]
gaf analyse     --assignments A.json [--data corpus.json] --out DIR
gaf validate    agreement --human H.json --machine M.json [--data corpus.json]
gaf validate    lexical --table T.json (--score-col NAME | --score-from codes --codebook C.json)
gaf report      --run DIR
gaf checkpoint  --run DIR [--interactive]
```

**Exit codes.** `0` success · `1` an ERROR finding or a refused fit · `2` usage ·
`3` unreadable or unsupported input.

Note the deliberate asymmetry: **`gaf check` exits 1 if and only if an ERROR was
found**, because it answers *"is this artefact valid?"*. **`gaf run` and `gaf analyse`
exit 0 whenever the run completes**, regardless of severity, because a finding is the
*output* of a run rather than a failure of it. A run over any real corpus will contain
unverifiable quotes; that is the check layer working.

---

## Coding a real corpus

```bash
uv run gaf ingest --xlsx "../Grounded AI Futures/data/NarrativeState(IndiaSample1-20).xlsx" --out runs/india/corpus.json
```

Real survey data lives **outside the repository** and stays there. `data/` is gitignored
except `data/synthetic/`, and every spreadsheet and document extension is excluded
repository-wide.

**But `.gitignore` only protects git.** Once you have coded a real corpus, `runs/` and
`.gaf_cache/` hold that corpus verbatim — every response, with its codes, spans and
findings attached. Those directories are invisible to a commit and completely visible to
a zip, a backup, an rsync or a directory copy. **Run `make scrub` before this directory
leaves your machine**, and re-create the outputs with `make demo` or another run. If you ever find a respondent file staged for commit, stop and remove
it from the index — do not attempt a history rewrite alone.

Ingest attaches the survey question to every record (it is absent from the workbook),
resolves columns by header name, tolerates the `No`/`Number` spelling variation, and
repairs mis-encoded text — reporting how many responses needed it rather than doing it
silently.

```bash
uv run gaf run --corpus runs/india/corpus.json --out runs/india
uv run gaf report --run runs/india
```

The run directory holds `codebook.json`, `assignments.json`, `findings.json`,
`stats.json`, `audit.jsonl`, `report.txt`, `codebook.html` and `gaf.sqlite`.

---

## The human gate

This is the one place a person's decision changes the codebook, and it is the only
place structural change happens at all. The fast loop never restructures — coders
propose, and integration merges or admits, but nothing splits, re-parents or renames
outside a checkpoint.

```bash
uv run gaf checkpoint --run runs/india --interactive
```

**What you will see.** The Refactorer sees the whole codebook with usage statistics and
proposes an edit script. Every operation is validated deterministically first — one that
could not be applied never reaches you — and you review a compact per-operation diff:
what it does, to which codes, the rationale, and how much evidence is at stake.

For each operation: **accept**, **reject**, or **edit** (substitute your own operation,
which is then validated exactly as the machine's was — the gate is not a bypass).

**Without `--interactive`, or with no terminal attached, the checkpoint is a no-op.**
Every operation is rejected and nothing is applied. This is deliberate: the absence of a
human is never an auto-accept.

Accepting produces a new content-addressed snapshot with the previous as its parent, and
a changelog recording what was proposed, what you decided and what was applied.

**When to open one.** Checkpoints are event-driven on codebook health — near-duplicate
pairs, code growth rate — with a hard floor of every 50 responses. `gaf checkpoint`
opens one on demand.

**Why the gate is here and not on every response.** Item-by-item verification of machine
codings is the decision-task overlay that the Vaccaro et al. meta-analysis finds makes
human–AI teams *worse* than either alone. Restructuring a hierarchy is a creation task
with a predetermined division of labour, which is the condition under which that
meta-analysis finds synergy. See `docs/METHODS.md` §2.

---

## The analysis tail

```bash
uv run gaf analyse --assignments runs/india/assignments.json --data runs/india/corpus.json --out runs/india/analysis
```

Writes the occurrence matrix as CSV, the agglomeration schedule, cluster assignments and
cluster means, the dendrogram and the saturation curve as SVG.

**Read the agglomeration schedule before trusting the cluster count.** The rule inherited
from Chan (2025) takes the largest break in the merge coefficients and subtracts its
stage from the sample size. It assumes that break falls near the root of the tree. On a
small sample with sparse code vectors it can fall at the leaf end instead, and the rule
then returns a degenerate answer — on the 20-response seed sample it returns 18 clusters.
The implementation reports this rather than hiding it, and `--n-clusters` records an
explicit override as an override. **The cluster count is the study's headline; take it
from a corpus large enough for the rule to behave, or state it and say that you did.**

---

## Validation

```bash
uv run gaf validate agreement --human golden.json --machine runs/india/assignments.json --data runs/india/corpus.json
# --score-from codes derives the score from each response's codes, so it needs the codebook
uv run gaf validate lexical --table runs/india/scored.json --score-from codes \
  --codebook runs/india/codebook.json
```

No command writes `scored.json` — it is a pooled table of `(response_id, text, score,
group)` that you assemble from whatever score the study is testing. From a completed run,
with the score derived from the codes:

```bash
uv run python -c "
import json
from gaf.ingest.corpus import load_corpus
rows = [{'response_id': r.id, 'text': r.content, 'group': r.source}
        for r in load_corpus('runs/india/corpus.json')]
json.dump(rows, open('runs/india/scored.json', 'w'), indent=2)
"
```

With a score column of your own instead, pass `--score-col NAME` and skip `--codebook`.

The lexical check **refuses to fit** when a binarised cut has fewer than ten positives
or negatives. On a 20-response sample it will refuse, and that is correct behaviour, not
a crash — an AUC from a 20/0 split would mean nothing.

### Swapping in the real hand-codings

The investigator's golden set drops into the regression harness with one environment
variable and no code change:

```bash
export GAF_GOLDEN_HUMAN_CODING="../Grounded AI Futures/data/<his file>.xlsx"
uv run pytest tests/test_golden.py
```

It dispatches on the file suffix — `.xlsx` through the coded-workbook reader, `.json`
through the assignments shape — and the file stays outside the repository. Until it is
set, one test skips, which is the correct state rather than a failure.

**Once it exists, run the threshold calibration.** τ_high = 0.80, τ_low = 0.45 and
τ_fit = 0.30 are provisional and uncalibrated.

There is **no CLI subcommand for this** — it is a Python API, because it is run once when
the golden set arrives rather than routinely:

```bash
uv run python -c "
import json
from gaf.checks.health import calibrate_thresholds
from gaf.config import CodingRules
from gaf.embed.service import EmbeddingService
from gaf.ingest.xlsx import read_coded_xlsx
from gaf.models import Assignment

human = read_coded_xlsx('../Grounded AI Futures/data/<his file>.xlsx')
machine = [Assignment.from_json(r) for r in json.load(open('runs/india/assignments.json'))]
report = calibrate_thresholds(human, machine, EmbeddingService(), CodingRules())
print(report.paragraph())
json.dump(report.to_json(), open('runs/india/calibration_report.json', 'w'), indent=2)
"
```

It reports and never silently changes a constant — moving a threshold is a decision to
record in `docs/DECISIONS.md`, not an edit to make quietly.

---

## Going live

Live models are opt-in and no test or CI run ever touches them.

```bash
cp .env.example .env      # then fill in the keys you actually intend to use
uv sync --extra live      # provider SDKs are optional extras, not core dependencies
uv run gaf run --corpus runs/india/corpus.json --out runs/india --live
```

Two coders from **different providers** and a judge from a **third** — the epistemic
diversity is the point, and it is also what makes disagreement a meaningful escalation
signal. The provider triple is configured, never hard-coded.

**Before the first live run, know what it will cost.** In offline runs the code–evidence
fit check accounts for the large majority of frontier calls, because the fallback
embedder cannot separate a code label from a quote. Whether a real embedding model does
is an open empirical question. Budget for the worst case of one judge call per quote,
watch the `llm_calls` table on a small batch first, and read ADR-0019 and ADR-0022.

Responses are cached by content hash, so a re-run costs nothing for anything unchanged.

---

## When something breaks

**The golden regression fails.** It will name what moved and tell you the regeneration
command. Decide whether the change was intended *before* regenerating — that test exists
precisely to make a prompt or threshold change visible.

**`make demo` output changed.** Something in the substrate moved: a prompt, a threshold,
a mock persona, the embedding space, or a fixture. The manifest in
`tests/fixtures/golden/` pins all of those and will say which.

**A check fires on real data that you think is correct.** Read the finding's `data`
payload — it carries the score, the span and the ids. Structural findings are
deterministic and replayable; semantic findings in an offline run may be artefacts of
the fallback embedder rather than facts about the coding.

**The store refuses a write.** Snapshots are immutable and the audit log is append-only,
enforced by database triggers. A refusal means something tried to rewrite history, which
is the guarantee working.
