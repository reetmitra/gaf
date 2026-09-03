# gaf — Grounded AI Futures

A reproducible hybrid human–LLM **grounded-theory coding pipeline** for the research
project *AI Futures and Analysis*.

> **RQ:** What are the constituent elements of global AI futures?

Input is open-ended survey responses about AI in 2050. Output is a two-level grounded
codebook, a per-response binary occurrence matrix, a hierarchical cluster analysis of
that matrix, and a verification dossier a methods reviewer can audit line by line.

## Start here

```bash
uv sync --all-groups
```

```bash
make demo
```

That codes a synthetic corpus end to end — two coders, every check, the router, the
store — and writes a run report, a codebook and an HTML explorer to `runs/demo/`. It
needs **no API key and no network**. Run it twice: the codebook JSON and the
snapshot-id sequence are byte-identical.

```bash
make check-all      # ruff, mypy, and the full offline suite
```

## Three properties, non-negotiable

1. **Offline-first.** The whole pipeline runs with mock model clients and a lexical
   embedding fallback, producing byte-identical output across runs. Live models are an
   opt-in flag, never a prerequisite for tests or CI.
2. **Auditable.** Every artefact is content-addressed and replayable. A finding, a code,
   a merge, a judge ruling, a dropped quote — each is a row with an id, a timestamp, a
   snapshot reference and the inputs that produced it. The audit log is append-only and
   snapshots are immutable, enforced by database triggers rather than by convention.
3. **Simple in the flow, complex in the substrate.** Complexity may live in
   infrastructure. It may not live in the control flow.

## The whole architecture

```
FAST LOOP — per response (cheap, parallel, stateless)
  response + its survey question
    -> deterministic prep: segmentation, dedup check, context assembly
       (top-k codes by embedding + hierarchy skeleton, from a FROZEN snapshot)
    -> Coder A (provider 1) and Coder B (provider 2), independently, identical context
    -> STRUCTURAL checks S1-S6   (deterministic; no embeddings, no LLM)
    -> SEMANTIC   checks M1-M4   (embedding-first; judge only in the grey zone)
    -> agree? accept  |  grey zone? -> Judge (frontier, provider 3)
    -> integrate (merge / create) -> write to the blackboard

SLOW LOOP — per checkpoint (rare, expensive, HUMAN-GATED)
  health + saturation metrics -> Refactorer proposes an edit script
    (split / re-parent / merge / batch-rename)
    -> HUMAN GATE: accept, reject or edit each operation
    -> apply -> new snapshot -> changelog

ANALYSIS TAIL (deterministic, no models)
  binary occurrence matrix -> low-frequency filter -> Ward's HCA
    -> agglomeration schedule -> cluster means
  respondent metadata joined ONLY here, never during coding

VALIDATION (deterministic, no models)
  human-vs-machine agreement on the golden set; L1 lexical vocabulary check
```

Two loops. Three LLM roles — Coder, Judge, Refactorer. One store. One deterministic
tail. **Anything in that diagram without a model name is plain Python.**

## Documentation

| Document | What it is for |
|---|---|
| [`docs/METHODS.md`](docs/METHODS.md) | methods-appendix prose, quotable in the paper |
| [`docs/VALIDATION.md`](docs/VALIDATION.md) | the verification dossier — every check, why it exists, and what it cannot see |
| [`docs/RUNBOOK.md`](docs/RUNBOOK.md) | operator guide, including the human-gate workflow |
| [`docs/CODING_RULES.md`](docs/CODING_RULES.md) | the PI's rules, each with the verbatim quotation behind it |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | the design law, and where the complexity actually lives |
| [`docs/DECISIONS.md`](docs/DECISIONS.md) | the ADR log — every non-obvious choice, including the ones that turned out badly |

## Data

Real corpora live **outside** the repository. `data/` is gitignored except
`data/synthetic/`, every spreadsheet and document extension is excluded repository-wide,
and the test suite builds its own workbooks in-process and codes a wholly invented
corpus on response ids in the 200s, which cannot collide with a real sample.

**One deliberate exception.** `docs/CODING_RULES.md` reproduces the principal
investigator's own negative examples from his `GPTPrompts.docx`, and those quote
respondents by id. They are kept at his explicit request: they are his working
document, and the coding rules are only defensible with the quotation attached. They
appear nowhere else — in particular the coder prompt, which is sent to model providers,
carries paraphrases instead.

That distinction exists because an earlier version of this repository made an
unconditional claim here that was false: fixture text drawn from real responses had been
committed, and a check that matched *file extensions* could not see it. See ADR-0024 for
what happened and what now tests the actual property.

## Three things a newcomer should know before trusting a number

- **The thresholds are uncalibrated.** τ_high = 0.80, τ_low = 0.45 and τ_fit = 0.30 were
  set against a stand-in embedder and have never been checked against human judgment.
  The calibration module is built and produces a full curve the day the PI's
  hand-codings arrive.
- **Offline similarity statistics describe the fallback embedder, not the codebook.**
  In particular the code–evidence fit check does not discriminate offline, so its
  warnings in a `make demo` run are artefacts. The run report says so where the counts
  appear. See ADR-0019 and ADR-0022.
- **Read the agglomeration schedule before quoting a cluster count.** The inherited rule
  assumes the largest break falls near the root of the tree; on a small sample it may
  not, and the rule then returns a degenerate answer. It was deliberately left
  unpatched. See ADR-0020.
