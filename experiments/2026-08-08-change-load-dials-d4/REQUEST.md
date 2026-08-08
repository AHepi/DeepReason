# Request: the load dials — Rung D4 of the dual-mode conjecture program

Captured: 2026-08-08 from this session's opening task message, plus its
cited source document `docs/proposals/DUAL_MODE_CONJECTURE_PREPLAN.md`
(Rung D4 section verbatim, and requirements R-f/R-g), plus CLAUDE.md's
"Operator design laws" section (binding standing law per the task's own
instruction to read it).

## Verbatim

This session's task message, opening instruction (full text):

> Setup FIRST: git fetch origin claude/monitor-session-handover-63ajqv
> && git checkout -B claude/<your-branch-name> origin/claude/monitor-
> session-handover-63ajqv, verify head b8e66ea5, preflight. Then read
> CLAUDE.md from this checkout (Operator design laws binding),
> .claude/skills/dr-explain-to-operator/SKILL.md directly (follow for
> every message), and .claude/skills/README.md.
> You are the executor for Rung D4 of the dual-mode conjecture program:
> the load dials. DESIGN-AND-STOP first — spec only, no code this
> window. Route through dr-change-orchestrator (dr-capture-request →
> dr-spec-change → STOP). Authority: docs/proposals/
> DUAL_MODE_CONJECTURE_PREPLAN.md Rung D4 verbatim, R-f (the operator's
> dial requirement: priority and share for conjecture vs criticism
> load, scratchpad load, simulation load, and coding load — "which
> gets priority and by how much") and R-g (kind-blindness binds every
> scheduling decision). Your measurement base: the D1 census's
> load-knob inventory (43 knobs, section 5 of experiments/2026-08-08-
> change-pipeline-census-d1/CENSUS.md) — cite its rows, re-measure only
> what the design turns on. Note the D3 tranche has since landed
> (encoder role, candidate-checker commitments, conjecturer.turn.v7) —
> the dial set must cover the coding load that now exists, not the
> pre-D3 tree.
> SPEC.md must decide, measured: the typed load-mix policy's shape (one
> record: weights/priorities over {conjecture, criticism, scratchpad,
> simulation, coding} — exact semantics of "priority" vs "share" per
> family, derived from what each knob actually meters per the census);
> mint-time freezing into the RunManifest (the rung-7 placement law: a
> continuation continues under the mix it was born with — expect this
> to be the design's one frozen-surface question, surface 4; name the
> contact precisely, assume no grant, and note the Amendment-3
> precedent shape from D3 for how a scoped grant was worded); which of
> the 43 knobs the mix DRIVES versus which stay independent (every knob
> dispositioned explicitly — driven, independent, or
> deprecated-by-this-design; silent omission is a bug); named presets
> as the operator surface (deepreason setup/reason flag shape, default
> preset = today's behavior byte-identical); the R-g argument for every
> scheduling touch (a dial may shift budget between WORK FAMILIES,
> never weight by conjecture KIND — state the distinction and its
> enforcement test); and the interaction with per-capability budgets
> (the shared-state pooling invariant from CLAUDE.md: budgets meter
> only their own capability's records). Frozen-surface forecast from
> scratch. Budget headline computed from itemization;
> tools/diff_budget.py discipline throughout. Close with the decision
> sheet — every fork priced as roads with recommendations. Commit and
> push REQUEST.md and SPEC.md, then STOP for operator words.

`docs/proposals/DUAL_MODE_CONJECTURE_PREPLAN.md` Rung D4 section,
quoted verbatim:

> ### Rung D4 — the load dials  [DESIGN-AND-STOP, then EXECUTE]
> One typed load-mix policy: weights/priorities for {conjecture,
> criticism, scratchpad, simulation, coding} — which gets budget and
> scheduling priority, and by how much. Frozen at mint time into the
> manifest (the rung-7 placement law: a continuation continues under
> the mix it was minted with), surfaced as named presets
> (BEHAVIOR_MODES_PREPLAN's modes; S7's packages consume these later).
> D1's knob inventory decides what the weights actually drive (rank
> re-weighting, per-role call ceilings, capability grant budgets,
> scratch attention share). Scheduler selection policy is
> operator-approval territory: SPEC stops for words before code.
> Accept for the eventual fix: two runs differing only in the mix show
> the predicted call-share shift from typed attempt records; a
> no-mix-specified run is byte-identical to today.

`docs/proposals/DUAL_MODE_CONJECTURE_PREPLAN.md` requirements R-f and
R-g, quoted verbatim:

> - R-f: a load-dial mechanism — operator-settable priority and share
>   for conjecture vs criticism load, scratchpad load, simulation
>   load, and coding load.
> - R-g (BINDING GUARDRAIL, operator's words 2026-08-08, "something
>   I've repeated endlessly": "as long as the existing infrastructure
>   does not force formalism and penalize conjectures that are not
>   formal"): no mechanism in this program — nor anywhere in the
>   harness — may require formal encoding for a conjecture to enter,
>   rank, survive, or be accepted; may weight ranking, scheduling, or
>   acceptance on a conjecture's KIND; or may escalate the
>   formal-channel option into pressure (the "when it implies"
>   surfacing is a one-time option rendering, never a repeated nudge,
>   never a penalty for declining). Formal backing may confer
>   PROTECTION (prose-immunity, as today); its absence confers no
>   disadvantage. D3's and D4's regressions must prove kind-blindness:
>   an informal conjecture's rank, criticism exposure, and acceptance
>   path are byte-identical whether or not the formal channel exists in
>   the build, and D5's formal-submission-rate metric is a MEASUREMENT,
>   never a target any mechanism optimizes toward.

CLAUDE.md "Operator design laws" section, quoted verbatim (binding
standing law):

> - **Formalism is an option, never an obligation** (2026-08-08,
>   repeated by the operator "endlessly" — do not make them repeat it
>   again): nothing may force a conjecture to be formal, and nothing
>   may penalize a conjecture for being informal — not admission, not
>   rank, not criticism exposure, not acceptance. Formal backing may
>   grant protection (prose-immunity); its absence grants no
>   disadvantage. Any design that weights outcomes on conjecture KIND
>   violates this law. See DUAL_MODE_CONJECTURE_PREPLAN.md R-g for the
>   full binding form.
> - **Seats change how content is GENERATED, never what counts as
>   EVIDENCE** (the modes/packages guardrail, BEHAVIOR_MODES_PREPLAN /
>   ROLE_SEAT_SEPARATION_PLAN S7): no seat, mode, or package may let a
>   generation seat's prose skip criticism.

## Requirements

R1 (process): "DESIGN-AND-STOP first — spec only, no code this
window."

R2 (process): "Setup FIRST: git fetch origin claude/monitor-session-
handover-63ajqv && git checkout -B claude/<your-branch-name>
origin/claude/monitor-session-handover-63ajqv, verify head b8e66ea5,
preflight." — done this session: verified.

R3 (process): "Then read CLAUDE.md from this checkout (Operator design
laws binding), .claude/skills/dr-explain-to-operator/SKILL.md directly
(follow for every message), and .claude/skills/README.md." — done this
session.

R4 (process): "Route through dr-change-orchestrator (dr-capture-request
→ dr-spec-change → STOP)." — in progress (this document is phase 1).

