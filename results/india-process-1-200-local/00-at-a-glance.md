# 00 - At a glance: India Process, 200 responses, cold on local models

Models were called for this run; every number below is one the run recorded about itself.

## Realisations

Each line is produced by a rule that fires only when the numbers it rests on exist and its condition holds; a rule whose input is absent is silent, not guessed.

- The coders took 10,611 of 16,870 model-seconds (63%) and the judge 6,258 (37%). Most of the time is the coders, so a faster model there is what would shorten a run; speeding up the other side would change little.
- The judge sided with coder B in 0 of 592 decisions, with coder A in 331 (55.9%) and with neither in 261 (44.1%). The run's own metrics note says that zero is built into the judge's two verdicts (keep both candidates, or drop coder B's), so it is not evidence of a preference; the informative figure is the 55.9% for coder A, the rate at which the judge dropped coder B's candidate. The judge runs the same model as coder B (gemma4:12b), the coder it never backed, so favouring its own model's output does not explain the zero.
- The machine's coding and his coding agree no better than chance at the level of the code (|kappa| < 0.1): with descriptions, kappa -0.009 (observed agreement 88.8%, 88.9% expected by chance) and F1 0.05, and kappa on the 4 matched codes alone is 0.75; by name only, kappa +0.012 (observed agreement 88.8%, 88.6% expected by chance) and F1 0.07, and kappa on the 7 matched codes alone is 0.57. The matched-code figure covers only the few codes both sides share. The two codings pick out almost none of the same code-and-response cells, so reconcile the codebooks before reading a score as a verdict on either side.
- 361 of 1,777 model calls (20%) were replayed from the cache, not sent to a model. The time and cost on this page are for the other 1,416 calls, so read them as what this run added; a run from an empty cache would take longer.
- Each of the 162 responses that reached a model took 104 s of model time on average (median 102 s, slowest 188 s); the other 38 of 200 responses had no model time to count. At that rate 100 responses need about 2.9 hours of model time.

## Where the model's time went

![model time by role and task](model-time.svg)

| role | task | model | calls | cache replays | model-seconds | share |
|---|---|---|---:|---:|---:|---:|
| coder_b | code | gemma4:12b | 200 | 38 | 6,804.2 | 40.3% |
| coder_a | code | qwen3.5:9b | 200 | 38 | 3,807.2 | 22.6% |
| judge | judge_dispute | gemma4:12b | 592 | 111 | 3,162.5 | 18.7% |
| judge | judge_route | gemma4:12b | 696 | 158 | 2,678.3 | 15.9% |
| judge | judge_fit | gemma4:12b | 89 | 16 | 417.5 | 2.5% |

## Coder agreement and the judge's siding

![coder agreement and the judge's siding](agreement-judge.svg)

A comparison is a matched pair of coder A and coder B candidates, or one candidate the other coder never proposed.

| measure | count | share |
|---|---:|---:|
| coder agreement: agreed outright | 302 | 26.6% |
| coder agreement: grey zone | 592 | 52.1% |
| coder agreement: disputed or unmatched | 243 | 21.4% |
| judge siding: coder A | 331 | 55.9% |
| judge siding: coder B | 0 | 0.0% |
| judge siding: neither | 261 | 44.1% |

## Agreement with his coding

![agreement with his coding](heldout-agreement.svg)

| matching | F1 | kappa | TP | FP | FN | kappa on matched codes |
|---|---:|---:|---:|---:|---:|---:|
| with descriptions | 0.050 | -0.009 | 7 | 125 | 139 | 0.750 over 4 codes |
| by name only | 0.072 | +0.012 | 10 | 122 | 136 | 0.575 over 7 codes |

## Calibration

*Not drawn: no `calibration_report.json` (the `calibrate_thresholds` snippet in `docs/RUNBOOK.md` writes it).*
