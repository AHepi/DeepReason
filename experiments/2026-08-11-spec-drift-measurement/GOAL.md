# Goal: measure how much of main's current public surface the harness-spec series (v1.3 base + v1.4/v1.5/v1.6 amendments) never mentions

Class: capability-gap (the spec documents are not wrong about anything they
say — they are silent about surfaces added after they were written; this
is a coverage gap, not a contradicted guarantee)

Observed: eight named terms drawn from the operator's own program
handover (seats, seat-bindings.v1, conjecturer.turn.v7,
candidate_checker, LEGACY_CRITICISM_ENABLED, school seats, blind
same-model judges, config referee) are all real, current concepts
somewhere in main's src/ or docs/map/ today, per direct grep, but a
case-insensitive grep of all eight terms across the four spec files
(docs/harness-spec-v1.3.md, -v1.4-amendment.md, -v1.5-amendment.md,
-v1.6-amendment.md) returns zero matches for seven of the eight, and
only three incidental (non-defining) uses of the word "seats" in v1.5.

Success criterion (machine-decidable):
    for f in docs/harness-spec-v1.3.md docs/harness-spec-v1.4-amendment.md \
             docs/harness-spec-v1.5-amendment.md docs/harness-spec-v1.6-amendment.md; do
      for term in "seat-bindings.v1" "conjecturer.turn.v7" "candidate_checker" \
                  "LEGACY_CRITICISM_ENABLED" "school seat" "blind same-model" \
                  "config referee"; do
        grep -ic -- "$term" "$f"
      done
    done
    Expected (already measured this tranche): all zero except "seats"
    (loose word, 3 incidental hits in v1.5, not a defined-term match).

In scope: docs/harness-spec-v1.3.md, docs/harness-spec-v1.4-amendment.md,
docs/harness-spec-v1.5-amendment.md, docs/harness-spec-v1.6-amendment.md
(read-only measurement); cross-checking each drift term against
src/deepreason/ and docs/map/ to confirm it is real (not a typo in the
task handover) and whether it exists on main today vs. only on the
unmerged claude/adjudication-judge-seats-optins-4nb7ov branch.
NOT in scope: drafting the v1.7 amendment itself (explicit STOP point —
the operator's own words: "The Spec needs updating, but carefully");
docs/ organization more broadly (Item 6, folded into this tranche's STOP
as a second question, not this GOAL's measurement).

Budget: 0 changed lines to src/ or docs/harness-spec-*.md (measurement
only, no edits to spec text this tranche); 1 commit for the drift-table
report; ~30 minutes.
Stop conditions inherited from orchestrator: yes — this tranche ends at
a STOP for operator words per the task handover's explicit instruction,
not at a fix.