R5 (process): "Authority: docs/proposals/DUAL_MODE_CONJECTURE_PREPLAN.md
Rung D4 verbatim, R-f ... and R-g ..." — quoted above in full.

R6 (process): "Your measurement base: the D1 census's load-knob
inventory (43 knobs, section 5 of experiments/2026-08-08-change-
pipeline-census-d1/CENSUS.md) — cite its rows, re-measure only what the
design turns on." — NOTE: this tranche's own re-reading of CENSUS.md
section 5 counts 54 knobs (26 `Config` + 17 capability-policy + 2
`CriticismPolicyV1` + 9 `AttentionPolicyV1`), not 43; flagged as Q1
below rather than silently substituted.

R7 (behavior): "Note the D3 tranche has since landed (encoder role,
candidate-checker commitments, conjecturer.turn.v7) — the dial set must
cover the coding load that now exists, not the pre-D3 tree."

R8 (behavior): "SPEC.md must decide, measured: the typed load-mix
policy's shape (one record: weights/priorities over {conjecture,
criticism, scratchpad, simulation, coding} — exact semantics of
'priority' vs 'share' per family, derived from what each knob actually
meters per the census)."

R9 (behavior): "mint-time freezing into the RunManifest (the rung-7
placement law: a continuation continues under the mix it was born
with — expect this to be the design's one frozen-surface question,
surface 4; name the contact precisely, assume no grant, and note the
Amendment-3 precedent shape from D3 for how a scoped grant was
worded)."

R10 (behavior): "which of the 43 knobs the mix DRIVES versus which stay
independent (every knob dispositioned explicitly — driven, independent,
or deprecated-by-this-design; silent omission is a bug)." — subject to
the same knob-count note as R6/Q1; every knob measured in this
tranche's own re-reading of CENSUS.md section 5 gets a disposition.

R11 (artifact): "named presets as the operator surface (deepreason
setup/reason flag shape, default preset = today's behavior
byte-identical)."

