# Diagnosis: the v6 deferral gate decides on `schema_version` alone, so no configuration can open it

Primary cause: `Scheduler._defer_untransactional_v6_phase`
(`scheduler/scheduler.py:696-752`) computes its entire answer from
`manifest.schema_version != 6` — it returns `False` for a non-v6 manifest and
`True` for every v6 manifest, unconditionally, before any other value is read.
It never consults `route_seat_behavioral_capability_plan`, a contract grant, a
route, a lease, or any `Config` field; nothing after the `schema_version` test
can change the return value, only what gets *recorded* on the way out. Both
producers of `hv_set` sit behind it (`hv-floor` at `scheduler.py:1358`,
`hv-spot-check` at `scheduler.py:2947`), so `hv` cannot be measured on a v6 run.
The gate was correct when written — v6 makes the adapter fail closed on any
unbound provider dispatch, and typed completion debt is better than a killed
root — but the operations-parity law (2026-08-13, ONE run path) made v6 the only
path a current run takes, which turned the `schema_version != 6` escape into
dead code and the safety net into a permanent lock.

Evidence:

  - **`experiments/2026-08-25-poietics-program/run` (P-R1) `log.jsonl`** ->
    2 707 events, **0** with a non-empty `state_diff.hv_set`, and **117**
    `v6-model-phase-deferred.v1` Measure events, every one of them role
    `variator` with reason `transaction-contract-unavailable`:
    `hv-spot-check` 74, `hv-floor` 42, `premise-demarcation-variation` 1.
    So `hv` was *asked for* 116 times on this root and deferred 116 times.
    Measured read-only this session; the 117 reproduces the operator brief's
    figure exactly. Sample event (seq 339):
    `inputs = ["v6-model-phase-deferred.v1", "premise-demarcation-variation",
    "variator", "premise-rent", "-", "transaction-contract-unavailable"]`.

  - **P-A1 live root `4565139800f5ca02...`**, read read-only out of
    `origin/claude/live-reasoning-p-a1-bv65kl` (never checked out, never
    written) -> 661 events, **0** non-empty `hv_set`, **20** deferrals of which
    **19 are role `variator`** (`hv-spot-check` 10, `hv-floor` 8,
    `premise-demarcation-variation` 1) and 1 is role `judge`
    (`pairwise-discrimination`). The brief's "P-A1 19" is the variator subtotal;
    confirmed. `run-status.json`: `state=failed`,
    `stop_reason=operational_failure`, cycle 5,
    `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY`.

  - **`experiments/2026-08-27-pc2b-symmetric-reasoning/run` (P-C2b)**, a
    *cleanly completed* root (`state=completed`, `stop_reason=converged`, 17
    cycles) -> 450 events, **0** non-empty `hv_set`, 0 `reach_set`. This one
    matters because it removes the obvious alternative reading: the zeros are
    not an artifact of runs dying early.

  - **The P-A1 offline soak, grant PRESENT** — `RESULTS.md` segment 2 on that
    branch: `24 of 24 cycles reached`, `A3-verify-root-clean 0 violations`,
    and segment 3 records **zero `hv_set` events** on that same soak. A
    24-cycle clean drive with `variator[0]` holding `variator.direct.v1` and
    still no measurement is the decisive observation, because it separates
    "the grant was missing" from "the grant is not consulted".

  - **Code, read only after the record had named the mechanism**:
    `scheduler.py:715-717` is `manifest = self.run_manifest; if manifest is None
    or manifest.schema_version != 6: return False`, and the function's sole
    other `return` is a bare `return True` at line 750. The docstring states the
    intent in its own words: *"Return True only for v6, so historical schedulers
    retain their byte-for-byte call paths and behavior."*

  - **`docs/map/SEAM-scheduler-x-workflow.md`, Traps** already documents this
    behaviour, and documents it as intended: *"Under v6 the local criticism
    ladder is empty, and that is not a bug. `_criticize`'s HV-floor and rubric
    arms, pairwise discrimination, experiment and property design, audit, vision
    and lazy HV all record deferral debt instead of dispatching."* That entry
    predates the modularity law (2026-08-26). It is now wrong as written and is
    this tranche's obligation to rewrite (map rule: a Traps entry is never
    deleted, only rewritten to say when it was fixed), with a `docs/ERRATA.md`
    entry for the "not a bug" claim.

Implicated code:
  - `src/deepreason/scheduler/scheduler.py:696-752` — the gate (primary)
  - `src/deepreason/scheduler/scheduler.py:1358` — `hv-floor` / `variator`, guards `run_hv_floor`
  - `src/deepreason/scheduler/scheduler.py:2947` — `hv-spot-check` / `variator`, guards `hv_spot_check`

