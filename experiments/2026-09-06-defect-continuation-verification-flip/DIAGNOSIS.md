# Diagnosis: a work order abandoned in flight verifies clean while it is open, and its honest closure is condemned

One primary cause, and it is not "one of the two verdicts is a lie about the
events". Both verdicts read the same three events correctly. They disagree
because the RECORD changed around those events: three work orders that were
still open when the run died were CLOSED by the continuation, and the check
that reads a closed call has no category for the shape those closures take.

## The answer to the goal's question

**R-STRICT, primarily: the check is too strict after a resume, and the run's
events were always sound.** The three calls carried wire-valid replies, and
nothing about them changed. What changed is that their work orders acquired the
semantic admission and the terminal the original run never lived to write.

**R-WEAK, but far narrower than P9 feared, and it must still be said plainly:**
the pre-continuation clean verdict WAS too permissive — not because clean
verdicts on roots carrying failed calls are untrustworthy in general (they are
not; see the census below), but because **a record with work orders still open
verified `valid: true` while the verifier's own stats listed them**. The
before-verdict's stats name exactly the three:

    outstanding_work_orders: ['sha256:322e7f2b…', 'sha256:dd844c38…', 'sha256:ea0b15ea…']
    violations: 0

Those are the work orders of calls 142, 295 and 215. The verifier knew the
record was incomplete, wrote it down, and did not let it affect the verdict.

## The mechanism, in the order the record shows it

**1. The three events never changed.** Byte-identical at both commits:
seq 142 `sha256 584145eedb0f0ddf6384f961…`, seq 215 `625ee4a13c7ca5a44c047060…`,
seq 295 `6629337a002121aeb55025e7…`, 2 548 bytes each, `rule: Control`,
`action: provider_result`. Each carries one attempt with `valid: true`,
`natural_stop: true`, `truncated: false` (29 218 / 30 136 / 30 166 tokens).

**2. The original run died with their work open.** The lifecycle of call 142's
work order in the pre-continuation log, complete:

    seq 140  work_transition   work-preparation-v1, work-lifecycle-transition-v1
    seq 141  work_transition   …dispatch-authorization-v1, work-lifecycle-transition-v1
    seq 142  provider_result   provider-attempt-v1, work-lifecycle-transition-v1
    (nothing further)

No semantic admission. No work terminal. The same holds for 215 and 295.

**3. The continuation closed them, without a model call.** In the
post-continuation log, three new pairs of events appear beyond the old tail
(the log grew 1 168 → 1 451 while `logged_tokens_this_run` stayed 0):

    seq 1171  semantic-admission-v1 outcome=schema_exhausted   → work 322e7f2b… (call 142)
    seq 1172  work-terminal-v1      status=schema_exhausted
    seq 1173  semantic-admission-v1 outcome=schema_exhausted   → work ea0b15ea… (call 215)
    seq 1175  semantic-admission-v1 outcome=schema_exhausted   → work dd844c38… (call 295)

Each admission's `provider_attempt_ref` is the ORIGINAL attempt's id, so the
closure is about the old call, written by the resume.

**4. That closure flips the verifier's classification of the old call.**
`invariants.py::_controller_v3_history` classifies a provider call by looking
up the admission under `(work_id, attempt_index)` whose `provider_attempt_ref`
matches the attempt (lines 795-802):

    if row["attempt"].outcome == "transport_failure":   failure_call_seqs.add(seq)
    elif admission is not None and admission.outcome != "admitted":
        …patch-repair rejection?  semantic_rejection_call_seqs.add(seq)
        else:                     failure_call_seqs.add(seq)

Before, `admission is None` → the call fell through to `SUCCESS_REQUIRED`.
After, the admission exists and is not `admitted` → `FAILURE_REQUIRED`.
Measured directly on the two logs, with the same objects directory:

    before: failure_call_seqs {119, 827, 832, 944, 949, 1062, 1067}
    after:  failure_call_seqs {119, 142, 215, 295, 827, 832, 944, 949, 1062, 1067}

**5. `FAILURE_REQUIRED` then forbids exactly the evidence that makes the
closure honest.** `verify_root`'s `attempt-validity` clause demands that a
failed call carry no wire-valid attempt (`invariants.py` ~3740):

    failed call must contain no valid attempt, got [0]

## Why that rule is right for real failures and wrong for these

