# Request: "Rung 4 of the v2 calculus program — frame assertions and the standing view"
Captured: 2026-08-22 from the operator's single tranche-opening message (this session, message 1)

## Verbatim

> Change tranche: Rung 4 of the v2 calculus program — frame assertions
> and the standing view. Route through dr-change-orchestrator; the
> workflow's own stop conditions apply, nothing else stops.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> claude/calculus-rung4-frame-assertions-b7pk2s origin/main;
> git merge-base --is-ancestor 3429bb619 HEAD || re-fetch. pip install
> -e . --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q. Use `python -m pytest`, never
> bare pytest. Read CLAUDE.md in full; load dr-drive-harness,
> dr-explain-to-operator.
>
> AUTHORITY: the operator-approved program ladder,
> experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md,
> Rung 4 — read that section IN FULL before SPEC.md, plus
> docs/COMPUTABLE_CALCULUS.md §9 and §12 (Def 9.2, Law 9.4, Props
> 12.3-12.5) and DECISIONS.md D-5 (answered: a fixed finite DSL for
> scope predicates, reusing the declarative_numeric_v1 shape from spec
> v1.6 — no free-form predicate language). Entry conditions met: Rung
> 3b delivered (frame separation, src/deepreason/calculus/
> separation.py), Rung 1b-ii delivered (signal consumption).
>
> WORK, per the ladder:
> - Frame assertion as an ORDINARY artifact with content
>   <subject, scope sigma, validity, departure protocol> (Def 9.2). No
>   new event rule, no kind field. `bounded` validity is content, not a
>   third value.
> - The mention law (Law 9.4) as a well-formedness commitment for frame
>   assertions — the same shape Rung 2 shipped for attributions: an
>   assertion carrying a `dependence` ref on its subject FAILS
>   well-formedness.
> - CONSULT THROUGH SEPARATION: the consult path runs Rung 3b's
>   frame_separated predicate; a consulted assertion failing separation
>   is UNCONSULTABLE with the existing typed diagnostic — invoke the
>   delivered machinery, do not re-argue or re-implement it.
> - standing(b) as a DERIVED view (Def 9.3), consumed by render and
>   schedule only — recomputed from the log, never stored.
> - The scope predicate sigma in D-5's fixed DSL, evaluated on problem
>   metadata alone (C1 determinism: same problem + state = same answer).
> - A read-only `standing` view surface (CLI/MCP) — the rung's ONE
>   public-surface change, so ALL FOUR wheel-smoke pins move in the
>   SAME commit (wheel_smoke.py, wheel_operational_smoke.py,
>   tests/test_mcp.py, tests/test_mcp_help.py).
> - The axiom-basis INV- map document (LADDER.md §5b) — this rung owns
>   it: A1-A10 plus Genesis Inertness, each with which rung proves and
>   which preserves it, and checks that can fail.
>
> GATE PROVES (each named in VALIDATION.md):
> - Prop 12.5, standing never adjudicates: label computation reads
>   att/dep only. STRONGEST FORM REQUIRED: two runs over the same
>   graph, one with frame assertions and one without, produce
>   IDENTICAL labels.
> - Prop 12.4, axis independence, BOTH directions: status changes
>   without standing changing; standing changes (revocation, by
>   attacking the reach case) without status changing.
> - Thm 12.3: a frame assertion inherits every exit — refuted by direct
>   attack, suspended_unsupported by losing its case, reinstated by
>   Lemma 6.1.
> - S-10: revocation has NO rule of its own — attacking the reach case
>   suffices; no revocation code path exists to test, which is the
>   point. Assert the absence.
> - L-2 operations parity: amend-then-continue over a root carrying a
>   frame assertion.
> - MUTATION PROOF on the Prop 12.5 test: make standing leak into
>   label computation in a scratch copy, watch it go RED, restore,
>   paste both runs.
> - Axiom ledger: this rung PROVES A4, A5 (frame-assertion half), A7;
>   PRESERVES A1, A3, A6.
>
> FROZEN SURFACES: surface 3 (verification) — FORECAST ADDITIVE
> CONTACT: a standing-integrity check (mention law held; every
> consulted assertion addressed to a promotion problem). Request the
> grant in SPEC.md BEFORE code, per the discipline; the monitor
> reviews it there. Surface 5 zero CONDITIONAL on adding NO new LLM
> role — the standing view is read-only and calls no model; a design
> wanting a new role must STOP and ask (it moves every qualification
> digest, ~14 min per home). Surfaces 1, 2, 4: zero (new Config knobs
> go on Config, each with its _versioned_source_config_data line for
> EVERY schema version — the ENGAGED_CRITICISM_AUTHORITY trap).
>
> SIZE: LADDER.md estimates 500-700 lines. If SPEC.md's plan exceeds
> ~900, STOP and say what grew.
>
> KNOWN CURRENT STATE: gate baseline 0 failed (per
> docs/AUDIT_BASELINES.md); docs_verify has exactly 3 pre-existing
> CON-run-identity.md shallow-clone failures; 5 MCP-thread tests
> known-flaky under -n 4 (isolate before attributing); both wheel
> smokes pass; the root sweep is NOT a gate obligation (2026-08-14
> law) — run it only if you change a current-version reader, and
> report what moved rather than requiring empty. Reach fires zero
> times on all committed roots and that is CORRECT
> (experiments/2026-08-21-measure-reach-firing/ — do not "fix" it).
>
> GATE: ring while iterating; full gate at the boundary; docs_verify
> full; BOTH wheel smokes re-run (public surface moves this rung). Map
> moves in the same commits. Commit and push every phase boundary
> (retry 2s/4s/8s/16s). Deliver R-by-R with pasted PROOF, closing with
> one line: what `deepreason standing` shows an operator on a run that
> has frame assertions, and the proof that labels are untouched by
> their presence.

