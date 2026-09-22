# 10 - The loop handover: where the matrix first hands over on real data

The fast loop never blocks. At every batch boundary it evaluates the handover rows
of the decision matrix and records the verdict; a `checkpoint_due` verdict says a
human should look at the codebook before coding continues. Nothing in this export
took a checkpoint: `--halt-on-checkpoint` is the flag that stops at one, and section
16 shows what happens when it does.

**First handover: batch 1, after 10 responses.**

| what | value |
|---|---|
| trigger | `health` |
| rule(s) fired | `handover.new_codes` |
| new codes in that batch | 15 |
| near-duplicate leaf pairs | 0 |
| spike rule | `-` |

> new codes this batch 15 > 8; the spike rule has no baseline yet: a ratio needs 3 coded batches behind it, so batch 1 is judged by the absolute ceiling alone

**17 of 20 batches came due.** Rules fired across the whole run:

Read that count with one thing in mind: `handover.floor` is a *schedule*, not a
diagnosis. Once the hard floor of responses has been passed it is satisfied at every
subsequent batch boundary, so a long run reports it repeatedly. The batches worth
looking at are the ones whose trigger is `health` or `spike` — those are the ones
saying something about this codebook rather than about how far the run has got.

| rule | batches |
|---|---:|
| `handover.floor` | 16 |
| `handover.new_codes` | 1 |

## The trace, batch by batch

| batch | responses coded | new codes | cumulative codes | near-duplicate pairs | spike rule | fired | held | trigger | verdict |
|---:|---:|---:|---:|---:|---|---|---|---|---|
| 1 | 10 | 15 | 15 | 0 | - | handover.new_codes | - | health | checkpoint_due |
| 2 | 20 | 3 | 18 | 0 | - | - | - | none | continue |
| 3 | 30 | 2 | 20 | 0 | - | - | - | none | continue |
| 4 | 40 | 0 | 20 | 0 | - | - | - | none | continue |
| 5 | 50 | 0 | 20 | 0 | - | handover.floor | - | floor | checkpoint_due |
| 6 | 60 | 0 | 20 | 0 | - | handover.floor | - | floor | checkpoint_due |
| 7 | 70 | 0 | 20 | 0 | - | handover.floor | - | floor | checkpoint_due |
| 8 | 80 | 0 | 20 | 0 | - | handover.floor | - | floor | checkpoint_due |
| 9 | 90 | 0 | 20 | 0 | - | handover.floor | - | floor | checkpoint_due |
| 10 | 100 | 0 | 20 | 0 | - | handover.floor | - | floor | checkpoint_due |
| 11 | 110 | 0 | 20 | 0 | - | handover.floor | - | floor | checkpoint_due |
| 12 | 120 | 0 | 20 | 0 | - | handover.floor | - | floor | checkpoint_due |
| 13 | 130 | 1 | 21 | 0 | - | handover.floor | - | floor | checkpoint_due |
| 14 | 140 | 0 | 21 | 0 | - | handover.floor | - | floor | checkpoint_due |
| 15 | 150 | 1 | 22 | 0 | - | handover.floor | - | floor | checkpoint_due |
| 16 | 160 | 0 | 22 | 0 | - | handover.floor | - | floor | checkpoint_due |
| 17 | 170 | 0 | 22 | 0 | - | handover.floor | - | floor | checkpoint_due |
| 18 | 180 | 0 | 22 | 0 | - | handover.floor | - | floor | checkpoint_due |
| 19 | 190 | 0 | 22 | 0 | - | handover.floor | - | floor | checkpoint_due |
| 20 | 200 | 0 | 22 | 0 | - | handover.floor | - | floor | checkpoint_due |

## The decision matrix, as this run's configuration renders it

Every decision the pipeline can take, which loop takes it, who decides, and the
condition under which it fires. Written by `gaf report` from the run's own config,
so the thresholds below are the ones this run used.

