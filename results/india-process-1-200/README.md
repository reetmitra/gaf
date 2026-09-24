# Coding results — India Process, responses 1-200

Everything on this page is produced by `scripts/export_results.py` from run
directories that stay on the researcher's machine. **No respondent's words appear in
this directory.** The exporter is fed every text those directories hold — both corpora,
every segment, every quote, every highlight, every example the organised codebook kept
— re-reads every file it writes, in every subdirectory and of every type, and deletes
the whole export rather than ship a file sharing a 20-character run with any of them.

**The machine coder here is not a model.** Every command below ran offline: the
coders, the judge and the refactorer are deterministic mocks, and the embedding space is
the lexical fallback. The offline coder is a keyword table. Its agreement with an expert
was never the question and is not reported as if it were; what is reported is whether
the harness measures, explains and reproduces a disagreement on real inputs.

## What is in this directory

| file | what it holds |
|---|---|
| [01-inputs.md](01-inputs.md) | the corpus, and how his highlights were placed onto it |
| [02-human-codebook.md](02-human-codebook.md) | his codebook organised: tree, counts, notes, definitions |
| [03-structural-checks.md](03-structural-checks.md) | his coding against his own rules |
| [04-clustering.md](04-clustering.md) | Ward's HCA: filter, schedule, clusters, means, dendrogram |
| [05-saturation.md](05-saturation.md) | new codes per batch |
| [06-agreement.md](06-agreement.md) | his coding against the machine's, both ways of matching codes |
| [07-calibration.md](07-calibration.md) | the threshold sweeps and what they say about sample size |
| [08-machine-run.md](08-machine-run.md) | the offline run: counts, findings, the machine codebook |
| [09-growth.md](09-growth.md) | code growth, the spike rule and saturation, both codings |
| [10-handover.md](10-handover.md) | where the decision matrix first hands over, and the matrix itself |
| [11-patterns.md](11-patterns.md) | pattern groups and the codes that travel together |
| [12-affinity.md](12-affinity.md) | themes that cut across the families |
| [13-crosswalk.md](13-crosswalk.md) | the machine's codebook mapped onto his |
| [14-timeline.md](14-timeline.md) | when each code was generated, and what happened to it |
| [15-seeded-run.md](15-seeded-run.md) | coding into his organisation — a demonstration, not a result |
| [16-halt-and-resume.md](16-halt-and-resume.md) | halting at the handover, and resuming without loss |
| [views-machine/views.html](views-machine/views.html) | a self-contained page of figures — no script, no network request, no respondent text |
| [views-machine/tree.mmd](views-machine/tree.mmd) | the codebook tree as Mermaid source (names and counts only) |
| [views-human/views.html](views-human/views.html) | a self-contained page of figures — no script, no network request, no respondent text |
| [views-human/tree.mmd](views-human/tree.mmd) | the codebook tree as Mermaid source (names and counts only) |
| [tree.mmd](tree.mmd) | the codebook tree as Mermaid source (names and counts only) |

Plus this README and the two figures — `dendrogram.svg` and `saturation.svg` —
which are embedded in the sections that discuss them rather than listed above.

## What was run

| quantity | value |
|---|---:|
| responses in the corpus | 200 |
| code-segment pairings in his export | 342 |
| placed exactly | 304 |
| placed by the fuzzy locator | 1 |
| placed by resolution (the weaker claim) | 7 |
| ambiguous, excluded | 24 |
| unlocated, excluded | 6 |
| responses in the coded set | 39 |
| his families | 15 |
| his leaves | 117 |
| machine run: segments | 1524 |
| machine run: assignment rows | 1952 |
| machine run: codes | 22 |
| machine run: families | 6 |
| machine run: offline | yes |

## What it shows

- **His coding passes his own rules.** 0 ERROR, 13 WARN, 312 INFO over the whole codebook (S3 10, S5 3). A WARN is kept and flagged and is never fatal; see [03-structural-checks.md](03-structural-checks.md).
- **The definitions arrived and were used.** 131 of 131 codes carry one (`pi-codebook-md` 131), read from `AI_Perceptions_Codebook1.md`. On 10 September every response-code pair was flagged `missing_description`; that gap is closed.
- **Clustering over the coded set gives 2 cluster(s)** of sizes 10, 29, over 39 responses x 68 codes after the low-frequency filter. The schedule raises no warning about the count. The choice of universe matters: clustering the whole corpus instead, with the uncoded responses as all-zero rows, is a different question and a different answer — see [04-clustering.md](04-clustering.md).
- **Agreement with the offline stand-in coder is nil either way** — with descriptions on both sides: 1 of 109 of his codes matched, kappa -0.043; names only: 3 of 109 of his codes matched, kappa -0.011. Both sides now carry definitions, which was the input asked for on 10 September, and it did not move the number. What binds is the keyword coder and the lexical space, not the missing definitions — see [06-agreement.md](06-agreement.md).
- **Calibration still has too little to work with.** Units per threshold: `tau_fit` 371, `tau_high` 20, `tau_low` 20. The unit for the two routing thresholds is a code pair, not a response, so five times the corpus barely moved it. The module reported and wrote nothing, which is what it is for — see [07-calibration.md](07-calibration.md).
- **The decision matrix first hands over at batch 1**, after 10 responses, on `handover.new_codes` with trigger `health` — see [10-handover.md](10-handover.md).
- **Stopping at the handover costs nothing.** 104 rows before the halt plus 1848 after resuming is 1952 rows, row-for-row identical to an uninterrupted run — see [16-halt-and-resume.md](16-halt-and-resume.md).
- **A seeded run codes into his organisation, and 186 rows change because of it.** 312 evidence rows arrived with the seed and were held out, so nothing his coding already established is counted as the machine's work. It is a demonstration and not evidence about his codebook (ADR-0035) — see [15-seeded-run.md](15-seeded-run.md).

