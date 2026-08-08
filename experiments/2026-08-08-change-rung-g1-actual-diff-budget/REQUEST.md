# Request: Rung G1 — actual-diff budget gate

Captured: 2026-08-08, executor session, from the task-assignment message
opening this session.

## Verbatim

> Read CLAUDE.md in full first, then .claude/skills/README.md. You are
> the executor for Rung G1 of the deterministic-gates program: the
> actual-diff budget gate. Base your working branch on
> origin/claude/monitor-session-handover-63ajqv and verify its head is
> d4f63007 — if not, stop and say so. Run the session preflight (which
> deepreason || pip install -e . --break-system-packages -q).
> Route through dr-change-orchestrator starting with dr-capture-request.
> Authority: docs/proposals/DETERMINISTIC_GATES_PREPLAN.md, Rung G1
> section, verbatim, plus its "Shape rules" section which binds every
> rung. Scope is G1 alone: tools/diff_budget.py emitting
> DIFF_BUDGET_RESULT_V1 (actual cumulative insertions by area, ceiling,
> verdict WITHIN / EXCEEDED / NO_CEILING; stable exit classes separate
> result-emitted / invalid-invocation / evidence-unavailable, semantic
> verdict inside the result), plus the two skill amendments the plan
> names (dr-spec-change: budget headline must be the computed sum of its
> itemization; dr-execute-step: gate runs at every [COMMIT] step,
> EXCEEDED is a STOP with priced options) — naming the tool path and
> result type exactly. Zero src/ contact; frozen surfaces untouched; the
> map moves in the same commit with a check: line for the gate.
> Acceptance, from the plan verbatim: correct verdicts on a fixture
> diff; mutation-proven; and the retrodiction test — replay Rung S5's
> own commit history (54feb5cc..2e009ba7 on
> origin/claude/s5-dr-plan-steps-q5utlc) through the gate and show it
> flags the overrun at the step where it actually happened. Full pytest
> gate 0 failed net of the named pre-existing P1/P3; full docs_verify 0
> failed. A defect found along the way is PARKED, never fixed — one
> tranche, one goal. Commit and push at every phase boundary with retry
> (2s/4s/8s/16s). Deliver through dr-validate-change and
> dr-deliver-change, then stop.

## Authority document, quoted in full (docs/proposals/DETERMINISTIC_GATES_PREPLAN.md)

### Shape rules (all rungs)

> - Gates live in `tools/`, never `src/` — zero frozen-surface contact,
>   zero harness behavior change, by construction.
> - Every gate consumes explicit inputs and emits a versioned typed
>   result (`*_RESULT_V1` JSON): stable exit classes distinguish
>   "result emitted" / "invalid invocation" / "evidence unavailable";
>   semantic verdicts live INSIDE the result, not in the exit code.
> - A gate reports facts; the OWNING SKILL decides policy. Each rung
>   therefore lands in two parts in one tranche: the tool, and the
>   amendment to the owning skill's SKILL.md naming when the gate runs
>   and what its verdicts oblige.
> - Each gate ships with its own mutation proof (perturb → gate goes
>   red → restore) and a `check:` line in the relevant map document, so
>   docs_verify holds the gate the way it holds every other claim.
> - The map moves in the same commit; full pytest gate + docs_verify at
>   every tranche boundary, as always.

### Rung G1 — actual-diff budget gate [EXECUTE, small]

> **Recorded failure:** Rung S5 overran its ledgered budget TWICE
> (REQUEST.md Amendments 2 and 3, R21/R22), each discovered by the
> executor noticing, not by any instrument; the SPEC's own headline
> estimate (220–300) contradicted its own itemization (~325–435) and
> nothing caught the arithmetic. Precedent tranche:
> `2026-08-05-change-budget-ceiling-at-commit`.
> **Deliverable:** `tools/diff_budget.py <base> [--ceiling N] [--paths ...]`
> → `DIFF_BUDGET_RESULT_V1` (actual cumulative insertions by area,
> ceiling, verdict WITHIN / EXCEEDED / NO_CEILING). Skill amendments:
> `dr-spec-change` — the Budget section's headline MUST be the computed
> sum of its own itemization (paste the gate run over the itemized
> estimates); `dr-execute-step` — run the gate at every [COMMIT] step
> against the ledgered ceiling; EXCEEDED is a STOP with priced options,
> raised at the commit that crosses the line, never discovered at
> delivery.
> **Accept:** gate emits correct verdicts on a fixture repo diff;
> mutation-proven; S5's own history replayed through the gate flags the
> overrun at the step where it actually happened (retrodiction test).

## Requirements

