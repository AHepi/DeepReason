# REQUEST — Rung 7: wounds, falls, and succession

Tranche directory: `experiments/2026-08-24-change-rung7-wounds-falls-succession/`
Branch: `claude/rung-7-calculus-wounds-falls-pc3urk`
Base: `origin/main` at `053c129ac` (`git merge-base --is-ancestor 053c129ac HEAD` — OK)
Captured: 2026-08-24
Family: `dr-change-orchestrator`

## 0. Authority

The operator's message is reproduced verbatim in §1. It delegates the
substance to committed authorities, and ALL of them are authority here,
not background:

- `experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md`,
  **Rung 7** (lines 711-760), read in full BEFORE this SPEC.
- `experiments/2026-08-14-change-calculus-reconciliation-v2/DECISIONS.md`
  **D-1** (answered **A**: crisis is a render state only — no
  standing-layer spawn trigger; the incumbent's promotion problem stays
  on the frontier, ranked by wound count, attention only) and **D-6**
  (answered **A**: program-first `accounts-for`, refined by R46/R57 to
  the STRONG relation).
- `docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` **Q2** — the
  succession-trial requirements, all four ledgered below as Q2a-Q2d.
- `docs/COMPUTABLE_CALCULUS.md` §9.6, §9.7, §9.8, §13; Prop 9.6,
  Prop 9.7.
- `docs/POIETIC_CALCULUS_FORMALIZED.md` §8.2 (the three exit grades,
  already shipped at Rung 6).

Entry condition: **Rung 6 delivered 2026-08-24**
(`experiments/2026-08-24-change-rung6-frame-render-departures/DELIVERY.md`,
VALIDATION verdict PASS at `053c129ac`) — frame render semantics, the
departure protocol, the three exit grades. **Met.**

## 1. The operator's words, verbatim