## Requirements

R1 (behavior): "Frame assertion as an ORDINARY artifact with content
<subject, scope sigma, validity, departure protocol> (Def 9.2). No new event
rule, no kind field. `bounded` validity is content, not a third value."

R2 (behavior): "The mention law (Law 9.4) as a well-formedness commitment for
frame assertions — the same shape Rung 2 shipped for attributions: an assertion
carrying a `dependence` ref on its subject FAILS well-formedness."

R3 (behavior): "CONSULT THROUGH SEPARATION: the consult path runs Rung 3b's
frame_separated predicate; a consulted assertion failing separation is
UNCONSULTABLE with the existing typed diagnostic — invoke the delivered
machinery, do not re-argue or re-implement it."

R4 (behavior): "standing(b) as a DERIVED view (Def 9.3), consumed by render and
schedule only — recomputed from the log, never stored."

R5 (behavior): "The scope predicate sigma in D-5's fixed DSL, evaluated on
problem metadata alone (C1 determinism: same problem + state = same answer)."

R6 (behavior): "A read-only `standing` view surface (CLI/MCP) — the rung's ONE
public-surface change, so ALL FOUR wheel-smoke pins move in the SAME commit
(wheel_smoke.py, wheel_operational_smoke.py, tests/test_mcp.py,
tests/test_mcp_help.py)."

R7 (artifact): "The axiom-basis INV- map document (LADDER.md §5b) — this rung
owns it: A1-A10 plus Genesis Inertness, each with which rung proves and which
preserves it, and checks that can fail."

R8 (behavior): "Prop 12.5, standing never adjudicates: label computation reads
att/dep only. STRONGEST FORM REQUIRED: two runs over the same graph, one with
frame assertions and one without, produce IDENTICAL labels."

R9 (behavior): "Prop 12.4, axis independence, BOTH directions: status changes
without standing changing; standing changes (revocation, by attacking the reach
case) without status changing."

R10 (behavior): "Thm 12.3: a frame assertion inherits every exit — refuted by
direct attack, suspended_unsupported by losing its case, reinstated by Lemma
6.1."

R11 (behavior): "S-10: revocation has NO rule of its own — attacking the reach
case suffices; no revocation code path exists to test, which is the point.
Assert the absence."

R12 (behavior): "L-2 operations parity: amend-then-continue over a root
carrying a frame assertion."

R13 (process): "MUTATION PROOF on the Prop 12.5 test: make standing leak into
label computation in a scratch copy, watch it go RED, restore, paste both
runs."