## Two corrections to the tranche brief, both from direct measurement

Recorded here rather than silently carried forward, because both propagate into
the `REC-` document and the PARKED prompts this tranche must write.

**1. Eleven call sites, not twelve.** `grep -n _defer_untransactional_v6_phase
src/deepreason/scheduler/scheduler.py` returns twelve lines; the first (696) is
the `def`. The eleven calls are 1358, 1366, 2187, 2582, 2606, 2611, 2693, 2736,
2742, 2819, 2947 — exactly the list the brief gives, with no "one more".

**2. Eleven phases, not twelve — `premise-rent` is a `target_ref`, not a
phase.** The brief and the P-A1 tranche's FINDINGS.md F2 both say "eleven
phases" and then list twelve names. The extra name is `premise-rent`, which is
the third positional argument at `scheduler.py:2582-2585`:

    self._defer_untransactional_v6_phase(
        "premise-demarcation-variation",   # phase
        "variator",                        # role
        "premise-rent",                    # target_ref
    )

The record settles it independently of the code: the deferral event's `inputs`
are `[marker, phase, role, target_ref, obligation_ref, reason]`, and P-R1's
event puts `premise-rent` in the `target_ref` slot. The eleven real phases,
with the role each names, are:

| # | line | phase | role |
|---|---|---|---|
| 1 | 1358 | `hv-floor` | `variator` |
| 2 | 1366 | `rubric-trial` | `judge` |
| 3 | 2187 | `pairwise-discrimination` | `judge` |
| 4 | 2582 | `premise-demarcation-variation` | `variator` |
| 5 | 2606 | `paraphrase-audit-variation` | `variator` |
| 6 | 2611 | `paraphrase-audit-judgment` | `judge` |
| 7 | 2693 | `experiment-generator-authoring` | `conjecturer` |
| 8 | 2736 | `property-design` | `property_designer` |
| 9 | 2742 | `property-relevance-trial` | `judge` |
| 10 | 2819 | `vision-criticism` | `vision_critic` |
| 11 | 2947 | `hv-spot-check` | `variator` |

Five roles, not six phases-worth of roles: `variator` x4, `judge` x4,
`conjecturer`, `property_designer`, `vision_critic`.

Falsifiable prediction: a cycle-soak case whose manifest is `schema_version: 6`
and whose `variator[0]` seat carries the `variator.direct.v1` behavioural
contract grant will, driven against the deterministic stub for 8 cycles,
produce **0** events with a non-empty `state_diff.hv_set` and **>=1**
`v6-model-phase-deferred.v1` event whose phase is `hv-floor` or `hv-spot-check`
and whose role is `variator`. Removing the grant from that same case changes
neither number. Concretely, on the unfixed tree:

    python -u scripts/cycle_soak.py --case <grant-case>
    # then, over the soak's root:
    #   non-empty hv_set events            == 0
    #   v6-model-phase-deferred.v1 events  >= 1, phase in {hv-floor, hv-spot-check}

If the grant-bearing case produced even one `hv_set`, this diagnosis is wrong.

Ruled out: **"the behavioural-contract grant was simply missing."** This was the
P-A1 tranche's own design hypothesis — P-S1's null `criticism_policy` gates the
defender/judge/variator grants at `run_manifest.py:2059-2077`, so its 171
deferrals looked fully explained by the absent grant. P-A1 closed that gap
(`variator[0]` holds `variator.direct.v1`) and the deferrals continued: 19 on
the live root measured above, and zero `hv_set` across a 24-of-24-cycle clean
soak. The grant was a real and separate defect; it is not this one. The gate
never reads the grant, so supplying it cannot change the gate's answer.

## Forecast stop conditions: checked, and neither is triggered

GOAL.md forecast two priced stops. Both are answered NO by reading, before any
design exists — recorded now so `dr-propose-fix` starts from measurement rather
than from hope, and so a later phase cannot quietly re-open them.

- **A new contract id or work kind (surface 3, `verification/`) — NOT needed.**
  `informal/trial.py:839-851` *already* dispatches a `role="variator"` call with
  `output_model=VariatorOutput` through `_v6_transactional_trial_call`, under
  the existing `WorkflowTaskKind.DEFENDED_TRIAL_STEP` and whatever
  `wire_contract_for("variator", VariatorOutput, profile, aliases)` resolves to
  — which is `variator.direct.v1` or `variator.compact.v1`
  (`cli/doctor.py:991-995`, `run_manifest.py:3067-3068`). `measures/hv.py:136`
  makes the identical `adapter.call("variator", pack, VariatorOutput)`. So the
  exact call shape `hv` needs is already transactionally dispatched elsewhere in
  the tree with no new contract and no new work kind.
