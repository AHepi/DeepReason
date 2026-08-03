# Request: rung 2 — buried choices become visible switches (tranche 1: inventory)
Captured: 2026-08-03 from the operator's continuation-session opening
message (authorizing rung 2) and `docs/HANDOVER_2026-08-03.md`'s rung 2
section, which the operator's message explicitly instructs be quoted
verbatim here.

This ledger covers BOTH of rung 2's tranches' authorizing words, so a
later tranche-2 (the switch) can cite it without re-capturing. This
invocation's SPEC/CHECKLIST/execution address ONLY the inventory
requirements (R1-R4 below); the switch requirements (R5-R8) are marked
`deferred (operator's own tranche split)` and belong to a separate,
later tranche directory.

## Verbatim

> You are the executor continuing the DeepReason modularisation program.
> Rung 1 is delivered and accepted. Your task is RUNG 2 ONLY, and this
> message is the operator authorization to begin it.
>
> SETUP, in order:
> 1. Preflight per .claude/skills/dr-drive-harness/SKILL.md (the container
>    rolls back silently: resync the branch, then reinstall
>    `pip install -e . --break-system-packages` PLUS pytest, pytest-xdist,
>    and jsonschema — a bare install does not restore them).
> 2. Work on branch claude/delivery-rungs-handover-m22sdy. FIRST, merge
>    origin/claude/handover-defect-audit-33pv3d into it and push the merge.
>    This brings docs/ERRATA_EXECUTOR.md (entries X1–X4, about YOUR previous
>    session) and the handover's feed-instruction into your checkout. From
>    now on that instruction applies to you: append an entry to
>    docs/ERRATA_EXECUTOR.md whenever the handover or skills mislead you,
>    are silent where you needed them to speak, or a guardrail fires as
>    designed — evidence pointers only.
> 3. Read, in order: CLAUDE.md; .claude/skills/dr-drive-harness/SKILL.md
>    including its calibration block; .claude/skills/README.md;
>    docs/ERRATA.md (E1–E9); docs/ERRATA_EXECUTOR.md;
>    docs/HANDOVER_2026-08-03.md in full; and the rung-1 tranche's
>    DELIVERY.md and PARKED.md
>    (experiments/2026-08-03-change-rung1-sockets-on-paper/).
>
> THE TASK — rung 2 of the handover, exactly as written there:
> - Route: dr-change-orchestrator. Quote the handover's rung-2 section AND
>   this message verbatim in REQUEST.md.
> - TRANCHE 1 — inventory only. Gather the hard-coded behavior choices that
>   could become named Config values (config.py is the sanctioned home, per
>   DR-INV-frozen-surfaces "Where authority is allowed to live instead").
>   Deliverable: the inventory document, with a map/code pointer and current
>   hard-coded value for each candidate. Zero src/ changes in this tranche.
> - TRANCHE 2 — one switch: engaged_criticism_policy in v6_policy.py
>   (hard-coded observe_only) becomes a Config value PRESERVING observe_only
>   as the default. Creating the switch is in scope. FLIPPING ANY DEFAULT IS
>   THE OPERATOR'S DECISION, NEVER YOURS.
> - THEN STOP. Present the inventory; further switches wait for the operator
>   to pick them. Do not start rung 3 or any other rung.
>
> ACCEPTANCE per switch tranche: full gate `python -m pytest tests/ -q -n 4`
> 0 failed (never bare pytest); root sweep `python tools/root_sweep.py`
> byte-identical before/after (42 rows, 11 ERROR expected — see ERRATA
> E5/E6/E8 before interpreting it); a test proving the switch's default
> equals prior behavior; map updated in the SAME commit as the code.
>
> CONSTRAINTS: frozen surfaces bind everything
> (docs/map/INV-frozen-surfaces.md). One rung per tranche; never let a
> tranche touch two rungs. Known flake:
> test_grounded_counterexample_recovery_does_not_invent_override_on_repeat
> can fail once under -n 4; rerun before diagnosing. Commit and push at
> every phase boundary. PARKED.md holds everything noticed but not done.
> Stop conditions are hard stops. Where a spec is silent, load
> dr-ask-the-right-question and route the question to the cheapest
> authority — do not improvise.
>
> — operator's continuation-session opening message

