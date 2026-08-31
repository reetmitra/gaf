# gaf — Grounded AI Futures

A reproducible hybrid human–LLM **grounded-theory coding pipeline** for the research
project *AI Futures and Analysis*.

> **RQ:** What are the constituent elements of global AI futures?

Input is open-ended survey responses about AI in 2050. Output is a two-level grounded
codebook, a per-response binary occurrence matrix, a hierarchical cluster analysis of
that matrix, and a verification dossier a methods reviewer can audit line by line.

## Three properties, non-negotiable

1. **Offline-first.** The whole pipeline runs end to end with mock model clients, a
   lexical embedding fallback, zero API keys and zero network, and produces
   byte-identical output across runs. Live models are an opt-in flag, never a
   prerequisite for tests or CI.
2. **Auditable.** Every artefact is content-addressed and replayable. A finding, a
   code, a merge, a judge ruling, a dropped quote — each is a row with an id, a
   timestamp, a snapshot reference and the inputs that produced it.
3. **Simple in the flow, complex in the substrate.** Complexity may live in
   infrastructure. It may not live in the control flow.

## The whole architecture

```
FAST LOOP — per response (cheap, parallel, stateless)
  response + its survey question
    -> deterministic prep: segmentation, dedup check, context assembly
    -> Coder A (mid-tier, provider 1)  +  Coder B (mid-tier, provider 2)
    -> STRUCTURAL checks S1-S6   (deterministic; no embeddings, no LLM)
    -> SEMANTIC   checks M1-M4   (embedding-first; judge only in the grey zone)
    -> agree? accept   |   disagree / grey zone? Judge (frontier, provider 3)
    -> integrate into the codebook -> write to the blackboard

SLOW LOOP — per checkpoint (rare, expensive, human-gated)
  blackboard -> health + saturation metrics -> Refactorer proposes an edit script
    -> HUMAN GATE (accept / reject / edit per operation) -> apply -> new snapshot

ANALYSIS TAIL (deterministic, no models)
  binary occurrence matrix -> low-frequency filter -> Ward's HCA
    -> agglomeration schedule -> cluster means
  respondent metadata is joined ONLY here, never during coding

VALIDATION (deterministic, no models)
  human-vs-machine agreement on the golden set; L1 lexical vocabulary check
```

Two loops. Three LLM roles (Coder, Judge, Refactorer). One store. One deterministic
tail. Anything in that diagram without a model name is plain Python.

## Getting started

```bash
uv sync --all-groups
```

```bash
uv run pytest
```

The suite is fully offline: no API keys, no network, no real survey data.

## Project state

Wave 0 (contracts and fixtures) is complete. The frozen contracts are:

| Module | What it fixes |
|---|---|
| `gaf/models.py` | the shared vocabulary — Response, Segment, Evidence, Candidate, Code, Codebook, Assignment, Operation |
| `gaf/config.py` | CodingRules, RunConfig, every threshold, the model registry, the survey-question variants |
| `gaf/checks/contracts.py` | Severity, CheckFinding, CheckReport, the four M3 fit verdicts |
| `gaf/llm/base.py` | the LLMClient protocol, JSON parsing, enum whitelisting, fail-safe defaults, retry, accounting |
| `gaf/embed/protocol.py` | the Embedder protocol, `code_text`, the MERGE/CREATE/JUDGE routing band |
| `gaf/store/schema.py` | the SQLite blackboard, with an append-only audit log enforced by triggers |
| `gaf/textnorm.py` | the single normalisation function every character span is defined against |

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the design and its rationale,
[`docs/CODING_RULES.md`](docs/CODING_RULES.md) for the PI's rules with the verbatim
quotation behind each, and [`docs/DECISIONS.md`](docs/DECISIONS.md) for the ADR log.

## Data

**No human survey response is ever committed.** `data/` is gitignored except
`data/synthetic/`, and every spreadsheet extension is excluded repository-wide. The
test suite builds its own workbooks in-process and codes an invented corpus.