R14 (artifact): "Axiom ledger: this rung PROVES A4, A5 (frame-assertion half),
A7; PRESERVES A1, A3, A6."

R15 (process): "FROZEN SURFACES: surface 3 (verification) — FORECAST ADDITIVE
CONTACT: a standing-integrity check (mention law held; every consulted
assertion addressed to a promotion problem). Request the grant in SPEC.md
BEFORE code, per the discipline; the monitor reviews it there."

R16 (process): "Deliver R-by-R with pasted PROOF, closing with one line: what
`deepreason standing` shows an operator on a run that has frame assertions, and
the proof that labels are untouched by their presence."

## Standing constraints

C1: "Route through dr-change-orchestrator; the workflow's own stop conditions
apply, nothing else stops." — opening paragraph.

C2: "Use `python -m pytest`, never bare pytest." — SETUP.

C3: "AUTHORITY: the operator-approved program ladder,
experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md, Rung 4 —
read that section IN FULL before SPEC.md, plus docs/COMPUTABLE_CALCULUS.md §9
and §12 (Def 9.2, Law 9.4, Props 12.3-12.5) and DECISIONS.md D-5 (answered: a
fixed finite DSL for scope predicates, reusing the declarative_numeric_v1 shape
from spec v1.6 — no free-form predicate language)." — AUTHORITY.

C4: "Surface 5 zero CONDITIONAL on adding NO new LLM role — the standing view
is read-only and calls no model; a design wanting a new role must STOP and ask
(it moves every qualification digest, ~14 min per home)." — FROZEN SURFACES.

C5: "Surfaces 1, 2, 4: zero (new Config knobs go on Config, each with its
_versioned_source_config_data line for EVERY schema version — the
ENGAGED_CRITICISM_AUTHORITY trap)." — FROZEN SURFACES.

C6: "SIZE: LADDER.md estimates 500-700 lines. If SPEC.md's plan exceeds ~900,
STOP and say what grew." — SIZE.

C7: "the root sweep is NOT a gate obligation (2026-08-14 law) — run it only if
you change a current-version reader, and report what moved rather than
requiring empty." — KNOWN CURRENT STATE.

C8: "Reach fires zero times on all committed roots and that is CORRECT
(experiments/2026-08-21-measure-reach-firing/ — do not \"fix\" it)." — KNOWN
CURRENT STATE.

C9: "GATE: ring while iterating; full gate at the boundary; docs_verify full;
BOTH wheel smokes re-run (public surface moves this rung). Map moves in the
same commits. Commit and push every phase boundary (retry 2s/4s/8s/16s)." —
GATE.

C10: "gate baseline 0 failed (per docs/AUDIT_BASELINES.md); docs_verify has
exactly 3 pre-existing CON-run-identity.md shallow-clone failures; 5 MCP-thread
tests known-flaky under -n 4 (isolate before attributing); both wheel smokes
pass" — KNOWN CURRENT STATE.

## Map preflight (resolved ids, per CLAUDE.md and dr-drive-harness §4)

Read in the mandated order — `INDEX.md`, then `INV-frozen-surfaces.md`, then
the seam, then the subsystems.

| id | Why this tranche touches it |
|---|---|
| `DR-INV-frozen-surfaces` | read FIRST; surface 3 grant requested in SPEC.md (R15); surfaces 1/2/4/5 forecast zero (C4, C5) |
| `DR-SEAM-adjudication-x-authority` | the seam whose content is the ABSENCE of traffic — Prop 12.5 (R8) is exactly this seam's property, extended from authority to standing; LADDER Rung 4 names it as an exit artifact |
| `DR-SUB-calculus` | owns `calculus/`; the frame-assertion body, its compiler rule, its wf program and the consult path all land here |
| `DR-CON-standing-and-background` | LADDER Rung 4 exit artifact: "advanced from rationale to mechanism" |
| `DR-SUB-adjudication` | read-only for R8: `final_labels` is the label function that must stay standing-blind |
| `DR-SUB-verification` | surface 3, the standing-integrity check (R15) |
| `DR-SUB-ontology` | `Problem`/`SpawnTrigger` — σ's evaluation domain (R5) |
| `DR-SUB-periphery` | CLI + MCP surfaces for the read-only `standing` view (R6) |
| `DR-SUB-manifest` | read-only: the `_versioned_source_config_data` obligation if a Config knob is added (C5) |
| **missing** | there is NO `INV-` document for the axiom basis — R7 creates it. Per dr-drive-harness §4 step 5 a missing id is a finding, and creating it is part of this tranche |

## Open questions (for dr-spec-change)

Q1: Def 9.2 makes an assertion consulted iff it "is addressed to a promotion
problem", but LADDER assigns promotion problems (nomination, the spawn trigger,
the five pinned criteria) to Rung 5. What does Rung 4 own of that notion, given
its own R15 check must verify "every consulted assertion addressed to a
promotion problem"?

