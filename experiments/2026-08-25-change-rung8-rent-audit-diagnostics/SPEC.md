# SPEC — Rung 8: rent, the authority audit, capture integration, the §14 diagnostics

Traces: every item cites R/C numbers from `REQUEST.md`. Untraceable items are
bugs.

Base: `origin/main` at `462d6091d`. Branch `claude/rung-8-closing-calculus-xgxyzt`.

---

## 0. What the record already contains, measured before designing

Six measurements, each a pasted command output, because five of this rung's
seven work items turn out to be about reconciling with something already
shipped rather than building something new.

**M1 — rent's EMPIRICAL half already ships as promotion criterion 1.**

```
$ grep -n "empirical-scope-without-observation-valued-commitment" src/deepreason/calculus/promotion.py
227:            "reason": "empirical-scope-without-observation-valued-commitment",
```
`subject_demarcation` (criterion 1) already fails a candidate whose scope is
empirical and whose subject carries no `observation_valued` commitment, and
already fails `demarcation == "no-attack-surface"` — which IS `active(b)`
(§9.3's `active(a) ⇔ crit ∧ mod`, `docs/COMPUTABLE_CALCULUS.md:644`). The half
of §9.3 that is NOT on the tree is ARTICULATION.

**M2 — articulation exists as a RENDER, not as a criterion.**

```
$ grep -n "def articulation_digest" src/deepreason/calculus/render.py
138:def articulation_digest(harness, subject_id: str) -> tuple[str, bool, tuple[str, ...]]:
```
Rung 6 ships `articulation_digest` for the frame slice. Nothing on the
promotion path requires a candidate background to BE articulated before it is
elevated. That is R1's delta and the whole of it.

**M3 — the record already distinguishes the two attack relations §14 and Rung 2
read.** `StateDiff` carries both:

```
$ python -c "from deepreason.ontology.event import StateDiff; print(list(StateDiff.model_fields.keys()))"
['att_add', 'dep_add', 'a_add', 'pi_add', 'status_changed', 'hv_set', 'reach_set', 'addr_add', 'carry_add']
```
`carry_add` is `(carrier artifact, warrant id)` — a NEWLY CARRIED warrant, which
is §14.2's own primitive. `att_add` is the materialized, closure-expanded edge
set, which is what the shipped `criticism.attack-target-entropy.v1` reads. They
are different relations, and the log records them separately. This is the
measurement that decides V-6 (§3, D1).

**M4 — there is a THIRD population with the same names, and it is not in the
registry at all.**

```
$ grep -n "attack_target_entropy\|criticism_debt\|reinstatement_rate\|validity_attack_rate" src/deepreason/capture/detection.py
187:        "attack_target_entropy": entropy,
188:        "criticism_debt": debt,
190:        "reinstatement_rate": (reinstatements / refutations) if refutations else None,
192:        "validity_attack_rate": (len(attacked_nus) / len(nus)) if nus else None,
```
`capture/detection.py::adjudicator_metrics` has FOUR same-named quantities, none
of them §14's, none of them declared signals (they feed `raw_flags`, never
`record_measure`). V-6 was rowed as a two-way collision; it is a three-way one.
Every difference is stated in §3.

**M5 — §14.7's five levers: one exists on `Config`, one exists elsewhere, three
do not exist.**

```
$ grep -n "quota\|QUOTA" src/deepreason/scheduler/scheduler.py src/deepreason/config.py | wc -l
0
$ grep -in "VARIAT" src/deepreason/config.py | wc -l
0
$ grep -n "FRAME_SLICE_ATTACKERS_N\|FRAME_SLICE_DEPARTURES_N" src/deepreason/calculus/render.py
46:FRAME_SLICE_ATTACKERS_N = 5
55:FRAME_SLICE_DEPARTURES_N = 4
```
Render slices exist (as module constants). Critic budgets exist, but as the
ALLOCATION controller's per-seat caps — a different controller with its own
envelope law. Lineage quotas, retrieval balance and variation budgets have no
lever on this tree. §5 says what the design does about that.

**M6 — `K_frame` already ships as a `Config` knob with its versioned line.**

```
$ grep -n "K_FRAME" src/deepreason/config.py src/deepreason/run_manifest.py
src/deepreason/config.py:361:    K_FRAME: int = 2
src/deepreason/run_manifest.py:2433:    data.pop("K_FRAME", None)
```
R6's `K_frame` clause is DISCHARGED BY RUNG 5 and this rung adds nothing to it;
it is reported in the closing ledger with its evidence, not re-implemented.

---

## 1. Frozen-surface grant, requested BEFORE any code is written

`tools/blast_radius.py`'s own computed lists, verbatim (not a summary):

```
"frozen_surface_contacts": [
  {"surface": "manifest schemas and validators (run_manifest.py)",
   "tier": "DIRECT", "target": "src/deepreason/run_manifest.py",
   "detail": "target file is surface path src/deepreason/run_manifest.py"},
  {"surface": "manifest schemas and validators (run_manifest.py)",
   "tier": "SYMBOL_INDIRECT", "target": "_versioned_source_config_data",
   "detail": "'_versioned_source_config_data' referenced in src/deepreason/run_manifest.py (grep-based; not proof of semantic contact)"}
],
"frozen_adjacent_contacts": [],
"frozen_surface_verdict": "CONTACT"
```

**This contact is already authorized, in the operator's own words, and needs no
new STOP.** R17 verbatim: *"FROZEN SURFACES (ladder row): none beyond Config
knobs, each with its `_versioned_source_config_data` line for EVERY schema
version."* The single contact the gate reports is exactly that: ten new
`data.pop(...)` lines, one per new knob, in the one function whose job is to
keep new knobs out of historical source contracts. Nothing else in
`run_manifest.py` is touched — no schema, no validator, no version.

Surfaces 1, 2, 3 and 5: **zero contact**, and the design keeps it that way on
purpose. The one place a reader would expect surface 3 (`invariants.py`) is the
authority audit, and §4 explains why it deliberately does NOT go there.

