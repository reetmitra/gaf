# Coding rules

Every rule the pipeline enforces comes from the PI's own coding instructions in
`GPTPrompts.docx`. This file is the bridge between that document and
`gaf/config.py::CodingRules`: each rule appears with the verbatim quotation behind it,
the field that encodes it, the check that enforces it, and the severity — and why.

**Severity follows the PI's own modality.** Where he states a rule as an absolute
("a maximum of two codes"), the check emits an ERROR. Where he qualifies it
("usually between 2 and 12"), it emits a WARN. The check layer does not promote his
hedges into hard constraints.

Quotations preserve his wording, punctuation and spelling exactly. Where the three
prompt versions differ, all variants are given.

---

## 1. What a code is

> "A code is an explanation of a segment of text's key meaning. A codebook summarises
> these codes and their relationships."
> — *Prompt Version 2 (State)*; repeated in *Prompt Version 3 (State)*

This is why `CodingRules.require_description = True`: a code without a description is
not yet an explanation of anything. **S1**, WARN (not ERROR — a description can be
supplied at the human gate, and the embedder falls back to the name meanwhile).

## 2. The codebook has two levels

> "I have created a codebook with two levels of codes."
> — *Prompt Version 1*

> "your specific task is to apply a codebook that includes codes, sub-codes and the
> relationship between codes and sub-codes in a hierarchical format"
> — *Prompt Version 3 (State)*

`CodingRules.hierarchy_depth = 2`. Names are `toplevel-sub_level`, split on the
**first** hyphen only. **S3** (names) and **S6** (parent chains); WARN.

## 3. Two to twelve codes per response

> "One response can correspond to multiple codes: usually between 2 and 12."
> — *Prompt Versions 1, 2 and 3*

`min_codes_per_response = 2`, `max_codes_per_response = 12`. **S5**, WARN
(`too_few_codes` / `too_many_codes`). The word is **"usually"**, so this is advisory
and never causes a drop. *Open item (brief §16.4): confirm whether the PI wants these
hard. Flipping them is a severity change in one place, not a code change.*

## 4. A sentence may take several codes; one piece of text may take at most two

> "One sentence can be coded with multiple codes. The same piece of text can be coded
> with a maximum of two codes."
> — *Prompt Versions 2 and 3*
>
> "One sentence can be coded with multiple codes. The same text can be coded with a
> maximum of two codes."
> — *Prompt Version 1*

`max_codes_per_segment = 2`. **S4**, **ERROR** — this is the one count the PI states
as an absolute ("a maximum of").

Two quotes count as "the same piece of text" when their character spans overlap at
Jaccard ≥ `segment_overlap_threshold` (0.5). Spans come from S2, which is why S4
depends on S2 having run.

**Resolution policy: keep-and-flag.** Choosing *which* of three codes on one segment
survives is a judgment about meaning, and the structural layer does not make meaning
judgments. All involved candidates survive; the finding is attached to each and goes
to the audit log for the human gate. In CLI mode it drives the exit code.
*Open item (brief §16.5): confirm this with the PI.*

## 5. Code at phrase or sentence level

> "Coding is applied on the level of phrase or sentence."
> — *Prompt Versions 1, 2 and 3*

