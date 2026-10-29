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
| [ADR-0031](#adr-0031--placing-highlights-on-200-responses-the-coded-set-breaks-a-tie-file-order-does-not) | Placing highlights on 200 responses: the coded set breaks a tie, file order does not | accepted (Wave C, T1 — new input shapes) |
| [ADR-0032](#adr-0032--the-pis-code-descriptions-are-model-drafted-from-his-own-prompt-imported-as-given-and-they-close-adr-0029s-description-asymmetry-on-one-side-only) | The PI's code descriptions are model-drafted from his own prompt, imported as given, and they close ADR-0029's description asymmetry on one side only | accepted (Wave C, T1 — new input shapes) |
| [ADR-0033](#adr-0033--a-ratio-spike-rule-beside-the-absolute-ceiling-the-handover-is-evaluated-every-batch-and-stated-as-data) | A ratio spike rule beside the absolute ceiling; the handover is evaluated every batch and stated as data | accepted (Wave C, T2 — growth, spike, decision matrix) |
| [ADR-0034](#adr-0034--the-definer-a-fourth-llm-role-outside-both-loops) | The Definer: a fourth LLM role, outside both loops | accepted (Wave C, T5 — Definer, `gaf codebook`) |
| [ADR-0035](#adr-0035--a-seeded-run-holds-the-seeds-evidence-out-and-says-what-it-costs) | A seeded run holds the seed's evidence out, and says what it costs | accepted (Wave C, T5 — seeded runs, the handover flags) |
| [ADR-0036](#adr-0036--pattern-mapping-and-affinity-are-views-affinity-clusters-leaves-across-families-both-blends-are-uncalibrated-constants-no-respondent-text-in-any-of-the-three) | Pattern mapping and affinity are views; affinity clusters leaves across families; both blends are uncalibrated constants; no respondent text in any of the three | accepted (Wave C, T3 — patterns, affinity, crosswalk) |
| [ADR-0037](#adr-0037--viewshtml-is-the-shareable-page-and-codebookhtml-is-not-how-the-palette-was-derived) | `views.html` is the shareable page and `codebook.html` is not; how the palette was derived | accepted (Wave C, T6/T8 — `views.html`) |
| [ADR-0038](#adr-0038--the-provenance-guard-met-a-coincidence-and-the-pis-own-definitions-are-not-blanket-shareable) | The provenance guard met a coincidence, and the PI's own definitions are not blanket-shareable | accepted (Wave C, T8 — from the wave's own notes) |
| [ADR-0039](#adr-0039--the-reorganisation-trail-carries-structure-not-payloads) | The reorganisation trail carries structure, not payloads | accepted (fix pass F1, from the R1 correctness audit; extended by F2 to the rationale, from R2 C-1) |
| [ADR-0040](#adr-0040--the-hard-floor-counts-from-the-last-checkpoint-and-the-spike-rule-stands-aside-where-it-has-no-baseline) | The hard floor counts from the last checkpoint, and the spike rule stands aside where it has no baseline | accepted (fix pass F1; amends ADR-0033) |
| [ADR-0041](#adr-0041--gaf-analyse-needs-the-run-to-cut-the-runs-curve-and-patterns-read-the-unfiltered-matrix) | `gaf analyse` needs the run to cut the run's curve, and patterns read the unfiltered matrix | accepted (fix pass F1, from the R1 correctness audit) |
| [ADR-0042](#adr-0042--the-definer-a-verbatim-segment-is-a-quote-at-any-length-and-the-prompt-registry-is-one-place) | The Definer: a verbatim segment is a quote at any length, and the prompt registry is one place | accepted (fix pass F1; amends ADR-0013 for the Definer and ADR-0034) |
| [ADR-0043](#adr-0043--a-checkpoint-id-carries-an-ordinal-where-a-checkpoint-can-legitimately-repeat) | A checkpoint id carries an ordinal where a checkpoint can legitimately repeat | accepted (fix pass F1; the same rule as ADR-0018) |
| [ADR-0044](#adr-0044--the-crosswalk-states-description-coverage-and-the-target-roll-up-has-its-own-shape) | The crosswalk states description coverage, and the target roll-up has its own shape | accepted (fix pass F1, from the R1 correctness audit) |
| [ADR-0045](#adr-0045--triple-candidates-are-ranked-by-their-exact-support-bound-before-the-cap-cuts-them) | Triple candidates are ranked by their exact support bound before the cap cuts them | accepted (fix pass F1, from the R1 correctness audit) |
| [ADR-0046](#adr-0046--a-family-tagged-both-ways-keeps-its-own-segments-and-a-description-never-travels-without-its-source) | A family tagged both ways keeps its own segments, and a description never travels without its source | accepted (fix pass F1; ADR-0032 made structural) |
| [ADR-0047](#adr-0047--the-provenance-guard-scans-at-the-exporters-twenty-characters-keeps-short-cells-subtracts-the-instrument-and-counts-respondents) | The provenance guard scans at the exporter's twenty characters, keeps short cells, subtracts the instrument and counts respondents | accepted (fix pass F2, from the R2 privacy audit) |
| [ADR-0048](#adr-0048--the-default-live-registry-names-models-that-exist-at-prices-read-on-a-stated-date) | The default live registry names models that exist, at prices read on a stated date | accepted (PI feedback pass; amends `gaf/config.py`, the ADR-0015 precedent) |
| [ADR-0049](#adr-0049--models-served-on-this-machine-are-a-provider-and-local-means-the-words-stay-here) | Models served on this machine are a provider, and "local" means the words stay here | proposed (local-models branch; amends `gaf/config.py` additively) |

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

**Status:** accepted (Wave 0). Applies to **S1**, in the fast loop, as written;
[ADR-0042](#adr-0042--the-definer-a-verbatim-segment-is-a-quote-at-any-length-and-the-prompt-registry-is-one-place)
rules the other way for the Definer's D3, where refusing destroys no evidence.

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

**Context.** Response 57 of the real seed sample contains a short quoted sentence whose
curly quotation marks arrive mis-decoded: UTF-8 curly quotes decoded once as a legacy
codepage. `“` is UTF-8 `E2 80 9C`, which read as MacRoman renders the three-character
sequence `‚Äú`; `”` is `E2 80 9D` and renders `‚Äù`. The cell therefore reads
`‚Äú<sentence>‚Äù` — six mis-decoded characters wrapped around the respondent's own
words, which this entry does not need and does not reproduce. Responses 9 and 10
contain a genuine `…` and a stray `‚` that must not be touched.

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
appeared under concurrency, and that is the worst kind to debug.

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

---

## ADR-0031 — Placing highlights on 200 responses: the coded set breaks a tie, file order does not

**Status:** accepted (Wave C, T1 — new input shapes)

**Context.** ADR-0029 §2 settled how a coding-tool export with no response number is
placed: locate its text, accept an exact substring of exactly one normalised response
or the single response above the S2 fuzzy threshold, and exclude anything that fits
more than one response (ambiguous) or none (unlocated). On twenty responses that rule
cost almost nothing — two highlights were ambiguous, both single words.

The corpus is now two hundred responses, and the same rule costs a great deal more.
**Thirty of the principal investigator's 342 highlights sit verbatim in more than one
of the two hundred responses.** These are not fabrications and not single words: they
are ordinary phrases about a shared subject, and the number of them grows with the
corpus, not with the coding. Under ADR-0029 §2 alone, every one of them is excluded.

Equally, the corpus tells us something ADR-0029 could not use. The PI coded
"Narrative Process Responses India (1-100)"; the 200-response file holds a superset of
those, and the coding demonstrably touches only part of it. After a first placement
pass, **39 of the 200 responses hold at least one exact or fuzzy highlight**. A
highlight whose text fits five responses, of which exactly one is in that set of 39, is
not really ambiguous: the other four are responses this coding never looked at.

Three options were on the table.

1. Leave the rule as it is and exclude all thirty. Defensible, and it throws away
   evidence for a reason that has nothing to do with the coding.
2. **Tie-break on file order or on the export's own highlight ids.** Rejected, and
   rejected once already: ADR-0029 §2 measured those ids and found they follow the
   order the PI *coded* in, not document order — six inversions, with one response's
   ids spanning the first and last batches. An id that does not track document order
   cannot break a document-order tie, and file order in the corpus is not evidence
   about which response a segment came from.
3. Use the coded set.

**Decision.** **Two passes, and the second is the only new rule.**

Pass one is ADR-0029 §2 unchanged. After it, the **coded set** is every response
holding at least one `exact` or `fuzzy` highlight. In pass two, an ambiguous highlight
with **exactly one** candidate in the coded set is placed there with the outcome
`resolved`. Everything else stays `ambiguous` and is excluded, as is everything
`unlocated`.

Three properties make this checkable rather than merely plausible.

* The coded set is computed from the **whole** of pass one, so the outcome does not
  depend on the order the rows arrive in. Re-running over a shuffled export gives the
  same answer.
* `resolved` is counted **apart from** `exact` and `fuzzy` and is named in
  `HighlightsReport.summary()`, because it rests on a different kind of evidence — the
  coverage of the coding rather than the text of the response — and a reader must be
  able to discount it separately.
* A resolved highlight still has to yield a span under the S2 locator. One that cannot
  (the candidates came from the fuzzy branch, so the text is not a substring of the
  response) stays ambiguous, which keeps `mapped` and the evidence in the codebook in
  exact agreement.

The rule is implemented once, in `gaf.ingest.xlsx.place_highlights`, which the
four-column workbook reader (`read_highlights_xlsx`) and the two-column CSV/XLSX
pairing reader (`gaf.ingest.tagged.read_tagged_pairs`) both go through, so the
workbook path and the CSV path cannot drift apart.

**Measured on the real files** (counts only; no respondent text appears in this
repository, and this measurement was independently reproduced while writing this entry
— `gaf codebook organise` on the same three files gives the same seven numbers):

| | count |
|---|---|
| highlights in the export | 342 |
| exact | 304 |
| fuzzy | 1 |
| **resolved** (the new rule) | **7** |
| ambiguous, excluded | 24 |
| unlocated, excluded | 6 |
| mapped (exact + fuzzy + resolved) | 312 |
| responses in the coded set | 39 |
| highlights sitting verbatim in more than one response | 30 |

The 24 that remain ambiguous have between 2 and 26 candidates each, and more than one
candidate inside the coded set in every case — the rule declines them rather than
guessing. The 6 unlocated belong to responses the 200-response file does not contain,
which is the same finding ADR-0029 §3 recorded at the smaller scale.

**Consequences.**

*What this buys.* Seven highlights and their codes re-enter the evidence base with a
stated, reproducible reason, and the reason is visible in the artefact rather than
folded into the `exact` count.

*What it costs.* `resolved` is a weaker claim than `exact`. It asserts that a segment
belongs to the one candidate response this coding covers, which is an inference from
the coding's coverage, not from the text. If the PI later sends a coding of responses
the current set does not cover, the coded set changes and so do these seven
placements — the count is a property of *this* pairing of coding and corpus, and
should be re-read as such rather than cited as a fixed number.

*What it does not change.* Ambiguity is still excluded by default, the S2 locator is
still the only thing that produces a span, and nothing here consults the export's own
ids. The rejected alternative stays rejected for the reason ADR-0029 measured.

---

## ADR-0032 — The PI's code descriptions are model-drafted from his own prompt, imported as given, and they close ADR-0029's description asymmetry on one side only

**Status:** accepted (Wave C, T1 — new input shapes)

**Context.** ADR-0029 recorded an input asymmetry that has blocked code-level
comparison since the golden set arrived. The principal investigator's coding export
carries code **names** and no descriptions; the machine codebook carries both. In the
lexical fallback space a name-plus-description vector against a name-only vector scores
the same concept at 0.4–0.7 — `problem_solving` against `problem-solving` at 0.696, the
*identical* name `future-inevitability` at 0.426 — so code-level matching at τ_high
found one pair in seventy-six. Matched name-against-name, that same pair scores 1.000.
The runbook has since said to compare without descriptions "until the PI's definitions
arrive".

They have arrived, as `codebook/AI_Perceptions_Codebook1.md`. Section `## 3.
Descriptions` holds a one-to-three-sentence definition for every code and subcode: 15
top-level codes and 116 subcodes, 131 definitions in all.

**They were not written by hand.** They were drafted by a language model, from the PI's
own prompt (`codebook/inductive-codebook-prompt2.md`), over the same 342 code-text
pairings this repository now reads. The prompt instructs the model to ground every
definition "only in the text segments actually associated with that code/subcode" and
not to speculate beyond the data, and the PI reviewed the result — but the sentences
are a model's, not his.

That leaves a choice about what to do with them.

**Decision.**

1. **Import them as given.** `gaf.ingest.definitions.read_definitions_md` reads section
   3 and nothing else, keyed by the pipeline's own name form (`parent-sub`, or `parent`
   for a parent or a top-level leaf). No rewriting, no truncation, no normalisation of
   the prose. A definition the PI is willing to stand behind is the definition of
   record; editing it here would make the artefact disagree with the document he holds.
2. **Record where they came from, on every code that receives one.**
   `attach_definitions` sets `meta["description_source"] = "pi-codebook-md"`. A reader
   of any downstream artefact can therefore tell a human-authored description from a
   model-drafted, human-reviewed one, which is precisely the distinction a methods
   appendix has to be able to make.
3. **Match names exactly, or through the same trivial consolidation as the pairings,
   and never otherwise.** `attach_definitions` does no fuzzy matching. It reports three
   things instead: codes defined but never tagged, codes tagged but never defined, and
   names that met only because `gaf.ingest.tagged` had already rewritten a trivial
   variant. A misspelt code stays undefined and is reported as such, because deciding
   that two nearly-identical names mean one thing is a judgment about meaning, and the
   ingest layer does not make those.
4. **Descriptions are respondent-derived output.** They are grounded in segments and
   may echo their phrasing. A codebook carrying them therefore belongs under `runs/`
   like every other artefact that touches the corpus, and is covered by `make scrub`
   and by the provenance scan.

**Measured on the real files** (counts only; independently reproduced while writing
this entry):

| | count |
|---|---|
| definitions read from section 3 | 131 |
| top-level codes defined | 15 (one of them a leaf) |
| lines in section 3 the reader could not parse | 0 |
| matched against the tagged codebook | 131 |
| defined but never tagged | 0 |
| tagged but never defined | 0 |
| matched only after trivial consolidation | 1 (`key-sectors-…` onto `key_sectors-…`) |

The correspondence is exact in both directions, which is itself evidence that the
descriptions were generated from these pairings and not from an earlier version of them.

**Consequences.**

*For ADR-0029's asymmetry.* It is closed **on the human side**: the PI's codes now
carry descriptions, so name-plus-description can be compared against
name-plus-description and the runbook's "compare without descriptions" caveat can be
retired for this sample. The asymmetry is *not* closed in the sense of being
eliminated: one side's descriptions were drafted by a model from the coded segments,
the other side's by the coder models during coding. That is a comparison of two
model-written glosses over the same corpus, and it should be reported as one. It
measures whether the two codings *mean* the same thing far better than names alone
did; it does not measure agreement between a human's definition and a machine's,
because no human definition exists for this codebook.

*For the agreement figures.* Any code-level match computed with these descriptions
attached must state that they are model-drafted, or it will be read as a stronger
claim than it is. A run that wants the weaker but cleaner claim can still compare
name-against-name; `meta["description_source"]` is what makes the two runs
distinguishable after the fact.

*A wrinkle worth naming.* ADR-0005 and ADR-0023 keep the words "frame" and "framing"
out of this project's output, because the study is inductive grounded theory and not
framing analysis. Some of the PI's imported descriptions use "framing" in its ordinary
English sense. They are **imported as given** under decision 1 and are not rewritten:
they are his data, not this project's vocabulary. Anything this repository *writes*
about them stays in grounded theory's vocabulary, and a vocabulary check over
generated output should exempt an imported description (`description_source ==
"pi-codebook-md"`) rather than fail on it or silently edit the PI's document.

---

## ADR-0033 — A ratio spike rule beside the absolute ceiling; the handover is evaluated every batch and stated as data

**Status:** accepted (Wave C, T2 — growth, spike, decision matrix), amended by
[ADR-0040](#adr-0040--the-hard-floor-counts-from-the-last-checkpoint-and-the-spike-rule-stands-aside-where-it-has-no-baseline),
which moved the hard floor onto `responses_since_checkpoint` and stopped the spike rule
falling back to the absolute ceiling where it has no baseline. The rest of this entry
stands as written.

**Context.** Two of the principal investigator's notes on the September review point at
the same gap. He asked for a **decision matrix** between the fast loop and the slow
loop, and he reported that the **number of codes spiked** as coding went on.

The build already had both loops and a trigger (`gaf.pipeline.slow_loop.should_checkpoint`,
`gaf.checks.health.checkpoint_signals`), but three things were missing.

1. **Nothing watched growth across batches.** `CheckpointPolicy.max_new_codes_per_batch`
   is an absolute ceiling, and an absolute ceiling cannot tell a *first* batch, where
   every code is new and eight of them is expected, from a *late* batch where eight new
   codes means the codebook has stopped converging and started accreting parallel
   concepts — which is the flattening failure of the predecessor study (ADR-0003,
   Ng & Chan 2026) arriving one batch at a time.
2. **The trigger was evaluated once, after the last response.** `run_fast_loop` computed
   `checkpoint_due` at the end of the run, against a health row taken with no `previous`
   codebook (so every code read as new) and with `responses_since_checkpoint` set to the
   whole run. A run that came due at batch 2 and had quietened by batch 7 was
   indistinguishable from one that never came due.
3. **No artefact stated which decision is taken where.** The architecture document
   describes the two loops in prose. Prose answers the question once and then rots,
   because nothing makes it false when the code changes.

**Decisions.**

1. **Three additive fields on the frozen `CheckpointPolicy`** (`gaf/config.py`):
   `spike_factor: float = 2.0`, `spike_window: int = 3`, `spike_min_new_codes: int = 4`.
   All three carry defaults, so every existing `RunConfig`, every stored config echo and
   every golden fixture is untouched. This is the third amendment to `config.py`, after
   ADR-0015.

2. **A ratio rule sits beside the absolute one; it does not replace it.**
   `gaf.checks.growth.detect_spikes` calls a batch a spike when it admitted at least
   `spike_min_new_codes` codes **and** at least `spike_factor` times the median
   new-code count of the previous `spike_window` batches. The first `spike_window`
   batches have no baseline — a ratio against nothing is not a measurement — and fall
   back to the absolute `max_new_codes_per_batch` ceiling, using the same strictly
   greater comparison `checkpoint_signals` already makes. Each rule answers a question
   the other cannot: only the absolute rule can speak about a first batch, and only the
   ratio rule can tell a late batch's eight new codes from an early batch's.

   `spike_min_new_codes` is load-bearing rather than cosmetic. After a run of quiet
   batches the baseline median is zero, every count is trivially at or above
   `spike_factor * 0`, and the floor is the only thing standing between the rule and
   calling one new code a spike. A spike with a zero baseline records `ratio: null`
   rather than an infinity, because `Infinity` is not JSON and no reader could
   interpret it.

3. **The defaults are uncalibrated, and are labelled so.** Like `tau_fit` (brief §11),
   2.0, 3 and 4 are set by argument rather than against human judgment: 2.0 is "twice
   the recent normal", 3 is the shortest window whose median is not merely the previous
   batch, and 4 is the floor below which a doubling is noise at this corpus size. They
   are named fields so that a calibration sweep can move them; they must move through a
   calibration report, not by hand.

4. **There is still only one saturation curve.** `gaf.checks.growth.code_growth`
   delegates the counting to `gaf.analysis.hca.saturation_curve` over the unfiltered
   occurrence matrix and adds exactly one column that curve does not carry — new codes
   per response. Counting new codes a second time would give a reader two numbers for
   one fact. The curve is computable two ways from one implementation: from an ordered
   list of `Assignment` rows plus a batch size (the shape a coding spreadsheet exports
   in, so the PI's own coding in his export's order gets the same curve), and from a
   run's audit log (`response_prepared` for the response order, `code_created` for the
   admissions). Admission rather than assignment row is the unit, because a code
   admitted with no verified quote writes no assignment row and a curve built from rows
   alone would not know the codebook had grown.

5. **`should_checkpoint` gains a `spike` trigger, and the precedence is documented and
   implemented once.** `TRIGGERS` becomes `("health", "spike", "floor", "cadence",
   "manual", "none")`, and when more than one is exceeded the order is **health, spike,
   floor, cadence**: health first because a codebook already carrying near-duplicates is
   the most specific thing that can be wrong with it; spike second because it is the
   newer and uncalibrated rule and must not mask the one that has been in the build
   since Wave 3; the floor and the cadence last because they are schedules and say
   nothing about this codebook. `gaf.pipeline.decision_matrix.first_trigger` is the one
   implementation, called by both `should_checkpoint` and `evaluate_handover`, so the
   fast loop's per-batch trace and a later `gaf checkpoint` cannot name different
   triggers for the same state. `should_checkpoint`'s `curve` argument defaults to
   `None`, and without it the function behaves exactly as it did before.

6. **The handover is a third column of the matrix, not a third loop.** "Is the slow loop
   due" is taken by neither loop: the fast loop measures and reports and never blocks,
   the slow loop needs a human at a terminal. Giving it its own `loop` value in the
   matrix is what lets the matrix say where it happens. The two loops of the
   architecture diagram are still two.

7. **The matrix is data and cannot drift.** `DECISION_MATRIX` is a tuple of 29 frozen
   `DecisionRule` rows, each carrying `id`, `decision`, `loop`, `decided_by`,
   `condition` (a template rendered against the `RunConfig` in force, so a matrix
   printed for a run states that run's thresholds), `outcome`, `audit_event`, `source`
   (`module:function`) and `covers`. Tests resolve every `source` to a real callable and
   assert that every `gaf.embed.protocol.Route`, every member of `slow_loop.TRIGGERS`
   and every member of `gaf.models.OPERATION_TYPES` is covered by some row — and that
   no row claims to cover a token nothing defines, so completeness cannot be satisfied
   vacuously. A new route, a renamed function or a new operation type fails by name.

8. **The handover is evaluated at every batch boundary, and `checkpoint_due` is derived
   from that trace.** `run_fast_loop` calls `evaluate_handover` after each batch, emits
   one `checkpoint_evaluated` audit event per batch, and keeps every evaluation on
   `RunStats.decision_trace`. `RunStats.checkpoint_due` is now the last row of that
   trace plus `batches_due`, keeping its `fires`/`trigger`/`reason` keys so every
   existing reader still works. The second, end-of-run computation is gone: it was a
   second place the trigger could be read, and the two could disagree.

   Two consequences of doing it per batch are deliberate. `new_codes` is now **this
   batch's** new codes, because the evaluation is given the codebook as it stood when
   the batch began; the old computation passed no `previous`, so every code read as new
   and the health trigger effectively always fired. And
   `responses_since_checkpoint` is the running total rather than the whole run, because
   a fast-loop run never *takes* a checkpoint — it reports that one is due and keeps
   going. Resetting the count at a batch whose verdict was `checkpoint_due` would claim
   a checkpoint happened that did not. A run resumed after `gaf checkpoint` starts its
   own count at zero, which is the reset that is true.

   **One consequence worth stating plainly, because it is a fact about every cold run
   this build has coded, not only about the demo.** At the default `batch_size = 10`
   and `max_new_codes_per_batch = 8`, a cold run's *first* batch has no predecessor to
   compare against, so every code the batch admits counts as new. On the synthetic demo
   (14 responses) batch 1 admits 12 new codes; on the real 200-response corpus it admits
   15. Both exceed 8, so **a cold run's first batch trips the absolute rule as a rule,
   not as a coincidence of these two corpora**, and `gaf run --halt-on-checkpoint` on a
   cold run halts after batch 1 in both cases (ADR-0035 measures the real one). This
   happens to land close to the predecessor pipeline's own cadence of an early
   checkpoint at ten responses.

9. **`halt_on_checkpoint` stops the run but never truncates the artefacts.**
   `run_fast_loop(..., halt_on_checkpoint=False)` is the default and preserves the
   existing behaviour exactly. Set, it stops after the first batch whose evaluation says
   `checkpoint_due` and still closes the run normally — the closing S6 and M4, the final
   snapshot, `run_completed` — recording `halted_at_batch` and `responses_uncoded`. A
   half-written run directory is worse than a short one: every tool that reads a
   complete run must be able to read a halted one.

10. **The static matrix is a file, not a report section.** The run report gains a
    `DECISION MATRIX` section carrying *this run's* handover trace (batch, responses
    coded, new codes, near-duplicate pairs, spike, verdict, reason) and its spikes. The
    full matrix — every decision either loop can take — is written to
    `decision_matrix.md` beside the report by `gaf.report.run_report.write_decision_matrix`,
    because it says nothing about this run and a reader should not scroll past it every
    time they do not want it. The report prefers the spikes the run *recorded* over
    re-deriving them: the spike policy may have been re-tuned since, and a report that
    silently re-derived them under today's numbers would misreport why the gate came
    due.

**Consequences.**

The PI gets a growth curve with a rule attached that can distinguish an early batch from
a late one, and a matrix that is generated from the code rather than written about it.
The run report now says when the codebook asked for a human and why, per batch, instead
of only at the end.

The cost is one `codebook_health` call per batch instead of one per run, and
`codebook_health` embeds the whole codebook. The embedding service caches, so the
measured cost on `make demo` is within run-to-run noise; on a 200-response run at the
default batch size it is twenty codebook embeddings instead of one, which is still cheap
and entirely offline.

`RunStats.checkpoint_due` may report a *different* trigger than it did before for the
same run — not because the rule changed but because the old number was wrong: it
compared the entire codebook against an empty predecessor, so `new_codes` was the whole
codebook and the health trigger fired on almost every run. The codebook, the
assignments, the snapshot ids and the findings of a run are unchanged, and the golden
fixtures pass byte-for-byte without regeneration.

The three new `RunStats` fields all carry defaults, so a `run.json` written before this
change still loads and still renders; its `DECISION MATRIX` section says that no batch
boundary was evaluated, and its spikes fall back to what the growth curve shows now.

---

## ADR-0034 — The Definer: a fourth LLM role, outside both loops

**Status:** accepted (Wave C, T5 — Definer, `gaf codebook`), amended by
[ADR-0042](#adr-0042--the-definer-a-verbatim-segment-is-a-quote-at-any-length-and-the-prompt-registry-is-one-place):
`definer-v1` is registered in `gaf.agents.prompts.loader` with the other three, and the
golden manifest filters to the roles that run inside the loops instead. The reasoning
below about what the manifest may claim stands; it belongs to the manifest, not to the
loader.

**Context.** The principal investigator wrote a prompt that builds a codebook
inductively from code-text pairings a human has already assigned
(`inductive-codebook-prompt2.md`): a tree, a listing ordered by frequency, a grounded
description of one to three sentences per code and subcode, two verbatim examples per
leaf, and a short set of notes for the researcher. He ran it through a chat model and
got a codebook back.

T1 made every deterministic part of that prompt Python. Splitting `Parent-Subcode` on
the first hyphen, building the hierarchy, counting segments, consolidating trivial
duplicates while flagging the rest, choosing two examples per leaf by a stated rule,
and writing the notes are all arithmetic over the pairings, and `gaf.ingest.tagged`
does all of it — deterministically, reproducibly, and without a model call.

Exactly one instruction in that prompt is not arithmetic:

> "For **every** code AND subcode, a concise definition (1-3 sentences) in your own
> words, grounded strictly in its associated text. Each definition should make clear
> what content the code captures and how it differs from its siblings."

That is prose, it is the only thing a model is genuinely for here, and nothing in the
build could produce it. `CodingRules.require_description` is `True`, so a codebook
organised from the researcher's pairings without his own Markdown attached reports one
S6 `missing_description` WARN per code — 131 of them on the real file.

The architecture document says "two loops, three LLM roles". This makes four, and the
question that needed deciding is what kind of fourth it is.

**Decisions.**

1. **A fourth role, and it sits outside both loops.** The Definer runs **once**, over a
   coding a person has already finished, before or beside a run. It never sees a
   response being coded, never proposes a code, never reads or writes a snapshot, and
   is not reachable from `run_fast_loop` or from `run_checkpoint`. So the reader-visible
   architecture is unchanged where it matters: there are still two loops, and the fast
   loop still has two Coders and a Judge while the slow loop still has a Refactorer.
   What changes is the sentence "three LLM roles", which becomes four with one of them
   in neither loop. `docs/ARCHITECTURE.md` says so.

   The alternative — folding description-writing into the Refactorer, which already
   sees the whole codebook — was rejected because the Refactorer is the slow loop's
   *proposer of structural edits* behind a human gate (ADR-0004), and a role that both
   restructures a codebook and writes the prose defending the structure is a role
   marking its own work.

2. **Prose is the only thing delegated, and the schema is what enforces it.** The
   reply object has one key, `description`. Renaming, merging, splitting, creating and
   choosing an example are not expressible in it, so the role cannot express them —
   `parse_description` reads one key and discards everything else unread. This is a
   stronger guarantee than an instruction, and it is the same argument ADR-0003 makes
   about the fast loop never restructuring the codebook: the operations a stage must
   not perform should be absent from its output type, not merely forbidden in its
   prompt.

3. **Input per call: the code's name, its parent, its sibling names, and *all* of its
   segments.** Siblings are in because the researcher's own instruction is that a
   definition must say how a code differs from them, and a model that cannot see them
   cannot do that. Every segment is in — not a sample — because a definition drawn from
   the two example segments would be a definition of the examples.

4. **A parent code is described from its children's descriptions and counts, never from
   raw segments.** Leaves are therefore defined first and parents second, so a parent's
   children already have descriptions when it is described. The segments beneath a
   parent still travel on the context, unrendered, because the guards must be able to
   see a quote however it came to be written.

5. **Four deterministic guards after every call, each a finding, none a repair.**

   | id | what it catches | severity | effect |
   |---|---|---|---|
   | D1 | an empty description | ERROR | refused |
   | D2 | more than `MAX_SENTENCES` (3) sentences | ERROR | refused |
   | D3 | a verbatim copy of one of the code's own segments | ERROR (was WARN; ADR-0042) | refused |
   | D4 | a run of >= `MAX_SHARED_WORD_RUN` (8) words from a segment | ERROR | refused |

   **D3 was a WARN because ADR-0013 already ruled on exactly this** (ADR-0042 raises it
   to ERROR, and says why the S1 reasoning does not carry over): a description that
   copies its quote is present but explains nothing, which is a judgment about quality
   rather than structural certainty of invalidity.

   **D4 is an ERROR because it is a different question.** Not "is this a good
   definition" but "is this string shareable". A description travels into documents the
   corpus does not — `organised_shareable.md` exists precisely to be one — and a run of
   eight consecutive words of a respondent's text inside it is a quote. Eight is the
   word-side counterpart of the repository's character provenance shingle
   (`make provenance`, 30 when this was written and 20 since ADR-0047): at roughly
   5.5 characters a word it clears either bar with headroom, and it is short enough that a description would have to be reproducing a
   phrase rather than reusing a term to reach it.

   The two rules compose correctly. Copying a segment of eight words or more trips both
   and is refused; copying a shorter one trips D3 alone and is **also refused**, because
   ADR-0042 raised D3 to ERROR — a whole segment is a quote at any length. The guard
   table above carries the amendment; this paragraph originally did not.

6. **A refused description is not written back, and is not recorded in its own
   finding.** `Definition.to_json()` carries the code, the source, the verdict, the
   sentence and word counts and the findings — and never the text. The guard that
   catches a quote must not become the thing that publishes it. The findings carry
   counts, which is what a researcher acts on: "four sentences" and "shares a run of
   eleven words" both say what to do next.

   The cost: a refused description cannot be inspected after the fact, only re-produced
   by re-running. That is the right trade for a file that is written beside a directory
   of respondent text and is the most likely thing in it to be pasted into an email.

7. **The check ids `D1`-`D4` are deliberately outside
   `gaf.checks.contracts.CHECK_IDS`.** That tuple is a frozen contract enumerating the
   fast loop's structural (S1-S6) and semantic (M1-M4) checks. The Definer runs in
   neither loop, and its findings land in `definer_findings.json`, never in a run's
   `findings.json`. `CheckFinding.check_id` is a free string and `scope` is not — so
   the findings use the existing `"codebook"` scope, and the frozen contract is not
   amended at all.

8. **No new model slot, and no new task type.** `gaf/config.py` and `gaf/llm/base.py`
   are frozen contracts and this build adds the fourth role without amending either:

   * the Definer **resolves its model through `ModelRegistry.refactorer`**, the way
     `gaf.cli.checkpoint` does. It is the right slot on the merits, not merely the
     available one: it is the frontier, whole-codebook, outside-the-fast-loop binding,
     and the Definer is a whole-codebook job that runs once per checkpoint-sized unit
     of work. The consequence is that a live definition pass is priced and rate-limited
     as a refactor pass;
   * the Definer **reuses `TaskType.REFACTOR`**. The fail-safe that comes with it
     (`{"operations": [], ...}`) parses to no description, which is already the correct
     non-destructive default: an unreadable reply leaves the code undescribed, which is
     a recoverable S6 WARN, rather than inventing a definition. The consequence is that
     definition calls land in the `refactor` bucket of `CallLog.by_task()`; they stay
     distinguishable by their prompt version (`definer-v1`) and their `define:<code>`
     subject.

   If a later wave amends either contract, a `Role` of `"definer"` and a `TaskType` of
   `DEFINE` are both one additive line, and this decision should be revisited then.

9. **The Definer's template is not registered in `gaf.agents.prompts.loader`.** It has
   its own three-line registry in `gaf.agents.definer`, raising the loader's own
   `UnknownTemplateError` so the refusal behaviour is identical. The reason is not
   bookkeeping: `loader.all_templates()` is **the prompt surface of a run** — the set
   whose content hashes the golden manifest records as having produced a coding, and
   which `tests/test_agents.py` asserts is exactly the three loop roles. A manifest
   carrying `definer-v1`'s hash would claim a run's coding depended on wording that run
   never read. Registering it is one line if a later decision disagrees, and would
   require the golden fixture regenerated on purpose.

10. **Offline, the mock persona is extractive and says so.** `MockDefinerClient` reports
    the commonest content words of the code's own segments with their counts:
    *"`<code>` collects N segments whose commonest words are w (3), x (2), ... Written
    offline from the codebook itself; a stand-in, not a definition."* Two properties
    are load-bearing. A **count sits between every pair of reported words**, so the
    description's word sequence is `word, number, word, number, ...` and a run of
    consecutive words shared with a segment cannot grow past one through the reported
    list. And the **second sentence says what the text is**, so an artefact that loses
    its label still carries the warning in its own body.

    Every artefact carrying such a description is labelled
    `description_source: "definer-mock"` — per code in `codebook.json` and
    `organised.json`, and as a header block on `organised.md` and
    `organised_shareable.md`, because `OrganisedCodebook.to_markdown` renders a
    description and not its source. **A mock description is built from a respondent's
    words**, so a directory carrying one belongs under `runs/` exactly like anything
    carrying examples.

11. **The live path is unexercised, like the other three roles.** Nothing in `tests/`
    or CI constructs a real client for it; `--live` on `gaf codebook define` builds one
    through the same `_live_client` the other commands use, and fails before spending
    anything if the SDK or the key is missing.

12. **`MAX_SENTENCES = 3` lives in `gaf.agents.definer`, not in `gaf.config`.** It is a
    transcription of a stated instruction in the researcher's own prompt, not a
    threshold a calibration sweep could move, and `config.py` is frozen. It is rendered
    into the prompt by the same constant the guard enforces, so the wording and the
    rule cannot say different numbers — a test drives a re-tuned bound through both.

**Consequences.**

*What this buys.* The 131 S6 `missing_description` WARNs on the real codebook close
without a human writing 131 paragraphs, and without a chat window: the description of
each code is produced from that code's own segments, recorded with its source, and
checked. Every guard is deterministic, so "the model wrote a quote instead of a
definition" is a row rather than something a reader notices three weeks later. The
codebook the researcher already built by hand is untouched: `gaf codebook define` never
overwrites a description whose source is `pi-codebook-md`, under any flag.

*What it costs.*

* **The architecture sentence is now longer.** "Two loops and three LLM roles" was a
  sentence you could print in a methods appendix. "Two loops, three LLM roles inside
  them and one outside" is still one line, but it is a line that needs the second half
  of decision 1 to defend it.
* **A fourth role is a fourth source of drift.** It is mitigated the way the other three
  are — a versioned prompt whose id travels with every call, a content-addressed disk
  cache, structured output, a call log, deterministic guards — and further by the role
  writing prose that nothing downstream computes on.
* **Definer calls are indistinguishable from refactor calls in the cost table** until a
  reader looks at the prompt version. Decision 8 is the reason; it is recoverable.
* **Some of the researcher's own imported descriptions use the word "framing" in its
  ordinary English sense.** They are his data, imported as given under ADR-0032, and
  this task did not rewrite them. The Definer's own output is generated text, which is
  where ADR-0005's vocabulary rule binds; no vocabulary guard is implemented here, and
  if one is added later it must read the **per-code** `description_source` this task
  records and exempt `pi-codebook-md` rather than fail on it or silently edit the
  researcher's document.
* **`organised_shareable.md` is shareable about *examples*, not about descriptions.**
  It withholds every segment, which is what it was built to do — and it still carries
  whatever the descriptions say. Measured on the real codebook with the researcher's own
  definitions attached, and independently reproduced while writing this entry: **5 of
  his 131 imported descriptions share a run of thirty or more characters with a real
  response, the longest of them forty-eight characters (top runs 48, 47, 41, 40, 38
  characters), and one carries an eight-word run** (`requirements-basic_income`,
  the same code as the 48-character run) — which is exactly what guard D4 refuses when
  the Definer writes it, and evidence that the eight-word bound is set in the right
  place rather than too tight. The same document built from `definer-mock` descriptions
  shares **no** thirty-character run at all; its longest shared *word* run is three, not
  two — the third word comes from a leaf's own hyphenated code name (the mock's leaf
  template opens with the code's own name, and a name like `self-driving_cars` or
  `quality_of_life` can, once split on its hyphen and underscore, reproduce an ordinary
  three-word phrase already present in the corpus). That is still five words clear of
  the D4 threshold and is the same class of coincidence ADR-0038 records for a fixture
  string, not a case of the guard missing anything: 0 of the 131 mock descriptions trip
  D4, against 1 of the 131 imported ones. An imported description is the researcher's
  own document and is not this build's to rewrite (ADR-0032), so the command labels the
  file rather than editing it, and the scan that would catch this on a tracked file
  (`make provenance`) does not see a directory under `runs/`. **Anyone about to send
  `organised_shareable.md` to a third party should read the descriptions first.**
* **A parent's description depends on its children's.** Re-defining one leaf therefore
  leaves its parent describing a codebook that has moved. `gaf codebook define` without
  `--only-missing` re-describes everything the Definer wrote, which is the recovery;
  nothing detects the staleness automatically.

---

## ADR-0035 — A seeded run holds the seed's evidence out, and says what it costs

**Status:** accepted (Wave C, T5 — seeded runs, the handover flags)

**Context.** The principal investigator observed that the machine has no idea how his
codes are organised. He is right, and the gap was never in the pipeline — it was in the
command line.

`run_fast_loop` has always taken `codebook: Codebook | None`, and
`gaf.pipeline.prep.assemble_context` has always put the frozen snapshot's hierarchy
skeleton in front of a coder alongside the top-k retrieved codes. A run started from a
codebook therefore codes *into* that organisation: retrieval finds its codes, the coder
sees its families, and M2's routing band merges into them rather than creating parallel
concepts beside them. None of it was reachable from `gaf run`, so every run this build
has ever done started from nothing.

Two things had to be decided before exposing it.

**First, what a seed's own evidence means for the run that reads it.** A codebook is not
only structure. `gaf.models.Code.evidence` holds verified quotes, and
`gaf.analysis.matrix.assignments_from_codebook` projects *every* verified quote a
codebook holds into the canonical assignment shape. The measurement, on the real files:
the codebook `gaf codebook organise` builds from the researcher's 342 pairings carries
**312 evidence rows across 109 codes**. Seed it into a run and carry that evidence
through, and the run's `codebook.json` holds 312 rows the run did not produce. They do
**not** reach `assignments.json` — those rows are built only from responses this run
coded — but they reach:

* `gaf analyse --assignments <run>/codebook.json`, which is one of the two documented
  ways to build the occurrence matrix, and therefore
* the binary occurrence matrix, the low-frequency filter, Ward's HCA and the saturation
  curve derived from it;
* `usage_from_codebook`, and so the usage table the Refactorer reasons about at the next
  checkpoint;
* every count a reader takes off the run's codebook.

The same human coding would then be counted twice — once in the coding that produced it
and once in the run seeded from it — and the two artefacts in one run directory would
disagree about what that run found.

**Second, what a seeded run is worth as evidence.** The golden-set validation this
project rests on (`docs/VALIDATION.md`, Alqazlan-style concurrent validation) compares a
human coding against a machine coding that did not see it. A run seeded from the
codebook that human coding produced has seen it. Its agreement with that coding is not a
measurement of anything.

**Decisions.**

1. **`gaf run --seed-codebook <codebook.json>` passes the seed to
   `run_fast_loop(codebook=...)`.** No change to the loop; the flag is the whole
   feature. The seed is read through `gaf.cli._common.load_codebook_arg`, so a file
   holding assignments rather than a codebook is refused by name.

2. **The seed's evidence is held out of the run.** `gaf.cli.run.seed_from` returns a
   copy of the seed with `evidence=[]` on every code, and stamps two facts on each
   code's `meta`: `seeded_from` (the seed's content hash) and
   `seed_evidence_held_out` (how many rows that code arrived with). What the seed
   supplies is **structure** — names, families, parents, descriptions — which is
   exactly and only what retrieval (`embed.protocol.code_text` reads name and
   description) and the coder's hierarchy skeleton consume. Its evidence is a previous
   coding's occurrences and has no business wearing this run's label.

   This makes "this run's outputs describe this run's coding" true by construction
   rather than by a caveat nobody reads, and it makes the two artefacts agree: on the
   real corpus, the occurrence matrix built from a seeded run's `codebook.json` and the
   one built from its `assignments.json` are identical, cell for cell.

   The seed file still holds its evidence; nothing is lost. `gaf validate agreement` is
   where two codings are meant to meet, and it takes both of them by name.

3. **The run records `seeded_from`** — the seed's path, its content hash, its code and
   family counts, how many of its codes carried a description, how much evidence was
   held out, and the distinct `source` / `description_source` values its codes carry —
   in `run.json` (under `provenance`), in `stats.json`, and as a `run_seeded` audit
   event emitted before the run begins.

   The brief asked for it on the `run_started` event. `gaf/pipeline/fast_loop.py` emits
   that event and is not this task's file to change (GLOBAL §7), so the seed is its own
   append-only row instead, written immediately before `run_fast_loop` is called so the
   log reads in the order the work happened. Folding it into `run_started` is a
   two-line change whenever that file is next open.

4. **The run report says what a seeded run costs, above every number.** ADR-0019 puts
   the caveats first because a reader must meet them before the figures, and the seeded
   caveat is inserted ahead of the offline one:

   > This run was SEEDED from an existing codebook (N code(s), content hash H). It coded
   > into an organisation somebody had already built, so its agreement with the coding
   > that produced that seed is NOT independent evidence about either of them: the
   > machine was shown the shape of the answer before it started. A cold run — the same
   > command with no `--seed-codebook` — is the validation path, and the agreement
   > figures that belong in a methods appendix come from one of those. The seed's own
   > evidence was held out of this run, so every number below describes this run's
   > coding and no other.

   The PROVENANCE section gains the seed's path, hash, counts and held-out evidence, so
   the caveat is checkable rather than merely asserted.

5. **`gaf run --halt-on-checkpoint` passes `halt_on_checkpoint=True`, and a halt exits
   0.** A checkpoint coming due is the designed behaviour of the handover (ADR-0033),
   not a failure, and exit 1 is reserved for an artefact that is invalid. On a halt the
   CLI prints the batch, the matrix rules that fired, the trigger, the reason, how many
   responses remain, and the two commands that continue the work:

   ```
   gaf checkpoint --run <dir>
   gaf run --corpus <corpus> --seed-codebook <dir>/codebook.json --skip-coded <dir>
   ```

   Default off; with the flag off nothing changes, which the golden set proves by
   continuing to pass unregenerated.

6. **`gaf run --skip-coded <run-dir>` excludes responses that run already coded.** The
   authority is the previous run's own per-response outcomes in `run.json`, unioned with
   its assignment rows — not the assignments alone, because a response the loop prepared
   and coded may legitimately have produced no assignment row (a duplicate, or one whose
   every candidate was dropped), and re-coding it would be coding it twice. The resumed
   run states what it skipped, on stdout and in `provenance.skipped_from`. Skipping
   everything is refused by name rather than producing an empty run.

**Consequences.**

*What this buys.* The researcher's own organisation of his codes is now something the
machine can be given, in one flag, and the run that results is honest about what that
does to it. The handover between the loops is a loop a person can actually run: code
until the gate is due, stop, review, resume — measured on the real corpus, and
independently reproduced while writing this entry: **the halt fires at batch 1** after
10 responses (15 new codes, over the absolute ceiling of 8; 190 remain), and
`--seed-codebook` + `--skip-coded` picks up the remaining 190.

**A measured result worth recording: the halted run and its resume together reproduce
the cold run's assignment rows exactly — 104 + 1848 = 1952 rows, and every one of those
1952 rows is also a row of the 1952 the single uninterrupted cold run produces, with no
row shared between the halted half and the resumed half.** Resuming through the
handover is lossless.

*What it costs.*

* **Independence.** This is the real price and it cannot be engineered away, only
  disclosed. A seeded run is a *production* tool: it codes the remaining 180 responses
  into the organisation the researcher built from the first 20. It is not a
  *validation* tool, and any agreement statistic computed against the coding that
  produced its seed is circular. Cold runs remain the validation path. The caveat says
  so in the report; `docs/VALIDATION.md` says so too.
* **The seed changes the coding, measurably.** On the real corpus a seeded run and a
  cold run over the same 200 responses both produce 1952 assignment rows, but **186 of
  the cold run's rows have no counterpart in the seeded run's** (and 186 of the seeded
  run's have no counterpart in the cold run's): the seeded run created 18 new codes
  where the cold run created 22, because four concepts merged into codes the seed
  already had. That is the mechanism working as designed, and it is also the precise
  reason the two runs are not independent measurements of the same thing.
* **A seeded run's codebook is mostly empty codes at batch 1.** Seeding 131 codes and
  holding their evidence out means `codebook_health` sees 131 zero-evidence codes on the
  first health row, and M4 measures near-duplicates across all 131 leaves. Neither is a
  trigger by itself (the handover fires on near-duplicate pairs, new codes and the
  spike rule), but a large seed makes a near-duplicate finding at batch 1 much more
  likely, and with `--halt-on-checkpoint` that means a seeded run can halt almost
  immediately. That is arguably correct — a seed with near-duplicate leaves is
  something a human should look at before coding 200 responses into it — but it is a
  behaviour change nobody asked for, and a reader should know it comes from the seed
  rather than from the corpus.
* **`RunStats` has no seed field.** `seeded_from` is written into `stats.json` beside
  the stats by the CLI, not carried on the dataclass, because `RunStats` is the loop's
  own shape and the seed is a fact about how the command was invoked. A reader loading
  `stats.json` gets it; a reader constructing a `RunStats` in Python does not.
* **Held-out evidence is invisible to the next checkpoint's usage table.** The
  Refactorer at a checkpoint in a seeded run sees the seed's codes with the usage
  *this* run gave them, which is the correct number for this run and an understatement
  of the code's total support across both codings. `meta["seed_evidence_held_out"]` is
  on every seeded code so a later stage can say so; nothing currently reads it.

---

## ADR-0036 — Pattern mapping and affinity are views; affinity clusters leaves across families; both blends are uncalibrated constants; no respondent text in any of the three

**Status:** accepted (Wave C, T3 — patterns, affinity, crosswalk)

**Context.** The PI asked for three related but distinct deterministic analyses over
artefacts the pipeline already writes (`gaf/analysis/patterns.py`,
`gaf/analysis/affinity.py`, `gaf/analysis/crosswalk.py`): which responses share which
combinations of codes, an affinity-style bottom-up thematic grouping of codes, and a
mapping of the machine's codebook onto the organisation of his own. None of the three
may edit a codebook — restructuring an admitted codebook happens only behind the human
gate in the slow loop (`docs/ARCHITECTURE.md`, "The flow", and ADR-0004), and all three
sit in the deterministic analysis tail alongside `matrix.py`, `hca.py` and
`agreement.py`, which they reuse rather than duplicate.

**Decisions.**

1. **Patterns and affinity are views, and never edit the codebook.** `build_patterns`
   takes whatever `OccurrenceMatrix` it is handed and reports the filter that already
   produced it (`PatternReport.filter`); it does not re-filter. `build_affinity`
   clusters leaf codes into groups for reading, never merges or renames anything —
   `AffinityGroup` is a reporting unit, not an `Operation`. `build_crosswalk` produces
   a read-only mapping between two `Codebook` objects; it does not write to either one.
   A caller wanting the crosswalk to inform an actual restructuring still has to carry
   the finding through the human gate by hand, the same as any other slow-loop
   proposal.

2. **Affinity clusters leaves *across* families, not within one.** An affinity
   diagram's whole method is to group notes by likeness while ignoring the heading
   they arrived filed under; scoping the clustering to one family at a time would
   defeat that on the one case this module exists to surface. ADR-0029 already
   recorded, on the PI's own highlights export, that a subcode label can recur
   identically under two or three different parent families (`problem_solving` /
   `problem-solving`-style near-duplication, and outright identical sub-labels under
   different tops). `build_affinity` therefore clusters every codebook leaf against
   every other leaf regardless of family, and reports `AffinityGroup.cross_family`
   plus a *separate*, purely structural table (`CrossFamilySubcode`) of every
   identical sub-label the codebook itself carries under more than one family —
   computed over the codebook directly, independent of clustering or of the
   occurrence matrix, so it is visible even when a family-scattered concept never
   clusters together on cosine or co-occurrence grounds.

3. **Both blended similarities are documented, single constants, and are flagged
   uncalibrated — the same posture as `CodingRules.tau_fit`.** Affinity blends
   `alpha * cosine(code_text) + (1 - alpha) * Jaccard(co-occurrence)`, `alpha = 0.7`
   (`DEFAULT_ALPHA`), cut at similarity `>= 0.5` (`DEFAULT_SIMILARITY_THRESHOLD`) for
   average-linkage agglomerative clustering. Neither constant has been checked against
   a human theming; both were set by inspection of the blend's plausible range, in
   exactly the sense `tau_fit`'s own docstring in `gaf/config.py` is provisional.
   Change either through a calibration report, not by hand. The crosswalk reuses the
   run's own `CodingRules.tau_high` / `tau_low` rather than inventing a fourth
   threshold, and reuses `gaf.embed.protocol.route_similarity` for the threshold
   comparison itself — the three-band vocabulary (`same` / `grey` / `unmapped`) is a
   renaming of `Route.MERGE` / `Route.JUDGE` / `Route.CREATE` for a cross-codebook
   comparison, not a re-implementation of the comparison.

4. **The crosswalk reports both a Hungarian assignment and the unconstrained nearest
   neighbour, because the interesting finding lives in the one the other cannot show.**
   `gaf.embed.matcher.hungarian_match` is reused, not reimplemented, for the
   one-to-one optimal assignment. But a one-to-one assignment cannot, by construction,
   show several source leaves converging on the same target — which is exactly the
   granularity finding this module exists to surface ("several machine codes landing
   on one human code"). Every source leaf therefore also gets its unconstrained
   nearest target (independent argmax over cosine, no assignment constraint at all),
   and the family roll-up (`FamilyRollup`, both directions) is built from that
   unconstrained mapping for the same reason. `n_unmapped` on `FamilyRollup` means a
   mirrored but different thing on each side — a source family's own leaves whose best
   score never reached `tau_low` (inventions) versus a target family's leaves that
   nothing maps to at all (blind spots) — and both are spelled out in the field's own
   docstring rather than left for a reader to infer from the field name alone.

5. **The triple-combination enumeration in `patterns.py` is bounded by an Apriori
   join, not by brute force, and the bound is reported when it bites.** A naive
   `C(n_codes, 3)` is infeasible well before "a few hundred codes"; a triple can only
   meet `min_support` if each of its three constituent pairs independently does,
   because support is monotone non-increasing as a combination grows. Candidate
   triples are therefore generated only by joining already-frequent pairs, and only
   those survivors are ever scored exactly against `min_support`. `MAX_TRIPLE_CANDIDATES`
   (20,000) is a second, harder cap on top of the join for the pathological case — a
   small `min_support` over a large, densely co-occurring codebook — where even the
   joined candidate set could still be too large; `CombinationReport.triple_bound_hit`
   and the two candidate counts (`triple_candidates_total` vs.
   `triple_candidates_considered`) say, in the artefact itself, whether the bound cut
   anything and by how much, rather than silently returning a partial answer that
   looks complete.

6. **No respondent text enters or leaves any of the three modules.** All three
   operate exclusively on response *numbers*, code *names*, family *names* and
   numeric scores — never a quote, a segment or a response's `content`. `patterns.py`
   and `affinity.py` take an `OccurrenceMatrix` (already stripped to code names and
   0/1 occurrence) and, for affinity, a `Codebook` (names and descriptions the PI or
   the pipeline wrote, never a respondent's words). `crosswalk.py` takes two
   `Codebook` objects for the same reason. This is asserted structurally by
   construction rather than by a runtime check: none of the three modules imports
   `gaf.models.Response` or accepts one as an argument, so there is no `content`
   field anywhere in reach to leak.

**Consequences.** A later task (T6) is expected to wire `build_patterns`,
`build_affinity` and `build_crosswalk` into `gaf analyse` and to draw their JSON in an
HTML page; the `to_json()` shape of every dataclass here is therefore treated as a
stable contract from the moment this ADR is accepted; the T3 report spells every shape
out field by field. The cost taken on is two uncalibrated constants (`DEFAULT_ALPHA`,
`DEFAULT_SIMILARITY_THRESHOLD`) joining `tau_fit` as thresholds that read like
calibrated numbers but are not; both carry the same "PROVISIONAL" posture in their
docstrings and neither should be quoted in the write-up as more than an inspection
default until a calibration report says otherwise.

---

## ADR-0037 — `views.html` is the shareable page and `codebook.html` is not; how the palette was derived

**Status:** accepted (Wave C, T6/T8 — `views.html`)

**Context.** The PI's tenth note asked for multiple views through more
visualisations: one page holding many readings of a coding, rather than one figure
scattered per artefact. `gaf report` already wrote one HTML page, `codebook.html`,
built to be audited against the corpus — every code, every quote, every finding
attached to it. That page cannot be the one that leaves the machine: it carries
respondent text by design, and it is not shareable. A second page was needed that
carries the *shape* of a coding — code names, family names, response numbers, counts
and scores — and nothing a respondent wrote, and eleven views of one coding need a
categorical colour to keep one family's mark the same colour from the codebook tree to
the heatmap to the affinity cards.

The real codebook the PI's own coding implies holds **fifteen families**
(ADR-0032; `AI_Perceptions_Codebook1.md`). No categorical palette of a size a person can
still tell apart at a glance is pairwise distinguishable under every form of colour
vision, and a twelve-slot palette designed by eye and checked afterwards failed three of
six standard checks (chroma floor, CVD separation, normal-vision separation).

**Decisions.**

1. **Two pages, one rule about what may appear on the shareable one.** `codebook.html`
   is the working artefact: it carries the evidence quotes and exists to be audited
   against the corpus. `views.html` is its shareable counterpart: it never reads
   `Assignment.segment`, `Evidence.quote` or `Response.content` — and, by the same
   reasoning, never prints a code's description or a model's prose rationale either,
   because a description is written by an agent that has just read a response, and the
   safe rule is the rule that does not have to distinguish "this generated prose is
   fine" from "that one is not." Six tests hold the property down; two are controls that
   fail if the fixtures driving them stop carrying respondent text at all, which is what
   makes them tests of the property rather than of the current output. `gaf/report/html.py`
   gains one paragraph linking `codebook.html` to `views.html` and saying, in one
   sentence, which is which — the only edit made to that file for this work.

2. **The palette is computed against a stated set of checks, not chosen by eye and
   checked after the fact.** Twelve evenly spaced OKLCH hues, one lightness and chroma
   ceiling per colour scheme, found by enumerating start angles and slot orderings and
   keeping the ordering that maximises the worst *adjacent* contrast under simulated
   colour-vision deficiency in both schemes at once. On the **adjacent** pairlist — the
   one that governs a neighbouring band, bar or row, which is what every figure on this
   page actually draws — the chosen ordering passes every check in both schemes: the
   lightness band, the chroma floor, the CVD separation, the normal-vision separation and
   the contrast against the page's own surface.

3. **On the all-pairs list it does not pass, and no twelve-slot categorical palette
   can: twelve hues are not pairwise separable under deuteranopia at any ordering.** The
   usual remedy — fold the excess series into "Other" — is not available here: fifteen
   families genuinely exist in the codebook the PI's own coding implies, and collapsing
   three of them into a bucket would be a lie about the data. `family_palette` therefore
   wraps past twelve slots rather than merging anything, and the module never lets that
   wrap stand alone: every band, bar and cell it draws carries a direct text label or a
   `<title>` naming the family and its count, and a full text listing sits beside every
   figure that uses the palette. **Colour groups; text identifies**, everywhere on this
   page — which is the actual mitigation, not a caveat beside a broken guarantee.

4. **The sequential ramp — the heatmap's density, the co-occurrence table — is an
   opacity over one hue, not a lightness ramp**, because an opacity is
   scheme-independent where a lightness step is not; the categorical palette keeps the
   same discipline through CSS custom properties defined once per scheme, so no literal
   colour is ever written into an element.

**Consequences.**

*What this buys.* A reader with a common form of colour vision deficiency can still
read every figure on `views.html`, because nothing on it depends on telling two
adjacent colours apart on sight alone — the family name is always there in text beside
the mark. The page can be handed to a collaborator or attached to an email in a way
`codebook.html` never should be, which is the whole reason this ADR exists beside
ADR-0038.

*What it costs.* The all-pairs guarantee a smaller codebook's palette could in
principle offer is gone the moment a codebook passes twelve families, which the real
one already does. That is disclosed rather than hidden: `gaf.report.svg`'s own module
docstring states the limitation, `views.html` never claims a colour-only encoding
anywhere, and if a codebook grows large enough that even the secondary text encoding
gets crowded, the next lever is a texture fill on alternate slots, which the palette
has room for and which this build does not yet need.

---

## ADR-0038 — The provenance guard met a coincidence, and the PI's own definitions are not blanket-shareable

**Status:** accepted (Wave C, T8 — from the wave's own notes). The two shingles this
entry contrasts — 30 for the document-level guard, 20 for the item-level one — are now
one number, 20, loaded from the exporter (ADR-0047). The *layering* this entry decides
is unchanged, and decision 1 is the rule ADR-0047's rewordings apply.

**Context.** Two incidents this wave, both instances of the same limit on the
provenance guard: a check that passes is evidence only about the set it was pointed at
(ADR-0030's lesson, for a fourth time).

**First.** Widening the provenance scan to read CSVs as well as workbooks (T1, so the
scan could see the 200-response corpus at all — ADR-0031's own context) flagged
`tests/test_llm.py`'s `UNPUNCTUATED` fixture constant: a 36-character run shared with
exactly one response in the 200-response CSV. Verified by commit date against file
date: the fixture sentence was invented in Wave 1 (commit `2b9ef89`, 1 September), and
the CSV it now overlaps with arrived on the machine on 12 September, eleven days later.
**This is a coincidence, not a leak** — the dates are a hard alibi — and it was resolved
the cheap way available for an invented sentence: the two offending lines were
reworded, and the scan passes.

**Second.** `gaf codebook organise --definitions ...` imports the PI's 131 descriptions
as given (ADR-0032). Scanning `organised_shareable.md` — the file built expressly to
withhold every segment — against the real corpus with the repository's own
30-character shingle finds, as ADR-0034's consequences already record, **5 of the 131
imported descriptions sharing a run of thirty characters or more with a real response**,
the longest 48. `organised_shareable.md` withholds the examples; it does not, and
structurally cannot, withhold anything inside a description the researcher wrote,
because it renders whatever `Code.description` holds, verbatim, as its whole reason for
existing.

**Decision.**

1. **The guard cannot tell coincidence from copying, and it should not try to.** A
   30-character shared run is exactly as consistent with "this fixture happened to
   share a stock phrase with unrelated text that arrived later" as with "this text was
   copied from the real corpus." Telling the two apart needs evidence the shingle scan
   does not have — a commit date measured against a file's arrival date, in this
   instance — so the guard's job stays narrow (find every candidate) and a person
   decides what each one means. Rewording is the right answer whenever a candidate is
   confirmed a coincidence and the string is the build's own invention to begin with;
   nothing about the guard's design should try to make that judgment on its own.

2. **A description is only as shareable as whoever wrote it made it, and an exporter
   that ships descriptions outside this repository must check each one on its own,
   never the document as a whole.** `scripts/export_results.py` (T7) already does
   this: every description it emits passes through its own `guarded_description`,
   tested against a 20-character shingle — stricter than the repository's own
   30-character guard, deliberately, because this script runs on the machine that has
   the data and can afford to be — and a colliding definition is replaced by its code
   name plus a fixed withheld-marker string rather than being emitted. Withholding a
   definition is not withholding the code: the name stays, only the prose that
   collided is removed, and the count of what was withheld is printed and written into
   the export itself. This is the operational answer to the finding above: the
   document-level guard (`make provenance`, the repository's 30-character scan over
   tracked files) and the item-level guard (the exporter's per-description check) are
   two different mechanisms answering two different questions, and neither is a
   substitute for the other.

3. **Neither finding changes what is tracked.** `organised_shareable.md` lives under
   `runs/` beside every other artefact `gaf codebook organise` writes — the command
   says so on every invocation (`gaf/cli/codebook.py`) — and it is never committed;
   `make provenance` scans tracked files and structurally cannot see it. The guard that
   does see it is the exporter's own per-item check at the moment a result crosses into
   `results/`, which **is** tracked and therefore inside `make provenance` as well
   (ADR-0030 decision 4).

**Consequences.**

*What this buys.* Two governance events this wave resolve to "the guard worked as
designed, and something one level downstream needed a second, narrower check that
already exists" rather than to a repeat of ADR-0024. The distinction between a
document-level guard and an item-level guard is now explicit rather than assumed, and a
reader of this log has both incidents in one place rather than scattered across two
task reports.

*What it costs, and what remains open.* Whether the PI is willing to have the five
colliding definitions rephrased, or would rather they simply never appear in a shared
document, is his decision and belongs in `results/india-process-1-200/README.md` (T7)
as a question for him, not answered here. Until he answers it, every document that
carries his imported descriptions — `organised.md`, `organised_shareable.md`, and any
results export that quotes a definition — must carry the same per-item check, and this
entry names none of the five colliding codes, so that this permanent record does not
itself become a map of which ones to go looking for.

---

## ADR-0039 — The reorganisation trail carries structure, not payloads

**Status:** accepted (fix pass F1, from the R1 correctness audit); extended by fix pass F2
(from the R2 privacy audit, finding C-1) to cover `Operation.rationale`

**Context.** `reorganisation_trail.json`/`.md` is the artefact most likely to be pasted
into a methods appendix: its whole purpose is to be readable by somebody who was not at
the gate. D7 and ADR-0036 say it carries code names, response numbers and counts only.
It did not. The independent correctness audit reproduced three leaks, twice:

* an operation the human **edits** was rendered as its raw `Operation.to_json()`, before
  and after. Editing a `split` is how a human moves quotes between the parts, so the
  operation most likely to be edited is the one most likely to carry them;
* an operation **dropped** in validation was rebuilt from the stored proposal with its
  payload intact, and a `create` carries its `evidence` there;
* a dropped operation's **reason** is the validator's own sentence, and
  `EvidenceLossError` embeds the ``(response_id, quote)`` pair it rejected, verbatim.

Measured with a 20-character shingle scan of the synthetic corpus against the produced
artefacts: 32 distinct corpus shingles in the JSON, 32 in the Markdown. `timeline.*`,
`views.html`, `decision_matrix.md` and every analysis artefact were clean.

**Decision.**

1. **An allow-list, not a deny-list.** `gaf.report.trail.SHAREABLE_PAYLOAD_KEYS` is the
   set of payload keys the trail may carry, applied recursively so a `split` entry's
   own keys are filtered too: `name`, `into`, `new_parent_id`, `parent_id`,
   `response_ids`. A payload key added later is withheld until somebody decides it is
   safe, which is the direction a privacy default should fail in.
2. **Withholding is visible.** Each `EditedOperation` names the keys removed from
   either side, each dropped operation's reason names the keys removed from it, and the
   entry carries the union. An artefact that silently omits something reads as complete.
3. **A validator's sentence never travels.** The trail states a gloss written in
   `gaf.report.trail.DROP_GLOSS` from the drop **marker** alone, and sends the reader to
   the run's own `findings.json`, under `runs/`, for the sentence itself. This is a
   general rule rather than a patch on `EvidenceLossError`: any validator's sentence can
   name the data it rejected, and a rule that had to be re-audited every time a message
   changed would not be a rule.
4. **The rationale is guarded at the source and at the sink** (added by F2, from R2 C-1).
   The first three decisions filtered the operation *payload* and left `rationale` — free
   model prose rendered beside it — untested, while `gaf/agents/prompts/refactorer_v1.py`
   *required* the model to put the evidence an operation rests on into that field. Both
   ends move. The prompt now requires the rationale to cite response numbers and code
   names and forbids quoting response text. `gaf.report.trail` builds a `_RunWording`
   needle set from every response in the store, every evidence quote in the run's
   snapshots and every assignment segment, and renders `rationale` — on an entry, on
   both sides of an `EditedOperation`, and on a dropped operation — only through
   `_RunWording.guarded`, substituting `RATIONALE_GLOSS`. The Refactorer's closing
   `reasoning` paragraph goes through the same guard with `REASONING_GLOSS`. The window
   is **eight words** (`RATIONALE_SHINGLE_WORDS`), not a character shingle: a rationale
   is prose *about* codes and will share short character runs with any response on the
   same subject however it is written, whereas eight consecutive words in common is a
   sentence in common. A text shorter than the window is held and matched whole, so a
   quote too short to fill it is still caught entire. `scripts/export_results.py` adds
   `rationale` to `TEXT_KEYS` at the same time, so the exporter withholds it the day any
   section starts emitting it.

**Consequences.**

*What this buys.* The claim D7 and ADR-0036 make about the trail is now true by
construction rather than by inspection, and a test drives an edited split, a dropped
`create` carrying evidence and an evidence-loss drop through a real checkpoint and
asserts that no twenty-character run of any synthetic response reaches
`reorganisation_trail.json`/`.md`, `timeline.json`/`.md`/`.svg` or `views.html`. The
same test asserts that the run's own `codebook.json` **does** contain such runs, so a
clean result means the scan works rather than that it looked nowhere.

*What it costs.* A reader of the trail can no longer see exactly which quotes a human
moved when they edited a split, or exactly which pair an evidence-loss drop lost. Both
are in the run directory, which is where a respondent's words belong. A reader also loses
the rationale itself wherever it reproduced eight words of the run's own text — the
operation, its type, its targets and its filtered payload are still there, so what is
lost is the model's sentence, not the record of what it did.

*What the rationale guard cost, and what it moved.* The prompt rewording changes the
Refactorer's prompt text, so `tests/fixtures/golden/manifest.json` moves by exactly one
line, the `refactorer/refactorer-v1` digest. Nothing else in the golden fixture moves:
`codebook.json`, `assignments.json`, `snapshots.json` and `findings.json` are
byte-identical, because the offline mock Refactorer's rationales are fixed strings that
no respondent shares and the guard therefore passes them through unchanged. That is the
manifest doing its job — it exists to make a prompt edit visible.

*The residual risk this entry does not close.* The guard is a wording test, not a
semantic one: a live Refactorer that paraphrases a response closely enough to stay under
eight consecutive shared words will still be rendered. The 8-word window is a judgement,
recorded here so it can be argued with; `tests/test_trail.py` holds both directions of it
(a rationale that quotes a response is withheld; one that quotes nobody is rendered as
written), and both are driven through a real checkpoint and read from disk.

---

## ADR-0040 — The hard floor counts from the last checkpoint, and the spike rule stands aside where it has no baseline

**Status:** accepted (fix pass F1; amends ADR-0033)

**Context.** ADR-0033 made the decision matrix evaluate the handover at **every** batch
boundary rather than once at the end of a run. Two of its rules did not survive the
change of frequency.

*The floor latched.* `hard_floor_reached` compared `responses_coded` — a running
total nothing resets — against `hard_floor_responses`. Evaluated every batch, that
means every batch after the fiftieth response reports `checkpoint_due` under trigger
`floor`, for ever, in that run and in every run resumed from it. Measured on a quiet
codebook at 200 responses and batch size 10: batches 5 through 20, sixteen of twenty
rows, verdict `checkpoint_due`, trigger `floor`. `gaf run --halt-on-checkpoint` then
halts at batch 5 on the schedule rather than on anything about the codebook, and the
resumed run, counting from zero, halts again fifty responses later. D6's handover
becomes a fixed four-stop schedule wearing an event trigger's name.

*The spike rule repeated the absolute one.* In the first `spike_window` batches
`detect_spikes` fell back to `max_new_codes_per_batch`, which is definitionally the
comparison `checkpoint_signals` already makes under `handover.new_codes`. Both fired on
one condition; the batch's `reason` stated the same fact twice, and
`CheckpointSignals.spike_detected` was true on a batch where no *ratio* spike had
occurred.

**Decision.**

1. **The floor is `responses_since_checkpoint >= hard_floor_responses`.** "A quiet
   codebook still gets a human look" is a statement about how long it has been since the
   last look, not about how far into the run the row sits. `responses_coded` is still
   reported beside it, because a reader needs to know where in the run they are.
2. **A resumed run carries the count forward.** `gaf run --skip-coded <dir>` reads that
   directory's store. A **decided** checkpoint there (applied, rejected or no-op — a
   rejection is a look) resets the count to the responses coded after it; no checkpoint
   means every response that run coded, plus whatever it had itself carried, is still
   owed a look; a missing or unreadable store means the command cannot establish it, and
   it says so on stdout and in `run.json` and counts conservatively, as though no
   checkpoint had been taken. `RunStats.responses_since_checkpoint` records where the
   run ended up.
3. **The spike rule does not fire before it has a baseline.** The first `spike_window`
   batches raise no `Spike` at all. `handover.new_codes` is the rule that speaks there,
   and the batch's reason says that the ratio rule has no baseline yet, once.

**Consequences.**

*What this buys.* The verdict column carries information again: `floor` now means "a
human has not looked for fifty responses", and taking a checkpoint clears it. The
handover row and the spike row no longer report one condition under two names, so the
`fired` list and `spike_detected` mean what they say.

*What it costs, and what a reader must still know.* Within a single uninterrupted run
that never takes a checkpoint, `responses_since_checkpoint` still grows monotonically,
so every batch after the floor was first crossed still reports due and
`checkpoint_due.batches_due` still lists them. That is a true statement about a codebook
nobody has looked at, not a latch; the latch was the part that survived a checkpoint.
Separately, on the 200-response corpus the machine run's reported spike count falls from
three to zero and the human coding's from one to zero. No batch behaved differently: the
counts that used to be attributed to the spike rule were the absolute ceiling's, and are
still reported under `handover.new_codes`. Any figure quoting "three spikes" from an
earlier export is quoting the double count.

---

## ADR-0041 — `gaf analyse` needs the run to cut the run's curve, and patterns read the unfiltered matrix

**Status:** accepted (fix pass F1, from the R1 correctness audit)

**Context.** `gaf analyse` reads a row-oriented assignments file, which knows nothing
about the process that produced it. Two consequences, both measured.

*The growth curve was cut on the wrong universe.* A response the fast loop coded to
nothing — a duplicate, or one whose every candidate was dropped on an unverifiable
quote or an `UNNECESSARY` ruling — leaves no assignment row, so it was absent from
the curve, and every batch after it was cut one response early. `code_growth`'s own
docstring warns about exactly this and takes `order=` and `response_ids=` for it; the
only caller passed neither. On the 14-response synthetic corpus, at the first attempt:
`gaf analyse` reported batch 2 as three responses and a rate of 0.667 where the run
itself reported four and 0.500. The batch size was taken from
`AnalysisConfig.saturation_batch_size` rather than the run's own, so a run coded at
`--batch-size 4` produced two different growth curves, and two different spike verdicts,
for one coding.

*Patterns were filtered.* `build_patterns` documents itself as unfiltered on purpose
— a pattern view exists to show which codes travel together, **including** the rare
ones — and its only caller handed it the low-frequency-filtered matrix. On the
PI's own corpus that removed exactly the long tail his pattern-mapping question is
about: 109 codes became 68.

**Decision.**

1. **`gaf analyse --run <run.json>`.** It supplies the order the run processed in, the
   responses it coded to nothing, its own batch size and its own checkpoint policy. The
   curve is then the curve the run's decision trace, handover verdicts and timeline are
   keyed to. `Makefile` and `scripts/run_full_results.sh` pass it.
2. **Without it, `growth.md` says so, at the top.** A curve cut on the rows themselves
   is still a curve over a coding — it is the only one available for a hand coding
   from a spreadsheet, which is a real and supported input — but it is not the run's,
   and an artefact that cannot tell the reader which one it is would be worse than
   either.
3. **Patterns are built over the unfiltered matrix**; clustering, the heatmap and the
   affinity map keep the filtered one. `PatternReport.filter` records which ran, so the
   two code counts differ on purpose and the artefact says why.

**Consequences.** The two growth curves a run can produce now agree, or say which is
which. `11-patterns.md` in the regenerated results reports 109 codes rather than 68, and
with the rare codes back the pattern groups fall from three to two and the responses
with a unique family signature rise from 33 to 35 — the long tail makes more
signatures unique, which is the finding the filter had been hiding.

---

## ADR-0042 — The Definer: a verbatim segment is a quote at any length, and the prompt registry is one place

**Status:** accepted (fix pass F1; amends ADR-0013 for the Definer and ADR-0034)

**Context.** Two findings about `gaf.agents.definer`, both from the R1 audit.

*D3 was defeated by a full stop.* It compared `normalise_for_match(description)` against
`normalise_for_match(segment)`, and that function folds case and whitespace and leaves
punctuation alone. A verbatim copy of a segment with a full stop added, or capitalised,
matched neither — and below `MAX_SHARED_WORD_RUN` (8) words D4 does not fire either,
so a short segment reached the description field, and through it
`organised_shareable.md`, with no finding at all. Even when D3 did fire it was a WARN
and the text was written anyway.

*The loader did not know about `definer-v1`.* `gaf.agents.prompts.loader`'s own first
sentence is that it is the one place that knows which prompt versions exist; the Definer
resolved through a private registry inside `gaf.agents.definer`, so the sentence was
false. ADR-0034 had a reason: `loader.all_templates()` feeds the golden manifest's
`prompts` block, whose claim is "every coding in this fixture was produced under this
wording", and the Definer produces no coding.

**Decision.**

1. **D3 compares word tokens** — `word_tokens(description) == word_tokens(segment)`
   — which subsumes the punctuation and capitalisation cases in one comparison
   rather than enumerating them.
2. **D3 is an ERROR.** ADR-0013 ruled WARN on the same defect in **S1**, where the
   reasoning was explicit: dropping a *candidate* would destroy evidence over a
   formatting complaint. Nothing is destroyed here. A refused Definer description leaves
   the code undescribed, which S6 already reports as a WARN of its own, and the question
   D3 asks is D4's — not "is this a good definition" but "is this string shareable".
   A whole segment reproduced is a quote whatever its length. ADR-0013 stands as written
   for S1.
3. **`definer-v1` is registered in the loader** with the other three, and
   `tests/test_golden.py` filters the manifest's `prompts` block to
   `loader.LOOP_ROLES`. ADR-0034's reasoning was right about the *manifest* and wrong
   about the *loader*; putting the filter where the claim is made satisfies both, and
   the golden fixture does not change by a byte.

**Consequences.** A live Definer that echoes a short segment is now refused rather than
flagged, which is one fewer description and one fewer route into a shared document. The
offline mock interleaves counts between words by design and cannot trip either guard, so
nothing in the test suite or in `make results-full` changes. `gaf.agents.definer`'s
`DEFINER_TEMPLATES`, `DEFINER_RENDERERS` and `DEFINER_LATEST` remain as views onto the
loader's registries, so nothing that imported them has to change.

---

## ADR-0043 — A checkpoint id carries an ordinal where a checkpoint can legitimately repeat

**Status:** accepted (fix pass F1; the same rule as ADR-0018)

**Context.** `gaf.ids.checkpoint_id` hashed `(run_id, at_response_count, trigger,
base_snapshot_id)`, and `Blackboard.write_checkpoint` inserts `ON CONFLICT DO NOTHING`.
The documented happy path produces two checkpoints that tie on all four: `gaf checkpoint
--run X` with no terminal uses `RejectAllGate`, writes no snapshot and codes nothing,
and prints "re-run with `--interactive`"; the operator does, and `--trigger` defaults to
`manual` both times. The second row collided with the first and was silently discarded,
so `read_checkpoints` returned one record built from the *first* proposal and the *last*
events, the rejection — which the brief requires to be an entry, because a rejection
is a decision — disappeared, and `build_timeline` (which reads the audit log) and
`build_trail` (which reads the checkpoints table) disagreed about how many times the
gate had opened.

**Decision.** `checkpoint_id` takes an `ordinal`, exactly as `llm_call_id` does and for
exactly the reason ADR-0018 gives: content-addressed ids carry an ordinal where the
content can legitimately repeat. `write_checkpoint` increments it until the id is free,
so it is deterministic and is **zero** whenever there is no collision. Ordinal 0 hashes
the four fields alone, as before, so every checkpoint that never collided keeps the id
it already has and no stored run, committed result or example output moves.

**Consequences.** Two checkpoints are two rows, two trail entries and two timeline
markers. The fix is in the store rather than in the trail because the trail could not
have recovered the second proposal: it had never been written. The cost is that a
checkpoint id is no longer a pure function of its four identifying fields — a caller
cannot re-derive one without knowing how many preceded it — and no caller does.

---

## ADR-0044 — The crosswalk states description coverage, and the target roll-up has its own shape

**Status:** accepted (fix pass F1, from the R1 correctness audit)

**Context.** Two defects in `gaf.analysis.crosswalk`, both of which made a table read as
saying something it did not.

*The fairness flags were computed over the wrong set.* `source_has_descriptions` was
`any()` over **every code in the codebook**, while only the **leaves** are embedded. A
parent carrying a description was enough to set it, so `fair_mode_note` reported "no fairness
gap" on precisely the ADR-0029 comparison the flag exists to warn about: a source leaf
with no description against an identically named target leaf with one, scoring 0.3922
and banding `unmapped` — the same concept reported simultaneously as a machine
invention and a human blind spot, where `names_only=True` scores it 1.000 and `same`.

*The target roll-up reused the source roll-up's shape.* `FamilyRollup`'s three fields
counted three different populations on the target side: `n_leaves` target leaves,
`distribution` *source* leaves, `n_unmapped` target leaves again. Under identical column
headers the source table reconciled and the target table did not (3 — 4 + 2), and
`scattered` silently changed meaning between them.

**Decision.**

1. **Coverage, not presence.** The flags are computed over the leaves actually rendered,
   and the result records `source_described_leaves` / `target_described_leaves` beside
   the leaf totals. `fair_mode_note` claims "no fairness gap" only when both sides are
   fully described or neither is described at all; anything between states the two
   fractions and says that every pair where one side is bare is compared unfairly. A
   boolean per side cannot say this: one described leaf in a hundred is not a
   symmetrical comparison either.
2. **`TargetFamilyRollup` is its own dataclass**, with its own JSON keys and its own
   column headers: target leaves, source leaves landing here, source families, blind
   spots. `scattered` becomes `drawn_from_several_families`, because the mirror of "this
   family's leaves land in several families" is "several families land on this one", and
   two different questions should not share a column name.

**Consequences.** On the real comparison both codebooks are fully described, so the note
changes wording and not verdict. `13-crosswalk.md`'s second table gains a column and
reconciles. Anything reading `target_family_rollup` from the JSON must read
`n_blind_spots` where it read `n_unmapped`; `scripts/export_results.py` is updated with
it.

---

## ADR-0045 — Triple candidates are ranked by their exact support bound before the cap cuts them

**Status:** accepted (fix pass F1, from the R1 correctness audit)

**Context.** `gaf.analysis.patterns` bounds the Apriori-joined triple candidates at
`MAX_TRIPLE_CANDIDATES` (20,000). It sorted them by **code name** and sliced, scored
only that prefix, then re-sorted the survivors by support — so the table read as a
top-by-support list and was not one. The module docstring called the bound "unreached at
the stated corpus scale (a few hundred codes)". Measured, it is reached at this
project's own scale: 200 responses over 117 codes at twelve codes per response produce
about 57,000 candidates (65% unexamined), and at 130 codes and fifteen per response
about 139,000 (86%). A planted triple whose three constituent pairs were the top three
rows of the pairs table did not appear in `triples` at all.

**Decision.** Rank before truncating, by the **smallest of the triple's three pair
supports**. That is an exact upper bound on the triple's own support, since a triple
cannot occur more often than any pair it contains, so a candidate outside the kept set
cannot beat the last one kept. The code-name tuple breaks ties, so the cut stays
deterministic. The warning in the Markdown says the kept set is the highest-possible-
support candidates rather than "the first N lexicographically", and the module docstring
and the constant's comment now state the measured scale at which the bound bites.

**Consequences.** The bound becomes a principled prune rather than an alphabetical one,
and the table is a top-by-support list in fact as well as in appearance. It remains a
prune: at a small `min_support` over a dense codebook some candidates are still never
scored, and the report still says how many. Below the bound nothing changes, which is
why the regenerated results' triples are unchanged.

---

## ADR-0046 — A family tagged both ways keeps its own segments, and a description never travels without its source

**Status:** accepted (fix pass F1; ADR-0032 made structural)

**Context.** Two defects in `gaf.ingest.tagged`, found by the R1 audit.

*A family that carries both its own segments and subcodes lost every own segment.*
`_build_tree` discarded a family's `own_segments` whenever it had children, and `_code`
gated the evidence and the meta counts on `is_leaf`. Pairs `alpha — s1`, `alpha —
s3`, `alpha-child — s2`, all three placed exactly, produced `segment_count=3` and
`placements.mapped=3` beside **one** evidence row and `placed + unplaced = 1`. Two of
three coded segments vanished with no note, no anomaly and no count, and the suite's own
accounting invariant broke without any test noticing, because no fixture built a mixed
family.

*`to_codebook(descriptions=...)` attached descriptions with no provenance.* ADR-0032
decision 2 says the source is recorded "on every code that receives one"; that path read
it from `organised.meta`, which the path never sets.

**Decision.**

1. **`OrganisedCode.own_count`** is `count` minus the children's, which is exact by
   construction. A family's own segments are its own examples, its own evidence and its
   own `segment_count`/`placed_segments`/`unplaced_segments`, children or not. A family
   used both ways earns a `family_with_own_segments` note, because the shape is unusual
   enough that a researcher should be told rather than have it absorbed. Section 4 of
   the rendering iterates `codes_with_segments()` rather than `leaves()`: `leaves`
   answers a question about structure and this one answers a question about data, and
   the two differ by exactly this case.
2. **`to_codebook` refuses descriptions with no source.** It takes
   `description_source=`, falls back to `organised.meta["description_source"]` or the
   per-code `["description_sources"]` map, and raises when a description would be
   attached with neither. Making ADR-0032's rule structural is cheaper than auditing
   every future caller for it.

**Consequences.** The PI's own file contains no mixed family (measured: 0 of 15
families), so his counts do not move — 342 pairs, 117 leaves, 15 families, 1
consolidation, unchanged. The fix is a guard against a shape his coding could take and
his tool permits, not a correction to a number he has been shown. `organised.json` gains
an `own_count` on every code, and a caller passing `descriptions=` to `to_codebook`
without a source now gets a `ValueError` naming the flag instead of a silently
unattributed description.


---

## ADR-0047 — The provenance guard scans at the exporter's twenty characters, keeps short cells, subtracts the instrument and counts respondents

**Status:** accepted (fix pass F2, from the R2 privacy audit — findings C-2 and I-1;
extends ADR-0024 and applies ADR-0038 decision 1)

**Context.** Two guards in this repository ask the same question with two different
numbers. `scripts/export_results.py` has always used a 20-character shingle. The
repository-wide scan, `tests/test_golden.py::test_no_tracked_file_contains_real_respondent_text`,
used 30 — and, worse, discarded any source cell shorter than 30 **before** the needle
set was built, so a short answer was undetectable at any length whatever.

The independent privacy audit found what that gap was hiding. ADR-0016 quoted a
respondent to illustrate a mojibake bug: a **25-character** shared run, of which **19
characters were the respondent's own words** and 6 were the mis-decoded quotation marks
the real cell also carries. `docs/DECISIONS.md` is not the declared exemption, so three
statements this project makes in three places — `README.md`, the test that asserts the
exempt set is exactly one file, and `CONTRIBUTING.md`'s "no human survey response may
ever enter git history" — were false, and the guard was structurally unable to say so.
Measured against the principal investigator's own coding export (342 highlights): **84
normalise to under 30 characters**, and **50 sit in the 20-to-29 band** the old value
could not reach.

Lowering the number is one line. Making the guard *usable* at that number is the rest of
this entry: at 20 characters, over 737 distinct real answers about a subject this
repository is itself about, ordinary English collides. The first run of the lowered scan
produced 65 shared runs across 28 files, none of them a copy.

**Decision.**

1. **One constant, loaded rather than copied.** `PROVENANCE_SHINGLE` is
   `scripts/export_results.py`'s `GUARD_SHINGLE`, imported by loading the script by
   specification, the way `tests/test_export_results.py` already loads it. A test
   asserts the two are the same number. Two guards that must not drift should not each
   hold their own copy of the thing they must agree about.

2. **A cell shorter than the shingle is kept whole, not discarded.** The needle set is
   bucketed by length: a cell at or above the shingle contributes every window of
   exactly that length, and a cell below it contributes itself, entire, in its own
   bucket, down to a floor of `PROVENANCE_MIN_CELL` (12). Below twelve a cell that has
   survived the "must contain whitespace" rule is a two-word fragment any English
   sentence reproduces by accident. This is the same shape `gaf.report.trail._RunWording`
   uses, one level up in words rather than characters (ADR-0039 decision 4).

3. **The survey question is the instrument, not an answer, and is subtracted.** It is
   the principal investigator's own text; it travels on every `Response` record; and
   respondents echo it back, so it is inside their answers too. Left in the needle set
   it charges three files that exist in order to reproduce it — `gaf/config.py`, which
   holds it as a frozen constant, `results/*/01-inputs.md`, which prints what was asked,
   and `examples/demo-run/corpus.json`, which carries it on every record. None of the
   three can be reworded, so the correction belongs in the needle set, and it is read
   from `gaf.config.QUESTION_VARIANTS` so a new variant is covered the day it is added.
   The subtraction is of the question, not of its neighbours: a window straddling the
   join between a respondent's own words and his echo of the question is his, and stays.

4. **A window two different respondents share is the corpus's language, not one
   respondent's words** (`PROVENANCE_MIN_SOURCES = 2`). A sentence copied out of one
   answer cannot appear in a second answer written by somebody else. This is the ground
   the audit applied by hand to 37 of its 75 runs, mechanised, and without it the scan
   at 20 charges "the difference between" in six modules and the principal
   investigator's own family name, rendered in prose, in his own imported definitions.
   Respondents are counted over **maximal** texts, because the 200-response export
   carries each answer twice — under `All` and again under `Trimmed` — and counting a
   trimmed cell as a second person is the one way this rule could hide a real copy.

5. **ADR-0016 is about bytes, so it now says bytes.** The quoted sentence is replaced by
   the byte description the entry already gave: `E2 80 9C` read as MacRoman renders the
   three-character sequence, and the cell reads that sequence wrapped around a short
   sentence the entry does not need. **`PROVENANCE_EXEMPT` is untouched.**
   `docs/CODING_RULES.md` remains the one exempt file, by the principal investigator's
   decision (ADR-0024 §3), and the test that asserts it is the only one stays true.

6. **A ruled coincidence is reworded, never exempted** — ADR-0038 decision 1, applied
   fifteen times instead of once. The guard's job stays narrow: find every candidate. A
   person rules each one, and where the colliding string is the build's own invention,
   rewording is the answer. No baseline file, no ruled-phrase registry, no per-file
   allowance: each of those would be a place a real paste could later hide, and a
   registry of ruled runs would itself be a tracked file full of respondent fragments.

7. **The failure message is a location and a length, never the run.** The old message
   printed 64 characters of the offending file, which is respondent text going to a
   terminal, a CI log and a scrollback buffer, none of which is gitignored and none of
   which `make scrub` empties. It now prints the path, the offset into the file's
   whitespace-collapsed, case-folded text, and the run length. This is the same change
   the exporter took for the same reason (R2 M-2).

**The rulings.** Run lengths only; no word of any response appears here or in the fix
pass's report. 65 shared runs over 28 files, every one classified:

| class | runs | files | run lengths | ruling |
|---|---|---|---|---|
| The declared exemption, `docs/CODING_RULES.md` | (excluded) | 1 | up to 73 | Unchanged. The principal investigator's decision, ADR-0024 §3. |
| Undeclared respondent text, `docs/DECISIONS.md` ADR-0016 | 1 | 1 | 25 (19 of them the respondent's) | **De-quoted.** Decision 5. |
| The survey instrument | 32 | 4 | 20-21 | **Not respondent text.** Subtracted from the needle set, decision 3. |
| The corpus's language — shared with 2 to 9 different respondents | 12 | 11 | 13-29 | **Coincidence, proved by multiplicity.** Cleared by decision 4. The longest, at 29, is shared with 8. |
| Single-respondent coincidences | 21 | 15 | 19-29 | **Coincidence, reworded.** Decision 6. Every one sat in a module docstring, a source comment, an invented test fixture, a CI step name or a prompt template's subject sentence; none reproduced any clause of a real answer beyond a generic collocation. |

**Consequences.**

*What this buys.* The guard now sees the band a quarter of the principal investigator's
own highlights live in, and it sees short answers at all. Run against the pre-fix
ADR-0016 paragraph recovered from `main`, it still flags it — all six of that run's
windows are unique to a single response, so neither the instrument subtraction nor the
multiplicity rule weakens the catch that motivated the change. That regression was run
before decision 4 was adopted and is the reason a word-boundary rule was **rejected**:
aligning windows to whole words is superficially attractive and would have missed
ADR-0016 entirely, because the mis-decoded quotation marks glue themselves to the words.

*What it costs.* Fifteen files were reworded to clear a coincidence, including a
docstring in the frozen contract `gaf/models.py` (a comment-only amendment, the ADR-0026
precedent) and the subject sentence of the Coder's system prompt, which now says "AI"
where it said the phrase in full. The prompt edit moves one line of
`tests/fixtures/golden/manifest.json` — the `coder/coder-v1` digest — which is the
manifest doing exactly what it exists for. `codebook.json`, `assignments.json`,
`snapshots.json` and `findings.json` are byte-identical.

*What remains open.* Decision 4 is a judgement, and it is the load-bearing one: a copy
that happens to consist only of phrasing at least two respondents both used would pass.
That is a narrow hole and it is the price of running at 20 characters at all; the
alternative measured here — running at 30 — is the hole this entry closes. The guard
also remains, as ADR-0038 decision 1 says, a finder of candidates and not a judge of
them: every future hit is a person's ruling, and the right answer to an invented string
is still to reword it.

## ADR-0048 — The default live registry names models that exist, at prices read on a stated date

**Status:** accepted (PI feedback pass, from the live-run cost estimate of 23 September
2026; amends the frozen contract `gaf/config.py` additively, on the ADR-0015 precedent)

**Context.** `--live` swaps in `DEFAULT_LIVE_REGISTRY` unconditionally and reads no other
registry: `gaf/cli/_common.py` has no flag for one, so that constant *is* the live
configuration. It had two defects, and neither could be found offline, because no test
and no CI job ever builds a provider client.

The first would have stopped a live run dead. `coder_b` named `gemini-2.0-flash`, which
Google's own deprecation page lists with a shutdown date of **1 June 2026** — nearly four
months before this entry — and which no longer appears on its pricing page at all. The
failure would have landed on the *second* call of the first response, after the coder-A
call on the same response had already been paid for.

The second would have been quieter and worse. Prices live only on `ModelSpec`, which is
the point: `cost_usd` is computed nowhere else, and `stats.llm.cost_usd` in a run report
is whatever those four pairs say. Three of the four were wrong. `coder_b` carried the
retired model's rates. `judge` carried 3.00 / 15.00 where Claude Sonnet 5 is 2.00 /
10.00, and `refactorer` carried 15.00 / 75.00 where Claude Opus 5 is 5.00 / 25.00 — the
rates of an Opus generation that has since been retired. Run against the measured call
profile of `runs/process200` (2,278 calls; 1,876 of them the judge's fit check), the four
stale numbers price the full corpus at about 54% above what it would actually cost. A
number that is wrong by half, printed beside a coding, is worse than no number.

Neither defect was detectable by reading the file, because the prices carried no date. A
rate with no date cannot be checked, only believed.

**Decision.**

1. **The four bindings are the ones the providers themselves published on 23 September
   2026**, each read from that provider's own page on that date:

   | Role | Provider | Model id | Input $/Mtok | Output $/Mtok | Source |
   |---|---|---|---:|---:|---|
   | `coder_a` | openai | `gpt-4o-mini` | 0.15 | 0.60 | `https://developers.openai.com/api/docs/pricing` |
   | `coder_b` | gemini | `gemini-3.6-flash` | 0.75 | 3.75 | `https://ai.google.dev/gemini-api/docs/pricing` |
   | `judge` | anthropic | `claude-sonnet-5` | 2.00 | 10.00 | `https://platform.claude.com/docs/en/about-claude/pricing` |
   | `refactorer` | anthropic | `claude-opus-5` | 5.00 | 25.00 | same |

   `gpt-4o-mini` appears on OpenAI's deprecation page in none of its own rows (only its
   transcribe, audio and realtime variants are deprecated), and both Anthropic ids are
   current on the pricing page above. Only one id had to move.

2. **`coder_b` takes `gemini-3.6-flash` because Google names it the replacement**, on the
   same deprecation page that retires `gemini-2.0-flash`. Two newer Flash models
   (`gemini-3.7-flash`, released 13 August 2026; `gemini-3.8-flash`, 2 September 2026)
   are on the pricing page at the *same* list rate and with no announced shutdown date,
   so this is not a cost choice — it is a defensibility one. "We used the replacement the
   provider documented" needs no methodological argument in a methods appendix; "we used
   the newest thing available on the day" needs one. Secondary web sources naming a 2.5
   Flash successor were read and discarded: the provider's own page is the source of
   record.

   The rate is introductory. Google states 0.75 / 3.75 **through 31 December 2026** and
   1.50 / 7.50 from 1 January 2027. The registry is therefore known to be wrong from that
   date, which is exactly the kind of thing decision 3 exists to make visible.

3. **`ModelSpec` gains `priced_on`, and `to_json()` omits it when it is empty.** The field
   is additive with a default of `""`, so every existing construction of a `ModelSpec` is
   unchanged and `MOCK_REGISTRY` carries no date, which is correct: a mock has no price to
   date. The omission is deliberate and is the reason this entry does not move a single
   byte of offline output. `RunConfig.to_json()` is compared **verbatim** by
   `Blackboard.register_run` before a run id may be continued, and it is committed, in
   full, in `tests/fixtures/golden/manifest.json` and rendered into
   `examples/demo-run/report.txt`. A key emitted unconditionally would have moved the
   golden fixture and the committed example to record an empty string about a model that
   costs nothing. Emitted only where a price date exists, it travels with every live run —
   the store, the manifest and the report all carry the date its rates were read — and
   with no offline one. `gaf.cli._common._run_config_from_json` needs no change: it
   already filters an incoming spec by `ModelSpec.__dataclass_fields__`, so the new field
   round-trips by name, and a test asserts the round trip is exact.

4. **Four assertions stand between these numbers and a silent drift**, in
   `tests/test_contracts.py` and `tests/test_cli.py`: every model id in both registries
   matches its provider's own prefix convention (`gpt-`, `gemini-`, `claude-`, `mock-`),
   which is what the retired id would *not* have failed and is therefore a guard against
   the next mismatch rather than this one; `distinct_coder_providers()` still holds, since
   it is the epistemic-diversity mechanism and not a preference; the four price pairs and
   their `priced_on` date are pinned to this entry; and a live-registry config survives
   the JSON round trip byte for byte, which is what `Blackboard.register_run` requires.

5. **The triple itself is not re-chosen here.** `claude-sonnet-5` and `claude-opus-5` keep
   their slots because both are current, not because they are optimal — Anthropic's
   pricing page also lists a newer Opus 5.5 tier at 4.00 / 20.00. Which models code this
   corpus is the principal investigator's decision and belongs in a methods appendix; this
   entry only makes the registry runnable and its arithmetic honest.

**Consequences.**

*What it buys.* A live run can now be started at all, and the `cost_usd` it prints can be
reconstructed by anyone who reads this entry: four rates, four sources, one date. The
cost estimate's recommendation (the registry's own triple with the retired id replaced)
and the registry now agree, so the budget the PI approves is the budget the code would
spend.

*What it costs.* A second additive amendment to a frozen contract, after ADR-0015. The
conditional key in `to_json()` is a small asymmetry — the serialisation of a `ModelSpec`
is no longer a plain `asdict` — and it is the price of leaving the golden set untouched;
`CheckpointPolicy.to_json()` already customises its output, so the shape is not new.

*What remains open.* Prices decay, and this entry dates them rather than fixing them: the
Google rate has a **known** step on 1 January 2027, and any of the four may move sooner.
Re-pricing is another ADR and another commit, and the pinned test is what will force one.
`gaf/config.py` is still the only place a triple can be changed — there is no CLI flag
for a registry, and this entry does not add one. The live path remains unexercised by any
test, by design (`CONTRIBUTING.md`, "The offline rule"), so these bindings are verified
against the providers' documentation and not against the providers.

---

## ADR-0049 — Models served on this machine are a provider, and "local" means the words stay here

**Status:** proposed (branch `local-models`, 25 September 2026; amends the frozen contract
`gaf/config.py` additively, on the ADR-0015 and ADR-0048 precedent)

**Context.** Three things were true at once. The live run was still waiting for the PI's
approval, so the live path — real replies through `parse_json_object`, the whitelists and
the fail-safes, and a real embedding space under M1–M3 — had never run against a model at
all. ADR-0019 and ADR-0022 left one question open that only a real embedding space can
answer: whether M3's code↔evidence fit check can discriminate, and so whether the judge
stays 64–80% of the bill. And the live run itself could not choose an embedding space:
`--live` swapped in `DEFAULT_LIVE_REGISTRY` and left `RunConfig.embedding` at the lexical
fallback, with no flag for either (ADR-0048, "What remains open").

Models that run on the laptop this pipeline is developed on answer all three without a key, a bill
or a decision about sending respondents' words to a new company. On the Apple M4 Pro with
24 GB this project runs on, Ollama serves 9–12B chat models and every current open
embedding model through the same OpenAI-compatible endpoints the hosted providers use.
The largest open families do not fit: Kimi K2.6 and K3 are trillion-parameter mixtures
whose smallest usable builds need hundreds of gigabytes, and Ollama offers them only as
*cloud* models, which are hosted and therefore not local in the sense below.

**Decision.**

1. **`"local"` joins `Provider`, and `"local"` joins `EmbeddingSpaceConfig.mode`.** Both
   are additive `Literal` members; no default, no existing value and no serialised byte of
   an offline run moves. A local model is priced at zero because nothing is billed; its
   token counts are still recorded, because they are what the same prompts would cost on
   a hosted model.

2. **One module decides where "local" is, and refuses anywhere else.**
   `gaf/local_endpoint.py` reads `GAF_LOCAL_BASE_URL` (default Ollama,
   `http://localhost:11434/v1`) and raises unless the host is a loopback address or
   `GAF_LOCAL_ALLOW_REMOTE=1` is set. The provider's name is a privacy claim — no
   respondent's words leave the machine — and a hosted Kimi, Qwen or DeepSeek endpoint
   speaks the same protocol, so the claim has to be enforced where the URL is read, not
   assumed from the name. Sending the corpus to a new provider stays the PI's decision.
   `GAF_LOCAL_API_KEY`, when set, is sent as the bearer token, so the same client can
   reach a hosted OpenAI-compatible endpoint under that override — for trying a model
   such as Kimi on the synthetic corpus, never the real one without approval.

3. **`LocalClient` is `OpenAIClient` with a standard-library transport.** Same request in
   JSON-object mode, same parse, same whitelist, same fail-safe, same `LLMError` on a dead
   server; no SDK and no extra. It removes `<think>` blocks before parsing, because a
   reasoning model's scratch work routinely contains braces and would capture
   `parse_json_object`'s outermost-`{…}` rescue, and it asks the server not to think.

4. **Two local coders must come from different model families.** Every local model has
   the provider `"local"` — the server, not the maker — so `distinct_coder_providers()`
   would refuse every all-local registry. The epistemic-diversity rule is about training
   lineage, so for two local coders it is applied to the maker's family instead
   (`qwen3.5:9b` against `gemma4:12b` passes; `qwen3.5:9b` against `qwen3:8b` does not).
   `ModelRegistry.distinct_coder_providers` itself is unchanged; the CLI's
   `coders_are_distinct` wraps it.

5. **`--profile JSON` replaces the default live registry for one run, and may carry an
   embedding space.** Its shape is the `models` and `embedding` blocks of a run's echoed
   config, so any run's configuration can be copied out and re-run. It requires `--live`.
   The run records the profile's registry and derived space id like any other, so a
   profile run is exactly as auditable as a default one. `profiles/local-ollama.json`
   ships as the example, and every shipped profile is tested to load with distinct coders.

6. **A local run checks its server and every model before it starts**, and names the
   `ollama pull` that would fix a missing one, so a typo costs a second rather than a
   segmented corpus.

**Measured, 25 September 2026.** Embedding spaces scored against the PI's coding (295
highlights, 131 codes; `scripts/compare_embeddings.py`, aggregates only): every real local
model puts the PI's code first 2.5–3.5× as often as `lexical-v1-512` on names alone (0.29–0.42
against 0.12). With descriptions, `embeddinggemma` led (top-1 0.65, fit AUC 0.92) and cut
the share of wrong pairs passing at a 90%-recall cut from 1.00 to 0.25. A 10-response pilot
with `profiles/local-ollama.json` made 115 calls with 0 fail-safes, at $0, in 1,051 s. The
M3 fit escalations of the offline run (103 of 104) fell to 0 of 67. But the grey zones
of M1 and M2 took their place (39 disputes, 56 of 64 routes), so judge calls per response
went from 10.3 to 9.5. The thresholds were set for the lexical space. ADR-0019's
calibration step, in the chosen space, is what moves the judge's share, not the space
alone. The run also produced 60 codes from 10 responses (the PI used 47 on them), which
is over-splitting from a τ_high that almost nothing in this space reaches.

**Consequences.**

*What it buys.* The live code path can be exercised end to end, on the real corpus, today,
for nothing, with the words never leaving the machine. An embedding space can be chosen by
measuring it against the PI's own coding (`scripts/compare_embeddings.py`) instead of by a
leaderboard. And `--profile` closes ADR-0048's open item: a triple, or an embedding space,
can now be changed without editing a frozen contract.

*What it costs.* A third additive amendment to `gaf/config.py`. A local model is a weaker
coder than the hosted triple, so a local run's agreement numbers are evidence about the
*pipeline* with a small model in it, not about what the approved triple would find; the
two must never be pooled or compared as if they were the same instrument. On a 24 GB
laptop the judge and refactorer have to share a family with one coder, which weakens the
third-lineage principle for local runs, and the profile says so in its description.

*What remains open.* Local models are slow: minutes per response where a hosted model
takes seconds. Whether a local embedding space is good enough to be the canonical one for
the live run is a decision for the PI, with the comparison in hand; this entry
makes it possible to choose, and does not choose.

---

## ADR-0050 — The PI's rulings on his export: the workbook is canonical, ambiguous highlights go into every coded candidate, a typo is merged provisionally, and one file records what each ruling changed

**Status:** accepted (live-run-oct04, 4 October 2026; extends ADR-0029 and ADR-0031 by
opt-in additions; corrects one sentence of ADR-0031; amends no frozen contract)

**Context.** The PI answered the questions the 22 September feedback left open. In
substance: the `.xlsx` is the canonical tagged export, not the `.csv`; `efficiency` is a
top-level code; the near-miss label pairs are likely typos and he asked to see the list;
and the ambiguous highlights should be included, since a fragment may be coded in more than
one place. Each answer moves a count, and the organiser (`gaf codebook organise`) had
nowhere to put a decision of his: it flags what looks odd and merges only trivial variants
(ADR-0031, `gaf.ingest.tagged`). This entry records the decisions, the mechanism that
carries them, and a measurement that contradicts a sentence in ADR-0031.

**Three files, compared by counts only.** The `.xlsx` in `data/` (12 September), the
`.xlsx` of the same name in `codebook/` (11 September, different hash) and the `.csv`
beside the first all hold the same **342 pairings and the same 117 distinct tags**. No tag
is in one and not another, and no row's content differs, before or after the encoding
repair. They differ in order and columns only. The `codebook/` workbook and the `.csv` are
in the order the codes were applied (the csv has 338 contiguous tag runs). The canonical
`data/` workbook groups the rows by tag (117 runs, one per tag, segment order inside a tag
unchanged), carries three extra columns (`count`, `Claude1`, `Claude2`) and fifteen rows
with neither tag nor content, which the reader already skipped. `read_tagged_pairs` reads
columns by header name, so it reads the canonical workbook as 342 pairings with no change.
Switching the file alone moves no count: `golden.json` and `codebook.json` are
byte-identical to the csv's. What does change: every source row number cited in earlier
notes was the csv's; index-based highlight ids are different labels for the same highlights;
and the pipeline's "is the export's row order the coding order?" check (step 3d of
`scripts/run_full_results.sh`) asks a question the grouped workbook can no longer answer.

**Decision.**

1. **The `.xlsx` in `data/` is the canonical tagged export.** `Makefile` (`FULL_TAGGED_EXPORT`,
   renamed from `FULL_TAGGED_CSV`), the runbook and the full-results script point at it.
   The baseline run `runs/human200`, built from the csv, is kept as it is and is
   reproducible; the new organisation goes to `runs/human200-v2`.

2. **One rulings file, read by `organise` (`--rulings PATH`).** It is JSON, names labels and
   flags and never respondent text, and so is tracked (`rulings/india-process.json`, with
   a one-line `description`). Keys: `top_level`, `label_merges` (each with a `provisional`
   flag), `label_merges_held`, `multi_place_ambiguous`, `manual_placements` and
   `manual_placements_file`. Unknown keys are refused: a mistyped key in a file that
   changes a coding must not be read as "no ruling". **Without `--rulings`, every output is
   byte-identical to before** (checked on the csv against a baseline from the unmodified
   tree). **With it, every ruling applied is recorded beside the count it moved:** in
   `organised.json` (`meta.rulings`), in the markdown renderings, in the printed counts,
   and in `rulings_applied.json`, which carries labels, counts and ids and no text.
   `gaf codebook define` re-reads the same file and refuses if it changed since `organise`,
   because it re-derives the organisation and would otherwise describe codes the directory
   does not hold.

3. **`efficiency` is a top-level code.** It already was one structurally (no hyphen, so a
   family of its own with no subcodes). What was open was the *note*: `bare_top_level_code`
   called it something that "may want splitting", and the results exporter turned that into
   a question for him. A label in `top_level` is no longer noted as bare, is recorded in the
   trail with its count and subcode count, and carries `meta.ruled_top_level` in
   `codebook.json`. Nothing needed re-parenting. The structural check S3 still warns on
   every use after the first (10 warnings on the baseline, 12 on the new run, the same
   warning on `efficiency` repeated); teaching it to read `ruled_top_level` is open.

4. **A label merge is a recorded, provisional consolidation.** It is applied after the
   trivial rules (case, whitespace, family separator), rewrites a label onto the canonical
   spelling (the correctly spelt one, else the more frequent), is stored as a
   consolidation with `ruling: true` and `provisional: <flag>`, and may rename a label
   whose correct form was never written. A definition keyed by the old spelling is carried
   to the new label if that label has no definition of its own, so a ruling can never
   replace a definition he wrote. *The reading of "the eight pairs are typos" matters.* The
   eight pairs the organiser finds are two label pairs and six token pairs. **Only one,
   `safety` against `saftey`, is a misspelling.** The others are different words two edits
   apart: `deskilling` and `upskilling` have opposite meanings and sit in the families
   `negative_impacts` and `positive_impacts`; `education` and `reduction` are unrelated; `safety-home` and
   `safety-women` are two subcodes of one family; `assistance` and `assistant` are in two
   separately defined codes; `research` and `search` are two defined codes; `impact` against
   `impacts` is a family beside two other families. Merging all eight literally would
   collapse codes he defined separately and rewrite family names. So the rulings file
   **applies one merge, provisionally, and lists the other seven under
   `label_merges_held`** with a reason each, recorded in the trail as "held, not merged".
   The pair is shown to him in the private review pack with the canonical spelling a merge
   would take, for his answer by number; promoting a held pair is a one-entry change.

5. **Ambiguous highlights: an opt-in rule that places a highlight in every coded
   candidate.** "Ambiguous" means the same highlighted text occurs in more than one
   response, so the tool cannot tell which was meant. It does not mean one fragment
   carrying two codes, which was always supported. With `multi_place_ambiguous: true`, a
   highlight that is still ambiguous after both passes and has **two or more candidates
   in the coded set** is placed in *every* such candidate, outcome `multi_placed`: one
   mapping row per response, one highlight, so `placed_segments` counts it once and the
   evidence carries a verified quote in each response. A highlight with no candidate in
   the coded set stays excluded, and one with exactly one is `resolved` as before. The
   coded set is a fact about pass one and the outcome does not depend on row order. The
   rule is off by default; `HIGHLIGHT_OUTCOMES` gains `multi_placed` and `manual`, and the
   placement report gains keys for them only when a ruling switched them on.

6. **A manual placement is applied after both passes, with outcome `manual`.** The mapping
   is `{highlight id: response id}`, inline in the rulings or in a file
   (`manual_placements_file`, or `--manual-placements`). The real file holds ids only, but
   it is the PI's answer about his own data, so it lives under `runs/` (gitignored by
   convention; `.gitignore` also names `manual-placements*.json`). **A file that is absent
   is a no-op**; one that is present and malformed stops the command. It replaces whatever
   the highlight was placed as and records what that was; the response named gets the
   locator's nearest span at threshold 0 and the score it earned, unrounded. An id that
   matches no highlight, a response not in the corpus, or text that cannot be given a span
   is listed as not applied with the reason, never guessed at. The coded set is not
   recomputed from manual placements.

**Measured, 4 October 2026** (the canonical workbook on the 200-response corpus; counts
only). Of the 24 highlights still ambiguous after pass two, split by candidates inside the
coded set of 39:

| candidates in the coded set | highlights | candidates outside it |
|---|---|---|
| 0 | 17 | 2 to 14 |
| 1 | 0 (those 7 were already `resolved`) | |
| 2 | 6 | 1, 1, 1, 2, 4, 6 |
| 3 | 1 | 23 |

**This contradicts ADR-0031**, whose measurement paragraph says the 24 "have more than one
candidate inside the coded set in every case". Seventeen have none. The sentence was not
reproduced when the 24 were counted. The multi-placement rule therefore recovers **7
highlights in 15 placements**, not 24, and leaves 17 excluded. Sixteen of those 17 have
both response 133 and response 571 among their candidates, neither of which is in the coded
set, and 571 contains the wording of 133, 339 and 217 almost entirely. The likely reading
is that the PI coded one of them and none of his highlights in it is unique enough to place
by text. That is a question for him, asked by number in the review pack, and the manual
placement above is how his answer enters.

Before and after (baseline `runs/human200` against `runs/human200-v2`): exact 304 and 304,
fuzzy 1 and 1, resolved 7 and 7, multi-placed none and 7 (15 placements), manual none and
0, ambiguous 24 and 17, unlocated 6 and 6, mapped 312 and 319, coded set 39 and 39,
`golden.json` rows 312 and 327 (the 15 added rows are all in already-coded responses),
codes in the golden set 109 and 109, families 15 and 15, leaves 117 and 117, near-miss
notes 8 and 7, bare-top-level notes 1 and 0, definitions matched 131 of 131 in both.

**Pre-registered split (P2.1), recorded here because it is drawn from this golden set.**
`runs/human200-v2/split.json` holds ids, the seed (20261004) and the method, and nothing
else; its sha256 is `0e77def6913194319797b25c866195ded2628227877396c6d383f10b3fd27939`. The
calibration fold is 20 responses: the ten pilot ids, which are fixed in it, and ten more
drawn by stratifying the others on distinct codes per response in three tercile bands,
each band taking the same calibration share. The held-out fold is the other 19. Responses
are chosen by id from the coded set, never by slicing the corpus. The split is
deterministic and re-running it writes the same bytes. It is **not** untouched by the
embedding choice: the 25 September comparison of eight embedding spaces scored all 295
highlights over all 39 coded responses, including the 19 held out. That is a selection
among eight spaces, not a fit, and the results page says so.

**Consequences.**

*What this buys.* Every decision the PI has made about his export is in one file he can
read and overrule, applied in one place, and recorded in the output next to what it
changed. The default is unchanged to the byte, so no earlier result moves. Seven more
highlights (fifteen placements) enter the evidence, with a stated reason and a distinct
outcome name.

*What it costs.* `multi_placed` is a weaker claim than `exact`, as `resolved` is: it says a
fragment belongs to each coded response its text occurs in, an inference from the coding's
coverage and not from the text. A multi-placed highlight puts the same code into two or
three responses, so the occurrence matrix and every agreement figure over the golden set
count it in each; a result quoted over the golden set should say that 15 of its 327 rows
are placements of 7 highlights. The two readings of "ambiguous" are easy to confuse, which
is why the review pack opens with three lines separating them.

*What remains open.* The seven held pairs await his answer. The 17 highlights whose
candidates are all outside the coded set await it too; if he says he coded response 571 or
133, the coded set becomes 40, `golden.json` grows by about 16 rows, and the pre-registered
split has to be extended and its hash re-recorded before any paid run. S3 still warns on
`efficiency`. The results exporter's README text still asks which export is canonical, asks
about the bare top-level code, and repeats ADR-0031's sentence about the 24; it also
reads only `exact`, `fuzzy` and `resolved` when it totals the mapped highlights, and will
understate a run that has `multi_placed` or `manual`.

---

## ADR-0051 — The Anthropic client speaks the 5-series: no sampling, effort per role, text blocks only, and an early stop is a fail-safe

**Status:** proposed (branch `live-run-oct`, 4 October 2026; amends the frozen contract
`gaf/config.py` additively, on the ADR-0015, ADR-0048 and ADR-0049 precedent)

**Context.** The PI chose Claude Opus 5.5 (`claude-opus-5-5`, $4 in / $20 out per million
tokens) for coder A, the judge and the refactorer; the Definer reuses the refactorer slot.
The Anthropic client could not call it. It was written for the request shape of the
Claude 4 era, and the 5-series changed that shape in ways that fail loudly or, worse,
quietly:

* **Sampling parameters are an HTTP 400.** On Opus 5.5 — and on Opus 5, Opus 4.7 and 4.8,
  Sonnet 5 and 5.5, and Fable 5 and 5.1 — any `temperature`, `top_p` or `top_k` is
  rejected, the default value included. The client sent `temperature` on every call.
* **Thinking is always on and cannot be disabled.** Its depth is set by
  `output_config.effort` (`low`, `medium`, `high`, `xhigh`, `max`); Opus 5.5's default is
  `medium`, one level below Opus 5's. Thinking tokens are billed as output and count
  against `max_tokens`, so a limit sized for a reply with no thinking can cut the reply
  off before it starts.
* **A reply opens with `thinking` blocks** before the `text` block.
* **A refusal is HTTP 200** with `stop_reason: "refusal"` and a `stop_details.category`
  (`cyber`, `bio`, `reasoning_extraction`, …). Opus 5.5 runs a broader classifier set
  than Opus 5. Prefill is rejected (the client never used it).
* **The SDK pin was too old.** `pyproject.toml` asked for `anthropic>=0.34`; the lock had
  resolved 1.2.0. The current line is 1.x on `httpx2`, in which `messages.create` and
  `messages.stream` have no `temperature` argument at all (passing one is a `TypeError`)
  and take `output_config`. On 4 October 2026 the newest release on PyPI was 1.11.0.

None of this could be found offline: no test and no CI job builds a provider client.

**Decision.**

1. **The SDK pin moves to `anthropic>=1.11,<2`**, in both the `anthropic` and `live`
   extras, and the lock to 1.11.0. It stays an optional extra that CI never installs. The
   OpenAI and Gemini clients and their tests are unaffected (`openai` 3.6.0 and
   `google-genai` 2.21.0 resolve beside it).

2. **Sampling parameters go only to the lines that accept them, by an explicit rule on
   the model id.** `accepts_sampling_params(model)` in `gaf/llm/anthropic_client.py` is
   true for the Claude 2 and 3 families and for Claude 4.0 to 4.6 (Opus, Sonnet, Haiku;
   bare or date-suffixed), and false for everything else — Opus 4.7 and later, Sonnet 5
   and later, Fable, Mythos, **and any id it does not recognise**. The default is to omit
   because the costs are lopsided: an omitted temperature fails nothing, while a sent one
   is a 400 on every model released since Opus 4.7. The older lines keep their old
   behaviour, `temperature` from the spec, sent through `extra_body` because the 1.x SDK
   dropped the argument. The rule is a function, not a `ModelSpec` field, because it is a
   fact about Anthropic's API rather than a choice a run makes: a field would be a second
   knob that could contradict the model id, and it would add a key to every run's config
   echo. A consequence to read correctly: an Opus 5.5 spec still echoes
   `"temperature": 0.0`, which on the 5-series means "not sent".

3. **`ModelSpec` gains `effort`**, an optional `Literal` of the five levels, default
   `None`, and `to_json()` omits it when it is `None` — the ADR-0048 pattern, so no byte
   of an offline run, the golden manifest or the committed example moves, and
   `_run_config_from_json` round-trips it by name. When set, it is sent as
   `output_config={"effort": ...}`; when unset, nothing is sent and the model's own
   default applies. A profile sets it per role, and `load_profile` refuses an unknown
   level and refuses `effort` on any provider but `anthropic`, where it would be recorded
   and do nothing. `profiles/opus-qwen.json` uses **coder A `medium`** (coding is the
   judgement the study measures, at the model's default), **judge `low`** (a one-word
   verdict on a short prompt, and the judge is 55 to 60% of the estimated bill), and
   **refactorer `high`** (one or two calls per checkpoint, each proposing edits a human
   will rule on; the Definer inherits it).

4. **`max_output_tokens` leaves room for thinking, through the profile**: coder A 8,192,
   judge 4,096, refactorer 16,000. They are ceilings, not costs; they were not set higher
   because a large ceiling buys nothing on these prompts and may count against an
   output-rate limit on a low tier.

5. **Only `text` blocks are read.** `thinking` blocks (empty under the default display)
   are skipped. Usage is recorded as before; output tokens include the thinking, which is
   billed as output, so `cost_usd` is the bill.

6. **A `refusal` or `max_tokens` stop on a JSON task is a fail-safe, recorded, and not
   retried inside the call.** The transport raises `IncompleteReplyError`, carrying the
   billed tokens and the refusal category; `complete_json` catches it inside the retried
   callable, so it does not count as a transport failure, and returns the task's
   non-destructive default (`FAIL_SAFE_DEFAULTS`: no codes, KEEP, CREATE, APPLIES, an
   empty edit script) with `fail_safe = True`. The result says why in three places:
   `llm_calls.fail_safe`, `data["_stop_reason"]` (and `_stop_category` for a refusal),
   and, for the judge and the refactorer, a `reasoning` of the form "fail-safe: the model
   stopped with refusal (bio)", which reaches the store with the verdict. The billed
   tokens are still counted. It is not retried in the call because a refusal is a
   property of the input and a truncation at the same ceiling is likely to repeat, while
   each retry bills the thinking again; it is not raised, because one refused response
   must not halt a 161-response run. It *is* retried on the next run: `CachingLLMClient`
   never stores a fail-safe, so "the existing retry path" for an early stop is a re-run,
   at the cost of that one call.

7. **The server-side `fallbacks` beta is not used.** Anthropic recommends opting into it
   for the 5-series, so that a refused request is re-run on another model inside the same
   call. Here that would be a silent change of coder: the `llm_calls` row, the agreement
   figures and the judge's lineage would all name Opus 5.5 for a reply another model
   wrote. Who coded what is the study's independent variable, so a refusal stays a
   visible fail-safe on the model the profile names, and its rate is a finding.

8. **Every request streams** (`client.messages.stream(...)` and `get_final_message()`,
   the SDK's documented pattern). The 1.x SDK refuses a non-streaming request it expects
   to take more than ten minutes (above about 21,000 `max_tokens`), and a refactor at
   `high` effort is the call most likely to run long. One code path, no timeout guard to
   trip.

9. **Tests, offline.** `tests/test_providers.py` pins the sampling rule on 22 ids, the
   request shape (no `temperature` or `thinking` on Opus 5.5, `output_config` only when
   effort is set, `extra_body` temperature on Sonnet 4.6), text-only reading, both early
   stops on every task type (fail-safe, recorded, billed, one attempt), and the live
   transport against a fake `anthropic` module that CI can run. One further test drives
   the real 1.11 SDK over an in-process `httpx2.MockTransport` serving a streamed reply
   with a thinking block, and checks the wire body itself; it skips where the SDK is
   absent.

**Consequences.**

*What it buys.* The PI's frontier model can be called at all, at the effort each role
needs, with a refusal or a truncation turning into the same non-destructive default a
malformed reply already did, and counted where the audit can see it. The billed cost of
thinking lands in `cost_usd`, so the smoke test measures the plan's largest uncertainty.

*What it costs.* A fourth additive amendment to `gaf/config.py`. The config echo's
`temperature` no longer means "what was sent" for the 5-series. Two things are recorded
less precisely than they could be, because their owners' files are frozen or owned
elsewhere: `llm_calls` has no `stop_reason` column (an additive `LLMResult.stop_reason`
and column would make refusals countable by SQL rather than by the fail-safe count), and
the response cache's key does not include `effort`, so a re-run under a different effort
would replay replies made at the old one.

*What remains open.* The refusal rate on this corpus is unknown until the smoke test; the
survey responses are about AI futures, not about biology or security, so it is expected
to be near zero. Prompt caching is unused: the coder's system prompt repeats on every
call, and Opus 5.5 caches prefixes from 512 tokens at $0.20 per million on a read; it
would cut coder-A input cost, and is left for after the first measured run because cache
writes change the cost accounting. `effort` levels are argued, not measured; a sweep on
the calibration fold would settle them.

---

## ADR-0052 — A hosted OpenAI-compatible model is its own provider, and never "local"

**Status:** proposed (branch `live-run-oct`, 4 October 2026; amends the frozen contract
`gaf/config.py` additively, on the ADR-0015, ADR-0048 and ADR-0049 precedent)

**Context.** The PI chose the newest Qwen, Qwen3.8-Max, as coder B. It is served by
Alibaba Cloud and by routers such as OpenRouter over the OpenAI Chat Completions
protocol — the same protocol `LocalClient` already speaks to Ollama. So it could have
been reached with no new code at all: point `GAF_LOCAL_BASE_URL` at the host, set
`GAF_LOCAL_ALLOW_REMOTE=1` and put the key in `GAF_LOCAL_API_KEY`.

That would have broken ADR-0049's central claim. There, `"local"` is a privacy claim —
no respondent's words leave the machine — and the run's config echo, every `llm_calls`
row and every report would have said `local` for a coder whose input went to a third
party in another jurisdiction. `GAF_LOCAL_ALLOW_REMOTE` exists for a deliberate,
recorded exception on the synthetic corpus, not as the configuration of a study's
coder. Sending the corpus to a new processor is the PI's decision, and the record of the
run has to name that processor.

**Decision.**

1. **`"openai_compatible"` joins `Provider`.** It is a hosted endpoint by definition; the
   name is what every echo, row and report carries. `OpenAICompatibleClient`
   (`gaf/llm/compat_client.py`) is `OpenAIClient` with the transport `LocalClient`
   uses: the request-and-parse body was extracted from `LocalClient` into
   `chat_completions_transport` in `gaf/llm/local_client.py` and both clients call it,
   so JSON-object mode, `<think>` removal, the whitelist, the fail-safe and `LLMError`
   on a dead server are one implementation, not two. Likewise the HTTP reading was
   generalised in `gaf/local_endpoint.py` (`read_json`, with an `EndpointError` base that
   `LocalEndpointError` now subclasses), with every local message and behaviour
   unchanged.

2. **Where the text goes is explicit and has no default.** `gaf/compat_endpoint.py`
   reads `GAF_COMPAT_BASE_URL`, which is required and must be `https` (respondent text
   does not cross the network in the clear), and `GAF_COMPAT_API_KEY`, which is required
   and sent as a bearer token. Both are checked when the client is built, so a missing
   one stops the run before anything is sent, with a message naming the variable. There
   is nothing to install: standard library only. `GAF_LOCAL_*` is never read by this
   provider, and `GAF_COMPAT_*` is never read by `local`.

3. **Thinking off, harmlessly.** By default the body carries `"enable_thinking": false`,
   the switch DashScope's compatible mode reads for a hybrid Qwen model (its JSON-object
   mode requires thinking off). A host that does not know the field ignores it;
   `GAF_COMPAT_THINKING_OFF=0` drops it for a host that rejects unknown fields instead.
   Any `<think>` block that arrives anyway is removed before parsing, as for a local
   model. Ollama's `reasoning_effort: "none"` is not sent: a router may map it onto
   something else.

4. **Two hosts are documented; the user chooses and verifies.** Preferred: Alibaba Cloud
   Model Studio, international, `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
   (the Singapore region; the user confirms the region on the account). Fallback:
   OpenRouter, `https://openrouter.ai/api/v1`, where model ids carry a maker prefix
   (`qwen/…`). A router is a further processor: text passes through OpenRouter and on to
   the upstream provider it selects, which the PI should know if the fallback is used.
   The model id string is the host's and is confirmed on the day; it is recorded in every
   `llm_calls` row and in the config echo.

5. **The coder-diversity rule treats `openai_compatible` like `local`.** Both name a
   server, not a maker, so whenever either coder is bound to one of them the two coders
   must come from different model families (`coder_family`, from the model id for a
   server provider and from the provider for a maker). Opus 5.5 beside a hosted Qwen
   passes; two hosted Qwens fail; a local Qwen beside a hosted Qwen fails (one family on
   two servers); and a Claude reached through a router (`anthropic/claude-…`) counts as
   Claude. Two hosted makers keep the provider rule. `ModelRegistry` is unchanged.

6. **The local loopback guard is unchanged, and a test says so**: with the hosted
   endpoint configured, a hosted URL in `GAF_LOCAL_BASE_URL` is still refused for
   `local` without `GAF_LOCAL_ALLOW_REMOTE=1`, and `LocalClient` still sends Ollama's field
   and not the hosted one.

7. **Profiles.** `profiles/opus-qwen.json` is the PI's line-up (Opus 5.5 on coder A, the
   judge and the refactorer; `openai_compatible` `qwen3.8-max` on coder B; local
   `embeddinggemma`, 768-d). `profiles/opus-local-qwen.json` is the cheaper rehearsal,
   with coder B on Ollama (`qwen3.5:9b`). `profiles/local-ollama.json` stays the
   all-local fallback. Each description states where respondent text goes. The Qwen rates
   ($2 in / $6 out per million tokens, dated 4 October 2026) come from third-party pages
   and are marked unverified in the profile; the user re-reads the host's own page on the
   day. Every shipped profile is tested to load and to pass `live_components`'
   validation.

**Consequences.**

*What it buys.* The PI's two-maker design runs with the second maker hosted, and the
record of every run says in plain words that its text went to that host. "Local" keeps
meaning local. The transport the local pilot already exercised is the one the hosted
coder uses, so the pilot's evidence about parsing and fail-safes carries over.

*What it costs.* A sixth `Provider` member (a fifth additive amendment to `gaf/config.py`, beside ADR-0051's) and a second endpoint module. A family is
inferred from the leading letters of the model id, so an id with no maker in it would be
its own family; the profile's description and this entry say which id is meant. There is
no pre-flight probe of the hosted model (a hosted `/models` listing is not guaranteed), so
a wrong id fails on the first coder-B call, after the retries — at the smoke test's scale
that costs cents, which is what the smoke test is for.

*What remains open.* The data-residency terms of the chosen host, and whether the PI's
ethics approval covers them, are the PI's to confirm before any run on real data. The
Qwen price is unverified until read on the host's own page.

---

## ADR-0053 — A spend cap that stops before a call, and the run statistics a reader asks for first

**Status:** proposed (branch `live-run-oct`, 4 October 2026; amends the frozen `llm_calls`
table additively, on the ADR-0015, ADR-0048 and ADR-0049 precedent; does not touch
`gaf/config.py`, the judge prompt or any provider client)

**Context.** The first paid run is on Monday 5 October and the meeting with the PI on
Thursday 8 October. Three things were missing, each named in the live-run plan.

* **There was no spend cap (blocker B4).** A live run with a key in the environment could
  not be stopped from spending except by killing the process. The estimate for the whole
  plan is $12 to $30 against a requested ceiling of $40, and Opus's thinking tokens, billed
  as output, are the main uncertainty (ADR-0051). A bug in a threshold, a retry storm or a
  wrong price would be paid for before anyone looked.
* **Nothing measured whom the judge backs (B5).** The judge shares coder A's model, and the
  dispute prompt (`judge_v1.py`) always shows coder A first. That is a standing risk of
  self-preference or position bias, and the PI's second question is whether two different
  models agree and how the judge settled the disagreements.
* **The run report did not say how often the coders agreed, how long a response took, or
  what each role cost.** `RunStats` held the counts the loop reconciles with
  (`acceptance_by_origin`, `judge_calls`, a total cost), but not the figures the results
  pack is built from. The cost estimate itself was made with a one-off query over
  `llm_calls`.

Reading the code before changing it settled four facts the design rests on.

1. **`llm_calls` already records `latency_ms`.** Every live client times its call with
   `perf_counter`; mock calls and cache replays record zero. No column or migration is
   needed for latency.
2. **The ledger lags the running process.** The fast loop writes `llm_calls` after each
   call *site* (`_Recorder.drain`), so a check that re-read the table before each call would
   be up to a call site behind.
3. **A resumed run is a new run.** `gaf run --skip-coded DIR` writes a new directory with a
   new database (and deletes any database already at its `--out`). Only `gaf checkpoint`
   continues a run's own database. "The run's spend" therefore has to be followed through
   the `skipped_from` link every resumed run already records.
4. **The judge cannot choose between coders in the way the brief's wording suggests.** The
   one place it arbitrates between coder A's and coder B's candidates is an M1 grey-zone
   dispute, and its verdicts are `KEEP` (both readings stay) or `DROP` (*the second
   candidate*, which is always coder B's, goes). It never backs B alone.

**Decision.**

1. **A guard in front of the model, behind the cache.** `BudgetedLLMClient`
   (`gaf/llm/budget.py`) wraps a client; before each call it asks the `SpendBudget` whether
   the cumulative billed cost has *reached* the cap (`>=`), and if so raises
   `BudgetExceededError` and does not call. After the call it adds the result's `cost_usd`.
   `guard_client` puts it *inside* `CachingLLMClient`, so a cache replay is answered from
   disk, is never checked and never charged, and is still answered when the cap has been
   reached; with `--no-cache` it wraps the bare client. `guard_agents` rebinds the public
   `.client` of each agent, so one function covers every command without any client factory
   knowing the cap exists. The exception is deliberately not an `LLMError`: that means "the
   transport failed after retries", and a decision must not be swallowed as a fault.

2. **The overshoot is at most one call, and the help text says so.** The cap is checked
   before a call and never during one; nothing can recall a request already sent. The total
   can therefore pass the cap by the cost of the one call in flight when it crossed.

3. **What the cap counts.** Billed dollars only: `cost_usd` is `tokens x the ModelSpec
   rate`, so the cap is exactly as accurate as the client's token counts and the profile's
   prices. The running total is kept in memory (fact 2): a baseline read from the ledger
   at the start plus each result's cost. The baseline is `Blackboard.llm_spend(run_id)` for
   the run, plus that of every run it was resumed from, following `skipped_from` links with a
   loop guard (`gaf/cli/_budget.py: cumulative_spend`); a directory with no readable ledger
   is reported as unreadable, not counted as zero. So a resumed run, or a `gaf checkpoint`
   after a halt, continues one budget, and the new `--max-usd` is the cumulative total.
   Offline and mock runs cost zero and never trip it; local models are free by construction.
   Hosted *embeddings* are not rows in `llm_calls` and are not counted; the run prints a
   warning if the embedding mode is `openai` (the plan embeds locally).

4. **A cap that could not see the spend is refused before anything is touched.** A
   non-positive or non-finite amount is a usage error (exit 2). A live run under a cap
   whose registry has a hosted role with both rates at zero is refused (`unpriced_hosted_roles`),
   because that is the one way the cap fails silently. A resume under a cap the chain has
   already reached is refused (exit 4) before the previous run's database can be replaced.

5. **A halt reuses the checkpoint halt's shape.** `run_fast_loop(budget=...)` catches the
   refusal around `_code_response`. The response in flight is **not coded**: every model call
   in a response precedes the first codebook change (`_integrate`), so the working codebook is
   exactly what the last complete response left. What the half-made response already paid for
   is drained into `llm_calls` first. The run then closes normally (a short batch is evaluated
   like any other, S6 and M4 run, a final snapshot is frozen) and records the reason:
   `RunStats.budget` (cap, baseline, run, cumulative, the response and the call it stopped
   before), a `run_halted_spend_cap` audit row, a STOPPED EARLY caveat at the top of the
   report, and a halt message with the command that resumes it. `gaf run` exits **0**, as for
   `--halt-on-checkpoint` (ADR-0035). The in-flight response is coded again on resume, mostly
   from the cache. With no flag the `budget` key is absent from the stats and the audit
   payloads; the codebook, assignments and findings are byte-identical (tested).

6. **Which commands.** `--max-usd` is registered beside `--live` in `_add_mode`, so it is
   accepted by `gaf run`, `gaf check semantic|all` (the M3 judge) and `gaf codebook define`
   (the Definer); `gaf checkpoint` has its own copy because it has no `--live` (its mode comes
   from the run's echoed config). The last three have nothing useful to show when stopped
   part-way and exit **4**; a refused checkpoint writes nothing. `gaf analyse`, `report`,
   `views` and `validate` make no model call.

7. **The run statistics are computed from the blackboard, by one function, for every run.**
   `gaf/pipeline/run_metrics.py: compute_run_metrics` reads the audit log and `llm_calls`
   (the audit log keeps one row per decision where the `findings` table collapses repeats), so
   the same code answers for a live run and for `runs/process200`. They go into
   `RunStats.run_metrics`, and so into `stats.json`, `run.json`, the `run_completed` audit
   row and a new section of the report. `gaf report` recomputes them from `gaf.sqlite` when it
   is there, so a run written before this ADR has them and a later `gaf checkpoint`'s spend is
   counted, and writes them alone to `run_metrics.json`. Counts, shares, ids and code names
   only: no respondent text and none of the judge's reasoning.

   * **(a) Coder agreement.** The unit is the M1 *comparison*: a matched pair of coder A and
     coder B candidates, or a candidate only one coder proposed. Each lands in exactly one
     outcome: agreed outright (cosine at or above tau_high), grey zone (split into ruled on
     by the judge and unresolved because no judge was available), or disputed (below tau_low)
     or unmatched (A only, B only). The router records a non-agreed pair as two candidate
     rows; the arithmetic that recovers pairs from them is tested against the loop's own
     counts. Beside it, how M2 routed the accepted candidates: merge, create, or the judge.
   * **(b) Judge siding.** Among M1 grey-zone rulings: coder A (`DROP`, B's candidate removed),
     coder B (zero by construction), and neither (`KEEP`, both readings kept), with counts,
     shares and a `flag` when the coder A share is strictly above 0.65. Below 20 rulings the
     block says the share is unreliable. The report states the asymmetry in words, because
     "B: 0%" without it would be read as a finding. The judge prompt is not changed.
   * **(c) Latency.** Per call, per role and task, and per response (the sum of that
     response's calls), from the recorded `latency_ms`; cache replays and unmeasured calls
     are left out, so an offline run says "not measured" rather than a mean of zero. For a
     live run only, the wall-clock time per response and for the run from the audit log; an
     offline run reports none, because two identical offline runs must render the same bytes
     (`test_the_run_report_itself_is_deterministic`).
   * **(d) Spend by role and task.** `Blackboard.llm_usage(run_id)`, the query the cost
     estimate was built from: calls, billed calls, cache hits, fail-safes, calls stopped early,
     tokens in and out, dollars, and dollars per response coded. Tokens count every call, replays
     included (they size the workload); dollars count only what reached a provider.

8. **`llm_calls.stop_reason`, additively.** A nullable column holding `refusal` or
   `max_tokens` when the model stopped early, NULL otherwise, so refusals can be counted in
   SQL rather than inferred from `fail_safe`. It is read from the `_stop_reason` key the
   Anthropic client already writes into `LLMResult.data` (ADR-0051) through a read-only
   `LLMResult.stop_reason` property, so no provider client changes. `apply_schema` adds the
   column to an older database with a nullable `ALTER TABLE` (`SCHEMA_VERSION` 1 to 2); no row
   is rewritten and a build that never heard of the column still reads the table.

9. **The cache key carries the role's effort, when it has one.** `cache_key` adds
   `effort=<level>` only when `ModelSpec.effort` is set (ADR-0051), so a reply made at `low`
   is never replayed to a role now at `high`. With no effort the key is byte-identical to
   before, so existing caches and golden fixtures still hit (the legacy hash is recomputed by
   hand in a test).

10. **One more small correction the cap needs.** `Blackboard.completed_response_count` counts
    responses with an `assignments_written` row, and the slow loop uses it for a checkpoint's
    `at_response_count` instead of `coded_response_count`, which counts a response as soon as
    one coder's pass is written and would include the half-made response of a halted run. A
    store with no fast-loop run falls back to the old count.

**Measured, 4 October 2026.** Offline, no paid call. `gaf report` on a copy of
`runs/process200` (200 responses) computes the block: 811 M1 comparisons, of which 729 (89.9%)
agreed outright, none fell in the grey zone, and 82 (10.1%) were disputed (37 pairs) or
unmatched (21 coder A only, 24 coder B only); M2 routed 848 candidates, 97.3% merge, 2.5%
create and 2 (0.2%) to the judge; the judge ruled on no M1 dispute, so there is no siding to
read. Spend by role and task reproduces the plan's inputs: 2,278 calls (1,878 replayed from
the cache), 403,374 input tokens for coder A, which is 2,017 per response, and $0. Latency is
"not measured", as it must be offline. With a fake client billed $0.10 per fresh call, a run
under a cap stops at the cap at seven caps chosen to fall mid-response (0.05 to 4.05): in
every case the dollars in `llm_calls` equal the dollars the guard counted, the cumulative
total is at least the cap and under it plus one call, and the halted run's codebook and
assignments are those of an uncapped run over exactly the responses it coded. Re-running
under a cap of one cent against a warm cache spends $0 and completes. A resume chain of three
runs counts the first two runs' spend. Gates after the change: `make lint` and `make
typecheck` clean, 1,474 passed and 5 skipped (65 of them in `tests/test_run_controls.py`),
coverage 97.14% against the floor of 93, `make provenance` passing.

**Consequences.**

*What it buys.* A paid run can be started with a number it cannot exceed by more than one
call, and halted and resumed without losing or double-paying for work. The results pack can
quote agreement, the judge's siding rate with its flag, time per response and spend per role
from one place, for the cold evaluation run and for the 161 alike.

*What it costs.* The cap is as good as the prices in the profile and the token counts the
client reports; the smoke test is where the recorded total should be compared with the
provider's own dashboard. The in-flight response of a halted run is paid for twice if the
cache is off. `RunStats` and `stats.json` gain `run_metrics` for every run (the `budget` key
only when the flag is used), `run_completed` payloads grow, and the committed
`examples/demo-run/` predates both until `make example` regenerates it. `gaf report` now reads
the ledger, so a report written after a `gaf checkpoint` differs from the one before it by
that call's cost; this is intended, and one existing test now refreshes the in-place report
before comparing a rebuild. Three CLI files outside the cap's own (`check.py`,
`codebook.py`, and one argument in `_common.py`) carry a line or two that routes the flag.

*What remains open.* Whether the siding flag can ever be read as bias: the judge shares coder
A's model *and* sees A first *and* has a prompt whose only removal is of the second
candidate, so self-preference, position and the prompt's own framing cannot be separated by
this measure; separating them needs a second judge model or a swapped-order run, which would
change the prompt and is the PI's decision. The 0.65 threshold is the plan's, not measured. A
`max_output_tokens` or `temperature` that the request leaves unset is still not in the cache
key; adding it would orphan every existing entry. Hosted embeddings are outside the cap. A run
directory that has been moved takes its spend with it: the chain finds it by the path the
resumed run recorded, and says so when it cannot.

