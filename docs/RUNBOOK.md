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
gaf ingest      --input PATH [--question-variant v2|v3] --out corpus.json
gaf run         --corpus PATH [--out DIR] [--run-id ID] [--batch-size N] [--seed N]
                [--seed-codebook CODEBOOK.json] [--halt-on-checkpoint]
                [--skip-coded RUN-DIR]
gaf check       structural|semantic|all
                (--codebook X.json | --assignments A.json) [--data corpus.json]
gaf analyse     --assignments A.json [--data corpus.json] --out DIR [--run RUN.json]
                [--codebook C.json] [--crosswalk-target C2.json] [--crosswalk-names-only]
gaf validate    agreement --human H.json --machine M.json [--data corpus.json]
gaf validate    lexical --table T.json (--score-col NAME | --score-from codes --codebook C.json)
gaf report      --run DIR [--out DIR] [--analysis DIR]
gaf checkpoint  --run DIR [--interactive] [--trigger NAME]
gaf codebook    organise --tagged PAIRINGS [--corpus corpus.json] [--definitions MD]
                [--sheet NAME] --out DIR
gaf codebook    define --organised DIR [--only-missing]
gaf views       (--run DIR | --assignments A.json --codebook C.json [--data corpus.json])
                [--analysis DIR] [--out PATH] [--batch-size N]
```

**Exit codes.** `0` success · `1` an ERROR finding or a refused fit · `2` usage ·
`3` unreadable or unsupported input. `codebook organise` and `codebook define` follow
`run`/`analyse`'s convention, not `check`'s: what they find is their deliverable, so
they exit 0 whenever the work completes and non-zero only on a bad argument or input
the readers refuse — a code the Definer refused to describe is a count in the output,
not a reason to fail the command. `views` exits 2 if given neither `--run` nor
`--assignments`, or both; a missing artefact it depends on is never an error, only a
line naming the command that would write it.

Note the deliberate asymmetry: **`gaf check` exits 1 if and only if an ERROR was
found**, because it answers *"is this artefact valid?"*. **`gaf run` and `gaf analyse`
exit 0 whenever the run completes**, regardless of severity, because a finding is the
*output* of a run rather than a failure of it. A run over any real corpus will contain
unverifiable quotes; that is the check layer working.

---

## Coding a real corpus

```bash
uv run gaf ingest --input "../data/NarrativeState(IndiaSample1-20).xlsx" --question-variant v3 --out runs/state/corpus.json
```

`--input` is the current spelling; `--xlsx` still works, unchanged, because it is in
older scripts. Despite the flag's name, a `.csv` is read exactly as readily as a
workbook — the shape is detected from the file's own contents, never from its
extension:

```bash
uv run gaf ingest \
  --input "../Grounded AI Futures/data/IndiaProcess(1-200)-FinalCleaned.csv" \
  --out runs/process200/corpus.json
```

A numbered CSV like this one comes in one of two shapes, both detected automatically: a
header naming `All` (optionally beside a `Trimmed` cleaning pass — where the two
disagree by more than whitespace, `Trimmed` wins, because it is the PI's own cleaning,
and the ingest line names which rows disagreed), or a headerless single column of
`NN. …` cells, the same grammar the numbered workbook uses. Two responses sharing one
number are both kept; the second's id becomes `number + 1000`, and the ingest line says
so.

**Name the question.** *State* files ("in 2050, what kind of roles") are `v3`; *Process*
files ("from now to 2050, what impacts") are `v2`. The default is `v2`, so a State file
ingested without the flag gets the wrong question in the coder prompt — which happened
once (ADR-0029). The ingest line now prints the question it attached and warns when the
file name disagrees with the variant; it never guesses on your behalf.

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
uv run gaf run --corpus runs/state/corpus.json --out runs/state
uv run gaf report --run runs/state
```

`gaf run` writes `codebook.json`, `assignments.json`, `findings.json`, `stats.json`,
`run.json`, `audit.jsonl`, `report.txt` and `gaf.sqlite`. `gaf report` adds `codebook.html`,
`timeline.json`/`.md`/`.svg`, `reorganisation_trail.json`/`.md`, `decision_matrix.md`,
`views.html` and `tree.mmd` — everything the run supports, in one command.

---

## A seeded run, a halted run, and its resumption

`gaf run` can start from a codebook someone already built instead of from nothing, and
can stop itself at the first batch a checkpoint comes due, so the fast loop and the
human gate can actually hand work back and forth:

