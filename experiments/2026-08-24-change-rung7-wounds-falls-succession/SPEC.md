# SPEC — Rung 7: wounds, falls, and succession

Authority: `REQUEST.md` (operator verbatim + R1-R9, G1-G7, C-FROZEN /
C-PUBLIC / C-SIZE / C-GATE / C-MAP / C-PUSH / C-DELIVER / C-D1 / C-D6).
Every item below cites the requirement it discharges. Every acceptance
check is a command or a named test.

## 0. Base facts, re-derived rather than assumed

| Fact | Value at this tranche's base (`053c129ac`) | How derived |
|---|---|---|
| Full gate | **3974 passed, 6 skipped, 2 failed** in 1187.11s — both failures are the operator's named `-n 4` MCP-thread flakes (`tests/test_mcp_run.py`), and both PASS serially: `7 passed in 12.13s`. Total 3976, matching the operator's KNOWN CURRENT STATE | `python -m pytest tests/ -q -n 4`, then `python -m pytest tests/test_mcp_run.py -q` |
| Frozen-surface verdict for the declared radius | `CONTACT`, one REAL (surface 3, the grant below) + one false positive | `tools/blast_radius.py`, §1 |
| Consumers of the declared radius | 12 test files, 19 map documents | same run |
| `open_orphans` reachability | **no live call path today** — the gate says so | same run |

## 1. Frozen surfaces — the census, and the grant requested BEFORE code

`python tools/blast_radius.py --files src/deepreason/calculus/standing.py
src/deepreason/calculus/render.py src/deepreason/calculus/nomination.py
src/deepreason/calculus/__init__.py src/deepreason/premises.py
src/deepreason/invariants.py src/deepreason/verification/report.py
src/deepreason/rules/crit.py src/deepreason/rules/conj.py
src/deepreason/scheduler/scheduler.py --symbols premise_orphaned
open_orphans standing_view consulted frames frame_slices
declared_frame_assertions exit_grade frame_exits
render_frame_slice_context` returns `"frozen_surface_verdict":
"CONTACT"` with four rows. Per E49 the census enumerates the SYMBOLS this
spec names as mechanisms, not only the files it plans to edit.

| Row | Disposition |
|---|---|
| `replay-validation record formats (invariants.py)` / `DIRECT` / `src/deepreason/invariants.py` | **REAL — this is the grant requested below (S9).** |
| `... / SYMBOL_INDIRECT / consulted` in `invariants.py` | **REAL, and already granted** — `_consulted_grants` is Rung 4's `standing-integrity` contact. Not re-opened: this tranche adds no field to `StandingGrant` and does not change `consulted()`. |
| `... / SYMBOL_INDIRECT / declared_frame_assertions` in `invariants.py` | **REAL, and already granted** — same Rung 4 contact, same reader. |
| `manifest schemas and validators (run_manifest.py)` / `SYMBOL_INDIRECT` / `consulted` | **substring false positive**, the same one Rung 6 disposed of. Every hit is the English word in a comment (lines 2393, 2400, 2414, 2425, 3439) and `run_manifest.py` imports nothing from `deepreason.calculus`. Re-derived: `grep -n "deepreason.calculus" src/deepreason/run_manifest.py` prints nothing. |

### THE GRANT REQUESTED — surface 3, additive (C-FROZEN)

The operator's own tranche instruction forecasts this contact and directs
that the grant be requested here rather than in chat:

> "FROZEN SURFACES (ladder row): surface 3 — FORECAST ADDITIVE CONTACT (a
> cascade-integrity check in verification); request the grant in SPEC.md
> BEFORE code, the monitor reviews it there."

**What is requested, exactly.** One additive `fail("cascade-integrity", …)`
family at the END of `verify_root`, in the shape Rung 4's
`standing-integrity` already established, plus the check's name in
`verification/report.py::_EPISTEMIC_CHECKS`. Three limbs, all of them
facts about the ROOT rather than about one artifact:

