# 00 - At a glance: India Process, 39 coded responses, local models

Models were called for this run; every number below is one the run recorded about itself.

## Realisations

Each line is produced by a rule that fires only when the numbers it rests on exist and its condition holds; a rule whose input is absent is silent, not guessed.

- The coders took 1,727 of 2,817 model-seconds (61%) and the judge 1,090 (39%). Most of the time is the coders, so a faster model there is what would shorten a run; speeding up the other side would change little.
- The judge sided with coder B in 0 of 113 decisions, with coder A in 65 (57.5%) and with neither in 48 (42.5%). The run's own metrics note says that zero is built into the judge's two verdicts (keep both candidates, or drop coder B's), so it is not evidence of a preference; the informative figure is the 57.5% for coder A, the rate at which the judge dropped coder B's candidate. The judge runs the same model as coder B (gemma4:12b), the coder it never backed, so favouring its own model's output does not explain the zero.
- The machine's coding and his coding agree no better than chance at the level of the code (|kappa| < 0.1): with descriptions, kappa -0.010 (observed agreement 88.6%, 88.7% expected by chance) and F1 0.05, and kappa on the 4 matched codes alone is 0.70; by name only, kappa +0.011 (observed agreement 88.6%, 88.5% expected by chance) and F1 0.07, and kappa on the 7 matched codes alone is 0.55. The matched-code figure covers only the few codes both sides share. The two codings pick out almost none of the same code-and-response cells, so reconcile the codebooks before reading a score as a verdict on either side.
- tau_fit: the best F1 (0.98) holds from 0.85 to 1.00, right up to the end of the grid; the recommended 0.95 is the middle of that range, not a peak the curve found, and the provisional 0.30 scores F1 0.08. 137 of 144 machine code applications are unsupported by the human coding. This golden set supports "at least 0.85", not 0.95 exactly.
- tau_high: the best F1 (1.00) holds from 0.90 to 1.00, right up to the end of the grid; the recommended 0.95 is the middle of that range, not a peak the curve found, and the provisional 0.80 scores F1 0.50. 4 of 68 candidate/nearest-neighbour pairs are the same code in the human coding. This golden set supports "at least 0.90", not 0.95 exactly.
- tau_low: the best F1 (1.00) holds from 0.90 to 1.00, right up to the end of the grid; the recommended 0.95 is the middle of that range, not a peak the curve found, and the provisional 0.45 scores F1 0.00. 64 of 68 candidate/nearest-neighbour pairs are absent from the human coding. This golden set supports "at least 0.90", not 0.95 exactly.
- 140 of 369 model calls (38%) were replayed from the cache, not sent to a model. The time and cost on this page are for the other 229 calls, so read them as what this run added; a run from an empty cache would take longer.
- Each of the 26 responses that reached a model took 108 s of model time on average (median 101 s, slowest 195 s); the other 13 of 39 responses had no model time to count. At that rate 100 responses need about 3.0 hours of model time.

## Where the model's time went

![model time by role and task](model-time.svg)

| role | task | model | calls | cache replays | model-seconds | share |
|---|---|---|---:|---:|---:|---:|
| coder_b | code | gemma4:12b | 39 | 13 | 1,126.8 | 40.0% |
| coder_a | code | qwen3.5:9b | 39 | 13 | 600.4 | 21.3% |
| judge | judge_route | gemma4:12b | 162 | 68 | 517.0 | 18.4% |
| judge | judge_dispute | gemma4:12b | 113 | 45 | 481.2 | 17.1% |
| judge | judge_fit | gemma4:12b | 16 | 1 | 91.6 | 3.3% |

## Coder agreement and the judge's siding

![coder agreement and the judge's siding](agreement-judge.svg)

A comparison is a matched pair of coder A and coder B candidates, or one candidate the other coder never proposed.

| measure | count | share |
|---|---:|---:|
| coder agreement: agreed outright | 56 | 25.5% |
| coder agreement: grey zone | 113 | 51.4% |
| coder agreement: disputed or unmatched | 51 | 23.2% |
| judge siding: coder A | 65 | 57.5% |
| judge siding: coder B | 0 | 0.0% |
| judge siding: neither | 48 | 42.5% |

## Agreement with his coding

![agreement with his coding](heldout-agreement.svg)

| matching | F1 | kappa | TP | FP | FN | kappa on matched codes |
|---|---:|---:|---:|---:|---:|---:|
| with descriptions | 0.050 | -0.010 | 7 | 127 | 139 | 0.702 over 4 codes |
| by name only | 0.071 | +0.011 | 10 | 124 | 136 | 0.552 over 7 codes |

## Calibration

![F1 against threshold](calibration.svg)

| threshold | provisional | F1 at provisional | recommended | F1 at recommended | best F1 | best-F1 range |
|---|---:|---:|---:|---:|---:|---:|
| `tau_fit` | 0.30 | 0.084 | 0.95 | 0.975 | 0.975 | 0.85-1.00 |
| `tau_high` | 0.80 | 0.500 | 0.95 | 1.000 | 1.000 | 0.90-1.00 |
| `tau_low` | 0.45 | 0.000 | 0.95 | 1.000 | 1.000 | 0.90-1.00 |
