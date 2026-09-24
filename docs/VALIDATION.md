# The verification dossier

*What this pipeline checks, why each check exists, what it costs, and what it cannot
see. Written so that a methods reviewer can audit a run line by line.*

The check layer is this project's implementation of the **concurrent validation** step
of the Alqazlan et al. human-in-the-loop computational grounded theory framework —
validation folded into the analysis as a practice, not applied afterwards as
correction.

Every check reports through one contract: a `CheckFinding` carrying a check id, a
severity, a scope, a subject, one human-readable sentence and a machine-readable
payload. **A checker never mutates the codebook, never writes to the store and never
calls the router.** That is structural rather than conventional: a `CheckReport` holds
findings and nothing else, and the router holds no report at all.

## Severity, and what it is allowed to cost

| Severity | Meaning | Consequence |
|---|---|---|
| **ERROR** | structural certainty of invalidity | at the candidate gate the candidate or quote is dropped; at codebook scope (S4, S6) nothing is dropped and the finding is the deliverable. `gaf check` exits 1 either way |
| **WARN** | a rule is violated but the judgment is contestable | kept and flagged for the human gate |
| **INFO** | an observation — a score, a band, a route | recorded for the audit trail |

ERROR is reserved for things that are certainly invalid regardless of interpretation: a
quote that is not in the source, a code name that is not unique, a parent that does not
exist. **Anything requiring a judgment about meaning is at most a WARN**, because the
structural layer does not make meaning judgments.

Severity also follows the principal investigator's own modality. Where he states a rule
absolutely ("the same piece of text can be coded with a maximum of two codes") the check
emits an ERROR. Where he qualifies it ("usually between 2 and 12") it emits a WARN. See
`docs/CODING_RULES.md` for the verbatim quotation behind every rule.

---

## Structural checks — deterministic, free, no embeddings, no model

| id | What it validates | Severity | Why it exists |
|---|---|---|---|
| **S1** | schema: a name, evidence, and a description that is not a copy of its own quote | ERROR on missing name or evidence; WARN on the description | a code is "an explanation of a segment's key meaning" — without one it is not yet a code |
| **S2** | evidence provenance: every quote located in the normalised response, exactly or by fuzzy window, with a character span recorded | INFO per unverified quote (dropped); ERROR if none survive | a code that cannot be traced to the corpus cannot be audited. This is the check that makes every downstream span meaningful |
| **S2b** | phrase- or sentence-level coding: at most two sentence terminators, and at most 40 words | WARN | the investigator's rule. The word bound exists because three of the twenty real responses contain no sentence punctuation at all, so a terminator count alone does not bind |
| **S3** | two-level name grammar, and preferring a sub-code before a new top-level code | WARN, never ERROR | his own codes are inconsistently capitalised and punctuated, so grammar is advisory |
| **S4** | at most two codes on the same piece of text, clustered by character-span overlap | ERROR | his one absolute count. **Keep-and-flag**: all involved candidates survive and the finding goes to the human, because choosing which code to drop is a meaning judgment |
| **S5** | two to twelve codes per response | WARN | "usually" — advisory, never a drop |
| **S6** | codebook invariants: unique names, resolvable parents, bounded depth, evidence at leaves, evidence pointing into the corpus | mixed | the shape the codebook must keep for the analysis tail to mean anything |

## Semantic checks — embedding-first, judge only in the grey zone

All similarity is computed in **one versioned embedding space**, whose identifier is
recorded with every score. Scores from different spaces are never comparable, which is
what makes a threshold a meaningful number rather than a floating constant.

| id | What it validates | Escalates when | Why it exists |
|---|---|---|---|
| **M1** | cross-coder agreement, by Hungarian assignment over the two coders' proposals | a score in the **grey band** only; a dispute below τ_low is kept and flagged | the epistemic-diversity mechanism. Two models from different providers agreeing is evidence the code is in the data. **A grey-zone score is the router's escalation signal**, so diversity and cost control are one mechanism |
| **M2** | integration routing against the codebook, in a two-threshold band | a score between τ_low and τ_high | contains the **dedup gate**: a new code is never created while a near neighbour sits above τ_high. Prevention, not cleanup |
| **M3** | whether a code fits the evidence it was applied to | fit below τ_fit | the investigator's four categories of coding error, made checkable. `UNNECESSARY` removes the quote; `IMPRECISE` and `INCOMPLETE` flag for the human and **never cause a replacement code to be invented** |
| **M4** | near-duplicate codes within a family | never | feeds the slow-loop refactor proposal. **Never auto-merges** — merging is a human-gated decision |