> TARGET REPOSITORY: AHepi/DeepReason — verify before anything else;
> if this session is based elsewhere, ask the operator to attach it
> with push access and STOP until then.
>
> Change tranche: Rung 7 of the v2 calculus program — wounds, falls,
> and succession. Route through dr-change-orchestrator; the
> workflow's own stop conditions apply, nothing else stops.
>
> SETUP (fresh container): git fetch origin main && git checkout -B
> <your session-designated branch> origin/main; git merge-base
> --is-ancestor 053c129ac HEAD || re-fetch. pip install -e .
> --break-system-packages -q; pip install pytest pytest-xdist
> jsonschema --break-system-packages -q; deepreason embedder-warmup
> (the live gate below runs the harness). Read CLAUDE.md in full;
> load dr-drive-harness, dr-explain-to-operator. THE OPERATOR
> SUPPLIES the OLLAMA_API_KEY env file only at the live-gate step —
> everything before it is offline.
>
> AUTHORITY: experiments/2026-08-14-change-calculus-reconciliation-v2/
> LADDER.md, Rung 7 — read the section IN FULL before SPEC.md.
> DECISIONS.md answers in hand: D-1 (crisis is a RENDER state only —
> no standing-layer spawn trigger; the incumbent's promotion problem
> stays on the frontier, ranked by wound count, attention only) and
> D-6 (program-first accounts-for). Entry met: Rung 6 delivered
> 2026-08-24. ALSO BINDING, from
> docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md Q2 — the
> succession-trial requirements, ledger all four:
> (Q2a) the trial judges BOTH orders of the two articulation digests;
> (Q2b) order-disagreement is a typed NO-VERDICT outcome, never a
>       tiebreak — flag and route onward, the way the harness
>       already treats no-consensus;
> (Q2c) criterion order within the trial is fixed or randomized, and
>       WHICH is recorded in the trial record;
> (Q2d) the per-trial FLIP RATE (top-choice reversal between orders)
>       is a first-class recorded diagnostic — a succession trial
>       that never reports its flip rate claims a precision it does
>       not have.
>
> WORK, per the ladder:
> - WOUNDS: nothing new is built. A fail verdict on the subject's own
>   observation-valued commitment already yields a demonstrative
>   warrant and a refuted status; this rung PROVES standing is
>   untouched by it (Prop 9.6).
> - THE SECOND CASCADE ENTRY wired into Rung 2's machinery: a
>   consulted assertion leaving unrefuted standing marks every
>   problem carrying it, with fall-grade ("premise refuted") or
>   revocation-grade ("premise unaccredited") — one marking function,
>   both entries, no second mechanism.
> - BATCH TRANSLATION OFFERS (§9.8): groups of orphans may be
>   materialized together — attention only.
> - SUCCESSION as ordinary discrimination, with THE ONE render
>   exception: the succession pack SUPPRESSES the incumbent's frame
>   slice and renders BOTH articulation digests, so the trial of a
>   frame is framed by neither party (incumbent-judge bias). Q2a-d
>   apply to exactly this pack.
> - ANOMALY CONSERVATION: accounts-for makes the successor claim the
>   incumbent's wounds as its own commitments; the successor's scope
>   statement fixes the incumbent's residual validity domain, leaving
>   a bounded-validity assertion — instrument standing, authored by
>   the successor, attackable like anything.
>
> GATE PROVES (each named in VALIDATION.md):
> - Prop 9.6 END TO END: a wound changes status(b) and does NOT
>   change standing(b) — the direct consequence of the mention law,
>   tested through the whole path. MUTATION PROOF: make a wound touch
>   standing in a scratch copy, RED, restore, GREEN, paste both.
> - Prop 9.7 NOW COMPLETE: both entry conditions, one marking
>   function — assert the second mechanism's ABSENCE.
> - §9.7's two grades distinguished by the two-pass labels with NO
>   new machinery — that absence is under test.
> - N3 AT SCALE: a thousand-problem cascade retires, translates, and
>   finds independent, and not one resolution asserts insolubility.
> - Q2a-d: both-orders, typed no-verdict, criterion-order recording,
>   and flip rate all present in the trial record — with a
>   constructed order-disagreement case proving the no-verdict road.
> - LIVE GATE (L-6): a fall staged on a live root, judged on typed
>   outcomes only (the mark appears with its grade, the cascade
>   fires, verify_root clean). CLAUDE.md law applies: NO launch
>   without a green cycle soak on the launch config — if the launch
>   config differs from the epoch3 case, extend the soak's case
>   table in the same commit rather than skipping the gate. Ask the
>   operator for the key ONLY once the soak is green.
> - Axiom ledger (§5b): PRESERVES A6 (separation, at the frame
>   entry), A9; the exit artifact carries §13's residue VERBATIM
>   ("a wounded background with no arriving rival frames forever…
>   and never declared irreplaceable" — T-8).
>
> FROZEN SURFACES (ladder row): surface 3 — FORECAST ADDITIVE
> CONTACT (a cascade-integrity check in verification); request the
> grant in SPEC.md BEFORE code, the monitor reviews it there. All
> others zero; NO new LLM role (STOP and ask if a design wants one).
> Public surface unchanged — no re-pin expected.
>
> SIZE: ladder estimates 500-700 lines. If SPEC.md's plan exceeds
> ~900, STOP and say what grew.
>
> KNOWN CURRENT STATE: gate baseline 0 failed (3976 at 053c129ac —
> re-derive at your base); docs_verify 3 pre-existing shallow-clone
> failures (0 on a full clone); 5 MCP-thread tests known-flaky under
> -n 4; both wheel smokes green; cycle soak expects exit 0; sweep
> retired; treadle's lane exists — no shared files, and only the
> operator or monitor authors its tasks.
>
> GATE: ring while iterating; full gate at the boundary; docs_verify
> full. Map moves in the same commits. Commit and push every phase
> boundary (retry 2s/4s/8s/16s). Deliver R-by-R with pasted PROOF,
> closing with two lines: what happens to a framed problem the day
> its frame falls, and what a succession trial now records that a
> courtroom would recognize.

## 2. Numbered requirements

### The work

- **R1 — Wounds: build nothing, prove standing is untouched.** "WOUNDS:
  nothing new is built. A fail verdict on the subject's own
  observation-valued commitment already yields a demonstrative warrant
  and a refuted status; this rung PROVES standing is untouched by it
  (Prop 9.6)." The deliverable is a proof, not a mechanism. A new wound
  mechanism would itself violate this requirement.

- **R2 — The second cascade entry, in Rung 2's machinery.** "THE SECOND
  CASCADE ENTRY wired into Rung 2's machinery: a consulted assertion
  leaving unrefuted standing marks every problem carrying it, with
  fall-grade ('premise refuted') or revocation-grade ('premise
  unaccredited') — one marking function, both entries, no second
  mechanism."

- **R3 — Batch translation offers.** "BATCH TRANSLATION OFFERS (§9.8):
  groups of orphans may be materialized together — attention only."

- **R4 — Succession as ordinary discrimination, with one render
  exception.** "SUCCESSION as ordinary discrimination, with THE ONE
  render exception: the succession pack SUPPRESSES the incumbent's frame
  slice and renders BOTH articulation digests, so the trial of a frame is
  framed by neither party (incumbent-judge bias). Q2a-d apply to exactly
  this pack."

- **R5 — Anomaly conservation.** "ANOMALY CONSERVATION: accounts-for
  makes the successor claim the incumbent's wounds as its own
  commitments; the successor's scope statement fixes the incumbent's
  residual validity domain, leaving a bounded-validity assertion —
  instrument standing, authored by the successor, attackable like
  anything."

### The succession-trial requirements (Q2), binding

- **R6 (Q2a)** — "the trial judges BOTH orders of the two articulation
  digests".
- **R7 (Q2b)** — "order-disagreement is a typed NO-VERDICT outcome,
  never a tiebreak — flag and route onward, the way the harness already
  treats no-consensus".
- **R8 (Q2c)** — "criterion order within the trial is fixed or
  randomized, and WHICH is recorded in the trial record".
- **R9 (Q2d)** — "the per-trial FLIP RATE (top-choice reversal between
  orders) is a first-class recorded diagnostic — a succession trial that
  never reports its flip rate claims a precision it does not have".

### What the gate must prove (each named in VALIDATION.md)

- **G1** — "Prop 9.6 END TO END: a wound changes status(b) and does NOT
  change standing(b) — the direct consequence of the mention law, tested
  through the whole path. MUTATION PROOF: make a wound touch standing in
  a scratch copy, RED, restore, GREEN, paste both."
- **G2** — "Prop 9.7 NOW COMPLETE: both entry conditions, one marking
  function — assert the second mechanism's ABSENCE."
- **G3** — "§9.7's two grades distinguished by the two-pass labels with
  NO new machinery — that absence is under test."
- **G4** — "N3 AT SCALE: a thousand-problem cascade retires, translates,
  and finds independent, and not one resolution asserts insolubility."
- **G5** — "Q2a-d: both-orders, typed no-verdict, criterion-order
  recording, and flip rate all present in the trial record — with a
  constructed order-disagreement case proving the no-verdict road."
- **G6 (L-6, live)** — "a fall staged on a live root, judged on typed
  outcomes only (the mark appears with its grade, the cascade fires,
  verify_root clean). CLAUDE.md law applies: NO launch without a green
  cycle soak on the launch config — if the launch config differs from the
  epoch3 case, extend the soak's case table in the same commit rather
  than skipping the gate. Ask the operator for the key ONLY once the soak
  is green."
- **G7** — "Axiom ledger (§5b): PRESERVES A6 (separation, at the frame
  entry), A9; the exit artifact carries §13's residue VERBATIM ('a
  wounded background with no arriving rival frames forever… and never
  declared irreplaceable' — T-8)."

