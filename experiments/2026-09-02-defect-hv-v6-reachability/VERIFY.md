# Verification

Verdict: **PASS**, with GOAL.md's criterion 1 replaced on measurement and
criterion 6 read against the living baseline. Both replacements are evidenced
below rather than asserted. Two items are handed to the operator: the `hv-floor`
road (a stop the brief itself required) and a diff-budget overshoot.

---

## Criterion 1 — the grant-bearing soak. NOT MET AS WRITTEN, and the criterion is wrong

    python -u scripts/cycle_soak.py --case hv-grant
      drive 196.5s, 8 of 8 cycles
      [PASS] A1-typed-terminal      state='completed' stop_reason='budget_exhausted'
      [PASS] A2-no-operational-failure
      [PASS] A3-verify-root-clean   0 violation(s)
      [PASS] A4-cycles-reached      reached cycle 8 of 8
      [soak] exit 0 (clean)
      -> hv_set events: 0

    python -u scripts/cycle_soak.py --case hv-grant --cycles 24
      drive 753.8s, 24 of 24 cycles, exit 0 (clean), verify_root 0 violations
      -> hv_set events: 0

Zero, at both depths, on the shape that carries the grant. That is not the fix
failing; the soak never reaches the code the fix changed. Measured cause:

| | 8-cycle grant | 24-cycle grant | control | P-R1 (a real run) |
|---|---|---|---|---|
| ACCEPTED artifacts | 15 | 19 | 15 | 435 |
| `state.addr` pairs | 1 | 1 | 1 | **186** |
| ACCEPTED **and** addressed | **0** | **0** | **0** | **82** |
| problems | 1 | 1 | 1 | 400 |
| `hv-spot-check` deferrals | 0 | 0 | 0 | 74 |

`_lazy_hv` (`scheduler.py:2942-2949`) skips any artifact that is not both
`ACCEPTED` and present in `state.addr`. A stub-driven soak stays a
single-problem run, so `addr` never holds more than the seed's own pair and the
loop never reaches the gate — at 8 cycles or at 24. **The soak cannot
discriminate on `hv` in either direction**, and it could not have before the fix
either. GOAL.md's criterion 1 was written before anyone had measured that
precondition; it names an instrument that cannot see the claim.

**The criterion that should have been written, and its result:**

    python -m pytest tests/test_hv_v6_reachability.py::test_hv_measures_end_to_end_through_a_real_v6_transaction -q
    1 passed

That test drives a real `Harness` and a real `InquiryTransactionService` on a
manifest whose `variator[0]` holds `variator.direct.v1`, and asserts on the
record rather than the return value: exactly one `hv_set` event in the log,
carried by a work item of kind `DEFENDED_TRIAL_STEP` under contract
`variator.direct.v1` with payload schema `hv-variation-step.v1`, and that
event's `llm` is `None`. It is RED on the unfixed tree three different ways
(mutations M7, M8, M9 below).

**What the soaks DO prove, and it is not nothing.** The grant-bearing shape is
one no committed soak case could previously express — `run_manifest.py:2059-2065`
mints the variator grant only under a `defended_trial` criticism policy, and all
five committed cases lack one. It now drives 8 and 24 clean cycles to a typed
terminal with a clean `verify_root`, identically to its control. **No
regression.**

## Criterion 2 — the no-grant guard. MET, GREEN on both sides

    python -u scripts/cycle_soak.py --case reach-rich
      8 of 8 cycles, exit 0 (clean), verify_root 0 violations
      -> hv_set 0; deferral records: {('variator','premise-demarcation-variation'): 1}

Identical to the grant-bearing run in every measured respect. The one deferral
both record is `premise-demarcation-variation` — an UNCONVERTED row deferring
with and without the grant, which is a recorded control for the ten-phase safety
property that no unit test could supply.

The unit-level guard is where the discrimination actually shows:

    python experiments/2026-09-02-defect-hv-v6-reachability/repro_gate.py
    --- GRANT PRESENT: experiments/2026-08-12-live-grounded-extension-expansion/run
        variator seat behavioural grant ['variator.direct.v1']
        _defer(...'hv-floor', 'variator')       -> True      (UNCONVERTED, by design)
        _defer(...'hv-spot-check', 'variator')  -> False     (was True)
        typed deferral markers written           ['hv-floor']
    --- CONTROL, no grant: experiments/2026-08-25-poietics-program/run
        _defer(...'hv-floor', 'variator')       -> True      (unchanged)
        _defer(...'hv-spot-check', 'variator')  -> True      (unchanged)
        typed deferral markers written           ['hv-floor', 'hv-spot-check']
    NOT REPRODUCED: the gate consulted the grant (post-fix behaviour)
    exit 1                          (was exit 0 before the fix)