```bash
# a seeded run — codes into the organisation `gaf codebook organise` (below) built
uv run gaf run --corpus runs/process200/corpus.json --run-id seeded \
  --out runs/process200-seeded --seed-codebook runs/human200/codebook.json

# a cold run that halts itself the first time a checkpoint comes due
uv run gaf run --corpus runs/process200/corpus.json --run-id halted \
  --out runs/process200-halted --halt-on-checkpoint
```

A halt exits **0** — it is the handover working, not a failure — and prints the batch,
which matrix rows fired, how many responses remain, and the two commands that continue
the work:

```bash
uv run gaf checkpoint --run runs/process200-halted
uv run gaf run --corpus runs/process200/corpus.json --run-id resumed \
  --out runs/process200-resumed \
  --seed-codebook runs/process200-halted/codebook.json \
  --skip-coded runs/process200-halted
```

**On the default settings, a cold run's first batch almost always trips the checkpoint**
— with no predecessor codebook, every code the first batch admits counts as new, and
the absolute ceiling is 8. It trips on `handover.new_codes` under trigger `health`, not
on the spike rule, which has no baseline that early and says so. Budget for
`--halt-on-checkpoint` to stop after 10 responses on a first run, not after 50.

**A seeded run is a production tool, not a validation one.** Its own evidence is held
out — a seed's codes arrive with no evidence, so its occurrence matrix, its saturation
curve and its codebook all describe only what *this* run coded, never the coding the
seed came from — but its agreement with the coding that produced its seed is still not
independent evidence about either: the machine was shown the shape of the answer before
it started. Only a cold run (no `--seed-codebook`) belongs in an agreement figure. The
run report's CAVEATS section says this above every number a seeded run produces.

`--skip-coded <dir>` excludes every response a previous run already coded, by its own
recorded outcomes, so resuming never codes a response twice; skipping every response in
the corpus is refused by name rather than producing an empty run.

---

## Building a codebook from a finished human coding

The PI's own coding — code-text pairings, tagged by hand — implies a two-level
codebook: family and sub-code split on the first hyphen, a count per code, examples,
and consolidation of trivial spelling variants. `gaf codebook organise` does all of
that arithmetic, places every segment onto a corpus when one is given, and attaches the
PI's own descriptions when he has written them:

```bash
uv run gaf codebook organise \
  --tagged "../Grounded AI Futures/data/CodebookIndiaProcess(1-20)CodesExamples.csv" \
  --corpus runs/process200/corpus.json \
  --definitions "../Grounded AI Futures/codebook/AI_Perceptions_Codebook1.md" \
  --out runs/human200
```

This writes `organised.json` / `.md` (the tree and the listing, with segments —
respondent text, stays out of git), `organised_shareable.md` (the same listing with the
segments withheld — **but not the descriptions**: read them before this file leaves the
machine, see below), `tree.mmd` (a Mermaid tree of names and counts only),
`codebook.json` (what every other command reads), `placement.json` and `golden.json`
(the row-oriented human coding, for `gaf validate agreement`).

**Filling in a description the PI has not written** is the one part of his own
inductive-codebook prompt that is not arithmetic — the Definer, a fourth LLM role
outside both loops:

```bash
uv run gaf codebook define --organised runs/human200
```

Offline, the Definer is an extractive stand-in — it reports the commonest words of a
code's own segments — and every description it writes is labelled
`description_source: definer-mock` so a reader can never mistake it for the
researcher's own. A description he wrote by hand is never overwritten, under any flag;
`--only-missing` additionally leaves alone anything the Definer itself already wrote, so
a second pass only fills genuine gaps.

**A description is only as shareable as whoever wrote it made it.** Withholding the
segments does not withhold a description that happens to echo them: on the real
codebook, 5 of the PI's 131 imported definitions share a run of thirty characters or
more with a real response. `gaf codebook organise` prints this warning every time it
writes `organised_shareable.md`, and a results export (below) withholds a colliding
definition by code name — but a document built directly by `organise` does not, and
should be read before it is sent anywhere.

---

## The two shapes the PI's files arrive in

The principal investigator's samples do not come as `Number | Response` workbooks.
Both shapes below are handled; neither is guessed.

**A numbered single-column corpus.** One column, no header, the response number folded
into the cell: `11. <the response text>`. `gaf ingest` detects this and reads
it; nothing to pass. Two responses carrying the *same* number are both kept — the
second is given `number + 1000` as its id, the number as written is kept on the
record's metadata, and the ingest line says so (`number 44 appears again -> id 1044`).
A headed workbook with a duplicate id still raises, because there two rows claiming one
respondent cannot both be that respondent; here the number is a label the PI wrote.

