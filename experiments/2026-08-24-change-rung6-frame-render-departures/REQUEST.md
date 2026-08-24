# REQUEST — Rung 6: frame render semantics and the departure protocol

Tranche directory: `experiments/2026-08-24-change-rung6-frame-render-departures/`
Branch: `claude/frame-render-departure-protocol-u4dnn7`
Base: `origin/main` at `7ad1b273f` (`git merge-base --is-ancestor 7ad1b273f HEAD` — OK)
Captured: 2026-08-24
Family: `dr-change-orchestrator`

## 0. Authority

The operator's message is reproduced verbatim in §1. It delegates the
substance to two committed authorities, and BOTH are authority here, not
background:

- `experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md`,
  **Rung 6** (lines 634-710), read in full including **RIDER 2 (R44)**.
- Three committed research notes, each cited by section:
  `docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md` (N1),
  `docs/RESEARCH_CONVERGENCE_LOOPS_2026-08-22.md` (N2),
  `docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` **Q1** (N3).

Entry condition: Rung 5 delivered 2026-08-24
(`experiments/2026-08-24-change-rung5-promotion-criteria/DELIVERY.md`) —
promotion problems, strong succession, the knowledge view. **Met.**

## 1. The operator's words, verbatim

> TARGET REPOSITORY: AHepi/DeepReason — verify before anything else;
> if this session is based elsewhere, ask the operator to attach it
> with push access and STOP until then.
>
> Change tranche: Rung 6 of the v2 calculus program — frame render
> semantics and the departure protocol. Route through
> dr-change-orchestrator; the workflow's own stop conditions apply,
> nothing else stops.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> <your session-designated branch> origin/main; git merge-base
> --is-ancestor 7ad1b273f HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q. Use `python -m pytest`,
> never bare pytest. Read CLAUDE.md in full; load dr-drive-harness,
> dr-explain-to-operator.
>
> AUTHORITY: experiments/2026-08-14-change-calculus-reconciliation-v2/
> LADDER.md, Rung 6 — read the section IN FULL before SPEC.md,
> including RIDER 2 (R44, the third exit grade). Entry condition met:
> Rung 5 delivered 2026-08-24 (promotion problems, strong succession,
> the knowledge view). ALSO BINDING, from the committed research
> notes — read each cited section before SPEC.md and ledger all three
> as requirements:
> (N1) docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md — OMIT, DON'T
>      REDACT: provenance-shaped fields are ABSENT from rendered
>      packs, never blanked or tagged "redacted" (a present-but-empty
>      provenance slot draws MORE judge attention than a populated
>      one). A check pins that the renderer emits no empty provenance
>      slots.
> (N2) docs/RESEARCH_CONVERGENCE_LOOPS_2026-08-22.md — THE PACK
>      RENDERER IS THE MEMORY POLICY: content that must keep acting
>      (standing attackers, active criticism) must keep RENDERING
>      within the horizon, and persistence is asserted AT THE
>      TERMINAL step, never at injection. The record forgetting
>      nothing does not make the pack remember.
> (N3) docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md Q1 — position in
>      the pack is a WEAK lever (standing rules decay in-context
>      regardless of placement): where a frame obligation can be a
>      deterministic gate the pack must pass, build the gate; render
>      position is a hedge, recorded as such, not a mechanism.
>
> WORK, per the ladder:
> - THE FRAME SLICE: for every consulted assertion whose scope
>   matches the problem, the pack carries the subject's articulation
>   digest (compressed, expandable by view) AND the subject's
>   standing attackers — wounds render in-frame, in every pack in
>   scope: "the frame ships its own crisis."
> - DEPARTURES: the slice carries the standing directive that
>   departures are permitted and must be declared as a list of broken
>   assumption/commitment ids. Declaration removes the
>   hidden-premise criticism's target; the declaration is itself
>   attackable. NOTHING scores departures, and scope predicates
>   NEVER read departure declarations — a departing conjecture
>   cannot be exiled from the frame it is criticizing (L-4, the R-g
>   guardrail: formalism-optional's sibling).
> - P4's RENDER HALF: the same deterministic section allocation
>   settles what an inherited-context problem may cite (the 0-of-36
>   finding P4 measured). P4b (quote wording) stays parked — do not
>   absorb it.
> - THE THIRD EXIT GRADE (R44): do NOT adopt FrameDecisive. Three
>   grades, keyed to the label: fall (R — the assertion itself
>   defeated), revocation (SU — accreditation lost), contestation
>   (S — unresolved attack, nobody has won). fall and revocation are
>   provably disjoint; contestation is what the two-exit claim
>   silently assumed away. The render distinguishes all three and
>   never rounds contestation to either neighbour.
>
> GATE PROVES (each named in VALIDATION.md):
> - ALL THREE GRADES REACHABLE, each by its own registration, and the
>   render distinguishes them — the anti-FrameDecisive check.
> - L-5 / Prop 12.5 AT THE RENDER LAYER, strongest form: two runs
>   over the same graph, one with the frame slice and one without,
>   produce IDENTICAL labels. A slice that changed a label would be a
>   seat deciding evidence. MUTATION PROOF: make the slice leak into
>   adjudication in a scratch copy, RED, restore, GREEN, paste both.
> - L-4: an undeclared departure is criticizable; a declared one
>   carries NO penalty in rank, admission, or acceptance — assert the
>   absence.
> - C1: the slice is a deterministic render — same problem and state
>   produce byte-identical packs.
> - N1's check: no empty provenance-shaped slot in any emitted pack.
> - N2's check: a standing attacker present at cycle k still renders
>   at the terminal cycle of a multi-cycle offline run — persistence
>   asserted at terminal.
> - Token economy: the slice fits the pack budget; the allocation is
>   logged; what the budget drops is DISCLOSED, not silent (no
>   silent caps).
> - Axiom ledger (§5b): PROVES A9's render half (render acts only
>   through attention); PRESERVES A3, A4, A10.
>
> FROZEN SURFACES (ladder row): surface 5 zero ONLY because no new
> LLM role is added — the ladder marks this the rung most tempted to
> add one; if articulation digests want a summarizer variant, REUSE
> the existing summarizer role, and a design wanting a new role must
> STOP and ask. Surfaces 1-4 zero (Config knobs get their
> versioned-source lines). Public surface: IF a frame/pack inspection
> view ships, ALL FOUR wheel pins move in the same commit; if none
> ships, say so and the smokes are not owed.
>
> SIZE: ladder estimates 300-450 lines plus 60-100 for the third
> grade. If SPEC.md's plan exceeds ~700, STOP and say what grew.
>
> KNOWN CURRENT STATE: gate baseline 0 failed (3939 at 7ad1b273f —
> re-derive at your base); docs_verify 3 pre-existing
> CON-run-identity.md shallow-clone failures (0 on a full clone); 5
> MCP-thread tests known-flaky under -n 4; both wheel smokes green;
> cycle soak expects exit 0 and is pre-launch only (this rung
> launches nothing); sweep retired; treadle's lane exists
> (tools/treadle/, .swarm/) — you share no files with it and only
> the operator or monitor authors its tasks.
>
> GATE: ring while iterating; full gate at the boundary; docs_verify
> full. Map moves in the same commits
> (DR-CON-packs-and-token-economy and DR-SEAM-llm-x-rules per the
> ladder; new checks run before written). Commit and push every
> phase boundary (retry 2s/4s/8s/16s). Deliver R-by-R with pasted
> PROOF, closing with two lines: what a pack now shows about a
> consulted frame that it did not before, and the three ways a frame
> can leave standing without any of them being rounded away.