# Decision matrix — fast loop, handover, slow loop

Every decision this pipeline takes, where it is taken, what decides it and which audit event records it. Generated from `gaf.pipeline.decision_matrix.DECISION_MATRIX`, with the thresholds of the run it was generated for: a row's condition is not a description of the code, it is the code's own numbers.

Checkpoint mode `event_driven`; batch size 10; tau_high 0.8, tau_low 0.45, tau_fit 0.3.

Trigger precedence when several handover rows fire at once: `health` > `spike` > `floor` > `cadence`.

## Fast loop — per response

Cheap, parallel, never blocking, and it never restructures the codebook.

| rule | decision | decided by | condition | outcome | audit event | source |
|---|---|---|---|---|---|---|
| `fast.duplicate_response` | Is this response a verbatim repeat of one already coded? | `deterministic` | the normalised response hashes to a digest an earlier response already produced | flagged as a duplicate on the response's outcome row and in the log; the response is still coded, because dropping it would silently change the denominator of every rate in the report | `duplicate_response` | `gaf.pipeline.prep:dedup_precheck` |
| `fast.structural_drop` | Does a proposed candidate survive the structural checks? | `deterministic` | S1 (a name, a description and at least one quote) or S2 (the quote occurs in the response it cites, at or above a fuzzy similarity of 0.85) reports an ERROR | the candidate is dropped before any embedding or model call; S2b, S3, S4 and S5 flag and never drop | `candidate_dropped` | `gaf.checks.structural:check_candidates` |
| `fast.accept_agreed` | What survives when the two coders propose the same code? | `deterministic` | the Hungarian-matched cross-coder score is at or above tau_high (0.8) | one candidate, carrying both coders' evidence. The common case, and it costs no model call | `candidates_accepted` | `gaf.pipeline.router:accept_candidates` |
| `fast.accept_grey` | What happens to a cross-coder pair in the grey band? | `judge` | the cross-coder score lies between tau_low (0.45) and tau_high (0.8) | the only pair that reaches the frontier judge. DROP accepts coder A's candidate and drops coder B's; any other verdict, an unreadable reply and the offline case with no judge all keep both | `judge_consulted` | `gaf.pipeline.router:escalates` |
| `fast.accept_disputed` | What happens to a cross-coder pair below tau_low? | `deterministic` | the cross-coder score is below tau_low (0.45) | both candidates are kept and flagged, never escalated: the coders named two different things, and choosing between them is a meaning judgment the fast loop is not allowed to make | `candidates_accepted` | `gaf.pipeline.router:accept_candidates` |
| `fast.accept_unmatched` | What happens to a code only one coder proposed? | `deterministic` | M1's Hungarian assignment leaves the candidate unmatched | accepted and flagged as unmatched. A code one coder saw and the other did not is the disagreement the two-coder design exists to surface | `candidates_accepted` | `gaf.pipeline.router:accept_candidates` |
| `fast.fit_below_tau_fit` | Does a quote actually evidence the code it was offered for? | `judge` | the code-to-evidence cosine fit is below tau_fit (0.3) | the pairing is put to the judge; a quote ruled UNNECESSARY is removed, and a candidate left with no verified quote is dropped. Offline this escalates nearly every pairing, so those counts are artefacts of the stand-in embedder (ADR-0019) | `candidate_dropped` | `gaf.checks.semantic:check_code_evidence_fit` |
| `fast.route_merge` | Does an accepted candidate fold into an existing code? | `deterministic` | the best retrieved code scores at or above tau_high (0.8) | MERGE: the target keeps its id, name, description and parent and gains this candidate's evidence. Merging evidence is integration; rewriting a description would be restructuring | `code_merged` | `gaf.pipeline.router:integrate` |
| `fast.route_create` | Is an accepted candidate a genuinely new code? | `deterministic` | the best retrieved code scores below tau_low (0.45) | CREATE: a new code, its id the content hash of its name, its provenance the snapshot the batch's coders read. Its parent is the family node only if one already exists — the fast loop does not invent hierarchy | `code_created` | `gaf.pipeline.router:integrate` |
| `fast.route_judge` | What happens when the geometry cannot tell merge from create? | `judge` | the best retrieved code scores between tau_low (0.45) and tau_high (0.8) | JUDGE: the judge's MERGE is honoured; every other verdict, and the offline case with no judge, CREATEs. A spurious code is visible to M4 and recoverable at the gate; a spurious merge destroys a distinction silently | `route_chosen` | `gaf.pipeline.router:integration_actions` |

