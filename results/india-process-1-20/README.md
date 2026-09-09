# Coding results — India Process sample (responses 1–20)

*Prepared 9 September 2026, in answer to: "Please send the code and results … I would like
a look, especially at the coding results."*

Everything on this page is reproduced by the commands in §8 from the two files sent:
the coding export `CodebookIndiaProcess(1-20).xlsx` and the corpus
`CorpusSample(IndiaProcess1-20).xlsx`. The numbered files beside this one are generated
from the run directory by `make results` and hold the full tables; this page is the
reading of them. **No respondent's words appear in this directory.** The segments behind
the agreement lists are in the local run directory, which never enters git.

| file | what it holds |
|---|---|
| [01-inputs.md](01-inputs.md) | the twenty responses (number, notes, words, highlights), and how the 342 highlights were placed |
| [02-human-codebook.md](02-human-codebook.md) | his 117 codes by family and by count, in the export and in this sample |
| [03-structural-checks.md](03-structural-checks.md) | his coding against his own rules, S1–S6 |
| [04-clustering.md](04-clustering.md) | Ward's HCA over his coding: filter, schedule, clusters, means, dendrogram |
| [05-saturation.md](05-saturation.md) | new codes per batch |
| [06-agreement.md](06-agreement.md) | his coding against the machine's, both ways of matching codes |
| [07-calibration.md](07-calibration.md) | the threshold sweeps, the module's recommendations and its own caveats |
| [08-machine-run.md](08-machine-run.md) | the offline run: counts, findings, the machine codebook's names and descriptions |

**One sentence:** the pipeline ran end to end on his files; his own coding passes his own
rules with three flags worth discussing; the clustering at n = 20 does not produce a
structure; and agreement between his coding and the *offline stand-in* coder is nil, for a
reason that is now precisely diagnosed and points at what to ask him for.

---

## 1. What arrived, and what it is

| File | What it turned out to be |
|---|---|
| `CodebookIndiaProcess(1-20).xlsx` | A coding-tool highlights export: **342 highlights**, columns `id · document · tag · content`. One document: *"Narrative Process Responses India (1-100)"*. **No response number** on any row. |
| `CorpusSample(IndiaProcess1-20).xlsx` | **20 responses**, one column, no header, the number folded into the text. Ids 11–61, non-contiguous. **Two different responses are numbered 44.** |

Neither file matched a shape the pipeline knew. Both readers refused rather than
guessing; two new readers were written and tested (ADR-0029), and the corpus now ingests
with one command. The second response numbered 44 is kept as id 1044, with the number as
written on its record.

**The export covers 100 responses; the sample is 20 of them.** Every highlight was placed
by locating its text in the corpus:

```
342 highlights:  147 mapped to a response (all exact, 0 fuzzy)
                   2 ambiguous — the single words "defence" and "education", each present in responses 14 and 33
                 193 unlocated — best fuzzy score 0.41–0.85, all under the 0.85 line: text from the other 80
```

The 147 are the golden set for this sample: 2–17 per response, every response covered.
They carry **76 of his 117 codes**.

**This is a different sample from the one the pipeline was developed on.** The earlier
file was *NarrativeState* — the "in 2050, what roles" question. This is *Process* — the
"from now to 2050, what impacts" question. That naming resolves an open item and exposes
a mistake: the earlier State runs used the Process question text in the coder prompt. The
mock coder never reads the question, so those results are unaffected in substance. The
State sample was re-run with v3 on 10 September 2026 (`runs/state/`, local): response
bodies, assignments, codebook and snapshot ids are identical to the v2 run, and only the
model-call statistics differ, because the prompt text does. `gaf ingest` now prints the
question it attached and warns when the file name disagrees with the variant.

---

## 2. His codebook, profiled

117 codes in 16 families; phrase-level coding (segments 1–27 words, median 8); 10 segments
coded twice, none three times — his own "at most two codes on one piece of text" rule,
visible in the data.

