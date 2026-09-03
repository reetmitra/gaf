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
| **ERROR** | structural certainty of invalidity | the candidate or quote is dropped; `gaf check` exits 1 |
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
| **M1** | cross-coder agreement, by Hungarian assignment over the two coders' proposals | a dispute, or a score in the grey band | the epistemic-diversity mechanism. Two models from different providers agreeing is evidence the code is in the data. **Disagreement is also the router's escalation signal**, so diversity and cost control are one mechanism |
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

The investigator's hand-codings of the seed sample **have not yet arrived**. The harness
is built and tested against a synthetic stand-in, and the real file drops in with one
environment variable and no code change (`docs/RUNBOOK.md`). Until then:

- the reported agreement figures are the harness's self-test, not findings about this
  study;
- **τ_fit, τ_high and τ_low remain uncalibrated** — the calibration module produces a
  full precision/recall curve and a recommendation the day real inputs exist, and it
  reports rather than silently changing a constant.

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
- **Order independence** is verified, not assumed: shuffling the corpus produces the
  same final codebook, because code identity is content-addressed and evidence is
  ordered by content rather than arrival.
- The **audit log is append-only and snapshots are immutable**, enforced by database
  triggers that abort the write — not by convention.
- Every model call records its **prompt version**, so a change of wording is an event in
  the log rather than invisible drift.
- A **golden-set regression harness** pins the offline output byte for byte, plus a
  manifest of the coding rules, the model registry, the embedding space and a hash of
  every prompt template — so a prompt edit that the mock clients happen to absorb still
  fails by name.
