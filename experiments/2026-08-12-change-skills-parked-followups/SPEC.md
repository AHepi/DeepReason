# Spec for: implement the parked skills-overhaul follow-ups
Traces: every item cites R/C numbers. Untraceable items are bugs.

## Items

S1 (R2): `.claude/skills/dr-ask-the-right-question/SKILL.md`. Before:
    line ~110 reads "the operator cannot be the blast-radius calculator
    for a 125,000-line codebase" as a standalone narrative clause
    (CENSUS.md `dr-ask-the-right-question-16`, flagged W5). After:
    trimmed to the operative rule with a bare parenthetical, matching
    the pattern applied to the 8 other W5 rows in
    `experiments/2026-08-12-change-skills-overhaul` (commit `4a389ce87`).
    accept: `git diff --stat .claude/skills/dr-ask-the-right-question/
    SKILL.md` shows a small (<=5 line) change confined to that one
    sentence; no other content in the file moves.

## Assumptions (operator may override)

A1: R1/R2's scope is exactly PARKED.md's P1 and P2 entries from the
    prior tranche — no other change. "Implement changes" (plural) is
    read as covering both parked items, not a request to invent new
    work; this is the smallest reading consistent with the verbatim
    message and the immediately-preceding delivery report (REQUEST.md's
    own "Reading" section).

## Questions for operator (STOP if non-empty — it is)

Q1 (R1, PARKED.md P1): give `dr-drive-harness`'s "never generalize
    instruction scope" rule a mechanical GATE, or accept it stays
    judgment-only with a recorded authoring-skills erratum? These are
    NOT close readings — one is new tooling (a lint-style check
    comparing an agent's stated scope against the files it actually
    touched: new code under `tools/`, a mutation-proof, a wiring point
    in `dr-drive-harness`/the gate table), the other is a single
    paragraph. >2x effort divergence, per `dr-ask-the-right-question`'s
    own "earns a question" bar — not decided here.

    Recommendation: accept judgment-only status, recorded as an
    authoring-skills erratum. Reason: this rule ("never generalize an
    instruction beyond its stated scope") is inherently about an
    agent's INTERPRETIVE judgment on ambiguous instructions — the same
    kind of judgment `dr-ask-the-right-question`'s own dominance test
    already exists to structure. A mechanical lint comparing "files
    touched" against "stated scope" would flag every DELTA edit this
    very skill-overhaul tranche made (each touched multiple files
    beyond the one literally named in a given CHECKLIST step) as a
    false positive, unless taught the same judgment it's meant to
    replace — a real design problem, not a quick build. The smaller,
    honest move is the erratum.

## Out of scope (explicit)

- Any change to `src/` or `tests/` (C2).
- Any PARKED.md entry other than P1/P2 (none exist for this prior
  tranche).
- Building new tooling under `tools/` unless the operator's answer to
  Q1 chooses that path.

## Frozen-surface contact forecast

    $ python tools/blast_radius.py --files
      .claude/skills/dr-ask-the-right-question/SKILL.md

    {"result_type": "BLAST_RADIUS_RESULT_V1", "targets": {"files":
    [".claude/skills/dr-ask-the-right-question/SKILL.md"], "symbols":
    []}, "base": null, "frozen_surface_contacts": [],
    "frozen_adjacent_contacts": [], "reachability": [], "consumers":
    {"tests": [], "map_checks": [], "qualification_digest": [],
    "wheel_smoke_pins": []}, "disclosure_summary": "This change touches
    none of the five frozen surfaces. 0 test file(s) and 0 map
    document(s) assert on the touched targets today.",
    "frozen_surface_verdict": "CLEAR"}

`frozen_surface_verdict: CLEAR`. No STOP required by this section (Q1's
STOP is independent, from the material-ambiguity rule, not frozen
surfaces).

## Blast-radius census

`consumers.tests: []`, `consumers.map_checks: []` — no test or map
document asserts on the one target file. No hits to classify.

## Budget

S1 (R2): ~3-5 lines, 1 commit. R1 (Q1) unbudgeted pending the
operator's answer — the two candidate resolutions differ by more than
an order of magnitude (one paragraph vs. new tooling), so no single
number would be honest here.

Frozen surfaces touched: none.

Rubric: 6/6 yes
- every R has a spec item with a machine-decidable accept, or is
  explicitly a Question: yes (R2 -> S1; R1 -> Q1)
- blast-radius census pasted and every hit classified: yes (empty,
  classified as such)
- frozen-surface contact forecast recorded (tool-pasted, verbatim): yes
- every mechanism the request names traced to code it actually
  reaches: yes (PARKED.md's own entries are the request's own naming)
- nothing untraceable to an R/C number: yes
- rubric pass performed as reviewer, not author: yes (this line)
