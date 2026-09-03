# Reproduction

Form: record-replay (committed roots) + end-to-end offline drive (stub)

Artifacts, both committed and re-runnable:

    python experiments/2026-09-03-defect-stopped-run-resumption/proof/outstanding_census.py
    python experiments/2026-09-03-defect-stopped-run-resumption/proof/three_shapes.py --workdir <dir>
    python experiments/2026-09-03-defect-stopped-run-resumption/proof/mutate_one_byte.py <root> <copy>

No provider, no credential, no network. `three_shapes.py` drives the committed
deterministic stub through `scripts/cycle_soak.py --case epoch3` — the same
instrument CLAUDE.md requires before any live launch — to each of the three
terminal shapes, and then runs the real `deepreason continue` against each
root. Total wall time ~14 minutes; far too slow for the gate, which is why the
gate regressions written in dr-implement-fix are unit-scale and this script is
the end-to-end proof recorded here.

`scripts/` was NOT extended. The window instruction permitted extending it for
the stub; it turned out to be unnecessary. `cycle_soak.py --case epoch3`
already produces the clean shape unmodified, and the other two are produced by
driving it — a SIGKILL of its process group for the killed shape, and a
one-function scheduler raise for the failed shape — from inside the tranche's
own `proof/` script. Nothing under `scripts/` or `src/` was touched to
reproduce this.

## Current output — RED, all three shapes

    === shape: clean ===                    (ordinary run, natural budget terminal)
        state: completed
        stop_reason: budget_exhausted
        terminal_lifecycle_refusal: STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY
        cycle: 8
        outstanding_work: 31
        unconsumed_provider_calls: 0
        terminal_lifecycle_decision: False
        record_verification_refusal: None
        continue rc=1 CONTINUE_TYPED_STOP_REQUIRED
        cycle after continue: 8 (was 8)

    === shape: failed ===                   (mid-cycle operational failure)
        state: failed
        stop_reason: operational_failure
        terminal_lifecycle_refusal: TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL
        cycle: 1
        outstanding_work: 3
        unconsumed_provider_calls: 0
        terminal_lifecycle_decision: False
        record_verification_refusal: None
        continue rc=1 CONTINUE_TYPED_STOP_REQUIRED
        cycle after continue: 1 (was 1)

    === shape: killed ===                   (SIGKILL with work in flight, then finalize)
        [killed] state before finalize: running
        [killed] finalize rc=0
        state: running
        stop_reason: None
        terminal_lifecycle_refusal: None
        cycle: 2
        outstanding_work: 11
        unconsumed_provider_calls: 0
        terminal_lifecycle_decision: False
        record_verification_refusal: None
        continue rc=1 CONTINUE_TYPED_STOP_REQUIRED
        cycle after continue: 2 (was 2)

Raw: `proof/RED_three_shapes.json`, `proof/RED_three_shapes.txt`.

## Fidelity against the live roots

The stub roots reproduce the live ones on every field the diagnosis turns on,
which is what makes this a reproduction rather than a resemblance:

| | live | stub |
|---|---|---|
| clean: refusal code | STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY | same |
| clean: outstanding / unconsumed | 6 / **0** and 2 / **0** | 31 / **0** |
| failed: refusal code | TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL | same |
| failed: outstanding / unconsumed | 6 / **0** | 3 / **0** |
| killed: state after finalize | `running` (P-A2 e4) | `running` |
| killed: outstanding / unconsumed | 10 / **0** | 11 / **0** |
| every shape: verify_root | 0 violations | gate returns `None` |
| every shape: continue | REFUSED | REFUSED |

The killed shape reproduces P-A2 epoch 4 down to a detail worth naming,
because it would otherwise read as a bug in the reproduction: after a
successful `finalize` (rc=0) `run-status.json` still says `state: running`.
`finalize` appends the terminal to the LOG and does not re-emit a progress
line, and `run-status.json` is `progress.jsonl`'s last record. The live root
shows exactly the same thing. This is a REPORTING gap, separate from the
defect under repair, and it is why the census reads the workflow state rather
than trusting `run-status.json` alone.

## Confirms diagnosis: YES

DIAGNOSIS.md's falsifiable prediction (1) named the decisive observation in
advance: `unconsumed_bound_call_seqs == ()` on a root that refuses. Measured
**0 unconsumed provider calls on all three shapes**, with 31, 3 and 11
outstanding work items respectively. The refusal fires on the first disjunct
of `workflow/lifecycle.py:236` alone; the second disjunct — the one carrying
the real protection against closing a stop over a provider result nobody read
— is satisfied everywhere. Predictions (2) and (3) also hold verbatim,
including that the killed shape lands on the SAME refusal path as the clean
one (`finalize_stopped_root` → `terminalize_text_run`).

Prediction (4) holds too, and is recorded separately as the control:

    target endpoint: http://127.0.0.1:34047/v1
    record_verification_refusal -> the record does not verify on the security
        channel: attempt-route, frozen-route
    continue rc= 1 | CONTINUE_RECORD_NOT_VERIFIED: the record does not verify
        on the security channel: attempt-route, frozen-route

One byte of `log.jsonl` altered on a copy of the clean root, and the
SECURITY-channel gate refuses by name. So the gate that SHOULD decide
continuation works and is simply never reached on an intact record, because
the lifecycle refusal fires first. Raw: `proof/RED_mutation.txt`.

Had any shape shown a non-empty `unconsumed_bound_call_seqs`, the diagnosis
would have been refuted and this phase would have routed back to dr-diagnose.
It did not.

## Post-fix expectation (the GREEN half, stated before the fix is designed)

Re-running `three_shapes.py` on the fixed tree must print, for all three
shapes:

    record_verification_refusal: None
    continue rc=0
    cycle after continue: <strictly greater than cycle before>

and `mutate_one_byte.py` must print the SAME two lines it prints today —
unchanged, character for character. That pairing is the whole success
criterion: the lifecycle refusal is gone, the security refusal is untouched.

One shape carries a known additional obligation, forecast here so a partial
GREEN is not mistaken for a full one: the killed root's 11 outstanding items
include work orders whose provider call never produced an attempt record
(P-A2 epoch 4 carried one such CRITICISM item; see DIAGNOSIS.md, "the
twenty-fourth item"). `Scheduler._recover_workflow_prefixes` closes the
result-bearing ones and asserts `"transaction recovery left unfinished
authority"` if any remain. If the killed shape resumes and then dies on that
assertion, the fix is incomplete, not working — and that is a FAIL of this
criterion, not a caveat to it.