### Constraints

- **C-FROZEN** — "FROZEN SURFACES (ladder row): surface 3 — FORECAST
  ADDITIVE CONTACT (a cascade-integrity check in verification); request
  the grant in SPEC.md BEFORE code, the monitor reviews it there. All
  others zero; NO new LLM role (STOP and ask if a design wants one)."
- **C-PUBLIC** — "Public surface unchanged — no re-pin expected."
- **C-SIZE** — "SIZE: ladder estimates 500-700 lines. If SPEC.md's plan
  exceeds ~900, STOP and say what grew."
- **C-GATE** — "GATE: ring while iterating; full gate at the boundary;
  docs_verify full."
- **C-MAP** — "Map moves in the same commits."
- **C-PUSH** — "Commit and push every phase boundary (retry
  2s/4s/8s/16s)."
- **C-DELIVER** — "Deliver R-by-R with pasted PROOF, closing with two
  lines: what happens to a framed problem the day its frame falls, and
  what a succession trial now records that a courtroom would recognize."
- **C-D1** — D-1 answered **A**: crisis is a RENDER state only. No
  standing-layer spawn trigger may be built by this tranche. The
  incumbent's promotion problem stays on the frontier, ranked by wound
  count — attention only.
- **C-D6** — D-6 answered **A**: program-first `accounts-for`; judges
  optional, admitted only through the existing trial guard. A design that
  requires a judge ensemble for succession is refused (it would collide
  with the operator's solo-run law).

## 3. Map preflight — resolved ids

Read in the map's own order: `INDEX.md` → `INV-frozen-surfaces.md` →
the SEAM before either subsystem → the subsystems.

| Id | Document | Why this tranche touches it |
|---|---|---|
| `DR-INV-frozen-surfaces` | `docs/map/INV-frozen-surfaces.md` | surface 3 grant (§3 of SPEC), read BEFORE designing |
| `DR-SEAM-calculus-x-rules` | `docs/map/SEAM-calculus-x-rules.md` | the succession pack crosses it — `rules/` receives TEXT from `calculus/render.py` and nothing else |
| `DR-SUB-calculus` | `docs/map/SUB-calculus.md` | the claim substrate, standing, promotion criteria, `accounts-for` |
| `DR-CON-standing-and-background` | `docs/map/CON-standing-and-background.md` | Def 9.3, the three exit grades, Prop 9.6's home |
| `DR-CON-problem-layer-lifecycle` | `docs/map/CON-problem-layer-lifecycle.md` | Rung 2's cascade machinery — the marking function R2 must extend, not duplicate |
| `DR-SUB-verification` | `docs/map/SUB-verification.md` | the cascade-integrity check (surface 3, additive) |
| `DR-INV-axiom-basis` | `docs/map/INV-axiom-basis.md` | A6 and A9 preserved (G7); A7 is why "carrying" is computed, not stored |
| `DR-SUB-rules` | `docs/map/SUB-rules.md` | the discrimination spawn that succession reuses unchanged |
| `DR-CON-packs-and-token-economy` | `docs/map/CON-packs-and-token-economy.md` | the succession section's budget treatment |

**The one ordering rule was obeyed:** `SEAM-calculus-x-rules.md` was read
before `SUB-calculus.md` and `SUB-rules.md`.

## 4. Recorded environment facts (from the operator's KNOWN CURRENT STATE)

| Fact | Operator's statement | Re-derived at this base |
|---|---|---|
| Gate baseline | 0 failed (3976 at `053c129ac`) | SPEC.md §0 |
| `docs_verify` | 3 pre-existing shallow-clone failures (0 on a full clone) | SPEC.md §0 |
| MCP-thread tests | 5 known-flaky under `-n 4` | carried |
| Wheel smokes | both green; no re-pin expected (C-PUBLIC) | SPEC.md §0 |
| Cycle soak | expects exit 0; required before any live launch | G6 |
| Root sweep | retired as an instrument | not run |
| treadle | lane exists; no shared files; only operator/monitor author tasks | untouched |

## 5. Amendments

### Amendment 1 (2026-08-24) — the diff-budget overrun, disposed

At the step-9 `[COMMIT]` checkpoint `tools/diff_budget.py` reported **893**
insertions over `src/` against SPEC.md's ledgered ceiling of **700**, with
~1000 projected at completion against the ladder's 500-700 estimate. That is
`dr-change-orchestrator`'s stop condition ("the estimated diff exceeds
SPEC.md's budget"), so the tranche stopped and put three priced roads to the
operator.

**The operator chose: continue and disclose.** Their selection, verbatim from
the option they picked:

> Continue and disclose (Recommended) — Finish steps 10-16 and land ~1000
> lines, with the overrun and its per-file breakdown recorded in DELIVERY.md
> rather than the ceiling re-baselined. This is Rung 6's own precedent
> (759/560, disclosed). Nothing is cut, the live gate still runs.

**R10 (new).** The 700 ceiling is NOT re-baselined. DELIVERY.md carries the
overrun, its per-file breakdown, and the cause below, as a disclosed result
rather than a corrected estimate.

**What grew, measured at the stop:**

| File | Insertions | SPEC estimate | Why |
|---|---|---|---|
| `calculus/succession.py` | 458 | 240 | the estimate counted EXECUTABLE lines and the instrument counts ADDED LINES. Measured at the stop: 241 executable, 217 docstring, comment and blank. The executable half is within 1 line of the estimate |
| `premises.py` | 138 | 80 | `orphan_causes` was not in the estimate at all — it exists because the batch offer must know which cause explains a mark, and its precedence rule had to be written on the label rather than the grade |
| `calculus/standing.py` | 126 | 60 | `unseparated_fallen_frames` and the shared `_fallen` helper, plus the recorded reason for requiring separation at the frame entry |
| `informal/trial.py` | 73 | 30 | the observer had to fire at FIVE exits, not one: a hook that only fired on clean verdicts would report a flip rate of zero on exactly the trials that flipped |
| `scheduler.py` | 49 | 45 | on estimate |
| `signals.py` | 32 | 12 | two signals, not one — `succession.trial-flip-rate.v1` was not foreseen at spec time and the gate refused it until it was declared |
| `calculus/render.py` | 22 | 20 | on estimate |
| `calculus/__init__.py` | 8 | 15 | under estimate |

**The single cause, stated so the next tranche does not repeat it.** SPEC.md
§4's estimate was built by counting the executable lines each item needs.
`tools/diff_budget.py` counts INSERTIONS, which includes every docstring,
comment and blank line — and this repository's own convention requires a
comment wherever the code cannot show the constraint. On the one new module the
two numbers differ by 90 per cent. A future SPEC's size table should either
estimate added lines directly or state which of the two it is estimating.

New operator messages are appended here verbatim, as new numbered requirements
or as `Rn a supersedes Rn`, BEFORE being acted on.
