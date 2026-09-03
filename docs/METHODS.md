# Methods

*Methods-appendix prose for the study "AI Futures and Analysis". Written to be read by
a methods reviewer, and to be quotable — with the numbers replaced by those of the run
being reported — in the paper itself.*

**Research question.** What are the constituent elements of global AI futures?

**Data.** Open-ended survey responses in which respondents describe one specific,
vivid scenario for AI in their society by 2050. The seed sample is 20 responses from
India. The survey question itself is not recorded in the response file and is attached
to every record at ingest, because it travels with every coding call: a coder that
cannot see the question cannot code the response in context.

---

## 1. Analytic approach

The study is **inductive grounded theory**, not framing analysis. Codes are generated
from the data rather than applied from a prior scheme, and the codebook is developed
through constant comparison across responses. The vocabulary throughout is grounded
theory's: initial coding, constant comparison, memoing, theoretical sampling,
theoretical saturation, core category, storyline (Chun Tie, Birks & Francis 2019).

The analysis is **computational grounded theory** in the sense of Alqazlan et al.: a
human codes a sample first, machine analysis then scales that coding to the full
corpus, the two are compared in a **concurrent validation** step, and the human
performs the interpretation. This pipeline's entire check layer *is* that concurrent
validation step, folded into the analysis as a practice rather than bolted on
afterwards as correction.

The quantitative tail follows Chan (2025), who established the method this study
extends: a hybrid human–LLM coding pass produces a **binary occurrence matrix** of
codes across units of analysis, low-frequency codes are filtered out, and **Ward's
hierarchical cluster analysis** over that matrix reveals groupings that are named and
interpreted. The number of groupings is taken from the agglomeration schedule rather
than chosen in advance.

---

## 2. Why the human sits where it sits

The most consequential design decision in this pipeline is **where the human works**,
and it follows from evidence rather than convenience.

