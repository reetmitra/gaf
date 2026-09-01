# Architecture decision records

Every non-obvious choice gets an entry. Format: context, decision, consequences.
Superseded ADRs stay in place with a pointer, never deleted — the log is part of the
audit trail.

---

## ADR-0001 — Clean-room rebuild rather than refactoring `pipeline3-main`

**Status:** accepted (Wave 0)

**Context.** A previous implementation exists, grown out of an inherited undergraduate
codebase. It carries an Entman `Function` enum this study does not want, `sys.path`
manipulation, a known `created_at`/`updated_at` class-definition-time default bug, and
a narrow edit-operation set that is the documented cause of codebook flattening. The
PI asked for the new project to stand on its own.

**Decision.** Build from scratch. Do not read, import, vendor or diff against
`pipeline3-main`. What carries over is the *design*, restated in the brief; every
algorithm is re-derived from specification.

**Consequences.** Some work is redone. In exchange the repository has no inherited
vocabulary, no dead paths, no `sys.path` hacks, and a git history that is entirely
this project's. Where the brief describes an algorithm that the old code also
implements, the specification in the brief is authoritative.

---

## ADR-0002 — SQLite blackboard rather than a directory of JSON files

**Status:** accepted (Wave 0)

**Context.** Chan (2025) used four plain stores (codebook, article database, chunks,
changelog). The predecessor pipeline wrote JSON files. Both are readable, and both
make cross-cutting questions ("every finding on response 39 across all runs") a
directory walk.

**Decision.** One SQLite database as the blackboard. Codebook snapshots are also
exported as JSON, because JSON is the artefact a reviewer reads and diffs.

**Consequences.** Referential integrity (`PRAGMA foreign_keys`), indexed queries, and
— the reason that matters — **append-only and immutability enforced by the database**.
Triggers abort `UPDATE`/`DELETE` on `audit` and on `snapshots`, so "the audit log is
append-only" is a property of the store rather than a promise about the code. Cost: a
binary file rather than greppable text, mitigated by the JSON exports and the HTML
explorer.

---

## ADR-0003 — Embedding-first matching, never lexical, for meaning

**Status:** accepted (Wave 0)

**Context.** The predecessor matched codes with TF-IDF cosine blended with word-set
Jaccard (0.6/0.4) at a threshold of 0.3, and recovered 21 matched pairs against 66 GPT
and 73 Gemini codes left unmatched (Ng & Chan 2026, §4).

**Decision.** One versioned embedding space for retrieval, the dedup gate, cross-coder
matching and code↔evidence fit. Hungarian assignment, not greedy matching. A
two-threshold routing band (τ_high = 0.80, τ_low = 0.45). Lexical similarity is used
only for **quote provenance** (S2), where the question really is "does this string
occur in the source", never for meaning.

**Consequences.** Every similarity in the system is comparable with every other, so a
threshold means one thing everywhere; the space id is recorded with each score so
scores from different spaces are never silently compared. `code_text()` is the single
rendering function. The offline path needs a lexical *fallback embedder* — a
deterministic stand-in for the space, not a return to lexical matching.

---

## ADR-0004 — The human gate sits at codebook-refactor level, not per response

**Status:** accepted (Wave 0)

