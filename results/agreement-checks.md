# Agreement with the PI, looked at four more ways

Five of the ideas listed as untried in the [results index](README.md) needed no new model calls, so
they were run on files the runs had already written. They are produced by
[`scripts/agreement_checks.py`](../scripts/agreement_checks.py) (numbers only, no respondent text) and
by a 4-fold calibration script that stays on the researcher's machine. Four further runs were then
made to test a judge swap and run-to-run variation, and are in the same table. The held-out fold is
the same 19 responses as everywhere else, and the PI's coding fills about 146 response-by-code cells in
it.

![kappa with intervals, leaf codes and families](agreement-checks.svg)

## What was added to the kappa

1. **An interval.** A percentile bootstrap over the 19 responses (5,000 resamples). Nineteen
   responses is small, so a point value alone says little.
2. **A chance reference.** The same kappa when the machine's per-response code sets are dealt to the
   responses at random (5,000 shuffles). This is the open circle in the figure. It sits below zero at
   leaf level and well above zero at family level, because a handful of families appear in nearly every
   response, which a pooled kappa does not account for.
3. **A trivial predictor.** One that never reads a response and gives every response the PI's most
   common codes (as many as the machine averages per response). It is told the PI's own totals, so it is
   generous to the trivial side. This is the diamond.
4. **Family level.** Each machine code is rolled up to the PI family of the PI code it is nearest to,
   whether or not that match was accepted as the same code, and the PI's codes to their families. Cells
   are response by family (15 families) instead of response by leaf code (116). It is a generous reading
   of "do the two find the same themes".

## Results (with descriptions on both sides; by-name-only is in each run's `agreement_checks.json`)

| run | leaf kappa [95% interval] | trivial, leaf | family kappa [95% interval] | chance, family | trivial, family | family F1 | family F1 minus trivial, 95% interval |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline `local-eval39` | -0.010 [-0.043, +0.025] | +0.219 | +0.506 [+0.427, +0.585] | +0.181 | +0.394 | 0.663 | [-0.009, +0.157] |
| `-plateau` (thresholds) | +0.018 [-0.026, +0.068] | +0.230 | +0.457 [+0.333, +0.585] | +0.145 | +0.394 | 0.634 | [-0.030, +0.122] |
| `-qwen25` (coder A) | +0.006 [-0.035, +0.052] | +0.198 | +0.474 [+0.365, +0.579] | +0.106 | +0.384 | 0.636 | [-0.042, +0.190] |
| `-llama31` (coder A) | -0.016 [-0.049, +0.025] | +0.221 | +0.556 [+0.447, +0.661] | +0.228 | +0.384 | 0.693 | [+0.019, +0.244] |
| `-mistral` (coder A) | -0.038 [-0.060, -0.013] | +0.215 | +0.492 [+0.387, +0.606] | +0.185 | +0.394 | 0.660 | [-0.001, +0.144] |
| cold run `local-cold200` | -0.009 [-0.042, +0.027] | +0.219 | +0.480 [+0.394, +0.567] | +0.172 | +0.394 | 0.644 | [-0.019, +0.130] |
| `-judge-llama31` (the judge) | -0.065 [-0.078, -0.048] | +0.167 | +0.330 [+0.239, +0.420] | +0.172 | +0.373 | 0.497 | [-0.109, +0.050] |
| `-repeat1` (repeat, fresh cache) | +0.003 [-0.045, +0.059] | +0.215 | +0.468 [+0.342, +0.599] | +0.198 | +0.394 | 0.633 | [-0.064, +0.155] |
| `-t07-s1` (temperature 0.7) | +0.022 [-0.027, +0.074] | +0.196 | +0.451 [+0.343, +0.552] | +0.159 | +0.384 | 0.605 | [-0.079, +0.156] |
| `-t07-s2` (temperature 0.7) | -0.057 [-0.066, -0.045] | +0.217 | +0.480 [+0.385, +0.573] | +0.184 | +0.394 | 0.649 | [-0.015, +0.129] |

## What it says

- **At leaf level the machine is at zero, and below a trivial predictor.** Kappa runs from -0.065 to
  +0.022 and every trivial predictor scores +0.17 to +0.23. That is expected when the vocabularies
  differ: only about 4 of the machine's 56 codes on this fold were accepted as the same code as one of
  his 71, so the machine cannot reproduce his leaf labels however well it reads the responses. The
  runs agree on 1 to 11 of his 146 cells.
- **There is still a small signal, in most runs.** The shuffled-response chance level at leaf level is
  -0.03 to -0.07. Eight of the ten runs sit above it (shuffles reach the observed value in at most 1 in
  250 cases). The judge swap and the second temperature-0.7 run do not (p about 0.48 and 0.25): each
  of them agreed on a single cell. A narrow interval at leaf level, such as their -0.078 to -0.048,
  says that nothing is happening, not that the figure is precise: with one agreed cell there is almost
  nothing to resample.
