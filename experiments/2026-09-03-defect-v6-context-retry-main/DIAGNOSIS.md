# DIAGNOSIS — the v6 conjecture-context retry plans what v6 refuses

Cause named from the typed record first, code read only after the
record ruled out a model fault. Both are quoted below.

## Primary cause (one)

`Scheduler.step` had TWO independent expressions producing the
conjecture context plan it dispatches `conj` with, and only the first
carried the v6 rule.

Primary path, `src/deepreason/scheduler/scheduler.py:2388-2392` on main
at `5df7246ad`:

```python
context_plan = self._plan_conjecture_context(problem, school_id)
if self.run_manifest is not None and self.run_manifest.schema_version == 6:
    # Controller-v3 persists preparation before its pure
    # planners; Conj owns that ordered transaction.
    context_plan = None
```

Retry path, `:2448-2451`, sixty lines below:

```python
except ConjectureContextStale:
    if context_attempt:
        raise
    context_plan = self._plan_conjecture_context(problem, school_id)
```

The retry re-enters `conj(..., conjecture_context_plan=context_plan)`
with a live plan on a v6 manifest. `src/deepreason/rules/conj.py:827`
raises on exactly that:

```python
raise ValueError("v6 conjecture context must be planned after durable work preparation")
```

`ValueError` is caught by none of the handlers around the dispatch
(`WorkBudgetDenied`, `SchemaRepairError`/`EndpointError`,
`RouteFirewallError`, …), so it propagates and terminalizes the run.
By construction the retry is the ONLY path on which a v6 run can
reach that raise.

## Record evidence (two independent roots, neither a code reading)

**(1) episode-config arm A, 2026-09-02.** Root
`run-cd878ff440f61294de34bea1fd45f8ad`, run id
`ddd04beda27574b911d439cb95aadc40328d9a7a4276a39dd7aef8a53d4c6f90`,
committed on branch `claude/model-profile-registry-opkgal` at
`06b0d9fd9` under
`experiments/2026-09-02-episode-config/A-ranking-on/home/runs/`.
`run-status.json`, verbatim fields:

    state                       failed
    stop_reason                 operational_failure
    message                     "v6 conjecture context must be planned
                                 after durable work preparation"
    cycle                       0
    token_spend                 71323
    terminal_lifecycle_refusal  TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL

**(2) P-A2 epoch 3, on main.** `experiments/2026-09-02-live-p-a2-corrected/`,
run `63e48f57415d05323b608a84f138ee5c22c274d7d8ebccc2e219b613d7c3a722`,
written up as F7 in that tranche's `FINDINGS.md:247`. Same stop reason,
same message, same cycle 0, `verify_root` 0 violations. F7 also
establishes it is NOT the F4 seat death: no
`workflow-route-seat-insufficient-capability-v1` object exists in the
root, and the last provider call before the stop was `valid=True` at
30 389 tokens. The model succeeded; the harness refused its own next
step.

## Reachability — why it hides

`ConjectureContextStale` is raised from exactly three sites, all in
`src/deepreason/scratch/conjecture.py` (lines 324, 432, 661) — the
scratchpad's conjecture-context machinery. So the retry path is
reachable only when the scratchpad is live enough to build a context
that can go stale.

| run | scratchpad | outcome |
|---|---|---|
| P-A1 | configured ON, did not fire | never stale, retry never taken, defect never reached |
| P-A2 epoch 3 | ON and fired | context went stale, retry taken, run dead |
| episode-config arm A | ON and fired (4 `Scratch` rules; arms B and C, 0) | run dead |
| episode-config arms B, C | ON, did not fire | survived |

The trigger is stochastic, not arm-specific: three arms ran the same
question and only the one that authored scratch material died.

## Map (§Map) — what this change moves besides code

Resolved at preflight, BEFORE the patch was applied. Two committed map
checks pin the PRE-FIX expression by literal text and go red the moment
the fix lands. They are part of this tranche, in the same commit:

1. `docs/map/SEAM-scheduler-x-workflow.md:86` asserts, inside
   `Scheduler.step`,
   `index("_plan_conjecture_context(problem, school_id)") <
   index("context_plan = None") < index("admitted = conj(")`. After the
   fix, `step` contains neither of the first two strings — planning
   moved to the `_dispatch_conjecture_context_plan` owner. The CLAIM
   (v6 must not pre-plan context) is unchanged and still checkable; the
   check must be re-expressed against the owner.
2. `docs/map/SEAM-schools-x-scratch.md:254` greps for the literal
   `context_plan = self._plan_conjecture_context(problem, school_id)`.
   Same situation, same claim, same remedy.

Neither is a frozen surface and neither claim is being weakened: each
re-expression must still fail if the v6 rule is removed. That is proven
in REPRO.md by the same mutation.

`docs/map/SEAM-scheduler-x-workflow.md:60` also carries a prose row
naming `context_plan = None` as the mechanism; it is updated to name
the owner.

## Frozen-surface check

`INV-frozen-surfaces.md` read before designing. The five frozen
surfaces span `capabilities/state.py`, `harness.py`, `invariants.py`,
`verification/`, `run_manifest.py`, `qualification.py`, plus the
frozen-adjacent `route_fingerprint` in `llm/firewall.py`.
`src/deepreason/scheduler/scheduler.py` is on none of them. CLEAR.