### The two-threshold band

A single cut forces every comparison into "same" or "different". The band admits a third
answer:

```
score >= tau_high  ->  MERGE    the geometry is certain enough to fold in
score <  tau_low   ->  CREATE   certain enough to admit as new
otherwise          ->  JUDGE    genuinely ambiguous, and the only case worth paying for
```

The predecessor study used a single blended lexical threshold of 0.3 and recovered 21
matched code pairs against 66 and 73 left unmatched. Lexical overlap is not meaning.

---

## Newer mechanisms, outside the frozen check layer

None of the six mechanisms below carries an id from `gaf.checks.contracts.CHECK_IDS` —
that tuple is frozen and enumerates only S1–S6 and M1–M4 — so each is documented here on
its own terms: what it checks, and, in the same place, what it cannot.

### Coded-set placement (the `resolved` outcome)

**What it checks.** On a corpus larger than the coding covers, a highlight that sits
verbatim in several responses is placed in the one response the coding demonstrably
reached — the **coded set**, every response already holding at least one `exact` or
`fuzzy` highlight — when exactly one of its candidates is in that set. It is counted
apart from `exact` and `fuzzy`, in `HighlightsReport.summary()`, because it rests on
different evidence: the coding's coverage, not the text of the response.

**What it cannot see.** Which response the segment actually came from, when a *coded*
response and an *uncoded* one happen to share the very phrase in question. The rule
only ever prefers the coded candidate because the uncoded ones are, on independent
grounds, less likely to be what the coding was about — it is an inference from coverage,
not a verification of authorship. If the researcher's coding later reaches a response it
had not reached before, the coded set changes and so, potentially, do these placements:
`resolved` is a property of *this* pairing of coding and corpus, not a fixed fact about
either alone (ADR-0031).

### The Definer's guards (D1–D4)

**What they check.** Form, not truth: whether a reply is empty (D1), how many sentences
it runs to (D2), whether it reproduces one of the code's own segments whole (D3) or
strings together a run of eight or more of its consecutive words (D4). All four are
deterministic string measurements, and all four are ERROR: a description that is a quote
is refused rather than flagged, because refusing destroys nothing here and a quote is
not shareable at any length (ADR-0042).

**What they cannot see.** Whether the description is *right* — whether it actually says
what the code captures and how it differs from its siblings, which is the researcher's
own instruction for what a description should do. A description that is fluent, three
sentences long, and uses none of its own segments' phrasing passes every guard even if
it is simply wrong about what the code means. The guards are a shareability and
structural-sanity net; judging whether a description is a *good* one is the same
interpretive act as judging whether a code is (see below), and belongs to whoever reads
`organised.md` or `organised_shareable.md` (ADR-0034).

### Code growth and the spike rule

**What it checks.** Whether a batch admitted an unusual number of new codes. Two rules,
each answering the question the batch's position in the run makes answerable: an
absolute ceiling (`handover.new_codes`), and, once `spike_window` batches exist behind
it, at least a stated multiple of the median of those batches (`handover.spike`). A
batch inside the window is judged by the ceiling **only**: the ratio rule reports that
it has no baseline and raises nothing, so the same fact is not reported twice under two
names (ADR-0040).

**What it cannot see.** Whether a spike is *bad*. The rule reports a count crossing a
line; it does not read the codebook to decide whether the line-crossing reflects
accretion of parallel concepts or a corpus that genuinely introduced a new topic in that
batch. The first batch of every cold run crosses the absolute ceiling by design, because
with no predecessor to compare against everything it admits counts as new — that is not
evidence of anything going wrong, and a reader must not treat a reported spike, or the
ceiling being crossed, as a defect.
Its floor, window and multiplier are uncalibrated, set by argument rather than against
a human's judgment of where a codebook actually started accreting parallel concepts,
and are labelled so everywhere they appear (ADR-0033).

### The decision matrix and the handover

**What it checks.** That every row's condition is rendered against the run's own
thresholds rather than a hard-coded default, and — by construction, asserted in tests —
that every routing band, every checkpoint trigger and every structural operation is
covered by some row, so the matrix cannot silently drift from the code it describes.