- **The qualification battery's enumeration (surface 5) — NOT changed.**
  `cli/doctor.py:385-420` projects doctor pairs from
  `manifest.route_seat_behavioral_capability_plan`, which is manifest data
  compiled at manifest build time. Reading that plan from the scheduler adds no
  contract to any seat and therefore adds no pair to the battery.
- **The plan is already in the scheduler's hand.** It is a field on the
  RunManifest (`run_manifest.py:1286`) and the scheduler already holds
  `self.run_manifest` (`scheduler.py:715`). The public resolver
  `resolve_route_seat_behavioral_capability(manifest, role=, seat=,
  endpoint_id=, route_sha256=)` (`run_manifest.py:2319`) returns a grant whose
  `.contracts` carry `.contract_id`. So making the gate configuration-driven
  requires reading `run_manifest.py`, not editing it.

## Second cause found and NOT pursued here

`docs/map/SEAM-scheduler-x-workflow.md`'s Traps records that the deferral marker
`v6-model-phase-deferred.v1` is bound to a local variable before
`record_measure`, so `tests/test_signals.py`'s AST scan — which reads only
*literal* first arguments — never sees it, and the signal is unregistered.
Confirmed still true at `scheduler.py:724`. It is independent of this tranche's
goal (registering the signal would not make `hv` measure, and making `hv` measure
would not register the signal) and is filed in PARKED.md as P4 rather than
folded in.

---

## Corrections to this document, 2026-09-02, from a wider census run after it was written

Recorded as amendments rather than by silent edit, except the arithmetic error,
which is corrected in place above because leaving a wrong number in the evidence
list would be worse than showing the edit.

**C1 — P-R1's event count was wrong by exactly 2x, and is corrected above.**
The Evidence list and GOAL.md said 5 414 events. The true figure is **2 707**
(`wc -l experiments/2026-08-25-poietics-program/run/log.jsonl` -> 2707). The
error was mine: the first census script counted a `Counter` that carried two
keys per event, so `sum(values())` doubled. Every other number in this document
came from later scripts and is unaffected — the 117 deferrals, the phase split
(74/42/1), the role, and the reason code all reproduce. The independent
reproduction artifact `repro_record.py` printed 2707 for this root from the
start, so the artifact was right and only the prose was wrong.

**C2 — a deferral RECORD is not a deferral CALL.** The gate deduplicates by the
4-tuple `(phase, role, target_ref, obligation_ref)` and keeps a per-Scheduler
`seen` set (`scheduler.py:724-733`), so "117 deferrals" means 117 DISTINCT
tuples, not 117 gate invocations. The true call count is higher and is not
recoverable from the record. Every count in this document and in
`repro_record.py` is a record count; none is a call count. The direction of the
error is safe — records under-count calls, so the defect is at least as large as
stated — but the sentence "hv was asked for 116 times" above should be read as
"hv was asked for on 116 distinct targets".

**C3 — P-R1 is a CONTROL, not the defect row, and the decisive root is a
different one on `main`.** P-R1's own manifest gives `variator[0]` an EMPTY
contract list (`criticism_policy: null`), so on that root the missing grant is a
SECOND, independent blocker sitting in front of the gate. Deferring there is
correct behaviour. The root that isolates this defect —
found after this document was first written, and now the primary evidence in
REPRO.md — is `experiments/2026-08-12-live-grounded-extension-expansion/run`:
`state=completed`, `stop_reason=budget_exhausted`,
`criticism_policy.authority = defended_trial`, `variator[0]` holding
`variator.direct.v1`, **336** hv deferrals (`hv-spot-check` 241, `hv-floor` 95)
and **zero** `hv_set`. It is on `main`, needs no branch and no soak, and it is
what makes the diagnosis decisive rather than merely consistent.

**C4 — the census is wider than this document claimed.** Across all committed
run roots: **zero** roots with a v6 manifest carry any `hv_set` event, and the
only roots that carry one at all have `schema_version` 1 or 2. The v6 subset
measured by `repro_record.py` is 50 roots, 56 501 events, 2 661 hv deferral
records, 0 measurements.

**C5 — two mechanisms downstream of the deferral, worth knowing before designing
the fix.** First, `_hv_skipped` (`scheduler.py:2952`) is an in-memory set on the
Scheduler instance, not durable: once an artifact is deferred it is blacklisted
for the life of the process and never re-checked, but a resume starts the
blacklist empty while the deduplicated marker set is rebuilt from the log — so
resume changes which artifacts are re-attempted. Second, an `hv-floor`
commitment is NOT registry-evaluable, so `crit_program` skips it and
`pareto_scores`' coverage denominator does not count it. A deferred `hv-floor`
therefore neither refutes its target nor lowers its coverage: it is completely
inert, which is why nothing downstream ever complained.
