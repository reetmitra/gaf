# Architecture

## The design law

> **Complexity may live in infrastructure — deterministic code, one versioned
> embedding space, a SQLite blackboard, routing rules. It may not live in the control
> flow.**

The reader-visible architecture is **two loops, and four LLM roles — three of them
inside the loops, one outside**. If the control flow cannot be printed in a methods
appendix on one page, it is wrong.

Concretely:

- No agent framework. Plain Python, provider SDKs, structured outputs.
- No agent-per-role chain. Slicing, quote checking, comparison and change tracking are
  deterministic code, not model calls. Each agent removed is a removed source of drift,
  cost and non-reproducibility.
- No vector database, no fine-tuning, no cross-call memory. A NumPy matrix and cosine
  similarity are sufficient at this corpus size. Human corrections are recycled as
  few-shot examples, never trained in.
- Deterministic code runs *before* any LLM call. A model is consulted only where the
  geometry is genuinely ambiguous.
- Checks **report**; the router and the audit log **decide and record**. A checker
  never mutates state.

## The flow

```
FAST LOOP — per response (cheap, parallel, stateless)
  response + its survey question
    → deterministic prep: segmentation, dedup check, context assembly
      (top-k codes retrieved by embedding + hierarchy skeleton from a frozen snapshot)
    → Coder A (mid-tier model, provider 1)  ┐
    → Coder B (mid-tier model, provider 2)  ┘  independent, same context
    → STRUCTURAL checks  S1–S5   (deterministic; no embeddings, no LLM)
    → SEMANTIC checks    M1–M3   (embedding-first; judge only in the grey zone)
      [S6 codebook invariants and M4 near-duplicate leaves run once, at run close]
    → agree? → accept   |   grey zone → Judge (frontier model, provider 3)
      (a dispute below τ_low is kept and flagged, not escalated — see below)
    → integrate into the codebook (auto-merge / auto-create / judge-decided)
    → write to the blackboard
    → at every batch boundary: the DECISION MATRIX evaluates the handover — near
      duplicates, new-code growth and the spike rule, the floor, the cadence — and
      records a verdict on the audit log. It reports; it never blocks the fast loop.

HANDOVER (the matrix's own column — taken by neither loop, decided between them)
  a checkpoint comes due
    → `gaf run --halt-on-checkpoint` stops the fast loop at that batch boundary
    → the human gate below opens on `gaf checkpoint`
    → `gaf run --seed-codebook ... --skip-coded ...` resumes without recoding anything

SLOW LOOP — per checkpoint (rare, expensive, human-gated)
  blackboard
    → health + saturation metrics (deterministic)
    → Refactorer (frontier model; whole codebook + usage stats)
        emits an edit script: split / re-parent / merge / batch-rename
    → HUMAN GATE — reviews the diff, accepts / rejects / edits per operation
    → apply → new snapshot → changelog

DEFINER (outside both loops — runs once, over a coding a person has already finished)
  code-text pairings, already organised into a two-level codebook (deterministic)
    → per code: name, parent, sibling names, every one of its own segments
    → Definer (frontier model, the same slot the Refactorer uses)
        emits a 1–3 sentence description, grounded in that code's own text
    → four deterministic guards: refuse an empty, over-long or quoted reply
  never sees a response being coded; cannot rename, merge, split or create a code

ANALYSIS TAIL (deterministic, no models)
  blackboard → binary occurrence matrix → low-frequency filter → Ward's HCA
    → agglomeration schedule → cluster means → cluster interpretation table
  + pattern mapping (which responses share which code combinations)
  + affinity (bottom-up thematic groups of leaf codes, across families)
  + an optional crosswalk mapping this codebook onto a second one
  + respondent metadata joined ONLY here, never during coding

VALIDATION (deterministic, no models)
  human-vs-machine agreement on the golden set  (Alqazlan-style concurrent validation)
  lexical validation: L1 vocabulary extraction under continuous vs binarised framings
```

Two loops. Four LLM roles: Coder, Judge and Refactorer inside the two loops; the
Definer, writing a code's description from a coding a person has already finished,
outside both (ADR-0034). One store. One deterministic tail. Anything in that diagram
without a model name is plain Python.

## Where the complexity actually lives

The substrate carries five mechanisms. Each one exists to prevent a *documented*
failure of the two predecessor studies (Chan 2025; Ng & Chan 2026).

