# hv v6 reachability — results

Dated, honest-ledger segments. What the record shows, and the residue — what
remains unproven. Accepted does not mean true.

---

## 2026-09-02 · Segment 1 — the defect is on `main`, and it is larger than the brief said

**What the record shows.** The tranche was commissioned on evidence from three
roots, two of which live on another branch. It did not need them. `main` alone
carries the whole contradiction, and joining two files of one root is the whole
reproduction.

Census over every committed v6 run root, read-only
(`repro_record.py`): **50 roots, 56 501 log events, 2 661 `hv` deferral records,
0 `hv_set` measurements.** No v6 root in this repository has ever measured `hv`.
The only roots that carry an `hv_set` event at all have `schema_version` 1 or 2.

The decisive row is `experiments/2026-08-12-live-grounded-extension-expansion/run`
— grounded-extension run `8e22d0431fd2b98d`:

| | |
|---|---|
| state / stop_reason | `completed` / `budget_exhausted` — not an early death |
| `criticism_policy.authority` | `defended_trial` |
| `variator[0]` behavioural grant | `['variator.direct.v1']` — **the exact contract the gate stands in for** |
| `hv` deferral records | **336** (`hv-spot-check` 241, `hv-floor` 95) |
| `hv_set` events | **0** |

Grant present, gate closed anyway. The other 46 deferring roots hold no grant,
and their deferrals are CORRECT — they are the control, and the fix leaves them
untouched.

**The mechanism, read only after the record named it.**
`Scheduler._defer_untransactional_v6_phase` (`scheduler.py:696-752`) computed
its whole answer from `manifest.schema_version != 6` and then returned `True`
unconditionally. Its only other branch was `schema_version != 6`, which
operations parity (2026-08-13, one run path) forecloses. Eleven optional model
phases sat behind it with run-config knobs — `HV_K`, `HV_MIN`, `AUDIT_PERIOD`,
`GEN_*`, `PROP_*`, `VISION_CRIT_PER_CYCLE`, `ADVISORY_TRIALS_PER_CYCLE` — that
parse, compile and appear in the manifest over behaviour that cannot fire.

**Two corrections to the commissioning brief, both measured.** *Eleven* call
sites, not twelve — the twelfth `grep` hit is the `def`. And *eleven* phases,
not twelve: `premise-rent` is the `target_ref` at `scheduler.py:2582-2585`, not
a phase name. The record settles the second independently of the code, because
the deferral marker's own `inputs` tuple is
`[marker, phase, role, target_ref, obligation_ref, reason]` and `premise-rent`
sits in the fourth slot. Both the 2026-09-01 P-A1 write-up and this tranche's
own instruction carried the twelve-name list; `docs/ERRATA.md` E68 records it so
the count is not carried forward again.

**One correction to this tranche's own first artifact.** GOAL.md and the first
draft of DIAGNOSIS.md said P-R1 carries 5 414 log events. It carries **2 707**
(`wc -l`). The error was a census script summing a `Counter` that held two keys
per event. Corrected in place, with the amendment recorded; every other figure
came from later scripts and reproduces. `repro_record.py`, written independently,
printed 2707 for that root from the start.

**Residue.** A deferral RECORD is not a deferral CALL — the marker deduplicates
by `(phase, role, target_ref, obligation_ref)`, so 2 661 under-states the
requests and the true rate is not recoverable from the record. The direction is
safe (the defect is at least as large as stated), but no number here is a call
count.

---

## 2026-09-02 · Segment 2 — the fix, and the two things that make it not obvious

**What shipped.** `workflow/legacy_phase_contracts.py` declares a VERSIONED
table of phase → (role, authorizing contracts, dispatch); the gate consults it
before recording debt and returns `False` when the seat holds a listed contract.
`measures/hv.py` self-detects the bound manifest and routes its variator call
through `informal/trial.py`'s existing v6 bracket, generalised by three keyword
parameters rather than copied. `hv-spot-check` is converted; the other ten rows
are not.

**The deferral branch is byte-identical.** Same marker string, same six-element
`inputs`, same `transaction-contract-unavailable` reason, same dedup set. A
grant-less run's log after the fix is the log it would have written before. That
is the property the 46 control roots demand, and it is asserted element by
element rather than as a set.

**Two design points the code cannot show, and both were proven by mutation
rather than argued.**

