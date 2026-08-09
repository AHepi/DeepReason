# Results: the two-tier hard question set (in progress)

Honest ledger, updated as each pilot leg completes (CHECKLIST.md steps
20/23 write to this file; step 25 turns it into the final narrative).
Full segment write-up follows at delivery; this section tracks the
S6-style numbered failure ledger for the pilot phase (R18, budget 6)
live, as spent, not retrospectively.

## Failure ledger (pilot phase, budget 6)

| # | Leg | What happened | Charged? |
|---|-----|----------------|----------|
| — | Tier V | `setup`/`qualify`/`reason`/both `continue` legs/all three audits all returned rc=0; one `verify_root` violation (`foreign-criticism`) appeared on the FIRST audit and had cleared by the second — not a run failure, a mid-run state that resolved, recorded honestly | **0 charged** |

Running total: **0 / 6** spent after the Tier V leg.

## Tier V pilot — typed outcome (full detail: CHECKLIST.md step 19)

- Qualification: **full tier**, 300/300 cases, fresh (not cached), 124s.
- Reason + 2x continue: 14 cycles total, `state=completed`,
  `stop_reason=budget_exhausted` (the full recipe budget was actually
  used, not just offered).
- `verify_root`: clean by the final audit (`replay_valid: true`, 0
  violations); the transient `foreign-criticism` finding on the first
  audit is PARKED (step 24) as a possible structural consequence of
  sole-model operation, not fixed here.
- Tier V checker (tv-m04, known answer 16592) run against all 102
  final accepted claims: **no match** (`checker_any_pass: false`).
  Acceptable typed outcome per R16/PREREG.md — the harness format
  worked end to end; the question was hard enough that gemma4:31b did
  not solve it within budget.
