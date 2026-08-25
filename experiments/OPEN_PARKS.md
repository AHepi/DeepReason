# OPEN_PARKS.md — the standing registry of deferred work

A **park** is a piece of work someone deliberately chose not to do, written
up at the moment of that choice as a ready-to-send prompt. Parks are the
project's memory of its own decisions not to act.

Until 2026-08-25 they lived scattered across each tranche's own
`PARKED.md`, findable only if you already knew which tranche parked what.
This file is where the open ones live now.

**Scope.** It carries **71 open park items** from the 18 tranche
directories that the 2026-08-25 close-out audit rowed EXTRACT-THEN-PRUNE —
directories otherwise ready to leave the tree, whose parks had to be
re-homed first. It is NOT a census of every park in the repository: parks
inside directories rowed KEEP stay in their own `PARKED.md`.

"Open" has the audit's mechanical meaning: **no later tranche's execution
artifact** (`DELIVERY.md`, `VALIDATION.md`, `VERIFY.md`, `FIX.md`,
`CHECKLIST.md`, or `docs/ERRATA.md`) ever cited the park. A citation from
another `PARKED.md` is a carry-forward, not an execution — the item was
re-parked, not done.

### The count is 71, not the 60 the audit reported

The audit counted park items with a regex matching `P<n>` labels. Three of
these eighteen files label items differently — `2026-07-30-fix-sandbox-contract`
carries `## D2a` and `## D1a`, both full park entries, one of them parked by
explicit operator instruction ("Park D2a"). Counting only `P<n>` would have
dropped eleven real items on the floor at the moment their directories were
deleted.

The extraction rule used here is structural instead of label-based: in a
`PARKED.md`, **every heading below the title starts an item**. It was then
verified line-by-line — across all 18 files, **zero non-blank lines after
the preamble fall outside an extracted item**. The audit's 60 is corrected
to 71; nothing was lost.

**Every item below is VERBATIM.** Nothing is summarized, trimmed, or
reworded — proven by asserting each item's exact byte block appears as a
literal substring of this file. A park loses its value when compressed: its
worth is that it can be pasted into an executor window unchanged. Each
tranche's own framing preamble is carried too, because it often says who
authorized the park and why.

**Provenance.** All 70 pruned directories exist in full at `6e64330fe`, the
commit immediately before the prune:

    git show 6e64330fe:experiments/<tranche>/PARKED.md

(One sha for all of them rather than one per file: this is a 59-commit
shallow clone, and per-file `git log` cannot see past its graft boundary —
it returns that boundary for every unmodified file, which would be uniform
and wrong. Recorded as assumption A1a in
`experiments/2026-08-25-change-closeout-prune/REQUEST.md`.)

**Nothing here is a commitment.** These are open questions and deferred
work, not a backlog anyone promised to clear. Several may be answered by
now, superseded, or no longer worth doing — the audit's test was
mechanical, not a judgment about merit.

## Contents