**What it cannot see.** Whether the conditions themselves are well chosen. The matrix is
a trigger, not a diagnosis: it can only say that a stated numeric line was crossed, using
thresholds that are themselves uncalibrated (the spike rule, above; the existing
τ_high/τ_low/τ_fit). A codebook that is fine but happened to cross a line, and one that
is quietly degrading but has not yet crossed any line, are both invisible to it in the
way that matters for a reader's trust.

### Affinity, patterns, the crosswalk

**What they check.** Affinity groups leaf codes by a blend of embedding cosine and
co-occurrence Jaccard; the crosswalk maps one codebook's leaves onto another's by the
same embedding space M2 already uses; pattern mapping reports code combinations by
Jaccard over binary occurrence, with no embedding step at all.

**What they cannot see, offline.** Affinity's cosine half and the crosswalk's whole
comparison describe the **fallback lexical embedder** in exactly the sense M3 does
(ADR-0019): a code's name-and-description pair sharing no tokens with another scores
zero regardless of whether the two concepts are related, so an affinity group or a
crosswalk mapping found offline is only as trustworthy as the lexical overlap it is
built from. `AffinityResult.offline_caveat` states this on the artefact itself whenever
the embedding space is the lexical fallback — including one a calibration run has
given a label of its own, which is exactly the run where it matters most — and
`Crosswalk.fair_mode_note` does the equivalent for an asymmetric comparison, stating how
many of the **leaves actually compared** carry a description on each side rather than
whether any code anywhere in either codebook does (ADR-0044). Affinity's blend weight and similarity cut are
additionally uncalibrated (ADR-0036), so an affinity group boundary is provisional
twice over — from the embedder underneath it and from the cut drawn on top of it. Pattern
mapping's Jaccard-over-code-sets has no embedding step and is not subject to this
caveat; it can still only say that codes co-occur, never why.

### Seeded runs

**What a seeded run enables.** Coding into an organisation a person has already built:
retrieval finds its codes, the coder sees its hierarchy, and the routing band folds new
evidence into it rather than beside it. Its own evidence is held out of the run, so its
codebook, occurrence matrix and saturation curve describe only what that run itself
coded.

**What it cannot be used for.** Validation. Its agreement with the coding that produced
its seed is not independent evidence about either, because the machine was shown the
shape of the answer before it started (ADR-0035). Only a **cold** run — no
`--seed-codebook` — belongs in the concurrent-validation figures below.

---

## What the checks cannot see

Stated plainly, because a validation dossier that lists only what it catches is
misleading.

**A code that was never invented.** The investigator's own error taxonomy includes
"you did not generate a new code" — a warranted code the machine failed to propose. This
leaves **no artefact inside a run**: there is nothing to check, because nothing was
produced. It is detectable only by comparison against a human coding of the same
responses, and appears there as the **blind-spot list**. This is why that list, rather
than the headline agreement percentage, is the most informative output of validation.

**Meaning, in the offline embedding space.** The offline fallback embedder measures
lexical overlap. It is adequate for code-to-code comparison (M1, M2, M4), where both
sides are short strings drawn from the same vocabulary. It is **not** adequate for M3,
which compares a code label against raw respondent prose: the median similarity is
0.000 and no threshold separates. In an offline run M3's warnings characterise the
stand-in embedder, not the coding, and the run report says so where the counts appear.

**Whether a code is *good*.** Every check here is about form, provenance, consistency
and geometry. Whether a codebook is a good grounded theory of the data is an
interpretive judgment that belongs to the researcher, and the pipeline is built to
deliver that judgment better evidence, not to replace it.

---

## Concurrent validation against the human golden set

Two levels, because they answer different questions.

**Code level.** Machine codes are matched to human codes through the embedding space by
Hungarian assignment at τ_high, then precision, recall, F1 and Cohen's κ are computed
over the response × code matrix. κ rather than Krippendorff's α: there are exactly two
coders, complete data and binary nominal categories, so α's extra machinery buys nothing
and κ is derivable by hand from the reported observed and expected agreement.

**Segment level.** Do human and machine attach the code to the *same span*? Agreement is
weighted by character-span overlap, so "right code, wrong place" is visible as a partial
failure rather than counted as a hit. The two levels demonstrably differ: on the
reference fixture a case with the same code on the same response but a different segment
scores 1.00 at code level and 0.00 at segment level.

