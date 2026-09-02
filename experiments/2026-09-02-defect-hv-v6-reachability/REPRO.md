# Reproduction

Form: **record-replay** (primary) + **offline unit reproduction** (secondary).
Both run offline, in seconds, against committed evidence. No provider was
called; no run root was opened writably; no production code was touched.

The primary form turned out to be cheaper *and* stronger than the tranche brief
anticipated, and the reason is worth stating: the brief expected the defect to
need the P-A1 window's soak (on another branch) to demonstrate. It does not.
`main` already carries a cleanly-completed v6 root whose `variator` seat holds
the `variator.direct.v1` grant and which measured no `hv` at all. The
contradiction is committed; it only had to be joined across two files of the
same root.

---

## Artifact 1 — record replay (primary)

    python experiments/2026-09-02-defect-hv-v6-reachability/repro_record.py

Walks every committed v6 run root read-only and joins, per root, the
`variator`-seat behavioural grant from `run-manifest.json` against the `hv_set`
and `v6-model-phase-deferred.v1` counts from `log.jsonl`.

Current output (full run saved as `repro_record_RED.txt`; exit 0 = reproduced):

    root                                                          grant  events  hv_set  hv_deferred  state
    experiments/2026-08-12-live-grounded-extension-expansion/run  YES     12991       0          336  completed/budget_exhausted
                                                                         {'hv-spot-check': 241, 'hv-floor': 95}
    experiments/2026-08-08-live-two-seat-ab-s6/.../run-6995cd12     no      1979       0          119  completed/budget_exhausted
    experiments/2026-08-25-poietics-program/run                     no      2707       0          116  completed/budget_exhausted
    ... 47 further roots, every one at hv_set = 0 ...

    DEFECT  experiments/2026-08-12-live-grounded-extension-expansion/run
            variator seat holds ['variator.direct.v1'], the run asked for hv
            336 times, and recorded 0 hv_set events.

    REPRODUCED: 1 grant-bearing root(s) measured no hv.

**The census, totalled: 50 committed v6 roots, 56 501 log events, 2 661 `hv`
requests deferred, 0 `hv` measurements.** Not one v6 root in the repository has
ever measured `hv`.

Confirms diagnosis: yes — the decisive row is
`2026-08-12-live-grounded-extension-expansion/run`. It is `state=completed`,
`stop_reason=budget_exhausted` (so the zero is not an early death), its manifest
grants `variator[0]` exactly the contract the gate exists to stand in for, and
it still recorded 336 typed `transaction-contract-unavailable` deferrals and
zero measurements. Grant present, gate closed anyway: the gate does not read the
grant. The 46 no-grant roots below it are the control — their deferrals are
CORRECT and must survive the fix unchanged.

Post-fix expectation: **this script's output does not change, and that is the
point.** The roots it reads were written by the defective code and are
append-only evidence of their own version; nothing may edit them. What changes
is Artifact 2 and any NEW grant-bearing root. This script's enduring job after
the fix is the control half: it must keep showing that no-grant roots deferred.

## Artifact 2 — offline unit reproduction (the one that inverts)

    python experiments/2026-09-02-defect-hv-v6-reachability/repro_gate.py

Loads the **real committed manifest** of the grant-bearing root above (parsed by
the shipped `RunManifest` model — it validates unchanged), builds the minimum
`Scheduler` surface the gate touches, and calls
`_defer_untransactional_v6_phase` for both `hv` phases. It runs the same probe
against the P-R1 manifest as a no-grant control.

Current output (saved as `repro_gate_RED.txt`; exit 0 = reproduced):

    --- GRANT PRESENT: experiments/2026-08-12-live-grounded-extension-expansion/run
        schema_version                 6
        variator seat behavioural grant ['variator.direct.v1']
        _defer(...'hv-floor', 'variator')  -> True
        _defer(...'hv-spot-check', 'variator')  -> True
        typed deferral markers written  ['hv-floor', 'hv-spot-check']

    --- CONTROL, no grant: experiments/2026-08-25-poietics-program/run
        schema_version                 6
        variator seat behavioural grant NONE
        _defer(...'hv-floor', 'variator')  -> True
        _defer(...'hv-spot-check', 'variator')  -> True
        typed deferral markers written  ['hv-floor', 'hv-spot-check']

    CONTROL holds: a seat with no grant defers both hv phases and writes the
    typed notice. This is the behaviour the fix must PRESERVE.

    REPRODUCED: variator[0] holds variator.direct.v1 and the gate deferred
                BOTH hv phases anyway.

Confirms diagnosis: yes — two manifests differing in exactly one thing, the
grant, produce an identical answer from the gate. That is the mechanism stated
as an experiment rather than as a reading of the source.

Post-fix expectation, exactly:

    GRANT PRESENT   _defer(...'hv-floor', 'variator')      -> False
                    _defer(...'hv-spot-check', 'variator') -> False
                    typed deferral markers written          []
    CONTROL         _defer(...'hv-floor', 'variator')      -> True    (unchanged)
                    _defer(...'hv-spot-check', 'variator') -> True    (unchanged)
                    typed deferral markers written          ['hv-floor','hv-spot-check']
    exit status 1 ("NOT REPRODUCED: the gate consulted the grant")

`dr-implement-fix` lands this same pair of assertions, inverted, in `tests/`.
They live here rather than in `tests/` today because a defect assertion inside
the gate would leave `pytest tests/ -q -n 4` red for the whole tranche, and
`0 failed` is the only acceptable gate result.

---

## Why the reproduction fidelity is real and not simulated

`dr-reproduce`'s fidelity rule says the reproduction must mirror the conditions
the record shows. Nothing here is constructed: both artifacts read committed
`run-manifest.json` and `log.jsonl` files. The only invented object is the
`Scheduler` shell in Artifact 2, and it supplies exactly the three attributes
the gate reads (`run_manifest`, `harness.log`, `harness.record_measure`,
`diagnostics`, `_cycles`) — the same shape the existing
`tests/test_v6_scheduler_model_phase_deferral.py::_scheduler` helper uses, so
the idiom is the repo's own rather than a new scaffold.

## One honest gap, carried forward to FIX.md rather than papered over

GOAL.md's success criterion 1 is stated in terms of `scripts/cycle_soak.py` on a
grant-bearing case. **No such case exists on `main`**, and that is itself part
of the finding: every committed soak case
(`epoch3`, `pr1`, `pc1`, `pc2`, `pc2b`) compiles a manifest with
`criticism_policy` either absent or non-`defended_trial`, and
`run_manifest.py:2059-2065` mints the `variator`/`defender`/`judge` behavioural
grants **only** when `criticism_policy.authority == "defended_trial"`. So no
committed soak case can exercise the grant-bearing path at all. The `pa1` case
that can exists only on `origin/claude/live-reasoning-p-a1-bv65kl`, together
with the two stub fixtures it needed.

Building a grant-bearing soak case is therefore a step in FIX.md, not a
precondition of this phase, and the two artifacts above already reproduce the
defect without it. Recorded here so the later phase inherits the reason rather
than rediscovering it.

**A consequence worth flagging now, because it bounds what this tranche can
claim.** After the fix, `hv` becomes reachable by configuration — but only
through a `criticism_policy` whose authority is `defended_trial`, because that
is what mints the grant. Whether the *minting* condition is itself too narrow
(the operator's solo-run law says sole-model operation may never be structurally
locked out of a capability) is a separate question about
`run_manifest.py:2059-2065`, not about the gate. It is parked as P5 with a
ready-to-send prompt, and FIX.md must state the limit plainly rather than let
"hv is now reachable" be read as "hv is reachable from every configuration".