R1 (artifact): "Deliverable: `tools/diff_budget.py <base> [--ceiling N]
[--paths ...]` → `DIFF_BUDGET_RESULT_V1` (actual cumulative insertions
by area, ceiling, verdict WITHIN / EXCEEDED / NO_CEILING)".

R2 (behavior): "stable exit classes distinguish 'result emitted' /
'invalid invocation' / 'evidence unavailable'; semantic verdicts live
INSIDE the result, not in the exit code" — applied to `diff_budget.py`
per the Shape rules that bind every rung.

R3 (artifact): "Skill amendments: `dr-spec-change` — the Budget
section's headline MUST be the computed sum of its own itemization
(paste the gate run over the itemized estimates)".

R4 (artifact): "`dr-execute-step` — run the gate at every [COMMIT] step
against the ledgered ceiling; EXCEEDED is a STOP with priced options,
raised at the commit that crosses the line, never discovered at
delivery".

R5 (process): "naming the tool path and result type exactly" — both
skill amendments (R3, R4) must cite `tools/diff_budget.py` and
`DIFF_BUDGET_RESULT_V1` literally, not paraphrased.

R6 (process): "Zero src/ contact; frozen surfaces untouched".

R7 (artifact): "the map moves in the same commit with a check: line for
the gate" — per Shape rules: "a `check:` line in the relevant map
document, so docs_verify holds the gate the way it holds every other
claim."

R8 (process): "Each gate ships with its own mutation proof (perturb →
gate goes red → restore)" — per Shape rules, applied to this gate:
"mutation-proven" (Accept criterion).

R9 (behavior/acceptance): "gate emits correct verdicts on a fixture
repo diff".

R10 (behavior/acceptance): "the retrodiction test — replay Rung S5's
own commit history (54feb5cc..2e009ba7 on
origin/claude/s5-dr-plan-steps-q5utlc) through the gate and show it
flags the overrun at the step where it actually happened".

R11 (process): "Full pytest gate 0 failed net of the named pre-existing
P1/P3; full docs_verify 0 failed."

R12 (process): "A defect found along the way is PARKED, never fixed —
one tranche, one goal."

R13 (process): "Commit and push at every phase boundary with retry
(2s/4s/8s/16s)."

R14 (process): "Deliver through dr-validate-change and dr-deliver-change,
then stop."

R15 (process — environment): "Base your working branch on
origin/claude/monitor-session-handover-63ajqv and verify its head is
d4f63007 — if not, stop and say so." (Preflight — already discharged
this session: head confirmed d4f63007, branch reset onto it.)

R16 (process — environment): "Run the session preflight (which
deepreason || pip install -e . --break-system-packages -q)." (Already
discharged this session: `deepreason` importable, package present.)

R17 (process): "Route through dr-change-orchestrator starting with
dr-capture-request."

## Standing constraints

C1: "Scope is G1 alone" — no work on G2–G5 of the pre-plan.

C2: "Zero src/ contact; frozen surfaces untouched" (same as R6, also a
hard constraint on every step).

C3: "naming the tool path and result type exactly" (same as R5, binds
wording of the skill amendments).

C4: "A defect found along the way is PARKED, never fixed — one
tranche, one goal" (same as R12).

C5: Full CLAUDE.md governs as project-level standing instruction
(commit discipline, gate discipline, frozen surfaces) — read in full
per task instruction before starting.

## Open questions (for dr-spec-change)

Q1: The task says to read ".claude/skills/README.md" but no such file
exists in the repository (`.claude/skills/` contains only skill
subdirectories, no README.md, on this branch or on main). Treated as
satisfied by reading the skill directory listing and
`dr-change-orchestrator`'s own SKILL.md, which serves the equivalent
orientation purpose. Not blocking — recorded as a documentation
discrepancy, PARKED per R12/C4 rather than fixed in this tranche.

Q2: "actual cumulative insertions by area" — "area" is not defined in
the plan. dr-spec-change must define what partitions a diff into
"areas" (e.g. top-level path segment under repo root, or a
caller-supplied `--paths` grouping) from the plan's own words: `--paths
...]` in the CLI signature suggests areas are caller-specified path
globs/prefixes, with a sensible default grouping if none given.

Q3: The named "pre-existing P1/P3" full-gate failures (R11) are not
enumerated in this task message. dr-spec-change/dr-validate-change must
identify them from the current gate run's own output (baseline pytest
run before any change) rather than assume a specific count or name.

## Amendments

**Amendment 1 (2026-08-08, operator message, verbatim).** Sent in
response to a budget-overrun STOP raised before step 8's commit: the
gate's own first real use, checking its own creator's work, reported
453 actual insertions against SPEC.md's 450 ceiling (`tools/` 228,
`tests/` 192, `.claude/skills/` 16, `docs/map/` 17), after the
`dr-execute-step` amendment's wording was already trimmed once. Two
options were priced: (A) bump the ceiling 450 -> 460; (B) trim the
amendment further, at a real cost to the clarity of instructions that
govern exactly this kind of check. Recommendation was (A).

> Bump please

New requirement, quoting the operator's own words:

R18 (process, budget correction): "Bump please" — the operator
authorizes raising SPEC.md's ceiling for this tranche from 450 to 460
insertions across the gate's own enforced scope (`tools/`+`tests/`+
`.claude/skills/`+`docs/map/`), per the priced Option A. No symbol,
file, or requirement beyond SPEC.md's already-declared Items S1-S11 is
authorized by this amendment; scope (C1: "G1 alone") is unchanged.