**Both unmatched lists are reported**: machine codes with no human counterpart
(over-coding) and human codes the machine missed (blind spots), formatted for direct
quotation with the response id, the segment and the nearest miss.

### Status

The investigator's hand-coding of the 20-response seed sample **arrived on 9 September**
and drops into the regression harness with one environment variable and no code change
(`docs/RUNBOOK.md`); the calibration module has since run against it
([`results/india-process-1-20/07-calibration.md`](../results/india-process-1-20/07-calibration.md)).
His codebook definitions and the full 200-response corpus arrived after that. Even so:

- **τ_fit, τ_high and τ_low remain uncalibrated in the sense that matters: the constants
  in `gaf/config.py` have not moved.** τ_high and τ_low rest on only 18
  candidate/nearest-neighbour pairs from the seed sample — too few to move a threshold
  on, by the calibration report's own reading — and τ_fit's F1 is flat from 0.45 to
  1.00 over the 197 code applications it does have, meaning this golden set barely
  discriminates it either. The module reports a recommendation for each; it does not
  act on one, and a move happens only through a recorded decision.
- The same posture now extends to two newer families of constant that did not exist
  when this dossier was first written: the spike rule's floor, window and multiplier
  (ADR-0033), and affinity's blend weight and similarity cut (ADR-0036). Neither has
  been checked against a human's judgment of the property it is meant to detect.
- Until a calibration with enough units to move a number exists, the reported agreement
  figures are still closer to the harness's self-test than to a finding about this
  study, and a **seeded** run's agreement figures are not evidence at all — see
  "Seeded runs", above.

---

## Lexical validation

A model-free external check on whether the vocabulary driving a per-response score
depends on how that score is posed. Three targets — a continuous model and two binarised
cuts — each fitted with an L1 penalty and cross-validated regularisation, across two
feature spaces built from an identical vocabulary, and their top-20 word lists compared
by Jaccard overlap.

Three things make it trustworthy rather than decorative:

1. **The vectoriser is fitted inside each cross-validation fold.** Fitting it on the
   full data first leaks and inflates the score; the pipeline structure is asserted in a
   test.
2. **Score = 2 is a negative example in the ge3 cut, never a dropped row.** Silently
   dropping those rows is the other common way to get this test wrong, and the count is
   asserted.
3. **Bootstrap stability.** L1 selection on a few hundred documents is unstable, so
   every fit is repeated over resamples and each word's selection frequency is reported.
   A word in 48 of 50 resamples means something; a word in 12 does not.

The module **refuses to fit** rather than producing a meaningless number when a
binarised cut has fewer than ten positives or ten negatives — which is what happens, and
should happen, on the 20-response seed sample. **Low Jaccard overlap is a finding to
report, not a failure**: the module never exits non-zero on it.

---

## Saturation

New codes per batch, cumulative unique codes and the rate of change, reported as a table
and a chart. A plateau is the evidence grounded theory requires that theoretical
sampling has reached saturation; a curve still climbing at the end of the corpus is
itself a finding about coverage.

---

## Reproducibility as a validation property

Every claim above is only as good as the run being reproducible.

- Codebook JSON contains **no wall-clock time**; a code records the snapshot that
  admitted it. Two runs produce byte-identical output and an identical snapshot-id
  sequence.
- **Order independence** rests on three things, and the first is the operative one:
  the fast loop sorts the corpus by `(source, id)` before coding, so the order a corpus
  arrives in never reaches the pipeline; code identity is content-addressed on the name;
  and evidence is ordered by content rather than arrival. Under a *genuine* reorder the
  codebook's substance — codes, names, descriptions, evidence, assignments — is
  identical, while `created_in_snapshot` legitimately differs, because it records which
  batch admitted a code and is provenance about that traversal rather than a property of
  the codebook.
- The **audit log is append-only and snapshots are immutable**, enforced by database
  triggers that abort the write — not by convention.
- Every model call records its **prompt version**, so a change of wording is an event in
  the log rather than invisible drift.
- A **golden-set regression harness** pins the offline output byte for byte, plus a
  manifest of the coding rules, the model registry, the embedding space and a hash of
  every prompt template — so a prompt edit that the mock clients happen to absorb still
  fails by name.
