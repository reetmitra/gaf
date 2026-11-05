# Coding results: India Process, all 200 responses, coded cold on local models

Produced by `scripts/export_results.py` from run directories that stay on the researcher's machine. **No respondent's words appear in this directory**: the exporter re-reads every file it wrote against every text the runs hold (22 files, 19,707 withheld texts, 20-character window, against every real source file the repository test reads) and removes the whole export on a hit. It withheld 228 model-written items (code descriptions and finding messages) because each shares a 20-character run with a response; they appear with a note.

## What this is, and is not

- **Two real models, both served on the researcher's laptop; nothing left the machine.** Coder A `qwen3.5:9b` (Alibaba), coder B `gemma4:12b` (Google), the judge and refactorer `gemma4:12b`, embeddings `embeddinggemma` (768-d). The judge is the same model as coder B.
- **It tests the pipeline. It is not what the approved line-up (Claude Opus 5.5 and hosted Qwen3.8-Max) would find.** That run has not happened: it waits on the principal investigator's confirmation of the two data processors and the keys.
- A cold run over the whole corpus: no seed, default thresholds, and no human gate (it never halted, so nothing was reviewed at a checkpoint).
- The agreement figures use the pre-registered held-out fold of 19 of the 39 responses the PI coded (ids-only split file, sha256 `0e77def6913194319797b25c866195ded2628227877396c6d383f10b3fd27939`).

## What was run

| quantity | value |
|---|---:|
| responses coded | 200 |
| segments | 1,524 |
| assignment rows | 1,633 |
| codes the machine created | 162, in 48 families |
| saturation | batch 18 of 20 (10 responses per batch) |
| his codebook for comparison | 15 families, 117 leaves |
| fail-safes | 2 (one per coder, of 162 fresh calls each) |
| billed model calls / cache replays | 1,416 / 361 |
| spend | USD 0 (local) |

## The six questions

1. **Does the machine find what the PI found? Not on this evidence, and more data did not change that.** On the 19 held-out responses, code-level kappa is **-0.009** with descriptions on both sides (7 response-code pairs agreed, 125 machine-only, 139 his-only; F1 0.050) and **+0.012** name against name (10 agreed; F1 0.072). That matches the 39-response run (-0.010 and +0.011). Segment-level strict F1 is 0.024 and 0.030. The machine built 57 codes on those responses against his 71. See [06-agreement.md](06-agreement.md) and the crosswalk in [13-crosswalk.md](13-crosswalk.md).
2. **Do the two models agree?** Across 1,137 comparisons they **agreed outright 26.6%** (302), fell in the **grey zone 52.1%** (592, all sent to the judge), and **disputed or were unmatched 21.4%** (243: 29 disputed, 68 unmatched on coder A's side, 146 on coder B's). Of the judge's 592 grey-zone rulings it dropped coder B's candidate in **55.9%** (331) and kept both readings in 44.1% (261). A 0% "for coder B" is built in: the judge can drop B's candidate or keep both, never back B alone, so it is not evidence of a preference.
3. **What does the rest of the corpus add?** Vocabulary, not agreement. The codebook grew from 91 codes in 31 families (the 39-response run) to **162 in 48**, and saturated at batch 18, so the last two batches introduced nothing new. See [09-growth.md](09-growth.md), [05-saturation.md](05-saturation.md) and [13-crosswalk.md](13-crosswalk.md) for the machine-only codes that are candidates for his codebook.
4. **Did calibration matter?** It was tried on the 39 responses and not adopted. Calibration pointed to about 0.95 for all three thresholds. Re-running under tau_fit 0.90, tau_high 0.95 and tau_low 0.90 (the plateau both folds share) needed **399 judge calls against 291 (+37%)**, created **125 codes against 91** and moved held-out kappa only from -0.010 to +0.018. More compute and a more fragmented codebook for a gain well within chance: no case for moving the defaults. See the 39-response pack's [07-calibration.md](../india-process-39-local/07-calibration.md).
5. **What did it cost, and how long did it take?** USD 0. Model time averaged **104 seconds per response** (median 102) over the 162 responses that reached a model; the other 38 were replayed from the cache. The run took 4 hours 45 minutes of wall clock, with no sleep in that window.
6. **Where does it fail?** Worked disagreement cases need respondent text and belong in a private appendix for the PI only. Not produced.

## Read these caveats first

- Start with [00-at-a-glance.md](00-at-a-glance.md): four figures and the findings the numbers support, each with the number it rests on.
- The patterns, affinity and clustering pages come from the deterministic analysis tail, which uses the lexical embedding fallback, not `embeddinggemma`.
- Only 39 of the 200 responses have his coding, and 19 are held out, so every agreement figure is an interval, not a point.
- This run never stopped at a checkpoint, so the human-gate step is untested here; see the seeded run in the plan for that.