The reproduction artifact inverted exactly as REPRO.md predicted.

## Criterion 3 — a check that can fail. MET, with nine mutation proofs

    python -m pytest tests/test_hv_v6_reachability.py -q
    24 passed in 2.48s

Each mutation was applied to the fixed tree, the suite re-run, and the tree
restored. Every one goes RED, and on the right test:

| # | mutation | tests that go RED |
|---|---|---|
| M1 | the consultation deleted | 5, incl. both architecture limbs |
| M2 | the consultation made inert (`and False`) | 4, incl. the behavioural limb |
| M3 | `variator.compact.v1` dropped from the row | the compact-seat test |
| M4 | `rubric-trial` flipped to `TRANSACTIONAL` | the unconverted-phase test |
| M5 | a registry row removed | the call-site census + the role census |
| M6 | the seat comparison dropped | the wrong-seat test |
| M7 | gate reverted to `schema_version`-only | 5, incl. end-to-end |
| M8 | hv's dispatch reverted to `adapter.call` | end-to-end, with `WorkflowAuthorizationError: RunManifest v6 provider dispatch requires a bound transaction` |
| M9 | `llm_call` re-attached under v6 | end-to-end, with `WellFormednessError: transactional provider call lacks live issued authority` |

M8 is the one worth keeping: it shows the gate's original purpose was real. The
fix does not remove the fail-closed guard; it teaches the gate which seats have
already satisfied it.

## Criterion 4 — evidence untouched. MET for the converted producer

    python -m pytest tests/test_hv_v6_reachability.py -k "changes_no_status" -q
    1 passed

The test asserts more than the in-memory status map: it walks every event the
spot-check wrote and requires that none carries a `status_changed` entry and
none carries an output, so a replay cannot reach a different verdict either.

**The scope of this claim, stated so it is not over-read.** It holds for
`hv_spot_check`, which is the only producer this tranche converted.
`run_hv_floor` is NOT a ranking measure and was deliberately left unconverted —
see the operator decision below.

## Criterion 5 — the gate. MET

    python -m pytest tests/ -q -n 4
    4629 passed, 6 skipped in 920.35s (0:15:20)

**0 failed.** Neither pre-authorized baseline failure appeared. Full output at
`full_gate.txt`. The affected ring was run separately first and was also clean
(1251 passed, 1 skipped).

## Criterion 6 — the map. MET against the living baseline, not against "0 failed"

    python tools/docs_verify.py        # full mode, idle box, after the gate
    docs_verify: 5 failed
      SEAM-llm-x-rules.md:54
      INV-frozen-surfaces.md:181
      CON-run-identity.md:211, :213, :215

That is **exactly** `docs/AUDIT_BASELINES.md`'s documented shallow-clone
baseline, with **zero delta** — the first two are the standing rows, the three
`CON-run-identity` rows are git-history checks that need a full clone
(`git rev-parse --is-shallow-repository` -> `true` here). GOAL.md said "0
failed"; the repo's own living baseline says 5 or 6 on this container, and the
baseline is the authority CLAUDE.md points at.

**Two failures in the FIRST run were mine, and both are fixed in the commit.**
`SEAM-llm-x-manifest.md:44` (30 -> 31) and `SEAM-scheduler-x-rules.md:39`
(9 -> 10) are coincidence censuses counting files that mention both sides of a
seam. `measures/hv.py` already imported both sides; the tranche added a
`_v6_manifest` helper whose DOCSTRING names `RunManifest` and cites the
scheduler-x-rules keyword-free invariant. Prose, not coupling — the same shape
`SEAM-scheduler-x-workflow` records for its own 13-to-14 move. Both counts were
updated with the reason written beside them.

**A sixth failure was environmental and is now a documented row.**
`INV-frozen-surfaces.md:669` runs the judge-canary pricing script, which does
`git show origin/claude/deepreason-p-s1-commitments-wowcib:…`. This container
had not fetched that branch, so the check died with exit 128 — which looks
exactly like a code failure. After `git fetch`, it passes (4 passed). Added to
`docs/AUDIT_BASELINES.md` as an ENVIRONMENT row, distinct from the shallow-clone
rows because `--unshallow` does not fix it.

