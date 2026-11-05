# 17 - `local-eval39` against 4 other run(s)

Run A, the baseline, is the exported run. Each later run is set against it; a figure is a count, a sum or a score the run recorded, and a difference is reported, not explained.

## Summary

| run | judge calls | codes created | families | fresh model minutes | fail-safes | F1, with descriptions | kappa, with descriptions | F1, by name only | kappa, by name only |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A `local-eval39` | 291 | 91 | 31 | 47.0 | 0 | 0.050 | -0.010 | 0.071 | +0.011 |
| B `local-eval39-plateau` | 399 | 125 | 39 | 65.0 | 0 | 0.074 | +0.018 | 0.095 | +0.038 |
| C `local-eval39-qwen25` | 255 | 73 | 22 | 49.3 | 0 | 0.068 | +0.006 | 0.150 | +0.092 |
| D `local-eval39-llama31` | 280 | 93 | 36 | 52.4 | 0 | 0.043 | -0.016 | 0.057 | -0.001 |
| E `local-eval39-mistral` | 247 | 75 | 20 | 50.2 | 0 | 0.028 | -0.038 | 0.057 | -0.010 |

A dash means the run does not hold that figure. Judge calls are all calls, replays included; model minutes count calls that reached a model, and are shown only for a run that called one.

|  | run | models |
|---|---|---|
| A | `local-eval39` | live models |
| B | `local-eval39-plateau` | live models |
| C | `local-eval39-qwen25` | live models |
| D | `local-eval39-llama31` | live models |
| E | `local-eval39-mistral` | live models |

## Configuration: what differs from A

| setting | `local-eval39` | `local-eval39-plateau` | `local-eval39-qwen25` | `local-eval39-llama31` | `local-eval39-mistral` |
|---|---|---|---|---|---|
| `models.coder_a.model` | qwen3.5:9b | qwen3.5:9b | qwen2.5:7b-instruct | llama3.1:8b | mistral:7b-instruct |
| `rules.tau_fit` | 0.30 | 0.90 | 0.30 | 0.30 | 0.30 |
| `rules.tau_high` | 0.80 | 0.95 | 0.80 | 0.80 | 0.80 |
| `rules.tau_low` | 0.45 | 0.90 | 0.45 | 0.45 | 0.45 |

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

## `local-eval39-qwen25` against `local-eval39`

| measure | `local-eval39` | `local-eval39-qwen25` | change |
|---|---:|---:|---:|
| judge calls, in all | 291 | 255 | -36 (-12.4%) |
| judge calls, fresh | 177 | 254 | +77 (+43.5%) |
| judge calls, cache replays | 114 | 1 | -113 (-99.1%) |
| fresh model-seconds, coder_a | 600.4 | 459.2 | -141.2 (-23.5%) |
| fresh model-seconds, coder_b | 1,126.8 | 1,078.7 | -48.2 (-4.3%) |
| fresh model-seconds, judge | 1,089.8 | 1,422.0 | +332.2 (+30.5%) |
| fresh model-seconds, all roles | 2,817.1 | 2,959.9 | +142.8 (+5.1%) |
| fail-safes | 0 | 0 | +0 |
| codes created | 91 | 73 | -18 (-19.8%) |
| families in the final codebook | 31 | 22 | -9 (-29.0%) |
| assignments | 316 | 281 | -35 (-11.1%) |
| escalations to the judge | 404 | 357 | -47 (-11.6%) |

## `local-eval39-llama31` against `local-eval39`

| measure | `local-eval39` | `local-eval39-llama31` | change |
|---|---:|---:|---:|
| judge calls, in all | 291 | 280 | -11 (-3.8%) |
| judge calls, fresh | 177 | 272 | +95 (+53.7%) |
| judge calls, cache replays | 114 | 8 | -106 (-93.0%) |
| fresh model-seconds, coder_a | 600.4 | 503.3 | -97.1 (-16.2%) |
| fresh model-seconds, coder_b | 1,126.8 | 1,106.6 | -20.3 (-1.8%) |
| fresh model-seconds, judge | 1,089.8 | 1,536.7 | +446.8 (+41.0%) |
| fresh model-seconds, all roles | 2,817.1 | 3,146.6 | +329.5 (+11.7%) |
| fail-safes | 0 | 0 | +0 |
| codes created | 91 | 93 | +2 (+2.2%) |
| families in the final codebook | 31 | 36 | +5 (+16.1%) |
| assignments | 316 | 295 | -21 (-6.6%) |
| escalations to the judge | 404 | 409 | +5 (+1.2%) |

## `local-eval39-mistral` against `local-eval39`

| measure | `local-eval39` | `local-eval39-mistral` | change |
|---|---:|---:|---:|
| judge calls, in all | 291 | 247 | -44 (-15.1%) |
| judge calls, fresh | 177 | 236 | +59 (+33.3%) |
| judge calls, cache replays | 114 | 11 | -103 (-90.4%) |
| fresh model-seconds, coder_a | 600.4 | 565.6 | -34.9 (-5.8%) |
| fresh model-seconds, coder_b | 1,126.8 | 1,136.7 | +9.8 (+0.9%) |
| fresh model-seconds, judge | 1,089.8 | 1,308.6 | +218.7 (+20.1%) |
| fresh model-seconds, all roles | 2,817.1 | 3,010.8 | +193.7 (+6.9%) |
| fail-safes | 0 | 0 | +0 |
| codes created | 91 | 75 | -16 (-17.6%) |
| families in the final codebook | 31 | 20 | -11 (-35.5%) |
| assignments | 316 | 311 | -5 (-1.6%) |
| escalations to the judge | 404 | 347 | -57 (-14.1%) |

