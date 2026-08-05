# Request: Execute Rung 7 — authority as a declared policy
Captured: 2026-08-04 from the operator's message approving rung 6, plus
the Rung 7 section of `docs/HANDOVER_2026-08-03.md` which that message
names as the thing to execute (same adoption pattern rungs 1 and 6 used).

## Verbatim

> Rung 6 SPEC approved: Option D is the accepted design, assumptions
> A1–A5 stand, grouped-commit budget accepted. Do NOT execute —
> implementation is deferred until after the rung program; when it runs,
> add temp-directory cleanup for the battery harness at plan time. Now
> Rung 7 via dr-change-orchestrator, same discipline: DESIGN-AND-STOP,
> through dr-spec-change ONLY, STOP after committing SPEC.md and present
> it. This is the most dangerous socket — frozen-adjacent everywhere —
> so the frozen-surface contact forecast is where this spec lives or
> dies. One rung only.

(The rung-6 half of this message — "Rung 6 SPEC approved ... at plan
time" — is ledgered in
`experiments/2026-08-04-change-rung6-plugin-conformance/REQUEST.md`
Amendment 1 as R12-R14. It is quoted here only for completeness of the
operator's verbatim words; it governs that tranche, not this one.)

> `docs/HANDOVER_2026-08-03.md`, Rung 7 section, adopted by this request:
> "### Rung 7 — authority as a declared policy  [DESIGN-AND-STOP]
> Route: `dr-change-orchestrator` through dr-spec-change ONLY.
> Goal: a SPEC for routing every status change through one narrow gate
> consulting a declared policy. This is the most dangerous socket
> (CON-authority; adjudication; frozen-adjacent everywhere). Same stop
> discipline as rung 6. Do not write this SPEC before rungs 1–4 are
> delivered — it depends on their vocabulary and fingerprints."

## Requirements

R1 (process): "Now Rung 7 via dr-change-orchestrator"

R2 (process): "same discipline: DESIGN-AND-STOP, through dr-spec-change
ONLY"

R3 (process): "STOP after committing SPEC.md and present it."

R4 (artifact): "the frozen-surface contact forecast is where this spec
lives or dies." — the forecast is not a checklist line in this spec; it
is the spec's load-bearing section and must be measured, not asserted.

R5 (process): "One rung only."

R6 (artifact, from the adopted handover text): "a SPEC for routing every
status change through one narrow gate consulting a declared policy."

R7 (constraint, from the adopted handover text): "This is the most
dangerous socket (CON-authority; adjudication; frozen-adjacent
everywhere)." — names the three map regions the spec must reckon with.

R8 (process, from the adopted handover text): "Do not write this SPEC
before rungs 1–4 are delivered — it depends on their vocabulary and
fingerprints." — precondition. Rungs 1-5 are delivered
(`experiments/*/DELIVERY.md`, branch head `2cc3fd50`); rung 6 is an
approved-but-deferred SPEC. Precondition satisfied.

## Standing constraints

C1: "DESIGN-AND-STOP, through dr-spec-change ONLY" — forbids
`dr-plan-steps`, `dr-execute-step`, `dr-validate-change`,
`dr-deliver-change` in this tranche. No `src/` change, no map change, no
gate run.

C2: "One rung only." — no rung-6 execution work here (rung 6 is
separately deferred by its own R13), and no new rung invented.

C3 (carried from the rung-6 tranche, still standing): P7 — the parked
`verify_root` `attempt-validity` violation from rung 5's live A/B arm B
— stays parked. The operator has not lifted it, and rung 7 touches
`invariants.py`-adjacent territory, so this is the tranche most likely
to be tempted.

C4 (from the adopted handover, Executor calibration): "The frozen
surfaces (`docs/map/INV-frozen-surfaces.md`) bind every rung: state
digests, harness event application, replay-validation formats, manifest
schemas AND validators, qualification subjects. Readers may be fixed;
formats may not; a change that moves a committed root's verdict is wrong
by definition."

C5 (from `docs/HANDOVER_2026-08-03.md`, ERRATA E10's generalized rule):
"accept lines state PROPERTIES; any named mechanism is a suggestion the
spec phase must verify for reachability."

C6 (from `.claude/skills/dr-spec-change/SKILL.md`): DESIGN-AND-STOP
specs require a Measurements section (every load-bearing claim backed by
pasted command output), a priced Options table, a Blast-radius census,
and a final six-question rubric pass.

C7 (`docs/map/SUB-adjudication.md`, "Where to change what" and Traps —
a codebase-side constraint the spec cannot negotiate with): "let a
measure, school, or rank steer status | **nothing here, by
construction**"; and "Changing anything here changes the status map of
every committed root ... Treat this package under
`DR-INV-frozen-surfaces`: fix readers, not labels."

## Map preflight (resolved ids)

Read before designing, in the order `dr-change-orchestrator` requires:

- `docs/map/INDEX.md` — routing.
- `docs/map/INV-frozen-surfaces.md` — **first**; five surfaces, plus the
  frozen-adjacent `route_fingerprint` and the `Config`-field trap.
- Seams before subsystems: `DR-SEAM-adjudication-x-rules`
  (`Owns:` `rules/warrants.py`, `adjudication/edges.py`).
- `DR-SUB-adjudication` (`Owns:` `src/deepreason/adjudication/`).
- `DR-CON-authority` (`Owns:` `authority.py`, `config.py`, `rules/crit.py`,
  `informal/trial.py`, `run_manifest.py`, `jolts.py`, `ops.py`,
  `scheduler/scheduler.py`, `v6_policy.py`, `preparation.py`).
- `DR-CON-warrants-and-attacks` (`Owns:` `rules/warrants.py`,
  `adjudication/edges.py`, `adjudication/grounded.py`,
  `adjudication/support.py`, `ontology/warrant.py`).

Undocumented seam noted at preflight, per `SCHEMA.md`'s rule that a
missing seam document is a finding rather than a blocker:
**adjudication x authority** is listed `Seams-undocumented:` on
`SUB-adjudication.md` and is precisely the pair this rung is about.
`SUB-adjudication.md`'s own seam table already characterizes it
("indirect, not absent"), which is the strongest available prior for
this spec's central question.

## Open questions (for dr-spec-change)

Q1: "every status change" — `SUB-adjudication.md` states that
`final_labels` is the only producer of `Status` values and
`Harness._adjudicate` is the sole writer of `state.status`. If that is
literally true, the "one narrow gate" the rung asks for ALREADY EXISTS,
and the requirement's live content is entirely in "consulting a declared
policy". The spec phase must measure this rather than assume it, and say
plainly which half of R6 is already satisfied.

Q2: if the gate exists, can it consult a policy at all? `SUB-adjudication`
says labels are recomputed on every root open, so a label that depends
on run configuration would make a recorded root's meaning depend on
something outside its own bytes. The spec phase must decide whether R6's
literal reading is achievable, and if not, deliver the PROPERTY R6 wants
(C5) with the contradiction recorded in writing rather than silently
redesigned.

Q3: which authority decisions are actually scattered today, and would a
single declared policy consolidate them? `CON-authority.md` names five
`Config` knobs plus a differently-shaped sixth, two closed vocabularies,
and three paths where the manifest preflight never runs. The spec phase
must inventory the real scatter by measurement, not by recall.

Q4: "declared" where? `Config` (invisible to replay, but the
`_versioned_source_config_data` trap applies) versus the manifest
(frozen surface 4, and every qualification subject digest derives from
it) versus a new record type. Materially different in effort and in
frozen-surface contact — the spec phase must price each.

## Amendments

**Amendment 1 (2026-08-04, operator, verbatim) — SPEC.md APPROVED; 7a
AUTHORIZED, 7b/7c DEFERRED.**

> Rung 7 SPEC approved: Option D with the 7a/7b/7c split, assumptions
> A1–A5 stand. The mint-time placement and its M5/M6 evidence are the
> accepted design. Do NOT execute 7b or 7c — deferred until after the
> rung program wrap-up, same as rung 6. You MAY execute 7a only (the
> seam document, docs-only) now, then stop and confirm the program is
> complete.

R9 (process): "Rung 7 SPEC approved: Option D with the 7a/7b/7c split,
assumptions A1–A5 stand. The mint-time placement and its M5/M6 evidence
are the accepted design." — SPEC.md as committed at `e1e23990` is the
approved design. A1-A5 cease to be open assumptions and become confirmed
decisions. The mint-time placement is settled: no later phase may
relitigate it.

R10 (process): "Do NOT execute 7b or 7c — deferred until after the rung
program wrap-up, same as rung 6." — sub-tranches 7b (the
`DeclaredAuthorityPolicy` object, SPEC S3) and 7c (the two ungated
argumentative mint sites, SPEC S4) are NOT executed. No `src/` file is
touched by this tranche.

R11 (behavior/artifact): "You MAY execute 7a only (the seam document,
docs-only) now" — sub-tranche 7a as specified in SPEC.md's Budget
section: `SEAM-adjudication-x-authority.md`, plus `INDEX.md`'s seam
matrix row, plus both sides' `Seams:`/`Seams-undocumented:` headers
(the ERRATA E9 lesson), carrying the M5/M6 measurements as checks.
Accept per SPEC.md 7a: `docs_verify` full mode 0 failed, `--audit` 0,
`--links` 0.

R12 (process): "then stop and confirm the program is complete." — after
7a is delivered, stop and report the state of the whole rung program
(rungs 1-7), not merely this tranche.

**Scope consequence:** this tranche now runs the full change workflow
(`dr-plan-steps` → `dr-execute-step` → `dr-validate-change` →
`dr-deliver-change`) for 7a ONLY. C1's "dr-spec-change ONLY" is
superseded for 7a by R11 and stands unchanged for 7b/7c. C3 (P7 stays
parked) and C4 (frozen surfaces) are unaffected and still bind.
