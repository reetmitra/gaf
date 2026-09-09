# Architecture decision records

Every non-obvious choice gets an entry. Format: context, decision, consequences.
Superseded ADRs stay in place with a pointer, never deleted — the log is part of the
audit trail.

## Index

| ADR | Title | Status |
|---|---|---|
| [ADR-0001](#adr-0001--clean-room-rebuild-rather-than-refactoring-pipeline3-main) | Clean-room rebuild rather than refactoring `pipeline3-main` | accepted (Wave 0) |
| [ADR-0002](#adr-0002--sqlite-blackboard-rather-than-a-directory-of-json-files) | SQLite blackboard rather than a directory of JSON files | accepted (Wave 0) |
| [ADR-0003](#adr-0003--embedding-first-matching-never-lexical-for-meaning) | Embedding-first matching, never lexical, for meaning | accepted (Wave 0) |
| [ADR-0004](#adr-0004--the-human-gate-sits-at-codebook-refactor-level-not-per-response) | The human gate sits at codebook-refactor level, not per response | accepted (Wave 0) |
| [ADR-0005](#adr-0005--grounded-theory-vocabulary-throughout-no-entman-framing) | Grounded theory vocabulary throughout; no Entman framing | accepted (Wave 0) |
| [ADR-0006](#adr-0006--stdlib-frozen-dataclasses-not-pydantic) | Stdlib frozen dataclasses, not Pydantic | accepted (Wave 0) |
| [ADR-0007](#adr-0007--created_in_snapshot-instead-of-created_at-on-a-code) | `created_in_snapshot` instead of `created_at` on a code | accepted (Wave 0) |
| [ADR-0008](#adr-0008--the-evidence-loader-accepts-both-on-disk-shapes) | The evidence loader accepts both on-disk shapes | accepted (Wave 0) |
| [ADR-0009](#adr-0009--operationtype-stays-a-literal-with-a-runtime-whitelist-beside-it) | `Operation.type` stays a `Literal`, with a runtime whitelist beside it | accepted (Wave 0) |
| [ADR-0010](#adr-0010--the-low-frequency-filter-supports-both-an-absolute-count-and-chans-fraction) | The low-frequency filter supports both an absolute count and Chan's fraction | accepted (Wave 0) |
| [ADR-0011](#adr-0011--scikit-learn-pinned-below-110) | scikit-learn pinned below 1.10 | accepted (Wave 0) |
| [ADR-0012](#adr-0012--python-pinned-to-312) | Python pinned to 3.12 | accepted (Wave 0) |
| [ADR-0013](#adr-0013--a-description-that-copies-its-own-quote-is-a-warn) | A description that copies its own quote is a WARN | accepted (Wave 0) |
| [ADR-0014](#adr-0014--the-embedding-protocol-is-frozen-separately-from-its-implementation) | The embedding protocol is frozen separately from its implementation | accepted (Wave 0) |
| [ADR-0015](#adr-0015--s2b-also-bounds-a-quote-by-word-count) | S2b also bounds a quote by word count | accepted (Wave 1, orchestrator amendment to a frozen contract) |
| [ADR-0016](#adr-0016--mojibake-is-repaired-at-ingest-never-in-normalisation) | Mojibake is repaired at ingest, never in normalisation | accepted (Wave 1) |
| [ADR-0017](#adr-0017--store-write-semantics-immutable-by-content-and-a-total-order-on-every-read) | Store write semantics: immutable-by-content, and a total order on every read | accepted (Wave 1, A1) |
| [ADR-0018](#adr-0018--content-addressed-ids-carry-an-ordinal-where-content-can-legitimately-repeat) | Content-addressed ids carry an ordinal where content can legitimately repeat | accepted (Wave 1, A1) |
| [ADR-0019](#adr-0019--m3-does-not-discriminate-in-the-offline-embedding-space-and-is-documented-as-such) | M3 does not discriminate in the offline embedding space, and is documented as such | accepted (Wave 1, orchestrator finding) |
| [ADR-0020](#adr-0020--chans-cluster-count-rule-is-not-robust-at-n--20-and-is-not-silently-repaired) | Chan's cluster-count rule is not robust at n = 20, and is not silently repaired | accepted (Wave 1, orchestrator finding) |
| [ADR-0021](#adr-0021--coders-read-the-frozen-snapshot-integration-routes-against-the-working-codebook) | Coders read the frozen snapshot; integration routes against the working codebook | accepted (Wave 2, B2 — verified by the orchestrator) |
| [ADR-0022](#adr-0022--m3-is-84-of-frontier-calls-on-the-real-sample) | M3 is 84% of frontier calls on the real sample | accepted (Wave 2, orchestrator measurement) |
| [ADR-0023](#adr-0023--where-framing-is-permitted-and-where-it-is-not) | Where "framing" is permitted, and where it is not | accepted (Wave 3, orchestrator ruling on a violation C2 reported) |
| [ADR-0024](#adr-0024--real-respondent-text-reached-git-history-and-what-was-done-about-it) | Real respondent text reached git history, and what was done about it | accepted (Wave 4, after an independent adversarial review) |
| [ADR-0025](#adr-0025--findings-of-the-wave-4-adversarial-review) | Findings of the Wave 4 adversarial review | accepted (Wave 4) |
| [ADR-0026](#adr-0026--a-meaning-ruling-never-is-an-error-but-it-can-leave-a-state-that-is) | A meaning ruling never *is* an ERROR, but it can leave a state that is | accepted (Wave 4, second adversarial review) |
| [ADR-0027](#adr-0027--what-the-history-rewrite-cost-and-what-was-done-about-it) | What the history rewrite cost, and what was done about it | accepted (Wave 4, second adversarial review) |
| [ADR-0028](#adr-0028--gitignore-protects-git-not-the-directory) | `.gitignore` protects git, not the directory | accepted (Wave 4, second adversarial review) |
| [ADR-0029](#adr-0029--the-pis-files-arrive-in-two-shapes-the-readers-did-not-know-and-one-of-them-names-no-response) | The PI's files arrive in two shapes the readers did not know, and one of them names no response | accepted (Wave 4, second adversarial review) |
| [ADR-0030](#adr-0030--a-respondent-fragment-reached-a-local-commit-through-a-code-comment-the-provenance-scan-read-one-corpus-only) | A respondent fragment reached a local commit through a code comment; the provenance scan read one corpus only | accepted (results export, 2026-09-09) |

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

---

## ADR-0020 — Chan's cluster-count rule is not robust at n = 20, and is not silently repaired

**Status:** accepted (Wave 1, orchestrator finding)

**Context.** Chan (2025), quoting Essary (2022), chooses the cluster count by finding
the largest break in the agglomeration coefficients and then taking
`n_clusters = n_samples − break_stage`. His worked example: 50 articles, largest break
entering stage 47, therefore 3 clusters. Our implementation reproduces that example
exactly (verified independently).

Applied to the real 20-response seed sample it returns **18 clusters**. The schedule
shows why:

```
stage  distance    delta
    1    0.0000   0.0000     two responses with identical code-vectors merge for free
    2    1.0000   1.0000  <- the largest delta in the whole schedule
   ...
   17    2.9059   0.4227     -> would give 3 clusters
   18    3.7268   0.8208     -> would give 2 clusters
   19    4.0042   0.2774
```

Twenty responses yield only 19 distinct code-vectors, so the first merge costs nothing
and the second necessarily jumps. That jump is the largest in the schedule, the rule
selects stage 2, and `20 − 2 = 18`.

**The rule silently assumes the largest break is near the root.** In Chan's data it was
3 merges from the end. At n = 20 with sparse binary vectors it is at the leaf end, and
the rule's arithmetic then reads the tree backwards.

**Decision.** Do **not** patch the rule. `choose_n_clusters` continues to implement it
literally, emits a warning when the result is degenerate, and `AnalysisConfig.n_clusters`
provides an explicit override that is recorded as `n_clusters_source = "config_override"`
rather than being passed off as a derived result.

**Consequences.** The cluster count is the headline of the analysis — it is how many
themes the study reports — so choosing it by a rule that misfires on the seed sample
would put a false number in the write-up. Three options exist and the choice is the
PI's, not the pipeline's:

1. run the analysis on the full corpus, where n is large enough for the break to fall
   near the root as Chan's does;
2. restrict the break search to the last k stages, which is what Chan's example does
   implicitly — a defensible amendment, but an amendment to a published method and so
   not one to make unilaterally;
3. state the count explicitly and record it as an override, which is what the current
   configuration supports.

On this sample the late breaks give 2 clusters (stage 18) or 3 clusters (stage 17); the
predecessor study expected 3 and produced 2, which is the failure this project exists
to avoid — so the number must not be arrived at by accident.

---

## ADR-0021 — Coders read the frozen snapshot; integration routes against the working codebook

**Status:** accepted (Wave 2, B2 — verified by the orchestrator)

**Context.** §4 of the brief places the frozen snapshot behind both the coder's context
and M2's integration routing. Taken literally, every candidate in a batch routes against
the codebook as it stood at the batch boundary — so within batch 1 nothing can ever
MERGE, because nothing has been created yet. On the real 20-response sample that yields
roughly 48 codes where the design intends 18.

**Decision.** Split the two uses of the snapshot:

* **Coders read the frozen snapshot.** This is the order-dependence guard, and it is
  where the guarantee actually lives: what a coder proposes must not depend on which
  responses came first.
* **Integration routes against the working codebook**, which accumulates within the
  batch. A new snapshot is frozen at the batch boundary.

**Consequences — and why this does not reintroduce order dependence.** The concern is
real and was tested rather than argued. Three properties hold, verified by the
orchestrator on the *real* corpus, not on fixtures:

1. Two runs in the same order produce byte-identical codebook JSON, assignments,
   findings and snapshot sequence.
2. **Three independent shuffles of the real corpus (seeds 1, 7, 99) produce a
   byte-identical final codebook and an identical assignment set.**
3. Re-running a batch from the snapshot frozen at its start reproduces the full run's
   final codebook, snapshot tail and assignments (B2's own test).

**Correction (Wave 4).** Property 2 as originally stated overclaimed, and the test
cited for it could not reach the property. `fast_loop._ordered` sorts the corpus by
`(source, id)` before anything is coded, and every fixture response shares one `source`
— so shuffling the *list* is undone before the first coder call. The shuffle test pins
that the sort exists and is load-bearing; it does not by itself demonstrate order
independence, because it never produces a different processing order.

Tested where it can actually fail — by varying `source` to permute the traversal, ids
and text untouched — the result is: **the codebook's substance is identical** (code set,
names, descriptions, evidence, and every assignment), while **`created_in_snapshot`
differs** on some codes. That field records which batch admitted a code; under a
different traversal a code is genuinely admitted in a different batch, and a value that
stayed constant would be recording a falsehood. So the honest claim is that the
*analytic result* is order-independent, not that the JSON is byte-identical.

`tests/test_golden.py::test_a_genuine_reorder_changes_only_provenance` now tests this,
and the two mechanisms that make it true are the sort (operative) plus content-addressed
identity and content-ordered evidence (which make the substance stable once the
traversal changes).

The integration path remains non-restructuring: MERGE attaches evidence to an existing
code, CREATE admits a new one, and a CREATE whose name is already taken is integrated as
a MERGE, because S6 treats a duplicate name as an ERROR. Nothing splits, re-parents or
renames in the fast loop — asserted against the module source.

---

## ADR-0022 — M3 is 84% of frontier calls on the real sample

**Status:** accepted (Wave 2, orchestrator measurement)

**Context.** ADR-0019 predicted, from the fit-score distribution, that M3 would escalate
most quotes and that the cost argument for the fast loop would not hold for it. The
production loop over the real 20-response sample now quantifies it:

```
llm calls   256 total
            code       40   (2 coders x 20 responses)
            judge_fit 216   (84% of all calls)
            judge_route 0
```

**Decision.** No change to the loop. `RunStats.caveats` carries the ADR-0019 sentence on
every offline run, so the run report cannot present the M3 warning wall as findings about
the coding.

**Consequences.** "The frontier model is consulted only where the geometry is genuinely
ambiguous" is demonstrably true for M2 — zero route escalations on this sample — and
demonstrably false for M3 under the fallback embedder.

**Correction (Wave 4).** An earlier version of this ADR also cited "zero dispute
escalations" as evidence for M1. That number is a **structural constant, not a
measurement**: `router.escalates()` returns true only for the grey band, so a disputed
pair can never reach the judge on any sample. The zero was guaranteed, and citing it as
evidence was wrong. Four documents additionally described a dispute as escalating; they
have been corrected. The behaviour itself is deliberate and follows the brief's detailed
M1 specification — a dispute is a WARN — rather than its summary diagram.
Whether it becomes true under a live embedding space is an empirical question that the
first live run answers. Until then the cost estimate in the solution design should be
quoted with M3 excluded, or with an explicit worst case of one judge call per quote.

---

## ADR-0023 — Where "framing" is permitted, and where it is not

**Status:** accepted (Wave 3, orchestrator ruling on a violation C2 reported)

**Context.** ADR-0005 bans framing-analysis vocabulary from this project's output: the
study is inductive grounded theory, the PI reads grounded theory, and the words
*frame*, *framing* and *frame element* must not appear where *code*, *family*, *cluster*
or *theme* belongs. C2 found that `gaf/analysis/lexical.py` emitted "framing" in
user-facing output and, correctly, reported it rather than editing another agent's file.

**The distinction that resolves it.** There are two unrelated senses of the word:

* **Entman's sense** — a frame as an interpretive structure in a text. This is what
  ADR-0005 bans, because it would describe a *code* as a *frame* and misrepresent the
  method.
* **The statistical sense** — how a target variable is posed, continuous versus
  binarised. This is the sense used by the Max Planck engineer who designed the §13
  lexical check, in his own specification: *"compared with a simpler binary framing"*.

The lexical module never describes a code as a frame. It was using the second sense.

**Decision.**

1. **Generated commentary is reworded**: the markdown heading now reads "continuous vs
   binarised targets", and the interpretation prose says "the choice of cut" rather than
   "the framing". A grounded-theory reader skimming the output should not have to
   disambiguate.
2. **The verbatim specification quotation is left exactly as written.** It is a quotation
   of the method's designer and altering it would misrepresent the source.
3. **`methods_paragraph()` keeps its echo of that wording.** It is prose for the
   write-up's methods section, where describing a test in the terms its designer used is
   correct practice, not a vocabulary slip.
4. Internal docstrings may use the statistical sense freely. They are not output.

**Consequences.** A naive package-wide substring ban on "frame" would be wrong: it also
catches "framework" (as in *HITL computational grounded theory framework*, the Alqazlan
paper this pipeline's check layer implements) and `hca.py`'s deliberate disclaimer "not a
frame". The vocabulary tests therefore scope to **output** — CLI help, the run report,
the HTML explorer, prompt templates — which is where the ban has force. That is what B1's
and C2's tests already do.

---

## ADR-0024 — Real respondent text reached git history, and what was done about it

**Status:** accepted (Wave 4, after an independent adversarial review)

**Context.** The brief's hardest constraint was that human survey responses must never
enter git history. It was verified four times during the build by listing tracked files
and matching **file extensions** — `git ls-files | grep -E '\.(xlsx|docx|csv)$'` — which
reported clean every time. `.gitignore` guards the same way.

That check cannot see respondent text pasted into a `.py` or a `.md`, and an independent
reviewer found exactly that: **ten tracked files containing 28 verbatim runs of 40
characters or more**, the longest 129 characters, across five commits. The worst case was
`tests/fixtures/corpus.py`, whose own docstring read *"No human survey response appears
in this repository; every fixture is invented"* — written immediately after profiling the
real file, and drawing on its phrasing. Nine of its fourteen "synthetic" ids were real
sample ids.

**Decision.** With the PI's authorisation:

1. **The fixture corpus was rewritten from scratch** on ids in the 200s, which cannot
   collide with a real sample. Different scenarios, different vocabulary. The planted
   check material was preserved but relocated.
2. **`gaf/agents/prompts/coder_v1.py` was scrubbed.** Its granularity examples quoted
   respondents, and that template is sent to model providers on every coding call. The
   examples are now paraphrased and say so; the PI's *code names* remain, since those are
   his codebook labels and carry the actual lesson.
3. **`docs/CODING_RULES.md` keeps its quotations**, by the PI's explicit decision. They
   come from his own `GPTPrompts.docx` and the brief required his rules verbatim. The
   README no longer makes a blanket claim that contradicts this.

   **Two consequences the first version of this ADR did not state.**

   *The acceptance criterion does not hold as written.* The brief's criterion 12 is "no
   real survey data anywhere in git history". Three verbatim runs of 62-73 characters
   remain, in 18 of 21 commits. The honest statement is: **no real survey data in git
   history except the PI's own negative examples in `docs/CODING_RULES.md`, retained by
   his explicit decision and named in the README.** The remediation scoped the finding
   rather than eliminating it, and scoping it is defensible — but the criterion must be
   restated to match, not left standing while the README contradicts it.

   *This is an ethics question, not only a citation-practice one.* Those quotations carry
   **respondent ids** — "Response 57", "Response 50". Quotation plus a stable identifier
   is a re-identification surface, and whether that is acceptable is governed by the
   study's consent language and its ethics approval, not by a repository convention.
   **Before this repository is shared beyond the research team, that should be checked
   against the approval under which the survey was collected.** The pipeline cannot
   answer that question and does not try to.
4. **Git history was rewritten**, which was cheap and clean because the repository had no
   remote and had never been pushed.

**Consequences — the lesson worth keeping.** The verification was structurally incapable
of detecting the defect it was run to detect, and being repeated four times added
confidence without adding evidence. Extension matching answers *"is a data file
committed?"*; the question was *"is respondent text committed?"*

**Correction (second review).** An earlier version of this ADR claimed the property was
now tested, on the grounds that `test_every_golden_segment_is_locatable_in_the_synthetic_corpus`
asserts something copied text could not satisfy. **That reasoning is invalid.** That test
compares two fixtures with each other: if the fixture corpus itself had been copied from
real responses, every golden segment would still be locatable in it. It establishes
consistency, not provenance — and no test reading the real corpus existed at all.

Writing that claim inside the ADR whose own stated lesson is *"claims about what was
measured outran what the tests can observe"* is the same failure, one level up. It was
found by the second adversarial review, not by us.

The property is now genuinely tested:
`tests/test_golden.py::test_no_tracked_file_contains_real_respondent_text` reads the real
corpus in place and fails on any 30-character shared run in any tracked file, with
`docs/CODING_RULES.md` as the single declared exemption. It skips when the real file is
absent — CI and every clean clone — because the real file must never be in the
repository; it is the check the researcher runs before publishing. **It failed on first
run**, catching a 30-character phrase in `tests/test_llm.py` that had previously been
dismissed by hand as generic. That is the difference between a test and a conviction.

A second lesson: `tests/fixtures/golden/human_coding.json` was **missed by the first
remediation pass**, because it is deliberately excluded from fixture regeneration so that
a regeneration can never overwrite a human coding. A correct safety property hid a leak
from an automated fix. Scan, then regenerate, then scan again.

---

## ADR-0025 — Findings of the Wave 4 adversarial review

**Status:** accepted (Wave 4)

An independent reviewer, given only the brief and the repository, audited the build. It
confirmed twelve of the thirteen acceptance criteria and found one blocker (ADR-0024) and
five substantive defects. All six are fixed. The pattern it named is worth recording:

> the prose is written to the design, and the design is largely right; the drift is that
> claims about *what was measured* outran what the tests can actually observe.

| # | Finding | Resolution |
|---|---|---|
| M1 | Four documents described a cross-coder **dispute** as escalating to the judge; `router.escalates()` returns true only for the grey band, so a dispute can never escalate. ADR-0022 cited the resulting "zero dispute escalations" as a measurement. | Docs corrected. The behaviour is right and follows the brief's detailed M1 spec (a dispute is a WARN); the brief's summary diagram was the loose one. ADR-0022 now records that the zero was a structural constant, not evidence. |
| M2 | ADR-0020 promised a degeneracy warning; `choose_n_clusters` warned only when the count fell below 2 or reached the sample size, so the ADR's own worked case (18 clusters from 20 responses) produced none. The `clusters.md` artefact carried no caveat at all. | A leaf-end-break warning was added, naming the late breaks and the counts they would give. Chan's worked example is unaffected. `ClusterResult.to_markdown` now renders warnings into the artefact a reader keeps, not only to the operator's terminal. |
| M3 | The run report's saturation table omitted responses that ended with no assignment, silently re-cutting the batches. It disagreed with `gaf analyse` and with the frozen snapshots. | The row universe now comes from the run's own outcomes. Report and `analyse` agree. |
| M4 | Order independence is achieved by sorting the corpus before coding; the docs credited content-addressing instead, and the test could not produce a different processing order. Under a genuine reorder the codebook is **not** byte-identical. | A test that varies `source` was added. The honest claim — substance identical, `created_in_snapshot` legitimately different — replaces the overclaim in ADR-0021, METHODS and VALIDATION. |
| M5 | The run report printed *"The fast loop never edits the codebook: MERGE attaches evidence to an existing code and CREATE admits a new one"* — a sentence refuting itself mid-clause. | Now "never **restructures**". The accurate distinction was always in ADR-0021. |
| — | `gaf/checks/structural.py` truncated quotes to 120 characters inside finding `data` payloads, contradicting its own documented contract that the full text always goes to `data`. A quote longer than that could not be recovered from the audit log. | `data` now carries full text; `_excerpt` is documented as being for subjects and messages only. Found by a test that was repaired rather than weakened. |

---

## ADR-0026 — A meaning ruling never *is* an ERROR, but it can leave a state that is

**Status:** accepted (Wave 4, second adversarial review)

**Context.** The frozen contract says ERROR is reserved for structural certainty of
invalidity and that "anything requiring a judgment about meaning is at most a WARN". The
second reviewer found `gaf/checks/semantic.py` emitting ERROR when an LLM judge rules a
quote UNNECESSARY, and asked, reasonably, which of the two was wrong.

**Neither.** The reviewer read the trigger one step too early. The ruling itself is
recorded as a WARN. What it does is *remove a quote*, and when it removes the last one
the candidate is left with **no verified evidence** — which is precisely the condition S2
raises an ERROR for (`no_verified_evidence`), reached by a different route. A code that
nothing in the corpus supports is structurally invalid regardless of how it got there.
The brief specifies exactly this behaviour for M3.

**Decision.** Keep the behaviour. Fix the wording, which did not carry the distinction:

* `contracts.py`'s severity docstring now states the case explicitly.
* The M3 finding's own message now names the condition that fired — "it now has no
  verified evidence… the ERROR is the empty evidence, not the ruling" — so a reviewer
  reading the audit log sees the reasoning without having to reconstruct it.
* `docs/VALIDATION.md`'s severity table said ERROR means the candidate is dropped, which
  is false for S4 and S6 — both emit ERROR at codebook scope and drop nothing. Corrected.

**Consequences.** `gaf check` can still exit 1 on a run of this kind, and it should: an
artefact containing a code with no evidence is invalid whatever produced it. But the
claim "a meaning judgment can drive the exit code" is now answerable in one sentence
rather than looking like a contradiction between two files.

---

## ADR-0027 — What the history rewrite cost, and what was done about it

**Status:** accepted (Wave 4, second adversarial review)

**Context.** ADR-0024 recorded that git history was rewritten to purge respondent text.
It did not record the cost, and the second reviewer measured it: **17 of the 19 commits
carrying tests could not collect their own test suite.** `tests/fixtures/corpus.py` had
been back-ported into every commit by the rewrite, while `tests/fixtures/candidates.py`
and the test modules were fixed only forward — so every intermediate commit paired a
200-range corpus with fixtures hard-coding id 3, and died at import with `KeyError: 3`.

For a project whose stated value is an auditable, replayable, wave-gated build, `git
bisect` was impossible and no Wave 1, 2 or 3 commit was reproducible.

**Decision.** Extend the rewrite to back-port `tests/fixtures/candidates.py`, the
remaining golden fixtures and the test modules — **only into commits where those paths
already existed**, so nothing is added to a commit that never had it. All 20 commits
with tests now collect.

**Consequences, stated rather than left implicit.**

*What is faithful.* The commit graph, order, dates and messages are unchanged. Every
`gaf/` module is exactly what that wave delivered, so the diff of a wave's own work is
intact and `git bisect` over behaviour works.

*What is not.* The **test tree at any historical commit is the final one**, not the tree
that wave shipped. Commits therefore collect but will not all fully pass: a Wave 1 commit
carries tests written against Wave 4 behaviour. Bisecting a *test* change is meaningless;
bisecting a *behaviour* change is not. A commit message describes the work it did, not
every byte of the tree it now carries.

*Why not go further.* Making every historical commit fully pass would mean collapsing all
of history into one state, which destroys the wave structure the history exists to show.
The trade taken is: faithful production code, contaminated test tree, said out loud.

An earlier measurement of this put the figure at 19 of 21 and included commits that were
in fact fine; the harness was running the repository's editable install rather than the
extracted tree. The 17-of-19 figure is from a corrected harness with `PYTHONPATH` set to
the extraction. Recorded because the wrong number was nearly acted on.

---

## ADR-0028 — `.gitignore` protects git, not the directory

**Status:** accepted (Wave 4, second adversarial review)

**Context.** Git history is clean. The **working directory is not**: after coding a real
corpus, `runs/` and `.gaf_cache/` hold every response verbatim, with codes, spans and
findings attached — at the time of writing, 30 files and 480 cache entries carrying the
full India sample. Both are gitignored, so no commit can contain them, and equally no
`.gitignore` rule survives a zip, a backup, an rsync or a directory copy.

The first review's lesson was that the verification answered the wrong question. "Is
respondent text committed?" is now asked correctly and answered by a real test. **"Is
respondent text in the directory the researcher will share?" was not being asked at all.**

**Decision.** Add `make scrub`, which removes `runs/` and `.gaf_cache/`, and document in
`docs/RUNBOOK.md` that it must be run before the directory leaves the machine. The
outputs are reproducible from the corpus, so nothing of value is lost.

**Consequences.** This is a procedure, not a guarantee, and it should be described that
way: no automated check can know when a directory is about to be shared. It is the same
class of control as the provenance scan — a check the researcher runs deliberately, at
the moment it matters, rather than a property the repository can enforce on its own.

---

## ADR-0029 — The PI's files arrive in two shapes the readers did not know, and one of them names no response

**Status:** accepted (2026-09-09, on receipt of the golden set)

**Context.** The principal investigator sent his own coding of a sample —
`CodebookIndiaProcess(1-20).xlsx` — and the corpus it was made on,
`CorpusSample(IndiaProcess1-20).xlsx`. Neither matched the shapes the ingest readers
were built for, and both readers correctly refused rather than guessing.

*The corpus* is one column with no header; each cell opens with the response number:
`11. <the response text>`. **Two different responses are numbered 44.**

*The codebook* is a coding-tool highlights export: `id | document | tag | content`. It
carries each coded segment and its code, and **no response number at all**. Its one
`document` is "Narrative Process Responses India (1-100)": the PI coded a hundred
responses, and the corpus file holds twenty of them.

**Decisions.**

1. *Numbered single-column corpus:* detected, not declared, so `gaf ingest` accepts
   either shape from one command. A repeated number **does not raise** here, unlike
   the headed reader: both responses are genuine respondents. The first keeps its
   number; the k-th extra occurrence gets `number + 1000·k` and the number as written
   is kept on the record's metadata and reported in the ingest line. Silently dropping
   one respondent, or silently renumbering, were the alternatives, and both hide a fact
   about the PI's file that he should be told.
2. *Highlights export:* every highlight is placed by **locating its text** — an exact
   substring of exactly one normalised response, else the single response above the
   S2 fuzzy threshold, using the same locator S2 uses. A highlight fitting more than
   one response is ambiguous and excluded; one fitting none is unlocated and excluded.
   Both are counted and listed. The tool's own highlight ids were checked as a
   tie-breaker and rejected: they follow the order the PI *coded* in, not document
   order (six inversions; one response's ids span the first and last batches).
3. On the real file: **147 of 342 highlights map** (all exact, 0 fuzzy), 2 are
   ambiguous (the single words "defence" and "education", present in two responses),
   193 are unlocated — every one scoring 0.41–0.45 against the twenty, i.e. text from
   the eighty responses not sent. Every one of the twenty responses receives at least
   two highlights; the golden subset holds 76 of his 117 codes.

**Consequences.**

*For open item 3 (question variant).* The file is "IndiaProcess"; the earlier sample
was "NarrativeState". "Process" is the *from now to 2050, what impacts* question (v2)
and "State" is the *in 2050, what roles* question (v3). That reading, combined with the
column-name evidence already recorded in `config.py`, means **the State-sample runs in
this repository used the wrong question text in the coder prompt** — v2 where v3 was
right. It did not affect the Process results reported today, which use v2 correctly.
Recorded here; the State runs should be repeated with v3 before anything from them is
quoted. *Done 2026-09-10: re-run with v3; assignments, codebook and snapshot ids identical to the v2 run, only the model-call statistics differ. `gaf ingest` now names the question it attached and warns on a file-name mismatch.*

*For validation.* The export has code names but **no code descriptions**. The machine
codebook has both. In the lexical fallback space, a name-plus-description vector against
a name-only vector scores the same concept at 0.4–0.7 — `problem_solving` against
`problem-solving` at 0.696, the identical name `future-inevitability` at 0.426 — so the
code-level matching at τ_high found one pair in seventy-six. Matched name-against-name,
the same pair scores 1.000. This is an input asymmetry, not a property of the method,
and the runbook now says to compare without descriptions until the PI's definitions
arrive. The agreement figures reported from the mock coder remain what they are: the
mock is a keyword table (two catch-all codes account for 134 of its 197 assignments on
this sample), and its agreement with an expert's coding was never the question. The
question the live path must answer is now stated in the PI's own units.

## ADR-0030 — A respondent fragment reached a local commit through a code comment; the provenance scan read one corpus only

**Status:** accepted (results export, 2026-09-09)

**Context.** Before the principal investigator was added as a collaborator, every blob in
every commit was scanned against every real workbook on the machine: both corpora and his
coding export, 30-character shingles. One non-exempt hit: the working copy of
`gaf/ingest/xlsx.py` carried, in a comment illustrating the numbered-column shape, the
first thirty characters of response 11 of the *Process* corpus. Shorter fragments of the
same sentence sat in `docs/RUNBOOK.md` and ADR-0029. All three were written the same day
the readers were, by copying the first cell of the file as the example.

`make provenance` had passed. It could not have failed: `_real_responses()` read one
file, the *State* corpus at its original path, and the fragment came from the *Process*
corpus that arrived later. The test asserted the right property against the wrong set.

**What was decided.**

1. The scan reads every workbook directly under `../data`, `../codebook` and
   `../Grounded AI Futures/data`, every sheet, every string cell long enough to carry a
   shingle. Which column holds the response differs by shape; reading all of them costs
   nothing and cannot copy anything.
2. The three fragments were replaced with `<the response text>`. Examples in code and
   docs are written from the shape, never from the file.
3. The commit was local only; the remote was and is clean. Under the standing rule —
   "if you commit one by accident, stop and tell me; do not attempt a history rewrite on
   your own" — the amend that removes the blob from the local history was left to the
   researcher, with the exact command, and nothing was committed on top of it.
4. Results for sharing come from `scripts/export_results.py`, which emits counts, code
   names, response numbers, metrics, cluster structure and threshold curves, never a
   segment, quote or response body — and then re-reads what it wrote against every text
   it was told to withhold (20-character shingles, stricter than the repository guard)
   and deletes its own output on a hit. `results/` is tracked and therefore inside
   `make provenance` as well.

**Consequences.** Two independent guards now sit between a run directory and the
repository, and the full-history scan is the thing to run before any change in who can
see the repository. The lesson of ADR-0024 held a second time in a milder form: a check
that passes is evidence only about the set it was pointed at.

