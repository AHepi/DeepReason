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
3. Apply the code change. Comments state the constraint the code
   cannot show ("compare by handle index, not mapping order: canonical
   JSON sorts keys"), never the change's history or your reasoning.
4. **Run outward rings, stop at first failure:**

        pytest <regression test> -x -q
        pytest <the changed subsystem's test files> -q
        pytest tests/ -q -n 4          # full gate, ~8 min

   The full gate must report **0 failed**. A pre-existing failure you
   did not cause: stop, report, do not "fix it while you're there."
5. A gate failure caused by your change is information: if a fixture
   depended on the defective behavior (FIX.md predicted it), update
   the fixture minimally so it exercises what the test actually
   guards; if the failure is NOT predicted by FIX.md, your fix is
   wrong — revert to the last green state and return to the
   orchestrator for re-diagnosis. Never weaken an assertion to green.
6. If a live run root is needed for the next phase and the identity is
   occupied: retire the old root (`git mv run-<id>
   <failed|completed>-epochN-run-<id>`), commit the rename FIRST as
   its own commit, then proceed.
7. Commit once, push with retry:

        git add <exact files> && git commit -m "<what and why, with
          the live evidence and 'Full gate: N passed, 0 failed'>"
        git push -u origin <branch>   # retry x4, backoff 2s 4s 8s 16s

## Prohibitions

- No drive-by refactors, renames, TODO cleanups, or formatting churn.
- No new dependencies, no config default changes, unless FIX.md lists
  them as change sites.
- Never edit committed run roots; never commit `env` files.

## Exit criteria

- One pushed commit (plus at most one root-retirement commit).
- Full gate output pasted into the tranche log: N passed, 0 failed.
- Return to the orchestrator.