### 1. Frozen, content-addressed snapshots — against order dependence

A coder reads a `snapshot_id`. Only the slow loop writes a new one. A snapshot id is
the content hash of its codebook JSON, and the codebook JSON contains no wall-clock
timestamps — which is what makes two runs byte-identical and what makes "re-running a
batch against the same snapshot reproduces the same output" a checkable claim.

Immutability is enforced by the database, not by convention: `gaf/store/schema.py`
installs triggers that abort any `UPDATE` or `DELETE` on `snapshots` and on `audit`.

### 2. One versioned embedding space — against weak cross-model correlation

The predecessor matched codes with TF-IDF cosine blended with word-set Jaccard
(0.6/0.4) at a threshold of 0.3, and recovered 21 matched pairs against 66 and 73
unmatched codes. Lexical overlap is not meaning.

Here a single space (`EmbeddingSpaceConfig.space_id`, recorded with every score)
serves retrieval, the dedup gate, cross-coder matching and code↔evidence fit. Codes
are rendered by exactly one function, `gaf.embed.protocol.code_text`. Cross-coder
matching is Hungarian assignment, not greedy. Routing uses a **two-threshold band**
(τ_high / τ_low) so that "certainly the same", "certainly different" and "genuinely
ambiguous" are three outcomes rather than two.

### 3. The blackboard — against context loss across an agent chain

All state lives in one SQLite database. Every model call is stateless and re-grounds
from canonical sources. Handoffs carry ids, not prose. The audit log is append-only.

### 4. Disagreement routing — against cost, and for epistemic diversity

**What actually escalates.** Only the **grey band** reaches the judge: a cross-coder
score between τ_low and τ_high, an M2 route in the same band, or an M3 fit below τ_fit.
A pair scoring *below* τ_low is **disputed and kept-and-flagged**, not escalated — the
two coders proposed genuinely different codes, and there is no single question a judge
could answer that would not amount to dropping one of them on a meaning call the fast
loop is not allowed to make. `router.escalates()` is the one place this rule is
written.

Two mid-tier coders from *different providers* code the same response against the same
context. Agreement — the common case — costs nothing extra. Only disagreement and
grey-zone similarity reach the frontier judge. Epistemic diversity and cost control
are the same mechanism, which is why `ModelRegistry.distinct_coder_providers()` is a
property worth asserting.

### 5. A wide operation set behind a human gate — against codebook flattening

The predecessor's fast loop could only create, merge-to-existing, merge-to-candidate,
rename or no-op. It could not split an overloaded code or re-parent a node, so instead
of restructuring it accreted parallel concepts, then merged semantically different
ideas on superficial lexical overlap, and the downstream clustering collapsed to two
clusters where three were expected.

Here the fast loop **never restructures the codebook** — coders only propose, and integration may merge evidence into a code or admit a new one, but nothing splits, re-parents or renames. Structural
edits happen only in the human-gated slow loop, and `Operation` includes `split` and
`reparent` precisely because their absence is the documented cause of the failure.

### 6. The decision matrix — where the handover between the loops is written down

The PI asked, in one of his review notes, for a decision matrix between the fast loop
and the slow loop: which decision is taken where, by whom, under what condition. Prose
would have answered that once and then rotted the first time a threshold moved. Instead
`gaf.pipeline.decision_matrix.DECISION_MATRIX` is data — a tuple of frozen rows, each
naming its loop, who decides it (`deterministic`, `coder`, `judge`, `refactorer`,
`human`), the condition rendered against the run's own thresholds, and the function
that implements it. Tests resolve every named function and assert that every routing
band, every checkpoint trigger and every structural operation is covered by some row,
so the matrix cannot drift from the code it describes.

"Is the slow loop due" is answered by neither loop — the fast loop only measures and
reports, the slow loop needs a human at a terminal — so the matrix gives that question
its own `loop` value, **handover**, evaluated at every batch boundary rather than only
once at the end of a run. `gaf run --halt-on-checkpoint` stops the fast loop at the
first batch boundary the matrix calls due; `gaf checkpoint` opens the human gate; a
seeded, `--skip-coded` resume picks the coding back up without repeating any of it
(ADR-0033, ADR-0035). The two loops of the diagram above are still two: the handover is
where they meet, not a third one.

## Why the human gate is where it is