`max_quote_sentences = 2`. **S2b**, WARN when a verified quote spans more sentence
terminators than that. (Chan 2025 independently used the same bound: "extracting no
more than two sentences of supporting evidence per code to maintain a clear audit
trail".)

## 6. Prefer a sub-code before inventing a top-level code

> "Consider adding a second level code first before adding a top-level code."
> — *Prompt Versions 1, 2 and 3*

`prefer_subcode_first = True`. **S3**, WARN `sub_code_first`, raised when a bare
top-level candidate is proposed and the codebook already holds that family.

## 7. Change a code only when the existing one does not fit

> "Change or add a code only if an existing code does not adequately describe a part
> of the response"
> — *Prompt Version 3 (State)*
>
> "Change or add codes only if a code in the current codebook does not adequately
> describe the response or parts of the response."
> — *Prompt Version 1*

This is the **M2 dedup gate**, not a text rule: a new code is never created while a
near neighbour sits above τ_high, and the grey zone between τ_high and τ_low goes to
the judge. Prevention, not cleanup.

## 8. Review, merge and split at the twenty mark

> "After coding 20 responses: Review the codebook; Merge or split codes as required;
> Reapply the new codebook to all responses coded to that point."
> — *Prompt Version 2 (State)*
>
> "Second level codes can be merged or split."
> — *Prompt Version 1*

This is the **slow loop**. Note that the PI's own instruction includes *split*, and
that "reapply the new codebook to all responses coded to that point" is a
re-examination step — which is why the operation set in `gaf/models.py::Operation`
includes `split` and `reparent`, and why merges are merge-with-re-examination.

## 9. What the final codebook must be

> "The final codebook should: describe the responses completely; include discrete
> codes; use no more codes than necessary; be parsimonious."
> — *Prompt Version 2 (State)*
>
> "The final codebook should: describe the responses completely; have discrete codes
> labels; use no more codes than necessary; be parsimonious."
> — *Prompt Version 3 (State)*

Four goals, each with a mechanism:

| Goal | Mechanism |
|---|---|
| describe the responses completely | M3 `INCOMPLETE` verdicts; the agreement report's human-only list |
| discrete codes | M4 near-duplicate detection; the M2 dedup gate |
| no more codes than necessary | M2 routing; S5 upper bound; the saturation curve |
| parsimonious | slow-loop merge and re-parent operations, human-gated |

## 10. Column semantics of the coding spreadsheets

> "The code is in the "Code" column, the part of the response coded in the "Response"
> column and the response number in the "No" column."
> — *Prompt Version 1*
>
> "the response number is in the "Number" column, the part of the response coded in the
> "Response" column and the code applied is in the "Code" column."
> — *Prompt Version 3 (State)*

Note that the header for the response number differs between versions (**"No"** vs
**"Number"**). The ingest readers accept both; `tests/fixtures/xlsx.py` builds both.

Note also that in a *coded* workbook the "Response" column holds **the segment coded**,
not the whole response. That is exactly `gaf.models.Assignment`.

---

## The negative examples, and what each one became

The PI supplies two passes of negative examples. They are the most valuable part of
the document, because they name the specific ways a model's coding goes wrong. Each
category maps to a mechanism — or, in one case, deliberately does not.

### Reworked taxonomy (`GPTPrompts.docx`, "Reworked negative examples based on above criteria")

| His category (verbatim) | Becomes | Where |
|---|---|---|
| "Your code did not describe the response segment completely." | verdict `INCOMPLETE` | M3, WARN |
| "Your code did not describe the response segment precisely." | verdict `IMPRECISE` | M3, WARN |
| "Your code did  not have to be applied." | verdict `UNNECESSARY` | M3 — the quote is removed; the candidate is dropped if nothing remains |
| "You did not apply enough codes." | `too_few_codes` | S5, WARN |
| "You did not have to develop a code." | the M2 dedup gate | route MERGE instead of CREATE |
| "You did not generate a new code." | **no check** — see below | agreement report, human-only list |

### From the India sample (`GPTPrompts.docx`, "Negative examples for NarrativeState(India)")

| His category (verbatim) | Becomes | Where |
|---|---|---|
| "You created a code when you could have used a sub-code for an existing code." | `sub_code_first` | S3, WARN |
| "Your code was not precise enough" | verdict `IMPRECISE` | M3, WARN |

His worked examples for these two, quoted in full because they are the calibration
targets for the coder prompt's granularity spec:

> Response 57. AI is nothing but a machine with very powerful processing abilities
> which relies heavily on data inputs and data access to assist
> Your code: technology-processing_power
> My code: AI-data-driven

> Response 26. AI can do everything
> Your code: technology-all_encompassing
> My code: AI-multi-use

> Response 50: it is crucial to ensure that AI is developed and used in an ethical and
> responsible manner
> My code: concern-ethical_development
> Your code: concern-core_programming

Two things follow from these examples and are enforced in code:

1. `AI-superintelligence` and `AI-data-driven` are **capitalised**, and
   `positive_impacts-problem-solving` contains **a hyphen inside the sub-code**. The
   PI's own names are not internally consistent. Therefore S3 grammar findings are
   **WARN, never ERROR**, the pattern is applied after lowercasing, and the split is on
   the first hyphen only.
2. The corrections run in *both* directions — sometimes his code is more abstract than
   the model's (`AI-multi-use` over `technology-all_encompassing`), sometimes more
   specific (`negative_impacts-job_destruction` over `impact-jobs`). Granularity is
   therefore not a monotone "be more specific" instruction, and the coder prompt must
   carry his examples rather than a rule of thumb.

### The one category with no check, and why

> "You did not generate a new code."
> — Response 67: "it have ability to understand universe, humans and many more."
> My code: AI-superintelligence · Your code: future-inevitability

A code the machine **failed to invent** is invisible from inside a run: there is no
artefact to check, because the missing code left no trace. It is detectable only by
comparison against a human coding of the same responses. That is precisely the
"human codes the machine missed" list in the concurrent-validation report
(`gaf/analysis/agreement.py`), and it is why that list — rather than the headline
agreement percentage — is the output the write-up should quote.

The fast loop must therefore **never invent a replacement code** on an `IMPRECISE` or
`INCOMPLETE` verdict. Refinement is slow-loop and human work; the WARN is the
deliverable.