`qualification_digest` reports `CONFIRMED` for `run_manifest.py` because the
file IS the manifest surface; the ten `data.pop` lines are what makes the
digest NOT move, and the acceptance check in S10 measures that rather than
asserting it.

---

## 2. Items

### S1 (R1) — rent as an explicit criterion on promotion

Files: `src/deepreason/calculus/promotion.py`, `src/deepreason/programs.py`
(registration only).

Before: five pinned promotion criteria. §9.3's empirical clause rides inside
criterion 1 (M1); articulation is not a criterion at all (M2).

After: a SIXTH criterion `promotion_rent`, registered in `PROMOTION_PROGRAMS`,
`programs.PROGRAMS` (`class_="structural"`) and `programs.BLOB_PROGRAMS`
exactly as the other five are — the dual registration is mechanical and its
reason is already written at the top of `promotion.py` (a criterion in
`BLOB_PROGRAMS` alone would count as SUBSTANTIVE, ground reach and confer
prose-immunity; promotion paperwork must do neither).

`promotion_rent` is a pure function of the candidate's bytes and the ONE frozen
reach certificate, like its five siblings. It returns `fail` when the subject is
NOT ARTICULATED, on three legs, in this order:

1. **commitments** — `subject.commitments` is empty. A background that declares
   no commitment has nothing a wound could violate. `fail`
   (`reason: "subject-enumerates-no-commitments"`).