The Vaccaro et al. (2024) meta-analysis finds that human–AI combinations average
*worse* than the better of the two alone (Hedges' g = −0.23, 95% CI −0.39 to −0.07).
The losses concentrate in **decision tasks** (g = −0.27), the gains in **creation
tasks** (g = 0.19), and synergy is moderated by whether the division of labour is
predetermined.

Item-by-item human verification of each machine coding is exactly the decision-task
overlay that the meta-analysis finds harmful. So the human gate does not sit there. It
sits at the **codebook-refactor level**, where the task is generative (restructure the
hierarchy) and the division of labour is fixed in advance: the machine proposes an
edit script, the human accepts, rejects or edits each operation. Less labour per
checkpoint, more leverage per decision.

See `docs/METHODS.md` for the full argument in methods-appendix prose.

## Vocabulary

This study is **inductive grounded theory**, not framing analysis. The vocabulary
throughout the code, the docs and every user-facing string is grounded theory's:
*initial coding, constant comparison, memoing, theoretical sampling, theoretical
saturation, core category, storyline*; and for the outputs, *codes, families,
clusters, themes*.

There is no `Function` enum, no framing functions, and the word "frame" does not
appear in text this project writes. It does appear, six times, in
`results/india-process-1-200/02-human-codebook.md` — every one inside a description the
principal investigator wrote, imported by `--definitions` and passed through
unrewritten, which is his data and which ADR-0032 deliberately exempts from this rule.

## Validation principles

Every module docstring names the principle it serves. The four are from the SLE final
report (Ng & Chan 2026), which derives them as the epistemic risks that HITL
qualitative analysis has to manage:

| Principle | Risk it answers | How this build serves it |
|---|---|---|
| **Transparency** | the black-box problem | content-hash snapshots, an append-only audit log, every finding a row, an HTML codebook explorer, a run report with a CHECKS section |
| **Reliability** | reproducibility at scale | offline determinism, frozen snapshots, seeded everything, one normalisation function, byte-identical artefacts |
| **Interpretive depth** | flattening nuance into generic patterns | the human gate at refactor level, keep-and-flag over auto-resolution, the unmatched lists in the agreement report |
| **Epistemic diversity** | one model's idiosyncrasy passing as a finding | two coders from different providers, a third-provider judge, cross-model codebook comparison |

## Module map

| Path | Role |
|---|---|
| `gaf/models.py` | the shared vocabulary — frozen dataclasses |
| `gaf/config.py` | every threshold, the coding rules, the model registry |
| `gaf/textnorm.py` | the single normalisation function every span is defined against |
| `gaf/ids.py` | content hashing, deterministic id minting |
| `gaf/store/` | the blackboard: schema, snapshots, audit log |
| `gaf/ingest/` | spreadsheet/CSV readers, the tagged-pairing organiser, the definitions reader, corpus assembly, question attachment |
| `gaf/llm/` | client protocol, three providers, deterministic mocks, disk cache |
| `gaf/embed/` | the embedding service and the matcher (cosine, Hungarian, routing) |
| `gaf/agents/` | the four LLM roles — Coder, Judge, Refactorer in the loops, the Definer outside them — and their versioned prompt templates |
| `gaf/checks/` | S1–S6, M1–M4, codebook health, threshold calibration, code growth and the spike rule |
| `gaf/pipeline/` | prep, the fast loop, the router, the slow loop, the decision matrix |
| `gaf/analysis/` | occurrence matrix, Ward's HCA, agreement, lexical validation, patterns, affinity, the crosswalk |
| `gaf/report/` | the run report, the two HTML pages (the codebook explorer and the shareable views page), the timeline and the reorganisation trail |
| `gaf/cli/` | one module per command, assembled by `parser.py` |

## Frozen contracts

These modules are fixed by Wave 0 and may not be changed by a later agent. A change
request goes to the orchestrator, who amends and re-broadcasts.

- `gaf/models.py`
- `gaf/config.py`
- `gaf/checks/contracts.py`
- `gaf/llm/base.py`
- `gaf/embed/protocol.py`
- `gaf/store/schema.py`
- `gaf/textnorm.py`

Amended twice since Wave 0, both times additively and both times recorded: ADR-0015
added `CodingRules.max_quote_words`; ADR-0033 added three fields to
`CheckpointPolicy` (`spike_factor`, `spike_window`, `spike_min_new_codes`) for the
growth-spike rule. Every existing `RunConfig`, stored config echo and golden fixture
reads unchanged either time, which is the property an additive amendment has to keep.
