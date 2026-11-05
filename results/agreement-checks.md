# Agreement with the PI, looked at four more ways

Five of the ideas listed as untried in the [results index](README.md) needed no new model calls, so
they were run on files the runs had already written. They are produced by
[`scripts/agreement_checks.py`](../scripts/agreement_checks.py) (numbers only, no respondent text) and
by a 4-fold calibration script that stays on the researcher's machine. The held-out fold is the same
19 responses as everywhere else, and the PI's coding fills about 146 response-by-code cells in it.

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
| `-plateau` | +0.018 [-0.026, +0.068] | +0.230 | +0.457 [+0.333, +0.585] | +0.145 | +0.394 | 0.634 | [-0.030, +0.122] |
| `-qwen25` | +0.006 [-0.035, +0.052] | +0.198 | +0.474 [+0.365, +0.579] | +0.106 | +0.384 | 0.636 | [-0.042, +0.190] |
| `-llama31` | -0.016 [-0.049, +0.025] | +0.221 | +0.556 [+0.447, +0.661] | +0.228 | +0.384 | 0.693 | [+0.019, +0.244] |
| `-mistral` | -0.038 [-0.060, -0.013] | +0.215 | +0.492 [+0.387, +0.606] | +0.185 | +0.394 | 0.660 | [-0.001, +0.144] |
| cold run `local-cold200` | -0.009 [-0.042, +0.027] | +0.219 | +0.480 [+0.394, +0.567] | +0.172 | +0.394 | 0.644 | [-0.019, +0.130] |

## What it says

- **At leaf level the machine is at zero, and below a trivial predictor.** Every interval sits around
  zero and every trivial predictor scores +0.20 to +0.23. That is expected when the vocabularies differ:
  only about 4 of the machine's 56 codes on this fold were accepted as the same code as one of his 71,
  so the machine cannot reproduce his leaf labels however well it reads the responses.
- **There is still a small signal.** The shuffled-response chance level at leaf level is -0.03 to
  -0.06, and every run's kappa sits above it (shuffles reach the observed value in at most 1 in 250
  cases). The machine puts its codes on the right responses a little more often than a random response
  would get them.
- **At family level the agreement is well above chance.** Kappa runs from +0.34 to +0.56 against chance
  levels of +0.11 to +0.23, and F1 from 0.56 to 0.69, in every run and both matching variants.
- **But it is not clearly better than guessing his common themes.** Against the trivial predictor the
  F1 gap interval includes zero in 11 of the 12 run-and-variant cases. The one exception is `-llama31`
  with descriptions (+0.019 to +0.244), a single run. The honest reading is that the machine finds the
  PI's themes better than chance and by a margin over "always say the common ones" that this fold is too
  small to confirm.
- **So part of the near-zero leaf agreement is vocabulary, not missing content.** Moving to his
  vocabulary at family level lifts kappa from about 0 to about 0.5. The roll-up is generous, which is why
  it is reported next to the trivial predictor and the shuffled-response chance.

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

- 19 held-out responses, and one run per configuration.
- The bootstrap treats the 19 as a random sample of responses; the permutation test deals whole
  machine code sets to responses.
- The family roll-up uses the nearest PI code regardless of the acceptance threshold. A stricter roll-up
  would give lower numbers.
- Run-to-run variation is still unmeasured; four further runs that address it were started and are not
  in this page (see the results index).