2. **enumerated assumptions** — the ids a departure may name. On this tree the
   assumption ids ARE the subject's own commitment ids: `DepartureDeclarationV1.
   broken_ids` is documented as "the subject's own commitment ids the candidate
   breaks with", and `render.frame_obligations` returns exactly
   `artifact.interface.commitments`. So the leg is: every id in
   `subject.commitments` must resolve to a registered commitment in the
   certificate's frozen `commitments` list. An id a departure could name but
   nothing defines is an unenumerable assumption. `fail`
   (`reason: "assumption-id-not-enumerated"`), or `overrun` when the
   certificate's environment cap dropped it (`truncated` names it) — "we could
   not check" is never a refutation (the `overrun` rule already written into
   `promotion_criteria_sweep`).
3. **vocabulary** — the subject's articulation must be non-empty after
   whitespace normalization, i.e. `articulation_digest`'s head is not "". A
   frame whose subject renders as nothing states no vocabulary, and the frame
   slice would show an empty coordinate system to every conjecture in scope.
   `fail` (`reason: "subject-states-no-vocabulary"`).

**Recorded design note (goes in the code as a constraint comment, not
narration):** legs 2 and 3 are decided from the FROZEN certificate and the
candidate's own bytes, never from live state — Rider 5 clause (4). Leg 2 reads
`certificate.commitments`, not `harness.commitments`.

**Why a sixth criterion and not an extension of criterion 1.** Criterion 1's
verdict is about DEMARCATION (does the subject forbid anything). Rent's is about
ARTICULATION (is what it forbids *enumerable*). A candidate can pass either and
fail the other, and folding them would make one `fail` reason cover two
different defects — which is what makes a promotion refusal unattackable in
practice, since a critic cannot answer a verdict that does not say which thing
was wrong.

accept:
```
python -m pytest tests/test_promotion_rent.py -q          -> N passed, 0 failed
python -c "from deepreason.calculus.promotion import PROMOTION_PROGRAMS; assert len(PROMOTION_PROGRAMS)==6 and 'promotion_rent' in PROMOTION_PROGRAMS"
```
plus a MUTATION PROOF pasted in VALIDATION.md: delete each of the three legs in
a scratch copy; each deletion turns at least one named test RED.

### S2 (R6) — scope-predicate budgets as `Config` knobs, WITHOUT breaking Prop 12.1

Files: `src/deepreason/calculus/scope.py`, `src/deepreason/calculus/claims.py`,
`src/deepreason/calculus/nomination.py`,
`src/deepreason/calculus/promotion.py`, `src/deepreason/config.py`.

Before: `_MAX_DEPTH = 16`, `_MAX_NODES = 512` are module constants read inside
`compile_scope`, which `scope_determinism` (criterion 3) calls.

**The contradiction, stated rather than resolved silently.** R6 asks for these
as `Config` knobs. A criterion's bound read straight off `Config` would make a
promotion VERDICT move when a run's configuration moves without the commitment
moving — which `promotion.py`'s own module docstring already forbids in as many
words ("A bound outside the content address would let a verdict move without the
commitment moving, which is exactly what §0 determinism forbids"), and which
Prop 12.1 rests on.

**The resolution, which is the precedent already in the tree, not a new idea.**
`K_frame` is a `Config` knob AND appears inside the reach certificate as
`k_frame` — the run's configuration chooses the bound once, at nomination, and
the bound then travels INSIDE the content address. Do exactly that:

- `Config.SCOPE_MAX_DEPTH: int = 16`, `Config.SCOPE_MAX_NODES: int = 512`
  (defaults are today's module constants, so no shipped behavior moves).
- `ReachCertificateV1` gains `scope_max_depth: int` and `scope_max_nodes: int`
  beside `k_frame`, populated by `build_certificate` from `Config`.
- `compile_scope(document, *, max_depth=None, max_nodes=None)` — `None` keeps
  the module defaults, so every existing caller and every existing test is
  unchanged (see the census, §7).
- `scope_determinism` passes the CERTIFICATE's two values, not `Config`'s.

after: the knob is configurable; the verdict is still a pure function of frozen
content.

accept:
```
python -m pytest tests/test_calculus_scope_predicate.py tests/test_calculus_nomination.py -q -> 0 failed
python -m pytest tests/test_promotion_rent.py::test_the_scope_bound_comes_from_the_certificate_not_the_config -q
```
The named test is the load-bearing one: it compiles a certificate under one
bound, then changes `Config` to a different bound, re-evaluates the SAME
certificate, and asserts the verdict does not move.

### S3 (R2, R3) — the authority audit (§9.9) as an executable replay program

New file: `src/deepreason/calculus/audit.py`. Export from
`src/deepreason/calculus/__init__.py`.

`authority_audit(harness) -> AuthorityAuditV1` — a pure read over a replayed
root, returning a typed result with one clause per §9.9 sentence and a
`violations` list. Five clauses, each named for the calculus constraint it
executes:

| clause | §9.9 sentence | what the program actually checks |
|---|---|---|
| `C4-derived` | "derived, never stored" | for every consulted grant, re-derive `standing_of(subject)` from `consulted()`/`frames()` and assert the derived set equals the reported one; and assert no artifact/state field stores a standing value (`harness.state` carries no standing map — checked structurally, not by grep) |
| `C3-content-not-type` | "content and edge-structure, never a type" | every grant's `validity`/`validity_domain`/`validity_tolerance` is CONTENT of the frame assertion body, and instrument standing is a `bounded` value of the same field rather than a distinct record type: assert `FrameAssertionV1` is the only body realizing standing and that no second schema name appears among consulted grants |
| `C5-absent-from-labels` | "appears in packs and schedules, never in label computation" | a DIFFERENTIAL: replay the root's own artifact/att/dep sets through `adjudication.grounded.label0` + `adjudication.support.final_labels` with the standing layer's inputs present, and again with every frame assertion's grant REVOKED, and assert every label is identical |
| `N1-attackable` | "every object realizing it ... is attackable" | for each realizing object — the frame assertion, each cited reach case, each of the subject's commitments, each succession ruling — assert it is a REGISTERED ARTIFACT (an id in `state.artifacts`) and therefore a legal `Warrant.target`; a realizing object that is not an artifact could not be attacked |
| `P6-reinstateable` | "and reinstateable" | assert no realizing object's status is absorbing: for each, that its current label is recomputed by the two passes from `att`/`dep` alone (Thm 12.3's shape), so removing the attack restores it. Executed as a differential on a COPY of the relations, never on the record |

**IT MUST BE ABLE TO FAIL (R3).** Each clause gets a seeded-violation test that
constructs a record violating exactly that clause and asserts the audit reports
it. VALIDATION.md pastes both runs for the whole program: the seeded tree RED,
the real tree GREEN — `docs_verify --audit`'s own standard, applied to a
program rather than to a doc check.

**Why NOT in `invariants.py`.** `verify_root` answers "is this record
well-formed and replayable" — surface 3, frozen, and the ladder forecasts zero
contact for Rung 8. The authority audit answers a different question: "does the
CALCULUS's authority story hold on this record". It needs to construct
counterfactual relation sets (clauses C5 and P6) — a `verify_root` limb that
built alternative label sets would be a validator with a simulator inside it.
Keeping it in `calculus/` costs nothing (the gate runs it; §6's checklist runs
it over the tranche's own fixtures) and keeps a frozen surface at zero.

accept:
```
python -m pytest tests/test_calculus_authority_audit.py -q  -> N passed, 0 failed
python -m pytest tests/test_calculus_authority_audit.py -q -k seeded  -> the 5 seeded-violation tests
```

### S4 (R8, R9) — the six §14 diagnostics

New file: `src/deepreason/capture/diagnostics.py`. Export from
`src/deepreason/capture/__init__.py`.

**The window, first, because it is what makes these six different from
everything already on the tree.** `window(harness, m) -> range` computes
`W_m(n) = {max(1, n-m+1), ..., n}` where `n` is the harness's highest applied
event `seq`. SEQUENCE NUMBERS, never wall-clock, never an event count — the
existing `harness.recent_semantic_events(window)` is an event-count window over
a filtered subset and is NOT this. Every one of the six filters by
`seq ∈ W_m(n)`.

**Canonical rounding is part of the policy (R9, A10).** One function,
`canonical(x, precision)`, using `decimal.Decimal.quantize` with
`ROUND_HALF_EVEN` and a precision taken from the POLICY (not hard-coded), and
one formatter that renders the fixed-precision decimal string. Every signal
value is emitted through it, and the precision in force is a field of the
recorded diagnostics payload, so a reader of the record can re-derive the
number without knowing the code's defaults.

The six, each a pure function of `(harness, window, config)`:

| fn | §14 | computed from |
|---|---|---|
| `stream_contraction` | 14.1 | `C_{m,n}` = artifacts registered by a `Conj` event with `seq ∈ W`. `φ_L(a)` = canonical JSON of (sorted `(commitment_id, verdict)` pairs from warrants targeting `a`; sorted declared relation `(role, target)` refs from `a.interface.refs`; `a`'s problem lineage root) → sha256. `N_eff = 1/Σp_z²`; `SC = 1 − (N_eff−1)/(N−1)` for `N > 1`, else `None` |
| `attack_target_entropy` | 14.2 | targets of NEWLY CARRIED attacks: `{warrants[wid].target for (carrier, wid) in state_diff.carry_add, seq ∈ W}` (M3). Normalized Shannon: `−Σq log q / log |{t: q>0}|`, `0.0` when one distinct target, `None` when none |
| `criticism_debt` | 14.3 | `U^old = {a: label unrefuted ∧ n − seq(a) ≥ h}`; `LiveAttackers(a) = {x: (x,a) ∈ att ∧ label(x) ≠ refuted}`; `Debt = |{a ∈ U^old: no live attackers}| / max(1, |U^old|)` |
| `reinstatement_rate` | 14.4 | `harness.transitions()` filtered to `seq ∈ W`, counting `refuted → accepted`, over `N_crit` = newly carried warrants in `W` (the same primitive ATH uses, so the two rates are commensurable); `RR = R→U / max(1, N_crit)` |
| `validity_attack_rate` | 14.5 | `N_ν` = newly carried warrants in `W` whose target is the `validity_node` of some registered warrant; `N_att` = all newly carried warrants in `W`; `VAR = N_ν / max(1, N_att)` |
| `exogenous_grounding_ratio` | 14.6 | `W^live` = warrants registered in `W` whose carrier's label is not refuted. `ExternallyGrounded(w)`: walk `w.validity_node` → that artifact's own carried warrants → their validity nodes, marking visited. A leaf is EXTERNAL when the node carries a program-evaluable commitment with a declared step budget, or is an admitted evidence/import-role artifact, or is an appellate ruling. A revisited node is a CLOSED LOOP and the warrant is not externally grounded. `EGR = |externally grounded| / max(1, |W^live|)` |

Every one returns `None` for the empty case rather than `0.0`, and every
`None` is emitted as the literal `none` rather than a number — a zero that
means "no data" is the reading error these six exist to prevent.

`diagnostics(harness, config) -> Capture14VectorV1` returns all six plus `n`,
`m`, `h` and `precision`, so the payload states the window it was computed over.

accept:
```
python -m pytest tests/test_capture14_diagnostics.py -q     -> N passed, 0 failed
python -m pytest tests/test_capture14_diagnostics.py -q -k "wall_clock or determinism"
```
Two properties get their own named tests: (a) the six are byte-identical across
two computations over the same record (determinism / A10), and (b) no diagnostic
reads `time`, `datetime`, or `Event.ts` — asserted by AST scan of the module,
not by grep, so a `from datetime import` cannot slip past it.

### S5 (R11, R12) — the hysteresis controller (§14.7)

New file: `src/deepreason/capture/hysteresis.py`.

`step(harness, config) -> dict | None`. Deterministic, and it does exactly two
things: it decides a MODE, and it records a POLICY ARTIFACT. It writes no knob
itself.

- **Enter:** `T_enter(D)` holds when at least `CAPTURE14_ENTER_K` of the six
  diagnostics are in their alarm band. Bands REUSE the existing capture
  thresholds wherever one exists — `ATTACK_ENTROPY_FLOOR` for ATH,
  `CRIT_DEBT_CEILING` for Debt, `LAMBDA_FLOOR` for EGR — which is G-4's
  "extend the existing instruments" in its most literal form (S6b). SC gets a
  new `CAPTURE14_SC_CEILING`; RR and VAR use `== 0.0` with the existing
  `MIN_ATTACKS_FOR_RITUAL` floor for "enough attacks to mean anything", which
  is the shape `raw_flags` already uses.
- **Exit:** `T_exit(D)` is STRICTER — at most `CAPTURE14_EXIT_K` (default 0)
  diagnostics in band. That asymmetry IS the hysteresis; it is not a tuning
  choice and the two knobs cannot be set to make it symmetric (validated on
  `Config`).
- **The policy artifact** `capture14-hysteresis.v1` is an ordinary registered
  artifact through `harness.create_artifact` with `Rule.REFL`, exactly as
  `Controller._emit_policy` already does — attackable (a critic warrant may
  target it), replayable (it is in the log), and reviewable by the EXISTING
  `config_referee` role (R12), which needs no new LLM role (R17). Its body
  carries: the mode, the diagnostic vector that justified it, the precision in
  force, the bands, and the `adjustments` it authorizes.
- **The five levers, disclosed rather than faked (M5).** `adjustments` names
  only levers that EXIST: `render_slices`, with the widened budgets it
  authorizes. The other four — `lineage_quotas`, `retrieval_balance`,
  `critic_budgets`, `variation_budgets` — appear in a `no_lever` list with a
  stated resolution each, reusing `allocation.open_loop_signals`'s established
  disclose-never-die shape. `critic_budgets` states that the lever exists but is
  owned by the allocation controller under its own envelope law, and that two
  controllers writing one cap is a defect this rung declines to create.

**Theorem 14.1 is structural here, not promised.** The module contains no
artifact/warrant/edge/label constructor, mirroring
`INV-signal-contract`'s existing check on `allocation.py`:
`! grep -qE "att_add|dep_add|Warrant\(|register_fail_warrant|_adjudicate" src/deepreason/capture/hysteresis.py`
(`create_artifact` is present, for the policy itself, and only for it — the
policy having a status is the design, P6, exactly as it is for allocation).

accept:
```
python -m pytest tests/test_capture14_hysteresis.py -q      -> N passed, 0 failed
python -m pytest tests/test_capture14_hysteresis.py -q -k "theorem_14_1 or differential"
```
The differential is the gate obligation: one scripted record, the controller in
`normal` and in `diversify`, and every label, every `att` edge, every `dep`
edge and every warrant identical — the policy artifact itself excluded, as
allocation's own differential excludes its policy for the same reason. MUTATION
PROOF pasted in VALIDATION.md: in a scratch copy, wire the mode into label
computation; RED; restore; GREEN.

### S6 (R4, R5) — capture integration

**S6a (R4, G-5) — before/after conditioning diagnostics on promotion events.**
File: `src/deepreason/scheduler/scheduler.py` (see S7).

An ELEVATION is the cycle in which a consulted grant first exists for an
assertion. Two records, both `capture14.promotion-conditioning.v1`:

- `phase: "before"`, emitted at the elevation, carrying the diagnostic vector as
  it stands at elevation and `conditioned_problems` — the count of problems the
  new grant's scope now frames (`standing.framed_problem_ids`). That count IS
  the size of the conditioning surface the elevation just created.
- `phase: "after"`, emitted at the NEXT diagnostics emission after the
  elevation, carrying the vector recomputed once the frame has actually
  conditioned a cycle's worth of generation.

**Both are derived from the log, not from scheduler state.** "Which elevations
still owe an `after`" is computed by reading back the `before` records that have
no matching `after` — so a resumed run owes exactly what it owed before, and no
in-process variable can disagree with the record.

**S6b (R5, G-4) — the existing instruments extend to the new surface.** Two
concrete extensions, not a claim:
1. `capture/detection.py::raw_flags` gains no new flag and changes no verdict;
   the §14 family is a SECOND, declared population (§3), and the hysteresis
   controller REUSES `raw_flags`'s own thresholds (`ATTACK_ENTROPY_FLOOR`,
   `CRIT_DEBT_CEILING`, `LAMBDA_FLOOR`, `MIN_ATTACKS_FOR_RITUAL`) rather than
   inventing a parallel set. One band vocabulary, two instrument families.
2. The frame slice — the conditioning surface itself — becomes measurable: the
   `before` record's `conditioned_problems` is the first number this harness has
   ever had for "how much of the run does this frame now sit on top of".

**S6c (R6) — slice budgets as `Config` knobs, at zero test churn.**
File: `src/deepreason/calculus/render.py`.
`frame_slices(harness, problem_id, *, attackers_n=FRAME_SLICE_ATTACKERS_N,
departures_n=FRAME_SLICE_DEPARTURES_N)`. The module constants stay as the
defaults, so the 16 test lines and 2 map checks that pin them do not move
(§7). `render_frame_slice_context` / `render_frame_crisis_context` resolve the
two budgets from the latest recorded hysteresis policy via a lazily-imported
`hysteresis.slice_budgets(harness, config)`; with no policy on the record they
get the `Config` defaults, which are the module constants. In `diversify` mode
the budgets WIDEN: more of the frame's own standing attackers and more already
declared departures are shown. Widening the crisis is diversification — it is
the frame's own indictments and the ways others have already broken with it.

accept:
```
python -m pytest tests/test_frame_render.py -q              -> 0 failed (unchanged)
python -m pytest tests/test_capture14_promotion_conditioning.py -q -> N passed
python -m pytest tests/test_capture14_promotion_conditioning.py -q -k "every_promotion or resumed"
```
`every_promotion` is the gate obligation R15 names: over a record with several
elevations, EVERY elevation has both a `before` and an `after`.

### S7 (R8, R4) — emission, once per cycle, beside the three that already fire

File: `src/deepreason/scheduler/scheduler.py`, inside
`_record_detection_signals` (the site that already emits the three v2 detection
signals every cycle, "so the series is complete rather than sampled").

Order, fixed and canonical: compute the vector once; emit the six; emit any owed
`after` records; detect new elevations and emit their `before` records; run the
hysteresis step. Computing once and emitting six times from one vector is what
makes the six commensurable — six independent computations could straddle a
cycle boundary and describe different windows.

accept:
```
python -m pytest tests/test_capture14_emission.py -q        -> N passed, 0 failed
python -m pytest tests/test_premise_channel_loop.py -q      -> 0 failed (the three Rung 2 signals still fire)
```

### S8 (R10, R13) — eight signal declarations, and the V-6 decision executed

File: `src/deepreason/signals.py`, through `SIGNAL_DECLARATIONS`
(`DR-REC-add-signal`, step 2). No `unspecified` anywhere — a new signal may not
carry the debt marker, and the census test enforces it.

| name | unit | staleness |
|---|---|---|
| `capture14.stream-contraction.v1` | ratio | cycle |
| `capture14.attack-target-entropy.v1` | ratio | cycle |
| `capture14.criticism-debt.v1` | ratio | cycle |
| `capture14.reinstatement-rate.v1` | ratio | cycle |
| `capture14.validity-attack-rate.v1` | ratio | cycle |
| `capture14.exogenous-grounding-ratio.v1` | ratio | cycle |
| `capture14.promotion-conditioning.v1` | event | permanent |
| `capture14.hysteresis-mode.v1` | event | cycle |

The V-6 decision and its execution are §3. `criticism.attack-target-entropy.v1`
gains ONE appended sentence to its `semantics` naming what it is not; nothing
else about it moves — no name, no unit, no staleness, no version.

accept:
```
python -m pytest tests/test_signal_contract.py tests/test_signals.py -q  -> 0 failed
python -c "from deepreason.signals import declaration; ns=['capture14.stream-contraction.v1','capture14.attack-target-entropy.v1','capture14.criticism-debt.v1','capture14.reinstatement-rate.v1','capture14.validity-attack-rate.v1','capture14.exogenous-grounding-ratio.v1','capture14.promotion-conditioning.v1','capture14.hysteresis-mode.v1']; ds=[declaration(n) for n in ns]; assert all(d and d.unit!='unspecified' and d.staleness!='unspecified' for d in ds)"
```

### S9 (R6, R17) — ten `Config` knobs with recorded defaults

File: `src/deepreason/config.py`.

| knob | default | where the default comes from |
|---|---|---|
| `SCOPE_MAX_DEPTH` | 16 | today's `scope._MAX_DEPTH`. **unmeasured** |
| `SCOPE_MAX_NODES` | 512 | today's `scope._MAX_NODES`. **unmeasured** |
| `FRAME_SLICE_ATTACKERS` | 5 | today's `render.FRAME_SLICE_ATTACKERS_N`. **unmeasured** |
| `FRAME_SLICE_DEPARTURES` | 4 | today's `render.FRAME_SLICE_DEPARTURES_N`. **unmeasured** |
| `CAPTURE14_WINDOW` | 200 | **unmeasured**; measurement plan in §8 |
| `CAPTURE14_AGE_FLOOR` | 50 | **unmeasured**; §14.3 fixes no `h` |
| `CAPTURE14_PRECISION` | 6 | declared, not measured — A10 requires a FIXED precision, not a justified one |
| `CAPTURE14_SC_CEILING` | 0.5 | **unmeasured** |
| `CAPTURE14_ENTER_K` | 2 | mirrors `raw_flags`'s existing `sum(ritual_conditions) >= 2`. **unmeasured** |
| `CAPTURE14_EXIT_K` | 0 | the hysteresis asymmetry; validated `< ENTER_K` |

accept: `python -c "from deepreason.config import Config; c=Config(); [getattr(c,k) for k in (...)]"` and
`python -m pytest tests/test_config*.py -q -> 0 failed`.

### S10 (R17) — one `_versioned_source_config_data` line per knob, EVERY schema version

File: `src/deepreason/run_manifest.py`. Ten `data.pop(<knob>, None)` lines,
unconditional (not version-gated), with one comment block stating the reason —
the same reason `K_FRAME`'s line already states: these are consulted at sites
inside the run and never written to the manifest, their effect IS recorded
(the reach certificate carries the two scope bounds; the hysteresis policy
artifact carries its own bands and precision), and omitting the drop would move
every qualification subject digest for a measure threshold, which is the
`ENGAGED_CRITICISM_AUTHORITY` incident exactly (`docs/ERRATA.md` E44).

accept — the digest must NOT move:
```
python -m pytest tests/test_reusable_qualification.py -q    -> 0 failed
python -m pytest tests/test_allocation_signal_consumption.py::test_the_shipped_qualification_subject_digest_does_not_move -q
python scripts/wheel_smoke.py && python -u scripts/wheel_operational_smoke.py
```

### S11 (R17) — exports

`src/deepreason/calculus/__init__.py` (`authority_audit`), and
`src/deepreason/capture/__init__.py` (`diagnostics`, `hysteresis`). No CLI
command, no MCP tool, no console entry point: **the public surface is
unchanged**, so no wheel pin moves. The two smokes are run anyway (S10) because
"unchanged" is a claim about a measured surface.

### S12 (R7, R16) — RESULTS.md: the closing honesty and the closing ledger

Artifact only, in this tranche directory. Two segments:

1. **Every constant this program introduced, with its evidence or the word
   "unmeasured"** (R7) — a table over the whole v2 program, not just this rung:
   `K_FRAME`, `PROMOTION_ENVIRONMENT_MAX`, `PROMOTION_STEPS`, the scope bounds,
   the slice budgets, `ARTICULATION_DIGEST_CHARS`, the eight `CAPTURE14_*`
   values, and the orphan-scheduling term (which has NO constant — the demotion
   is a boolean rank term, not a tunable weight, and saying so is the honest
   entry).
2. **The closing ledger** (R16) — rung by rung: which axioms are now PROVED,
   which PRESERVED, and what the v2 program leaves deliberately open: Rung D's
   parked D2, P4b's quote wording, the IAF layer (§3, D2), and §13's residue
   quoted verbatim.

accept: both segments present; `python tools/docs_verify.py --links` resolves
every `DR-` reference in the map documents this tranche moves.

---

## 3. The two decisions this rung is required to MAKE

### D1 (R13) — V-6: a DISTINCT FAMILY, and the reasons

**Decision: declare a distinct family. Re-found neither Rung 2 signal.**

Four reasons, three of them measurements:

1. **Only one of the two is even a candidate.** `problem.thrash.v1` has no §14
   counterpart at all — §14 has no thrash formula. A decision that can be
   executed on only half its subject is not a decision, and "re-found them" was
   never available.
2. **They read different relations, and the log records the difference (M3).**
   The shipped signal reads `att` — the materialized, closure-expanded standing
   attack relation. §14.2 reads `carry_add` — newly carried warrants, before
   closure. These are not two implementations of one quantity; they are two
   quantities, and the record has always distinguished them.
3. **Re-founding would change a declared signal's MEANING under a fixed
   version.** `criticism.attack-target-entropy.v1` is declared, emitted every
   cycle, and consumed. Changing what the name means while the name and the
   `.v1` stay put is precisely the drift the registry contract exists to
   prevent — worse than the collision it would fix.
4. **The collision is three-way, not two-way (M4).** `capture/detection.py`
   carries four more same-named quantities, none of them declared signals.
   Re-founding two registry entries would have left that untouched and would
   have felt finished.

**How the decision is EXECUTED**, so it is not just a paragraph:

- The six ship under the `capture14.` prefix. Every one of the six declarations
  states, in its `semantics`, the §14 subsection it implements and that it is
  computed over the fixed sequence-number window.
- `capture14.attack-target-entropy.v1`'s semantics says explicitly that it is
  NOT `criticism.attack-target-entropy.v1` and names the difference (newly
  carried attacks in a window vs. the whole standing attack relation).
- `criticism.attack-target-entropy.v1` gains ONE appended sentence saying the
  same thing from the other side. Nothing else about that entry moves.
- The undeclared third population (M4) is recorded in the map with its four
  differences, and a `check:` asserts that `capture/detection.py`'s functions
  are NOT registry signals — so a future author who wires them to
  `record_measure` without declaring them fails the gate.

### D2 (R14) — the IAF question: PARKED, with the price stated

**Decision: PARK. A target-scoped edge-relevance diagnostic does NOT fit this
rung's budget.**

The measurement's verdict is not in doubt and this spec adopts it: a
whole-graph stability certificate is worthless here (97.71 % of candidate edges
relevant, `k = 0` on 0 of 96 roots), and a SEED-TARGETED one carries real
information (96.15 % of candidate spurious edges irrelevant to the seed;
`k = 0` for deletions on 18 of 20 roots).

The price of building it here, itemized: the diagnostic is an exhaustive or
sampled single-edge perturbation sweep re-running BOTH adjudication passes per
candidate edge. `battery_c.py` is a working prototype and took part of a ~9
minute offline run over 96 roots; as a per-cycle signal it needs a bounded
candidate space, a budget, and its own `overrun` semantics — a seventh
diagnostic that is not a formula over the window but a SEARCH. Estimated
250–350 insertions on top of §6's 1 077, which breaks R18's ~1100 ceiling on
its own.

Two further reasons the park is the right call rather than a budget excuse:

- **Its own caveat is unpaid.** The measurement says re-run the battery on
  post-Rung-7 roots before finalizing. That is a battery run, not a code change,
  and it is cheap; building the signal before paying it would validate a design
  on graphs 76 of 96 of which have an EMPTY attack relation.
- **R14 says so.** "Do not build the full uncertain-edge layer here — that is an
  operator scope decision, explicitly."

`PARKED.md` carries the ready-to-send prompt: re-run batteries A–C on
post-Rung-7 roots first, then scope the seed-targeted diagnostic against the
refreshed numbers.

---

## 4. Assumptions (operator may override)

A1 (Q3) — **the six are emitted from `_record_detection_signals`, once per
cycle.** Assumed, operator may override. It is the site that already exists for
exactly this purpose and already promises a complete rather than sampled series.

A2 (Q4) — **`m = 200` sequence numbers, `h = 50`.** Assumed, operator may
override, and recorded as **unmeasured** in RESULTS.md rather than defended.
`m = 200` is chosen so a window spans several cycles on the run shapes this
tree produces (the epoch3 configuration reached 69 accepted artifacts in 2
cycles), and `h = 50` so "old" means roughly a quarter of a window rather than
a fixed number of cycles. Neither number is evidence.

A3 (Q5) — **the hysteresis controller writes no knob directly; it records a
mode and a policy, and the render reads it.** Assumed, operator may override.
It is what keeps Theorem 14.1 structural rather than promised, and it is the
shape the allocation controller already uses.

A4 (R2) — **"succession rulings" as a realizing object means the
`succession-trial.v1` record and the discrimination problem's own artifacts.**
Assumed, operator may override; both are registered artifacts, which is what
the N1 clause needs.

A5 (R11) — **`critic_budgets` is disclosed as owned-elsewhere rather than
steered.** Assumed. Two controllers writing one cap is a defect, and this rung
declines to create it; the disclosure names the lever and its owner.

A6 (S1) — **assumption ids ARE commitment ids on this tree.** Assumed and
stated in the code, because `DepartureDeclarationV1.broken_ids` and
`render.frame_obligations` both already say so. If the operator wants a
separate assumption id space, that is a new claim body and a new rung.

## 5. Questions for operator

**None.** Every fork above was closed by the record or by a recorded operator
value, per `dr-ask-the-right-question`'s dominance test:

- V-6 (Q1) is DECIDED, not asked: R13 requires the decision be made here.
- The IAF fork (Q2) is DECIDED as a park, which R14 explicitly authorizes as one
  of its two outcomes.
- The frozen-surface contact (§1) is pre-authorized by R17 verbatim.
- The scope-budget contradiction (S2) has a resolution already in the tree
  (`K_frame`'s precedent), so it is reported and resolved rather than forked.

## 6. Out of scope (explicit)

- **The uncertain-edge / IAF layer.** Not requested — R14 forbids it here.
- **`invariants.py` / `verify_root` limbs for the audit.** Not requested; §3's
  reason.
- **A diagnostics CLI view or MCP tool.** R17 makes it conditional ("unless a
  diagnostics view ships"); nothing in R1–R16 requires one, so none ships and
  no wheel pin moves.
- **Re-founding `capture/detection.py`'s four metrics on §14.** Not requested.
  V-6 names two signals; the third population is DOCUMENTED (D1) not rebuilt.
- **A live run.** R-none asks for one, and the operator's KNOWN CURRENT STATE
  says this rung launches nothing.
- **A new LLM role for anything.** R17 forbids it; `config_referee` already
  exists for R12.

## 7. Blast-radius census

`tools/blast_radius.py`'s own `consumers` fields, classified. Every hit listed.

**MUST NOT MOVE** (the design is built so these do not):

| target | hits | why it must not move |
|---|---|---|
| `FRAME_SLICE_ATTACKERS_N` | `tests/test_frame_render.py` :29 :143 :148 :150 :151 :432 :444 :447 :703 :711 :712 :714 | S6c keeps the module constant as the default; only a keyword argument is added |
| `FRAME_SLICE_DEPARTURES_N` | `tests/test_frame_render.py` :426 :434 :445 :449 | same |
| `compile_scope` | `tests/test_calculus_nomination.py` :22 :156; `tests/test_calculus_scope_predicate.py` :17 :39 :58 :72 :75 :86 :88; `tests/test_frame_render.py` :1116 :1124 :1135 | S2 adds keyword-only args defaulting to `None` = today's module constants |
| `frame_slices` | `tests/test_calculus_succession.py` :24 :182 :192 :300; `tests/test_frame_render.py` :35 :136 :149 :312 :443 :686 | keyword-only args with today's defaults |
| `_versioned_source_config_data` | `tests/test_reusable_qualification.py` :261 | ten pops is what KEEPS the digest still; S10's accept measures it |
| `src/deepreason/signals.py` | `tests/test_signals.py` :52 | the AST scan; new tags are declared, so it stays green |
| `src/deepreason/run_manifest.py` | `tests/test_decommissioned_pipeline_stays_out.py` :116 | no schema, no validator, no version touched |
| `src/deepreason/calculus/render.py` | `tests/test_calculus_succession.py` :292 | the succession suppression is untouched |
| `src/deepreason/calculus/scope.py` | `tests/test_frame_render.py` :1134 | as above |

**EXPECTED TO MOVE** (the design predicts it):

| target | hits | what moves |
|---|---|---|
| `PROMOTION_PROGRAMS` | `tests/test_promotion_criteria.py` :150 :378 :408; `tests/test_promotion_solo.py` :108 | the tuple grows from five to six. Any test asserting a LENGTH or an exact tuple moves; a test asserting membership does not. Each of the four is inspected and updated minimally in the same commit, and the change is predicted here rather than discovered by the gate |
| `promotion_criteria_sweep` | `tests/test_promotion_closure.py` :119 :135 :149 :159 :161 :170; `tests/test_promotion_solo.py` :129 | the sweep now also fires `promotion_rent`. Fixtures whose subject is unarticulated will newly earn a `fail` — expected, and the design's whole point |
| `ReachCertificateV1` | `tests/test_calculus_anomaly_conservation.py` :33 :106; `tests/test_promotion_solo.py` :155 :158; `tests/test_promotion_succession.py` :29 :50 | two new fields with defaults. Constructions without them keep working; any test pinning the model's field set or a certificate DIGEST moves |
| `build_certificate` | (map only) `docs/map/SUB-calculus.md` :299 | populates the two new fields |

**Map checks EXPECTED TO MOVE, and moving in the same commits as the code:**
`DR-SUB-calculus` (:190 :197 :296 :299 :300 :314 :385 — criteria count, the
sweep, `compile_scope`, `build_certificate`), `DR-SEAM-evaluation-x-rules`
(:246 :247 :267 :268 :323 — the promotion-program set),
`DR-CON-packs-and-token-economy` (:44 :159 :160 — the slice budgets),
`DR-INV-signal-contract` and `DR-REC-add-signal` (the new declarations and the
V-6 family table), `DR-INV-frozen-surfaces` (:194 :231 — the new `data.pop`
lines), `DR-CON-standing-and-background` (the authority audit),
`DR-INV-axiom-basis` (A9 and A10 now PROVED at Rung 8), `DR-SUB-periphery`
(the two new `capture/` modules), `DR-SUB-scheduler` (:114 :115 — the emission
site).

**`reachability: UNKNOWN`** for `PROMOTION_PROGRAMS`, `FRAME_SLICE_ATTACKERS_N`,
`FRAME_SLICE_DEPARTURES_N`, `ReachCertificateV1` — the gate says in writing it
cannot judge these (module-level constants and a pydantic class are not call
targets), so the manual cross-check was run and its hits are the rows above.
`wheel_smoke_pins: []` — no public-surface consumer, consistent with S11.

## 8. The measurement plan R6 requires

Every knob in S9 ships **unmeasured** and says so. What would measure each,
stated so the honesty is falsifiable rather than decorative:

| knob | the measurement that would set it |
|---|---|
| `CAPTURE14_WINDOW` (`m`) | emit the six at several `m` over one committed root and report at which `m` each stops being dominated by its own empty-case; the series is already complete per cycle, so this is a replay, not a live run |
| `CAPTURE14_AGE_FLOOR` (`h`) | the distribution of `n − seq(a)` for artifacts that DID eventually attract a live attacker; `h` should sit above its median or the debt number counts artifacts nobody has had time to attack |
| `CAPTURE14_SC_CEILING` | SC's distribution over committed roots, split by whether the run was later judged to have stalled |
| `CAPTURE14_ENTER_K` / `EXIT_K` | how often `T_enter` fires on roots with no independent sign of capture — a false-positive rate, which needs roots labelled by something other than these six |
| `SCOPE_MAX_DEPTH` / `SCOPE_MAX_NODES` | the depth and node counts of scope documents actually written by models; today's 16/512 have never been approached on any committed root |
| `FRAME_SLICE_ATTACKERS` / `DEPARTURES` | a pack-budget measurement: what the slice costs in tokens against what a candidate does with the extra attackers |
| `CAPTURE14_PRECISION` | not measurable and not meant to be — A10 requires a FIXED precision; 6 is declared |

None of these runs in this tranche. The plan is the deliverable; the numbers
are not.

## 9. Frozen-surface contact forecast

**CONTACT — one surface, pre-authorized.** `tools/blast_radius.py`'s computed
lists are pasted verbatim in §1, together with the operator's words (R17) that
already authorize exactly this contact and nothing else. Surfaces 1, 2, 3, 5
and `route_fingerprint`: `frozen_adjacent_contacts: []`, and the design keeps
surface 3 at zero on purpose (S3's "Why NOT in `invariants.py`").

## 10. Record-observable guardrails

This change adds typed-record OBSERVABLES: eight new measure signals, one new
policy artifact body, and two new `ReachCertificateV1` fields.

- **The reader lands absence-tolerant.** Every new reader (`hysteresis.
  slice_budgets`, the owed-`after` derivation, `authority_audit`) returns the
  pre-change answer when its input is absent, so a root written before this rung
  reads exactly as it did. Asserted by a named test per reader, not by
  inspection.
- **New certificate fields carry defaults**, so a certificate serialized without
  them decodes.
- **No sweep probe is proposed**, and the reason is a standing operator ruling
  rather than an omission: the root sweep is RETIRED as an instrument (operator
  ruling 2026-08-22, CLAUDE.md). The replacement obligation — targeted,
  mutation-proven regression tests committed in the same tranche — is what S1,
  S3, S4 and S5 each carry.

## 11. Budget

Itemized, in INSERTIONS — `tools/diff_budget.py`'s own unit, NOT executable
lines. This is a correction to a twice-recorded mismatch: Rung 6 (759 against
560) and Rung 7 (1027 against 700) both overran because their SPEC estimated
executable lines while the gate counts every docstring, comment and blank line;
Rung 7 parked it as P4. The ratio measured on Rung 7's own new module was 1.90.

```
$ python3 -c "..."
1077 insertions across 11 items
   90  S1 rent criterion
   55  S2 scope budgets into certificate
  170  S3 authority audit
  350  S4 six diagnostics
  115  S5 hysteresis controller
   40  S6 render slice budgets
  100  S7 scheduler emission + G-5
   80  S8 signal declarations
   45  S9 Config knobs
   20  S10 versioned config lines
   12  S11 exports