> ### Rung 2 — buried choices become visible switches  [EXECUTE]
> Route: `dr-change-orchestrator`, one switch per tranche.
> Goal: gather hard-coded behavior choices into named `Config` values
> (`config.py` is the sanctioned home — `DR-INV-frozen-surfaces`, "Where
> authority is allowed to live instead"), each PRESERVING the current
> default so no behavior changes. Inventory first (one tranche), then one
> switch per tranche. The known first candidate:
> `engaged_criticism_policy` authority in `v6_policy.py` (hard-coded
> observe_only) — NOTE: creating the switch with the current default is
> EXECUTE; flipping any default is the operator's decision, never yours.
> Accept per switch: full gate 0 failed; root sweep byte-identical; the
> switch's default proven equal to prior behavior by a test.
>
> — `docs/HANDOVER_2026-08-03.md`, "The program: seven rungs, in order"

## Requirements — Tranche 1 (this invocation)

R1 (artifact): "TRANCHE 1 — inventory only. Gather the hard-coded behavior
choices that could become named Config values (config.py is the sanctioned
home, per DR-INV-frozen-surfaces 'Where authority is allowed to live
instead')."

R2 (artifact): "Deliverable: the inventory document, with a map/code
pointer and current hard-coded value for each candidate."

R3 (process): "Zero src/ changes in this tranche."

R4 (process): "THEN STOP. Present the inventory; further switches wait for
the operator to pick them. Do not start rung 3 or any other rung."

## Requirements — Tranche 2 (deferred, separate tranche directory)

R5 (behavior, deferred): "one switch: engaged_criticism_policy in
v6_policy.py (hard-coded observe_only) becomes a Config value PRESERVING
observe_only as the default. Creating the switch is in scope."

R6 (process, deferred): "FLIPPING ANY DEFAULT IS THE OPERATOR'S DECISION,
NEVER YOURS."

R7 (process, deferred): "ACCEPTANCE per switch tranche: full gate `python
-m pytest tests/ -q -n 4` 0 failed (never bare pytest); root sweep `python
tools/root_sweep.py` byte-identical before/after (42 rows, 11 ERROR
expected); a test proving the switch's default equals prior behavior; map
updated in the SAME commit as the code."

R8 (process, deferred): "Route: `dr-change-orchestrator`, one switch per
tranche" (rung 2's own route line — governs tranche 2's workflow, not
tranche 1's).

## Standing constraints

C1: "Preflight per .claude/skills/dr-drive-harness/SKILL.md (the container
rolls back silently: resync the branch, then reinstall `pip install -e .
--break-system-packages` PLUS pytest, pytest-xdist, and jsonschema)" —
operator's opening message. DONE this session before REQUEST.md was
written: branch resynced (no rollback detected, head already at
`f0e9af30`), deps reinstalled and confirmed importable.

C2: "Work on branch claude/delivery-rungs-handover-m22sdy. FIRST, merge
origin/claude/handover-defect-audit-33pv3d into it and push the merge" —
operator's opening message. DONE this session: merge commit `b73db3ba`,
pushed, `docs_verify --fast` 0 failed post-merge.

C3: "From now on that instruction applies to you: append an entry to
docs/ERRATA_EXECUTOR.md whenever the handover or skills mislead you, are
silent where you needed them to speak, or a guardrail fires as designed —
evidence pointers only" — operator's opening message, quoting
`docs/HANDOVER_2026-08-03.md`'s "Feed the executor errata" bullet. Binding
on this and all future tranches in this session.

C4: "frozen surfaces bind everything (docs/map/INV-frozen-surfaces.md)" —
operator's opening message.

C5: "One rung per tranche; never let a tranche touch two rungs." —
operator's opening message, echoing the handover's own "Executor
calibration."

C6: "Known flake:
test_grounded_counterexample_recovery_does_not_invent_override_on_repeat
can fail once under -n 4 — rerun before diagnosing." — operator's opening
message.

C7: "Commit and push at every phase boundary." — operator's opening
message.

C8: "Where a spec is silent, load dr-ask-the-right-question and route the
question to the cheapest authority — do not improvise." — operator's
opening message.

## Open questions (for dr-spec-change)

Q1: "hard-coded behavior choices that could become named Config values" —
the words do not bound the search: which packages/files count as in
scope for the inventory sweep? The whole `src/deepreason/` tree, or only
files already touched/mapped by rung 1's sockets (schools, conjecture
source, criticism source, scheduler ranking, authority)?

Q2: R1 references `DR-INV-frozen-surfaces`'s "Where authority is allowed
to live instead" section specifically — does this mean the inventory is
SCOPED to authority-shaped choices only (mirroring the one named example,
`engaged_criticism_policy`'s authority), or to hard-coded behavior choices
generally (of which authority is only the illustrative first example)?

Q3: R2 says "a map/code pointer and current hard-coded value for each
candidate" — no explicit format (table? list? one doc per candidate?) or
minimum/maximum count is specified.

## Amendments

(none yet)
