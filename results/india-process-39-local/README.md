# Coding results: India Process, the 39 responses the PI coded, on local models

Produced by `scripts/export_results.py` from run directories that stay on the researcher's machine. **No respondent's words appear in this directory**: the exporter re-reads every file it wrote against every text the runs hold (26 files, 18534 withheld texts, 20-character window, against every real source file the repository test reads) and removes the whole export on a hit. It also withheld 112 model-written code descriptions because each shares a 20-character run with a response; those codes appear by name with a note.

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
2. **Do the two models agree?** Across 220 comparisons, they **agreed outright 25.5%** (56), fell in the **grey zone 51.4%** (113, all sent to the judge), and **disputed or were unmatched 23.2%** (51: 6 disputed, 8 unmatched on coder A's side and 37 on coder B's). Of the judge's 113 grey-zone rulings it dropped coder B's candidate in **57.5%** (so coder A's stood alone) and kept both readings in 42.5%. A 0% "for coder B" is built in: the judge can drop B's candidate or keep both, never back B alone, so it is not evidence of a preference. Here the judge is the same model as coder B, so favouring its own model does not explain the zero either. The siding flag (65%) did not fire.
3. **What does the rest of the corpus add?** Not yet answered. It needs the cold run over all 200 responses, and the seeded run on the other 161, which halted by design at its first checkpoint after 10 responses to wait for the PI as the human gate.
4. **Did calibration matter?** Calibration was *run*, and it says the provisional thresholds (tau_fit 0.30, tau_high 0.80, tau_low 0.45) are wrong for this embedding space: on the 20-response fold and again on the 19 held-out, all three point to about 0.95 on a flat plateau. It was tried and not adopted: re-running these 39 responses under tau_fit 0.90, tau_high 0.95 and tau_low 0.90 (the plateau both folds share) needed **399 judge calls against 291 (+37%, counting calls replayed from an earlier cache)**, created **125 codes against 91** (39 families against 31) and moved held-out kappa from -0.010 to +0.018 (F1 0.050 to 0.074; 11 cells agreed instead of 7 of about 146). More compute and a more fragmented codebook for a gain well within chance: there is no case here for moving the defaults. The evidence behind the recommendation was also thin (3 to 4 same-code pairs back tau_high). See [07-calibration.md](07-calibration.md) and the side-by-side in [17-comparison.md](17-comparison.md).
5. **What did it cost, and how long did it take?** USD 0. Model time averaged **108 seconds per response** (median 101, 90th percentile 155) over the 26 responses not already cached, with 229 fresh calls averaging 12.3 seconds. About 47 minutes of active running; the run's 106-minute wall clock includes an hour in which the laptop slept.
6. **Where does it fail?** Worked disagreement cases need respondent text and belong in a private appendix for the PI only. Not produced.

## Model tests: does changing one thing change anything?

Eight more cold runs on the same 39 responses, the same held-out fold and the same agreement code. Each changes **one thing** from the baseline: the three thresholds, coder A (`qwen3.5:9b` replaced by `qwen2.5:7b-instruct`, `llama3.1:8b` or `mistral:7b-instruct`), the judge (`gemma4:12b` replaced by `llama3.1:8b`), or it repeats a configuration to see how much a run moves on its own: once with a fresh cache at temperature 0, and twice with both coders at temperature 0.7 (seeds 1 and 2). Everything is served by Ollama on the laptop. Unless stated, coder B, the judge and the refactorer stayed `gemma4:12b` and the embedder `embeddinggemma`. Numbers come from each run's own `stats.json`, database and agreement files; the full tables are in [17-comparison.md](17-comparison.md), and the intervals, chance level and family-level view are in [../agreement-checks.md](../agreement-checks.md).

| run | what changed | codes (families) | judge calls, all / fresh | fresh model minutes | F1 / kappa, with descriptions | F1 / kappa, by name only | agreed cells of 146 (desc. / name) |
|---|---|---:|---:|---:|---:|---:|---:|
| baseline `local-eval39` | nothing | 91 (31) | 291 / 177 | 47.0 | 0.050 / -0.010 | 0.071 / +0.011 | 7 / 10 |
| `-plateau` | the three thresholds | 125 (39) | 399 / 398 | 65.0 | 0.074 / +0.018 | 0.095 / +0.038 | 11 / 14 |
| `-qwen25` | coder A: qwen2.5:7b-instruct | 73 (22) | 255 / 254 | 49.3 | 0.068 / +0.006 | 0.150 / +0.092 | 9 / 20 |
| `-llama31` | coder A: llama3.1:8b | 93 (36) | 280 / 272 | 52.4 | 0.043 / -0.016 | 0.057 / -0.001 | 6 / 8 |
| `-mistral` | coder A: mistral:7b-instruct | 75 (20) | 247 / 236 | 50.2 | 0.028 / -0.038 | 0.057 / -0.010 | 4 / 8 |
| `-judge-llama31` | the judge: llama3.1:8b | 23 (12) | 312 / 312 | 41.4 | 0.008 / -0.065 | 0.066 / -0.006 | 1 / 8 |
| `-repeat1` | nothing; fresh cache, seed 1729 | 78 (21) | 268 / 266 | 64.4 | 0.066 / +0.003 | 0.058 / -0.006 | 9 / 8 |
| `-t07-s1` | both coders at temperature 0.7, seed 1 | 57 (15) | 170 / 170 | 49.4 | 0.080 / +0.022 | 0.104 / +0.046 | 10 / 13 |
| `-t07-s2` | both coders at temperature 0.7, seed 2 | 77 (26) | 259 / 259 | 69.1 | 0.007 / -0.057 | 0.014 / -0.051 | 1 / 2 |

What the table supports, and what it does not:

- **Every run agrees with the PI at about chance or below.** No kappa reaches 0.1 in either matching. The best single figure is `-qwen25` by name only (20 of his 146 cells, F1 0.150, kappa +0.092); it is one run, matched on names, and the same run with descriptions gives 9 cells. Across the nine runs the count with descriptions is 1 to 11 of 146 cells.
- **A repeat moves about as much as most changes do.** The baseline and its repeat are the same configuration. They differ by 13 codes (91 against 78), 10 families (31 against 21), 2 agreed cells (7 against 9), and a family-level kappa of +0.506 against +0.468. So the codebook-size differences between the coder swaps (20 to 39 families, 73 to 125 codes) are not clearly more than one run's own variation. Two repeats cannot put a number on that variation, only show that it is there.
- **The one change that stands out is the judge.** Swapping the judge for `llama3.1:8b` gave 23 codes in 12 families, far below every other run (57 to 125 codes) and by more than the repeat's difference. It also scored lowest at family level (kappa +0.330 against +0.45 to +0.56 in the other eight 39-response runs) and, matched by name, is the one run clearly below a predictor that only repeats his commonest themes. Its judge calls were also faster: 312 fresh calls took 12.4 minutes, 2.4 seconds each, against 6.2 for `gemma4:12b`.
- **Temperature 0.7 makes coder A's output volatile.** Coder A wrote 6,196 output tokens in one seed and 24,751 in the other (17,865 in the repeat at temperature 0), and the two seeds had 1 and 3 fail-safes where none of the temperature-0 runs on these 39 responses had any. Codebooks of 57 and 77 codes came from them.
- **Identical requests did not give identical replies across runs.** The 20 coder requests of the first batch, where the codebook is still empty, are byte-identical in the shared cache from the earlier runs and in the repeat's fresh cache (temperature 0, seed 1729 both times). The repeat's replies differed from the stored ones in all 20. Replaying four of them now gave the same reply twice in a row every time, matched the repeat's own reply from hours earlier in 2 of 4, and matched the stored earlier reply in none. So the model is steady over minutes and not between runs. A difference in the first batch changes the codebook, which changes every later prompt, so differences compound. The cause (a server update, a reloaded model, load) is not established.
- **The model-minute column favours the baseline.** The baseline replayed 114 of its judge calls from an earlier cache, so only 177 were timed; the others timed 236 to 398. Per fresh judge call the time is about the same in every `gemma4:12b`-judge run (5.4 to 6.2 seconds), so compare calls, not minutes.
- One run per configuration (two for the temperature-0.7 pair), 19 held-out responses, and none of these models is the approved line-up. These are tests of the pipeline's plumbing and of how sensitive it is to its settings, not a ranking of models.

## Files

Start with [00-at-a-glance.md](00-at-a-glance.md): four figures and the findings the numbers support, each stated with the number it rests on.

| file | what it holds |
|---|---|
| [00-at-a-glance.md](00-at-a-glance.md) | model time by role, coder and judge agreement, agreement with his coding, calibration curves, and the realisations |
| [01-inputs.md](01-inputs.md) to [05-saturation.md](05-saturation.md) | the corpus, his codebook organised and checked, clustering, saturation |
| [06-agreement.md](06-agreement.md) | his coding against the machine's, both ways, on the held-out 19 |
| [07-calibration.md](07-calibration.md) | the threshold sweeps on the calibration fold |
| [08-machine-run.md](08-machine-run.md) to [14-timeline.md](14-timeline.md) | the machine run, growth, handover, patterns, affinity, crosswalk, timeline |
| [17-comparison.md](17-comparison.md) | the default run set against eight others (plateau thresholds; coder A swapped for qwen2.5, llama3.1, mistral; judge swapped for llama3.1; a temperature-0 repeat; two temperature-0.7 repeats): summary table, configuration, calls, codes, agreement, one figure, realisations per run |
| [views-machine/views.html](views-machine/views.html) | a self-contained page of figures |

## Read these caveats first

- The patterns, affinity and clustering pages were computed by the deterministic analysis tail, which uses the lexical embedding fallback, not `embeddinggemma`. Their own caveats say so.
- The sampling is small: 39 responses, 19 in the held-out fold. Treat every agreement figure as an interval, not a point.
- A seeded run is a production tool and not a validation one; only this cold run belongs in an agreement figure.
