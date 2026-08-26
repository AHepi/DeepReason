# PARKED — found by the cycle soak, not fixed here

Cross-routing is strict (CLAUDE.md): a defect found mid-change is PARKED, not
fixed. Both entries below are in adapter/transaction code, which REQUEST.md R8
puts under an explicit stop: "If you need to edit adapter/transaction code,
STOP and say so."

---

## P1 — a repair under transactional authorization leaves a record `verify_root` rejects

> **RESOLVED 2026-08-25** by `experiments/2026-08-25-defect-workflow-call-pairing/`.
> The defect was real and is fixed, but this note's own framing was wrong twice over:
> the failing event is NOT a repair (`attempt: 0`, four transport retries inside one
> authorized attempt), and neither suspect below was the cause. `verify_root`'s
> pairing check compared an absent raw blob spelled `None` on the durable attempt
> against the same absence spelled `""` on the call — false by construction for every
> `outcome="transport_failure"` attempt, repair or not. The checker over-specified;
> the writer was right. See `docs/ERRATA.md` E53. The standing caveat below asked the
> right question and it was answered: no committed root witnesses the class (0 of 459
> attempts across 14 roots), so the fix rests on the induced witness plus the
> structural argument, and that is recorded as such rather than glossed over.

**What.** With one induced repair, the run produces a record that fails the
`workflow-call-pairing` epistemic check: `event seq=24: provider result differs
from its authorized attempt`. Deterministic — two runs of
`python -u scripts/cycle_soak.py --cycles 8 --induce-repairs 2` produced a
byte-identical violation (same check, same detail, same seq).

**Why it is suspicious rather than expected.** `llm/adapter.py` already knows a
repair cannot reuse an authorization bundle — the branch immediately above the
reservation-bound check raises `WorkflowAuthorizationError("transactional repair
requires a new authorization bundle")` when `attempt != 0` under a dispatch
authorization. In the observed run that guard did not fire; the repair
dispatched and the resulting attempt record did not pair with its
authorization. So either the guard has a hole, or the pairing check and the
guard disagree about what a repaired attempt should look like. Both are
answers a reader can reach; neither is one this tranche may implement.

**Standing caveat.** The repair was INDUCED by
`scripts/cycle_soak.py --induce-repairs`, which makes the stub answer the run's
first wire schema unusably once. A real provider fails validation for its own
reasons, so the trigger is synthetic even though the code path is real. Whoever
picks this up should decide first whether an induced fault is an admissible
witness here; if it is not, the finding downgrades to "the repair ladder is
untested offline" and P1 closes as not-a-defect.

### Ready-to-send prompt

```
Route: deepreason-orchestrator (defect).
One goal: decide whether a repair dispatched under a transactional
authorization bundle may leave an attempt record that verify_root's
workflow-call-pairing check rejects — and if it may not, fix it.

Reproduce (deterministic, ~35s, no provider spend):
  python -u scripts/cycle_soak.py --cycles 8 --induce-repairs 2 --out /tmp/p1 --keep
Expect: A3-verify-root-clean FAILS with
  {'check': 'workflow-call-pairing',
   'detail': 'event seq=24: provider result differs from its authorized attempt'}
and the report's attempts.repairs == 1.

Evidence to read first, in order:
  - /tmp/p1/soak-report.json  (checks, seams, attempts)
  - /tmp/p1/run/log.jsonl at seq=24, and the authorization bundle it names
  - src/deepreason/llm/adapter.py, the `attempt != 0` guard above the
    reservation-bound check (~line 1393): it raises
    WorkflowAuthorizationError("transactional repair requires a new
    authorization bundle") — establish why it did not fire here
  - docs/map/SEAM-llm-x-workflow.md before either subsystem

Decide first: is an INDUCED validation failure an admissible witness for this
seam? The soak forces it by returning a schema-invalid response once. If the
answer is no, close this as not-a-defect and record that the repair ladder has
no offline witness.

End state: either a fix with a regression test naming this reproduction, or a
recorded not-a-defect with the reason. Surface 3 (verification) is FROZEN —
verify_root's output shape may not move to make this green.
```

---

## P2 — the reservation-bound seam itself (D4), for the window that owns it

> **RESOLVED** by `experiments/2026-08-23-fix-reservation-bound-authority/`; the soak
> now reports `[PASS] D4-reservation-bound`. The `EXPECTED_RED` deletion this note's
> prompt required was missed by that tranche and carried out 2026-08-25 by the P1
> tranche above (`docs/ERRATA.md` E54). The map is now empty.

**What.** The default soak (`--cycles 8`, no induction) dies at cycle 1 with
`operational_failure` / `transactional reservation bound differs from rendered
request` — the same typed message as the live root
`experiments/2026-08-22-change-epoch3-second-lineage/failed-attempt3-run-bb045538…`,
which died at cycle 2. Deterministic across runs.

**Not parked for diagnosis — parked for OWNERSHIP.** REQUEST.md R7 says a
parallel window is already fixing this seam in `llm/adapter.py`; this tranche
drives that code and does not modify it. The entry exists so the owning window
gets the offline reproduction for free, and so that nobody re-diagnoses a seam
that is already assigned.

**What this tranche contributes to it:** a 35-second, zero-token reproduction
that previously cost a full live run (~110k tokens) to observe.

### Ready-to-send prompt

```
Route: whichever window owns the llm/adapter.py reservation-bound fix.
Context: the offline cycle soak now reproduces your seam deterministically,
on the bench, in ~35 seconds with no provider spend.

  python -u scripts/cycle_soak.py --cycles 8 --out /tmp/d4 --keep

Terminal: state=failed, stop_reason=operational_failure,
message='transactional reservation bound differs from rendered request',
cycle 1. Same typed message as the live root failed-attempt3-run-bb045538…
(which reached cycle 2 before dying).

Note the depth dependence, which is the whole reason the smoke missed it:
the SAME config at --cycles 1 terminates cleanly (state=completed,
stop_reason=budget_exhausted, verify_root 0 violations). The seam only trips
once the run is allowed to go deeper.

When your fix lands, delete the "D4-reservation-bound" entry from EXPECTED_RED
in scripts/cycle_soak.py in the same commit — an expected-red seam nobody
clears is indistinguishable from a seam nobody fixed, and the soak's exit 3
stops meaning anything.
```