1. **A resolution with no mark.** A consulted orphan resolution
   (`retire` / `translate` / `independence`) whose problem carries no
   mark. A problem taken off the frontier with no premise-criticism
   behind it is exactly the silent path N3 forbids.
2. **A fallen frame with an unmarked framed problem.** For every frame
   assertion in a MARKING exit grade whose other three Def 9.2 conditions
   hold, every problem its σ admits must appear in the marks. **Derived
   INDEPENDENTLY of the marking function** — the check recomputes the
   obligation from the exits and σ and compares with what
   `premise_orphaned` produced, so a mutation to either side breaks it.
   A check that called the marking function on both sides would be a
   tautology wearing a check's clothes.
3. **A fallen frame that marks nothing because it is not separated.**
   Disclosure, not an accusation: an assertion that was never
   consultable never framed anything, so its fall orphans nothing — and a
   reader of a finished run needs telling that the record contains one,
   because components only ever GROW and a separation can be LOST after
   consultation (A5).

**Why it is additive, provably rather than by assertion.** All three limbs
recognise their inputs by bodies and commitments that no root written
before 2026-08-22 contains, and by `premise_orphaned`, whose two locks are
never both satisfied on such a root. **Insertions only, zero deletions**:
no existing finding's shape, name, order or detail string changes. Pinned
by a probe against a committed root, not by a fixture (S9's acceptance).

**Every other surface receives zero contact:**

- **F1. Surface 1** (`capabilities/state.py`) — standing is not a
  capability; nothing in §9 flows through the proposal/work-order maps.
  Not in the declared radius.
- **F2. Surface 2** (`harness.py`) — the cascade's marks, the batch
  offers and the trial record are ARTIFACTS and derived views, never new
  event rules. Prop 9.7's own proof requires it: "resolutions exist only
  as registered problem-closures", and a closure that is a registered
  artifact is attackable while an event rule is not.
- **F3. Surface 4** (manifest schemas AND validators) — **no new
  top-level `Config` field.** Every constant this tranche needs is a
  module constant, following `PREMISE_INVITE_AFTER`'s own recorded
  reason. So no `_versioned_source_config_data` line is owed for any
  schema version, and the `ENGAGED_CRITICISM_AUTHORITY` trap does not
  apply.
- **F4. Surface 5** (qualification subject digests) — **NO NEW LLM
  ROLE.** The succession trial uses the EXISTING `judge` role through the
  existing `pairwise_discriminate` guard, and it is OPTIONAL: the program
  road runs with no seat at all (C-D6, and the operator's solo law). The
  pair inventory is unchanged; no home owes a battery rerun. **The
  STOP-and-ask condition is therefore not triggered.**
- **F5. Frozen-adjacent `route_fingerprint`** — zero; the census reports
  no adjacent contact.
- **F6. Public surface** (C-PUBLIC) — no console entry point, MCP tool or
  wheel-layout change. `wheel_smoke_pins` in the census is EMPTY. No
  re-pin expected; the smokes are run at the boundary anyway to prove it.

## 2. What ships — spec items

### S1 (R2, G2) — the frame entry's recognition, `calculus/standing.py`

Additive functions; `consulted()`, `StandingGrant`, `frame_assertions`
and `consultability_of` keep their signatures and semantics unchanged.

| Symbol | Contract |
|---|---|
| `FallenFrame` | frozen dataclass: `assertion_id, subject_id, problem_id, scope, label, grade` |
| `fallen_frames(harness)` | every assertion that satisfies Def 9.2's conditions **except** `final(fa) = unrefuted`, whose label is `REFUTED` (grade `fall`) or `SUSPENDED_UNSUPPORTED` (grade `revocation`), sorted by assertion id |
| `unseparated_fallen_frames(harness)` | the same, for assertions that fail ONLY the separation condition — the disclosure limb 3 of S9 reads |
| `framed_problem_ids(harness, scope)` | every problem id σ admits, sorted; a scope that no longer compiles admits NOTHING, exactly as `frames` treats it |

**Why STRICT recognition** (`frame_assertion_body`, not
`declared_frame_assertions`): an assertion whose interface the compiler
would not have emitted is not this claim at all, so it never framed
anything and its fall orphans nothing. The loose reading exists for the
INTEGRITY check and for nothing else — S9 limb 3 keeps that split.

**Why separation is required at the frame entry** (G7, A6): an
unseparated assertion is UNCONSULTABLE, and R64 says a violation "moves
no edge, no warrant and no label". It never had standing to lose. The
condition is evaluated with Rung 3b's OWN predicate through
`separation.consultability`, never re-derived — two definitions of one
invariant would leave no way to tell which the record meant.

**The limit, stated so it is not over-read (A1):** components only grow,
so an assertion separated when consulted can be UNSEPARATED now, and the
frame entry is then silent for it. That silence is not hidden — S9 limb 3
reports it as a typed finding on the record.

Acceptance:
`python -m pytest tests/test_calculus_cascade_frame_entry.py -q`

### S2 (R2, G2, G3) — ONE marking function, both entries, `premises.py`

`premise_orphaned` gains the frame entry and stays the ONLY function that
assigns a cascade grade. Its body becomes: collect `(problem_id, status)`
pairs from BOTH entries, then apply ONE grading step.

| Entry | Source of the pair |
|---|---|
| premise (Rung 2, unchanged) | `standing_attributions` → `(problem_id, status(premise))` |
| frame (Rung 7, new) | `fallen_frames` × `framed_problem_ids(σ)` → `(problem_id, status(assertion))` |

Grading, identical for both and unchanged from Rung 2: `REFUTED` →
`PREMISE_REFUTED` ("premise refuted"), `SUSPENDED_UNSUPPORTED` →
`PREMISE_UNACCREDITED` ("premise unaccredited"); fall-grade dominates
revocation-grade when one problem is reached by both, because a refuted
premise is a stronger fact about the problem than an unaccredited one.
`SUSPENDED` (contestation) marks NOTHING on either entry — nobody has won,
and §9.7's table names only the two.

**G3's absence, under test.** No grade is stored anywhere: no field is
added to `Problem`, `EpistemicState` or `Event`; the grade is a pure
function of the two-pass label. A source scan asserts that
`PREMISE_REFUTED` / `PREMISE_UNACCREDITED` are ASSIGNED in exactly one
module and exactly one function.

**The import direction, and the map row it narrows.** `premises.py` gains
a function-local import of `deepreason.calculus.standing`. `SUB-calculus.md`
today pins a PROXY — "`premises.py` contains no `deepreason.calculus`
string" — for a claim that is really "the premise channel is not on the
claim substrate; the two attribution shapes are kept in step by hand".
This tranche does not move the channel onto the substrate. The check is
therefore NARROWED to the claim itself, in the same commit and in the same
shape as Rung 5's scheduler narrowing: `premises.py` imports no symbol
from `calculus.claims`, `calculus.compiler` or `calculus.operations`, and
still registers its own attribution shape. The narrower form is SHARPER —
it names the modules, so it cannot be satisfied by importing the same
things under another path.

Acceptance:
`python -m pytest tests/test_premise_channel.py tests/test_calculus_cascade_frame_entry.py -q`

### S3 (R3) — batch translation offers, `premises.py`

| Symbol | Contract |
|---|---|
| `batch_translation_offers(harness)` | open orphans grouped by CAUSE: `({"cause": id, "grade": grade, "problems": [...], "size": n}, ...)`, sorted by cause id then problem id |

The cause is the fallen premise for the premise entry and the fallen
assertion for the frame entry — §9.8's "groups of orphans may be
materialized together" is a grouping over what fell, because that is what
one translation into a better vocabulary would answer for.

**ATTENTION ONLY (C5, A9).** It registers nothing, spawns nothing, and
moves no label; it is a derived view plus one per-cycle receipt. It also
gives `open_orphans` its first live call path — the census in §0 recorded
that it had none.

New signal, declared through the typed channel per `DR-REC-add-signal`:
`premise.batch-translation-offered.v1`, unit `event`, staleness `cycle`,
semantics naming it as attention-only and non-validating.

Acceptance: `python -m pytest tests/test_premise_batch_offers.py -q` and
`python -c "from deepreason.signals import declaration; d =
declaration('premise.batch-translation-offered.v1'); assert d is not None
and d.unit != 'unspecified' and d.staleness != 'unspecified'"`

### S4 (R4) — succession detection and the ONE render exception

New module `src/deepreason/calculus/succession.py`. READ-ONLY in the same
sense `render.py` is: it holds no call that could write a label, an edge
or a warrant.

| Symbol | Contract |
|---|---|
| `SuccessionTrialV1` | frozen dataclass: `problem_id, promotion_problem, subject_ids, rival_ids, criteria` |
| `succession_trial_of(harness, problem_id)` | the trial, or `None`. A problem qualifies when its trigger is `DISCRIMINATION`, `provenance.from_[0]` is a `PROMOTION` problem, and at least TWO of `from_[1:]` are recognised frame assertions addressed to it |
| `SUCCESSION_CRITERION_ORDER = "fixed"` | Q2c's recorded answer (S6) |
| `succession_criteria(harness, trial)` | the PROMOTION problem's criteria, SORTED — the fixed order, used by both the pack and the record so the two cannot disagree |
| `render_succession_context(harness, problem_id)` | the model-facing text, or `None` |

**The render exception, and it is exactly one site.**
`calculus/render.py::frame_slices` returns `()` for a succession trial
problem, so BOTH `render_frame_slice_context` and
`render_frame_crisis_context` fall to their existing `None` path, and
`render_frame_slice_context` returns the succession context instead.
Nothing in `llm/packs.py` changes and no new pack section is added — the
succession text rides the existing non-droppable `frame_slice_context`
slot, so `DR-SEAM-calculus-x-rules`'s agreement ("a rule receives TEXT")
is unchanged and the seam's import check still passes by name.

**What the succession context renders**, symmetric by construction:

- BOTH articulation digests, via `render.articulation_digest`, sorted by
  SUBJECT ID — not by incumbency, which is provenance-shaped ordering
  (Ax 4.1).
- each subject's standing attackers (its wounds), through
  `render.subject_attackers`, under the same cap and with the cap stated
  in-band — anomaly conservation is visible on both sides or on neither.
- the fixed-order criteria the trial will judge on.
- NO provenance, populated or blank; no "incumbent" / "challenger"
  label; no frame directive. `RESEARCH_JUDGE_BLINDING`'s placebo result
  is why an absent part is ABSENT rather than announced.
- an in-band statement that neither candidate frames this problem — the
  mitigation is symmetric exposure, and the calculus's own words are that
  "a view from nowhere is not on offer".

Acceptance: `python -m pytest tests/test_calculus_succession.py -q`

### S5 (R6, R7, R9) — the trial's two roads, both orders

| Symbol | Contract |
|---|---|
| `PairwisePresentation` (in `informal/trial.py`) | frozen dataclass `(a_text, b_text, criteria)`; when passed, `pairwise_discriminate` judges THOSE texts and criteria |
| `observer` (in `informal/trial.py`) | optional callable invoked with `(ruling1, ruling2, outcome)` once both orders have been judged |
| `program_road(harness, trial)` | for each rival pair, the program verdict in BOTH presentation orders |
| `run_succession_trial(harness, problem, adapter, config, *, authority, diagnostics)` | composes both roads and records the trial |

**Both keywords on `pairwise_discriminate` are GENERIC.** `informal/`
learns nothing about `calculus/` — no import is added in that direction,
so no new package edge is created and the succession module supplies both.
That is why there is ONE pairwise instrument and not two: D-6 answer A
admits a rubric ruling "only through the existing trial guard", and its
referential-integrity, order-swap and execution-supremacy screens all
still apply.

**Q2a — both orders of the two articulation DIGESTS.** The rubric road is
handed the digests, not the frame assertions' JSON: the assertions are
paperwork, and §9.7's own words are that the succession pack "renders both
articulation digests". The program road evaluates the same digest pair in
both orders too — order-invariance is DEMONSTRATED by running it, never
asserted.

**Q2b — order-disagreement is a typed NO-VERDICT.** The rubric road's
existing `blocked:order-swap` IS that outcome and is reused unchanged; the
trial record carries `outcome: "no-verdict"` with
`no_verdict_reason: "order-disagreement"`, and the rivalry stays
unresolved. It is never a tiebreak, and no ruling is "picked" from either
order.

**The program road, and why it usually says `neither`.** By the time a
succession trial exists, both rivals have already passed `accounts-for` —
a rival that fails is refuted by `promotion_criteria_sweep` and is not a
surviving rival, so the discrimination never spawns. The program therefore
discriminates only where the record already separates the two, and
otherwise records `neither` with its reason and routes onward. That is
D-6 answer A working as specified: a program adjudicates where a program
can, and where it cannot the fallback is VISIBLE.

**Solo (C-D6, the operator's standing law).** With no `judge` seat the
trial still runs, records both program orders, and reports its flip rate.
Succession is not locked out of a solo run.

Acceptance: `python -m pytest tests/test_calculus_succession_trial.py -q`

### S6 (R8, R9, G5) — the trial record

Registered as an ORDINARY artifact — attackable (P6) — with **no
`problem_id`**, for `file_premise`'s own recorded reason: an artifact
addressed to the discrimination problem would become a RIVAL in the
rivalry it is a diagnostic of. One Measure receipt names it.

```
{"schema": "succession-trial.v1",
 "problem": "<disc problem id>",
 "promotion_problem": "<promotion problem id>",
 "rivals": [...],                       # sorted
 "criterion_order": "fixed",            # Q2c: WHICH, recorded
 "criteria": [...],                     # in the order used
 "evaluations": [
   {"pair": [a, b], "road": "program"|"rubric",
    "orders": [{"order": "ab", "top": <id|null>, "reason": "..."},
               {"order": "ba", "top": <id|null>, "reason": "..."}],
    "flipped": bool,
    "outcome": "<id>"|"no-verdict"|"neither",
    "no_verdict_reason": "order-disagreement"|null}],
 "flips": n, "evaluated": m,
 "flip_rate": n/m,                      # Q2d, 0.0 when m == 0
 "outcome": "<id>"|"no-verdict"|"neither"}
```

**Q2c's answer is FIXED, and the reason is recorded rather than assumed.**
A randomized criterion order would need a seed, and §12.1's determinism
requirement admits exactly two roads — seed the kernel or log the draw —
both of which buy nothing here: Q2's own measurement is that criterion
order shifts a criterion's mean, not that randomizing removes the shift.
Fixing it makes the shift CONSTANT and NAMED. The record says `"fixed"`
so a reader never has to infer it.

**Q2d is first-class, not derived on request.** `flip_rate` is a field of
the record and a Measure input; a trial with no evaluations reports
`0.0` beside `evaluated: 0`, so an empty rate can never be read as a
clean one.

Acceptance: `python -m pytest tests/test_calculus_succession_trial.py -q`

### S7 (R5) — anomaly conservation, proved end to end

Nothing new is built here either: `succeeded_wound_refs`, the
machine-derived `wound_refs`, `bounded` validity with its domain and
tolerance, and the MENTION compilation of a claimed wound all shipped at
Rungs 4-5. What this rung adds is the PROOF that the road exists and
closes, in `tests/test_calculus_anomaly_conservation.py`:

1. the successor's claim carries the incumbent's wounds and the compiler
   makes each a MENTION, never a dependence — so a reinstated wound cannot
   suspend the successor;
2. `succeeds` refuses a rival whose recovery residue is unaccounted, and
   accepts one whose `bounded` validity names the residue as its domain;
3. the residual assertion for the FALLEN subject — filed with
   `validity="bounded"`, its domain and tolerance — is consultable and
   keeps framing exactly its granted domain: **instrument standing**, and
   `StandingGrant.validity` is where a reader tells it from unqualified
   standing (C3, no third value);
4. it is attackable like anything: refuting it ends the residual grant,
   and the fallen subject stops framing even its bounded domain.

Acceptance:
`python -m pytest tests/test_calculus_anomaly_conservation.py -q`

### S8 (C-D1) — the incumbent's promotion problem, ranked by wound count

D-1 answered **A**: crisis is a RENDER state only. **No standing-layer
spawn trigger is built**, and its absence is asserted (S10). The one
scheduling consequence D-1 names is attention:

| Symbol | Contract |
|---|---|
| `calculus/nomination.py::promotion_wound_counts(harness)` | `{promotion problem id: len(warrants against its subject)}`, from `provenance.from_[0]` and `harness.warrants` |
| `Scheduler._select_problem` | one term added to `rank`, AFTER the SEED term |

The term reads NO standing view and NO problem-status view — it is a
warrant count against an id named in the problem's own provenance — so
`DR-SUB-calculus`'s NO SCHEDULER SELECTION row and
`DR-CON-standing-and-background`'s disambiguation check both continue to
hold as written, unnarrowed.

**The operator's seed question still wins every tie** (a CLAUDE.md
invariant): the new term sits after `p.provenance.trigger != SEED`, never
before it.

Acceptance: `python -m pytest tests/test_scheduler_promotion_rank.py -q`

### S9 (G2, and the §1 grant) — `cascade-integrity` in `verify_root`

The three limbs of §1's grant, plus the name in
`verification/report.py::_EPISTEMIC_CHECKS`. Insertions only.

Acceptance:
`python -m pytest tests/test_cascade_integrity.py -q` and a probe against
a committed root proving the check reports NOTHING on a root that
predates it.

### S10 (G1, G2, G3, G4, G7) — the gate's own proofs

| Test file | Proves |
|---|---|
| `tests/test_calculus_wound_persistence.py` | **G1**: a wound changes `status(b)` and does NOT change `standing(b)`, through the whole path — the subject is refuted, the assertion stays consulted, its grant is unchanged byte for byte, the frame still renders, and NO cascade mark appears. MUTATION PROOF pasted in VALIDATION.md |
| `tests/test_calculus_cascade_frame_entry.py` | **G2**: both entry conditions reach one marking function; the SECOND MECHANISM'S ABSENCE is asserted structurally |
| `tests/test_calculus_cascade_frame_entry.py` | **G3**: the two grades come from the two-pass labels with no new machinery; no grade is stored; exactly one assigning function |
| `tests/test_cascade_n3_at_scale.py` | **G4**: a thousand-problem cascade retires, translates and finds independent, and NOT ONE resolution asserts insolubility |
| `tests/test_calculus_succession_trial.py` | **G5**: Q2a-d present in the record, with a CONSTRUCTED order-disagreement case proving the no-verdict road |
| `tests/test_calculus_axioms_rung7.py` | **G7**: A6 preserved at the frame entry, A9 preserved (the succession render and the trial record write no label); no standing-layer spawn trigger exists (C-D1) |

### S11 (G6, live) — the live gate, and the soak that must precede it

**No launch without a green cycle soak on the launch config** (CLAUDE.md
law, restated by the operator). The launch config is the epoch3 shape,
which is ALREADY in the soak's case table, so no case is added:

    python -u scripts/cycle_soak.py --case epoch3     # expect exit 0

Only once that is green is the operator asked for the `OLLAMA_API_KEY`
env file. The live gate then stages a fall on a live root and is judged on
TYPED OUTCOMES ONLY: the mark appears with its grade, the cascade fires,
`verify_root` is clean. Model prose is not evidence.

## 3. Assumptions recorded (SPEC.md's own ledger)

| # | Assumption | Why, and what would falsify it |
|---|---|---|
| A1 | "Carrying" a frame is σ-admission, computed, never stored | A7's mechanism is that there is no mechanism; `frames()` has meant exactly this since Rung 4, and the cascade must not invent a second meaning. Falsified if a stored pose-time frame field is ever added |
| A2 | The frame entry requires the three non-label Def 9.2 conditions | R64: an unseparated assertion moves nothing. Falsified if a fall on an unconsultable assertion should mark |
| A3 | Components only grow, so a separation lost after consultation silences the frame entry for that assertion | S9 limb 3 reports it rather than hiding it |
| A4 | `SUSPENDED` (contestation) marks nothing | §9.7's table names two grades; nobody has won |
| A5 | Fall-grade dominates revocation-grade on one problem | a refuted premise is a stronger fact than an unaccredited one; identical for both entries, which is what keeps it ONE function |
| A6 | Criterion order is FIXED, and recorded as such | §12.1 determinism; Q2 measured that order SHIFTS a criterion's mean, not that randomizing removes it |
| A7 | The trial record is an artifact with NO `problem_id` | `file_premise`'s recorded reason: an addressed artifact becomes a rival |
| A8 | The rubric road is optional; the program road needs no seat | C-D6 and the operator's solo law |
| A9 | The succession text rides the existing `frame_slice_context` slot | no new pack section, no `llm/packs.py` change, seam unchanged |
| A10 | No new `Config` field; module constants only | F3, and `PREMISE_INVITE_AFTER`'s own recorded reason |

## 4. Size — the ledgered ceiling (C-SIZE)

| Area | Production lines (estimate) |
|---|---|
| `calculus/standing.py` (S1) | 60 |
| `premises.py` (S2, S3) | 80 |
| `calculus/render.py` (S4 suppression) | 20 |
| `calculus/succession.py` (S4, S5, S6) | 240 |
| `informal/trial.py` (S5, two generic keywords) | 30 |
| `calculus/nomination.py` + `scheduler.py` (S8, S3 receipt) | 45 |
| `invariants.py` + `verification/report.py` (S9) | 60 |
| `signals.py` (S3) | 12 |
| `calculus/__init__.py` exports | 15 |
| **total** | **562** |

**562 is inside the ladder's 500-700 and well inside C-SIZE's ~900 STOP
threshold.** Ledgered ceiling for `tools/diff_budget.py` at every
`[COMMIT]`: **700 production lines**, `src/` only. Tests and the tranche's
own documents are budgeted separately and are not counted against it,
following Rung 6's own separation of the two ceilings.

## 5. Map documents that move in the same commits (C-MAP)

| Document | What changes |
|---|---|
| `DR-CON-problem-layer-lifecycle` | the second cascade entry, one marking function, batch offers, the new signal |
| `DR-SUB-calculus` | `fallen_frames`, succession, the trial record; the NARROWED `premises.py` trap check (S2) |
| `DR-CON-standing-and-background` | Prop 9.6 proved; the frame entry beside the three exit grades |
| `DR-SEAM-calculus-x-rules` | the succession render exception, and the seam's import check re-pinned to include it |
| `DR-INV-frozen-surfaces` | the granted surface-3 contact, recorded with its three checkable facts |
| `DR-INV-axiom-basis` | A6 and A9 preserved at Rung 7; A7's "computed, never stored" carried into the cascade |
| `DR-SUB-verification` | `cascade-integrity` |
| `DR-INV-signal-contract` | the new signal, per `DR-REC-add-signal` |
| `DR-CON-scheduler-ranking` | the wound-count term, attention only |
