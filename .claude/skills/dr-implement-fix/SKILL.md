---
name: dr-implement-fix
description: Apply an approved FIX.md to DeepReason with regression tests and the full gate. The only skill allowed to modify production code. Use after FIX.md passes its approval gate.
---

# Implement the fix

Input: an approved FIX.md. Output: one commit containing the fix, its
regression test, and any fixture updates FIX.md authorized — nothing
else.

## Procedure

1. **Touch only FIX.md's change sites.** If implementation reveals a
   needed site FIX.md missed, STOP: amend FIX.md first (one commit),
   then continue. Silent scope growth is the failure mode this
   workflow exists to prevent.
2. **Write the regression test first**, converting the REPRO artifact:
   it fails before your change, passes after. Its docstring names the
   live run/record that motivated it (e.g. "Regression (selfstudy
   run-9175f0ec): ..."), so the next reader can find the evidence.
   Build it to `dr-execute-step`'s "Durable tests, checks, and probes"
   rules — committed evidence only, meaning over form, mutation-proved,
   wall-clock scrubbed recursively, absence-tolerant — so it survives
   repo changes and fails only when the defect returns.
3. Apply the code change. Comments state the constraint the code
   cannot show ("compare by handle index, not mapping order: canonical
   JSON sorts keys"), never the change's history or your reasoning.
4. **Run outward rings, stop at first failure:**

        pytest <regression test> -x -q
        pytest <the changed subsystem's test files> -q
        pytest tests/ -q -n 4          # full gate, ~8 min

   The full gate must report **0 failed**. A pre-existing failure you
   did not cause: stop, report, do not "fix it while you're there."
   If FIX.md's change sites touch the packaging surface (pyproject
   entry points, CLI commands, MCP tools/schema, wheel layout), one
   more ring the gate does not run: `python scripts/wheel_smoke.py`,
   with its pinned expectations updated in this same commit.
5. A gate failure caused by your change is information: if a fixture
   depended on the defective behavior (FIX.md predicted it), update
   the fixture minimally so it exercises what the test actually
   guards; if the failure is NOT predicted by FIX.md, your fix is
   wrong — revert to the last green state and return to the
   orchestrator for re-diagnosis. Never weaken an assertion to green.
6. If a live run root is needed for the next phase and the identity is
   occupied: retire it — procedure canonical in `dr-drive-harness` §3
   (retire by rename, commit the rename FIRST as its own commit).
7. **Update the map in THIS commit** — see "Map obligations" below.
8. Before committing, run the mechanized budget gate against FIX.md's
   Estimated-diff ceiling — the same instrument `dr-execute-step` uses
   for Family-2 steps, so this check can no longer be an eyeballed
   `git diff --stat` compare:

        python tools/diff_budget.py <tranche-base> --ceiling <FIX.md's
          Estimated-diff ceiling> --paths <FIX.md's change sites>

   Read `DIFF_BUDGET_RESULT_V1.verdict`. `WITHIN`/`NO_CEILING`:
   continue. `EXCEEDED` is a STOP in the standard format (decision,
   priced options, recommendation), not a footnote — the by-eye
   version of this check missed an over-budget diff before this gate
   existed (V1 tranche 2026-08-05: 193 insertions landed against a
   <=150 ceiling with no stop). Then commit once, push with retry:

        git add <exact files> <map files> && git commit -m "<what and
          why, with the live evidence and 'Full gate: N passed, 0
          failed'>"
        git push -u origin <branch>   # retry x4, backoff 2s 4s 8s 16s

## Map obligations (docs/map/)

Same procedure `dr-execute-step` uses for Family-2 steps (same commit
not a follow-up; SEAM before subsystem docs; new invariant needs a new
check; advance `Verified-at:` only if re-run; `docs_verify` full +
`--audit` must pass before commit) — canonical there, not restated here.
One Family-1-specific addition: **every fix earns a `Traps` entry** in
the `SUB-`/`CON-`/`SEAM-` document covering the changed code. A defect
that reached the record is exactly the memory the map exists to keep.
Name the run id or the tranche. Never delete an old Traps entry —
rewrite it to say it was fixed and when.

## Prohibitions

- No drive-by refactors, renames, TODO cleanups, or formatting churn.
- No new dependencies, no config default changes, unless FIX.md lists
  them as change sites.
- Never edit committed run roots; never commit `env` files — both
  procedures canonical in `dr-drive-harness` §1/§3.

## Exit criteria

- One pushed commit (plus at most one root-retirement commit).
- Full gate output pasted into the tranche log: N passed, 0 failed.
- `python tools/docs_verify.py` passes, and the map documents covering
  the changed code carry a Traps entry for this defect.
- Return to the orchestrator.
