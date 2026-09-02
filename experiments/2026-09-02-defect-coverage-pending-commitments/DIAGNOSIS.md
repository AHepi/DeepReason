# Diagnosis: the ranking axis is the one consumer that reads OVERRUN as a failed check

Primary cause: `scheduler/scheduler.py:202-241` `pareto_scores` builds the
coverage denominator from `programs.evaluable(...)` and then counts only
`programs.PASS` in the numerator, so a commitment whose verdict is
`programs.OVERRUN` — the typed verdict meaning *the harness obtained no
verdict* — is counted as a non-pass and lowers the score. Observation-valued
counterconditions are exactly this shape: `workloads/text.py:222-226` rewrites
a conjecturer's declared `eval: "observation"` into
`eval: "program:reasoning_observation_pending"`, whose program body
(`programs.py:306-307`) returns `OVERRUN, {"reason": "observation requires
registered evidence"}` unconditionally. Every falsifiable countercondition an
artifact declares therefore *subtracts* from its own coverage until evidence
arrives. With `hv` unmeasurable on v6 until `5f34e4d00` and `reach` empirically
zero, coverage was the only axis with any variance, so it alone decided the
frontier — and it decided it against the artifacts that made testable claims.

## Evidence

All three roots re-tabulated read-only (`Harness(root, read_only=True)`) with
the shipped `pareto_scores` / `capture.pareto.frontier`, script preserved at
`rescore.py` in this directory.

| root | survivors | Pareto frontier | frontier composition | dominated composition |
|---|---|---|---|---|
| P-S1 `9e48a36b1dec91ee` (`completed-epoch2-run-…`, branch `claude/deepreason-p-s1-commitments-wowcib`) | 98 | 58 | **58/58 answer a harness-minted `connection` problem** | **40/40 answer the operator's SEED question** |
| P-A1 `4565139800f5ca02` (branch `claude/live-reasoning-p-a1-bv65kl`) | 11 | 7 | **7/7 `connection`** | **4/4 SEED** |
| P-R1 poietics (`experiments/2026-08-25-poietics-program/run`, on main) | 58 | 40 | **40/40 `connection`** | **18/18 SEED** |

The split is total on all three roots: not one seed-answering artifact reached
the frontier, and not one harness-minted connection artifact was dominated.

- **The dominated artifacts pass strictly MORE checks than the winners.**
  Identical on all three roots: every SEED artifact scores 4 passes, every
  `connection` artifact 2. **Zero commitments FAIL anywhere on any of the three
  roots** (`fail=0`, 156 survivors total). Coverage therefore carries no
  quality signal at all in this record — its entire variance is the count of
  pending counterconditions:

      root   group        n    pass/artifact  fail  overrun/artifact
      P-S1   connection   58   2.00           0     0.00
      P-S1   seed         40   4.00           0     3.23
      P-A1   connection    7   2.00           0     0.00
      P-A1   seed          4   4.00           0     2.50
      P-R1   connection   40   2.00           0     0.00
      P-R1   seed         18   4.00           0     3.61

- **Every OVERRUN in all three roots has one reason.** `observation requires
  registered evidence` — 129 (P-S1), 10 (P-A1), 65 (P-R1); no other OVERRUN
  reason occurs. All are `program:reasoning_observation_pending`.

- **Worked example, P-A1 artifact `f3f96ed708a2…`** (answers the seed
  question; dominated). Its seven battery commitments:

      reasoning-envelope-wf          program:reasoning-envelope-wf        -> PASS
      pa1-limit-verdict@v1           predicate:...                        -> PASS
      pa1-obstruction-structure@v1   predicate:...                        -> PASS
      pa1-scaling-law@v1             predicate:...                        -> PASS
      reason-counter@f5606b1f6e3b9   program:reasoning_observation_pending -> OVERRUN
      reason-counter@da36ecdce2c76   program:reasoning_observation_pending -> OVERRUN
      reason-counter@496666cc21e1b   program:reasoning_observation_pending -> OVERRUN

  coverage = 4/7 = 0.5714, dominated by seven connection artifacts at 2/2 =
  1.0. **The harness minted a research problem for each of those same three
  pending counterconditions** — `frontier.txt` carries
  `research:reason-counter@f5606b1f6e3b94854219cb8f:f3f96ed708a2` and its two
  siblings. The run simultaneously recognised those counterconditions as worth
  gathering evidence for, and penalised the artifact on the ranking axis for
  having declared them.