**Context.** Vaccaro et al. (2024, *Nature Human Behaviour*) meta-analyse 106 effect
sizes: human–AI combinations average **worse** than the best of human or AI alone
(Hedges' g = −0.23, 95% CI −0.39 to −0.07). Losses concentrate in decision tasks
(g = −0.27); gains concentrate in creation tasks (g = 0.19); synergy is moderated by
whether the division of labour is predetermined.

**Decision.** No item-by-item human verification of machine codings. The human gate is
at the slow loop, reviewing a compact refactor diff: accept, reject or edit each
operation.

**Consequences.** The human task is generative (restructure a hierarchy) rather than a
decision overlay, and the division of labour is fixed in advance — the two conditions
under which the meta-analysis finds synergy. Less labour per checkpoint, more leverage
per decision. Risk: an individual mis-coding can survive to the analysis tail. That is
accepted deliberately and answered by the *concurrent validation* against the golden
set, which measures the residual error rather than trying to eliminate it by hand.

---

## ADR-0005 — Grounded theory vocabulary throughout; no Entman framing

**Status:** accepted (Wave 0)

**Context.** The Chan (2025) baseline is a framing study and codes Entman's four frame
functions. This study is inductive grounded theory with an open research question.
The PI reads grounded theory.

**Decision.** No `Function` enum, no framing functions, no "frames" in any output. The
vocabulary is grounded theory's throughout code, docs and user-facing strings:
initial coding, constant comparison, memoing, theoretical sampling, theoretical
saturation, core category, storyline; and codes, families, clusters, themes.

**Consequences.** The analysis tail is inherited from Chan unchanged as *method*
(binary occurrence matrix → Ward's HCA → agglomeration schedule → cluster means) while
its *interpretation* changes: clusters of responses characterised by prominent codes,
not frames. `families()` groups by the first-hyphen split of a code name, which is the
grounded-theory two-level structure, not a fixed function taxonomy.

---

## ADR-0006 — Stdlib frozen dataclasses, not Pydantic

**Status:** accepted (Wave 0)

**Context.** The brief allows either, and asks for a justification.

**Decision.** `dataclasses` from the standard library, `frozen=True, slots=True`.

**Consequences.**

1. *Fewer dependencies on the offline path.* Offline-first is a hard requirement, and
   every core dependency is a thing that can fail to install from a clean clone.
2. *The validation Pydantic would provide is needed in exactly one place* — parsing
   untrusted model replies — and there it must be **fail-safe rather than raising**: a
   malformed reply has to degrade to a non-destructive default, not throw. That is
   `gaf/llm/base.py`'s `parse_json_object` + `validate_enum` + `FAIL_SAFE_DEFAULTS`,
   which is a different contract from schema validation.
3. *Frozen-ness is load-bearing.* The design law says a checker reports and never
   mutates; frozen dataclasses make a mutation a `FrozenInstanceError` rather than a
   convention, so a stage that must alter a candidate constructs a new one and the
   change becomes visible.

Cost: `to_json`/`from_json` are written by hand. They earn their place anyway, because
the evidence loader must tolerate two on-disk shapes (see ADR-0008).

---

## ADR-0007 — `created_in_snapshot` instead of `created_at` on a code

**Status:** accepted (Wave 0)

**Context.** Acceptance criterion 3 requires two runs of `make demo` to produce
byte-identical codebook JSON. A wall-clock timestamp on a code makes that impossible.
(The predecessor codebase additionally shared one class-definition-time default across
every instance — a known wart.)

**Decision.** `Code` carries `created_in_snapshot`, the id of the snapshot that
admitted it, and no timestamps at all. Codebook JSON is timestamp-free. Wall-clock
time lives in the store (`audit.created_at`, `snapshots.created_at`), where it belongs
and where byte-identity is not claimed.

**Consequences.** A code's provenance is content-addressed and reproducible rather
than dependent on when the run happened. `Codebook.to_json_str()` — sorted keys,
name-sorted codes — is the exact byte sequence hashed into a snapshot id.

---

## ADR-0008 — The evidence loader accepts both on-disk shapes

**Status:** accepted (Wave 0)

**Context.** The canonical in-memory shape is `list[Evidence]`. Codebook JSON in this
lineage has also stored evidence as `{response_id: [quote, ...]}`, and a JSON
round-trip stringifies the integer keys.

**Decision.** `Code.from_json` accepts a list of evidence objects *or* a mapping keyed
by response id with **either str or int keys**. `to_json` always emits the canonical
list. A bare string in an evidence list raises, rather than being guessed at: a quote
that cannot name its response has no provenance.

**Consequences.** The PI's artefacts and the pipeline's own load through one path.
Asymmetric round-trip (read two shapes, write one) is deliberate and tested.

---

## ADR-0009 — `Operation.type` stays a `Literal`, with a runtime whitelist beside it

**Status:** accepted (Wave 0)

**Context.** The brief froze `Operation.type` as
`Literal["create","merge","split","reparent","rename","noop"]`. A `StrEnum` would give
runtime validation, but would deviate from the frozen contract.

**Decision.** Keep the `Literal` exactly as specified, and export
`OPERATION_TYPES: tuple[str, ...]` alongside it. `Operation.from_json` validates
against the tuple and raises on an unknown type.

**Consequences.** Static typing and runtime validation both hold, the frozen contract
is honoured verbatim, and the slow loop can validate an incoming edit script before
anything is applied. Serialised JSON is identical either way.

---

## ADR-0010 — The low-frequency filter supports both an absolute count and Chan's fraction

**Status:** accepted (Wave 0)

**Context.** The brief specifies "drop codes appearing in fewer than *n* responses;
default 2". Chan (2025) specifies a *fraction*: "elements that appeared in less than 5%
of the codes (than three out of fifty articles) were filtered out". At n = 50 those are
different filters.

**Decision.** `AnalysisConfig` carries both: `min_code_frequency: int = 2` (the brief's
default, always active) and `min_code_frequency_fraction: float | None = None` (set to
0.05 to reproduce Chan's rule exactly). When both are set, the stricter applies. Both
are reported in the run report.

**Consequences.** The brief's default is what runs unless someone asks for Chan's, and
"reproduce the Chan method exactly" remains achievable in one config change rather
than a code edit. Which filter produced a matrix is always recorded.

---

## ADR-0011 — scikit-learn pinned below 1.10

**Status:** accepted (Wave 0)

**Context.** Brief §13 specifies the lexical validation's binarised cuts verbatim:
`LogisticRegressionCV(penalty="l1", solver="liblinear", scoring="roc_auc", ...)`.
scikit-learn 1.9 deprecates `penalty=` on that estimator in favour of `l1_ratios`, and
warns that its fitted attributes are simplified in 1.10.

**Decision.** Pin `scikit-learn>=1.4,<1.10`.

**Consequences.** The brief's literal specification runs as written, and the fitted
attributes the vocabulary extraction reads do not change under the project mid-flight.
When the pin is eventually lifted, `penalty="l1"` becomes `l1_ratios=(1,)` and the
coefficient-reading code must be re-checked against `use_legacy_attributes=False`.
This ADR should be revisited then, not silently.

---

## ADR-0012 — Python pinned to 3.12

**Status:** accepted (Wave 0)

**Context.** `requires-python = ">=3.12"`. The development machine's system
interpreter is Homebrew Python 3.14.6, whose `pyexpat` fails to load against the
system libexpat — which breaks `openpyxl` (and anything else parsing XML) for reasons
unrelated to this project.

**Decision.** `.python-version` pins 3.12; `uv` provisions its own interpreter.

**Consequences.** The environment is identical on any machine and in CI, and does not
depend on the host's Python being healthy. The floor stays `>=3.12` in
`pyproject.toml`, so the package itself is not narrowed by the pin.

---

## ADR-0013 — A description that copies its own quote is a WARN

**Status:** accepted (Wave 0)

**Context.** S1 requires a description "that is not a verbatim copy of an evidence
quote". The brief assigns ERROR to a missing name or missing evidence and WARN to a
missing description, but does not state a severity for a description that is present
and is a copy.

**Decision.** WARN.

**Consequences.** ERROR is reserved for structural certainty of invalidity, and a
description that is present is not *missing* — the defect is that it explains nothing,
which is a judgment about quality. Dropping the candidate would destroy evidence over
a formatting complaint that the human gate can repair in one edit. Recorded here
because it is a Wave-0 ruling that a later agent would otherwise have to guess at.

---

## ADR-0014 — The embedding protocol is frozen separately from its implementation

**Status:** accepted (Wave 0)

**Context.** Wave 1 runs A2 (embedding service) and A4 (semantic checks) in parallel.
A4 needs the embedding contract; it must not need A2's code.

**Decision.** `gaf/embed/protocol.py` is a frozen Wave-0 contract holding the
`Embedder` protocol, `code_text`, `Route` and `route_similarity`. A2 implements it;
A4 codes against it and tests with `tests/fixtures/embedding.py::StubEmbedder`.

**Consequences.** The two agents cannot collide, and the routing band and the code
rendering are defined in exactly one place — which is what makes τ_high mean the same
thing in M1, M2 and M4. Same reasoning applies to `gaf/store/schema.py`, frozen apart
from A1's repository API.

---

## ADR-0015 — S2b also bounds a quote by word count

**Status:** accepted (Wave 1, orchestrator amendment to a frozen contract)

**Context.** S2b enforces the PI's rule that "Coding is applied on the level of phrase
or sentence" by counting sentence terminators in a verified quote. Profiling the real
seed sample showed that **three of the twenty responses contain no sentence terminator
at all** — ids 18, 21 and 56, at 107, 107 and 102 words respectively. A quote of such a
response in full counts as one sentence and passes S2b untouched, so on 15% of the real
corpus the rule does not bind.

**Decision.** Add `CodingRules.max_quote_words: int = 40` as a second S2b condition,
with its own finding marker. 40 is the word-equivalent of the existing two-sentence
bound: this corpus runs about 20 words per sentence (median 5 sentences per ~105-word
response). This is not a new rule — it is the same rule of the PI's, made enforceable
on text that lacks the punctuation the terminator count relies on.

**Consequences.** The frozen contract `gaf/config.py` gained a field mid-wave. The
change is **additive with a default**, so nothing that already reads `CodingRules`
breaks; the frozen-contract rule exists to prevent incompatible change, not to prevent
a compatible extension the real data demands. Re-broadcast to A3, who owns S2b.

Related, and deliberately *not* changed: S4 clusters quotes by span overlap, so an
unpunctuated response is only a problem if a coder quotes it whole. The fix belongs in
the coder (quote at phrase level, splitting on clause boundaries when punctuation is
absent), not in the check. A3 must not assume every response contains a full stop.

---

## ADR-0016 — Mojibake is repaired at ingest, never in normalisation

**Status:** accepted (Wave 1)

**Context.** Response 57 of the real seed sample contains `‚ÄúNot now. I am tired‚Äù` —
UTF-8 curly quotes decoded once as a legacy codepage (`“` is UTF-8 `E2 80 9C`, which
read as MacRoman renders `‚Äú`). Responses 9 and 10 contain a genuine `…` and a stray
`‚` that must not be touched.

**Decision.** Repair at **ingest**, in `gaf/ingest/`, before the text becomes
`Response.content` and before the content hash is computed. `gaf/textnorm.py` is not
changed. A repair is accepted only when re-encoding strictly *reduces* the count of
suspicious characters, which is what keeps the genuine ellipsis and the lone `‚` intact.

**Consequences.** Every persisted span indexes into `normalise(content)`, so repairing
downstream of ingest would mean spans pointing into mangled text; repairing inside
`normalise` would change the frozen span contract for every caller. Ingest is the only
place both problems are absent. After repair plus normalisation all twenty real
responses are pure ASCII. The repair is recorded on the response's metadata rather than
applied silently — a silent data mutation is what the transparency principle forbids.

---

## ADR-0017 — Store write semantics: immutable-by-content, and a total order on every read

**Status:** accepted (Wave 1, A1)

**Context.** Acceptance requires byte-identical artefacts across runs. Two things
quietly break that: a re-write that silently reconciles differing content under an
existing key, and a read whose row order depends on insertion timing rather than
content.

**Decision.**

1. *Immutable by content.* Re-writing an identical snapshot, response or run config is
   a no-op. Writing **different** content under the same key raises
   (`SnapshotIntegrityError` / `StoreConflictError`) rather than reconciling.
2. *Every read has a total `ORDER BY`.* Insertion order (`rowid` / `event_id`) is used
   only where insertion order *is* the meaning — the audit log, findings read back as a
   `CheckReport`, LLM calls, snapshots. Everywhere else the order is by content:
   responses by `(source, response_id)`, assignments by
   `(response_id, code_name, span_start, assignment_id)`.

**Consequences.** The occurrence matrix is independent of the order in which the fast
loop happened to finish responses, so a parallel run and a serial run produce the same
matrix. A partial-tie `ORDER BY` would have been a latent non-determinism that only
appeared under concurrency, which is the worst kind to debug.

Two mutating methods exist beyond the read/append surface — `update_candidate` (status,
resolution, code id) and `decide_checkpoint` (the human gate's per-operation verdicts).
Neither table is trigger-protected, because a candidate's fate and a human's decision
are genuinely state transitions rather than facts. The immutable tables remain
`snapshots` and `audit`.

---

## ADR-0018 — Content-addressed ids carry an ordinal where content can legitimately repeat

**Status:** accepted (Wave 1, A1)

**Context.** Ids must be pure functions of content so that two runs mint the same ids.
But some content legitimately repeats: the same finding can be emitted twice, one
coding can propose the same candidate name twice, one run can make the same LLM call
twice.

**Decision.** `candidate_id`, `finding_id` and `llm_call_id` take an `ordinal`.
Hash parts are joined with `\x1f` and `None` renders as `\x00`, so `("ab", "c")` and
`("a", "bc")` — and `None` versus `""` — cannot collide.

**Consequences.** Ids stay deterministic while a primary-key collision becomes
impossible. `HASH_LENGTH = 16` hex characters (64 bits) is the truncation, justified in
the module docstring by the birthday bound at this corpus size; the full digest remains
available.

---

## ADR-0019 — M3 does not discriminate in the offline embedding space, and is documented as such

**Status:** accepted (Wave 1, orchestrator finding)

**Context.** Running the delivered Wave-1 components as a fast loop over the real
20-response India sample produced 174 code↔evidence pairs. Their fit scores under the
offline lexical embedder (`lexical-v1-512`):

```
n=174   min 0.000   median 0.000   mean 0.087   max 0.475

tau_fit   0.05   0.10   0.15   0.20   0.30
escalate   51%    59%    76%    86%    95%
```

The **median is zero**: after stoplisting and stemming, a code's `name: description`
and a survey-response fragment share no tokens at all in about half of all pairs. No
threshold separates good pairs from bad ones, because the signal is not present.

The same run's M2 code↔code scores are perfectly bimodal — 79 pairs at exactly 1.000
and 18 below 0.45, with **nothing in the grey zone**.

**The cause is structural, not a tuning error.** M1, M2 and M4 compare a code to a
code: two short, similarly-shaped strings drawn from the same vocabulary. M3 compares a
code to a *quote*: a curated label against raw respondent prose. These are different
geometries, and a threshold calibrated on one cannot be reused on the other. The
project has one τ_high and one τ_low precisely because code↔code comparison is one
space; τ_fit was specified as if it belonged to the same family, and it does not.

**Decision.** Three things, none of which is a silent change to a threshold:

1. τ_fit stays at 0.30. It is not lowered to chase the offline distribution, because
   even τ_fit = 0.05 escalates 51% — there is nothing to tune towards.
2. **M3's offline behaviour is documented as non-discriminating.** Its WARNs in an
   offline run are an artefact of the fallback embedder, not findings about the coding,
   and the run report must say so rather than presenting 166 warnings as substance.
3. τ_fit calibration requires **both** the PI's golden set **and** a live embedding
   model. `gaf/checks/health.py::calibrate_thresholds` already produces the curve and
   never writes to `CodingRules`; it needs real inputs, not more code.

**Consequences.** The cost argument for the fast loop — "the judge is consulted only
where the geometry is ambiguous" — holds for M1/M2 but is **unproven for M3**. If a
live embedding space does not separate code↔quote pairs substantially better, M3 as
specified would escalate most quotes and the frontier-call budget would not hold. That
is a risk to surface in the methods write-up, not to paper over.

A design alternative exists and is deliberately **not** implemented here, because it
exceeds the brief: compare a quote against the code's existing *evidence centroid*
(quote-to-quote, one geometry) rather than against its label and description. That
would make M3 the same kind of comparison as the rest. It should be put to the PI as a
question before anyone builds it.

Related: the same run shows M2's routing decided by exact name identity under the
lexical fallback (79 of 97 at cosine 1.000). A2 independently measured that a
paraphrased candidate retrieves its true match at only 0.385 — below τ_low — so the
router would create a duplicate. Offline dedup counts are therefore not evidence about
the codebook, and must not be reported as such.
