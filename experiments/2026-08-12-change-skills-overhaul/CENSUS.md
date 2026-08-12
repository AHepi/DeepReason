# Census of .claude/skills/ (Phase A, read-only)

## Inventory

| File | Purpose | Entry artifact | Exit artifact | Lines |
|---|---|---|---|---|
| `.claude/skills/README.md` | Index over both families: phase tables, cross-cutting skills, and the shared rules that hold the set together. Not itself a workflow phase. | n/a (reference document) | n/a (reference document) | 56 |
| `.claude/skills/authoring-skills/SKILL.md` | Standing authority for writing/editing/retiring any skill or workflow file (this tranche's own binding authority). | a skill/workflow file being created, reviewed, or retired | none — it is a rule set an author consults, not a phase that hands off an artifact | 146 |
| `.claude/skills/deepreason-orchestrator/SKILL.md` | Family 1 (defect) router: selects exactly one subskill by which artifact is missing, holds the family's scope contract, map preflight, environment preflight, and hard prohibitions. | a problem statement (implicit; the family's actual first artifact is GOAL.md, produced by the subskill it routes to) | none directly — routes to whichever of GOAL/DIAGNOSIS/REPRO/FIX/fix-commit/VERIFY the routing table names next | 124 |
| `.claude/skills/dr-ask-the-right-question/SKILL.md` | Cross-cutting: routes any question to the cheapest authority (record -> framework -> operator), the dominance test for deciding-without-asking, and the wrong-question table. | an ambiguous/terse operator message, a phase's "stop and ask", or evidence contradicting expectation | none — its output is a decision recorded inline in whichever artifact the calling phase owns (no artifact of its own) | 150 |
| `.claude/skills/dr-capture-request/SKILL.md` | Family 2 phase 1: copies the operator's suggestion verbatim and splits it into numbered requirements. | the operator's message(s) | `REQUEST.md` | 59 |
| `.claude/skills/dr-change-orchestrator/SKILL.md` | Family 2 (change) router: the ledger rule, scope contract, map/environment preflight, routing table keyed on missing artifact, hard prohibitions. | an operator-suggested change | none directly — routes to whichever of REQUEST/SPEC/CHECKLIST/checked-step/VALIDATION/DELIVERY the routing table names next | 127 |
| `.claude/skills/dr-deliver-change/SKILL.md` | Family 2 phase 6: final commit/push, R-by-R reconciliation, map-delta and errata reporting. | a PASS `VALIDATION.md` | `DELIVERY.md` | 90 |
| `.claude/skills/dr-diagnose/SKILL.md` | Family 1 phase 2: locates one primary cause from the typed record (map Traps first, then the record's priority-ordered sources), no code change. | `GOAL.md` | `DIAGNOSIS.md` | 95 |
| `.claude/skills/dr-drive-harness/SKILL.md` | Cross-cutting driving manual: session preflight, public CLI lifecycle, live-run ladder rules, where to look before modifying/when diagnosing, process hygiene, routing index. | session start (no code artifact) | none — an index over other authorities (CLAUDE.md, docs/map, the workflow skills), not itself artifact-producing | 198 |
| `.claude/skills/dr-execute-step/SKILL.md` | Family 2 phase 4: executes exactly one unchecked `CHECKLIST.md` step, proves its done-criterion, updates the map in the same commit if behaviour changed, commits and pushes. The only Family-2 skill allowed to modify the tree. | `CHECKLIST.md` with >=1 unchecked step | one more checked step with pasted proof (loops; final exit is "all steps checked") | 147 |
| `.claude/skills/dr-explain-to-operator/SKILL.md` | Cross-cutting communication discipline: worry-first, in-line glossing on every intermediary message, exactly one closing analogy on every final output. | session start, before the first operator-facing message | none — a wording discipline applied to every message, not an artifact | 101 |
| `.claude/skills/dr-implement-fix/SKILL.md` | Family 1 phase 5: applies an approved `FIX.md` with a regression test, runs outward test rings, updates the map in the same commit. The only Family-1 skill allowed to modify production code. | approved `FIX.md` | one pushed commit (fix + regression test + map update) | 103 |
| `.claude/skills/dr-plan-steps/SKILL.md` | Family 2 phase 3: converts `SPEC.md` into an ordered, one-done-criterion-per-step checklist; scopes from the map first; plans map-update and `[COMMIT]` checkpoints. | `SPEC.md` | `CHECKLIST.md` | 82 |
| `.claude/skills/dr-propose-fix/SKILL.md` | Family 1 phase 4: designs the smallest correct fix as `FIX.md`; DeepReason-specific design rules (record is law, frozen surfaces need a flag, budgets/priorities as guarantees, counters count one thing); no code change. | `DIAGNOSIS.md` + `REPRO.md` | `FIX.md` | 58 |
| `.claude/skills/dr-reproduce/SKILL.md` | Family 1 phase 3: demonstrates the diagnosed cause with the smallest offline artifact (record replay > unit test > in-memory check); no live runs, no code change. | `DIAGNOSIS.md`'s falsifiable prediction | `REPRO.md` + one runnable artifact | 63 |
| `.claude/skills/dr-set-goal/SKILL.md` | Family 1 phase 1: turns a vague problem statement into one bounded, falsifiable, machine-decidable goal. | a problem statement (operator, failed run, RESULTS.md, or PARKED.md) | `GOAL.md` | 56 |
| `.claude/skills/dr-spec-change/SKILL.md` | Family 2 phase 2: maps every REQUEST.md requirement to a concrete, machine-decidable spec item; mandatory blast-radius/frozen-surface gate calls; budget arithmetic; rubric pass. | `REQUEST.md` | `SPEC.md` | 196 |
| `.claude/skills/dr-validate-change/SKILL.md` | Family 2 phase 5: re-runs every SPEC.md acceptance check plus the full gate, frozen-surface diff, packaging check, map validation; verdict PASS/FAIL; never patches. | `SPEC.md`'s acceptance checks + a fully-checked `CHECKLIST.md` | `VALIDATION.md` (PASS or FAIL) | 117 |
| `.claude/skills/dr-verify-outcome/SKILL.md` | Family 1 phase 6: proves the fix against `GOAL.md`'s success criterion, optionally one guarded live run; verdict PASS/FAIL; never patches. | `GOAL.md`'s success criterion + the pushed fix | `VERIFY.md` (PASS or FAIL) | 73 |

Total: 19 files, 2041 lines (`wc -l .claude/skills/README.md .claude/skills/*/SKILL.md`).

Files with no per-invocation exit artifact (README.md, authoring-skills,
the two family routers, and the three cross-cutting advisory skills —
dr-ask-the-right-question, dr-drive-harness, dr-explain-to-operator) are
flagged here for the evidence-binding pass below: authoring-skills S1
("One SKILL = one loop iteration... Entry and exit states are named
artifacts on disk") is written for WORKER skills; whether a router or an
advisory skill is exempt from S1/S2, or is itself evidence of S1 pressure
("loop control inside a worker skill" — see Rule extraction, W-class and
S-class flags below), is carried into the Rule extraction and Evidence
binding sections rather than resolved here.