**A coding-tool highlights export.** Two shapes: the two-column `tag,content` pairing a
coding tool exports directly, and the four-column `id | document | tag | content` export
— the coded text and its code, but **no response number** in either. `gaf codebook
organise` (above) reads both through one command now; every highlight is placed by
locating its text in the corpus, exactly as before: an exact substring of exactly one
normalised response, else the single response above the S2 fuzzy threshold, else — on a
corpus larger than the coding covers — the one candidate inside the **coded set** (every
response the coding demonstrably reached), counted separately as `resolved` rather than
folded into `exact` (ADR-0031). A highlight that still fits more than one response is
*ambiguous* and excluded; one that fits none is *unlocated* and excluded. All four
outcomes are counted and listed in `placement.json`, never assigned by guess. On the
200-response Process corpus the summary line reads `342 highlights: 304 exact, 1 fuzzy,
7 resolved, 24 ambiguous (excluded), 6 unlocated (excluded) -> 312 mapped`; quote the
outcomes separately, never "312 mapped" alone — a `resolved` placement is a weaker claim
than an `exact` one.

`golden.json`, written beside `codebook.json` by `organise`, is the row-oriented
assignments shape every comparison consumes, and the path to hand to
`GAF_GOLDEN_HUMAN_CODING`.

**Before comparing against a coding with no descriptions, know what it lacks.** A coding
export with only code names, matched against a machine codebook that carries both a name
and a description, scores the same concept at 0.4–0.7 in the lexical space —
`problem_solving` against `problem-solving` at 0.696, an identical name at 0.426 — so
almost nothing clears τ_high. Run `gaf validate agreement` **without** `--codebook` to
match name against name in that case. Where the PI's own definitions exist
(`--definitions` on `organise`, above), this asymmetry is closed **on his side**: his
codes now carry descriptions too, so a name-plus-description comparison is fair on both
sides. It is not eliminated, only moved — one side's descriptions were drafted by a
model from his prompt over his own pairings, the other's by the coder models during
coding, so a match with descriptions attached is now a comparison of two model-written
glosses over the same corpus, and should be reported as one (ADR-0032).

## The human gate

This is the one place a person's decision changes the codebook, and it is the only
place structural change happens at all. The fast loop never restructures — coders
propose, and integration merges or admits, but nothing splits, re-parents or renames
outside a checkpoint.

```bash
uv run gaf checkpoint --run runs/state --interactive
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
pairs, code growth rate — with a hard floor of **50 responses since the last
checkpoint**. `gaf checkpoint` opens one on demand.

The floor counts from the last checkpoint, not from the start of the run (ADR-0033, as
amended by ADR-0040). Taking a checkpoint clears it; the next one comes due fifty
responses later. Until one is taken the floor keeps reporting due, because the look is
still owed — so on a long run `checkpoint_due.batches_due` lists every batch after the
floor was first crossed, and that is a true statement about a codebook nobody has
looked at rather than a schedule. A run resumed with `--skip-coded` **carries the count
forward**: it reads the previous run directory's store, and if no checkpoint was taken
there it counts that run's responses as still owed a look. It prints which of the three
cases it found, and says so plainly when the previous store is missing and it cannot
know.

**Why the gate is here and not on every response.** Item-by-item verification of machine
codings is the decision-task overlay that the Vaccaro et al. meta-analysis finds makes
human–AI teams *worse* than either alone. Restructuring a hierarchy is a creation task
with a predetermined division of labour, which is the condition under which that
meta-analysis finds synergy. See `docs/METHODS.md` §2.

**What the trail carries, and what it withholds.** An independent review this wave found
that `reorganisation_trail.json`/`.md` could carry a respondent's own words: the trail
rendered the raw `before`/`after` operation payload for any operation you *edit* at the
gate — and editing a `split` is how you move quotes between the parts — and rebuilt a
dropped operation's record, including the validator's own sentence, which names the
``(response_id, quote)`` pair it rejected. That is fixed (ADR-0039).

The trail now carries an operation's payload filtered to a fixed allow-list of keys
that cannot hold text (`name`, `into`, `new_parent_id`, `parent_id`, `response_ids`,
at any depth), names the keys it withheld on the entry and beside each dropped
operation, and replaces a validator's sentence with a gloss written from the drop
marker. The whole sentence is still in the run's own `findings.json`, under `runs/`,
which is where a respondent's words belong. `views.html` was independently confirmed
clean before and remains so.

---

## The analysis tail

```bash
uv run gaf analyse --assignments runs/state/assignments.json --data runs/state/corpus.json \
  --run runs/state/run.json \
  --codebook runs/state/codebook.json --out runs/state/analysis
