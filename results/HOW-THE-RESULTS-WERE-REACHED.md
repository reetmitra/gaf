# How the results were reached

The same 39 responses were coded many times, each time with one thing changed, and each result
decided what to try next. This page is the sequence: what each run was for, what was expected, what
happened, and what it led to. Numbers are in the [results index](README.md) and the folders it points
to; this page is about the reasoning.

## Ground rules that shaped every run

- **One change at a time.** Every comparison run keeps the same 39 responses, the same held-out
  fold (19 responses, fixed in advance by an ids-only split file with a recorded hash) and the same
  agreement code, and changes a single thing: the thresholds, or coder A, or the judge.
- **Calibrate on one fold, judge on the other.** The 20 responses of the calibration fold were used to
  look at thresholds. The 19 held-out responses were never used to tune anything.
- **Local first.** The approved line-up (Claude Opus 5.5 with hosted Qwen3.8-Max) waits on the PI's
  confirmation of two data processors, so everything here ran on models served on one laptop, at a cost
  of USD 0. These runs test the pipeline and say nothing about what the hosted models would find.
- **Report refuted hypotheses.** Two of the main hypotheses below failed, and the failures are in the
  results as findings.
- **Nothing leaves the machine un-scanned.** Every exported file is checked against every real response
  at a 20-character window before it lands, and the whole export is deleted on a hit.

## The sequence

| step | when | question | what changed | what happened | what it led to |
|---|---|---|---|---|---|
| 1. Offline baseline | Sep | Does the harness run end to end and measure agreement? | coders were deterministic stand-ins (a keyword table) | it did; agreement with the PI was near zero (kappa about -0.04 and -0.01) | agreement from a stand-in coder was never the question; move to real models |
| 2. Local models | 25 Sep | Can every role run on this machine with nothing leaving it? | a provider for Ollama (ADR-0049), an embedding comparison, a 10-response pilot | yes | a profile for the all-local line-up |
| 3. Plan for the live run | 4 Oct | What must exist before real models touch real data? | providers for Anthropic and a hosted Qwen, a spend cap, the PI's rulings, a pre-registered split (ADR-0050 to 0053) | built and tested | the all-local chain as a fallback and a rehearsal, because the hosted run was blocked |
| 4. Calibration fold | 7 Oct | Are the provisional thresholds right for this embedding space? | 20 responses coded; the threshold sweep run on them | all three thresholds pointed to about 0.95, on a flat plateau | do not adopt on one fold; check on the held-out fold |
| 5. Evaluation | 7 to 8 Oct | How much does the machine agree with the PI? | 39 responses coded cold on default thresholds | kappa near zero (-0.010 with descriptions, +0.011 by name); the held-out calibration check pointed the same way | the cause was not obvious, so test the obvious levers one at a time |
| 6. Seeded run | 8 Oct | Does the hand-over to a human gate work? | seeded with the PI's codebook, set to halt at the first checkpoint | it halted after 10 of 161 responses, by design | the PI has to act as the gate; this is open |
| 7. A way to test calibration | 29 Oct | Does acting on the calibration help? | `--thresholds` file option (ADR-0054) so a before-and-after costs one run, not an edit to the code | shipped, defaults unchanged | the plateau experiment |
| 8. Plateau thresholds | 30 Oct | Hypothesis: the calibrated thresholds cut compute and do not hurt agreement | thresholds 0.90, 0.95, 0.90 | **refuted**: 399 judge calls against 291, 125 codes against 91, kappa +0.018 against -0.010, which is within chance | keep the defaults; calibration is evidence about the space, not a recipe |
| 9. Cold run on all 200 | 30 Oct | Hypothesis: more responses improve agreement | all 200 coded with no seed | **refuted** for agreement: codes grew from 91 to 162 and saturated at batch 18, held-out kappa stayed at -0.009 | more data adds vocabulary; look at the coder and at how agreement is measured |
| 10. Coder swaps | 5 Nov | Hypothesis: coder A is the bottleneck | qwen3.5:9b replaced by qwen2.5:7b-instruct, llama3.1:8b, mistral:7b-instruct in turn | **mostly refuted**: codebook size moved (20 to 36 families) and agreement did not | the measure itself deserves a second look |
| 11. Re-examining the measure | 5 Nov | Is "kappa near zero" the whole story? | bootstrap intervals, a shuffled-response chance level, a trivial predictor, and a roll-up to the PI's 15 families | leaf-level agreement is at zero and below the trivial predictor because the vocabularies differ; at family level kappa is 0.34 to 0.56, above chance, but not clearly above the trivial predictor | part of the near-zero is vocabulary mismatch; the diagnosis is partial |
| 12. New strategies | 5 Nov | Is the judge the problem? Is a run reproducible? How big is run-to-run variation? | a third-family judge; a repeat with a fresh cache; two repeats with both coders at temperature 0.7 | started 22:04; see the results index for what has finished | the answers decide whether any single-run comparison above is worth more than its interval |

## What each result taught

- **Coders dominate the clock.** About 61% of model time is the two coders and 39% the judge, so the
  levers on speed are output length and model choice, not the judge.
- **The thresholds are wrong for this embedding space, and moving them still does not help.** The
  calibration direction is stable (four folds all say about 0.95), but acting on it costs more judge
  calls and a more fragmented codebook for no agreement gain. Two statements that sound contradictory
  are both true and are kept apart.
- **The judge's pattern is partly its design.** It can drop coder B's candidate or keep both, never
  back B alone, so a zero for B is built in. An early note read that zero as a possible bias and was
  corrected the same day.
- **A comparison needs fresh calls counted separately from replayed ones.** The baseline replayed 114
  judge calls from earlier runs, which flattered its timings until the comparison page counted fresh
  calls on their own.
- **The coder's effect is on the codebook's shape.** Twenty to thirty-six families from the same
  responses, with agreement unmoved.
- **Leaf-level agreement was the wrong headline on its own.** It mixes "did not find the theme" with
  "named it differently". The family-level roll-up separates them, and says the machine finds the PI's
  themes better than chance.

## Things that went wrong on the way, and what was done

- A phrase in the knowledge-graph report tripped the privacy test; the graph was moved outside the
  repository.
- The exporter's guard missed a response when a string sat at the edge of a cell, when a description
  quoted a whole short response, and when a finding's message quoted a response. Each was fixed with a
  test. While adding one rule, an edit left the guard scanning almost nothing for one export; the
  exporter's own tests caught it, the export was deleted before it left the machine, and it was never
  committed.
- A wrong estimate (4.5 hours for the whole seeded run) ignored that the run halts at its first
  checkpoint; it was corrected in the ledger.
- A laptop sleep window froze the first evaluation for an hour; that hour is excluded from the time
  counted.
- While setting up the repeat runs, the response cache turned out not to key on a model's temperature, so
  a changed temperature would have replayed the old answers. It was fixed (ADR-0055) and the repeat runs
  use a fresh cache each.

## What is still open

The hosted-model run, the human gate, repeats (started), the private worked-disagreement appendix, and a
reading of why the leaf vocabularies differ. The ideas not yet run are listed in the results index.