Vaccaro, Almaatouq and Malone (2024, *Nature Human Behaviour*) meta-analyse 106 effect
sizes and find that human–AI combinations perform, on average, **worse than the better
of human or AI alone** (Hedges' g = −0.23, 95% CI −0.39 to −0.07). The losses
concentrate in **decision tasks** (g = −0.27); the gains concentrate in **creation
tasks** (g = 0.19); and synergy is moderated by whether the **division of labour is
predetermined**.

Item-by-item human verification of each machine coding is precisely the decision-task
overlay that finding warns against. So this pipeline does not do it. The human gate
sits instead at the level of **codebook restructuring**, where the task is generative —
split an overloaded code, re-parent a misplaced one, merge two that turned out to be
one concept — and where the division of labour is fixed in advance: the machine
proposes an edit script, the human accepts, rejects or edits each operation.

This is less human labour per checkpoint and more leverage per decision. It is also
the reason the residual error is *measured* rather than hand-corrected: see §6.

---

## 3. The pipeline

### 3.1 Fast loop, per response

Each response is prepared deterministically — normalised, segmented into phrase- and
sentence-level spans, checked against the corpus for exact duplication, and given a
context assembled from a **frozen, content-addressed snapshot** of the codebook: the
hierarchy skeleton plus the codes nearest the response in the embedding space.

Two coders then code the response **independently, from identical context**, using
mid-tier models from **different providers**. This is the epistemic-diversity
mechanism: two models with different training and different failure modes agreeing on
a code is evidence the code is in the data rather than in one model's habits.

Coders **propose**; they never edit the codebook.

### 3.2 Verification, in two tiers

**Structural checks (S1–S6)** are deterministic, free, and use no embeddings and no
model. They validate the *form* of the coding against the principal investigator's own
coding instructions, each of which is recorded verbatim in `docs/CODING_RULES.md`:
schema and description (S1); evidence provenance, with every quote located in the
normalised response text and a character span recorded (S2); phrase- or sentence-level
coding (S2b); two-level code-name grammar and the preference for a sub-code before a
new top-level code (S3); at most two codes on the same piece of text (S4); the usual
range of two to twelve codes per response (S5); and codebook invariants — unique names,
resolvable parents, bounded depth, evidence at leaves (S6).

Severity follows the investigator's own modality. Rules he states absolutely produce
ERRORs; rules he qualifies ("usually between 2 and 12") produce WARNs. The check layer
does not promote his hedges into hard constraints.

**Semantic checks (M1–M4)** are embedding-first. All similarity in the system is
computed in **one versioned embedding space**, so a threshold means the same thing
everywhere. M1 matches the two coders' proposals by **Hungarian assignment** and
reports the agreement rate. M2 routes each accepted proposal against the codebook using
a **two-threshold band**: at or above τ_high it merges into an existing code, below
τ_low it becomes a new code, and only the band between is genuinely ambiguous. M3 asks
whether a code fits the evidence it was applied to. M4 reports near-duplicate codes
within a family.

The **dedup gate** lives in M2: a new code is never created while a near neighbour sits
above τ_high. This is prevention rather than cleanup, and it is the direct answer to the
duplicate-code proliferation documented in the predecessor study.

### 3.3 Escalation

A frontier model from a **third provider** acts as judge, and is consulted only where
the deterministic layers cannot decide: a cross-coder dispute, a grey-zone similarity,
or a low code–evidence fit. **Coder disagreement is the escalation signal.** Agreement,
the common case, costs nothing extra — so epistemic diversity and cost control are the
same mechanism rather than competing ones.

When the judge rules on code–evidence fit it returns one of four verdicts, mirroring
the investigator's own categories of coding error: `APPLIES`; `IMPRECISE` ("your code
was not precise enough"); `INCOMPLETE` ("did not describe the response segment
completely"); and `UNNECESSARY` ("your code did not have to be applied"), which removes
that quote from the code's evidence. The fast loop never invents a replacement code on
`IMPRECISE` or `INCOMPLETE` — refinement is slow-loop and human work, and the flag is
the deliverable.

### 3.4 Slow loop, per checkpoint

Checkpoints are event-driven on codebook health, with a hard floor of every 50
responses. At a checkpoint a frontier model sees the whole codebook with usage
statistics and proposes an **edit script** over a deliberately wide operation set:
create, merge, **split**, **re-parent**, rename, no-op.

The width matters. The predecessor study's agent could only create, merge or rename;
unable to restructure, it accreted parallel concepts, then merged semantically
different ideas on superficial lexical overlap, and the codebook progressively
flattened until the downstream clustering collapsed. `split` and `re-parent` exist
because their absence is the documented cause of that failure.

Every proposed operation is validated deterministically before a human sees it — an
operation that could not be applied never reaches the review — and the resulting
codebook is re-checked against the S6 invariants. **Evidence is conserved by
assertion**: the multiset of (response, quote) pairs is compared before and after every
operation, and an operation that would lose evidence raises rather than proceeding.

The human then reviews a compact per-operation diff and accepts, rejects or edits each
one. **Nothing is applied without an explicit accept**; with no human present the
checkpoint is a no-op, never an auto-accept. Applying produces a new content-addressed
snapshot and a changelog.

### 3.5 Analysis tail

Deterministic, with no model calls. Codes and responses become a **binary occurrence
matrix**; codes appearing in fewer than *n* responses are filtered out; **Ward's
linkage** clusters the responses; the **agglomeration schedule** is reported with each
merge distance and its change; and **cluster means** give the prominence of each code
within each cluster, which is what the clusters are interpreted from.

Respondent metadata is joined **here and only here** — never during coding, so that a
coder cannot condition on who the respondent is.

---

## 4. Reproducibility

Every artefact is content-addressed. A codebook snapshot's identifier is the hash of
its own canonical serialisation, which contains no wall-clock time; a code records the
snapshot that admitted it rather than when it was created. Two runs of the pipeline
over the same corpus with the same configuration therefore produce **byte-identical
codebook JSON and an identical snapshot-id sequence**.

Order independence was verified rather than assumed: shuffling the corpus and re-running
produces the same final codebook, because code identity derives from content and
evidence is ordered by content rather than by arrival.

The audit log is append-only, enforced by database triggers rather than by convention;
snapshots are immutable on the same basis. Every model call records its prompt version,
so a change of wording is a visible event rather than silent drift.

The entire pipeline runs offline with deterministic mock model clients and a lexical
embedding fallback, requiring no API key and no network. That is the configuration the
test suite and continuous integration use.

---

## 5. Thresholds

τ_high = 0.80, τ_low = 0.45 and τ_fit = 0.30 are **provisional**. They were set against
a lexical fallback embedder and have not been calibrated against human judgment. A
calibration module exists and produces, from a human-coded golden set, a precision/recall
curve for each threshold together with a recommendation; it reports and never silently
changes a constant. **These values should be described as provisional in any write-up
until that calibration has been run against the investigator's own hand-codings.**

One finding from the offline runs bears directly on this and should be reported rather
than buried. M1, M2 and M4 compare a code to a code — two short strings of similar
shape. M3 compares a code to a *quote* — a curated label against raw respondent prose.
These are different geometries, and in the offline lexical space the second does not
discriminate at all: the median code–evidence similarity is 0.000, and no threshold
separates good applications from bad. Consequently, in an offline run M3's warnings are
artefacts of the stand-in embedder rather than findings about the coding, and the run
report says so. Whether a live embedding model separates them is an empirical question
that the first live run answers.

---

## 6. Validation

See `docs/VALIDATION.md` for the full dossier. In summary, three independent checks:

**Concurrent validation** against the investigator's own hand-coding of the seed sample,
at two levels. At **code level**, machine codes are matched to human codes through the
embedding space and precision, recall, F1 and a chance-corrected agreement statistic are
reported. At **segment level**, agreement is weighted by span overlap, so that a code
applied to the right response but the wrong sentence is visible as a partial failure
rather than scored as a hit.

Both directions of non-agreement are reported explicitly: codes the machine applied that
the human did not (**over-coding**), and codes the human applied that the machine missed
(**blind spots**). The second list is the only place one of the investigator's own
categories of coding error — failing to generate a code that was warranted — can be
detected at all, because a code that was never invented leaves no artefact inside a run.
These two lists, rather than the headline agreement percentage, are the most informative
output of the validation.

**Saturation.** New codes per batch, cumulative unique codes and the rate of change are
tracked across the run, giving the plateau that theoretical sampling requires as evidence
that the corpus has been saturated.

**Lexical validation.** A model-free external check, designed by a software engineer at
the Max Planck Institute, Berlin, on whether the vocabulary driving a per-response score
depends on how that score is posed. An L1-penalised continuous model and two binarised
cuts are each fitted with cross-validated regularisation, the vectoriser fitted inside
each fold, and their top-20 vocabularies compared by Jaccard overlap with bootstrap
stability. High overlap means the simpler binary presentation is defensible. **Low
overlap is a finding to report, not a failed test**, and the module never fails on it.

---

## 7. Limitations

- The thresholds are uncalibrated (§5) and the offline embedding space is a stand-in
  that measures lexical overlap rather than meaning. Similarity statistics from an
  offline run characterise the fallback, not the codebook.
- **M3's cost profile is unproven.** In offline runs the fit check accounts for the
  large majority of frontier calls, which is the opposite of the intended profile in
  which the judge is rare. Until a live run demonstrates otherwise, the cost estimate
  should be quoted either excluding M3 or with an explicit worst case of one judge call
  per quote.
- **Chan's cluster-count rule is not robust at n = 20.** The rule takes the largest
  break in the agglomeration coefficients and subtracts its stage from the sample size;
  it assumes that break falls near the root of the tree, as it did in his 50-article
  study. On a 20-response sample with sparse code vectors the largest break falls at the
  leaf end and the rule returns a degenerate answer. It has deliberately not been
  patched: the cluster count is the study's headline, and amending a published method to
  make a number look sensible is exactly the failure this project exists to avoid. The
  count must be taken from a corpus large enough for the rule to behave, or stated
  explicitly and recorded as an override.
- The seed sample is small and uneven: five of the twenty responses fall below the
  survey's own 100-word minimum, and three contain no sentence punctuation at all, which
  constrains how finely they can be segmented.
- Human corrections are held out of the coder prompt by default. Recycling them as
  few-shot examples is supported but would make the golden set no longer independent of
  the system it evaluates.

---

## References

Alqazlan, L. et al. *A Novel Human-in-the-Loop Computational Grounded Theory Framework
for Big Social Data.* Big Data & Society.

Chan, D. *The University and Employability in Singapore Media.* 2025.

Chun Tie, Y., Birks, M. & Francis, K. *Grounded Theory Research: A Design Framework for
Novice Researchers.* SAGE Open Medicine, 2019.

Essary, A. *A Guide to Hierarchical Cluster Analysis in Agricultural Communications
Research.* 2022.

Ng, W. X. & Chan, D. *SLE Final Report.* 2026.

Vaccaro, M., Almaatouq, A. & Malone, T. *When Combinations of Humans and AI Are Useful:
A Systematic Review and Meta-analysis.* Nature Human Behaviour, 2024.
