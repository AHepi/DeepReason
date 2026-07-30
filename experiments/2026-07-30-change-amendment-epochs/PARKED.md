# Parked — noticed in this tranche, deliberately not done

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
