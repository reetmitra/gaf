# Agreement with the PI's refined codebook (provisional rescoring)

On 6 November 2026 the PI sent a refined edition of his codebook: 15 families and 67 leaf codes, down from 116
subcodes, with merged overlapping codes, 13 discarded codes and three additions. This page rescored the ten runs
against it. The machine's codes, the 19 held-out responses, the matching method and the statistics are the same as
in [agreement-checks.md](agreement-checks.md). Only the reference changed. No model was run; the only new computation
was the embeddings the matching step uses. Every number below is a count or a statistic over counts.

**Provisional.** The reference was rebuilt from the list of merges in his Notes, not from his refined pairings file
(see [Caveats](#caveats)). The refined edition arrived after the results, so this is a sensitivity check, and the
pre-registered figures in the other pages stay the headline.

## What it shows

- **Leaf level did not move.** Kappa with descriptions on both sides is -0.080 to +0.027 across the ten runs
  (against -0.065 to +0.022 on the first edition). No run matches more than 12 of his 134 cells on the
  held-out fold. Name-only matching gives -0.042 to +0.074. Cutting his subcodes from 116 to 64 did not
  bring the machine's codes any closer to his.
- **Family level is about the same.** Kappa is +0.397 to +0.537 (against +0.330 to +0.556), above the
  shuffled-response chance of +0.027 to +0.263 in every run. The gap between the machine's F1 and a predictor that repeats his
  commonest families has an interval that includes zero in 20 of 20 comparisons (18 of 20 before).
- **A predictor that repeats his commonest leaf codes still beats the machine.** Its F1 is 0.25 to 0.31; the
  machine's is 0.00 to 0.09.
- **So granularity of the first edition does not explain the near-zero leaf agreement.** Whatever it is, it survives
  merging his overlapping codes. The other candidates from the main results page (only 39 coded responses, small
  models, differences in vocabulary) remain open.

![agreement with the refined codebook](agreement-refined.svg)

## Run by run

Kappa with descriptions on both sides. "Before" is the first edition; "after" is the refined edition, with the
95% bootstrap interval over the 19 responses. Cells matched is the number of response-by-code cells both sides have.
Chance is the mean kappa when the machine's per-response code sets are dealt to the responses at random.

| run | leaf kappa before | leaf kappa after (95% interval) | cells matched before | cells matched after | family kappa before | family kappa after (95% interval) | family chance after |
|---|---:|---|---:|---:|---:|---|---:|
| baseline | -0.010 | +0.025 (-0.018 to +0.068) | 7 | 12 | +0.506 | +0.484 (+0.395 to +0.565) | +0.182 |
| calibrated thresholds | +0.018 | -0.013 (-0.046 to +0.026) | 11 | 7 | +0.457 | +0.397 (+0.291 to +0.504) | +0.027 |
| coder A: qwen2.5 | +0.006 | +0.002 (-0.039 to +0.047) | 9 | 9 | +0.474 | +0.530 (+0.434 to +0.613) | +0.145 |
| coder A: llama3.1 | -0.016 | -0.028 (-0.059 to +0.015) | 6 | 5 | +0.556 | +0.481 (+0.401 to +0.559) | +0.126 |
| coder A: mistral | -0.038 | -0.045 (-0.067 to -0.020) | 4 | 4 | +0.492 | +0.497 (+0.396 to +0.603) | +0.220 |
| cold run, all 200 | -0.009 | +0.027 (-0.016 to +0.071) | 7 | 12 | +0.480 | +0.484 (+0.369 to +0.592) | +0.168 |
| judge: llama3.1 | -0.065 | -0.080 (-0.094 to -0.062) | 1 | 1 | +0.330 | +0.429 (+0.305 to +0.545) | +0.212 |
| repeat, fresh cache | +0.003 | -0.010 (-0.055 to +0.045) | 9 | 8 | +0.468 | +0.450 (+0.334 to +0.571) | +0.208 |
| temperature 0.7, seed 1 | +0.022 | -0.026 (-0.060 to +0.012) | 10 | 5 | +0.451 | +0.473 (+0.363 to +0.572) | +0.181 |
| temperature 0.7, seed 2 | -0.057 | -0.072 (-0.079 to -0.065) | 1 | 0 | +0.480 | +0.537 (+0.411 to +0.663) | +0.263 |

## How the reference was rebuilt

1. His first-edition coding of the 39 responses (327 response-by-code assignments) was relabelled to the refined
   edition's leaf codes using the merges, the one rename, the collapse of five single-segment sectors and the additions
   listed in his Notes. 16 assignments sit on codes he discarded and were dropped, leaving 311.
2. The code descriptions come from the refined edition. The matching step uses them exactly as it used the first
   edition's.
3. The same matching, the same fold and the same statistics script were run for each of the ten runs. The first-edition
   results in each run folder were not touched.

## Caveats

- **The crosswalk is approximate.** 44 of the 67 refined leaf counts are reproduced exactly from our copy of his coding.
  The other 23 differ by 1 to 3 segments: some source codes are absent from our 39 responses, a few segments appear to have
  been reassigned (education, health, defence), and his Notes say the new ambivalence code draws on three existing codes
  without saying which segments. Only the two context-specific segments were mapped to it. His refined pairings file
  would make the rescoring exact. Matched cells are 12 or fewer in every run, so small changes in the reference cannot
  move these figures far, but this is judgement and not a proof.
- **One run per configuration, 19 held-out responses.** The intervals are wide and the runs are not independent
  draws; the run-to-run spread is itself unmeasured (see [the main results page](README.md)).
- **Not the approved models.** These are the same local models as everywhere else in this directory.
- **Privacy.** The refined reference holds descriptions grounded in his coded segments, so it stays in a git-ignored
  run folder. This page carries counts, run names and a figure only.