| Family | Codes | Family | Codes |
|---|---:|---|---:|
| applications | 22 | safety | 5 |
| positive_impacts | 16 | future | 5 |
| negative_impacts | 13 | requirements | 4 |
| key_sectors | 10 | ease | 3 |
| improvement | 8 | progress | 3 |
| AI | 8 | efficiency | 1 |
| impact | 6 | key | 1 |
| jobs | 6 | | |
| adoption | 6 | | |

Most-used codes across all 342 highlights: `efficiency` 16, `ease-work` 14,
`positive_impacts-general` 13, `positive_impacts-problem-solving` 12, `ease-life` 11,
`future-positive` 11.

Two things a reader notices that the checks also caught (§3): `efficiency` is the only
bare top-level code; and `key-sectors-elder_care` (hyphen) sits in a family of its own,
apart from the ten `key_sectors-…` codes (underscore) — almost certainly a typo, and one
the first-hyphen split faithfully reproduces.

---

## 3. His coding against his own rules

`gaf check structural` over the 147 rows, using the rules transcribed verbatim from his
`GPTPrompts.docx`:

```
check  ERROR  WARN  what it checks
S1         0   134  a candidate has a name, a description and at least one quote
S2         0     0  every quote locates in the response (with a character span)
S4         0     0  at most two codes on the same piece of text
S3         0     7  two-level name grammar; sub-code before new top-level
S5         0     1  the usual two to twelve codes per response
RESULT: PASS — no ERROR finding
```

**Zero errors.** Every segment locates. He never puts more than two codes on one piece of
text. Three flags, each worth a minute:

- **S3 × 7 — `sub_code_first`, all on `efficiency`.** His rule: *"consider adding a
  second-level code first before adding a top-level code."* `efficiency` is the only
  bare top-level code in the export: used 16 times across the 342 highlights, 10 times
  in this sample, while `ease-work`, `improvement-speed` and
  `positive_impacts-productivity` exist beside it. The check fires on every use after
  the first: *"The family 'efficiency' already exists in the codebook; consider a
  sub-code of it before adding another top-level code."* This is his own negative-example
  category — *"you created a code when you could have used a sub-code"* — applied to his
  own coding. A question, not a verdict: is `efficiency` meant to be a family?
- **S5 × 1 — response 33 carries 14 distinct codes**, above his "usually 2–12". Advisory
  by his own wording; the response is 101 words and got 17 highlights.
- **S1 × 134 — `missing_description`.** Not a coding fault: the export has no column for
  code definitions, so every one of the 134 response–code pairs lacks one. It is,
  however, the input gap that most affects §5. **Ask: are the 117 codes defined anywhere?**

---

## 4. What the clustering does with his coding at n = 20

Chan's method, applied to *his* assignments (binary occurrence matrix → low-frequency
filter → Ward → agglomeration schedule → cluster means):

```
low-frequency filter   keeps 29 of 76 codes (47 appear in only one response)
Ward's linkage         largest break at stage 18 of 19  ->  20 - 18 = 2 clusters
cluster sizes          19 and 1
```

Two clusters — the number the predecessor study was faulted for — but **19 against 1 is
not a structure, it is an outlier**. The singleton is response 51 (103 words, 12
highlights, 11 distinct codes: robotics, self-driving cars, job destruction, automation,
computer operators …), whose *combination* of codes isolates it. Cluster 1's only
prominent code is `ease-work` at 0.47. Ward is known to be outlier-sensitive; Chan's
low-frequency filter is his mitigation, and it cannot help here because all eleven of 51's
codes survive the filter — each appears in at least one other response. The break the
rule cuts on is clear (Δ 0.62 at stage 18; the next largest is 0.32), so this is the
method working as specified on an input too small for it.

Saturation on his coding: batch 1 introduced 47 new codes, batch 2 another 29. The curve
has not flattened. Twenty responses is a seed; his own file, at 100, is the study.