- **At family level the agreement is above chance in every run.** Kappa runs from +0.29 to +0.56
  against chance levels of +0.08 to +0.24, and F1 from 0.50 to 0.69, across the ten runs and both
  matching variants.
- **But it is not clearly better than guessing his common themes.** Against the trivial predictor the
  F1 gap interval includes zero in 18 of the 20 run-and-variant cases. One is above it: `-llama31` with
  descriptions (+0.019 to +0.244), a single run. One is below it: `-judge-llama31` matched by name
  (-0.152 to -0.008). The honest reading is that the machine finds the PI's themes better than chance
  and by a margin over "always say the common ones" that this fold is too small to confirm.
- **So part of the near-zero leaf agreement is vocabulary, not missing content.** Moving to his
  vocabulary at family level lifts kappa from about 0 to about 0.5. The roll-up is generous, which is why
  it is reported next to the trivial predictor and the shuffled-response chance.

## Repeats, and a different judge

Four runs were added to say how much a run moves on its own, and whether the judge matters.

| run | what changed | codes (families) | family kappa | leaf cells agreed |
|---|---|---:|---:|---:|
| baseline | nothing | 91 (31) | +0.506 | 7 |
| `-repeat1` | nothing; fresh cache, temperature 0, seed 1729 | 78 (21) | +0.468 | 9 |
| `-t07-s1` | both coders at temperature 0.7, seed 1 | 57 (15) | +0.451 | 10 |
| `-t07-s2` | both coders at temperature 0.7, seed 2 | 77 (26) | +0.480 | 1 |
| `-judge-llama31` | the judge: `llama3.1:8b` | 23 (12) | +0.330 | 1 |

- **A run does not reproduce itself.** The repeat made the same configuration as the baseline and
  differs by 13 codes, 10 families and 0.038 of family kappa. Of the first batch's 20 coder requests,
  which are byte-identical between the two (the codebook is still empty), the repeat's replies differed
  from the stored ones in all 20. A request replayed now gives the same reply twice in a row (4 of 4), so
  the model is steady over minutes and not from one run to the next. Differences in the first batch
  change the codebook and so every later prompt. The cause is not established.
- **So the coder-swap results are not yet separable from that.** Family kappa across the eight runs that
  changed only a coder, a threshold, a repeat or a temperature sits between +0.451 and +0.556. The
  repeat alone spans 0.038 of it. `-llama31`, the one run whose gap over the trivial predictor excluded
  zero, is 0.05 above the best of the repeats. With two repeats of one configuration there is no spread
  to calibrate that against.
- **The judge is the one change larger than the repeat.** `llama3.1:8b` as judge gave 23 codes where the
  baseline gave 91 and the repeat 78, the lowest family kappa (+0.330, with the upper end of its
  interval just under the baseline's lower end), and the only run clearly below the trivial predictor
  by name. It made more assignments (336 against 316) onto far fewer codes. A codebook that small
  cannot carry his distinctions; that reading was not tested separately.
- **Temperature 0.7 made coder A's output volatile.** It wrote 6,196 output tokens in one seed and
  24,751 in the other (17,865 in the temperature-0 repeat), with 1 and 3 fail-safes.

## Calibration with four folds instead of two

The 39 responses were dealt at random into four folds (10, 10, 10 and 9 responses) and the thresholds
calibrated on each fold alone.

| fold | tau_fit (plateau) | tau_high (positive pairs) | tau_low |
|---|---|---|---|
| 1 | 0.95 (0.90 to 1.00) | 0.95 (2) | 0.95 |
| 2 | 0.90 (0.80 to 1.00) | 0.95 (3) | 0.95 |
| 3 | 0.95 (0.85 to 1.00) | 0.95 (3) | 0.95 |
| 4 | 0.85 (0.70 to 1.00) | 0.95 (1) | 0.95 |

The direction holds in every fold: all three thresholds point to about 0.95, and the plateaus overlap
from 0.90 to 1.00 for each threshold. The plateau run (0.90 / 0.95 / 0.90) sits inside all four.
tau_high rests on one to three same-code pairs per fold, so the evidence for its exact value is thin, as
before. This repeats the two-fold finding more firmly; it does not change the decision to leave the
defaults alone (ADR-0054).

## Caveats

- 19 held-out responses, and one run per configuration except the temperature-0.7 pair.
- The bootstrap treats the 19 as a random sample of responses; the permutation test deals whole
  machine code sets to responses.
- The family roll-up uses the nearest PI code regardless of the acceptance threshold. A stricter roll-up
  would give lower numbers.
- The run-to-run spread is shown to exist and is not measured: three or four runs of a configuration
  would be needed to put an interval on it.
- The first-batch replay check reads the response cache, which holds respondent text, so it was run on
  the researcher's machine and only its counts are reported here.