The check has three shapes, and the record shows it applying them correctly
everywhere else. Classifying every provider call in this root:

| | before | after |
|---|---|---|
| SUCCESS, carries a valid attempt | 76 | 73 |
| FAILURE, carries NO valid attempt | 7 | 7 |
| SEMANTIC_REJECTION, carries a valid attempt | 2 | 2 |
| **FAILURE, carries a valid attempt** | 0 | **3** ← the violations |

Every one of the seven genuine failures — the repair-exhausted and
transport-failed calls — carries no wire-valid attempt, in both readings. The
rule holds for them. It breaks for the three because their failure is of a
different kind: **the wire reply validated; the semantics were never
adjudicated.** The check already has the category for that shape —
`SEMANTIC_REJECTION`, which permits "at most one final wire-valid attempt" —
but the only route into it is `_is_patch_repair_semantic_rejection`, which
requires a `repair.semantic-task.v1` payload in patch mode with a parent work
id. An ordinary conjecturer call closed as `schema_exhausted` cannot reach it,
so it lands in `FAILURE_REQUIRED` and is condemned for carrying the valid
attempt it legitimately carries.

**Primary cause, one sentence:** a non-admitted semantic admission is routed to
`FAILURE_REQUIRED`, whose rule assumes the call never produced a wire-valid
reply, but a semantic non-admission is precisely the case where it did.

## What this means for the continuation gate

The gate did not fail, and it is not the cause — but the record shows a gap
worth stating. `_continuation_authority` (`application/results.py:625`) reads
only whether the workflow state carries a terminal lifecycle decision or an
open resume decision. It consults neither the replay verdict nor
`outstanding_work_orders`. Separately, `continue` and `amend` refuse on
SECURITY-channel findings; `attempt-validity` is an INTEGRITY finding, so it
would not have blocked this resume even after the flip.

So the operator's 2026-08-29 law — continuation is integrity-gated, "I don't
want a jailbroken run to be continuable" — is served by a gate that in this
case reported `true` over a record whose own stats said three work orders were
still open. Nothing was tampered with here; the exposure is that the gate's
integrity half is thinner than the law's words imply. **Not this tranche's to
fix** (the goal is the verdict disagreement) and it is not a defect in the
sense of contradicting a documented guarantee, so it is PARKED as P1 rather
than folded in.

## Ruled out

- **The events were altered.** No: byte-identical, hashed at both commits.
- **The continuation spent tokens or made a call.** No: `logged_tokens_this_run: 0`,
  and the new admissions reference the original attempts' ids.
- **The objects changed.** No: 85 admissions and 85 attempts in both, same
  outcome counts (73 admitted / 5 rejected / 7 schema_exhausted).
- **Proposal receipts.** `workflow_failure_call_seqs` from
  `h.workflow_state.proposal_receipts` is empty on this root (0 receipts); the
  condemnation comes entirely from the controller-v3 history.
- **An amendment epoch.** The flip needs no epoch; it is the admission lookup
  alone. (The root has no amendment epochs.)

## Evidence pointers

- root: `experiments/2026-09-06-change-writers-room-organiser-testing/runs/home-r/runs/run-c3f3bf10bc57d63e224a9f1c68bf1057`
- verdicts: that tranche's `runs/armR/ARMR_RESULTS.json` at `ee962fb05` (0 violations) and `5e01bcd9e` (4)
- stored: `REPLAY_VALIDATION.json` — three `attempt-validity` violations, verbatim above
- re-derived here on faithful copies (the committed root untouched; `git archive ee962fb05` for the before-root, so its checkpoint matches its log):
  `verify_root(before)` → 0 violations, `outstanding_work_orders` = the three work ids;
  `verify_root(after)` → 3 `attempt-validity` violations, `outstanding_work_orders` = []
- code: `src/deepreason/invariants.py` lines 119-140 (`_expected_call_outcome`), 352-354 (the admissions map), 795-802 (the classification), ~3737-3746 (the failing clause)

## Frozen-surface note (read before any fix is designed)

The cause is inside `src/deepreason/invariants.py`, which is **frozen surface
3** together with `src/deepreason/verification/`
(`docs/map/INV-frozen-surfaces.md`). Any fix there needs an operator grant
requested in FIX.md before implementation, with `tools/blast_radius.py`'s own
computed contact list pasted. This diagnosis proposes nothing; the roads and
their prices belong in FIX.md.