## 2. Numbered requirements

Each requirement is one obligation. SPEC.md items cite these numbers;
CHECKLIST.md steps cite SPEC items; VALIDATION.md proves per number.

### The work

**R1 — the frame slice.** For every CONSULTED frame assertion whose scope
predicate σ admits the problem, the pack carries a frame slice containing
(a) the subject's **articulation digest**, compressed, expandable by view,
and (b) the subject's **standing attackers**. Wounds render in-frame, in
every pack in scope. Ladder: "the frame ships its own crisis."

**R2 — the departure directive.** The frame slice carries the standing
directive that departures are permitted and must be declared as a list of
the subject's broken assumption / commitment ids.

**R3 — declaration removes the hidden-premise target.** A declared
departure removes the target of the hidden-premise criticism; the
declaration is itself attackable.

**R4 — nothing scores departures.** No penalty (and no reward) in rank,
admission, or acceptance may read a departure declaration. This is L-4,
the R-g guardrail's sibling. Asserted as an ABSENCE.

**R5 — scope predicates never read departure declarations.** A departing
conjecture cannot be exiled from the frame it is criticizing.

**R6 — P4's render half.** The same deterministic section allocation
settles what a problem that INHERITED its context may cite — the general
question P4 raised when it measured 0 of 36 sub-problem prompts carrying
citable evidence blocks. **P4b (the "optionally with a quote" prompt
wording) stays parked and MUST NOT be absorbed.**

**R7 — the third exit grade (RIDER 2 / R44).** Do NOT adopt
`FrameDecisive`. Three grades, keyed to the label: **fall** (`R`,
refuted — the assertion itself defeated), **revocation** (`SU`,
suspended_unsupported — accreditation lost), **contestation** (`S`,
suspended — unresolved attack, nobody has won). fall and revocation are
provably disjoint (Formalization Theorem 8.1). The render distinguishes
all three and **never rounds contestation to either neighbour**.

