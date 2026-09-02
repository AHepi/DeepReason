# Goal: a commitment that was NOT EVALUATED must not move an artifact's coverage coordinate

Class: defect

Observed: on three live roots the Pareto frontier is dominated by problems the
harness minted from itself rather than by artifacts answering the operator's
seed question — P-S1 `9e48a36b1dec91ee` (58 frontier members harness-minted,
all 40 seed-answering artifacts dominated), P-A1 `4565139800f5ca02` (14
frontier members, 1 seed = 7%, 13 harness-minted; corroborated independently
at `experiments/2026-09-01-live-all-modules-p-a1/MONITOR_REVIEW.md`, row "D1:
frontier 1 seed / 13 harness-minted — AGREE, `frontier.txt`: 1 seed, 3 conn,
8 research, 2 disc"), and P-R1 in the same shape. `PARETO_AXES =
["hv","reach","coverage"]`; `hv` was structurally unmeasurable on every v6 run
until `5f34e4d00` (MONITOR_REVIEW.md row F2 — AGREE, verified in code) and
`reach` is empirically zero, so the frontier sorted on `coverage` alone.
`coverage` is passes / evaluable-commitments (`scheduler/scheduler.py:202-218`
`pareto_scores`); an observation-valued commitment evaluates through
`programs.py` `_reasoning_observation_pending`, which returns OVERRUN
unconditionally ("observation requires registered evidence"). OVERRUN is not
PASS, so every falsifiable countercondition an artifact declares LOWERS its
coverage — the artifact making more testable claims ranks below the one making
none.

Success criterion (machine-decidable):

    # 1. RED today, GREEN after: declaring pending commitments is free
    python -m pytest tests/test_coverage_pending_commitments.py -q
    #    two artifacts identical except one declares three additional
    #    observation-valued counterconditions receive the SAME coverage
    #    coordinate

    # 2. GREEN today, GREEN after: a commitment that actually FAILS still
    #    lowers coverage (the fix must not blunt real refutation)
    python -m pytest tests/test_coverage_pending_commitments.py -q -k fails_still_lowers

    # 3. GREEN today, GREEN after: acceptance/refutation identical before and
    #    after on the fixed stub (ranking is efficiency, never evidence)
    python -m pytest tests/test_coverage_pending_commitments.py -q -k status_unchanged

    # 4. unchanged, extended not weakened
    python -m pytest tests/test_formalism_optional_rank.py -q

    # 5. the gate
    python -m pytest tests/ -q -n 4        # 0 failed

    # 6. measurement, reported not asserted: offline re-score of the committed
    #    P-A1 root on a COPY, before/after frontier composition
    experiments/2026-09-02-defect-coverage-pending-commitments/rescore_pa1.py

In scope (max 3):
  - `src/deepreason/programs.py` (evaluable / evaluate — the OVERRUN verdict)
  - `src/deepreason/scheduler/scheduler.py` `pareto_scores` (the denominator)
  - `src/deepreason/capture/pareto.py` (the frontier comparison, only if the
    denominator change is insufficient)

NOT in scope: strict seed domination (a parked tranche — the seed question wins
rank TIES today and that stays exactly as it is); `reach`'s empirical zeros;
the nine phases behind the v6 legacy deferral gate; `llm/endpoints.py`,
`application/text_runs.py` and `runtime/continuation.py` (other live windows
own them); any live reasoning run.

Budget: <=150 changed lines, 1 commit, ~4 hours
Stop conditions inherited from orchestrator: yes

## Map preflight (resolved before any design)

Read in the order `dr-drive-harness` §4 requires: `docs/map/INDEX.md` →
`docs/map/INV-frozen-surfaces.md` → seam → subsystems.

| id | why it is in the tranche |
|---|---|
| `DR-INV-frozen-surfaces` | read FIRST. The five surfaces span seven paths (`capabilities/state.py`, `harness.py`, `invariants.py`, `verification/`, `run_manifest.py`, `qualification.py`) plus frozen-adjacent `route_fingerprint` in `llm/firewall.py`. **None of the three in-scope paths appears on that list** — no expected frozen contact. |
| `DR-SUB-scheduler` | `Owns: src/deepreason/scheduler/` — `pareto_scores`, `PARETO_AXES`, the frontier section |
| `DR-SUB-evaluation` | `Owns: src/deepreason/programs.py` — `evaluable`, `evaluate`, `_reasoning_observation_pending`, the PASS/FAIL/OVERRUN verdict vocabulary |
| `DR-SUB-periphery` | `Owns: src/deepreason/capture/` — `capture/pareto.py::frontier`, which already drops an ABSENT axis from the pairwise comparison |
| `DR-CON-conjecture-kinds` | the R-g guardrail: nothing may weight rank/admission/acceptance on conjecture KIND. `pareto_scores`' own docstring cites it for the sibling case this goal generalizes. |
| `DR-CON-scheduler-ranking` | which problem a cycle works on; the recorded seed-question rank-tie invariant lives here |

**Map gap, recorded as a finding not a blocker** (`dr-drive-harness` §4.5): the
pair scheduler × evaluation has NO seam document and does not appear in
`INDEX.md`'s seam matrix at all. The whole agreement of this tranche crosses
it — `scheduler/scheduler.py::pareto_scores` reaches `programs.evaluable` /
`programs.evaluate` / `programs.PASS` through a FUNCTION-LOCAL import (`from
deepreason import programs`), which is precisely the traffic INDEX.md states
its coupling metric cannot see, and precisely the shape that cost the
`llm × verification` and `capabilities × channels` incidents. The agreement is
what a verdict MEANS to its only ranking consumer. Writing that seam is part of
this tranche.

## The falsifier for the diagnosis itself

The mechanism above is a hypothesis until the record carries it. `dr-diagnose`
must tabulate, per artifact on P-A1's frontier AND per dominated seed-answering
artifact: commitments by class, PASS/FAIL/OVERRUN counts, and the coverage
score the sort actually used. The diagnosis is CONFIRMED only if the dominated
seed answers carry more OVERRUN (pending) commitments than the harness-minted
winners. If the record shows something else, DIAGNOSIS.md says so verbatim and
this goal is re-bounded before any code is touched.