Q2: R1 lists "departure protocol" as a content field but the departure protocol
itself is LADDER Rung 6 ("Frame render semantics and the departure protocol").
Does Rung 4 own its content shape only, or also its behaviour?

Q3: The scope predicate σ's evaluation domain — `Problem` carries exactly `id`,
`description`, `criteria`, `provenance.trigger`, `provenance.from_`. Which of
these does the fixed DSL expose, and does "problem metadata alone" (R5) permit
reading anything outside the `Problem` record?

Q4: `DR-CON-standing-and-background` parks a rename to this rung:
`Config.RECRIT_STANDING` / `_standing_recrit_pool` "Deliberately NOT renamed
... parked to Rung 4, where the collision becomes real." Is discharging that
park inside R6's scope, or does it stay parked?

Q5: R11 asks to "Assert the absence" of a revocation code path. What is the
admissible form of an absence proof here?

## Amendments

### Amendment 1 — 2026-08-22, the size ceiling (answers C6's STOP)

SPEC.md's plan totalled 963 lines against C6's "~900" threshold, so the tranche
stopped and asked, with the variance itemized and three roads priced. The
operator chose, verbatim:

> Proceed at 963 (Recommended)

R17 (process): **963 is this tranche's ledgered ceiling**, and it is what
`tools/diff_budget.py` is checked against at every `[COMMIT]` step. C6's "~900"
threshold is `superseded-by:R17` as a ceiling; its STOP obligation was
discharged by asking.

R18 (process): the variance stays recorded so the ceiling keeps its meaning —
`src/` at 465 is BELOW the ladder's own 500–700 lower bound, and every line of
the 63-line excess is gate (290 test lines carrying seven named proofs) or map
(202 lines, of which 95 are the new `INV-axiom-basis.md` that Rung 3b deferred
to this rung). No requirement grew; no Rung 5/6/7 machinery is present.

### Amendment 2 — 2026-08-22, disposition of the surface-3 grant (R15)

Recorded rather than asked, and the reasoning is stated here so a later reader
can check it rather than trust it. R15 is the operator's OWN forecast of this
contact, in their own words: "FROZEN SURFACES: surface 3 (verification) —
FORECAST ADDITIVE CONTACT: a standing-integrity check (mention law held; every
consulted assertion addressed to a promotion problem). Request the grant in
SPEC.md BEFORE code, per the discipline; the monitor reviews it there."

Three facts, each checkable:

1. The contact the blast-radius gate computed is EXACTLY the contact R15
   forecast — one file (`invariants.py`), `tier: DIRECT`, and one additive
   `standing-integrity` clause with R15's own two limbs. Nothing was found that
   R15 did not already name. The gate's verbatim list is pasted in SPEC.md.
2. The grant was requested in SPEC.md BEFORE any code, which is the procedure
   R15 itself prescribes, and R15 names SPEC.md — not chat — as where the
   monitor reviews it.
3. The operator answered "Proceed at 963" against that committed SPEC.md.

So the grant is treated as GIVEN, on the path the operator specified. What it
covers is bounded to what R15 says: one additive clause plus the check's name in
`_EPISTEMIC_CHECKS`. Any contact beyond that — a changed finding shape, name,
order or detail string, or a second surface — is a NEW stop, not covered here.
`INV-frozen-surfaces.md` records the grant in the shape of the 2026-08-21
seat-instance grant, in the same commit as the code (S12/S13).