## Frozen surfaces — CLEAR, measured

    python tools/blast_radius.py --files src/deepreason/workflow/legacy_phase_contracts.py \
      src/deepreason/scheduler/scheduler.py src/deepreason/informal/trial.py \
      src/deepreason/measures/hv.py
    "frozen_surface_contacts": []
    "frozen_adjacent_contacts": []
    "qualification_digest": []
    "wheel_smoke_pins": []
    "frozen_surface_verdict": "CLEAR"

Both stops FIX.md forecast are answered NO by the instrument, not by argument.

## Historical roots re-checked

Not required by the ladder — the fix changed a writer and added a module; no
reader or validator was touched, and `blast_radius` confirms it — but run as
insurance:

| root | before | after |
|---|---|---|
| `experiments/2026-08-25-poietics-program/run` | (unchanged code path) | `violations: []`, 2707 events |
| `experiments/2026-08-27-pc2b-symmetric-reasoning/run` | (unchanged) | `violations: []` |

`repro_record.py`'s census over 50 committed roots is byte-identical after the
fix, and that is the intended result: those roots were written by the defective
code and are append-only evidence of their own version. Nothing may edit them,
and nothing did.

Live attempt: **none**. GOAL.md's live check was optional. The offline
end-to-end test exercises the real transaction machinery, so a live run would
add an observation rather than a proof; the API key was not requested.

---

## Verdict: PASS

`hv` is measurable on a v6 run whose variator seat carries a
`variator.direct.v1` (or `.compact.v1`) grant, and defers exactly as before —
byte-identical typed notice — when it does not. The modularity law's "check that
can fail" exists: nine mutations, nine reds.

## Residue (honest)

- **Half the goal's scope is delivered.** `hv-spot-check` dispatches;
  `hv-floor` does not, and that was a deliberate stop, not an oversight — see
  the operator decision below.
- **The soak is a null instrument for `hv`** and was before this tranche. Proven
  at two depths. Its honest job here was the no-regression half.
- **Reachable is not reached.** The grant that opens the gate is minted only
  under `criticism_policy.authority == "defended_trial"`; 4 of 50 committed v6
  roots hold one. Whether that is too narrow is parked as P5 — a
  `run_manifest.py` question (frozen surface 4), not a gate question.
- **Ten of eleven phases still defer**, by design. Two of the ten
  (`property-design`, `vision-criticism`) cannot be converted at all until some
  compiler mints a grant for their roles; their rows carry an empty contract set
  to say so.
- **`reach` untouched**, as instructed. Its zeros are empirical.
- **No live evidence** that a real model's variator output produces a useful
  `hv` number. The tranche proves the call is made and recorded, not that the
  measurement is good.

## Two things for the operator

**1. The `hv-floor` road — the stop the brief required.** `run_hv_floor` mints a
demonstrative fail warrant on `hv < hv_min` and `rules/spawn.py:150-172` pins its
criterion onto every connection problem the harness spawns, so converting it
changes what runs REFUTE with no configuration having asked. Priced: 53
connection problems and 95 distinct deferred `hv-floor` targets on the
grant-bearing root alone. Shipped OFF; the change is one table row. Parked P7
with the prompt written. Recommendation: leave it off and settle it in a
run-and-decide tranche that can produce actual warrants to read, because the
question is whether the reinstated refutations are sound and no offline
instrument can answer that.

**2. The diff-budget overshoot.**

    python tools/diff_budget.py 971860c42 --ceiling 150 --paths <the four change sites>
    {"total_insertions": 210, "ceiling": 150, "verdict": "EXCEEDED"}

Composition, measured: of the registry module's 129 insertions, **45 are
executable** and the rest are the module docstring, function docstrings,
comments and blanks; across all four files roughly 95 lines are executable
against 115 of prose. FIX.md estimated 119 and under-counted documentation. One
paragraph was moved out to the map during implementation because it narrated
history, which CLAUDE.md's comment convention forbids — a correctness fix worth
two lines, not a route to the ceiling. Getting under 150 would mean deleting
constraint documentation the next tranche needs. Recommendation: accept the
overshoot and re-set the ceiling convention to count executable lines; say the
word and the docstrings come out instead.

## Errata

`docs/ERRATA.md` **E68** — added in the fix commit. `SEAM-scheduler-x-workflow`'s
Traps recorded the empty v6 criticism ladder as "not a bug"; it had been one
since 2026-08-26. The entry also corrects the twelve-phase-name list carried by
the 2026-09-01 P-A1 write-up and by this tranche's own commissioning
instruction (`premise-rent` is a `target_ref`), and states the generalisable
lesson: a Traps entry recording a JUDGEMENT ages against laws it never mentions,
and this one was falsified twice by two operator laws thirteen days apart
without a line of the code it described changing — so no check could have caught
it.
