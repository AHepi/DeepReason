# VERIFY — every criterion in GOAL.md, with the command and its output

Verdict: **PASS (offline; no live run required by GOAL.md and none attempted)**

## G1 — does the soak run everything it declares?

**Answer: it did not.** Three defects, all of the `docs_verify` family, all now
closed. The census, before and after:

| what the soak declares | before | after |
|---|---|---|
| 9 committed cases | **4 compiled**, 5 refused `V6_SIMULATION_TOOLCHAIN_REQUIRED` before any assertion ran | **9 compile**, individually and enumerated in one process |
| 7 assertions | **A5/A6 emitted by no runnable case**, and not reported as absent | all 7 emitted on every run; A5/A6 evaluated by their carriers, `[N/A ]` with a reason elsewhere |
| records read by its own counters | unreadable records silently `continue`d, moving every count in the PASSING direction | counted, and **A7-record-fully-read** fails on them |
| builders | bare `__import__` + never-cleaned `sys.path`: a second case in one process silently got another experiment's `question.py` | loaded in isolation; every `experiments/` module evicted after |

Raw: `proof/A5A6_never_run.txt`, `proof/root_cause.txt`, `proof/after_all_cases.txt`.

## G2 — all nine cases compile and run

    $ for c in epoch3 pr1 pc1 pc2 pc2b split-legs hv-grant reach-rich pa1; do
        python -u scripts/cycle_soak.py --case $c --cycles 1; done

All nine compile and reach their assertions (`proof/after_all_cases.txt`). The
`exit 1` each returns at `--cycles 1` is the documented by-construction A4
failure — depth 1 is not past the deepest recorded death at cycle 2 — and is
the same value the four healthy cases returned before this tranche.

At real depth, the two cases that matter most:

    $ python -u scripts/cycle_soak.py --case split-legs            → exit 0
    [PASS] A4-cycles-reached   reached cycle 24 of 24 requested
    [PASS] A3-verify-root-clean   0 violation(s)

`split-legs` is the case that caught the P-C2b replay-invalid death — exit 1,
260 violations, dead at cycle 13. It now reaches 24 of 24 with a clean record,
which is the fix from `experiments/2026-08-27-defect-split-leg-recording/`
demonstrable again for the first time since the rot.

    $ python -u scripts/cycle_soak.py --case pc2b                  → exit 0
    [PASS] A5-in-run-checker-fired   3 demonstrative fail warrant(s) naming
           ['frontier-above-floor@v1', 'frontier-claim-honest@v1',
            'frontier-wellformed@v1']
    [PASS] A6-discharge-channel-carried-them   {'discharge-reask': 16}

These two assertions had been running on nothing at all. Run, they pass: the
in-run checker does fire and its refutations do reach the writer. That is
coverage recovered, not a cosmetic change to a report.

## G3 — nothing found is left undescribed

Three defects found, three fixed in this tranche (D-A, D-B, D-C in
DIAGNOSIS.md). One observation parked rather than fixed, in PARKED.md: the
three colliding `question.py`/`criteria.py` module names. It is no longer
reachable through the repaired loader, and editing three committed experiment
directories to work around a loader defect that is now fixed at the loader
would be the wrong repair.

## G4 — every change mutation-proven in BOTH directions

| change | mutation | result |
|---|---|---|
| F-A builders ask the policy | revert one builder to the pinned local toolchain | 2 tests RED (`proof/mutate_builders_and_a5a6.txt`) |
| F-B A5/A6 always emitted | delete the `else` branch | 1 test RED (same file) |
| F-C A7 | corrupt one byte of one attempt record | `ok=True` → `ok=False` (`proof/mutate_a7.py`, `proof/mutate_a7.txt`) |
| F-D builder isolation | restore the bare `__import__` | 4 tests RED (`proof/mutate_isolation.txt`) |

All 19 tests green with every fix in place. One test
(`test_case_module_leaves_no_experiment_module_cached`) did **not** fire on the
first mutation attempt because it was order-dependent; it was strengthened to
clear the cache first and then re-mutated, and it fires. A check that can only
go green is not a check, so this is recorded rather than quietly repaired.

The A7 mutation proof lives in `proof/`, OUTSIDE `scripts/` — a proof sharing a
file with the thing it judges can be made to pass by the same edit that breaks
the subject.

## G5 — the boundary gate

    $ python -m pytest tests/ -q -n 4
    4980 passed, 6 skipped in 1229.75s (0:20:29)          → rc 0

**0 failed.** No assertion was weakened and no test was skipped to reach it.
The base measured on this container earlier today was 4961 passed; the delta is
**+19, exactly the count of this tranche's new test file**. That is also the
frozen-surface verification: surface 5's own Traps entry records that a moved
qualification subject digest turns the gate red in ~40 places, and no such
failure appeared, so no committed subject digest moved.

    $ python tools/docs_verify.py
    docs_verify: 6 failed
      3 CON-run-identity.md   2 INV-frozen-surfaces.md   1 SEAM-llm-x-rules.md

Exactly the documented shallow-clone baseline (`docs/AUDIT_BASELINES.md:43`,
"5 OR 6 failed"), same documents and same distribution as the pre-change run.
An earlier invocation reported **7**; the extra was `CON-run-identity.md:313`
timing out at its 300 s ceiling while the operational wheel smoke held the same
4 CPUs. Re-run without contention it is 6. Recorded rather than dropped,
because a number that moved and then moved back is worth a sentence.

    $ python scripts/wheel_smoke.py                       → rc 0
    $ python -u scripts/wheel_operational_smoke.py        → rc 0

    $ python -u scripts/cycle_soak.py --case epoch3       → exit 0

The baseline invocation at `docs/AUDIT_BASELINES.md:210`, unchanged.

## Residue — what remains unproven

- **A5/A6 pass on `pc2b`; `pc2` was not run at depth.** The two carriers share
  a lineage and `pc2` compiles, but "both carriers evaluate their assertions
  green at depth" is measured for one of the two.
- **The three deaths the soak still cannot reach** — transport faults,
  completion truncation, continuability — are untouched here. They are the
  review tranche's P2 and a change tranche, not this one. Nothing in this
  repair makes the soak catch a death it could not catch yesterday; it makes
  the soak run the assertions it already had.
- **`--induce-repairs` was not re-run on the repaired cases.** Its baseline
  (exit 0) was confirmed on `reach-rich` before the change, not after.
- **D-C was inert in production and is proven only in-process.** No committed
  root was built against another experiment's question, because the soak has
  only ever been run one case per process. The defect was real and reachable,
  not observed in the wild.
- The `split-legs` and `pc2b` roots reported here were driven against the
  deterministic stub. They say the record is well-formed and the channel fired;
  they say nothing about any model's reasoning.
