---
name: dr-execute-step
description: Execute exactly one unchecked step from CHECKLIST.md, prove its done-criterion, record the output, and stop. The only skill in the change workflow allowed to modify the tree. Invoke repeatedly, once per step.
---

# Execute one step

Input: CHECKLIST.md. Output: one more checked step with its
done-criterion output pasted beneath it. You do this for ONE step,
then return. The loop lives in the orchestrator, not in you — that is
what keeps a long change from drifting.

## Procedure

1. Re-read REQUEST.md (including Amendments) and CHECKLIST.md in
   full. Find the FIRST unchecked step. That is your entire job. Do
   not read ahead "to be efficient"; do not batch steps.
2. Confirm the step still makes sense against the tree (a prior step
   may have failed silently). If the tree contradicts the step —
   file missing, test already passing, root identity occupied — do
   not improvise: record the contradiction under the step, commit,
   and return to the orchestrator (route: dr-plan-steps).
3. Execute the action. Only files this step's spec item names may
   change. Mid-step discoveries ("this file also needs...") go to
   PARKED.md or, if the change cannot land without them, back through
   dr-spec-change as an amendment — never just typed in.
4. Run the done-criterion command. Paste its real output (trimmed to
   the relevant lines) under the step. If it does not match expected:
   the step is NOT done — leave it unchecked, record the output and
   one line on the mismatch, and return to the orchestrator. Two
   failures of the same step = stop condition.
5. **If this step changed behaviour, update the map in the SAME
   commit** — see "Map obligations" below.
6. Mark the box, update CHECKLIST.md, and if the step is tagged
   [COMMIT] (or changed any file): commit and push now.

        git add <files this step touched> <map files> <tranche-dir>
        git commit -m "step <n>: <checklist line>"
        git push -u origin <branch>   # retry x4, backoff 2s 4s 8s 16s

## Map obligations (docs/map/)

The map is part of the change, not a chore after it.

- A step that changes what a caller may do, what a guard admits, or
  where a rule is enforced, updates the covering `SUB-`/`CON-`/`SEAM-`
  document **in the same commit**.
- A step that changes an interaction updates the `SEAM-` document
  before the subsystem ones — the seam is what the next reader opens
  first, and a correct pair of subsystem docs with a stale seam between
  them is worse than either being stale alone. The file is
  `docs/map/SEAM-<a>-x-<b>.md` (sides alphabetical); how to change one
  is `docs/map/REC-change-a-seam.md`; how to write one is
  `docs/map/SCHEMA.md`.
- New behaviour needs a new check at column 0 that would fail if the
  behaviour regressed. Run it before you write it down.
- Advance `Verified-at:` only if you re-ran that document's checks.
- `python tools/docs_verify.py` must pass before you commit; a failure
  is a failed step, exactly like a failed test.
- A step that only writes tests or records evidence changes no map
  document. Do not touch stamps you did not verify.

## Style discipline for code steps

- Match the surrounding code's idiom, naming, and comment density.
- Comments state constraints the code cannot show, never narrate the
  change ("why this must hold", not "changed X to Y").
- Test docstrings name the motivating requirement or record
  ("Implements R3: ..." / "Regression (run-<id>): ...").
- Never weaken an existing assertion to make a step pass; that is a
  failed step, not a passed one.

## Exit criteria

- Exactly one more step checked, with pasted proof; tranche dir
  committed and pushed.
- OR the step failed / contradicted the tree: recorded, unchecked,
  reported back for re-planning.
- Return to the orchestrator either way.