---

## 5. His coding against the machine's — the honest number, and the diagnosis

The machine here is the **offline mock coder**: a deterministic keyword table used so the
pipeline can be tested without a model or a key. It is not a coder; two catch-all codes
account for 134 of its 197 assignments on this sample. Its agreement with an expert's
coding was never the question. **The question was whether the harness works on real
inputs and says something useful when they disagree.** It does.

| Comparison | codes matched | TP | FP | FN | precision | recall | F1 | κ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| as first run (machine codes carry descriptions, his do not) | 1 / 76 | 0 | 85 | 134 | 0.000 | 0.000 | 0.000 | −0.059 |
| name-to-name (no descriptions on either side) | 3 / 76 | 3 | 82 | 131 | 0.035 | 0.022 | 0.027 | −0.032 |
| … on the three codes both sides share | | 3 | 9 | 4 | 0.250 | 0.429 | 0.316 | 0.198 |

**Why the first row is all zeros — and why it is an input problem, not a method one.**
Code-level matching pairs his codes with the machine's in the embedding space at
τ_high = 0.80. His export has code *names* only; the machine codebook has names *and
descriptions*. In the offline lexical space that asymmetry scores the same concept far
below the threshold:

```
                                                        with descriptions   name-only
positive_impacts-problem_solving  ~  positive_impacts-problem-solving   0.696   1.000
positive_impacts-job_creation     ~  positive_impacts-jobs              0.480   0.866
negative_impacts-job_loss         ~  negative_impacts-job_destruction   0.416   0.750
negative_impacts-dependence       ~  negative_impacts-dependency        0.385   0.667
positive_impacts-quality_of_life  ~  improvement-quality_of_life        0.472   0.577
```

Only `future-inevitability`, spelt identically on both sides, cleared τ_high in the first
run — and the machine applied it to one response where he had not, and missed the four
where he had. Name against name, three pairs clear the threshold and the conceptual
matches land in the grey band (0.45–0.80), which is exactly where the live pipeline sends
a pair to the judge. Three things would move this number without touching the method:

1. **his code definitions** (removes the asymmetry);
2. **a live embedding model** in place of the lexical fallback (ADR-0003 — lexical
   overlap is not meaning);
3. **a live coder** in place of the keyword mock.

**The output he asked to look at.** [06-agreement.md](06-agreement.md) carries two lists.
The **blind spots** — 75 of his codes the machine never produced, 143 segments, each with
the nearest machine code and its score — are the only place his own error category *"you
did not generate a new code"* is observable, because a code never invented leaves no
trace inside a run. Six of them, by response number (the segments are in the local
`agreement.md`):

| response | his code | nearest machine code | cosine |
|---:|---|---|---:|
| 33 | `AI-tool` | `future-uncertainty` | 0.250 |
| 51 | `adoption-high` | `adoption-social_change` | 0.224 |
| 11 | `applications-chatbots` | `future-uncertainty` | 0.250 |
| 52 | `applications-robotics` | `applications-automation` | 0.447 |
| 33 | `applications-decision-making` | `applications-data_driven_systems` | 0.324 |
| 45 | `applications-planning` | `applications-education` | 0.250 |

The **over-coding** list (17 machine codes, 196 segments) is the mirror: what the machine
applied that he did not. Segment-level agreement, which asks whether the two attach a
code to the *same span*, is ≈ 0.01 — consistent with the above.

---

## 6. Threshold calibration — first run against real judgment

The calibration module ran against his coding for the first time. It recommended moving
every threshold (τ_fit 0.30 → 0.75, τ_high 0.80 → 0.95, τ_low 0.45 → 0.95) — and
qualified each recommendation in its own notes:

> *tau_fit's F1 maximum is flat from 0.45 to 1.00, so this golden set barely discriminates
> it. tau_high rests on only 18 units, which is too few to move a threshold on; treat the
> curve as a shape, not a measurement.*

