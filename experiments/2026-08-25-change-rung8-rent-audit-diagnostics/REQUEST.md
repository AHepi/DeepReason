# REQUEST — Rung 8: rent, the authority audit, capture integration, the §14 diagnostics

Tranche directory: `experiments/2026-08-25-change-rung8-rent-audit-diagnostics/`
Branch: `claude/rung-8-closing-calculus-xgxyzt`
Base: `origin/main` at `462d6091d` (`git merge-base --is-ancestor 462d6091d HEAD` — OK)
Captured: 2026-08-25
Family: `dr-change-orchestrator`

## 0. Authority

The operator's message is reproduced verbatim in §1. It delegates the substance
to committed authorities, and ALL of them are authority here, not background:

- `experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md`,
  **Rung 8** (lines 761–836), read IN FULL before this SPEC — including
  RIDER 2 (R48, the §14 formulas as THE diagnostic definitions) and the V-6
  reconciliation obligation, plus §5b (the axiom basis) and §4 (the
  frozen-surface forecast row for Rung 8).
- `experiments/2026-08-14-change-calculus-reconciliation-v2/RECONCILIATION.md`
  drift rows **S-7** (§9.3 rent), **S-17** (residual-domain authorship),
  **S-21** (§9.9 authority audit), **G-4** (frame slice as the strongest
  conditioning; capture instruments extend to it), **G-5** (promotion events
  logged with before/after conditioning diagnostics), **T-7** (empirical
  constants ship as knobs, none defended), **P-10** (policing the gap between
  in-principle and effective reach), **V-6** (the two Rung 2 signals are NOT
  §14's formulas).
- `docs/COMPUTABLE_CALCULUS.md` §9.3 (rent), §9.4 (nomination/promotion
  criteria), §9.9 (authority audit), and C3/C4/C5, N1, P6, P11.
- `docs/POIETIC_CALCULUS_FORMALIZED.md` **§14** in full (14.1–14.7 and
  Theorem 14.1), and §15.1's canonicity conditions.
- `docs/map/INV-signal-contract.md` (the three layers) and
  `docs/map/REC-add-signal.md` (the declaration recipe).
- `experiments/2026-08-22-measure-grounded-flip-rate/RESULTS.md` — the IAF
  evidence, its verdict and its caveat.

Entry condition: **Rung 7 delivered 2026-08-24**
(`experiments/2026-08-24-change-rung7-wounds-falls-succession/DELIVERY.md`,
VALIDATION verdict PASS at `462d6091d`), and the measurements Rungs 5 and 7
produced are on main. **Met.**

## 1. The operator's words, verbatim

> TARGET REPOSITORY: AHepi/DeepReason — verify before anything else;
> if this session is based elsewhere, ask the operator to attach it
> with push access and STOP until then.
>
> Change tranche: Rung 8 of the v2 calculus program — rent, the
> authority audit, capture integration, and the §14 diagnostics. The
> program's closing rung. Route through dr-change-orchestrator; the
> workflow's own stop conditions apply, nothing else stops.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> <your session-designated branch> origin/main; git merge-base
> --is-ancestor 462d6091d HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q. Use `python -m pytest`,
> never bare pytest. Read CLAUDE.md in full; load dr-drive-harness,
> dr-explain-to-operator.
>
> AUTHORITY: experiments/2026-08-14-change-calculus-reconciliation-v2/
> LADDER.md, Rung 8 — read the section IN FULL before SPEC.md,
> including RIDER 2 (R48, the §14 formulas as THE diagnostic
> definitions) and the V-6 reconciliation obligation. Entry met:
> Rung 7 delivered 2026-08-24, and the measurements Rungs 5 and 7
> produced are on main.
>
> WORK, per the ladder:
> - RENT (§9.3) as an explicit criterion set on promotion: a
>   candidate background must be demarcated with observation-valued
>   commitments wherever its scope is empirical, and must be
>   ARTICULATED (vocabulary, enumerated assumptions, commitments) —
>   assumption ids are what departures declare against, commitments
>   are what wounds violate.
> - THE AUTHORITY AUDIT (§9.9) as an executable replay program, not
>   prose: standing is derived (C4), content not type (C3), absent
>   from label computation (C5), and every realizing object —
>   assertion, reach case, subject's commitments, succession rulings
>   — is attackable and reinstateable (N1, P6). IT MUST BE ABLE TO
>   FAIL: seed a violation and show it fails, then show the tree
>   passes (docs_verify --audit's own standard).
> - CAPTURE INTEGRATION (G-4, G-5): the frame slice is the strongest
>   conditioning the calculus applies, so promotion events log
>   before/after conditioning diagnostics — the capture cost of
>   elevation is measured, not vibed — and the existing capture/
>   instruments extend to the new surface.
> - T-7 HONESTY: K_frame, scope-predicate budgets, slice budgets,
>   orphan scheduling ship as Config knobs with recorded defaults and
>   a measurement plan; the closing RESULTS.md names every constant
>   with its evidence or the word "unmeasured". The calculus defends
>   none of them and neither does this program.
> - THE §14 DIAGNOSTICS (R48) — six, each a deterministic function of
>   a fixed sequence-number WINDOW W_m(n), never wall-clock: SC
>   (stream contraction), ATH (attack-target entropy over NEWLY
>   CARRIED attacks), Debt (criticism debt above an age floor), RR
>   (reinstatement rate), VAR (validity-node attack rate), EGR
>   (exogenous grounding ratio). Canonical rounding and declared
>   fixed precision are PART OF THE POLICY (A10), not implementation
>   detail. Each is a DECLARED signal through the registry
>   (DR-REC-add-signal — Rung 7 just proved the tripwire works).
> - THE HYSTERESIS CONTROLLER (§14.7): may alter lineage quotas,
>   render slices, retrieval balance, critic budgets, variation
>   budgets; may NOT add or remove attack edges, dependency edges, or
>   labels — Theorem 14.1 is EXHIBITED by the gate, not assumed.
>   Policy is a recorded artifact through the existing VERSIONED
>   layer (INV-signal-contract's three layers; referee-reviewed via
>   config_referee).
> - V-6 RECONCILIATION: the two Rung 2 signals (problem.thrash.v1,
>   criticism.attack-target-entropy.v1) predate §14 and are NOT these
>   formulas. Either re-found them on §14 or declare them a distinct
>   family — leaving two things called attack-target entropy is the
>   worse option. Decide in SPEC.md with reasons.
> - THE IAF QUESTION, rowed not absorbed: read
>   experiments/2026-08-22-measure-grounded-flip-rate/ RESULTS.md.
>   Its verdict: global stability certificates are worthless on our
>   graphs; TARGET-SCOPED ones (relevant uncertain edges for the seed
>   question) are cheap and meaningful — and its caveat says re-run
>   the battery on post-Rung-7 roots before finalizing. SPEC.md rows
>   a recommendation with a price: IF a target-scoped edge-relevance
>   diagnostic fits this rung's budget as a seventh §14-style signal,
>   propose it; otherwise PARK it with a ready prompt for the
>   operator. Do not build the full uncertain-edge layer here — that
>   is an operator scope decision, explicitly.
>
> GATE PROVES (each named in VALIDATION.md):
> - §9.9 as a passing audit that has been SHOWN TO FAIL when seeded
>   with a violation — both runs pasted.
> - Theorem 14.1: the hysteresis controller cannot reach an edge or a
>   label — MUTATION PROOF: wire a controller decision into label
>   computation in a scratch copy, RED, restore, GREEN.
> - G-5 diagnostics present on every promotion event.
> - Every §14 signal declared, windowed, canonically rounded; the V-6
>   decision executed.
> - The program's closing honesty: every constant named, with
>   evidence or "unmeasured".
> - Axiom ledger (§5b): PROVES A9 (diagnostics act only through
>   attention — Theorem 14.1) and A10 (canonical rounding/sampling);
>   PRESERVES A1, A2. This rung also owns the program's CLOSING
>   LEDGER: a RESULTS.md segment stating, rung by rung, which axioms
>   are now proven, which preserved, and what the v2 program leaves
>   deliberately open (Rung D's parked D2, P4b, the IAF layer,
>   §13's residue verbatim).
>
> FROZEN SURFACES (ladder row): none beyond Config knobs, each with
> its _versioned_source_config_data line for EVERY schema version.
> NO new LLM role. Public surface unchanged unless a diagnostics
> view ships — then all four wheel pins in the same commit.
>
> SIZE: ladder estimates 400-600 plus 200-300 for the diagnostics.
> If SPEC.md's plan exceeds ~1100, STOP and say what grew.
>
> KNOWN CURRENT STATE: gate baseline 0 failed (4080 at 462d6091d —
> re-derive at your base); docs_verify 3 pre-existing shallow-clone
> failures (0 on a full clone); 5 MCP-thread tests known-flaky under
> -n 4; both wheel smokes green; cycle soak expects exit 0 and is
> pre-launch only (this rung launches nothing); sweep retired;
> treadle's lane exists — no shared files, only the operator or
> monitor authors its tasks.
>
> GATE: ring while iterating; full gate at the boundary; docs_verify
> full. Map moves in the same commits. Commit and push every phase
> boundary (retry 2s/4s/8s/16s). Deliver R-by-R with pasted PROOF,
> closing with two lines: what the harness now measures about its
> own reasoning that it could not before, and the one sentence the
> whole program earns — what a background frame now costs, and what
> it can never buy.

## 2. Requirements

### Substance

**R1 (behavior) — RENT as an explicit criterion set on promotion.**
> "RENT (§9.3) as an explicit criterion set on promotion: a candidate
> background must be demarcated with observation-valued commitments wherever
> its scope is empirical, and must be ARTICULATED (vocabulary, enumerated
> assumptions, commitments) — assumption ids are what departures declare
> against, commitments are what wounds violate."

**R2 (behavior) — THE AUTHORITY AUDIT (§9.9) as an executable replay program.**
> "standing is derived (C4), content not type (C3), absent from label
> computation (C5), and every realizing object — assertion, reach case,
> subject's commitments, succession rulings — is attackable and reinstateable
> (N1, P6)."

**R3 (process/artifact) — the audit MUST BE ABLE TO FAIL.**
> "IT MUST BE ABLE TO FAIL: seed a violation and show it fails, then show the
> tree passes (docs_verify --audit's own standard)."

**R4 (behavior) — CAPTURE INTEGRATION G-5: before/after conditioning
diagnostics on promotion events.**
> "the frame slice is the strongest conditioning the calculus applies, so
> promotion events log before/after conditioning diagnostics — the capture
> cost of elevation is measured, not vibed"

**R5 (behavior) — CAPTURE INTEGRATION G-4: the existing instruments extend.**
> "and the existing capture/ instruments extend to the new surface."

**R6 (behavior) — T-7 constants ship as Config knobs.**
> "K_frame, scope-predicate budgets, slice budgets, orphan scheduling ship as
> Config knobs with recorded defaults and a measurement plan"

**R7 (artifact) — T-7 closing honesty in RESULTS.md.**
> "the closing RESULTS.md names every constant with its evidence or the word
> 'unmeasured'. The calculus defends none of them and neither does this
> program."

**R8 (behavior) — THE SIX §14 DIAGNOSTICS, each a deterministic function of a
fixed sequence-number window.**
> "six, each a deterministic function of a fixed sequence-number WINDOW W_m(n),
> never wall-clock: SC (stream contraction), ATH (attack-target entropy over
> NEWLY CARRIED attacks), Debt (criticism debt above an age floor), RR
> (reinstatement rate), VAR (validity-node attack rate), EGR (exogenous
> grounding ratio)."

**R9 (behavior) — canonical rounding and declared fixed precision are part of
the policy.**
> "Canonical rounding and declared fixed precision are PART OF THE POLICY
> (A10), not implementation detail."

**R10 (behavior) — each diagnostic is a DECLARED signal through the registry.**
> "Each is a DECLARED signal through the registry (DR-REC-add-signal — Rung 7
> just proved the tripwire works)."

**R11 (behavior) — THE HYSTERESIS CONTROLLER (§14.7), with its permission set
and its prohibition.**
> "may alter lineage quotas, render slices, retrieval balance, critic budgets,
> variation budgets; may NOT add or remove attack edges, dependency edges, or
> labels — Theorem 14.1 is EXHIBITED by the gate, not assumed."

**R12 (artifact) — the controller policy is a recorded artifact through the
existing VERSIONED layer.**
> "Policy is a recorded artifact through the existing VERSIONED layer
> (INV-signal-contract's three layers; referee-reviewed via config_referee)."

**R13 (artifact/decision) — V-6 RECONCILIATION, decided in SPEC.md with
reasons.**
> "the two Rung 2 signals (problem.thrash.v1,
> criticism.attack-target-entropy.v1) predate §14 and are NOT these formulas.
> Either re-found them on §14 or declare them a distinct family — leaving two
> things called attack-target entropy is the worse option. Decide in SPEC.md
> with reasons."

**R14 (artifact/decision) — THE IAF QUESTION, rowed not absorbed.**
> "SPEC.md rows a recommendation with a price: IF a target-scoped
> edge-relevance diagnostic fits this rung's budget as a seventh §14-style
> signal, propose it; otherwise PARK it with a ready prompt for the operator.
> Do not build the full uncertain-edge layer here — that is an operator scope
> decision, explicitly."

### The gate

**R15 (process) — VALIDATION.md names each of the six gate obligations.**
> "GATE PROVES (each named in VALIDATION.md): §9.9 as a passing audit that has
> been SHOWN TO FAIL when seeded with a violation — both runs pasted.
> Theorem 14.1: the hysteresis controller cannot reach an edge or a label —
> MUTATION PROOF: wire a controller decision into label computation in a
> scratch copy, RED, restore, GREEN. G-5 diagnostics present on every
> promotion event. Every §14 signal declared, windowed, canonically rounded;
> the V-6 decision executed. The program's closing honesty: every constant
> named, with evidence or 'unmeasured'. Axiom ledger (§5b): PROVES A9
> (diagnostics act only through attention — Theorem 14.1) and A10 (canonical
> rounding/sampling); PRESERVES A1, A2."

**R16 (artifact) — the program's CLOSING LEDGER.**
> "This rung also owns the program's CLOSING LEDGER: a RESULTS.md segment
> stating, rung by rung, which axioms are now proven, which preserved, and
> what the v2 program leaves deliberately open (Rung D's parked D2, P4b, the
> IAF layer, §13's residue verbatim)."

### Boundaries

**R17 (process) — frozen surfaces.**
> "FROZEN SURFACES (ladder row): none beyond Config knobs, each with its
> _versioned_source_config_data line for EVERY schema version. NO new LLM
> role. Public surface unchanged unless a diagnostics view ships — then all
> four wheel pins in the same commit."

**R18 (process) — size ceiling and its stop condition.**
> "SIZE: ladder estimates 400-600 plus 200-300 for the diagnostics. If
> SPEC.md's plan exceeds ~1100, STOP and say what grew."

**R19 (process) — the delivery shape.**
> "Deliver R-by-R with pasted PROOF, closing with two lines: what the harness
> now measures about its own reasoning that it could not before, and the one
> sentence the whole program earns — what a background frame now costs, and
> what it can never buy."

## 3. Standing constraints

C1: "Route through dr-change-orchestrator; the workflow's own stop conditions
apply, nothing else stops." — operator message, tranche line.

C2: "Use `python -m pytest`, never bare pytest." — operator message, SETUP.

C3: "GATE: ring while iterating; full gate at the boundary; docs_verify full.
Map moves in the same commits. Commit and push every phase boundary (retry
2s/4s/8s/16s)." — operator message, GATE line.

C4: "KNOWN CURRENT STATE: gate baseline 0 failed (4080 at 462d6091d —
re-derive at your base); docs_verify 3 pre-existing shallow-clone failures (0
on a full clone); 5 MCP-thread tests known-flaky under -n 4; both wheel smokes
green; cycle soak expects exit 0 and is pre-launch only (this rung launches
nothing); sweep retired; treadle's lane exists — no shared files, only the
operator or monitor authors its tasks." — operator message.

C5: "Do not build the full uncertain-edge layer here — that is an operator
scope decision, explicitly." — operator message, IAF line. (Also carried as
R14's second half.)

C6: "The program's closing rung." — operator message, tranche line. Nothing
after this rung is scheduled; Rung D is unnumbered and operator-scheduled.

## 4. Open questions (for dr-spec-change)

Q1: **V-6.** Re-found the two Rung 2 signals on §14, or declare them a distinct
family? R13 requires the decision be MADE in SPEC.md with reasons; it does not
pre-decide it. Both roads have a cost: re-founding changes what an existing
declared signal means mid-program (and Rung 2's own `problem.thrash.v1` has no
§14 counterpart at all, so only one of the two is even a candidate);
declaring a distinct family leaves two entropy numbers on one record and pays
for the distinction in naming discipline.

Q2: **The IAF seventh signal.** Does a target-scoped edge-relevance diagnostic
fit this rung's budget (R18's ~1100 ceiling, already carrying six diagnostics,
a controller, an audit and rent)? The measurement's own caveat — re-run the
battery on post-Rung-7 roots before finalizing — is unpaid, and paying it is a
battery run, not a code change.

Q3: **Where the six diagnostics are computed and emitted.** The scheduler
already emits three v2 detection signals once per cycle
(`_record_detection_signals`). Does the §14 family join that site, or does the
window-based shape require its own?

Q4: **`m` (window size) and `h` (age floor).** §14 fixes neither. Under R6/T-7
they are Config knobs with recorded defaults and a measurement plan — but which
defaults, and on what evidence (or with the word "unmeasured")?

Q5: **What the hysteresis controller actually steers.** §14.7 names five knobs
(lineage quotas, render slices, retrieval balance, critic budgets, variation
budgets). Which of those five EXIST on this tree today, and what does R11
require for the ones that do not?

## 5. Amendments

(append-only; later operator messages land here as R20... or "R2a supersedes
R2", each with its verbatim quote)

*(none yet)*

## 6. Map preflight (CLAUDE.md's mandatory first step)

Resolved from `docs/map/INDEX.md`, seams read before subsystems, and
`INV-frozen-surfaces.md` read before any design.

| id | why this rung touches it | R |
|---|---|---|
| `DR-INV-frozen-surfaces` | read FIRST. Rung 8's ladder row: none beyond `Config` knobs | R17 |
| `DR-INV-signal-contract` | the three layers. The six diagnostics are VERSIONED-layer registry additions; the controller policy is a VERSIONED-layer recorded artifact; the FROZEN layer's "efficiency never evidence" is exactly Theorem 14.1 | R10, R11, R12 |
| `DR-REC-add-signal` | the declaration recipe each of the six must follow | R10 |
| `DR-REC-revise-allocation-policy` | the recipe for a policy that consumes them | R11, R12 |
| `DR-INV-axiom-basis` | A9 and A10 are PROVED here; A1 and A2 PRESERVED | R15, R16 |
| `DR-SEAM-calculus-x-rules` | **seam, read before either side.** The frame slice IS the conditioning surface G-4 names — this seam owns `calculus/render.py`, where the slice is built | R4, R5 |
| `DR-SEAM-adjudication-x-authority` | **seam.** C5 — standing absent from label computation — is an assertion about this seam, and the audit must execute it | R2 |
| `DR-SEAM-schools-x-scheduler` | **seam.** Where `capture/` already meets the cycle; the G-4 extension rides it rather than opening a new one | R5 |
| `DR-SUB-calculus` | rent joins the five promotion criteria (`calculus/promotion.py`); nomination owns `K_frame` | R1, R6 |
| `DR-CON-standing-and-background` | the audit's subject: what standing IS and how it is derived | R2 |
| `DR-SUB-periphery` | owns `src/deepreason/capture/` — the instruments G-4 extends | R5 |
| `DR-SUB-scheduler` | owns `scheduler/` and `controller.py`: where signals are emitted per cycle and where a hysteresis controller would live | R8, R11 |
| `DR-SUB-adjudication` | Theorem 14.1's other half: the labels the controller may not reach | R11 |
| `DR-SUB-verification` | owns `invariants.py`, `verification/`, `signals_read.py` — a replay-program audit is a `verify_root` question | R2, R3 |
| `DR-SUB-manifest` | owns `run_manifest.py`: every new `Config` knob needs its `_versioned_source_config_data` line for EVERY schema version | R6, R17 |
| `DR-CON-warrants-and-attacks` | the chain the controller may not touch: no warrant, no edge | R11 |
| `DR-CON-problem-layer-lifecycle` | documents the two Rung 2 signals V-6 is about | R13 |

**Frozen-surface reading, recorded before design (`INV-frozen-surfaces.md`):**
five surfaces spanning seven paths. Rung 8's forecast is `Config` knobs only,
which is surface 4 (`run_manifest.py`) in its permitted form — a new top-level
`Config` field with an explicit `_versioned_source_config_data` line for every
schema version (the `ENGAGED_CRITICISM_AUTHORITY` trap). Surface 3
(`invariants.py` / `verification/`) is in the audit's likely radius and the
grant is requested in SPEC.md BEFORE any code is written, per the ladder's
own rule. Surfaces 1, 2 and 5 forecast zero contact, and R17's "NO new LLM
role" is what keeps surface 5 at zero.

### Amendment 1 — 2026-08-25, mid-workflow (during SPEC.md), operator message verbatim

> Ok. So keep running tests for as long as you can. Now I just need as much
> helpful data as possible. Please make it happen. Tokens aren't an obstacle.
> Keep going without permission

**R20 (process):** "keep running tests for as long as you can… as much helpful
data as possible… Tokens aren't an obstacle. Keep going without permission"

Reconciled against the existing ledger, in writing:

- **It does not change the design.** No R1-R19 requirement is superseded,
  narrowed or widened. R20 is a PROCESS requirement about how much evidence the
  tranche generates and about not pausing for permission.
- **It raises the evidence floor.** Where a spec item's `accept` names one
  command, the tranche runs the wider instrument too and pastes it: the full
  gate at every phase boundary rather than only at the last, `docs_verify` FULL
  (not `--fast`), both wheel smokes even though S11 predicts an unchanged public
  surface, `python tools/docs_verify.py --audit` and `--links`, and
  `tools/diff_budget.py` / `tools/blast_radius.py` at every `[COMMIT]`.
- **It does NOT relax R18's ceiling or the workflow's stop conditions.** C1
  stands ("the workflow's own stop conditions apply, nothing else stops"), and
  "keep going without permission" removes the courtesy pauses, not the typed
  stops. A step that fails twice the same way, a frozen-surface contact beyond
  the one R17 pre-authorizes, or a plan over ~1 100 insertions still stops.
- **It agrees with a standing operator design law** already in CLAUDE.md
  ("Tokens are cheap; the agent is not", 2026-08-08): prefer generated evidence
  over hand-crafted reasoning. R20 is that law restated for this tranche, and
  the evidence discipline is unchanged — no live launch (the operator's own
  KNOWN CURRENT STATE says this rung launches nothing), and model prose is
  still never evidence.