## Handover — per batch boundary

Neither loop: the deterministic question of whether the slow loop is due. Evaluated at every batch boundary and reported; the fast loop never blocks for it.

| rule | decision | decided by | condition | outcome | audit event | source |
|---|---|---|---|---|---|---|
| `handover.near_duplicates` | Has the codebook accumulated near-duplicate leaves? | `deterministic` | mode is event_driven, M4 counts more than 3 near-duplicate leaf pairs, and spacing is satisfied | verdict checkpoint_due under trigger `health` | `checkpoint_evaluated` | `gaf.checks.health:checkpoint_signals` |
| `handover.new_codes` | Did this batch admit too many codes in absolute terms? | `deterministic` | mode is event_driven, the batch admitted more than 8 new codes, and spacing is satisfied | verdict checkpoint_due under trigger `health` | `checkpoint_evaluated` | `gaf.checks.health:checkpoint_signals` |
| `handover.spike` | Did this batch admit far more codes than the batches just before it? | `deterministic` | mode is event_driven, the batch admitted at least 4 new codes and at least 2.0x the median of the previous 3 batches, and spacing is satisfied. The first 3 batches have no baseline and do not spike at all: `handover.new_codes` is the rule that speaks there, and this one would only repeat it | verdict checkpoint_due under trigger `spike`. The defaults are uncalibrated (ADR-0033) | `checkpoint_evaluated` | `gaf.checks.growth:detect_spikes` |
| `handover.floor` | Has a quiet codebook gone too long without a human look? | `deterministic` | 50 responses have been coded **since the last checkpoint**, whatever the codebook looks like | verdict checkpoint_due under trigger `floor`. Not held by spacing: the floor exists precisely for the run where nothing else ever fires. Measured since the last checkpoint, so taking one clears it; measured from the start of the run it would latch on and report a checkpoint due at every later batch of every later run (ADR-0033, R1 I1) | `checkpoint_evaluated` | `gaf.checks.health:checkpoint_signals` |
| `handover.cadence` | Is this one of the scheduled checkpoints? | `deterministic` | mode is fixed and the running total of responses coded is one of 10, 20, 30, 40, 50 | verdict checkpoint_due under trigger `cadence` (the predecessor's schedule) | `checkpoint_evaluated` | `gaf.pipeline.slow_loop:should_checkpoint` |
| `handover.spacing_hold` | Has enough been coded since the last checkpoint for another to be worth it? | `deterministic` | fewer than 10 responses since the last checkpoint | every event trigger — health, new codes, spike — is held: the evaluation names the held rule and its reason and returns verdict continue. The floor and the cadence are not held | `checkpoint_evaluated` | `gaf.pipeline.decision_matrix:evaluate_handover` |
| `handover.manual` | May an operator open the gate with nothing firing? | `human` | the operator runs `gaf checkpoint` and supplies the trigger themselves | a checkpoint runs under trigger `manual`. The fast loop never blocks for the gate, so this is how a person acts on a checkpoint that is due | `checkpoint_started` | `gaf.pipeline.slow_loop:run_checkpoint` |

## Slow loop — per checkpoint

Rare, expensive, human-gated, and the only place the codebook changes structurally.

| rule | decision | decided by | condition | outcome | audit event | source |
|---|---|---|---|---|---|---|
| `slow.proposal` | What structural edits does the codebook need? | `refactorer` | a checkpoint has fired and the whole codebook plus usage statistics is assembled | an edit script. The Refactorer proposes and never applies; this is a creation task, which is where the Vaccaro et al. meta-analysis finds human-AI pairing helps | `checkpoint_proposed` | `gaf.agents.refactorer:RefactorerAgent.propose` |
| `slow.validation_drop` | Could this operation be applied at all? | `deterministic` | the operation's shape, targets or name collide, or the codebook it would produce fails S6 — including a hierarchy deeper than 2 | dropped with a finding before any human sees it, and the valid operations beside it still apply: one hallucinated row must not cost five good ones | `operation_dropped` | `gaf.pipeline.slow_loop:validate_script` |
| `slow.gate_accept` | Does this operation go into the codebook? | `human` | the person at the gate returns `accept` for this operation | the operation is applied. Silence, an unreadable verdict and no human at all all reject | `operation_applied` | `gaf.pipeline.slow_loop:ConsoleGate.review` |
| `slow.gate_reject` | Does this operation go into the codebook? | `human` | the person returns `reject`, returns nothing, or no human is present | nothing is applied and the codebook is byte-identical. A machine that disposes of its own proposals when nobody is watching is the failure the gate exists to prevent (ADR-0004) | `operation_rejected` | `gaf.pipeline.slow_loop:RejectAllGate.review` |
| `slow.gate_edit` | May the person replace the operation with their own? | `human` | the person returns `edit` with a replacement operation | the replacement is validated exactly as the machine's was, then applied. An `edit` with no replacement rejects | `operation_applied` | `gaf.pipeline.slow_loop:ConsoleGate.review` |
| `slow.op_create` | Admit a code the coders never proposed. | `human` | an accepted `create` operation names a new code and its parent | a new code, its provenance the base snapshot the proposal was made against | `operation_applied` | `gaf.pipeline.slow_loop:apply_operations` |
| `slow.op_merge` | Fold two codes that turned out to be one. | `human` | an accepted `merge` operation names two or more existing codes | merge-with-re-examination: every source's evidence carries into the target, and an apply that lost a quote raises rather than reaching a snapshot | `operation_applied` | `gaf.pipeline.slow_loop:apply_operations` |
| `slow.op_split` | Break an overloaded code into the concepts it was carrying. | `human` | an accepted `split` operation names one code and the codes to distribute it into | the target's evidence is distributed across the resulting codes and none is dropped. The predecessor had no split, and that absence is the documented cause of its codebook flattening | `operation_applied` | `gaf.pipeline.slow_loop:apply_operations` |
| `slow.op_reparent` | Move a code under a different family. | `human` | an accepted `reparent` operation names a code and its new parent | the code's parent and name change together, so the derived family and the explicit parent_id stay in agreement and S6 still passes | `operation_applied` | `gaf.pipeline.slow_loop:apply_operations` |
| `slow.op_rename` | Correct a code's name without changing what it means. | `human` | an accepted `rename` operation names a code and its new name | the code keeps its evidence; a rename reads as one new and one lost code on the health row | `operation_applied` | `gaf.pipeline.slow_loop:apply_operations` |
| `slow.op_noop` | Record that the Refactorer looked and found nothing to change. | `refactorer` | the proposed operation is `noop` | no structural change, and the checkpoint is recorded as `noop` rather than `rejected`: a codebook found healthy is not the same fact as a refusal | `operation_applied` | `gaf.pipeline.slow_loop:apply_operations` |
| `slow.apply_and_snapshot` | What becomes of the codebook the accepted operations produce? | `deterministic` | at least one accepted operation changed the codebook's bytes | a new snapshot, content-addressed, its parent the base snapshot, plus a changelog naming both ids. An unchanged codebook writes no snapshot at all | `snapshot_frozen` | `gaf.store.snapshot:freeze` |
