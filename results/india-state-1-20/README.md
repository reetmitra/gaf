# Machine run — India State sample (responses 1–20), under its own question

*10 September 2026. The offline stand-in coder on the State sample, re-run with the v3
question ("In 2050, what kind of roles do you think AI will play in your society?") after
ADR-0029 found the earlier runs had used the Process question.*

**There is no human coding for this sample.** Nothing here measures agreement with the
principal investigator; that is the Process sample's job
([`../india-process-1-20/`](../india-process-1-20/README.md)). What this directory shows
is the pipeline running end to end on the second real sample under the right question,
and what the offline coder and the deterministic tail do with twenty responses. **No
respondent's words appear in this directory.**

| file | what it holds |
|---|---|
| [01-inputs.md](01-inputs.md) | the twenty responses: number, notes, words, machine assignments per response |
| [04-clustering.md](04-clustering.md) | Ward's HCA over the machine's coding: filter, schedule, clusters, dendrogram |
| [05-saturation.md](05-saturation.md) | new codes per batch |
| [08-machine-run.md](08-machine-run.md) | counts, findings by check and by marker, every ERROR and WARN, the machine codebook |

---

## 1. The question variant, settled

The same workbook was ingested twice, with v2 and with v3, and both were run. Response
bodies, all 224 assignments, the 18-code codebook with its descriptions, and the three
snapshot ids are identical. Only the model-call statistics differ, because the prompt
text does. The mock coder never reads the question, so the earlier State runs were wrong
in form and not in substance. `gaf ingest` now prints the question it attached and warns
when a file named *State* is ingested as v2, or *Process* as v3.

## 2. What the offline coder produced

```
responses 20   segments 170   assignments 224   codes 18 in 6 families
routes     CREATE 18   MERGE 79   JUDGE 0
dropped    5 candidates, all structural (S2: no quote could be verified)
coder agreement rate 0.922
```

Two catch-all codes, `adoption-social_change` (72) and `future-imagined_scenario` (69),
account for 141 of the 224 assignments. That is the keyword table's fallback behaviour,
not a finding about the responses. Fourteen of the 18 codes are the same names the
coder produced on the Process sample, which is what a fixed keyword table does.

The five S2 errors are candidates whose only quote could not be located in the response;
each was dropped at the gate, and the surviving codebook passes `gaf check all` with no
ERROR. The four M1 warnings are coder disputes and unmatched proposals, all routed
deterministically; the judge was never called.

## 3. Clustering at n = 20 is degenerate, and the schedule says so

The frequency filter keeps 14 of 18 codes. Ward's schedule puts its largest break at
**stage 2 of 19**, near the leaf end of the tree, so the Chan/Essary rule asks for
20 − 2 = 18 clusters: 17 non-empty ones, 14 of them singletons. The analysis records
its own verdict in the schedule's warnings:

> *The rule assumes the largest break falls near the root; at this sample size it does
> not, and this count is degenerate rather than a finding. Take the count from a larger
> corpus, or set `AnalysisConfig.n_clusters` explicitly and report it as an override.*

It also lists the late breaks a reader would take instead: stage 18 (Δ 0.821) → 2
clusters, stage 17 (Δ 0.423) → 3. This is ADR-0020's fragility, seen on real data:
the rule is followed, the count is reported, and the report refuses to call it a result.

Saturation: batch 1 introduced 15 codes, batch 2 another 3. Not saturated; with a
keyword table the curve flattens because the table is finite, not because the data is.

## 4. What this sample is for

It is the second of the two survey questions. The *Process* question asks about impacts
over time; the *State* question asks about roles at a point in time. Whether the two
produce different constituent elements is a question for the live coder on both full
corpora, with his coding of both to validate against. Until then this directory is a
smoke test under the right question, not a finding.

## 5. Reproduce

```bash
uv run gaf ingest --xlsx "../data/NarrativeState(IndiaSample1-20).xlsx" --question-variant v3 --out runs/state/corpus.json
uv run gaf run --corpus runs/state/corpus.json --run-id state --offline --out runs/state
uv run gaf report --run runs/state
uv run gaf check all --codebook runs/state/codebook.json --data runs/state/corpus.json
uv run gaf analyse --assignments runs/state/assignments.json --data runs/state/corpus.json --out runs/state/analysis
make results RESULTS_RUN=runs/state RESULTS_OUT=results/india-state-1-20 RESULTS_LABEL="India State sample, responses 1-20"
```
