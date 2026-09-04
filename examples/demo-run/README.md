# examples/demo-run/

A committed snapshot of what `gaf` produces, so you can see the pipeline's output
without installing anything or running a single command.

**This is not real data.** Every response here comes from the fourteen invented
entries in `tests/fixtures/corpus.py` (`synthetic_corpus()`), coded offline with the
deterministic mock LLM clients (`--offline`, no API key, no network call). No human
survey response has ever been in this directory.

## Regenerating it

```
make example
```

This runs a fresh `make demo` (`gaf run` + `gaf report` over the synthetic corpus)
and `make analyse` (`gaf analyse`), then copies the files below out of `runs/demo/`
into this directory. `runs/demo/` itself is gitignored — this directory is the
durable copy.

Two runs are deterministic except for `stats.json`'s `cache_hits` field and the
matching line in `report.txt`, which record whether the LLM response cache was warm;
everything else — codebook, assignments, findings, the analysis artefacts — is
byte-identical run to run.

## What's here

| File | What it is |
|---|---|
| `report.txt` | The human-readable run report: provenance, the codebook summary, the theoretical-saturation table and the CHECKS section (every finding the run produced, by check). |
| `codebook.json` | The coded codebook: every code, its description, its parent, and every verified quote of evidence for it. |
| `codebook.html` | The same codebook as a single self-contained, browsable HTML file — no script, no network request, no external asset. |
| `assignments.json` | The response-to-code assignments the fast loop produced. |
| `findings.json` | Every finding emitted by every check (S1-S6, M1-M4), the full detail behind the CHECKS table in `report.txt`. |
| `stats.json` | Run-level counters: candidates proposed/accepted/dropped, agreement rate, acceptance by origin, cache hits. |
| `corpus.json` | The synthetic corpus this run coded, materialised from `tests/fixtures/corpus.py`. |
| `analysis/occurrence_matrix.json` | The binary response x code occurrence matrix (the CSV form is gitignored repo-wide; this JSON carries the same data). |
| `analysis/clusters.json`, `analysis/clusters.md` | Ward's hierarchical cluster analysis: the cluster assignment, cluster means and the interpretation table, as data and as prose. |
| `analysis/dendrogram.svg` | The HCA dendrogram. |
| `analysis/saturation.json`, `analysis/saturation.md` | The theoretical-saturation curve (new codes per batch), as data and as prose. |
| `analysis/saturation.svg` | The saturation curve, plotted. |

Not included: `gaf.sqlite` (the run's blackboard database — binary) and `audit.jsonl`
(the append-only audit log — timestamped, so not reproducible byte-for-byte).
