# Guide for the principal investigator

This guide says what to open, in what order, what to look for in each file, and what is
waiting on you. Every path is relative to the repository root (`reetmitra/gaf`, branch
`live-run-oct`). Nothing in the repository contains a respondent's words, so every file
named here is safe to open and to forward.

## The result in five lines

1. The pipeline runs end to end on two small models on the researcher's laptop, costs
   nothing, and logs every step.
2. On the 19 held-out responses you coded, its individual codes do not line up with yours.
   Kappa is -0.010 in the baseline run and lies between -0.065 and +0.022 across ten runs
   (descriptions matched on both sides). The best single figure, +0.092, is one run matched
   by name only.
3. Rolled up to your 15 families, the same runs reach kappa +0.29 to +0.56. That is above a
   shuffled-response chance of +0.08 to +0.24, but 18 of 20 comparisons cannot tell it from
   a predictor that never reads a response and only repeats your commonest themes.
4. Changing the thresholds, the coder model, the judge or the temperature changed the size
   of the codebook and left agreement about where it was. The same settings run twice gave
   78 codes in 21 families the second time instead of 91 in 31.
5. None of this is the approved line-up (Claude Opus 5.5 with hosted Qwen3.8-Max). That run
   has not happened.

## What to open, in this order

Open the Markdown files on GitHub or in any editor. Open the `.svg` figures and
`views.html` in a web browser.

| # | Open | What it shows | What to look for |
|---|---|---|---|
| 1 | [`results/README.md`](../results/README.md) | The index to everything: the short version, every run in one table, what was built, what was tested, what was not | The five findings under "The short version", then "Not yet tried" near the end |
| 2 | [`results/india-process-39-local/00-at-a-glance.md`](../results/india-process-39-local/00-at-a-glance.md) | The 39 responses you coded, coded cold by local models: four figures and the findings each number supports | "Realisations" at the top; the agreement and calibration figures further down |
| 3 | [`results/agreement-checks.md`](../results/agreement-checks.md) and [`agreement-checks.svg`](../results/agreement-checks.svg) | Agreement with you, with 95% intervals, a shuffled-response chance level, the trivial predictor and a family-level roll-up | The dot chart: the machine's interval against the two baselines, leaf level and family level |
| 3b | [`results/agreement-refined.md`](../results/agreement-refined.md) | The same runs rescored against your refined codebook of 6 November | Whether the leaf-level result moves (it does not, provisionally), and the caveats on how the reference was rebuilt |
| 4 | [`results/india-process-39-local/06-agreement.md`](../results/india-process-39-local/06-agreement.md) | Your coding against the machine's, both ways, on the held-out 19 | "Over-coding" (machine codes you have no counterpart for) and "Blind spots" (your codes the machine never produced) |
| 5 | [`results/india-process-39-local/17-comparison.md`](../results/india-process-39-local/17-comparison.md) | The baseline against eight runs that each change one thing | The summary table at the top, then the realisation under each run |
| 6 | [`results/HOW-THE-RESULTS-WERE-REACHED.md`](../results/HOW-THE-RESULTS-WERE-REACHED.md) | The run history, step by step: the question each run asked, what changed, what happened | "Things that went wrong on the way" and "What is still open" |
| 7 | [`results/india-process-1-200-local/README.md`](../results/india-process-1-200-local/README.md) | All 200 responses coded cold: vocabulary growth, saturation, clustering | The saturation figure and the caveats at the end |
| 8 | [`results/india-process-39-local/views-machine/views.html`](../results/india-process-39-local/views-machine/views.html) | One self-contained page of figures from the machine's coding | Open it in a browser; no server needed |

The numbered pages inside each results folder (`01-inputs.md` to `14-timeline.md`) are the
tables behind the claims. You only need them to check a specific number.

## What is waiting on you

These are the eight decisions from the meeting. The recommendations are proposals for you to
overrule.

| # | Decision | Where it is explained |
|---|---|---|
| 1 | Confirm that sending response text to Anthropic and Alibaba Cloud is allowed under the ethics approval, and approve a spend ceiling (proposed USD 40; estimate USD 12 to 30) | [`docs/RUNBOOK.md`](RUNBOOK.md), "Live run: Opus 5.5 + hosted Qwen" |
| 2 | Rule on the 7 held label pairs | [`rulings/india-process.json`](../rulings/india-process.json), the `label_merges_held` list (7 pairs); the one merge already applied there is provisional until you overrule it |
| 3 | Confirm the reading of the 24 ambiguous highlights | [`results/india-process-39-local/01-inputs.md`](../results/india-process-39-local/01-inputs.md), "Ambiguous highlights" |
| 4 | Say what to do with the 6 highlights that could not be located | The same page, the "unlocated" row and the line below it |
| 5 | Say whether 40 of your code definitions stay local or are reworded, because they share a run of text with real responses | [`README.md`](../README.md), "Status and limitations", the bullet on imported code descriptions |
| 6 | Say how the two codebooks should be compared (proposed: family level first, leaf level second) | Steps 3 and 4 above |
| 7 | Say who acts as the human gate on the seeded run, and when | The next section |
| 8 | Choose a licence; the repository has none, so nobody else may legally reuse it | Nothing to read: it is a choice |

