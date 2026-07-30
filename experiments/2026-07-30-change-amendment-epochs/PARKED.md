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
