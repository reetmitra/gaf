# Coding results: India Process, the 39 responses the PI coded, on local models

Produced by `scripts/export_results.py` from run directories that stay on the researcher's machine. **No respondent's words appear in this directory**: the exporter re-reads every file it wrote against every text the runs hold (19 files, 8899 withheld texts, 20-character window, against every real source file the repository test reads) and removes the whole export on a hit. It also withheld 86 model-written code descriptions because each shares a 20-character run with a response; those codes appear by name with a note.

## What this is, and is not

- **Two real models, both served on the researcher's laptop; nothing left the machine.** Coder A `qwen3.5:9b` (Alibaba), coder B `gemma4:12b` (Google), the judge and refactorer `gemma4:12b`, embeddings `embeddinggemma` (768-d). The judge is the same model as coder B.
- **It tests the pipeline. It is not what the approved line-up (Claude Opus 5.5 and hosted Qwen3.8-Max) would find.** That run has not happened: it waits on the principal investigator's confirmation of the two data processors and the keys.
- A cold run: the machine started from an empty codebook, with no seed.
- The agreement figures are on a **pre-registered held-out fold** of 19 of the 39 responses (ids-only split file, sha256 `0e77def6913194319797b25c866195ded2628227877396c6d383f10b3fd27939`). The other 20 were the calibration fold.

## What was run

| quantity | value |
|---|---:|
| responses coded | 39 |
| segments | 291 |
| assignment rows | 316 |
| codes the machine created | 91, in 31 families |
| his codebook for comparison | 15 families, 117 leaves |
| fail-safes | 0 |
| billed model calls / cache replays | 229 / 140 |
| spend | USD 0 (local) |

## The six questions

1. **Does the machine find what the PI found? Not on this evidence.** On the 19 held-out responses, code-level kappa is **-0.010** with descriptions on both sides (counted over response-code pairs: 7 agreed, 127 machine-only, 139 his-only; F1 0.050) and **+0.011** name against name (10 agreed; F1 0.071). Segment-level strict F1 is 0.024 and 0.030. The machine built 56 codes on those 19 responses against his 71; 4 (with descriptions) or 7 (names only) matched. The "matched codes only" kappas (0.70 and 0.55) are over those few codes and are not a headline. Why the vocabularies do not line up has not been diagnosed; see [06-agreement.md](06-agreement.md) and the crosswalk in [13-crosswalk.md](13-crosswalk.md).
2. **Do the two models agree?** Across 220 comparisons, they **agreed outright 25.5%** (56), fell in the **grey zone 51.4%** (113, all sent to the judge), and **disputed or were unmatched 23.2%** (51: 6 disputed, 8 unmatched on coder A's side and 37 on coder B's). The judge sided with coder A on **57.5%** of its 113 decisions, with coder B on **0%**, and with neither on 42.5%. The siding flag threshold is 65%, so it did not fire. A judge that never sides with a coder that is the same model as itself, in a fixed presentation order, is a result to understand before trusting it.
3. **What does the rest of the corpus add?** Not yet answered. It needs the cold run over all 200 responses, and the seeded run on the other 161, which halted by design at its first checkpoint after 10 responses to wait for the PI as the human gate.
4. **Did calibration matter?** Calibration was *run*, and it says the provisional thresholds (tau_fit 0.30, tau_high 0.80, tau_low 0.45) are wrong for this embedding space: on the 20-response fold and again on the 19 held-out, all three point to about 0.95 on a flat plateau. Nothing was adopted, so there is no before-and-after run yet. The evidence is thin (3 to 4 same-code pairs back tau_high) and setting tau_low equal to tau_high would remove the judge's band. See [07-calibration.md](07-calibration.md).
5. **What did it cost, and how long did it take?** USD 0. Model time averaged **108 seconds per response** (median 101, 90th percentile 155) over the 26 responses not already cached, with 229 fresh calls averaging 12.3 seconds. About 47 minutes of active running; the run's 106-minute wall clock includes an hour in which the laptop slept.
6. **Where does it fail?** Worked disagreement cases need respondent text and belong in a private appendix for the PI only. Not produced.

## Files

| file | what it holds |
|---|---|
| [01-inputs.md](01-inputs.md) to [05-saturation.md](05-saturation.md) | the corpus, his codebook organised and checked, clustering, saturation |
| [06-agreement.md](06-agreement.md) | his coding against the machine's, both ways, on the held-out 19 |
| [07-calibration.md](07-calibration.md) | the threshold sweeps on the calibration fold |
| [08-machine-run.md](08-machine-run.md) to [14-timeline.md](14-timeline.md) | the machine run, growth, handover, patterns, affinity, crosswalk, timeline |
| [views-machine/views.html](views-machine/views.html) | a self-contained page of figures |

## Read these caveats first

- The patterns, affinity and clustering pages were computed by the deterministic analysis tail, which uses the lexical embedding fallback, not `embeddinggemma`. Their own caveats say so.
- The sampling is small: 39 responses, 19 in the held-out fold. Treat every agreement figure as an interval, not a point.
- A seeded run is a production tool and not a validation one; only this cold run belongs in an agreement figure.