With 197 of 197 machine applications unsupported by his coding, "always escalate" and
"always create" maximise F1 trivially. The module detected that, reported it, and wrote
nothing: `CodingRules` in `gaf/config.py` still reads 0.80 / 0.45 / 0.30. That is the
behaviour it was built for: it reports; it never silently changes a constant.
**τ_fit = 0.30, τ_high = 0.80, τ_low = 0.45 remain provisional.** Calibration becomes
meaningful when items 1–3 in §5 are in place. The sweeps are in
[07-calibration.md](07-calibration.md).

The golden-set regression harness also accepted his coding with one environment variable
and no code change; the test that had been skipping since Wave 3 now runs and passes.

---

## 7. What to ask him for

1. **Definitions for the 117 codes.** The export has none; without them every comparison
   is name-against-name-plus-description, which is not a fair test.
2. **The full 100-response corpus.** All 342 highlights would map, and every number in
   §3–§6 would rest on five times the data.
3. **Which response is 44.** Two are. Both were kept (the second as id 1044); he should
   say which is which.
4. **Confirm the question variants:** *Process* = "from now to 2050, what impacts"?
   *State* = "in 2050, what roles"? The file names say so; the earlier State runs used the
   wrong one.
5. **`efficiency`** — intended as a top-level family, or a sub-code of something?
6. **`key-sectors-elder_care`** — a typo for `key_sectors-…`?
7. **Approval for a live run** — the provider triple and a budget. It is the only way the
   agreement number stops being a statement about a keyword table.

---

## 8. Reproduce

From the repository root, with the two files at `../data/` and `../codebook/`:

```bash
uv run gaf ingest --xlsx "../data/CorpusSample(IndiaProcess1-20).xlsx" --question-variant v2 --out runs/process/corpus.json
# map his highlights -> runs/process/golden.json  (snippet in docs/RUNBOOK.md, "The two shapes")
uv run gaf check structural --assignments runs/process/golden.json --data runs/process/corpus.json
uv run gaf analyse --assignments runs/process/golden.json --data runs/process/corpus.json --out runs/process/analysis_golden
uv run gaf run --corpus runs/process/corpus.json --out runs/process && uv run gaf report --run runs/process
uv run gaf validate agreement --human runs/process/golden.json --machine runs/process/assignments.json --data runs/process/corpus.json --out runs/process/agreement_nameonly
GAF_GOLDEN_HUMAN_CODING="$PWD/runs/process/golden.json" uv run pytest tests/test_golden.py -q -rs
make results RESULTS_RUN=runs/process RESULTS_OUT=results/india-process-1-20
```

The run directory `runs/process/` holds the corpus, the golden set, the machine codebook
with its quotes, `codebook.html`, both agreement reports with segments, and the
calibration report. It is gitignored because it contains respondents' words; `make scrub`
removes it before the directory goes anywhere.

---

## 9. Meeting — a 20-minute shape

| min | section | one line |
|---:|---|---|
| 0–2 | §1 | What arrived, what it is, 147 of 342. Ask for the other 80 (ask 2). |
| 2–5 | §2 | His codebook profiled; `efficiency` and the elder_care typo (asks 5, 6). |
| 5–9 | §3 | **His coding passes his rules: 0 errors.** The three flags. Ask for definitions (ask 1). |
| 9–12 | §4 | 19 vs 1 is an outlier, not two clusters. Twenty is a seed. |
| 12–17 | §5 | Agreement is nil, and precisely why. The blind-spot list is the thing to hand him. |
| 17–19 | §6 | Calibration ran and declined to move a threshold on this input. |
| 19–20 | §7 | The live run is the next result (ask 7). |

Lead with §3. A pipeline that checks the expert's coding against the expert's own rules
and finds nothing invalid — and three things worth a conversation — is the most credible
opening available, and it puts him in the reviewer's seat rather than the audience's.