## Agreement with his coding

| run | matching | kappa | F1 | TP | FP | FN |
|---|---|---:|---:|---:|---:|---:|
| `local-eval39` | with descriptions | -0.010 | 0.050 | 7 | 127 | 139 |
| `local-eval39` | by name only | +0.011 | 0.071 | 10 | 124 | 136 |
| `local-eval39-plateau` | with descriptions | +0.018 | 0.074 | 11 | 139 | 135 |
| `local-eval39-plateau` | by name only | +0.038 | 0.095 | 14 | 136 | 132 |
| `local-eval39-qwen25` | with descriptions | +0.006 | 0.068 | 9 | 111 | 137 |
| `local-eval39-qwen25` | by name only | +0.092 | 0.150 | 20 | 100 | 126 |
| `local-eval39-llama31` | with descriptions | -0.016 | 0.043 | 6 | 130 | 140 |
| `local-eval39-llama31` | by name only | -0.001 | 0.057 | 8 | 128 | 138 |
| `local-eval39-mistral` | with descriptions | -0.038 | 0.028 | 4 | 131 | 142 |
| `local-eval39-mistral` | by name only | -0.010 | 0.057 | 8 | 127 | 138 |

## Figure

![runs compared](comparison.svg)


## Realisations

### `local-eval39-plateau`

- `local-eval39-plateau` needed 37% more judge calls than `local-eval39`: 399 against 291 (398 against 177 once cache replays are set aside).
- `local-eval39-plateau` created 34 more codes than `local-eval39`: 125 against 91 (+37%), in 39 families against 31.
- Matching with descriptions, agreement with his coding moved from kappa -0.010 in `local-eval39` to +0.018 in `local-eval39-plateau` and from F1 0.050 to 0.074; true positives went from 7 to 11, which is 4 cells of the 146 cells his coding fills. Both kappas are under 0.1 in size, which is within chance.
- Matching by name only, agreement with his coding moved from kappa +0.011 in `local-eval39` to +0.038 in `local-eval39-plateau` and from F1 0.071 to 0.095; true positives went from 10 to 14, which is 4 cells of the 146 cells his coding fills. Both kappas are under 0.1 in size, which is within chance.
- `local-eval39-plateau` was slower than `local-eval39` in model time: 65.0 against 47.0 model-minutes on calls that reached a model (+38%). The largest change is the judge, from 18.2 to 35.9 minutes. A cache replay takes no time, and the runs replayed different shares (140 of 369 calls in `local-eval39`, 21 of 477 in `local-eval39-plateau`), so this compares fresh calls only.

### `local-eval39-qwen25`

- `local-eval39-qwen25` needed 12% fewer judge calls than `local-eval39`: 255 against 291 (254 against 177 once cache replays are set aside).
- `local-eval39-qwen25` created 18 fewer codes than `local-eval39`: 73 against 91 (-20%), in 22 families against 31.
- Matching with descriptions, agreement with his coding moved from kappa -0.010 in `local-eval39` to +0.006 in `local-eval39-qwen25` and from F1 0.050 to 0.068; true positives went from 7 to 9, which is 2 cells of the 146 cells his coding fills. Both kappas are under 0.1 in size, which is within chance.
- Matching by name only, agreement with his coding moved from kappa +0.011 in `local-eval39` to +0.092 in `local-eval39-qwen25` and from F1 0.071 to 0.150; true positives went from 10 to 20, which is 10 cells of the 146 cells his coding fills. Both kappas are under 0.1 in size, which is within chance.

### `local-eval39-llama31`

- Matching with descriptions, agreement with his coding moved from kappa -0.010 in `local-eval39` to -0.016 in `local-eval39-llama31` and from F1 0.050 to 0.043; true positives went from 7 to 6, which is 1 cell of the 146 cells his coding fills. Both kappas are under 0.1 in size, which is within chance.
- Matching by name only, agreement with his coding moved from kappa +0.011 in `local-eval39` to -0.001 in `local-eval39-llama31` and from F1 0.071 to 0.057; true positives went from 10 to 8, which is 2 cells of the 146 cells his coding fills. Both kappas are under 0.1 in size, which is within chance.
- `local-eval39-llama31` was slower than `local-eval39` in model time: 52.4 against 47.0 model-minutes on calls that reached a model (+12%). The largest change is the judge, from 18.2 to 25.6 minutes. A cache replay takes no time, and the runs replayed different shares (140 of 369 calls in `local-eval39`, 18 of 358 in `local-eval39-llama31`), so this compares fresh calls only.

### `local-eval39-mistral`

- `local-eval39-mistral` needed 15% fewer judge calls than `local-eval39`: 247 against 291 (236 against 177 once cache replays are set aside).
- `local-eval39-mistral` created 16 fewer codes than `local-eval39`: 75 against 91 (-18%), in 20 families against 31.
- Matching with descriptions, agreement with his coding moved from kappa -0.010 in `local-eval39` to -0.038 in `local-eval39-mistral` and from F1 0.050 to 0.028; true positives went from 7 to 4, which is 3 cells of the 146 cells his coding fills. Both kappas are under 0.1 in size, which is within chance.
- Matching by name only, agreement with his coding moved from kappa +0.011 in `local-eval39` to -0.010 in `local-eval39-mistral` and from F1 0.071 to 0.057; true positives went from 10 to 8, which is 2 cells of the 146 cells his coding fills. Both kappas are under 0.1 in size, which is within chance.

Each line reports a difference and none says why. The configuration differences above are the only ones this page can see, and one run of each cannot tell a setting's effect from run-to-run variation.