- **`hv` and `reach` are absent, not merely low.** `len(state.hv) == 0` and
  `len(state.reach) == 0` on all three roots, so `state.hv.get(aid, 0.0)`
  returns 0.0 for every artifact and neither axis can break any tie. Coverage
  decided the frontier alone. (Corroborates MONITOR_REVIEW.md row F2 — "`hv`
  structurally unreachable on any v6 run — AGREE, verified in code".)

- **Every OTHER consumer of `programs.evaluate` already reads OVERRUN as
  "no verdict", never as a failure.** `pareto_scores` is the sole dissenter:

  | site | what it does with OVERRUN |
  |---|---|
  | `rules/act.py:15-17` | "OVERRUN (malformed spec) is a spec defect, not the candidate's fault: measure only." |
  | `rules/crit.py:893-897` | refuses the criticism — "produced no verdict — the proposed input grounds nothing" |
  | `rules/crit.py:1145-1147` | `QUARANTINE_TICK` and `continue` — the property is skipped, not counted as a violation |
  | `programs.py:314-322` (`_lean_external_check` docstring) | "an operational overrun, never a failed proof or a warrant" |
  | **`scheduler/scheduler.py:236-240`** | **counts it in the denominator as a non-pass — a penalty** |

- **Why the existing regression test never caught it — two spellings, only one
  protected.** `tests/test_formalism_optional_rank.py:64-66` builds its pending
  commitment as `Commitment(id="obs", eval="observation",
  observation_valued=True)`. `programs.evaluable` returns **False** for
  `eval="observation"` (`programs.py:533-537`: only `predicate:` and known
  `program:` kinds are evaluable), so that commitment is screened out of the
  battery, the battery is empty, and the existing `if battery:` guard omits
  coverage entirely — the protected road. But no live run ever produces that
  spelling: `workloads/text.py:224-226` rewrites every declared
  `eval: "observation"` to `eval: "program:reasoning_observation_pending"`,
  which **is** evaluable, enters the battery, and evaluates OVERRUN. Verified:

      evaluable(eval='observation')                        -> False
      evaluable(eval='program:reasoning_observation_pending') -> True

  The test pins a shape the harness rewrites away before any artifact carries
  it. That is why the guarantee is green in the gate and inverted in all three
  live roots.

## Implicated code

- `src/deepreason/scheduler/scheduler.py:225-241` — battery and coverage
  (the defect site)
- `src/deepreason/programs.py:306-307` — `_reasoning_observation_pending`
  returns OVERRUN unconditionally (correct as written; it is the *reader* that
  misreads it)
- `src/deepreason/workloads/text.py:222-226` — the rewrite that moves a
  declared observation onto the evaluable road

## Falsifiable prediction (what `dr-reproduce` must show)

On a fixed stub root built with the repo's own idiom, two artifacts identical
except that one carries three additional `program:reasoning_observation_pending`
commitments:

    python -m pytest tests/test_coverage_pending_commitments.py -q

must FAIL today at the equal-coverage assertion, reporting the declaring
artifact at coverage 2/5 = 0.4 against its sibling's 2/2 = 1.0, and the
declaring artifact absent from `run_report(...)["frontier"]`.

## Ruled out

**"The inversion is the spawn rules minting too many connection problems, not
the coverage axis."** Checked and rejected. The harness-minted problem
population is real (P-A1: 14 registered problems, 1 seed + 13 minted), but it
cannot explain the artifact frontier, because the frontier is computed over
SURVIVORS by score, not over problems: P-A1's seven frontier artifacts win on a
coverage coordinate of 1.0 against 0.57–0.67, and the counterfactual isolates
the axis — recomputing with pending commitments removed from the denominator
moves **every** dominated seed artifact onto the frontier on all three roots
(P-S1 58→98, P-A1 7→11, P-R1 40→58) with no other change. Problem-population
skew is a separate question and is PARKED, not fixed here.

## Correction to GOAL.md's Observed line (the record says something sharper)

GOAL.md cited "P-A1: 14 frontier members, 1 seed (7%), 13 harness-minted" from
MODULE_COVERAGE.md D1. That number is **not the Pareto artifact frontier**:
`frontier.txt` is the output of `deepreason --root … frontier`, whose handler
(`cli/main.py:998-1004`, help text "show the problem frontier") prints *every
registered problem*, unfiltered. It is the problem registry, so D1 measured the
problem population, not the ranking outcome.

This does not weaken the goal — it strengthens it. Measured properly, the
artifact frontier on P-A1 is **7 of 11 survivors, 0% seed-answering**, and the
same tabulation on P-S1 (58/98, 0% seed) and P-R1 (40/58, 0% seed) makes it
three roots with a total split rather than a percentage. The goal's success
criterion is unchanged and still the right one; only the Observed line's
citation is corrected. No re-bounding is required.
