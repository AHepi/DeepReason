# Spec for: reduce operator steering (unstick guardrails)
Traces: every item cites R/C numbers.

## Items

S1 (R1): `deepreason-orchestrator` scope-contract item 1,
`dr-change-orchestrator` scope-contract item 2, `dr-deliver-change`
step 3 + template | before: a parked item is "one line"; the follow-up
prompt is authored later by whoever picks it up | after: the parked
entry carries its ready-to-send prompt, written at park time; delivery
lists the queue and recommends a next item.
    accept: grep "ready-to-send" in all three files → ≥1 hit each.

S2 (R2): `dr-plan-steps` CHECKLIST template, `dr-execute-step` step 6,
`dr-drive-harness` §1 | before: resuming a stuck session needs a
hand-written re-entry prompt reconstructing context | after: State:
line in the checklist header, refreshed every commit; drive-harness
states the one-line resume protocol.
    accept: grep "State:" dr-plan-steps + dr-execute-step → hits;
    grep "Resume tranche" dr-drive-harness → hit.

S3 (R3): `dr-execute-step` step 4 (two-failure stop),
`dr-change-orchestrator` stop conditions, `dr-drive-harness`
calibration paragraph | before: a stop may be an unstructured report
the operator must interrogate | after: every operator-facing stop
leads with the decision in one sentence, priced options, and a
recommendation.
    accept: grep -i "recommendation" in all three files → ≥1 hit each.

S4 (R4): `dr-drive-harness` new §5b | before: operational traps live
only in commit messages | after: a Process hygiene section, each rule
citing its paid-for incident.
    accept: grep "Process hygiene" dr-drive-harness → hit.

## Assumptions (operator may override)

A1: R3 applies to operator-facing stops; internal routing (validation
FAIL → re-plan) keeps its existing evidence-first format.
A2: the State: line lives in CHECKLIST.md (change workflow); defect
tranches are short enough that GOAL.md + latest artifact already carry
resume state — not duplicated there.

## Out of scope (explicit)

- The jargon-to-prose layer (C1 — operator's next project).
- Any driver/tooling automation of the queue (the Haiku-harness
  pre-plan owns that direction).
- Editing PARKED.md files of past tranches — the rule is forward-only.

## Frozen-surface contact forecast

none expected — checked against INV-frozen-surfaces.md; skill files
only.

## Blast-radius census

grep -rln "PARKED\|CHECKLIST" tests/ docs/map/ → no test or map check
asserts on skill-file content or PARKED/CHECKLIST formats (re-run this
session: zero hits). Nothing to classify.

## Budget

~55 lines across 6 skill files, 1 commit. Frozen surfaces touched:
none.

Rubric: 6/6 yes — every R has an item with a greppable accept; census
pasted-empty; contact forecast recorded; no named mechanism adopted
unverified (all four changes derive from this session's recorded
steering events, each named in the edits); not DESIGN-AND-STOP so M/O
sections not owed; nothing untraceable.
