# PARKED — noticed in this tranche, deliberately not done here

## P1 — the patch prompt never shows the model what a patch looks like

**What:** `llm/repair.py::patch_repair_prompt` names the schema
("Return exactly one repair.patch.v1 JSON object") and hands over the envelope,
but shows no worked example. Six of the 13 recorded epoch-1 responses wrapped
the patch under the schema name or a container key, and two spelled the pointer
field `pointer`. This tranche absorbed those spellings; it did not reduce how
often they are emitted. A one-line example costs a few prompt tokens per repair
turn and might remove the class at the source.

Not done here because it changes the rendered prompt, and this tranche's fix
was scoped to touch no prompt, digest or run identity.

```
Route: dr-change-orchestrator (operator-suggested change, not a defect --
the harness is correct as it stands; this is a generation-side improvement).

One goal: decide from live evidence whether adding a worked example to
patch_repair_prompt reduces the rate of unreadable patch responses, and if so
land the smallest prompt change that does it.

Evidence, already committed:
  - experiments/2026-08-22-fix-repair-patch-transport/repair-turn-census.json
    -- 13 dispatched repair turns of run-40e713b30a147dfc, with the recorded
    response shape of each. Six needed transport tolerance to be read at all.
  - experiments/2026-08-22-fix-repair-patch-transport/repair_turn_census.py
    -- re-derives that table over any root:  python repair_turn_census.py <root>
  - src/deepreason/llm/repair.py::patch_repair_prompt -- the prompt as it
    stands, and repair_patch_response_schema, which already narrows the
    provider's "path" field to an enum of exactly the authorized pointers.

Read first: CLAUDE.md "Tokens are cheap; the agent is not" -- this question is
answered by running repair turns, not by reasoning about prompts. A pair of
live runs on the same question with and without the example, censused by
repair_turn_census.py, is the evidence; a hand-argued prompt is not.

Constraint: a prompt change moves the rendered request and therefore the prompt
digest of every repair turn. It does NOT move run identity or the qualification
subject (those are fixed before dispatch), but confirm that against
CON-run-identity.md before landing rather than assuming it.

End state: either a landed prompt change with a censused before/after rate, or
a recorded negative result saying the example did not move the rate.
```

## P2 — `experiments/2026-08-22-live-reach-rich-run/repair_census.py` still
## reads the post-hoc `diagnostic_ref`

**What:** the script that produced the falsified P7-reach reading is still in
the tree and still scores responses against the diagnostic derived after them
(`DIAGNOSIS.md` Finding 0, `docs/ERRATA.md` E42). It is a prior tranche's
committed artifact, so this tranche superseded it with
`repair_turn_census.py` here rather than editing it, and recorded the
correction in ERRATA. Anyone re-running the old script will reproduce the wrong
answer.

Not done here because editing another tranche's committed evidence script is
outside this goal, and the correction is already ledgered where a reader looks.

```
Route: dr-change-orchestrator (housekeeping change).

One goal: make experiments/2026-08-22-live-reach-rich-run/repair_census.py
either read the frozen dispatched authority (the work preparation's
repair.semantic-task.v1 payload) or carry a header pointing at its superseding
script, so it cannot silently produce the falsified reading again.

Evidence, already committed:
  - docs/ERRATA.md E42 -- the full correction and why the join was wrong.
  - experiments/2026-08-22-fix-repair-patch-transport/repair_turn_census.py
    -- the corrected join, already written and run.

Constraint: experiments/2026-08-22-live-reach-rich-run/PARKED.md P7-reach is a
committed finding. Do not rewrite it to say something else; ERRATA is the
mechanism for correcting a committed document, and E42 already carries it.

End state: the old script cannot be run into the wrong answer without seeing
the correction.
```
