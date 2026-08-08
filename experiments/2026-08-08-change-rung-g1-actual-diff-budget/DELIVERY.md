# Delivered: Rung G1 — actual-diff budget gate
Branch: claude/rung-g1-actual-diff-budget-b0jede @ b697fc22 (pushed, tree clean)

## What changed

`tools/diff_budget.py` is a new, standalone command-line tool that
measures how many lines a change actually inserts (via `git
--numstat`), broken down by declared area, against a ledgered ceiling
— and reports one of `WITHIN` / `EXCEEDED` / `NO_CEILING` in a typed
JSON result (`DIFF_BUDGET_RESULT_V1`). It replaces the hand-arithmetic
budget check that let Rung S5 overrun its ledgered budget twice
(REQUEST.md Amendments 2/3 in that tranche) with a mechanical one. It
ships with 13 permanent tests (`tests/test_diff_budget.py`) and its
own `--self-test` mode, and is proven mutation-provable: a deliberate
one-operator perturbation of its verdict comparison was shown to fail
4 of those tests, then the perturbation was reverted and the suite
re-confirmed green.

Two workflow skills were amended to use it: `dr-spec-change`'s Budget
step now requires the SPEC.md headline to be the computed arithmetic
sum of its own itemization, naming the gate; `dr-execute-step`'s
`[COMMIT]` step now runs the gate itself and reads its verdict field,
with `EXCEEDED` remaining a STOP in the standard decision/options/
recommendation format. `docs/map/INV-frozen-surfaces.md` gained a
third instrument subsection (alongside the full gate and the root
sweep) with two `check:` lines pinning the tool's existence and shape.

The gate's own retrodiction proof — required by the tranche's
acceptance criteria — replayed Rung S5's real commit history through
it and confirmed it flags the overrun at the exact commit ("step
7-10", `b0813f59`) where S5's own record shows it actually happened,
not one step earlier and not indiscriminately. Building that proof
caught a real bug in the gate's own first draft (it was counting
insertions from the WHOLE diff rather than the declared areas,
returning `EXCEEDED` too early); the bug was found, fixed, and
re-verified within this tranche before delivery. The gate's own use
against its own creation also caught a real 3-line budget overrun on
this tranche itself (453 vs a 450 ceiling), which was raised to you as
a STOP rather than pushed through silently — you authorized a ceiling
bump to 460, recorded as REQUEST.md Amendment 1.

Zero contact with `src/`, the five frozen surfaces, or the append-only
record's writer/reader code — confirmed by an explicit empty-diff
check, not by intent alone.

## Reconciliation

| R | Operator's words (short) | Disposition | Proof |
|---|---|---|---|
| R1 | "tools/diff_budget.py ... DIFF_BUDGET_RESULT_V1" | done | c32b045f, VALIDATION S1 |
| R2 | "stable exit classes ... invalid invocation / evidence unavailable" | done | c32b045f, VALIDATION S2 (exit-class tests) |
| R3 | "dr-spec-change — budget headline MUST be the computed sum" | done | dba76ae1, VALIDATION S4 |
| R4 | "dr-execute-step — run the gate at every [COMMIT] step" | done | 614f8e67, VALIDATION S5 |
| R5 | "naming the tool path and result type exactly" | done | VALIDATION S4+S5 (exact-string greps) |
| R6 | "Zero src/ contact" | done | VALIDATION frozen-surface + full src/ diff (both empty) |
| R7 | "the map moves in the same commit with a check: line" | done | c32b045f, VALIDATION map section |
| R8 | "mutation-proven" | done | fd85e7d6 (perturb/red/restore/green) |
| R9 | "correct verdicts on a fixture repo diff" | done | 398fc26f, VALIDATION S1+S2 |
| R10 | "the retrodiction test ... flags the overrun at the step where it actually happened" | done | 38d28528, VALIDATION S3 |
| R11 | "Full pytest gate 0 failed net of P1/P3; full docs_verify 0 failed" | done | 40ee7cf5, 33b03579, VALIDATION Full gate + Map |
| R12 | "A defect found along the way is PARKED, never fixed" | done | 0f2ef768 (PARKED.md P1) |
| R13 | "Commit and push at every phase boundary with retry" | done | full commit history, every push succeeded |
| R14 | "Deliver through dr-validate-change and dr-deliver-change, then stop" | done | b697fc22 (VALIDATION PASS), this document |
| R15 | "Base your working branch on ... verify its head is d4f63007" | done | session-start check (this session's transcript) |
| R16 | "Run the session preflight" | done | session-start check (this session's transcript) |
| R17 | "Route through dr-change-orchestrator starting with dr-capture-request" | done | 71868ba3 |
| R18 | "Bump please" (ceiling 450 -> 460) | done | d5343afe, VALIDATION S12 |

No row is `not-done`. No row is `deferred`.

## Assumptions the operator may override

A1: "area" = one caller-supplied `--paths` value, reported verbatim as
the JSON `areas` key; omitting `--paths` yields a single `"total"`
area over the unrestricted diff.
A2: the named pre-existing `P1/P3` full-gate failure is
`tests/test_module_fingerprints.py::
test_absence_is_valid_before_the_feature_and_presence_valid_after`
(confirmed identical on the pristine base commit, matching Rung S5's
own recorded count).
A3: the retrodiction proof (R10) is a one-time, pasted demonstration,
not a permanent pytest test — its input commits live only on a branch
this tranche does not merge, and pinning a permanent test to them
would pass in this session and fail on any fresh clone (the exact
failure mode `docs/ERRATA.md` E7 already names). The fixture-repo
tests give the same verdict logic permanent coverage instead.

## Map delta

changed: `docs/map/INV-frozen-surfaces.md` (new "The diff budget gate
(Rung G1)" subsection, 2 new checks, `Verified-at` advanced to
`6a033fa2`; header renamed "The two instruments..." -> "The
instruments..." since there are now three)
created: none
new checks: 2 (`ast.parse` syntactic validity, `DIFF_BUDGET_RESULT_V1`
content grep — both over `tools/diff_budget.py`)
left stale: none from this tranche (`docs_verify --stale` lists 15
other documents, all predating this tranche and out of its scope,
C1 — see VALIDATION.md's Map section for the full list and reasoning)

## Parked (not done, not promised)

P1 — `.claude/skills/README.md`, named in this tranche's own task
instructions, is absent from this branch but exists on
`origin/claude/monitor-session-handover-63ajqv`'s current tip
(`2c9a2023`), along with three skills (`dr-ask-the-right-question`,
`dr-drive-harness`, `dr-explain-to-operator`) this branch also does
not carry — expected branch divergence (this branch was deliberately
reset to an earlier point, `d4f63007`, on that same branch), not a
missing artifact. No follow-up prompt is owed: it resolves itself on
the next rebase/merge onto that branch's later state. Full detail in
`PARKED.md`.

recommended next: none from this tranche — P1 needs no action, only
awareness. The pre-plan's own ladder (`docs/proposals/
DETERMINISTIC_GATES_PREPLAN.md`) names G2 (mutation attestation) as
the next rung in sequence, at the operator's discretion.
