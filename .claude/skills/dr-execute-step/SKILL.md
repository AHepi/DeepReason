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
   failures of the same step = stop condition, in the standard format
   — canonical in `dr-drive-harness` §6's calibration note.
5. **If this step changed behaviour, update the map in the SAME
   commit** — see "Map obligations" below. If it changed the packaging
   surface (pyproject entry points, CLI commands, MCP tools/schema,
   wheel layout), update `scripts/wheel_smoke.py`'s pinned expectations
   and re-run the smoke in the same commit too — no gate runs it for
   you.
6. Mark the box, update CHECKLIST.md — including its header State:
   line (next step, blockers), which is what a fresh session resumes
   from — and if the step is tagged [COMMIT] (or changed any file):
   `git add` this step's files, then run `python tools/diff_budget.py
   <tranche-base> --ceiling <SPEC.md's ceiling> --paths <SPEC.md's
   declared areas>` and read its `DIFF_BUDGET_RESULT_V1.verdict`.
   WITHIN/NO_CEILING: continue. EXCEEDED is a STOP in the standard
   format (decision, priced options, recommendation), not a footnote
   (recorded miss: 193 insertions landed against a ≤150 ceiling with
   no stop, V1 tranche 2026-08-05). Alongside it, run
   `python tools/blast_radius.py --files <this step's actually
   git-added files> --symbols <this step's actually touched top-level
   defs, from the diff hunks> --against <tranche-base>` (Rung G6,
   `docs/map/INV-frozen-surfaces.md`) and diff its
   `frozen_surface_contacts`/`reachability` output against THIS
   document's own Frozen-surface contact forecast and Blast-radius
   census sections in SPEC.md. Any `frozen_surface_contacts` entry not
   already named in SPEC.md, or any `reachability` entry whose
   `direction` is `newly_dead`/`newly_live` and was not predicted, is
   DRIFT — a STOP in the exact same format as `diff_budget.py`'s own
   EXCEEDED, never a footnote (this is the 2026-08-09 incident's own
   fix, mechanized: `docs/ERRATA_EXECUTOR.md`'s "the frozen-surface stop
   did not hold" happened at exactly this commit-time gap, before this
   checkpoint existed). No drift: continue. Then commit and push now.

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

## Durable tests, checks, and probes

Anything you add here must survive dramatic repo changes — refactors,
renames, reformats — failing only when the CLAIM it guards stops being
true. Five rules, each paid for once already:

1. **Pin to committed, immutable evidence.** A test or check may open
   only roots and fixtures that `git ls-files` knows; regression tests
   name their motivating run in the docstring. Session-local artifacts
   die with the session and take the check's meaning with them
   (docs/ERRATA.md E7: four checks pinned to never-committed roots
   passed on one machine and failed on every fresh clone).
2. **Anchor to meaning, not form.** Prefer behavior (call the function,
   compare typed outcomes), structure (AST shape, resolved-call counts),
   or counts over literal source text. When a textual marker is
   unavoidable, choose the minimal substring invariant across the
   refactors you can foresee — rung 3 shortened a boundary marker from
   `assigned = schools.allocate(` to `assigned = schools` so it matched
   both sides of its own migration; two other form-brittle checks broke
   on legitimate reformatting and had to be replaced mid-tranche. Never
   pin line numbers.
3. **Mutation-prove it can fail, before writing it down.** Break the
   guarded thing, watch the test/check/probe go red, restore. For
   equality tests, keep a permanent companion mutation test in the
   suite (rung 3's determinism test ships with a reversed-allocation
   backend that must always fail the comparison). `docs_verify --audit`
   catches vacuous checks; nothing catches a vacuous test but this rule.
4. **Compare typed outcomes, and exclude wall-clock RECURSIVELY.**
   Equality over applied state and event logs, with time-dependent
   fields scrubbed at every nesting depth — a top-level-only scrub left
   `llm.ms` inside `attempt_trace` and a 1-in-3 flake (commit
   `863a0fa3`). Diagnose flakes to the exact field; never widen an
   exclusion on a guess.
5. **Tolerate absence in old records.** Any test or sweep probe reading
   the typed record must accept every existing committed root, which
   predates your feature — assert the attribute exists before reading
   it, and treat absence as valid, never as failure (the sweep's probe
   rule; the rung-4 reader-before-writer guardrail).

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