- [`2026-07-30-change-amendment-epochs`](#2026-07-30-change-amendment-epochs) — 5 item(s)
- [`2026-07-30-fix-citation-quote-check`](#2026-07-30-fix-citation-quote-check) — 4 item(s)
- [`2026-07-30-fix-sandbox-contract`](#2026-07-30-fix-sandbox-contract) — 6 item(s)
- [`2026-08-01-fix-decomposition-merge-pairing`](#2026-08-01-fix-decomposition-merge-pairing) — 9 item(s)
- [`2026-08-02-map-falsification`](#2026-08-02-map-falsification) — 6 item(s)
- [`2026-08-03-change-driving-skill`](#2026-08-03-change-driving-skill) — 3 item(s)
- [`2026-08-03-change-rung1-sockets-on-paper`](#2026-08-03-change-rung1-sockets-on-paper) — 6 item(s)
- [`2026-08-03-change-rung2-bridge-unification`](#2026-08-03-change-rung2-bridge-unification) — 4 item(s)
- [`2026-08-03-change-rung2-config-inventory`](#2026-08-03-change-rung2-config-inventory) — 6 item(s)
- [`2026-08-05-fix-smoke-entry-point-reader`](#2026-08-05-fix-smoke-entry-point-reader) — 4 item(s)
- [`2026-08-08-change-rung-g1-actual-diff-budget`](#2026-08-08-change-rung-g1-actual-diff-budget) — 1 item(s)
- [`2026-08-09-change-errata-sweep-and-automation`](#2026-08-09-change-errata-sweep-and-automation) — 1 item(s)
- [`2026-08-11-change-docs-reorg-steps-3-4`](#2026-08-11-change-docs-reorg-steps-3-4) — 1 item(s)
- [`2026-08-14-change-rung1-vocabulary-groundwork`](#2026-08-14-change-rung1-vocabulary-groundwork) — 4 item(s)
- [`2026-08-15-change-rung2-premise-channel`](#2026-08-15-change-rung2-premise-channel) — 2 item(s)
- [`2026-08-15-change-rung3a-h1-successor-deletion`](#2026-08-15-change-rung3a-h1-successor-deletion) — 2 item(s)
- [`2026-08-22-audit-scalarization`](#2026-08-22-audit-scalarization) — 3 item(s)
- [`2026-08-24-change-rung5-promotion-criteria`](#2026-08-24-change-rung5-promotion-criteria) — 4 item(s)

---

<a id="2026-07-30-change-amendment-epochs"></a>
## 2026-07-30-change-amendment-epochs

Origin: `experiments/2026-07-30-change-amendment-epochs/PARKED.md` — 5 open item(s).
Full original: `git show 6e64330fe:experiments/2026-07-30-change-amendment-epochs/PARKED.md`

*Its own framing, verbatim:*

> # Parked — noticed in this tranche, deliberately not done

<!-- verbatim: experiments/2026-07-30-change-amendment-epochs/PARKED.md lines 3-55 -->

## P1 — Materialize a distinct successor manifest digest per amendment epoch

Parked by operator instruction (REQUEST.md R12b): *"Park the
successor-manifest digest materialization in PARKED.md as a possible
future tranche; do not implement it now."*

**What it would be.** Today an amendment epoch copies the run manifest
verbatim, so `successor_manifest_digest == parent_manifest_digest`, and
the epoch's superseding run-input and dossier are named by the
`run-amendment.v1` record. The parked alternative mints a genuinely
distinct successor manifest whose `run_input_digest` points at the
epoch's own input, making the manifest — not the record — the authority
for which input an epoch runs under.

**Why it is not a small change.** The run's `(manifest digest,
run_input_digest)` pair is bound for the life of a root by:

- `workflow/state.py` — `WorkflowProcessStateV1.manifest_digest`, and
  `apply_decision` refusing any transition whose `manifest_digest`
  differs from the state's;
- `capabilities/state.py` — the capability transition chain requiring
  `transition.run_input_digest == previous.run_input_digest` (a
  CLAUDE.md frozen surface);
- `workflow/lifecycle.py` — `build_resumed_lifecycle` requiring
  `terminal.manifest_digest == manifest_digest`;
- `runtime/terminal_authority.py` — `derive_terminal_authority` requiring
  the passed manifest to equal the root-bound one, plus the terminal
  commitment and replay-validation bindings minted against it;
- `runtime/continuation.py` — `_continuation_history` requiring every
  record to carry one manifest digest;
- `cli/doctor.py` — the qualification report bound to one manifest
  digest;
- roughly twenty further identity comparisons in `invariants.py`.

Making those epoch-aware is not additive. Records below the fence carry
the parent digest and would have to keep validating against it while
records above carry the successor — which means every one of those sites
needs per-record epoch attribution, several of them on surfaces the
project has declared frozen precisely because getting this wrong
invalidates existing replay-valid roots.

**What would justify unparking it.** A concrete need the record-carried
design cannot serve — for example an amendment that must change routing,
budgets, or capability policy, not just the question and the evidence.
Nothing in the current requirement calls for that: the qualification
subject is meant to stay unchanged across an amendment, which is exactly
what copying the manifest verbatim guarantees by construction.

**Cost if unparked.** A full tranche of its own, with a real risk of
invalidating committed roots; it should carry its own goal, its own
frozen-surface approval, and a before/after `verify_root` sweep over
every committed root as its acceptance check.

<!-- verbatim: experiments/2026-07-30-change-amendment-epochs/PARKED.md lines 56-101 -->

## P2 — RESOLVED: re-attaching an already-admitted source made the root invalid

Found 2026-07-30 while answering an operator question about the
admission path, after the tranche was delivered. Parked briefly, then
UNPARKED by operator instruction (REQUEST.md R25: *"Amend needs to
reject up front"*) and fixed in the same tranche. The original entry is
kept below unchanged; the resolution is appended at the end.

**Reproduction.** Take a converged root whose dossier already admits
some file F. Run `deepreason amend --attach F` with F's exact bytes.
`amend` accepts and commits the epoch. Then:

    dossier-1 source ids: ['src-a7b17a1063413cfec12df194df73083127c3757a']
    dossier-1 block ids : ['7275171c263c', '8fd103c96358']
    amend accepted; new dossier: b7aab4b02d8c
    dossier-2 source ids: ['src-a7b17a1063413cfec12df194df73083127c3757a']
    dossier-2 block ids : ['7275171c263c', '8fd103c96358']
    same source id across epochs: True
    same block ids across epochs: True
    verify_root violations: [{'check': 'attached-evidence',
      'detail': 'event seq=10: attached source differs from its bound
       dossier or arrived late'}]

**Cause (unconfirmed, from reading).** `verify_root`'s attached-evidence
sweep carries one `source_records` map across every epoch window and
fails any source id it sees twice. That is correct within an epoch — it
is what stops a source being introduced twice under one dossier — but
across epochs it collides with a second dossier that legitimately
contains the same content-addressed source. The dossier digests differ
(different `problem_ref` and provenance), so the epoch is not skipped by
the `admitted_digests` short-circuit, and `attach_bound_evidence`
registers a second, differently-worded source record for the same id.

**Severity.** Narrow but real: an operation the tool permits produces a
record the tool then calls invalid. An operator who re-attaches a
document they already attached gets a root that fails its own integrity
check with no warning at `amend` time.

**Suggested direction, not a decision.** Refuse the duplicate at `amend`
time with a typed code (the source is already admitted; nothing would be
added), rather than loosening the cross-epoch uniqueness rule — the rule
is doing real work and the duplicate carries no new evidence. Whether a
partial overlap (some files new, some already admitted) should be
refused wholesale or admitted minus the duplicates is the open design
question, and belongs to that tranche's spec.

<!-- verbatim: experiments/2026-07-30-change-amendment-epochs/PARKED.md lines 102-132 -->

### Resolution (R25)

`amend` now refuses the duplicate before any parse, blob write, or
staging. `_admit_supplement` receives the content digests of every source
already bound to the run — across all epochs, not just the original
dossier — and fails the whole invocation with
`AMEND_SOURCE_ALREADY_ADMITTED`, naming the offending path and the source
id it duplicates.

The refusal is whole-invocation rather than admit-minus-duplicates: that
is the rule `collect_attachment_inputs` already applies to an unreadable
path, on the same reasoning — silently admitting a subset of what the
operator pointed at would misrepresent the evidence base.

The cross-epoch uniqueness rule in `verify_root` was left untouched, as
the original entry suggested. It was never wrong; it was correctly
reporting a record `amend` should not have produced.

Reproduction, re-run against the fix:

    amend refused up front: AMEND_SOURCE_ALREADY_ADMITTED
    message: .../same-again.md is already admitted as
      src-a7b17a1063413cfec12df194df73083127c3757a. An amendment admits
      new evidence only; drop the already-admitted file(s) and re-run
    run-epochs staged: False
    verify_root violations: []

Regression: `test_amend_refuses_a_source_already_admitted_to_this_run`
(including the mixed-batch case and the drop-the-duplicate recovery) and
`test_amend_refuses_content_admitted_by_an_earlier_amendment`.

<!-- verbatim: experiments/2026-07-30-change-amendment-epochs/PARKED.md lines 133-162 -->

## P3 — OBSERVATION: two MCP run tests are wall-clock fragile under load

Not caused by this tranche and not fixed here. Recorded because it cost
a diagnosis and will cost the next person one too.

`tests/test_mcp_run.py::test_start_poll_result_and_progress_notifications`
and `::test_typed_v6_stop_can_continue_and_append` failed in two gate
runs and passed in every other. Cause, established rather than guessed:

    concurrent  2 failed, 3165 passed in 891.57s   (two -n 4 gates at once)
    concurrent  2 failed, 3165 passed in 900.66s   (the other of the pair)
    exclusive   3167 passed, 7 skipped in 476.57s

Both failures occurred only while two full `pytest -n 4` gates ran
simultaneously — eight workers on a box sized for four, roughly doubling
wall time. The two tests drive a real run worker thread and wait on it
with hard two-second bounds (`_RUN_THREADS[...].join(timeout=2)`,
`cycle_started.wait(timeout=2)`), which a 2x-oversubscribed machine
misses. They pass in isolation, and pass in an exclusive full gate.

**Severity.** Low for correctness, real for signal: a loaded CI box can
turn these into a red gate with no defect behind it, and "0 failed is the
only acceptable result" then costs someone an investigation. The fix
would be to derive those waits from a scaling factor rather than a fixed
two seconds, or to make the test wait on a condition rather than a
deadline.

**Operator note.** The proximate cause was mine: I started a second full
gate before the first finished. Don't.

<!-- verbatim: experiments/2026-07-30-change-amendment-epochs/PARKED.md lines 163-210 -->

## P4 — `TOKEN_ACCOUNTING.json` counts research records as simulation records

Found 2026-07-30 while diagnosing the tensor-rank live run
(`run-27b80f26bd398c718360e97e2a403593`), which denied its only
simulation proposal at validation and never compiled, executed, or
dispatched a simulation. That root's `TOKEN_ACCOUNTING.json` nonetheless
reports:

    simulation_compilations: 1
    simulation_executions: 1
    simulation_backend_attempts: 1

All three are its one Wikipedia research fetch.

**Cause (confirmed by reading and by the record).** `capabilities/audit.py`
lines 435-438 read the shared capability-state maps without filtering by
record type:

    "simulation_compilations": len(state.compiled),
    "simulation_executions": state.execution_count,   # len(state.work_orders)
    "simulation_backend_attempts": sum(
        len(receipt.attempts) for receipt in state.receipts.values()
    ),

and `capabilities/state.py` deliberately pools both capabilities in those
maps — `CompiledResearchFetchV1` into `compiled` (line 307), the research
execution receipt into `receipts` (line 340), the research work order into
`work_orders`. This is the CLAUDE.md invariant *"the shared capability-state
maps pool ALL capabilities' proposals and work orders; always filter by
type"*, violated in the reporter. The budget meter alongside it
(`capabilities/simulation.py:1134`) filters by `isinstance` and is right,
which is why `run-result.json`'s `capability_accounting` reports
`simulation_executions: 0` for the same run.

**Severity.** No effect on adjudication, budgets, or `verify_root` — the
enforcing paths filter correctly. Real for evidence: `TOKEN_ACCOUNTING.json`
is a typed artifact an operator reads to judge whether a capability was
exercised, and on this root it asserts a simulation ran when none did. Two
typed artifacts of one run root disagree.

**Not fixed here.** Out of this tranche's scope; found during a live-run
diagnosis, not during the change. The fix is small (filter each counter by
`isinstance`, mirroring simulation.py:1134) but it changes the bytes of
`TOKEN_ACCOUNTING.json` for existing roots, so it needs its own goal, a
check that no committed root's `verify_root` verdict depends on those
fields, and a decision about whether research gets its own counters rather
than simply vanishing from the report.

---

<a id="2026-07-30-fix-citation-quote-check"></a>
## 2026-07-30-fix-citation-quote-check

Origin: `experiments/2026-07-30-fix-citation-quote-check/PARKED.md` — 4 open item(s).
Full original: `git show 6e64330fe:experiments/2026-07-30-fix-citation-quote-check/PARKED.md`

*Its own framing, verbatim:*

> # Parked — out of this tranche's goal

<!-- verbatim: experiments/2026-07-30-fix-citation-quote-check/PARKED.md lines 3-26 -->

## D2 — the sandboxed_python_v1 program contract never reaches the model

NOT abandoned. Operator-ordered ("the first two need fixing
immediately"); it is the NEXT tranche, split from this one only because
CLAUDE.md requires one defect per commit and the two fixes together
exceed this tranche's 150-line budget.

`validate_sandboxed_python_source` (`src/deepreason/simulation/compiler.py:212`)
requires the module body to be exactly one `def simulate(inputs, rng)`.
In `run-27b80f26bd398c718360e97e2a403593` the model submitted an
11-statement script and was denied `invalid_model_program` with an empty
detail. The words `simulate`, `inputs`, and `rng` appear nowhere in the
23,570-byte context pack (blob `9705881e`), which describes
`model_source` only as `{"maxLength": 262144, "minLength": 1, "type":
"string"}`. Latent second failure behind it: `requested_observables` must
be keys of the mapping `simulate` returns
(`src/deepreason/verification/contained.py:202`), so the proposal's
`["stdout"]` would have failed one stage later as a missing declared
observable.

Open question that tranche must settle before touching anything: whether
adding the contract to the pack or role text moves the qualification
subject digest, which CLAUDE.md declares frozen.

<!-- verbatim: experiments/2026-07-30-fix-citation-quote-check/PARKED.md lines 27-31 -->

## P4 — TOKEN_ACCOUNTING.json counts research records as simulation records

Operator instruction: investigate further, do not fix. Full entry in
`experiments/2026-07-30-change-amendment-epochs/PARKED.md`.

<!-- verbatim: experiments/2026-07-30-fix-citation-quote-check/PARKED.md lines 32-49 -->

## Q1 — an unquoted citation is recorded as "byte-verified"

Checked during diagnosis and found to be INTENDED, so it is not part of
this tranche's cause. `EvidenceRefClaimV1.quote` is
`str | None = Field(default=None, ...)` and its docstring says a quote
"when present, must reproduce a contiguous byte span" — optional by
design (`src/deepreason/llm/contracts.py:32`). A bare block reference
asserts only that the block exists, which the checker does establish, and
`EvidenceCitationCheckV1.quoted` records which kind it was.

What is NOT clean, and is left parked: the ledger event carries only the
code, not the `quoted` flag (`src/deepreason/rules/conj.py:2314`), so
`findings.py` counts both kinds together and `FINDINGS.md` for this run
reports "Byte-verified citations of admitted evidence: 4" when all four
carried no quote and no bytes were compared. That line overstates what
the record holds. Narrow, cosmetic in effect, and a separate change to
the signal shape — out of scope here.

<!-- verbatim: experiments/2026-07-30-fix-citation-quote-check/PARKED.md lines 50-74 -->

## D1a — the wire contract still describes the old, stricter quote rule

Split out of this tranche after the gate refused it. `EvidenceRefClaimV1`'s
docstring (`src/deepreason/llm/contracts.py:20-27`) tells the model a
quote "must reproduce a contiguous byte span of the block's canonical
text exactly — the citation checker byte-verifies it". After this
tranche the checker folds whitespace, so the text is stricter than the
rule.

Harmless in effect: a model that obeys the stricter text verifies under
the looser check. It is a documentation debt.

Not free to fix. Pydantic promotes the class docstring into the JSON
schema `description`, which is serialised into the conjecturer's context
pack, and the pack's bytes sit inside committed provenance digests:
`test_semantic_freedom_constitution`'s
`tokens_per_admitted_useful_candidate` baseline and
`test_incident_wave_a_v2_fixtures`'s `generated_root_sha256`. Changing
the docstring turns the gate red on both (proven by isolation, see
FIX.md's retraction). Regenerating those digests is frozen-record
semantics and needs operator approval.

Belongs to the D2 tranche, which is about what the pack tells the model
and will have to pay this cost once for both changes rather than twice.

---

<a id="2026-07-30-fix-sandbox-contract"></a>
## 2026-07-30-fix-sandbox-contract

Origin: `experiments/2026-07-30-fix-sandbox-contract/PARKED.md` — 6 open item(s).
Full original: `git show 6e64330fe:experiments/2026-07-30-fix-sandbox-contract/PARKED.md`

*Its own framing, verbatim:*

> # Parked — out of this tranche's goal

<!-- verbatim: experiments/2026-07-30-fix-sandbox-contract/PARKED.md lines 3-19 -->

## D2a — a capability transition cannot say why it denied a program

Parked by explicit operator instruction ("Park D2a").

`CapabilityTransitionV1` has no detail field, so the validator's message
("sandboxed Python must define exactly one simulate function") is
discarded and the record carries only `reason_code=invalid_model_program`.
An operator reading the record cannot tell which of the validator's ten
distinct rejection paths fired. Adding the field means changing a
capability-state record — `capabilities/state.py` digests and event
application are named frozen in CLAUDE.md — so it needs its own tranche
and its own approval.

Not urgent after D2b: once the contract is disclosed, the common cause of
`invalid_model_program` (the model never knew the rule) is gone, so the
missing detail is diagnostic debt rather than an active blocker.

<!-- verbatim: experiments/2026-07-30-fix-sandbox-contract/PARKED.md lines 20-40 -->

## D1a — the wire contract still describes the old, stricter quote rule

Carried forward from `2026-07-30-fix-citation-quote-check/PARKED.md`,
where it was parked "for the D2 tranche, which is about what the pack
tells the model and will have to pay this cost once for both changes
rather than twice."

That reasoning was sound and it is NOT being followed, deliberately. The
operator's approval reads "approved for D2b only" and enumerates exactly
two disclosures — the `simulate(inputs, rng)` contract and the
`requested_observables` rule. `EvidenceRefClaimV1`'s quote docstring is
neither. Folding it in would widen the approved pack surface on my own
authority, which is the failure the frozen-surface stop exists to
prevent; the fact that it would be cheap now is an argument for asking,
not for assuming.

The cost of not folding it in, stated so the operator can price it: the
same two baselines will have to be regenerated a second time when D1a is
approved. Nothing else is lost — the text is stricter than the harness
enforces, so a model that obeys it verifies.

<!-- verbatim: experiments/2026-07-30-fix-sandbox-contract/PARKED.md lines 41-45 -->

## P4 — TOKEN_ACCOUNTING.json counts research records as simulation records

Operator instruction: investigate further, do not fix. Full entry in
`experiments/2026-07-30-change-amendment-epochs/PARKED.md`.

<!-- verbatim: experiments/2026-07-30-fix-sandbox-contract/PARKED.md lines 46-52 -->

## Q1 — an unquoted citation is recorded as "byte-verified"

Checked in the previous tranche and found INTENDED at the contract level;
the residue is that the ledger event carries only the code, not the
`quoted` flag, so FINDINGS.md overstates what was compared. Full entry in
`experiments/2026-07-30-fix-citation-quote-check/PARKED.md`.

<!-- verbatim: experiments/2026-07-30-fix-sandbox-contract/PARKED.md lines 53-68 -->

## D2c — the declarative_numeric_v1 document shape is still undisclosed

Found while writing the disclosure, parked because the operator's
approval enumerated the `simulate(inputs, rng)` contract and the
`requested_observables` rule, and this is neither.

`model_source` now tells the model that a `declarative_numeric_v1` source
is a JSON document rather than Python. It does not say what the document
must contain: exactly the keys `schema` and `observables`, with
`schema == "declarative-numeric.v1"`, and each observable an expression
over a fixed vocabulary (`compile_declarative_numeric`,
`src/deepreason/simulation/compiler.py:138-170`). That is the same defect
class as D2b — a rule enforced and never shown — one simulation mode
over. Cheaper than D2b was: the same wire constant is the change site,
and the incident-wave A3 digest would move again.

<!-- verbatim: experiments/2026-07-30-fix-sandbox-contract/PARKED.md lines 69-86 -->

## D2e — the simulation contract text is disclosed unconditionally

`ConjecturerTurnWireContractV6.model_json_schema` omits the
`simulation_proposals` property when simulation is disabled, but the
`SimulationProposalWireV1` entry stays in `$defs` (measured: v6 with
simulation disabled still carries the whole definition). So the ~1.2 KB
of contract text this tranche added is present in packs for runs that
cannot propose a simulation.

The dangling definition predates this tranche; the tranche makes it
bigger. Two fixes are possible and neither is in this goal: prune the
`$defs` entry when the property is omitted (changes schema bytes for
every non-simulation pack, so it would move baselines of its own), or
inject the descriptions conditionally the way
`V6_SCRATCH_WORKSHOP_SCHEMA_DESCRIPTION` is injected — which needs a
`model_json_schema` override on `ConjecturerTurnWireContractV5`, since
v5 has none. FIX.md records why the conditional route was not taken here.

---

<a id="2026-08-01-fix-decomposition-merge-pairing"></a>
## 2026-08-01-fix-decomposition-merge-pairing

Origin: `experiments/2026-08-01-fix-decomposition-merge-pairing/PARKED.md` — 9 open item(s).
Full original: `git show 6e64330fe:experiments/2026-08-01-fix-decomposition-merge-pairing/PARKED.md`

*Its own framing, verbatim:*

> # Parked
> 
> One line each. Noticed during this tranche, not worked in it. Sources:
> `experiments/live_jolt_2026-07-31/INVESTIGATION.md`.

<!-- verbatim: experiments/2026-08-01-fix-decomposition-merge-pairing/PARKED.md lines 6-9 -->

- `run-status.json` reports `accepted`/`refuted`/`suspended` as pydantic
  defaults the terminal emit never populates (`application/text_runs.py:1095-1108`),
  so the file contradicts its own `display_status_counts` — this is what caused
  the run's outcome to be misreported to the operator.

<!-- verbatim: experiments/2026-08-01-fix-decomposition-merge-pairing/PARKED.md lines 10-11 -->

- `run-stop.json` writes a fresh `StopMetrics` rather than measurements
  (`text_runs.py:1031-1032`); `queued_criticism` has no writer anywhere in `src/`.

<!-- verbatim: experiments/2026-08-01-fix-decomposition-merge-pairing/PARKED.md lines 12-13 -->

- `budget_exhausted` is a fall-through label applied when the scheduler returned
  no stop reason (`text_runs.py:1022-1027`), not a measured cause.

<!-- verbatim: experiments/2026-08-01-fix-decomposition-merge-pairing/PARKED.md lines 14-16 -->

- Text workloads hard-return `TrialAuthority.OBSERVE_ONLY` (`authority.py:97-101`)
  pending a calibration-receipt verifier that does not exist, so no text run can
  mint a warrant or attack anything.

<!-- verbatim: experiments/2026-08-01-fix-decomposition-merge-pairing/PARKED.md lines 17-20 -->

- The ritual detector cannot fire in the zero-attack case that
  `docs/harness-spec-v1.3.md:446` names as the pathology: two of its four
  conditions sit behind `MIN_ATTACKS_FOR_RITUAL=5` and `attack_target_entropy`
  is `None` with no attacks.

<!-- verbatim: experiments/2026-08-01-fix-decomposition-merge-pairing/PARKED.md lines 21-22 -->

- `run-result.json` reported `epistemic_checks_passed: true` for a run that
  could not falsify anything.

<!-- verbatim: experiments/2026-08-01-fix-decomposition-merge-pairing/PARKED.md lines 23-25 -->

- The supported v6 text launch path cannot seed a failable criterion:
  `preparation.py` hardcodes `criteria=()` at five sites and `spec_from_text`
  supplies none. Needs an operator design decision, not a fix.

<!-- verbatim: experiments/2026-08-01-fix-decomposition-merge-pairing/PARKED.md lines 26-28 -->

- 11 of 42 roots under `experiments/` cannot be opened by the current `Harness`
  (`UnsupportedRunManifestVersionError`, all pre-v6). CLAUDE.md says old roots
  stay valid; whether these are deliberately retired is unestablished.

<!-- verbatim: experiments/2026-08-01-fix-decomposition-merge-pairing/PARKED.md lines 29-32 -->

- The simulation contract says "math is available and nothing else may be
  imported", which glm-5.2 read as permission to `import math`; the AST guard
  refuses it and denied the run's only simulation as `invalid_model_program`.

---

<a id="2026-08-02-map-falsification"></a>
## 2026-08-02-map-falsification

Origin: `experiments/2026-08-02-map-falsification/PARKED.md` — 6 open item(s).
Full original: `git show 6e64330fe:experiments/2026-08-02-map-falsification/PARKED.md`

*Its own framing, verbatim:*

> # Parked — repo-level gaps found while falsifying the map
> 
> One line each; found 2026-08-02, none fixed here.

<!-- verbatim: experiments/2026-08-02-map-falsification/PARKED.md lines 5-7 -->

- `SCHOOL_ROUTE_LEASE_MISMATCH` / `SCHOOL_ROUTE_ENDPOINT_MISMATCH`: disabling
  the firewall's lease-mismatch refusal leaves the entire test suite green;
  no test asserts either code (found via SEAM-manifest-x-schools).

<!-- verbatim: experiments/2026-08-02-map-falsification/PARKED.md lines 8-9 -->

- `resolve_conjecture_route` and `compile_criticism_assignments` are imported
  by no test anywhere (same seam).

<!-- verbatim: experiments/2026-08-02-map-falsification/PARKED.md lines 10-12 -->

- `test_failed_control_append_rolls_live_materialization_back` passes with
  `_commit`'s `_reset()` deleted — `WorkflowReplayState.digest` cannot see a
  failed append (found via SEAM-harness-x-workflow).

<!-- verbatim: experiments/2026-08-02-map-falsification/PARKED.md lines 13-14 -->

- No test covers a context receipt without scratch exposure; deleting that
  recovery guard passes the suite (found via SEAM-rules-x-scratch).

<!-- verbatim: experiments/2026-08-02-map-falsification/PARKED.md lines 15-17 -->

- Writer-side torn-tail repair was uncovered by the ring the seam doc named;
  the doc's ring now includes test_torn_append.py, but the gate-level gap is
  worth its own look (found via SEAM-harness-x-verification).

<!-- verbatim: experiments/2026-08-02-map-falsification/PARKED.md lines 18-21 -->

- The sweep instrument vs direct-load census delta (11 ERROR vs 14 raising
  manifests): three pre-v6 roots surface through verify_root_report as
  verdicts rather than errors — unexplained, measured only.

---

<a id="2026-08-03-change-driving-skill"></a>
## 2026-08-03-change-driving-skill

Origin: `experiments/2026-08-03-change-driving-skill/PARKED.md` — 3 open item(s).
Full original: `git show 6e64330fe:experiments/2026-08-03-change-driving-skill/PARKED.md`

*Its own framing, verbatim:*

> # Parked — noticed or deferred during this tranche, deliberately not done

<!-- verbatim: experiments/2026-08-03-change-driving-skill/PARKED.md lines 3-14 -->

- **R8, deferred in the operator's own words** ("the sub documents never
  mentions the seam documents they're involved with, and how to tell
  whether a modification is just isolated or requires directions from
  rec-seam document. But this job is a later task. For now, focus on the
  others."): a later tranche should (a) make every `docs/map/SUB-*.md`
  cross-reference the SEAM documents it participates in — note the
  `Seams:`/`Seams-undocumented:` headers already exist, so the job is
  likely surfacing them in prose plus the missing half — and (b) add a
  triage rule to SCHEMA.md or the SUB template for deciding isolated
  modification vs. REC-change-a-seam-guided modification. Ready-made
  inputs: `docs/map/SCHEMA.md` anatomy section, `REC-change-a-seam.md`
  steps 1-2, INDEX.md's seam matrix.

<!-- verbatim: experiments/2026-08-03-change-driving-skill/PARKED.md lines 15-16 -->

- A docs_verify mode for `.claude/skills/` checks — still parked from the
  dr-ask-the-right-question tranche.

<!-- verbatim: experiments/2026-08-03-change-driving-skill/PARKED.md lines 17-23 -->

- Flaky under parallel load:
  `tests/test_v6_nonconjecture_recovery.py::test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`
  failed once in a `-n 4` full gate on a loaded box (761s run), passed
  solo, with its file, and in the immediate full-gate rerun (3290/0).
  Zero src/tests changes in the failing tranche. Defect-family candidate:
  reproduce under load, diagnose order/timing dependence.

---

<a id="2026-08-03-change-rung1-sockets-on-paper"></a>
## 2026-08-03-change-rung1-sockets-on-paper

Origin: `experiments/2026-08-03-change-rung1-sockets-on-paper/PARKED.md` — 6 open item(s).
Full original: `git show 6e64330fe:experiments/2026-08-03-change-rung1-sockets-on-paper/PARKED.md`

*Its own framing, verbatim:*

> # Parked — noticed or deferred during this tranche, deliberately not done

<!-- verbatim: experiments/2026-08-03-change-rung1-sockets-on-paper/PARKED.md lines 3-6 -->

- **Rungs 2-7 of the modularisation ladder** (`docs/HANDOVER_2026-08-03.md`).
  This tranche is rung 1 only, per C1/A2. Rung 2 (buried choices become
  visible switches) is the natural next tranche when the operator wants to
  proceed.

<!-- verbatim: experiments/2026-08-03-change-rung1-sockets-on-paper/PARKED.md lines 7-11 -->

- **The `INDEX.md` Subsystems-table gap for `amendment`/`application`/
  `periphery`.** All three have real `SUB-*.md` documents (and got their
  `## Seams` section in this tranche) but are not listed in `INDEX.md`'s
  routing table. Out of scope per SPEC.md ("not requested"); a one-line
  addition if the operator wants it fixed.

<!-- verbatim: experiments/2026-08-03-change-rung1-sockets-on-paper/PARKED.md lines 12-19 -->

- **Every `Seams-undocumented:` pair this tranche glossed as "not yet
  analyzed" rather than "real" or "deliberately absent"** — roughly 30
  pairs across the 16 `SUB-*.md` files (e.g. `bridge x scratch`,
  `capabilities x llm`, `manifest x verification`, `ontology x scratch`,
  `application x verification`). R2 asked only that these be named and
  honestly glossed, not resolved; a dedicated tranche could investigate
  each and either confirm "deliberately absent" (like several this tranche
  DID confirm directly from existing checks) or write the seam document.

<!-- verbatim: experiments/2026-08-03-change-rung1-sockets-on-paper/PARKED.md lines 20-24 -->

- **14 of 20 `SEAM-*.md` documents have no `Sweep:` header**
  (`docs_verify --coverage`). SCHEMA.md's own rule: this is advisory,
  ratcheting in only "the next time the document is edited" — this
  tranche never edited a `SEAM-*.md` document's body, so it doesn't
  trigger the ratchet. Noted for whoever next touches one of those 14.

<!-- verbatim: experiments/2026-08-03-change-rung1-sockets-on-paper/PARKED.md lines 25-29 -->

- **Writing the SEAM documents themselves** for any `Seams-undocumented`
  pair, including the ones this tranche's own audit confirmed real
  (e.g. `harness x scratch`, `llm x schools`, `manifest x scratch`). R2
  asked for naming and glossing in prose, not full seam documents — SPEC.md
  called this out explicitly as out of scope.

<!-- verbatim: experiments/2026-08-03-change-rung1-sockets-on-paper/PARKED.md lines 30-34 -->

- **`bridge × ontology` stays genuinely unwritten** in `INDEX.md`'s seam
  matrix (coupling 15, no file) — the only row this tranche's INDEX.md
  fix (ERRATA E9) left as "not yet written" because it is actually true;
  everything else previously marked that way already had a real document.

---

<a id="2026-08-03-change-rung2-bridge-unification"></a>
## 2026-08-03-change-rung2-bridge-unification

Origin: `experiments/2026-08-03-change-rung2-bridge-unification/PARKED.md` — 4 open item(s).
Full original: `git show 6e64330fe:experiments/2026-08-03-change-rung2-bridge-unification/PARKED.md`

*Its own framing, verbatim:*

> # Parked — noticed or deferred during this tranche, deliberately not done

<!-- verbatim: experiments/2026-08-03-change-rung2-bridge-unification/PARKED.md lines 3-16 -->

- **R1's literal instruction ("change BridgeConfig's defaults") itself,
  as a future possibility.** This tranche did NOT flip `BridgeConfig`'s
  shared class-level defaults (`mode="legacy_thesis"`,
  `max_schema_repair_attempts=2`, `max_grounding_repair_attempts=4`,
  `output_section_limit=32`) to match the engaged preset's values —
  Amendment 1 records the operator's explicit choice not to, because
  those defaults are load-bearing for every bare `Config()` construction
  (a pinned test, `test_safe_defaults_are_bounded_and_features_remain_
  opt_in`, and the `deepreason config compile` CLI path). If the
  operator later decides the SHARED default really should change (e.g.
  because `legacy_thesis` is judged genuinely obsolete rather than a
  deliberate safe fallback), that is a separate, explicit future
  decision — not something this tranche implements or recommends.

<!-- verbatim: experiments/2026-08-03-change-rung2-bridge-unification/PARKED.md lines 17-23 -->

- **Rung 2's remaining inventory candidates, unchanged from tranche 1's
  own PARKED.md**: Group C's env-var-sourced switches
  (`DEEPREASON_SIMULATION_RUNNER`, `DEEPREASON_RESEARCH_ALLOWLIST`/
  `_MAX_REQUESTS`/`_MAX_SOURCES`, `DEEPREASON_CONFIG_REFEREE`) and Group
  D's `STANCE_LIBRARY` (content, not a switch). Neither addressed by
  this tranche; still the operator's call for any future tranche.

<!-- verbatim: experiments/2026-08-03-change-rung2-bridge-unification/PARKED.md lines 24-35 -->

- **`docs/map/CON-authority.md`'s "Adjacent, not authority" section
  placement.** This claim about `engaged_bridge_source()` lives in a
  document titled "Authority — who may change a Status," which it is
  not about. It is placed there because `CON-authority.md` is the only
  established `Owns:` home for `v6_policy.py`/`preparation.py`
  (from tranche 2), and creating a new document for one small hygiene
  fix would be disproportionate. If rung 2 (or a later rung) adds a
  THIRD unrelated claim to these same two files, that would be a signal
  worth acting on — a dedicated "preset construction" document might
  earn its keep at that point. Not created here; noted for whoever
  next finds themselves in the same position.

<!-- verbatim: experiments/2026-08-03-change-rung2-bridge-unification/PARKED.md lines 36-46 -->

- **No structural guard against a future `BridgeConfig`-bypassing
  regression.** Nothing prevents a future edit to `engaged_bridge_
  source()` from reverting to a bare literal dict again — the two tests
  (the pre-existing exact-dict check and this tranche's new
  built-through-`BridgeConfig` check) would catch VALUE drift but a
  reviewer could still hand-edit the function back to a literal without
  either test failing, as long as the literal's values still matched.
  No stronger enforcement (e.g. an AST-level check forbidding a bare
  dict literal as the return statement) was designed or requested;
  noted as a possible future hardening, not built here.

---

<a id="2026-08-03-change-rung2-config-inventory"></a>
## 2026-08-03-change-rung2-config-inventory

Origin: `experiments/2026-08-03-change-rung2-config-inventory/PARKED.md` — 6 open item(s).
Full original: `git show 6e64330fe:experiments/2026-08-03-change-rung2-config-inventory/PARKED.md`

*Its own framing, verbatim:*

> # Parked — noticed or deferred during this tranche, deliberately not done

<!-- verbatim: experiments/2026-08-03-change-rung2-config-inventory/PARKED.md lines 3-7 -->

- **Tranche 2 (the `engaged_criticism_policy` switch itself)** — R5-R8,
  explicitly a separate, later tranche per the operator's own split.
  "further switches wait for the operator to pick them" (R4) — this
  tranche does not recommend which inventory candidate goes first beyond
  the one the operator already named.

<!-- verbatim: experiments/2026-08-03-change-rung2-config-inventory/PARKED.md lines 8-14 -->

- **Group B (`BridgeConfig` vs `engaged_bridge_source()`)** — a genuinely
  different-shaped candidate from the named example (a `Config` home
  already exists; the preset bypasses it with an inline dict instead of
  named per-field defaults). Not resolved into a switch here; worth the
  operator's explicit attention before it becomes a tranche, since "wire
  the preset to the existing Config fields" is a different, arguably
  simpler shape of change than "invent a new Config field."

<!-- verbatim: experiments/2026-08-03-change-rung2-config-inventory/PARKED.md lines 15-21 -->

- **Group C's env-var-sourced switches** (`DEEPREASON_SIMULATION_RUNNER`,
  `DEEPREASON_RESEARCH_ALLOWLIST`/`_MAX_REQUESTS`/`_MAX_SOURCES`,
  `DEEPREASON_CONFIG_REFEREE`) — plausibly `Config`-shaped (they already
  flow into the manifest and qualification subject), but converting an
  env-var invocation surface to a `Config` field changes how operators
  invoke the preset, not just where a literal lives — a larger question
  than Group A's literal switches, not decided here.

<!-- verbatim: experiments/2026-08-03-change-rung2-config-inventory/PARKED.md lines 22-26 -->

- **`DEEPREASON_DISABLE_V6_LAUNCHES`/`DEEPREASON_RELEASE_POLICY`** — noted
  in INVENTORY.md as PROBABLY the wrong shape for a `Config` migration at
  all (deliberately launch-only rollback levers, per
  `runtime/launch_policy.py`'s own docstring — "Rollback is deliberately a
  launch-only concern"). Recorded for completeness, not recommended.

<!-- verbatim: experiments/2026-08-03-change-rung2-config-inventory/PARKED.md lines 27-31 -->

- **`STANCE_LIBRARY`** (Group D, `capture/schools.py`) — hard-coded
  outside `config.py` but content curation, not a mode switch (no
  alternative value to choose between). Not recommended as a switch
  candidate; noted only because it is technically "hard-coded" and the
  sweep's own methodology (rung 1's five sockets) surfaced it.

<!-- verbatim: experiments/2026-08-03-change-rung2-config-inventory/PARKED.md lines 32-36 -->

- **An exhaustive, unbounded scan of every hard-coded constant in
  `src/deepreason/`** (125k lines) beyond the bounded sweep (preset files
  + rung 1's five sockets + `config.py`) — SPEC.md's A1 explicitly scoped
  this; a broader sweep is available on request.

---

<a id="2026-08-05-fix-smoke-entry-point-reader"></a>
## 2026-08-05-fix-smoke-entry-point-reader

Origin: `experiments/2026-08-05-fix-smoke-entry-point-reader/PARKED.md` — 4 open item(s).
Full original: `git show 6e64330fe:experiments/2026-08-05-fix-smoke-entry-point-reader/PARKED.md`

*Its own framing, verbatim:*

> # Parked — noticed during the smoke tranche, not done

<!-- verbatim: experiments/2026-08-05-fix-smoke-entry-point-reader/PARKED.md lines 3-69 -->

## S1 — the operational smoke's own loopback fixture stops serving, so it times out at `qualify` (SECOND DEFECT, blocks this GOAL's third criterion)

**This is why GOAL.md's `wheel_operational_smoke.py -> exits 0`
criterion is NOT met.** It is a defect distinct from the entry-point
reader, it is not caused by this tranche's change, and per the
orchestrator's stop condition ("a command fails twice the same way")
the dig was stopped and reported rather than improvised into a second
fix inside a one-goal tranche.

**The typed record, twice, identically:**

    "schema": "deepreason-wheel-operational-failure-v4",
    "stage": "qualify",
    "failure_kind": "timeout",
    "timeout": true,
    "mcp_liveness": "not_started",
    "first_lifecycle_state": "not_observed"

**Not caused by this tranche.** The complete diff to
`scripts/wheel_operational_smoke.py` is three lines — the schema sha and
two tool names — and all three are read at the MCP stage, which the run
never reaches (`mcp_liveness: not_started`). `STAGE_QUALIFY` precedes
them.

**What the evidence shows, and it is not slowness.** Measured on a
`--keep` run while it was stuck:

- The `deepreason qualify --yes` subprocess accumulated **2 seconds of
  CPU across 175 seconds elapsed, flat** across three samples. It is
  blocked, not working.
- Its main thread sits in `futex_do_wait`; its four worker threads all
  sit in `hrtimer_nanosleep` — the shape of a connect-fail/backoff loop,
  not of request processing.
- The qualify process holds **no socket file descriptors at all** (fds
  0, 1, 2 only).
- Nothing is listening on the profile's endpoint:
  `http://127.0.0.1:52037/v1` → `[Errno 111] Connection refused`, and no
  `/proc/net/tcp` LISTEN entry for that port exists.
- The smoke's own process, which starts the fixture as
  `threading.Thread(target=server.serve_forever, daemon=True)` at
  `scripts/wheel_operational_smoke.py:1245-1247`, was down to **one
  thread and zero socket fds** — the serving thread had exited and
  released the socket while the main thread went on waiting out the
  600s subprocess timeout.

**Ruled out — the container cannot serve loopback HTTP.** A control
`ThreadingHTTPServer` bound in the same container was reachable
immediately on its assigned port. Loopback TCP works here; this
fixture's server specifically stopped.

**What is NOT yet known**, and is the next tranche's job: why the
serving thread exits. Candidates not investigated — an unhandled
exception inside the handler killing `serve_forever`; the daemon thread
being reaped; a port-reuse or bind race; or an interaction with the
600s `_run` timeout path. The diagnosis should start from the record
(a `--keep` run with the server thread instrumented), not from reading
the handler.

**Why it did not surface before.** `wheel_smoke.py` has been red since
`4940b5f7` (2026-07-28) and CI runs the two smokes as consecutive steps
in the same job (`.github/workflows/wheel-smoke.yml`), so the operational
step has not been reached on a green predecessor in over a week. Fixing
the reader is what made this visible — which is the value of the fix,
not a regression from it.

Suggested disposition: its own `deepreason-orchestrator` tranche.

<!-- verbatim: experiments/2026-08-05-fix-smoke-entry-point-reader/PARKED.md lines 70-80 -->

## S2 — both smokes carry byte-identical duplicate pins

`EXPECTED_MCP_TOOLS` and `EXPECTED_MCP_SCHEMA_SHA256` exist twice, once
in each script, and were identically stale before this tranche. Two
copies of one pin can drift apart, and the next person to refresh one
may not know the other exists. De-duplicating into a shared module is a
refactor rather than this defect, and would have required touching a
third file.

Suggested disposition: small change tranche.

<!-- verbatim: experiments/2026-08-05-fix-smoke-entry-point-reader/PARKED.md lines 81-89 -->

## S3 — nothing in `docs/map/` covers `scripts/`

`grep -rl "wheel_smoke" docs/map/` → no hits. The map describes
`src/deepreason/` by charter, and `scripts/` is navigated by convention.
That was defensible while the smokes were invisible to the workflow;
`20f2c8d1` has just named them in `CLAUDE.md` as the third instrument,
so the gap is now a visible one. Not this tranche's job — the fix
touches no `src/` file, so nothing the map currently describes moved.

<!-- verbatim: experiments/2026-08-05-fix-smoke-entry-point-reader/PARKED.md lines 90-96 -->

## S4 — carried, still parked

P1a (ERRATA E5 misidentifies the no-manifest three), P1b (the
delivery-measurement gap), P1e (a `src/` mutation inside a worktree is
never loaded under an editable install), and P7 (the round-robin arm's
`attempt-validity` violation) all remain open and untouched.

---

<a id="2026-08-08-change-rung-g1-actual-diff-budget"></a>
## 2026-08-08-change-rung-g1-actual-diff-budget

Origin: `experiments/2026-08-08-change-rung-g1-actual-diff-budget/PARKED.md` — 1 open item(s).
Full original: `git show 6e64330fe:experiments/2026-08-08-change-rung-g1-actual-diff-budget/PARKED.md`

*Its own framing, verbatim:*

> # Parked — found during Rung G1 (actual-diff budget gate), not fixed

<!-- verbatim: experiments/2026-08-08-change-rung-g1-actual-diff-budget/PARKED.md lines 3-33 -->

## P1 — `.claude/skills/README.md` named in task instructions, absent
on this tranche's own branch (not a defect — a branch-timing artifact)

**Where found:** session preflight (Q1, REQUEST.md), before any code
was read. The task instruction said "Read CLAUDE.md in full first,
then .claude/skills/README.md." `.claude/skills/` on this tranche's
base commit (`d4f63007`) contains only skill subdirectories, no
`README.md`.

**Corrected finding (checked again at park time, not the original
guess):** the file is NOT missing from the project — it exists on
`origin/claude/monitor-session-handover-63ajqv`'s current tip
(`2c9a2023`), along with three skills (`dr-ask-the-right-question`,
`dr-drive-harness`, `dr-explain-to-operator`) this tranche's branch
also does not carry. This tranche's branch was deliberately reset to
`d4f63007` — an EARLIER commit on that same monitor branch — per this
tranche's own task instructions, before the monitor session's later
work (including `README.md` and those three skills) landed on top of
it. This is expected branch divergence, not an absent artifact: the
file exists in the project, just not yet on this branch's own history.

**Not this tranche's finding to fix, and no action is actually owed:**
out of scope regardless (C1: "Scope is G1 alone"); satisfied instead
by reading the skill directory listing and `dr-change-orchestrator`'s
own `SKILL.md`, which serves the same orientation purpose. The
discrepancy resolves itself the ordinary way — whenever this branch's
work is next rebased onto or merged with the monitor branch's later
state, `README.md` and the three newer skills arrive with it. No
follow-up prompt is needed; this entry exists so a future reader does
not re-diagnose the same "missing file" surprise from scratch.

---

<a id="2026-08-09-change-errata-sweep-and-automation"></a>
## 2026-08-09-change-errata-sweep-and-automation

Origin: `experiments/2026-08-09-change-errata-sweep-and-automation/PARKED.md` — 1 open item(s).
Full original: `git show 6e64330fe:experiments/2026-08-09-change-errata-sweep-and-automation/PARKED.md`

*Its own framing, verbatim:*

> # Parked — not done, not promised

<!-- verbatim: experiments/2026-08-09-change-errata-sweep-and-automation/PARKED.md lines 3-36 -->

## P1 — `test_bronze_report.py`'s gate_measures/gate_blocked mismatch
still fails the full gate (already known: D2's PARKED P-D2-3)

WHAT: `pytest tests/ -q -n 4` fails
`test_bronze_report.py::test_census_totals_internally_consistent`
(`assert counts["gate_blocked"] == census["streams"][stream]
["gate_measures"]` -> `159 == 165`). This tranche independently
reconfirmed the failure is pre-existing (byte-identical on a fresh
`origin/main` checkout, isolated venv) and out of this docs-only
tranche's scope (no `src/`/`tests/` file touched). It is the SAME
defect already found and parked by
`experiments/2026-08-08-change-pipeline-design-d2/PARKED.md` item
P-D2-3, dated 2026-08-08 — not a new discovery, a re-confirmation that
it is still unresolved five tranches later.

Not fixed here, on purpose: this tranche's `REQUEST.md` scopes it to
`docs/ERRATA.md` and two `.claude/skills/` files; a bronze-census
arithmetic defect is a `src/`/`tests/` code fix, not a committed
document's claim shown wrong, so it belongs to
`deepreason-orchestrator`, never this ledger's or this workflow's own
change track.

Ready-to-send prompt: "`tests/test_bronze_report.py::
test_census_totals_internally_consistent` fails with `assert 159 ==
165` (gate_blocked vs gate_measures) on a clean `origin/main` checkout
— confirmed pre-existing and unrelated to any recent docs-only tranche.
Diagnose starting from `dr-set-goal`, using
`experiments/2026-08-08-change-pipeline-design-d2/PARKED.md`'s P-D2-3
entry as the prior investigation record (it already narrows the
mismatch to the bronze census's gate-Measure counting) and this
tranche's `VALIDATION.md` Full-gate section as the reconfirmation
evidence (byte-identical failure on `origin/main`, isolated venv,
2026-08-09)."

---

<a id="2026-08-11-change-docs-reorg-steps-3-4"></a>
## 2026-08-11-change-docs-reorg-steps-3-4

Origin: `experiments/2026-08-11-change-docs-reorg-steps-3-4/PARKED.md` — 1 open item(s).
Full original: `git show 6e64330fe:experiments/2026-08-11-change-docs-reorg-steps-3-4/PARKED.md`

*Its own framing, verbatim:*

> # Parked (found mid-tranche, not requested, not fixed here)

<!-- verbatim: experiments/2026-08-11-change-docs-reorg-steps-3-4/PARKED.md lines 3-44 -->

## P1 — bare `pytest` on PATH resolves to an isolated interpreter without the `deepreason` editable install

Found running CS3 (the full gate). `which pytest` ->
`/root/.local/bin/pytest`, whose shebang points at
`/root/.local/share/uv/tools/uv-managed` interpreter — a `uv`-tool
install, separate from `/usr/local/lib/python3.11/dist-packages` where
`pip install -e . --break-system-packages` puts the editable
`deepreason` package. Running bare `pytest tests/ -q -n 4` (exactly the
command CLAUDE.md's "Build and test" section prints) fails immediately:
`ModuleNotFoundError: No module named 'deepreason'` from
`tests/conftest.py:5`. `python -m pytest tests/ -q -n 4` (using
`/usr/local/bin/python`, confirmed via `pip show deepreason`) runs
correctly.

This is a container/environment PATH quirk, not a DeepReason code
defect — out of scope for a docs-reorg change tranche either way. But
it will cost the next session the same ~10 minutes of misdiagnosis it
cost this one (a `ModuleNotFoundError` reads exactly like a broken
install), and CLAUDE.md's own printed gate command is the one that
fails. Ready-to-send prompt for whoever picks this up:

> Route: `deepreason-orchestrator` (or a `dr-change-orchestrator`
> tranche if the operator wants CLAUDE.md's own command text changed).
> Goal: bare `pytest` on this container's PATH resolves to a uv-tool
> interpreter lacking the `deepreason` editable install, so
> CLAUDE.md's own "Build and test" section's literal `pytest tests/ -q
> -n 4` command fails with `ModuleNotFoundError: No module named
> 'deepreason'` even in a correctly-provisioned container.
> Evidence: `which pytest` -> `/root/.local/bin/pytest` (uv-tool
> shebang); `pip show deepreason` -> `Location:
> /usr/local/lib/python3.11/dist-packages`, i.e. a DIFFERENT
> interpreter's site-packages. `python -m pytest tests/ -q -n 4`
> succeeds using the correct interpreter.
> End state: either CLAUDE.md's gate command is corrected to
> `python -m pytest tests/ -q -n 4` (if this PATH shape is
> container-standard), or the container provisioning is fixed so bare
> `pytest` resolves to the interpreter with the editable install (if
> the uv-tool shadowing is itself the defect). Operator should say
> which is intended before either is changed — this could also be a
> one-off quirk of this particular container instance, not a standing
> fact about the fleet.

---

<a id="2026-08-14-change-rung1-vocabulary-groundwork"></a>
## 2026-08-14-change-rung1-vocabulary-groundwork

Origin: `experiments/2026-08-14-change-rung1-vocabulary-groundwork/PARKED.md` — 4 open item(s).
Full original: `git show 6e64330fe:experiments/2026-08-14-change-rung1-vocabulary-groundwork/PARKED.md`

*Its own framing, verbatim:*

> # Parked — found during Rung 1, deliberately NOT worked

<!-- verbatim: experiments/2026-08-14-change-rung1-vocabulary-groundwork/PARKED.md lines 3-22 -->

## P1 — `Config.RECRIT_STANDING` and `_standing_recrit_pool` still use "standing" in a third sense

**What.** Rung 1 freed the word "standing" at two of its three sites. The third
is the scheduler's: `_standing_recrit_pool` and `Config.RECRIT_STANDING` mean
*the pool of still-standing survivors to re-criticize*, not frame role.

**Why parked, not fixed.** `RECRIT_STANDING` is a `Config` FIELD NAME. It is
pinned by a check in `DR-SUB-scheduler`, it is readable from profile YAML, and
`_versioned_source_config_data` in `run_manifest.py` has to be told about config
keys explicitly (the `ENGAGED_CRITICISM_AUTHORITY` trap in
`INV-frozen-surfaces.md`). Renaming it is a compatibility decision, not
vocabulary work, and Rung 1's whole point was to be the cheapest possible rung.

**Where it goes.** Rung 4 of the v2 program, where the calculus's standing axis
actually arrives and the collision stops being cosmetic. Recorded in the Traps
section of `docs/map/CON-standing-and-background.md` so a reader meeting the word
in the scheduler meanwhile reads it correctly.

---

<!-- verbatim: experiments/2026-08-14-change-rung1-vocabulary-groundwork/PARKED.md lines 23-46 -->

## P2 — `tools/root_sweep.py` cannot finish on this tree, and loses everything when it doesn't

**What.** Two independent defects, both hit during this rung's A4:

1. **Write-once at the end.** The tool accumulates every row in memory and calls
   `out.write_text(...)` after the loop. A run killed by a timeout produces an
   empty file, so 25 minutes of work yields nothing. Measured twice here.
2. **It cannot complete inside a reasonable timeout.** With the baseline's
   known-hang root (`experiments/live_tri_2026-07-27/
   run-c5ab654afd1b4aa131aede83bdca0f03`) and the generally degraded per-root
   throughput already parked in
   `experiments/2026-08-13-change-smoke-currency-audit/PARKED.md` P1, the full
   107-root sweep took **two passes of ~50 minutes each**. `AUDIT_BASELINES.md`
   already tells the reader to "run the sweep under `timeout` and exclude this
   root" — but the tool has **no exclude flag** (the CLI gap parked as
   `experiments/2026-08-13-audit/PARKED.md` P3), so following the documented
   advice requires editing a copy of the script.

**How A4 was actually obtained** (recorded so the next rung does not rediscover
it): a scratchpad copy of the same script with exactly two changes — skip the
known-hang root with a `SKIPPED` row, and write the output file after every root
so a timeout costs progress instead of everything — run in two passes, the second
skipping roots already present in the first.

<!-- verbatim: experiments/2026-08-14-change-rung1-vocabulary-groundwork/PARKED.md lines 47-85 -->

### Ready-to-send prompt

```
Fix tranche: tools/root_sweep.py loses all progress on timeout and cannot
complete on the current tree. Route through deepreason-orchestrator.

EVIDENCE (measured 2026-08-14, experiments/2026-08-14-change-rung1-
vocabulary-groundwork/VALIDATION.md A4 and PARKED.md P2): the tool writes
its output once, after the loop, so two separate runs killed at 25 and 50
minutes produced empty files. The full 107-root sweep required two ~50
minute passes from a patched copy. AUDIT_BASELINES.md instructs the reader
to exclude the known-hang root, but the tool takes only an output path --
no exclude flag (already parked as experiments/2026-08-13-audit/PARKED.md
P3, the CLI gap).

SCOPE, three parts:
(1) write incrementally -- one row per root, flushed, so a killed run
    leaves usable partial evidence;
(2) add the exclude/skip surface AUDIT_BASELINES.md already assumes exists,
    and a --resume that skips roots already present in the output file;
(3) decide whether the per-root slowdown is worth its own diagnosis or
    whether (1)+(2) make it tolerable -- the throughput defect is parked
    separately at experiments/2026-08-13-change-smoke-currency-audit/
    PARKED.md P1 and should NOT be silently absorbed here.

GUARDRAIL: this tool is the instrument that protects every committed root.
Its OUTPUT FORMAT is compared across tranches (committed sweep files exist
in at least six tranche directories) -- adding a column or reordering
fields breaks those comparisons. Change how it writes, not what it writes.

TESTS: a sweep killed mid-run leaves a valid partial file; --resume over
that file produces the same total set as an uninterrupted run; the output
of an unpatched full run is byte-identical to today's for the same roots.
GATE: full gate at the boundary, docs_verify full. Map moves in the same
commit. Commit and push at every phase boundary.
```

---

<!-- verbatim: experiments/2026-08-14-change-rung1-vocabulary-groundwork/PARKED.md lines 86-96 -->

## P3 — the CLAUDE.md design law and its INV document are split across two rungs

**What.** The operator's signal-contract design law is ledgered in CLAUDE.md by
this rung; its `INV-` map document and two `REC-` recipes belong to Rung 1b,
because `docs_verify --audit` refuses checks that cannot fail and an INV document
about an unbuilt mechanism would ship vacuous ones.

**Not a defect** — a deliberate split argued in `RECONCILIATION.md` §2L. Recorded
here only so that a reader who finds the law without the document knows the
document is scheduled rather than missing.

---

<a id="2026-08-15-change-rung2-premise-channel"></a>
## 2026-08-15-change-rung2-premise-channel

Origin: `experiments/2026-08-15-change-rung2-premise-channel/PARKED.md` — 2 open item(s).
Full original: `git show 6e64330fe:experiments/2026-08-15-change-rung2-premise-channel/PARKED.md`

*Its own framing, verbatim:*

> # Parked — Rung 2, step 2

<!-- verbatim: experiments/2026-08-15-change-rung2-premise-channel/PARKED.md lines 3-31 -->

## P1 — the premise channel is built but not yet WIRED

**What is built** (`src/deepreason/premises.py`, 17 tests): the attribution and
resolution shapes, the mention-law check, the derived orphan predicate with both
grades, the three resolutions with reversibility, the producer's decision rule,
and the operator's siren case passing end to end.

**What is not**: nothing calls the producer rule yet, so no run will produce an
attribution on its own. Three pieces remain, and they are the ones that touch
running code rather than the channel's own shape:

1. **S3 — the premise rent battery.** A demarcation criterion pinned onto premise
   artifacts requiring a SUBSTANTIVE commitment (reuse
   `measures/reach.py::_substantive`), so a premise that forbids nothing is
   refuted by program. This is what makes the siren case work on a LIVE run
   rather than in a test that refutes the premise by hand. It also needs the
   `crit` half of `active()`, today an unimported stub in
   `measures/demarcation.py` (drift row M-1).
2. **S6b — the wiring.** The critic pack gains the invitation; the scheduler
   consults `premise_work_invited` and deprioritises marked problems and skips
   retired ones. Attention only.
3. **The three detection signals** — problem thrash, attack-target entropy, the
   independence-resolution rate — declared through the Rung 1b-i contract for
   Rung 1b-ii's policy to consume (Amendment 3, R39).

**Why it stopped here.** The channel is a complete, tested, gate-green unit and
the wiring is a separable one. Splitting at this seam keeps a half-finished
scheduler change out of the record.

<!-- verbatim: experiments/2026-08-15-change-rung2-premise-channel/PARKED.md lines 32-66 -->

### Ready-to-send prompt

```
Rung 2 step 2 of the v2 calculus program: wire the premise channel. Route
through dr-change-orchestrator.

READ FIRST: experiments/2026-08-15-change-rung2-premise-channel/SPEC.md
(S3, S6b), docs/map/CON-problem-layer-lifecycle.md, and
src/deepreason/premises.py -- the channel is built and tested; this
tranche connects it.

SCOPE, three parts:
(1) the premise rent battery: a demarcation criterion on premise artifacts
    requiring a SUBSTANTIVE commitment (reuse measures/reach.py::_substantive
    -- structural checks must not satisfy it, per the self-immunisation trap
    in rules/warrants.py::formally_backed). Build the crit half of active();
    measures/demarcation.py is an unimported stub today.
(2) the wiring: critic pack invitation + scheduler consulting
    premise_work_invited, deprioritising marked problems and skipping
    retired ones. ATTENTION ONLY -- no label may move.
(3) declare the three detection signals through the Rung 1b-i contract:
    problem thrash, attack-target entropy, independence-resolution rate.

HARD CONSTRAINTS: no problem is minted from a conjecture's failure (H1 --
failure may redirect attention only); nothing ranks or admits a conjecture
differently for carrying or lacking an attribution; no new LLM role (it
would move every qualification subject digest).

TESTS: the producer fires in an offline run of the actual loop, not just in
a unit test of the rule; a live premise falls by demarcation with no hand
-written refutation; a marked problem is deprioritised and a retired one is
not selected. GATE: full gate 0 failed, docs_verify full, map moves in the
same commit.
```

---

<a id="2026-08-15-change-rung3a-h1-successor-deletion"></a>
## 2026-08-15-change-rung3a-h1-successor-deletion

Origin: `experiments/2026-08-15-change-rung3a-h1-successor-deletion/PARKED.md` — 2 open item(s).
Full original: `git show 6e64330fe:experiments/2026-08-15-change-rung3a-h1-successor-deletion/PARKED.md`

*Its own framing, verbatim:*

> # Parked — Rung 3a

<!-- verbatim: experiments/2026-08-15-change-rung3a-h1-successor-deletion/PARKED.md lines 3-28 -->

## P1 — is `easy.py`'s repair-successor a SECOND H1 site?

**What.** H1 deleted the refuted⇒successor branch from `scan_spawns`. A census
run while executing this rung found a second, live producer of the same trigger
that H1 was never stated about:

    src/deepreason/easy.py::seed_component
        {"trigger": "successor", "from": [repair_of]}
    src/deepreason/workflows/website.py:1643, 1717   the two live call sites

It is arguably the same shape — integration criticism implicates a component,
and a problem is minted from that implication. It is also arguably not: H1 was
stated about the reasoning loop's failed verdict, the staged website workflow is
a deterministic pipeline rather than a frontier, and its repair problems are
bounded by the manifest's component list rather than growing without limit.

**Why it is parked and not decided.** The operator said this rung ships ALONE,
and answering either way changes `easy.py` and `workflows/website.py`. Deciding
it here would have broken the one constraint the rung exists under. It is also
genuinely the operator's: H1 is a pre-decided doctrine item, and its reach is a
doctrine question, not an implementation detail.

**It is why the enum member survives.** Not compatibility — the 2026-08-14 law
retired that — but liveness. Reading `SpawnTrigger.SUCCESSOR`'s survival as "H1
was not applied" is the specific misreading `DR-SUB-rules` now warns against.

<!-- verbatim: experiments/2026-08-15-change-rung3a-h1-successor-deletion/PARKED.md lines 29-61 -->

### Ready-to-send prompt

```
Decide whether H1 reaches the staged website pipeline.

H1 deleted the refuted-verdict successor trigger from the reasoning loop
(experiments/2026-08-15-change-rung3a-h1-successor-deletion/). A second
producer of trigger: "successor" survives, in a different subsystem:
easy.py::seed_component mints a component REPAIR problem when integration
criticism implicates a component, called from workflows/website.py:1643
and :1717.

Same shape (a problem minted from a failure) or not (a bounded pipeline
step over a fixed manifest, not a growing frontier)?

Road A -- H1 reaches it: re-found repair problems on a non-failure trigger,
or remove the auto-mint and let the pipeline re-pose explicitly. ~150-250
lines across easy.py, workflows/website.py, tests/test_chunked.py,
tests/test_website_state_machine.py. THEN SpawnTrigger.SUCCESSOR can be
deleted and the v2 trigger vocabulary matches the behaviour.

Road B -- H1 stops at the reasoning loop: record the boundary in
docs/map/SUB-rules.md and CON-problem-layer-lifecycle, keep the enum
member permanently, and state in one sentence why a pipeline repair is
not a conjecture's failure. ~30 lines, documentation only.

Recommendation: B, with the boundary written down. H1's recorded purpose
is that a failed conjecture must not grow the frontier without anyone
posing the question; a component repair problem is posed by the pipeline
against a fixed manifest and cannot cascade. But this is doctrine, and
doctrine is yours.
```

---

<a id="2026-08-22-audit-scalarization"></a>
## 2026-08-22-audit-scalarization

Origin: `experiments/2026-08-22-audit-scalarization/PARKED.md` — 3 open item(s).
Full original: `git show 6e64330fe:experiments/2026-08-22-audit-scalarization/PARKED.md`

*Its own framing, verbatim:*

> # Parked — scalarization census, 2026-08-22
> 
> This tranche is READ-ONLY on `src/` and `tests/` by operator instruction. Every
> finding below is a ready-to-send prompt for a LATER tranche. Nothing here was
> fixed, and nothing here should be fixed inside this tranche.
> 
> One prompt per SELECTION-BY-SCORE finding (P1) and per finding-grade scalar note
> (P2), plus the map gap the preflight turned up (P3).
> 
> ---

<!-- verbatim: experiments/2026-08-22-audit-scalarization/PARKED.md lines 12-69 -->

## P1 — SELECTION-BY-SCORE: the evidence pack ranks survivors by `hv` and truncates

**WHAT:** `bridge/evidence_pack.py:757` sorts the ACCEPTED partition by
`-hv` and `:766` truncates it to `MAX_EVIDENCE_PACK_ITEMS`, so when survivors
exceed the cap a scalar — not partition membership plus a typed tie-break —
decides which survivors reach the delivered grounded-application evidence pack.
An unmeasured survivor sorts below an `hv = 0.0` one (`-1.0` default), and `hv`
is a lazy one-per-cycle spot-check that only runs when the run has a `variator`
role, so pack membership can turn on an attention fact.

```
Route: dr-change-orchestrator (this is a design change, not a defect —
nothing violates a documented guarantee; the shape is what is in question).

ONE GOAL: decide, and implement, what the grounded-application evidence pack
does when the ACCEPTED survivor set exceeds MAX_EVIDENCE_PACK_ITEMS — so that
which survivors reach a delivered answer is decided by partition membership
plus a TYPED tie-break, never by a scalar, and so that any truncation is
RECORDED rather than silent.

Read first, in this order:
  - experiments/2026-08-22-audit-scalarization/CENSUS.md section 4 (the
    finding, with the reason it is medium and not severe)
  - docs/RESEARCH_SHAPE_CRITIQUE_2026-08-22.md section 2(A) — the -10pp /
    +16.7 result that motivates the whole question
  - docs/map/SUB-adjudication.md (the partition is the product)
  - docs/map/SUB-bridge.md and SEAM-bridge-x-manifest.md BEFORE either side
  - src/deepreason/easy.py::pick_survivor — the repo's own model of a lawful
    best-candidate selection: partition membership, then (event_seq, aid)
  - src/deepreason/scheduler/scheduler.py::_select_problem — the operator-seed
    tie-break law, the same shape applied to problems

Evidence pointers:
  src/deepreason/bridge/evidence_pack.py:744-766 (survivors) and :849
    (refutations, same shape)
  src/deepreason/measures/hv.py — contains NO reference to Status, so hv is
    adjudication-independent; this is why the finding is medium, and the fix
    must not accidentally make it adjudication-dependent
  src/deepreason/scheduler/scheduler.py::_lazy_hv — one measurement per cycle,
    variator-gated: the reason many survivors carry no hv at all

Candidate roads to price for the operator (do not pick one before SPEC.md):
  (a) replace the sort key with a purely typed one — e.g. (event_seq, ref),
      matching pick_survivor's "longest-standing survivor" rationale
  (b) keep hv as an ordering but emit a typed truncation record naming what
      was dropped and by which key, so the pack never silently omits survivors
  (c) both

End state: SPEC.md with per-requirement acceptance checks; the change; a
regression test that FAILS on the current sort-and-truncate and passes after;
full gate 0 failed; map moved in the same commit.

Do NOT widen this into a general measures review, and do NOT touch
adjudication/ — the partition itself is correct and is not the subject.
```

---

<!-- verbatim: experiments/2026-08-22-audit-scalarization/PARKED.md lines 70-121 -->

## P2 — Compensatory scalar over an adjudication result: the appellate docket

**WHAT:** `informal/appellate.py:22-57` builds one summed `score` in which an
adjudication-derived term (`+2` when a discrimination problem has ≥2 ACCEPTED
rivals) is added to non-adjudication terms (ensemble-split `+3`, audit-hit `+2`,
guard-block `+1`), sorts by `-score`, and truncates to `USER_RULINGS_BUDGET`.
This is the only compensatory weighted sum in the codebase with an adjudication
result as an addend. It is lawful today because it allocates ATTENTION only and
its sole caller is the operator-facing `deepreason` CLI (`cli/main.py:1238`) —
all three of which a later change could remove without anyone noticing.

```
Route: dr-change-orchestrator.

ONE GOAL: decide whether the appellate docket's ranking should stay a
compensatory weighted sum with an adjudication-derived addend, or become a
lexicographic/stratified rank in which the adjudication term can order WITHIN a
stratum but never trade against non-adjudication evidence — and record the
decision either way, so a future reader knows it was chosen rather than
inherited.

Read first:
  - experiments/2026-08-22-audit-scalarization/CENSUS.md section 5b (the full
    list of nine label-to-scalar conversions; this is the only compensatory one)
  - docs/RESEARCH_SHAPE_CRITIQUE_2026-08-22.md section 2(A), in particular
    "any scheme that eventually recombines the channels into one scalar
    reinherits the conflation it was built to remove"
  - src/deepreason/informal/appellate.py (whole file — it is 100 lines)
  - src/deepreason/informal/standards.py:88-99 — precedent_slice, and its
    "pack ordering is the only authority a user ruling has (N1: never status
    privilege)", which is the constraint any redesign must preserve

Evidence pointers:
  src/deepreason/informal/appellate.py:24-27 (bump), :41-46 (the adjudication
    addend), :48 (the sort), :57 (the cap)
  src/deepreason/cli/main.py:1238 (the sole caller — confirm it is still sole)
  src/deepreason/config.py:294 (USER_RULINGS_BUDGET default 2 — the cap is
    small, which is what makes the ranking decisive)

The operator's judge-suspicion law applies here (CLAUDE.md: judges "prosecute
without any discernable discrimination"): the docket spends the operator's own
attention, which is scarcer than any judge seat, so the bar for what may
reorder it is higher, not lower.

End state: SPEC.md, the change or a recorded decision NOT to change with its
reason, regression test, full gate 0 failed, map moved in the same commit.

Do NOT touch the docket's non-adjudication signals — they are out of scope.
```

---

<!-- verbatim: experiments/2026-08-22-audit-scalarization/PARKED.md lines 122-155 -->

## P3 — Map gap: three SUB- documents are absent from INDEX.md's routing table

**WHAT:** `docs/map/` holds 18 `SUB-*.md` files; `docs/map/INDEX.md`'s
Subsystems table has 15 rows. `SUB-application.md`, `SUB-amendment.md` and
`SUB-periphery.md` exist but cannot be reached by routing — this census reached
`SUB-application.md` by filename, which is exactly what `INDEX.md` says the map
exists to prevent. Verified: `ls docs/map/SUB-*.md | wc -l` = 18;
`grep -c '^| `SUB-' docs/map/INDEX.md` = 15.

```
Route: dr-change-orchestrator (a map change, small).

ONE GOAL: add the three missing rows to docs/map/INDEX.md's Subsystems table
(SUB-application.md, SUB-amendment.md, SUB-periphery.md), each with an
accurate one-line "Covers" cell derived from the document's own Owns: header,
and add a check that would FAIL if a SUB- document is added without a routing
row.

Read first: docs/map/SCHEMA.md (the contract for writing map documents),
docs/map/INDEX.md.

Evidence: ls docs/map/SUB-*.md | wc -l  -> 18
          grep -c '^| `SUB-' docs/map/INDEX.md -> 15

The check is the point — a routing table that can silently fall behind is the
same failure the map's re-derivation discipline exists to prevent. Something
like:
  check: python -c "import pathlib,re; d=pathlib.Path('docs/map'); files={p.name for p in d.glob('SUB-*.md')}; rows=set(re.findall(r'`(SUB-[a-z-]+\\.md)`', (d/'INDEX.md').read_text())); assert files==rows, sorted(files^rows)"
(run it before writing it down — SCHEMA.md's rule.)

End state: INDEX.md updated with the new check passing, python
tools/docs_verify.py 0 failed, one commit.
```

---

<a id="2026-08-24-change-rung5-promotion-criteria"></a>
## 2026-08-24-change-rung5-promotion-criteria

Origin: `experiments/2026-08-24-change-rung5-promotion-criteria/PARKED.md` — 4 open item(s).
Full original: `git show 6e64330fe:experiments/2026-08-24-change-rung5-promotion-criteria/PARKED.md`

*Its own framing, verbatim:*

> # Parked — Rung 5 (promotion problems and their criteria as programs)
> 
> Found while doing Rung 5, not done, not promised. Each carries a
> ready-to-send prompt so the follow-up costs a paste rather than an
> authoring session.
> 
> ---

<!-- verbatim: experiments/2026-08-24-change-rung5-promotion-criteria/PARKED.md lines 9-53 -->

## P1 — Re-nomination: a subject conjectured AFTER nomination can never be judged

**What.** The reach certificate freezes its candidate subject pool at
nomination (SPEC.md A5). A subject that did not exist then is absent from the
environment, so `promotion_subject_demarcation` and `promotion_accounts_for`
answer `overrun` with `subject-not-in-environment` — honest and typed, and it
means a genuinely better rival authored later cannot be adjudicated against the
incumbent on that promotion problem. Today the pool is adequate because a frame
assertion's SUBJECT is normally an existing artifact and a subject with no reach
case cannot be promoted anyway. It stops being adequate the moment a live run
produces a second reach event on the same lineage set.

**Ready-to-send prompt:**

```
Change tranche: re-nomination for promotion problems. Route through
dr-change-orchestrator.

AUTHORITY: experiments/2026-08-24-change-rung5-promotion-criteria/
PARKED.md P1, and that tranche's SPEC.md assumption A5, which states the
boundary being lifted: the reach certificate freezes its candidate subject
pool at nomination, so a subject conjectured later answers `overrun` with
`subject-not-in-environment` on two of the five criteria.

WORK: decide and implement how a promotion problem acquires a SECOND
frozen environment without editing its first. The shape the tree already
has for "reshape the question without losing the epistemic state" is
`deepreason amend`'s amendment epochs (docs/proposals/AMENDMENT_EPOCHS.md)
— check whether a promotion problem can carry an amendment-shaped second
certificate, or whether re-nomination should mint a second promotion
problem whose id encodes the certificate. Do NOT edit a registered
certificate: it is content-addressed and the criteria are bound to its
digest by their own commitment ids.

GATE PROVES: a rival conjectured after nomination is adjudicated rather
than answered `overrun`; the FIRST certificate's verdicts are byte-
unchanged; and the `subject-not-in-environment` overrun still fires for a
subject in neither environment (the honest answer must survive).

SIZE: unestimated — the first step is the design decision, so this is a
DESIGN-AND-STOP unless the operator says otherwise.
```

---

<!-- verbatim: experiments/2026-08-24-change-rung5-promotion-criteria/PARKED.md lines 54-83 -->

## P2 — Rider 5 clause (4) names four frozen artifacts; this rung shipped one

**What.** The external implementation advice (REQUEST.md Amendment 8, Rider 5
clause 4) says programs consume frozen fence-stamped input artifacts —
`ReachCertificate`, `IncumbentWoundLedger`, `ScopeEnvironment`, `CaptureWindow`.
Rung 5 ships ONE artifact carrying the wound ledger and scope environment as
SECTIONS, and no capture window at all. The deviation is recorded as SPEC.md A4
and was taken for the size budget, which the tranche then overran anyway — so
the reason no longer holds even though the decision may still be right. Capture
integration is Rung 8's, so the fourth artifact is scheduled regardless.

**Ready-to-send prompt:**

```
Question, not a change tranche: should the promotion criteria's frozen
input stay ONE artifact or become the four Rider 5 clause (4) names?

Read experiments/2026-08-24-change-rung5-promotion-criteria/SPEC.md A4 and
src/deepreason/calculus/claims.py::ReachCertificateV1. The single
certificate carries reach_records, problems, commitments, subjects,
consulted and truncated; splitting it would give each section its own
content address and its own attack surface — "your wound ledger is wrong"
would land separately from "your scope environment is wrong" — at the cost
of four registrations per nomination and four digests in every criterion
spec. Answer A (keep one) or B (split), and if B, whether it lands before
or with Rung 8's capture integration.
```

---

<!-- verbatim: experiments/2026-08-24-change-rung5-promotion-criteria/PARKED.md lines 84-122 -->

## P3 — `load-bearing` demarcation is never written, so no promotion candidate can clear criterion 1

**What.** `FrozenSubjectV1.demarcation` has three values and nomination only
ever writes two: `declared-only` (the typed abstention) or `no-attack-surface`
(a settled failure). `load-bearing` is reserved for a sweep that holds a
variator seat, and no such sweep exists. Consequence, stated plainly:
`promotion_subject_demarcation` today returns `pass` for NO candidate — it is
`fail` or `overrun`. That is honest (the run genuinely has not taken the second
reading) and it is not a defect of this rung, whose §12.2 obligation was to
implement the clause. But it means the criterion cannot yet CONFIRM anything,
only refuse, and a reader could mistake a run with no promotions for a run with
no promotable subjects.

**Ready-to-send prompt:**

```
Change tranche: take the §12.2 `load` reading for promotion subjects.
Route through dr-change-orchestrator.

AUTHORITY: experiments/2026-08-24-change-rung5-promotion-criteria/
PARKED.md P3. `calculus/nomination.py::_demarcation` writes only
`declared-only` or `no-attack-surface`; the `load-bearing` value exists and
nothing produces it, so `promotion_subject_demarcation` can refuse and
abstain but never confirm.

WORK: give nomination (or a sweep beside it) the variator seat, taking
Rung 2's cost answer unchanged — cache per subject, ONE sample for the life
of the run, and the typed abstention when the seat is absent, which is
`premises.py::premise_rent_sweep`'s exact shape and is already what the
frozen `declared-only` value means.

GATE PROVES: a subject whose role variants draw a different verdict vector
freezes as `load-bearing` and its candidate PASSES criterion 1; a solo run
with no variator still completes the whole promotion path (L-3) and still
records the abstention rather than a pass.
```

---

<!-- verbatim: experiments/2026-08-24-change-rung5-promotion-criteria/PARKED.md lines 123-150 -->

## P4 — `Verified-at:` stamps on eight map documents are stale from earlier tranches

**What.** `python tools/docs_verify.py --stale` lists eight documents whose
owned files moved under commits that pre-date this branch:
`CON-criticism-source`, `CON-run-identity`, `CON-seats`, `INV-signal-contract`,
`SEAM-llm-x-scheduler`, `SEAM-llm-x-workflow`, `SUB-llm`, `SUB-verification`.
This tranche cleared the seven it made stale and deliberately did NOT touch
these: advancing a stamp over checks read for another tranche's sake is the
false stamp the map's own rule forbids.

**Ready-to-send prompt:**

```
The operator asks what is out of date: run dr-audit-orchestrator's
docs-drift dimension, scoped to the eight documents `python
tools/docs_verify.py --stale` lists. For each, re-read the document
against its owned files, re-run its checks, and either advance
`Verified-at:` or record what actually drifted. Read-only: findings
become parked prompts, no fixes.
```

---

**Recommended next: P3.** It is the only one of the four that changes what a
live run can currently DO — without it the promotion path can refuse candidates
and never confirm one, so a first live promotion is not reachable. P1 and P2 are
design questions with no live consequence yet, and P4 is housekeeping.

---

*71 open park items from 18 tranche directories, re-homed 2026-08-25 by*
*`experiments/2026-08-25-change-closeout-prune/` (stage 1), acting on*
*`experiments/2026-08-25-audit/PARKED.md` P4.*
