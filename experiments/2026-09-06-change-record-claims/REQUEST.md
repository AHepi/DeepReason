# Request: "what about now?" — adopt h-EPI's claims mechanism for DeepReason's measures
Captured: 2026-09-06, from the executor brief that carries the operator's
verbatim words (the operator pointed the monitor at their other repository
and asked what it offers now, then corrected the monitor's reading of one of
its rules).

## Verbatim

The operator, four messages, in order, as relayed in the executor brief:

> https://github.com/AHepi/h-EPI
> what about now?
> Actually that ruling was old. Does this next prompt take that into account?
> no the rule from the other harness

Standing operator law quoted by the brief and binding here (CLAUDE.md,
2026-08-28, the ungated-seats law), in the operator's own words:

> My intention was that configuration of seats need to be able to turn gates
> on and off at will. Meaning no limits to what model you place where. It also
> means that when and if I decide to replace schools with something different,
> those flags don't gate seat configuration paths. Gates are always optional:
> with warnings.

## The monitor's reading, stated here as the interpretation (not the operator's words)

The brief instructs that this reading be stated in REQUEST.md as the
interpretation of the four messages above:

- Adopt h-EPI's CLAIMS mechanism for DeepReason's measures.
- Do NOT adopt h-EPI's rule that a model's criticism must be marked ready by
  a person before it can defeat anything. The operator has said that rule is
  old ("Actually that ruling was old", "no the rule from the other harness").
- In DeepReason, whether criticism carries authority is the harness's to
  decide by its own rules, judges and configuration (the ungated-seats law,
  2026-08-28), with no person in the loop. Nothing in this tranche may assume
  otherwise or build a human-readiness step.

## Requirements

R1 (artifact): Clone the operator's repository READ-ONLY beside this one
  (`git clone https://github.com/AHepi/h-EPI /home/user/h-epi`); record its
  head commit; never modify or vendor it.

R2 (process): Read, in the clone, `docs/how-it-works.md` §"Conjectures,
  tested by the records", `src/creib/forge/conformance/claims.py`,
  `forge/conformance/schema/conformance-claims.schema.json`,
  `forge/conformance/pilots/travel-claim/claims.json`, and
  `docs/what-the-records-refute.md` (the standing column and its H21
  paragraph).

R3 (behavior): Take the SHAPE, not the code. "a claim is a universal
  `never`/`always` statement with a declared scope and a condition; one
  record refutes it; a survival is 'UNREFUTED_FOR_DECLARED_SCOPE' and carries
  a STANDING that says whether its refuting condition held on any supplied
  record at all ('not shown able to fail' when it never did)".

R4 (artifact): `tools/record_claims.py`, "a read-only tool over one or more
  DeepReason run roots (`log.jsonl`, `objects/`, `run-status.json`, and the
  typed measures the record already carries — citation checks, seat
  retirements, transport faults, budget denials, judge verdicts, criticism
  dispatch declarations)".

R5 (behavior): The tool takes "a claims file and print[s] every claim's
  status, the refuting record ids (at most five), and the standing".

R6 (artifact): `docs/CLAIMS_SCHEMA.md` "describing the claims file".

R7 (artifact): A first claims file
  `experiments/2026-09-06-change-writers-room-organiser-testing/claims.json`
  "that re-states that tranche's PREREG predictions as claims (at least: the
  organiser never cites an id outside the legend; every seat's section plan
  names its directive; a run never stops `operational_failure`; the critic
  never exhausts its smallest contract; every countercondition registered
  came from a room proposal)".

R8 (behavior): That claims file "is run against the FAILED root
  `runs/home-r/runs/run-36d9a22c3e2045ae1b8c7bfb9d95d092` (or its retired
  name if the re-launch window has renamed it — read the tree) so the output
  shows real refutations".

R9 (behavior): "Conditions are expressed over the record's own typed fields
  (event kinds, measure codes, status values, seat ids)".

R10 (process): "read `docs/map/INDEX.md` → `SUB-harness.md` /
  `CON-evidence-states.md` / `INV-evidence-channels.md` for the record's
  vocabulary and cite the documents in SPEC.md".

R11 (behavior): "The 'not shown able to fail' standing is REQUIRED: a claim
  whose condition never occurred on the supplied roots must print as such."

R12 (artifact): "Prove the tool with tests under
  `tests/test_record_claims.py`: a synthetic root that refutes each claim
  kind, one that survives, one where the standing fires."

R13 (behavior): "No claim in this tranche is about correctness of any answer;
  every claim is about what the record shows a seat or the harness DID."

R14 (behavior): "Not a gate, not a status, not a score: the tool writes
  nothing into any root and changes no status; its output is an instrument
  for RESULTS.md."