### The three research notes, binding

**N1 — omit, don't redact.** Provenance-shaped fields are ABSENT from
rendered packs, never blanked or tagged "redacted": a present-but-empty
provenance slot draws MORE judge attention than a populated one
(`RESEARCH_JUDGE_BLINDING_2026-08-22.md`, the placebo-label result,
lines 86-94). **A check pins that the renderer emits no empty provenance
slots.**

**N2 — the pack renderer is the memory policy.** Content that must keep
acting (standing attackers, active criticism) must keep RENDERING within
the horizon, and persistence is asserted AT THE TERMINAL step, never at
injection. "The record forgetting nothing does not make the pack
remember." (`RESEARCH_CONVERGENCE_LOOPS_2026-08-22.md`, Rung 6
consumption point.)

**N3 — position is a weak lever.** Standing rules decay in-context
regardless of placement; the load-bearing repair is a deterministic gate
the pack must pass, not a render position. Where a frame obligation can
be such a gate, build the gate; render position is a hedge, recorded as
such, not a mechanism. (`RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` Q1,
"Repair path — Rung 6".) **N3 SUPERSEDES the render-position half of
N2's consumption point**, by that note's own header; N2's omit-persist
and N1's omit-don't-redact requirements stand unchanged.

### What the gate must prove (each named in VALIDATION.md)

**G1** — all three grades REACHABLE, each by its own registration, and the
render distinguishes them (the anti-`FrameDecisive` check).

**G2** — L-5 / Prop 12.5 at the RENDER layer, strongest form: two runs
over the same graph, one with the frame slice and one without, produce
IDENTICAL labels. **MUTATION PROOF required**: make the slice leak into
adjudication in a scratch copy, show RED, restore, show GREEN, paste both.

**G3** — L-4: an undeclared departure is criticizable; a declared one
carries NO penalty in rank, admission, or acceptance. Assert the absence.

**G4** — C1: the slice is a deterministic render; the same problem and
state produce byte-identical packs.

**G5** — N1's check: no empty provenance-shaped slot in any emitted pack.

**G6** — N2's check: a standing attacker present at cycle k still renders
at the TERMINAL cycle of a multi-cycle offline run.

**G7** — token economy: the slice fits the pack budget; the allocation is
LOGGED; what the budget drops is DISCLOSED, not silent. No silent caps.

**G8** — axiom ledger (LADDER §5b): PROVES **A9**'s render half (render,
measures, diagnostics and knowledge views act only through attention);
PRESERVES **A3**, **A4**, **A10**.

### Constraints

**C-FROZEN** — surface 5 is ZERO **only because no new LLM role is
added**. The ladder marks this the rung most tempted to add one. If
articulation digests want a summarizer variant, REUSE the existing
summarizer role. **A design wanting a new role must STOP and ask.**
Surfaces 1-4 zero; any new `Config` knob gets its
`_versioned_source_config_data` line in the SAME commit.

**C-PUBLIC** — if a frame/pack inspection VIEW ships, all four wheel
pins (`scripts/wheel_smoke.py` and `scripts/wheel_operational_smoke.py`,
each `EXPECTED_MCP_TOOLS` + `EXPECTED_MCP_SCHEMA_SHA256`) move in the
same commit. If none ships, SAY SO and the smokes are not owed.

**C-SIZE** — ladder estimate 300-450 production lines plus 60-100 for the
third grade. If SPEC.md's plan exceeds ~700, **STOP** and say what grew.

**C-GATE** — ring while iterating; full gate (`python -m pytest tests/ -q
-n 4`) at the boundary; `python tools/docs_verify.py` FULL. The map moves
in the SAME commits (`DR-CON-packs-and-token-economy`,
`DR-SEAM-llm-x-rules`); every new check is RUN before it is written down.
Commit and push at every phase boundary, push with 2s/4s/8s/16s retry.

**C-DELIVER** — DELIVERY.md is R-by-R with pasted PROOF, closing with two
lines: (i) what a pack now shows about a consulted frame that it did not
before, and (ii) the three ways a frame can leave standing without any of
them being rounded away.

## 3. Map preflight — resolved ids

Read in the order `dr-drive-harness` §4 requires (INDEX → frozen surfaces
→ seam → subsystems).

