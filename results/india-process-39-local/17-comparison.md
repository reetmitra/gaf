# 17 - `local-eval39` against 1 other run(s)

Run A, the baseline, is the exported run. Each later run is set against it; a figure is a count, a sum or a score the run recorded, and a difference is reported, not explained.

|  | run | models |
|---|---|---|
| A | `local-eval39` | live models |
| B | `local-eval39-plateau` | live models |

## Configuration: what differs from A

| setting | `local-eval39` | `local-eval39-plateau` |
|---|---|---|
| `rules.tau_fit` | 0.30 | 0.90 |
| `rules.tau_high` | 0.80 | 0.95 |
| `rules.tau_low` | 0.45 | 0.90 |

## `local-eval39-plateau` against `local-eval39`

| measure | `local-eval39` | `local-eval39-plateau` | change |
|---|---:|---:|---:|
| judge calls, in all | 291 | 399 | +108 (+37.1%) |
| judge calls, fresh | 177 | 398 | +221 (+124.9%) |
| judge calls, cache replays | 114 | 1 | -113 (-99.1%) |
| fresh model-seconds, coder_a | 600.4 | 619.5 | +19.0 (+3.2%) |
| fresh model-seconds, coder_b | 1,126.8 | 1,129.8 | +2.9 (+0.3%) |
| fresh model-seconds, judge | 1,089.8 | 2,151.3 | +1,061.4 (+97.4%) |
| fresh model-seconds, all roles | 2,817.1 | 3,900.5 | +1,083.4 (+38.5%) |
| fail-safes | 0 | 0 | +0 |
| codes created | 91 | 125 | +34 (+37.4%) |
| families in the final codebook | 31 | 39 | +8 (+25.8%) |
| assignments | 316 | 366 | +50 (+15.8%) |
| escalations to the judge | 404 | 403 | -1 (-0.2%) |

## Agreement with his coding

| run | matching | kappa | F1 | TP | FP | FN |
|---|---|---:|---:|---:|---:|---:|
| `local-eval39` | with descriptions | -0.010 | 0.050 | 7 | 127 | 139 |
| `local-eval39` | by name only | +0.011 | 0.071 | 10 | 124 | 136 |
| `local-eval39-plateau` | with descriptions | +0.018 | 0.074 | 11 | 139 | 135 |
| `local-eval39-plateau` | by name only | +0.038 | 0.095 | 14 | 136 | 132 |

## Figure

![runs compared](comparison.svg)


## Realisations

- `local-eval39-plateau` needed 37% more judge calls than `local-eval39`: 399 against 291 (398 against 177 once cache replays are set aside).
- `local-eval39-plateau` created 34 more codes than `local-eval39`: 125 against 91 (+37%), in 39 families against 31.
- Matching with descriptions, agreement with his coding moved from kappa -0.010 in `local-eval39` to +0.018 in `local-eval39-plateau` and from F1 0.050 to 0.074; true positives went from 7 to 11, which is 4 cells of the 146 cells his coding fills. Both kappas are under 0.1 in size, which is within chance.
- Matching by name only, agreement with his coding moved from kappa +0.011 in `local-eval39` to +0.038 in `local-eval39-plateau` and from F1 0.071 to 0.095; true positives went from 10 to 14, which is 4 cells of the 146 cells his coding fills. Both kappas are under 0.1 in size, which is within chance.
- `local-eval39-plateau` was slower than `local-eval39` in model time: 65.0 against 47.0 model-minutes on calls that reached a model (+38%). The largest change is the judge, from 18.2 to 35.9 minutes. A cache replay takes no time, and the runs replayed different shares (140 of 369 calls in `local-eval39`, 21 of 477 in `local-eval39-plateau`), so this compares fresh calls only.

Each line reports a difference and none says why. The configuration differences above are the only ones this page can see, and one run of each cannot tell a setting's effect from run-to-run variation.