```

**~1 077 `src/` insertions against R18's ~1 100 ceiling. 7 commits.**
Tests and docs are budgeted separately and are not counted against it, per the
convention Rung 7's DELIVERY records.

R18's STOP does not fire: 1 077 < ~1 100. It is close enough that the ceiling is
a live constraint, not a formality — which is why D2 parks the IAF diagnostic
(250–350 more insertions) rather than absorbing it.

Frozen surfaces touched: **one — `run_manifest.py`, `Config` knobs only,
pre-authorized by R17.**

Rubric: 6/6 yes
- every R has a spec item with a machine-decidable accept — yes (R1→S1, R2/R3→S3,
  R4→S6a, R5→S6b, R6→S2/S6c/S9/§8, R7→S12, R8→S4/S7, R9→S4, R10→S8, R11→S5,
  R12→S5, R13→§3 D1/S8, R14→§3 D2, R15→VALIDATION's six named obligations,
  R16→S12, R17→S9/S10/S11/§1, R18→§11, R19→DELIVERY)
- blast-radius census pasted and every hit classified — yes (§7)
- frozen-surface contact forecast recorded — yes (§1, §9)
- every mechanism the request names traced to code it actually reaches — yes
  (`DR-REC-add-signal`→`SIGNAL_DECLARATIONS` (S8); `config_referee`→
  `referee.run_config_referee`, an existing role (S5); `docs_verify --audit`'s
  standard→S3's seeded-violation tests; `capture/` instruments→M4/S6b)
- DESIGN-AND-STOP only — n/a, this is an implementing tranche
- nothing untraceable to an R/C number — yes (anti-invention pass run; M1–M6 and
  §3's two decisions are all required by R13/R14 or support a cited item)