| Id | Document | Why it is in scope |
|---|---|---|
| `DR-INV-frozen-surfaces` | `docs/map/INV-frozen-surfaces.md` | read FIRST; the five surfaces and the two instruments. Forecast contact: **none** (see C-FROZEN) |
| `DR-CON-packs-and-token-economy` | `docs/map/CON-packs-and-token-economy.md` | **the ladder names it.** Owns `llm/packs.py`, `packs/allocate.py`, `packs/ir.py`. The frame slice is a pack SECTION under its deterministic allocation; its two `_pack_section` census checks pin the current 15/11 slot counts and move with the code |
| `DR-SEAM-llm-x-rules` | `docs/map/SEAM-llm-x-rules.md` | **the ladder names it.** The slice text is computed in `rules/` and rendered in `llm/`, exactly as `frozen_evidence_context` / `citable_evidence_context` already cross. Its name-census and call-count checks are the ones a new crossing moves |
| `DR-CON-standing-and-background` | `docs/map/CON-standing-and-background.md` | owns `calculus/standing.py` — `consulted`, `frames`, `standing_view`, the consultability path the exit grades sit beside |
| `DR-SUB-calculus` | `docs/map/SUB-calculus.md` | owns the whole `calculus/` package: `claims.py` (a departure-declaration body), `compiler.py` (its ref roles), `scope.py` (R5's structural answer) |
| `DR-INV-axiom-basis` | `docs/map/INV-axiom-basis.md` | G8: A9 proved here, A3/A4/A10 preserved |
| `DR-CON-conjecture-kinds` | `docs/map/CON-conjecture-kinds.md` | holds the R-g guardrail whose sibling R4/L-4 is; its negative-grep pattern is the model for G3 |
| `DR-SUB-rules` | `docs/map/SUB-rules.md` | `rules/conj.py` and `rules/crit.py` are the two call sites that build the slice |
| `DR-CON-scheduler-ranking` | `docs/map/CON-scheduler-ranking.md` | R4's "no penalty in RANK" half lives against `Scheduler._select_problem` |

**No missing id found.** Every subsystem this tranche expects to touch has
a covering document. If execution reaches a file no document owns, that is
a finding to record, not a blocker.

## 4. Recorded environment facts (from the operator's KNOWN CURRENT STATE)

- Gate baseline `0 failed` (3939 at `7ad1b273f`) — **re-derived at this
  tranche's base**; the number is recorded in SPEC.md, not assumed.
- `docs_verify` carries **3 pre-existing `CON-run-identity.md` failures**
  under a shallow clone (0 on a full clone). Pre-existing; not this
  tranche's.
- **5 MCP-thread tests are known-flaky under `-n 4`.**
- Both wheel smokes green at base.
- The cycle soak is PRE-LAUNCH only; **this rung launches nothing**, so no
  soak is owed.
- The root sweep is RETIRED as an instrument (operator ruling
  2026-08-22).
- treadle's lane (`tools/treadle/`, `.swarm/`) shares no file with this
  tranche, and only the operator or the monitor may author its tasks.

## 5. Amendments

### Amendment 1 (2026-08-24) — the diff-budget overrun, disposed

At the step-9 `[COMMIT]` checkpoint `tools/diff_budget.py` reported **759**
insertions over `src/` against SPEC.md's ledgered ceiling of **560**, with
~820 projected at completion against the ladder's 360-550 estimate. That is
`dr-change-orchestrator`'s stop condition ("the estimated diff exceeds
SPEC.md's budget"), so the tranche stopped and put three priced roads to
the operator.

**The operator chose: continue and disclose.** Their selection, verbatim
from the option they picked:

> Continue and disclose (Recommended) — Finish steps 10-16 and land ~820
> lines, with the overrun and its per-file breakdown recorded in
> DELIVERY.md rather than the ceiling re-baselined. This is P4's own
> precedent (it exceeded 504/420 and disclosed). Nothing is cut.

**R8 (new).** The 560 ceiling is NOT re-baselined. DELIVERY.md carries the
overrun, its per-file breakdown, and the three causes below, as a disclosed
result rather than a corrected estimate.

**What grew, measured at the stop:**

| File | Insertions | SPEC estimate | Why |
|---|---|---|---|
| `calculus/render.py` | 380 | 185 | the step-7 crisis/digest split added a second renderer and a third cap; 125 of the 380 lines are docstrings and 18 are comments, per the repo's own convention that a comment states the constraint the code cannot show |
| `llm/packs.py` | 165 | 80 | the split doubled the section blocks, and the step-8 disclosure loop grew a helper plus the corrected termination argument |
| `rules/crit.py` | 57 | ~18 | two helpers, plus the THIRD `render_crit_pack` call site SPEC.md did not know about |
| everything else | 157 | ~222 | under estimate |

Three causes, two of them forced by measurement rather than chosen: the
crisis/digest split (a failing test, step 7), the third crit-pack call site
(the census check, step 9), and documentation density.

**C-SIZE is therefore DISCHARGED BY DECISION, not by staying inside it.**
The stop fired, the options were priced, the operator ruled. No later phase
may cite the 560 number as a constraint still in force.