*The `dispatch` field, not the grant, is what converts a phase.* Ten rows have
no dispatch written. Opening the gate on the grant alone would send them to a
provider unbound and trip the fail-closed adapter guard the gate exists to
respect — turning a silent inertness into a killed root. Mutation M8 (revert
hv's dispatch, leave the gate open) raises exactly
`WorkflowAuthorizationError: RunManifest v6 provider dispatch requires a bound
transaction`. The gate's original author was right; only its decision was wrong.

*`llm_call` is `None` under v6 because the transaction is the accounting.*
`Harness.record_llm_calls`'s own docstring states the rule — every call reaches
the log exactly once, or replay and `eval_report` silently under-count. Mutation
M9 (re-attach the call) raises `WellFormednessError: transactional provider call
lacks live issued authority`. Returning `None` makes all five downstream record
sites correct with no edit to any of them.

**Frozen surfaces: CLEAR, measured not asserted.**
`python tools/blast_radius.py --files …` returns
`"frozen_surface_contacts": []`, `"frozen_adjacent_contacts": []`,
`"qualification_digest": []`, `"wheel_smoke_pins": []`,
`"frozen_surface_verdict": "CLEAR"`. No new contract id (both variator
contracts already exist and are already granted), no new work kind
(`informal/trial.py` already dispatches the identical variator call under
`DEFENDED_TRIAL_STEP`), no battery change (the fix reads the plan and grants
nothing).

The writer-side alternative — widening the grant compiler so v6 runs get the
variator grant by default — is closed on its own evidence, and this is worth
recording because it was the more obvious road: the behavioural plan is
RE-DERIVED and compared on every manifest reload
(`run_manifest.py:1595-1604`, raising
`V6_ROUTE_SEAT_BEHAVIORAL_CAPABILITY_PLAN_MISMATCH`), so a compiler change would
invalidate every committed v6 root on load. Reader-side is not merely preferred
here; it is the only road that does not break the corpus.

---

## 2026-09-02 · Segment 3 — the soak is green and cannot see the thing it was asked to see

**What the record shows.** Two soaks, differing in exactly three config lines,
both clean:

| | grant-bearing (`--case hv-grant`) | control (`--case reach-rich`) |
|---|---|---|
| terminal | `completed` / `budget_exhausted` | `completed` / `budget_exhausted` |
| cycles | 8 of 8 | 8 of 8 |
| `verify_root` | 0 violations | 0 violations |
| `hv_set` events | 0 | 0 |
| deferral records | 1 (`premise-demarcation-variation`) | 1 (`premise-demarcation-variation`) |
| ACCEPTED artifacts | 15 | 15 |
| `state.addr` pairs | 1 | 1 |
| ACCEPTED **and** addressed | **0** | **0** |

That last row is the finding. `_lazy_hv` requires an artifact that is both
`ACCEPTED` **and** present in `state.addr` (`scheduler.py:2942-2949`), and an
8-cycle single-problem stub run produces none: `addr` holds one pair, the seed's
own. P-R1, by contrast, carries 435 ACCEPTED artifacts, 186 `addr` pairs and 82
that are both — which is why P-R1 recorded 74 `hv-spot-check` deferrals and the
soak records none. **The soak never reaches the gate, so it cannot discriminate
on `hv` in either direction.**

**What the soaks DO prove, and it is not nothing.** The grant-bearing shape —
the one no committed soak case could previously express, because
`run_manifest.py:2059-2065` mints the variator grant only under a
`defended_trial` criticism policy and all five committed cases lack one — drives
eight clean cycles to a typed terminal with a clean `verify_root`, identically
to its control. No regression. And the one deferral both runs record is
`premise-demarcation-variation`, an UNCONVERTED row, deferring identically with
and without the grant: a recorded control for the nine-phase safety property
that no unit test could supply.

**What proves the dispatch instead.**
`tests/test_hv_v6_reachability.py::test_hv_measures_end_to_end_through_a_real_v6_transaction`
drives a real `Harness` and a real `InquiryTransactionService`: the granted seat
opens the gate, the variator call goes out under contract `variator.direct.v1`
and work kind `DEFENDED_TRIAL_STEP` with payload schema `hv-variation-step.v1`,
exactly one `hv_set` event lands in the log, and that event's `llm` is `None`.
Reverting either half of the fix breaks it (mutations M7, M8, M9).

**Honest correction to GOAL.md's own success criterion.** Criterion 1 asked the
cycle soak on a grant-bearing shape to produce ≥1 `hv_set` within 8 cycles. That
criterion is not satisfiable by any 8-cycle soak on the deterministic stub, and
the reason has nothing to do with the fix. It was written before anyone had
measured `_lazy_hv`'s precondition. The criterion it should have named is the
end-to-end transaction test; the soak's honest job here is the no-regression
half, which it did.

---

## 2026-09-02 · Segment 4 — residue

Stated as residue rather than buried, because two of these bound what the
tranche may be read to have proven.

- **`hv-floor` is NOT converted, and `hv` is therefore only half-reachable.**
  `run_hv_floor` is not a ranking measure: on `hv < hv_min` it calls
  `register_fail_warrant` and REFUTES its target, and `rules/spawn.py:150-172`
  pins its criterion onto every connection problem the harness mints. Converting
  it changes refutation outcomes with no configuration having asked. Priced from
  the record: 53 connection problems and 95 distinct deferred `hv-floor` targets
  on the grant-bearing root alone. Parked P7 with the prompt written; the code
  change is one table row and the evidence question is the whole tranche.
- **Reachable does not mean reached.** `hv` is now reachable by configuration —
  but only through a `criticism_policy` whose authority is `defended_trial`,
  because that is what mints the grant. Of 50 committed v6 roots, exactly 4 hold
  a variator grant and all 4 are `defended_trial`. Whether that minting
  condition is itself too narrow — the solo-run law says sole-model operation
  must not be locked out of a capability, and `hv` invokes no judge — is parked
  as P5, and it is a `run_manifest.py` question (frozen surface 4), not a gate
  question.
- **Ten of eleven phases still defer**, by design.
  `REC-give-a-legacy-phase-v6-transactional-dispatch.md` is the path, one phase
  per tranche; P1 carries the prompt. Two of the ten (`property-design`,
  `vision-criticism`) cannot be converted at all until some compiler mints a
  grant for their roles — their rows carry an empty contract set to say so.
- **No live run.** GOAL.md's optional live check was not taken: the offline
  end-to-end test proves the dispatch on the real transaction machinery, and a
  live run would add an observation, not a proof. The API key was not requested.
- **The diff exceeded its own budget.** `tools/diff_budget.py` returns
  `EXCEEDED`: 210 insertions against GOAL.md's 150-line ceiling. Measured
  composition: ~95 lines are executable, the remainder module and function
  docstrings and blanks. One paragraph of the registry's docstring was moved to
  the map during implementation, because it narrated history — which CLAUDE.md's
  own comment convention forbids — but that was a correctness fix worth two
  lines, not a route to the ceiling. The overshoot is real and is reported
  rather than shaved.
- **`reach` untouched**, as instructed. Its zeros are empirical, not structural;
  parked P3.