```

Writes the occurrence matrix as CSV, the agglomeration schedule, cluster assignments and
cluster means, the dendrogram and the saturation curve as SVG — and, beside them, three
further readings of the same matrix: `patterns.md`/`.json` (which responses share which
code combinations), `affinity.md`/`.json` (bottom-up thematic groups of leaf codes that
cut across families), and `growth.md`/`.json` (new codes per batch and the spike rule's
verdict). `--codebook` is what lets affinity compare code *descriptions*, not just
names; without it, affinity still runs, names-only, and says so on the artefact itself.

**Pass `--run` whenever these assignments came from a `gaf run`.** A row-oriented
assignments file knows nothing about the process that produced it: a response the run
coded to nothing leaves no row, so it is invisible, and the batch size the run used is
written nowhere in the rows. Without `--run`, `growth.json` is therefore cut on the
responses that *have* a row, at the analysis batch size, and disagrees with the run's
own decision trace and timeline; `growth.md` says at the top which of the two it is
(ADR-0041). The clustering, the saturation curve and the affinity map do not need it.

**Where the filter applies.** Clustering, the heatmap and the affinity map read the
low-frequency-filtered matrix. **Patterns do not**: a pattern view exists to show which
codes travel together, including the rare ones, so `patterns.json` is built over the
unfiltered matrix and its `filter` block says so. The two therefore report different
code counts on purpose.

Add `--crosswalk-target` to map this coding's codebook onto a second one — the PI's own,
for instance:

```bash
uv run gaf analyse --assignments runs/state/assignments.json --data runs/state/corpus.json \
  --codebook runs/state/codebook.json \
  --crosswalk-target runs/human200/codebook.json --crosswalk-names-only \
  --out runs/state/analysis
```

`--crosswalk-names-only` compares both sides by name alone, which is the fair comparison
whenever only one codebook carries descriptions (ADR-0029) — exactly the case of a
machine codebook against the PI's own, until his definitions are attached to both sides
of the comparison.

**Read the agglomeration schedule before trusting the cluster count.** The rule inherited
from Chan (2025) takes the largest break in the merge coefficients and subtracts its
stage from the sample size. It assumes that break falls near the root of the tree. On a
small sample with sparse code vectors it can fall at the leaf end instead, and the rule
then returns a degenerate answer — on the 20-response seed sample it returns 18 clusters.
The implementation reports this rather than hiding it, and `--n-clusters` records an
explicit override as an override. **The cluster count is the study's headline; take it
from a corpus large enough for the rule to behave, or state it and say that you did.**

---

## Eleven views in one page

```bash
uv run gaf views --run runs/state
```

Builds `views.html` from whatever the run and, if `<run>/analysis` exists beside it, the
analysis directory already hold: the codebook tree, code frequencies, the
response-by-code heatmap, co-occurrence, patterns, affinity, growth beside the timeline,
the loop handover, the reorganisation trail, the crosswalk, and clusters and saturation.
`gaf report` writes this same page as part of rendering a run; `gaf views` builds it
alone, which is what you want after analysing a run further, or for a coding that never
went through `gaf run` at all:

```bash
uv run gaf views --assignments runs/human200/golden.json \
  --codebook runs/human200/codebook.json \
  --data runs/process200/corpus.json \
  --out results/india-process-1-200/views-human/views.html
```

**No respondent text reaches this page, ever** — no quote, no segment, no code
description, no model's prose rationale — only code names, family names, response
*numbers*, counts and scores. This is the file that may leave the machine.
`codebook.html`, by contrast, carries the evidence quotes and stays a working artefact;
it links to `views.html` and says so. A missing artefact is never an error here: the
view that depends on it prints the command that would write it.

---

## Validation

`golden.json` is written beside `codebook.json` by `gaf codebook organise` (above); there
is no `golden.json` at the repository root, so give the path the organise step wrote:

```bash
uv run gaf validate agreement --human runs/human200/golden.json \
  --machine runs/process200/assignments.json --data runs/process200/corpus.json
```

`scored.json` has to exist before anything can read it, and **no command writes it** — it
is a pooled table of `(response_id, text, score, group)` that you assemble from whatever
score the study is testing. Build it first. From a completed run, with the score derived
from the codes:

```bash
uv run python -c "
import json
from gaf.ingest.corpus import load_corpus
rows = [{'response_id': r.id, 'text': r.content, 'group': r.source}
        for r in load_corpus('runs/state/corpus.json')]
json.dump(rows, open('runs/state/scored.json', 'w'), indent=2)
"
```

Then, and only then:

```bash
# --score-from codes derives the score from each response's codes, so it needs the codebook
uv run gaf validate lexical --table runs/state/scored.json --score-from codes \
  --codebook runs/state/codebook.json
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

