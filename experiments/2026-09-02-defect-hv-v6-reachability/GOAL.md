# Goal: make `hv` measurable on a v6 run whose variator seat carries a grant

Class: defect

Observed: on every committed v6 run, `hv` is never measured — the P-R1 root
`experiments/2026-08-25-poietics-program/run` carries 5 414 log events and
**zero** with a non-empty `state_diff.hv_set` (and zero non-empty `reach_set`),
measured by re-reading `log.jsonl` read-only:

    python - <<'PY'
    import json
    root="experiments/2026-08-25-poietics-program/run"
    hv=reach=n=0
    for line in open(root+"/log.jsonl"):
        e=json.loads(line); n+=1; sd=e.get("state_diff") or {}
        hv += bool(sd.get("hv_set")); reach += bool(sd.get("reach_set"))
    print(n, hv, reach)
    PY
    # -> 5414 0 0        (measured 2026-09-02, this container)

The operator's tranche brief reports the same shape on two further roots —
P-S1 `9e48a36b1dec91ee` (171 variator deferrals) and P-A1 `4565139800f5ca02`
(19 deferrals, 24 cycles) — and records P-A1 as decisive because its
`variator[0]` seat *held* the `variator.direct.v1` grant and `hv` still never
measured. Confirming those two roots' numbers against their own records is
`dr-diagnose`'s first obligation, not an assumption of this goal.

The documented guarantee contradicted is the modularity law (CLAUDE.md,
2026-08-26, operator verbatim: "There needs to be a priority that enforces
modularity. Customisation needs to be easy."): every behaviour a run can vary
must be reachable as configuration, and "enforced" means a check that can fail.
Eleven configurable phases sit behind one gate that no configuration can open,
and no check goes red.

## Map ids resolved (preflight, `docs/map/INDEX.md`)

| Id | Why it is in scope |
|---|---|
| `DR-SEAM-scheduler-x-workflow` | **read first** — owns `scheduler/scheduler.py` and the "legacy model phase with no transaction contract is recorded as typed completion debt rather than dispatched unbound" promise. The gate under investigation IS this seam's expression. |
| `DR-SUB-scheduler` | Owns `src/deepreason/scheduler/` — `_defer_untransactional_v6_phase` and its call sites |
| `DR-SUB-evaluation` | Owns `src/deepreason/measures/` and `src/deepreason/informal/` — `measures/hv.py` (the two `hv_set` producers) and `informal/trial.py` (the existing v6-transactional recipe to generalise) |
| `DR-SUB-workflow` | Owns `src/deepreason/workflow/` — the transaction service the dispatch must go through |
| `DR-INV-frozen-surfaces` | read before designing; five surfaces, seven paths, none of which this tranche may touch |
| `DR-INV-signal-contract` | "allocation touches EFFICIENCY NEVER EVIDENCE" — `hv` is a ranking measure, so this tranche may not move any status |
| `DR-CON-seats` | grants are seat-instance-keyed, not role-keyed |

**Map gap recorded, not a blocker:** the pair *evaluation × scheduler* has no
`SEAM-` document and no row in `INDEX.md`'s matrix, yet
`scheduler/scheduler.py:30-43` imports `measures.attention`, `measures.hv` and
`measures.reach` directly. The matrix lists pairs at coupling >= 10 plus
already-documented pairs, so the absence is the cutoff working as designed —
but INDEX.md's own rule applies: a pair absent from the table "never means the
two do not interact". Whether this tranche must write that seam document is a
`dr-propose-fix` decision, not a goal-setting one.

Success criterion (machine-decidable):

    # 1. THE DEFECT, offline. A cycle-soak case whose manifest is schema_version 6
    #    and whose variator seat holds `variator.direct.v1`:
    python -u scripts/cycle_soak.py --case <grant-case>
    # expected BEFORE the fix: 0 events with non-empty state_diff.hv_set  (RED)
    # expected AFTER  the fix: >=1 such event within 8 cycles             (GREEN)

    # 2. THE GUARD, offline. The same case with the grant removed from the seat:
    python -u scripts/cycle_soak.py --case <no-grant-case>
    # expected BEFORE and AFTER: 0 hv_set events AND the existing typed
    # deferral notice present, unchanged  (GREEN both sides)

    # 3. THE LAW, as a check that can fail. An architecture test that goes RED
    #    if `_defer_untransactional_v6_phase` can return True without consulting
    #    the route-seat behavioural capability plan:
    python -m pytest tests/test_hv_v6_reachability.py -q
    # expected: passes on the fixed tree; mutation-proven RED on the unfixed one

    # 4. EVIDENCE UNTOUCHED. On one fixed stub, a run with hv_set and a run
    #    without it produce identical status sets:
    python -m pytest tests/test_hv_v6_reachability.py -k evidence_unchanged -q
    # expected: passes

    # 5. THE GATE.
    python -m pytest tests/ -q -n 4
    # expected: 0 failed, except the two pre-authorized known-not-mine baselines
    # the operator named (the bc-dependent map check;
    # test_the_shipped_qualification_subject_digest_does_not_move) — recorded,
    # not stopped on.

    # 6. THE MAP.
    python tools/docs_verify.py
    # expected: 0 failed, full (non-`--fast`) mode, on the same commit as the code

In scope:
  - `src/deepreason/scheduler/scheduler.py` (the gate + the two `hv` call sites at 1358 and 2947)
  - `src/deepreason/measures/hv.py` (`run_hv_floor`, `hv_spot_check` — their dispatch path only)
  - one new shared v6-transactional dispatch helper, generalised from
    `src/deepreason/informal/trial.py::_v6_transactional_trial_call`, plus the
    declared VERSIONED grant-id-to-phase table it reads

NOT in scope (the nearest tempting things — each PARKED with a ready prompt):
  - **the nine other phases behind the same gate** (premise-demarcation-variation,
    premise-rent, paraphrase-audit-variation, experiment-generator-authoring,
    rubric-trial, property-design, property-relevance-trial,
    paraphrase-audit-judgment, pairwise-discrimination, vision-criticism). This
    tranche writes the recipe as a `REC-` map document so each is a one-step
    follow-up; it converts none of them.
  - **the coverage-charges-counterconditions inversion** in
    `src/deepreason/capture/programs.py`. Making `hv` measurable gives the
    Pareto sort a second axis; this tranche does not touch the sort.
  - **`reach`**: deterministic and ungated, its zeros are empirical. Noted, not touched.
  - **any file owned by the three concurrent windows**: `llm/providers.py`,
    `llm/split.py`, `application/text_runs.py`, `runtime/continuation.py`,
    `llm/endpoints.py`.

Budget: <=150 changed lines of `src/`, 1 commit (tests and map documents ride
in the same commit per repo law and are outside that count), <n> hours.

Stop conditions inherited from orchestrator: yes. Three are forecast now, before
any code is read, so a later phase cannot rationalise past them:
  - **any frozen-surface contact.** In particular: if the transactional dispatch
    needs a NEW contract id or work kind that replay validation must recognise,
    that is surface 3 (`verification/`) contact -> PRICED STOP, grant requested
    in FIX.md before a line of code. Prefer the existing `variator.direct.v1`
    contract and existing work kinds.
  - **any change to what the qualification battery enumerates** -> surface 5 ->
    PRICED STOP.
  - **any change that could alter acceptance/refutation on a fixed stub** ->
    STOP. Criterion 4 above exists to make this failure loud rather than silent.