## The human gate

The one step that only you can do is the human gate. The seeded run over the other 161
responses halts by design at its first checkpoint and waits for a person.

```bash
uv run gaf checkpoint --run runs/<the halted run> --interactive
```

The refactorer proposes an edit script for the codebook: splits, re-parents, merges and
renames. Each operation is checked by deterministic code first, so one that could not be
applied never reaches you. For each operation you accept, reject or edit it. Without
`--interactive`, or with no terminal attached, every operation is rejected and nothing is
applied, so the absence of a person is never an automatic accept. The full procedure is in
[`docs/RUNBOOK.md`](RUNBOOK.md), "The human gate".

## The ten steps after the meeting

Steps 1 and 7 are yours. The rest can be run by the researcher or whoever takes over.

| # | Step | Who |
|---|---|---|
| 1 | Confirm the approvals and the spend ceiling | You |
| 2 | Add the API keys; confirm the Qwen host, model id and rates | Researcher or successor |
| 3 | Smoke test on 2 responses with a USD 1 cap | Researcher or successor |
| 4 | Calibrate on the 20-response fold | Researcher or successor |
| 5 | Evaluate on the 39 coded responses | Researcher or successor |
| 6 | Run the seeded run on the 161, halting at the first checkpoint | Researcher or successor |
| 7 | Act as the human gate at a terminal | You |
| 8 | Resume the run and export the results pack | Researcher or successor |
| 9 | Decide the thresholds and record the decision | You and the researcher |
| 10 | Optional: a private appendix of worked disagreement cases (needs respondent text, so it stays off GitHub) | Researcher or successor |

## Where the rest of the repository is

| To find | Open |
|---|---|
| The method in prose you can quote in the paper | [`docs/METHODS.md`](METHODS.md) |
| Every check, why it exists and what it cannot see | [`docs/VALIDATION.md`](VALIDATION.md) |
| How to run anything, including live runs and spend caps | [`docs/RUNBOOK.md`](RUNBOOK.md) |
| Your coding rules, each with the quotation behind it | [`docs/CODING_RULES.md`](CODING_RULES.md) |
| The design and where its complexity sits | [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) |
| Every non-obvious decision, including the ones that went badly | [`docs/DECISIONS.md`](DECISIONS.md) (55 records; ADR-0049 is the local models, ADR-0051 and ADR-0052 your line-up, ADR-0055 the cache fix) |
| The model line-ups | `profiles/`: `local-ollama.json` is the all-local baseline, `opus-qwen.json` your approved line-up, `opus-local-qwen.json` its cheaper rehearsal |
| The code | `gaf/`, with one folder per stage; the tests are in `tests/` |

## What the results do not show

- They describe two small models on a laptop, not the approved line-up.
- The agreement figures rest on 19 held-out responses, one run per configuration. Read each
  one as an interval, not a point.
- The same settings do not reproduce between runs, even at temperature 0 with a fixed seed.
  The cause has not been found, and the size of the run-to-run spread has not been measured.
- The human gate has never been run, so no result here includes a person restructuring the
  codebook.
- The clustering and pattern pages use a lexical similarity, not the real embedder, and say
  so in their own caveats.

## Words used in the results

| Word | Meaning here |
|---|---|
| Kappa | Agreement beyond chance. 0 is chance, 1 is perfect. Below 0.1 is treated as within chance |
| F1 | The share of matched cells, balancing what the machine found against what you found |
| Cell | One response paired with one code. Your 19 held-out responses give about 146 cells |
| Leaf level, family level | Individual codes, against your 15 top-level families |
| Held-out fold | 19 of your 39 coded responses, fixed in advance and never used to calibrate |
| Cold run | The machine starts from an empty codebook |
| Seeded run | The machine codes into a codebook you already built; a production tool, not a validation one |
| Grey zone | Where the two coders neither clearly agree nor clearly differ, so the judge rules |
| Trivial predictor | A baseline that repeats your commonest themes without reading anything |
| Shuffled chance | Agreement after the machine's codes are shuffled across responses |