R15 (behavior): "Not h-EPI's appraisal layer: that module labels arguments
  in/out/undecided by a fixed-point rule AND takes each argument's readiness
  from a person; only the labelling rule is of interest here."

R16 (artifact): "Park it with a ready prompt that points the parked
  premise-declaration fork
  (`experiments/2026-09-05-criticism-premise-declaration/PARKED.md`, the
  UNDECIDED-premise-still-refutes question) at
  `src/creib/forge/conformance/appraisal.py` for the labelling rule alone
  ('undecided underneath means contested'), and that says in its first line
  that readiness in DeepReason is read from the record — warrant checks,
  judge verdicts, criticism dispatch — never marked by a person."

R17 (behavior): "Not a change to any PREREG already sealed."

R18 (process): "`src/deepreason/` byte-untouched (a tool under `tools/`,
  tests, docs, one claims file)".

R19 (process): "no frozen surface (say so after checking
  `docs/map/INV-frozen-surfaces.md`)".

R20 (process): "park, never fix, anything found".

R21 (artifact): "Map: add the tool to the map document that owns `tools/`
  instruments with a `check:` that runs it on a committed root and exits 0,
  in the same commit."

R22 (process): "Ring while iterating; the full gate ONCE at the boundary
  (tests/ changed)."

R23 (process): "Deliver through `dr-validate-change` and `dr-deliver-change`
  with the R-by-R table."

R24 (process): "Commit and push at every phase boundary with retry
  (2s/4s/8s/16s). Stop when delivered and pushed."

R25 (behavior): Do not build a human-readiness step anywhere. Whether
  criticism carries authority is the harness's own decision, read from the
  record. (From the operator's "Actually that ruling was old" / "no the rule
  from the other harness", as interpreted above.)

## Standing constraints

C1: "Never verify a review without the operator's explicit permission."
  — CLAUDE.md MANDATORY block, operator verbatim 2026-09-05. This tranche is
  a CHANGE, not a review, so its own gate and checks are the change
  workflow's, not a review's.

C2: "Route through `dr-change-orchestrator` starting with
  `dr-capture-request`." — the brief.

C3: "Read CLAUDE.md from this checkout in full (every operator design law
  binds; the MANDATORY block at the top binds you), read
  `.claude/skills/pinker-write-for-readers/SKILL.md` directly with the Read
  tool and follow it for every message, and read `.claude/skills/README.md`."
  — the brief. NOTE: `.claude/skills/README.md` DOES NOT EXIST in this
  checkout (`ls .claude/skills/` lists 26 skill directories and no README).
  Recorded here rather than silently skipped.

C4: "Gates are always optional: with warnings." — CLAUDE.md, operator
  verbatim 2026-08-28. Binds R14 and R25: this tool is not a gate.

C5: "a complete answer isn't the goal. Neither is correctness." — CLAUDE.md,
  operator verbatim 2026-09-03. Binds R13.

C6: "Prompts written for the operator to paste into executor windows are
  delivered inline in the chat reply as ONE fenced code block" — CLAUDE.md
  Conventions, operator request 2026-08-11. Binds R16's parked prompt.

## Open questions (for dr-spec-change)

Q1: Which typed measures does the record actually carry under the names the
  brief lists (citation checks, seat retirements, transport faults, budget
  denials, judge verdicts, criticism dispatch declarations)? The brief names
  them; the record's own vocabulary decides the condition keys. Answer from
  the record and the map (R9, R10), not from the operator.

Q2: The brief names a claim "every seat's section plan names its directive".
  The section-plan record kind is `workflow-context-section-plan-v1`
  (DR-INV-frozen-surfaces, granted contact 2026-09-04). Whether every seat's
  plan carries a directive section, or only the organiser's, is a fact of the
  record to be read, not a design choice.

Q3: Does `experiments/2026-09-06-change-writers-room-organiser-testing/` own
  a `claims.json` slot without disturbing its sealed PREREG.md (R17)? The
  claims file re-states predictions; it must not be presented as an amendment
  to the sealed document.

Q4: `.claude/skills/README.md` does not exist (C3). Nothing in the brief
  depends on it; recorded, not asked.

## Amendments

(append-only; later operator messages land here as R26... or "R2a supersedes
R2", each with its verbatim quote)

**Amendment 1 (2026-09-06, mid-turn — the brief was re-sent with two more
operator messages and one added prohibition).** The first brief carried two
operator messages ("https://github.com/AHepi/h-EPI", "what about now?") and
described the parked appraisal layer as "the appraisal layer (readings under
criticism)". The re-sent brief adds the operator's third and fourth messages
verbatim ("Actually that ruling was old. Does this next prompt take that into
account?", "no the rule from the other harness"), adds R25's prohibition, and
sharpens R15/R16. This document is written against the RE-SENT brief; the
requirement numbers above are the re-sent brief's. Nothing was acted on under
the first reading before this amendment was written.