**This has already been run once, against the 20-response seed sample**
([`results/india-process-1-20/07-calibration.md`](../results/india-process-1-20/07-calibration.md)):
τ_high and τ_low move to 0.95 on only 18 candidate pairs — too few to move a threshold
on, by the module's own reading — and τ_fit's F1 is flat from 0.45 to 1.00 over 197
code applications, meaning even that many barely discriminates it. τ_high = 0.80,
τ_low = 0.45 and τ_fit = 0.30 remain unmoved in `gaf/config.py`. Re-run it whenever a
larger golden set arrives, or against the 200-response corpus once its own human coding
covers enough of it:

There is **no CLI subcommand for this** — it is a Python API, because it is run
deliberately, when a golden set of a useful size exists, rather than routinely:

```bash
uv run python -c "
import json
from gaf.checks.health import calibrate_thresholds
from gaf.config import CodingRules
from gaf.embed.service import EmbeddingService
from gaf.ingest.xlsx import read_coded_xlsx
from gaf.models import Assignment

human = read_coded_xlsx('../Grounded AI Futures/data/<his file>.xlsx')
machine = [Assignment.from_json(r) for r in json.load(open('runs/state/assignments.json'))]
report = calibrate_thresholds(human, machine, EmbeddingService(), CodingRules())
print(report.paragraph())
json.dump(report.to_json(), open('runs/state/calibration_report.json', 'w'), indent=2)
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
uv run gaf run --corpus runs/state/corpus.json --out runs/state --live
```

Two coders from **different providers** and a judge from a **third** — the epistemic
diversity is the point, and it is also what makes disagreement a meaningful escalation
signal. The provider triple is configured, never hard-coded.

**Before the first live run, know what it will cost.** In offline runs the code–evidence
fit check accounts for the large majority of frontier calls, because the fallback
embedder cannot separate a code label from a quote. Whether a real embedding model does
is an open empirical question. Budget for the worst case of one judge call per quote,
watch the `llm_calls` table on a small batch first, and read ADR-0019 and ADR-0022.

**The registry's prices carry the date they were read.** `DEFAULT_LIVE_REGISTRY` in
`gaf/config.py` is the only registry `--live` reads, and each of its four bindings now
records a `priced_on` date beside its two rates — 23 September 2026, from the providers'
own pages (ADR-0048). `stats.llm.cost_usd` is only as good as those four numbers, so
check them before a paid run: the coder-B rate is an introductory one that rises on
1 January 2027, and a model id that has been retired fails on the call, not before it.

Responses are cached by content hash, so a re-run costs nothing for anything unchanged.

---

## Exporting results for a collaborator

A run directory is the coded corpus, verbatim, and stays gitignored. To share the
*results* — what was found, not what respondents wrote — export them:

```bash
make results RESULTS_RUN=runs/process RESULTS_OUT=results/india-process-1-20
```

`scripts/export_results.py` reads the run and writes numbered Markdown files (inputs,
his codebook profiled, structural checks, clustering, saturation, agreement, calibration,
the machine run) plus the two SVGs. It never emits a segment, quote, highlight content or
response body, and after writing it re-reads every file it produced against every text it
was told to withhold; a hit aborts the export and deletes the output. The result directory
is tracked, so `make provenance` covers it as well. Write the narrative `README.md` in the
result directory by hand, from those files, and keep respondent text out of it too.

**The full 200-response corpus produces more than one run** — a cold baseline, a human
coding, a seeded run and its halt-and-resume pair — and `make results` only takes one
`RESULTS_RUN`. Run the exporter directly for the rest:

```bash
uv run python scripts/export_results.py \
  --run runs/process200 --human runs/human200 \
  --seeded runs/process200-seeded --halted runs/process200-halted \
  --resumed runs/process200-resumed \
  --out results/india-process-1-200 --label "India Process sample, responses 1-200"
```

`--human` takes the directory `gaf codebook organise` wrote (above): its `golden.json`
is the row-oriented human coding, and its `codebook.json`, `organised.json` and
`tree.mmd` are read alongside it. `--run` is the cold baseline; `--seeded`, `--halted`
and `--resumed` are the runs from "A seeded run, a halted run, and its resumption",
above.

Every description this exporter emits — the PI's own imported ones included — is
tested individually against every text it was told to withhold before it is written; a
colliding definition is replaced by its code name plus a fixed withheld-marker, never
by silently passing the whole document through. This is the operational half of the
description-shareability limitation above: withholding examples is not the same
guarantee as withholding a definition, and this exporter is where the second guarantee
actually lives.

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