R12 (behavior): "the R-g argument for every scheduling touch (a dial
may shift budget between WORK FAMILIES, never weight by conjecture
KIND — state the distinction and its enforcement test)."

R13 (behavior): "the interaction with per-capability budgets (the
shared-state pooling invariant from CLAUDE.md: budgets meter only
their own capability's records)."

R14 (artifact): "Frozen-surface forecast from scratch."

R15 (process): "Budget headline computed from itemization;
tools/diff_budget.py discipline throughout."

R16 (artifact): "Close with the decision sheet — every fork priced as
roads with recommendations."

R17 (process): "Commit and push REQUEST.md and SPEC.md, then STOP for
operator words."

R18 (process, from dr-explain-to-operator): "follow [it] for every
message" — done this session; every operator-facing message in this
tranche worries-first, glosses technical terms in intermediaries, and
closes the final message with one analogy.

## Standing constraints

C1: "DESIGN-AND-STOP first — spec only, no code this window" — no file
under `src/`, `tests/`, or `tools/` may change in this tranche; only
`experiments/2026-08-08-change-load-dials-d4/` and (if a map gap is
found) `docs/map/` may change, and even the latter is describing the
CURRENT tree, not a design not yet built.

C2 (R-g, quoted above in full): binding guardrail — no scheduling touch
this design proposes may weight ranking, scheduling, or acceptance on a
conjecture's KIND; every dial moves WORK FAMILIES only.

C3 (Operator design law, CLAUDE.md, standing): "Formalism is an option,
never an obligation ... nothing may penalize a conjecture for being
informal — not admission, not rank, not criticism exposure, not
acceptance."

C4 (Operator design law, CLAUDE.md, standing): "Seats change how content
is GENERATED, never what counts as EVIDENCE ... no seat, mode, or
package may let a generation seat's prose skip criticism."

C5 (CLAUDE.md, standing): "Commits: one defect or one change per
commit; message states what, why ... Push with retry (2s/4s/8s/16s
backoff)."

C6 (CLAUDE.md, standing): "The map moves in the SAME COMMIT as the
code" — not applicable to code (none this tranche), but any map
document touched to record the design's forecast moves with the
artifact it describes.

## Open questions (for dr-spec-change)

Q1: the task's own knob count ("43 knobs, section 5") does not match
this tranche's own re-reading of `CENSUS.md` section 5, which tables 54
knobs (26 `Config` + 28 manifest-embedded: 17 capability-policy + 2
`CriticismPolicyV1` + 9 `AttentionPolicyV1`). Need to decide in
dr-spec-change whether "43" was a stale/partial count (e.g. counting
only one sub-family) and, either way, disposition EVERY row this
tranche's own re-reading finds — silent omission is R10's own named
bug, and citing "43" without reconciling the discrepancy would itself
be a silent omission.

Q2: "the dial set must cover the coding load that now exists" — D3
landed `rules/encoding.py::draft_encoded_commitment` (the `"encoder"`
seat delegation) and `rules/relatedness.py::relatedness_trial`, but
`docs/map/SEAM-rules-x-workflow.md` states both are DORMANT: "neither
has any caller anywhere in `src/` yet ... unreachable from every
scheduler path". Need to decide in dr-spec-change how a load dial can
meter a family with zero live call sites today — whether the design
names this as a documented gap (no live knob to drive yet) or proposes
the dial's coding-share apply prospectively to whichever future tranche
wires the call site.

Q3: "exact semantics of 'priority' vs 'share' per family" is not
self-evident from R-f's words alone ("which gets priority and by how
much" could mean a scheduling tie-break order, a proportional budget
split, or both). Need dr-spec-change to derive the two concepts
separately from what the D1 knobs actually meter (e.g. `ARG_CRIT_PER_
CYCLE` is a ceiling, not a share; `INTEGRATION_BUDGET_SHARE` already IS
a fraction) rather than assuming one English word maps to one
mechanism.

Q4: "expect this to be the design's one frozen-surface question,
surface 4" — need to confirm in dr-spec-change whether ANY other
frozen surface (1, 2, 3, or 5) is actually touched by a mix that drives
manifest-embedded knobs (capability policies, `CriticismPolicyV1`,
`AttentionPolicyV1`) at mint time, rather than assuming surface 4 alone
per the task's own expectation.

Q5: "note the Amendment-3 precedent shape from D3 for how a scoped
grant was worded" — need to locate and quote D3's (the
`2026-08-08-change-pipeline-design-d2` tranche's) REQUEST.md Amendment
3 verbatim in dr-spec-change, as the precedent shape for how this
tranche should word its own surface-4 ask if the operator later grants
one.

## Amendments

(none yet)
