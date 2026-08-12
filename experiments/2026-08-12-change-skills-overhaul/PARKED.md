# Parked (not done, not promised)

Per this tranche's own scope contract (`dr-change-orchestrator`'s
"Scope contract" item 2 and `authoring-skills`): anything noticed but
not requested goes here, ready for a future runner to paste and go —
never fixed in passing.

## P1 — `dr-drive-harness`'s "never generalize scope" negation has no
enforcing GATE

**What:** DESIGN.md's gate table (`experiments/2026-08-12-change-
skills-overhaul/DESIGN.md`, "Gate table" section) found that
`dr-drive-harness`'s calibration-block rule — "Never generalize an
instruction beyond its stated scope; if a spec seems silent about your
case, that is a question... not an invitation to infer" — is the one
authoring-skills W3 case (a "never" with no independently mechanized
trigger) this tranche's Phase C could not close. Building a NEW gate
for it was out of scope for this tranche (REQUEST.md authorized
applying DELTAs from CENSUS.md/DESIGN.md, mutation-proving EXISTING
gates, and one L5 ship-test — not designing new enforcement mechanisms).

**Route:** `dr-change-orchestrator` (this is itself a workflow-design
change, not a code defect).

**One-goal statement:** Give `dr-drive-harness`'s "never generalize
instruction scope" rule a mechanical trigger — either (a) a lint-style
check comparing an agent's stated scope (GOAL.md's "In scope" /
REQUEST.md's requirement numbers) against the files it actually
touched, flagging any touch outside the named scope, or (b) an
explicit operator decision that this rule stays judgment-only (in
which case W3's "surviving negation must be enforced by a GATE" rule
itself gets an authoring-skills erratum noting the accepted exception).

**Evidence pointers:**
- `experiments/2026-08-12-change-skills-overhaul/CENSUS.md`, Rule
  extraction, `dr-drive-harness-36`.
- `experiments/2026-08-12-change-skills-overhaul/DESIGN.md`, "Gate
  table", the `**Never generalize an instruction beyond its stated
  scope**` row.

**End state:** either a new, mutation-proved GATE exists and is added
to `dr-drive-harness` + the gate table, or the operator's acceptance of
judgment-only status is ledgered as an authoring-skills erratum.