## What this cannot show

- **Nothing here is evidence about a live pipeline.** No model was called. The
  coder is a keyword table, the judge is a stub, and the embedding space is a
  lexical fallback that cannot tell a code label from a quote.
- **An agreement number computed against that coder is a statement about the
  keyword table.** It is reported because the harness's job is to explain a
  disagreement, and it explains this one precisely.
- **No checkpoint ran.** The slow loop needs a human at a terminal. The handover
  trace says where one would have been asked to look.
- **The segments are not here and will not be.** Every list that would be more
  useful with the text beside it names response numbers instead; the text is in
  the gitignored run directory on the researcher's machine.

## Definitions, and the ones held back

113 definition(s) are reproduced in this directory. **40 were withheld** because the definition itself shares a 20-character run with a response, which makes it respondent text however it is labelled. Each appears with its code name and the note "definition withheld: shares wording with a response".

| written by | reproduced | withheld |
|---|---:|---:|
| the offline stand-in coder | 22 | 0 |
| the researcher's codebook | 91 | 40 |

## What is still needed

1. **Approval for a live run** — the provider triple and a budget. It is the only
   thing that stops every agreement, crosswalk and calibration number on this page
   from being a statement about a keyword table and a lexical fallback. Everything
   else on this list is a tidy-up; this one is the result.

The rest are small and answerable in a sentence each; they are listed in the
numbered files where they arise, and repeated here so nothing is lost:

2. **40 of the definitions quote a response.** They are withheld from this directory rather than published. Reword them, or confirm they stay local and are never exported — either answer is fine, but the exporter cannot make that call.
3. **Which export is canonical, the `.csv` or the `.xlsx`?** They hold the same pairings in different row order with different columns. The `.csv` was used here and the row numbers in the notes are its rows.
4. **24 highlights are still ambiguous** — their text occurs verbatim in more than one response and more than one candidate is in the coded set. They are excluded rather than guessed.
5. **6 highlights could not be located at all.** They belong to responses outside this corpus, or the text was edited after it was highlighted.
6. **The bare top-level code** — a family, or a sub-code of something? The structural check flags every use after the first.
7. **8 pairs of labels differ by one or two characters.** They are flagged and never merged. Which are typos and which are distinct codes?
8. **10 sub-labels appear under more than one family.** The affinity map flags the same overlaps from the data side; they are worth reading together.
9. **Is the coded set meant to stay at its current size?** The export places highlights on a fraction of the corpus; everything about his coding is computed over that fraction, and the clustering is sensitive to it.

## Reproduce

```bash
# every command offline: mock clients, the lexical embedder, no key, no network
uv run gaf ingest --input <corpus.csv> --question-variant v2 --out RUN/corpus.json
uv run gaf codebook organise --tagged <tagged.csv> --corpus RUN/corpus.json \
    --definitions <codebook.md> --out HUMAN
uv run gaf check all --codebook HUMAN/codebook.json --data RUN/corpus.json \
    --out HUMAN/golden_checks.json
uv run gaf analyse --assignments HUMAN/golden.json --out HUMAN/analysis_golden \
    --codebook HUMAN/codebook.json
uv run gaf views --assignments HUMAN/golden.json --codebook HUMAN/codebook.json \
    --analysis HUMAN/analysis_golden --out HUMAN/views/views.html
uv run gaf run --corpus RUN/corpus.json --run-id RUN --offline --out RUN
uv run gaf analyse --assignments RUN/assignments.json --data RUN/corpus.json \
    --run RUN/run.json \
    --out RUN/analysis --codebook RUN/codebook.json --crosswalk-target HUMAN/codebook.json
uv run gaf report --run RUN --analysis RUN/analysis
uv run gaf views --run RUN --analysis RUN/analysis --out RUN/views/views.html
# step 5a of scripts/run_full_results.sh writes RUN/assignments_coded_set.json —
# the machine rows on the responses his coding demonstrably reached, which is the
# row set every agreement figure on this page is computed over — and
# RUN/agreement_codebook_merged.json, which carries a description for every code
# either side names. The page reports agreement BOTH ways, so there are two runs:
uv run gaf validate agreement --human HUMAN/golden.json \
    --machine RUN/assignments_coded_set.json --data RUN/corpus.json \
    --codebook RUN/agreement_codebook_merged.json --out RUN/agreement
uv run gaf validate agreement --human HUMAN/golden.json \
    --machine RUN/assignments_coded_set.json --data RUN/corpus.json \
    --out RUN/agreement_nameonly
uv run gaf run --corpus RUN/corpus.json --offline --out SEEDED --seed-codebook HUMAN/codebook.json
uv run gaf run --corpus RUN/corpus.json --offline --out HALTED --halt-on-checkpoint
uv run gaf run --corpus RUN/corpus.json --offline --out RESUMED \
    --seed-codebook HALTED/codebook.json --skip-coded HALTED
make results-full
```

The run directories those commands write hold the corpus, the coded segments and
every quote. They are gitignored, and `make scrub` removes them before this
directory leaves the machine by any path other than `git push`.
