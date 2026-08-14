# LADDER — the v2 implementation program

Deliverable 2 (REQUEST.md R16–R17). Each rung is **one tranche**, routed through
`dr-change-orchestrator`, with its own REQUEST/SPEC/CHECKLIST/VALIDATION/
DELIVERY. Rows cited as `S-3`, `D-2`, `P-11` etc. are `RECONCILIATION.md` drift
rows.

**The invariant that governs every rung, without exception:**

> Every committed run root replays byte-unchanged, at every rung.
> `python tools/root_sweep.py` must show zero verdict drift before AND after.

---

## 1. The suggested shape, verified against the drift table (R16)

The operator's suggested seven stages hold **in their dependency order**. Two
corrections came out of the verification, both recorded with their reason
rather than applied silently:

**Correction 1 — the cascade's general half must ship WITH the premise
channel, not five rungs later.** The suggested shape puts "premise channel +
spawn-trigger deletion" at stage 2 and "falls/cascade/orphans" at stage 6. But
H1 deletes succession-by-failure and H2's replacement for it is the **translate**
resolution of the orphan cascade. If the deletion lands before the resolutions
exist, the harness spends four rungs with *no succession mechanism at all* —
a regression window the drift table's own H1 row forbids ("succession
survives; it just stops being a byproduct of one candidate dying"). The
cascade has two entry conditions and only one of them needs frame assertions:

| Entry condition | Needs | Lands at |
|---|---|---|
| attribution unrefuted ∧ premise refuted (H2's general case) | nothing beyond the premise channel | **Rung 2** |
| a consulted frame assertion leaves unrefuted standing (§9.8's original case) | frame assertions + promotion | **Rung 7** |

So the cascade MECHANISM (marks, three resolutions, retirement, scheduler
deprioritization) ships at Rung 2, and Rung 7 wires the second entry condition
plus the fall/revocation grades into the same, already-proven machinery.

**Correction 2 — the spawn-trigger deletion earns its own rung.** It is the
only rung in the program that REMOVES behavior; its gate is a measurement
("nothing addressable was lost"), not a feature demonstration; and it is the
one change that could silently starve a live run. Bundling it with the premise
channel would hide a subtraction inside an addition.

Net: **eight rungs**, mapping onto the operator's seven stages as follows.

| Operator's suggested stage | Rung(s) |
|---|---|
| groundwork / vocabulary | **1** |
| *(signal contract — added by Amendment 2, placement argued in `RECONCILIATION.md` §2L)* | **1b**, with clause (6)'s design law in **1** |
| premise channel + spawn-trigger deletion | **2** (channel + cascade) and **3** (deletion) |
| frame assertions + standing view | **4** |
| promotion problems + programs | **5** |
| render semantics + departure protocol | **6** |
| falls / cascade / orphans | **7** |
| rent / nomination / authority-audit + capture integration | **8** |

---

## 2. Program-wide rules every rung inherits

**Gate, at every rung's boundary, in this order:**

1. `python -m pytest tests/ -q -n 4` — 0 failed, the only acceptable result.
2. `python tools/root_sweep.py <out.txt>` — diff against the previous rung's
   sweep; `valid` and `len(att)` must not move for any root.
3. `python tools/docs_verify.py` (FULL, not `--fast`) — the map moves in the
   same commit as the code.
4. `python scripts/wheel_smoke.py` and `python -u
   scripts/wheel_operational_smoke.py` — **only** required at rungs that change
   the public surface (console entry points, MCP tool set + schema sha), which
   is Rungs 4 and 6; those rungs update the pins in the SAME commit.
5. `python tools/blast_radius.py --files ...` at each `[COMMIT]` checkpoint, and
   `python tools/diff_budget.py` against the rung's ledgered ceiling.

**Frozen-surface discipline, program-wide.** Three of the five surfaces should
receive **zero** contact across the entire program, and a rung that finds itself
touching one has mis-designed something:

| Surface | Forecast across all eight rungs |
|---|---|
| 1. `capabilities/state.py` digests | **zero contact.** Standing is not a capability; nothing in §9 flows through the proposal/work-order maps |
| 2. `harness.py` event application | **zero contact.** Every new object is an ordinary artifact registered through existing `Conj`/`Crit`/`Register`/`Spawn` events. **Retirement and the orphan resolutions are ARTIFACTS, not new event rules** — that single design choice is what keeps this surface untouched, and every rung's SPEC must re-state it |
| 3. `invariants.py` / `verification/` formats | **additive reader-widening only** — new checks appended, existing record formats never altered. Rungs 2, 4 and 7 have forecast contact and must request the grant IN ADVANCE in their own SPEC.md. `INV-frozen-surfaces.md`'s own Trap applies: "A STOP already written in prose is not a STOP that was obeyed" — the CP1-M tranche wrote the finding and shipped anyway |
| 4. Manifest schemas AND validators | **zero contact by design.** Every new per-run mode goes on `Config`, per `INV-frozen-surfaces.md`'s own guidance. **Trap, ledgered:** a new top-level `Config` field is not done until `_versioned_source_config_data` in `run_manifest.py` has an explicit line for it, for EVERY schema version — the `ENGAGED_CRITICISM_AUTHORITY` incident. Rungs 2, 4, 5, 6, 7, 8 each add knobs and each carry this line in their checklist |
| 5. Qualification subject digests | **zero contact, conditional on one rule: the v2 program adds NO new LLM role.** The frame slice is a pack SECTION; departures are candidate CONTENT; promotion and succession use the existing conjecturer / critic / judge / variator roles. A new role would change the pair inventory, change every subject digest, and cost a ~14-minute battery rerun per home. Any rung that thinks it needs a new role must STOP and ask |
| frozen-adjacent `route_fingerprint` | zero contact |

**Standing-law obligations inherited by every rung** (`RECONCILIATION.md` §2K):
all-configs compile (L-1), lifecycle operations reach every run (L-2), a solo
run can do everything (L-3), no outcome weighted on conjecture kind (L-4), no
seat decides evidence (L-5).

---

## 3. The rungs

---

### Rung 1 — Groundwork and vocabulary

**Discharges:** H3 (A-2), P-6 (the new-rule-objects obligation), C-3/C-4/C-5
conformance scaffolding, the map gap recorded in REQUEST.md §3.

**Entry artifacts:** this tranche's `RECONCILIATION.md` + `LADDER.md`; the
operator's answers to `DECISIONS.md`.

**Exit artifacts:** `SPEC.md`, `CHECKLIST.md`, `VALIDATION.md`, `DELIVERY.md`;
a new map concept document `docs/map/CON-standing-and-background.md`
(`DR-CON-standing-and-background`) carrying Prop 9.1's rigidity dilemma as its
rationale section; the status-vocabulary mapping shipped at the view layer.

**Work:**
- The H3 rendering map (`accepted → unrefuted`, with the
  `suspended_unsupported → "orphaned, not false"` gloss) applied in
  `status_display.py`, `report.py`, `findings.py`, CLI views, `views/`, and
  pack rendering. **Stored strings and machine JSON unchanged.**
- The new map concept document, with `check:` lines that would fail if the
  vocabulary drifted back.
- Register the v2 program's signal names in `src/deepreason/signals.py` as they
  are introduced (the registry is AST-enforced by `tests/test_signals.py`) —
  and see `DECISIONS.md` D-7.

**Gate proves:** no calculus proposition (it is vocabulary), but it proves the
program's central discipline in the cheapest possible place: a rendering change
that moves **zero** stored bytes. Root sweep byte-identical; a test asserts
that every root's stored `status` strings are still `accepted`.

**Estimated size:** 150–250 lines (mostly renderers + tests + one map doc).

**Frozen-surface forecast:** none. Public surface unchanged (no new command).

---

### Rung 1b — The signal contract

Added by REQUEST.md Amendment 2 (R29–R36). Numbered `1b` rather than renumbering
the program: the suffix marks POSITION, not size — this is a full tranche, and
the repo has the precedent (`experiments/2026-08-03-change-rung3b-...`).

**Why here and not folded into Rung 4:** argued from the drift table in
`RECONCILIATION.md` §2L. In short — the registry must become a contract BEFORE
the rungs that emit new signals (Rung 2 onward, and G-5's promotion diagnostics
at Rung 8), or every one of them is a retrofit; and its blast radius is disjoint
from the standing layer's.

**Discharges:** SC-1 … SC-6, and the operator's all-configurations law (L-1) in
executable form for the allocation controller.

**Entry artifacts:** Rung 1's DELIVERY, including the CLAUDE.md design law text
for the FROZEN/VERSIONED/FREE layering (clause 6's ledger half).

**Exit artifacts:** the five tranche artifacts; `docs/map/INV-signal-contract.md`
with checks that can fail; **two** REC recipes — `REC-add-signal.md` and
`REC-revise-allocation-policy.md`. **No new skill or workflow** — the operator's
tripwire is explicit: a dedicated workflow only after two recorded recipe
failures (`authoring-skills` E1).

**Work:**
- **The typed signal record** (SC-1): name, unit, producer-agnostic semantics,
  staleness bound. The 89 existing entries in `src/deepreason/signals.py` migrate
  into it; `tests/test_signals.py`'s AST scan keeps its job, now checking
  declaration completeness rather than mere presence.
- **Seat-instance keying** (SC-2): signals key on the seat identity already in
  the record (`seat-bindings.v1`, v1.7 §A — resolved `group →
  provider/model/profile-digest`, already read by `tools/root_sweep.py`), so two
  structurally asymmetric seats filled by one conjecturer throttle
  independently. **Adds no role**, therefore moves no qualification digest.
- **Interface-only consumption** (SC-3): the architecture test — which passes on
  the tree as it stands, since `controller.py`'s only `deepreason` import is
  `deepreason.ontology`. The real migration is the controller's three direct
  `harness.state.status.get(...)` reads, which become declared signals.
- **The compiled topology matrix** (SC-4): solo, no-schools, judges-off,
  legacy-on and the rest each compile, the controller attaches, and every
  policy-referenced signal has a producer.
- **Open-loop disclosure** (SC-5): a typed `allocation open-loop for signal X`
  notice, extending the `controller-authority` record E28's fix already
  established. **Disclose, never die.**
- **The layering** (SC-6) made checkable: FROZEN change protocol, VERSIONED
  registry + policy algorithm (policy-as-recorded-artifact, referee-reviewed via
  the existing `config_referee`), FREE parameter values inside the existing
  `cap_envelope`/`clamp` bounds.

**Gate proves:**
- **L-1 executably:** every configuration class in the matrix compiles; a
  topology missing a producer compiles WITH the open-loop notice and without a
  refusal.
- **SC-3's boundary holds** — and, because it holds today, the test's value is
  that it fails the day someone breaks it, not that it turns anything green now.
- **The FROZEN layer's own clause — "allocation touches efficiency never
  evidence"** — is C5 and L-5 in the controller's terms: a test proves no signal
  and no allocation decision reaches a label. This is the row to be strictest
  about, because seat identity in a signal key is provenance-shaped, and
  provenance that reaches adjudication is the one thing the harness forbids by
  construction.
- Root sweep byte-identical: the migration is a reader/declaration change, and
  signal STRINGS in committed roots keep their spelling (`INV-frozen-surfaces`'s
  own trap: "Renaming a typed reason string" — decline reasons and Measure
  inputs are compared against recorded roots).

**Estimated size:** 450–650 lines, of which the 89-entry migration is the bulk
and is mechanical.

**Frozen-surface forecast:** surfaces 1–5 zero. Surface 5 explicitly zero
because SC-2 adds no role. The one genuine hazard is not a frozen surface but a
frozen *string*: no existing signal name may change spelling during the
migration.

---

### Rung 2 — The premise channel and the problem-layer lifecycle

The largest rung, and the one the operator's H2 is about.

**Discharges:** H2 in full (O-6, S-18, S-19, S-20), A-7/N3, and — per Correction
1 — the general half of the §9.8 cascade. Absorbs parked **P5** (answered) and
**P6**.

**Entry artifacts:** Rung 1's DELIVERY; `DECISIONS.md` answers to D-2 (siren)
and D-3 (derived vs stored `provenance.frame`).

**Exit artifacts:** the five tranche artifacts; a new map document for the
problem-layer lifecycle (pose → attribution → orphan mark → resolution),
recorded in REQUEST.md §3 as the second map gap; updates to
`DR-SEAM-ontology-x-rules` and `DR-SEAM-scheduler-x-rules`.

**Work:**
- `presupposition-wf` as a program commitment: parses an artifact's content into
  ⟨problem-id, premise-artifact-id⟩, passes iff both resolve and the parsed
  premise is the artifact the attribution `mention`s. Registered as an ordinary
  artifact (P6/Refl) — **no `kind` field anywhere** (C3).
- **The premise rent battery** (added by REQUEST.md Amendment 1, R27). A premise
  artifact carries a demarcation criterion at registration — the rent §9.3
  charges a candidate background, applied to premises — so that a premise
  forbidding nothing is refuted **by program**, demonstratively, with no judge
  and no second model family. This is what makes the operator's siren case
  executable on a solo run under the shipped default authority posture. Two
  constraints, both from existing code: the criterion must require a
  **SUBSTANTIVE** commitment, reusing `measures/reach.py::_substantive`
  (structural checks like `json-wf`/`skeleton_wf` prove nothing about the
  subject and must not satisfy it — the self-immunisation trap
  `rules/warrants.py::formally_backed` already documents); and `crit`/`mod`/
  `active` are **unimplemented stubs** today (`RECONCILIATION.md` M-1,
  corrected), so Rung 2 builds the `crit` half it needs and Rung 5 completes
  `active`.
- **Scope boundary, from drift row W-1 and `DECISIONS.md` D-8:** Rung 2 ships
  the channel for premises that fall by demarcation or by a failing formal
  commitment. A premise that is contentful and wrong *by argument alone* needs an
  argumentative-authority road that does not exist in any solo configuration
  today; Rung 2's SPEC.md must state that boundary explicitly rather than let a
  green gate imply the channel is complete.
- The mention-law well-formedness check, generalized (Law 9.4′): an attribution
  carrying a `dependence` ref on its premise FAILS `presupposition-wf`. This is
  the one check that makes the cascade unable to disarm itself.
- `premise_orphaned(π)` as a derived predicate over replayed state (C4), with
  both grades.
- The three resolutions as **ordinary artifacts** addressing the orphan problem:
  retire / translate / independence. Retirement removes π from scheduler
  selection; it does not delete π (P8) and it is itself attackable (N1) — so
  reinstating the premise, or refuting the retirement, returns π to the frontier.
- Lazy materialization + attention-only deprioritization of marked problems (C5).
- **P6's absorption:** a typed operational finding when the anti-relapse gate is
  unarmed. Rung 2 leans on the negative-case-law gate as half of P5's answer, so
  it may not ship on a gate that can be silently inert.

**Gate proves:**
- **Prop 9.7 (cascade totality)** for the premise entry condition: every problem
  with a consulted attribution to a refuted premise receives a mark; no mark
  resolves except by a registered closure.
- **N3:** none of the three resolutions is an insolubility verdict; retirement
  is reversible; a starved problem is a schedule condition, never a verdict.
- **N1 / Lemma 6.1** across the whole siren sequence, including move 8 (the
  faulty instrument): reinstating the premise un-orphans the problem by the same
  computed predicate.
- **A-3 at the problem layer:** a premise-orphaned problem's candidates keep
  their own labels — orphaned ≠ false, one level up.
- **C4:** the marks are recomputed from the log, never stored.
- **The operator's siren sequence, end to end, offline and on a SOLO
  configuration** — π₁ posed, X registered, ρ consulted, X refuted by the
  demarcation criterion (a demonstrative verdict, status-changing under every
  authority mode), π₁ marked, retired; then ν attacked, X reinstated, the
  retirement attacked, π₁ back on the frontier. **No conjecture is proposed on
  π₁ at any point** (R28) and no observation, evidence artifact or judge seat
  appears anywhere in the run.
- **Live-run gate (L-6):** one siren-shaped live run on the existing ladder,
  judged only on typed outcomes — the mark appears, a resolution registers,
  `verify_root` green.

**Estimated size:** 700–1 000 lines (raised from 600–900 by Amendment 1: the
premise rent battery and the `crit` half of demarcation are new work this rung
now owns). This is the rung to split if the diff-budget gate says EXCEEDED; the
natural split is (2a) channel + predicate + rent battery, (2b) resolutions +
scheduler.

**Frozen-surface forecast:**
- Surface 3 — **forecast contact, additive**: `verify_root` should learn to
  check that every orphan resolution names a registered problem and a consulted
  attribution. Reader-widening only; the grant is requested in Rung 2's SPEC.md
  before any code, per the CP1-M trap.
- Surface 4 — zero, but new `Config` knobs (orphan scheduling weight, relapse-
  gate policy) each need their `_versioned_source_config_data` line.
- Surfaces 1, 2, 5 — zero. Explicitly: retirement is an artifact, not a new
  event rule.

---

### Rung 3 — Delete the spawn trigger (H1)

**Discharges:** H1 (D-2 in the drift table), EC-1 and EC-2 errata candidates.

**Entry artifacts:** Rung 2's DELIVERY (the replacement must exist first);
`DECISIONS.md` answer to D-1 (crisis problem).

**Exit artifacts:** the five tranche artifacts; updated `docs/map/SUB-rules.md`
(the successor-inheritance row and the `rsplit("Original problem: ")` note) and
`DR-SEAM-ontology-x-rules` (its `test_successor_descriptions_do_not_nest` check)
— **in the same commit**, since map documents move with the code and are not
errata; the two errata entries themselves, minted against a freshly re-checked
ledger tail (E29 was next free at `50e2397a9`).

**Work:** remove the SUCCESSOR branch from `scan_spawns`; retire
`SpawnTrigger.SUCCESSOR` **as a producer while keeping the enum member**, so
every committed root carrying `trigger: "successor"` still parses. That
distinction is the whole risk of this rung: *stop writing it, never stop reading
it.*

**Gate proves:** no calculus proposition — a deletion proves absence of loss:
- **the frontier-delta measurement** on root `8e22d0431fd2b98d`: the 16 SUCCESSOR
  problems disappear from a re-run's shape and nothing else moves;
- **P7 untouched:** `Conj` is still gated on `Π ≠ ∅`;
- **P8 untouched:** refuted candidates, their warrants, failed commitments,
  verdicts and traces all survive;
- **no addressability lost:** every problem addressable before the deletion is
  addressable after — the deleted successor was a copy of its parent's criteria
  under a new id;
- **root sweep byte-identical**, which is what proves the enum member still reads.

**Estimated size:** 150–250 lines (deletion + regression tests + map + errata).

**Frozen-surface forecast:** none. The enum member is retained precisely so no
stored value becomes unreadable.

---

### Rung 4 — Frame assertions and the standing view

**Discharges:** S-1, S-3, S-5, S-6, S-10, O-9, O-10, T-3, T-4, T-5.

**Entry artifacts:** Rung 3's DELIVERY; `DECISIONS.md` answer to D-5 (scope
predicate language).

**Exit artifacts:** the five tranche artifacts; `CON-standing-and-background.md`
advanced from rationale to mechanism; an update to
`DR-SEAM-adjudication-x-authority` — the seam whose content is the ABSENCE of
traffic, and whose whole job is to keep standing out of label computation.

**Work:**
- Frame assertion as an ordinary artifact with content ⟨subject, scope σ,
  validity, departure protocol⟩ (Def 9.2).
- The mention law (Law 9.4) as a well-formedness commitment — the same shape
  Rung 2 already shipped for attributions, now for its original subject.
- `standing(b)` as a **derived view** (Def 9.3), consumed by render and schedule
  only. `bounded` validity is content, not a third value (C3).
- The scope predicate σ in whatever language D-5 settles, evaluated on problem
  metadata alone (C1 determinism).
- A read-only `standing` view surface (CLI/MCP) — **the rung's one public-surface
  change**, so the wheel-smoke pins move in the same commit.

**Gate proves:**
- **Prop 12.5 (standing never adjudicates):** label computation still reads
  `att`/`dep` only. The strongest form of this gate is a test that a run with
  frame assertions and a run without produce IDENTICAL labels on the same graph.
- **Prop 12.4 (axis independence):** both directions, as the calculus states
  them — status changes without standing changing, and standing changes
  (revocation, by attacking the reach case) without status changing.
- **Thm 12.3:** a frame assertion inherits every exit — refuted by direct attack,
  `suspended_unsupported` by losing its case, reinstated by Lemma 6.1.
- **S-10 revocation with no rule of its own:** attacking the reach case is
  sufficient; no revocation code path exists to be tested, which is the point.
- **L-2 (operations parity):** amend-then-continue over a root carrying a frame
  assertion.

**Estimated size:** 500–700 lines.

**Frozen-surface forecast:**
- Surface 3 — forecast contact, additive: a `standing-integrity` epistemic check
  (mention law held; every consulted assertion addressed to a promotion problem).
  Grant requested in SPEC.md in advance.
- Surface 5 — zero, **conditional on adding no new role**; the standing view is
  read-only and calls no model.
- Public surface — **changes**; wheel smokes run and pins update in-commit.

---

### Rung 5 — Promotion problems and their criteria as programs

**Discharges:** S-8, S-9, D-6 (the promotion spawn trigger), M-4, P-4/O-7/I-2
(the mechanism-load-bearing half of demarcation), T-1.

**Entry artifacts:** Rung 4's DELIVERY; `DECISIONS.md` answer to D-6
(program-first `accounts-for` vs a judge ensemble).

**Exit artifacts:** the five tranche artifacts; `DR-SEAM-evaluation-x-rules`
updated (promotion criteria are ordinary program commitments on the existing
evaluation path).

**Work:**
- Nomination as a **measure-rule** over the log (C5 channel (a)): reach events
  for one subject spanning ≥ `K_frame` distinct problem lineages over a coherent
  candidate scope ⇒ Spawn a promotion problem. **The measure detects; it never
  decides** — the promotion itself is an ordinary Conj→Crit→Adj pass.
- The five pinned criteria as programs: subject-demarcation, reach-integrity
  (against the log's own timestamps, using the existing sealed-holdout machinery,
  I-6), scope-determinism, compatibility (an overlapping consulted assertion
  routes to discrimination — rivals never co-frame), accounts-for.
- Remark 9.5's default-consult closure: criteria instantiated at registration
  generate demonstrative program warrants BEFORE the renderer's next
  consultation, and the renderer consults only assertions addressed to promotion
  problems.
- Pin the mechanism-load-bearing criterion into the root battery for empirical
  scopes, reusing `µ_struct` (P-4). **As a criterion, never a gate** (C5).
- **Complete `active(a)` = `crit(a) ∧ mod(a)`** (drift row M-1, corrected):
  §9.3's rent law is written in terms of `active(b)`, and today
  `measures/demarcation.py` holds two stubs that raise `NotImplementedError`
  with no importers. Rung 2 builds the `crit` half for premises; this rung
  completes `mod` over the existing variator kernel and wires `active` into the
  promotion criteria. If `mod` proves too costly to evaluate per promotion, the
  alternative — rent defined on `crit` plus observation-valuedness alone — is a
  SPEC.md decision for this rung, recorded with its reason, not a silent
  omission.

**Gate proves:**
- **Remark 9.5:** a frame assertion registered outside a promotion problem is an
  ordinary artifact the renderer ignores; an unattacked one addressed to a
  promotion problem does NOT silently frame its scope, because its criteria fire
  first.
- **Prop 12.1:** every criterion terminates inside its declared budget; `overrun`
  means unobtainable, never slow (C2).
- **M-4:** nomination fires on lineage-spanning reach and on nothing else.
- **L-3:** the whole promotion path completes on a solo configuration.
- **Live-run gate (L-6):** nomination measured on a reach-rich committed root
  rather than a synthetic fixture.

**Estimated size:** 400–600 lines.

**Frozen-surface forecast:** surface 4 zero (new constants go on `Config`, each
with its `_versioned_source_config_data` line); surfaces 1, 2, 3, 5 zero. Public
surface unchanged.

---

### Rung 6 — Frame render semantics and the departure protocol

**Discharges:** S-11, S-12, L-5, and the render half of parked **P4**.

**Entry artifacts:** Rung 5's DELIVERY.

**Exit artifacts:** the five tranche artifacts; `DR-CON-packs-and-token-economy`
updated with the frame slice's deterministic allocation;
`DR-SEAM-llm-x-rules` updated.

**Work:**
- The frame slice: for every consulted assertion whose σ matches the problem,
  the pack carries the subject's articulation digest (compressed, expandable by
  view) **and the subject's standing attackers**. Wounds render in-frame, in
  every pack in scope — "the frame ships its own crisis".
- Departures: the slice carries the standing directive that departures are
  permitted and must be declared as a list of broken assumption/commitment ids.
  Declaration removes the hidden-premise criticism's target; the declaration is
  itself attackable. **Nothing scores departures** and **scope predicates never
  read departure declarations** — a departing conjecture cannot be exiled from
  the frame it is criticizing.
- **P4's render half:** the same deterministic section allocation settles what a
  problem that INHERITED its context may cite — the general question P4 raised
  when it measured 0 of 36 sub-problem prompts carrying citable evidence blocks.
  P4b (the "optionally with a quote" wording) is a separate prompt change and
  stays parked.

**Gate proves:**
- **L-5 / Prop 12.5, at the render layer:** the strongest available form — two
  runs over the same graph, one with the frame slice and one without, produce
  identical labels. A slice that changed a label would be a seat deciding
  evidence.
- **L-4 / the R-g guardrail:** an undeclared departure is criticizable; a
  declared one carries no penalty in rank, admission or acceptance.
- **C1:** the slice is a deterministic render; the same problem and state
  produce byte-identical packs.
- Token economy: the slice fits the pack budget; the allocation is logged.

**Estimated size:** 300–450 lines.

**Frozen-surface forecast:** surface 5 zero **only because no new role is
added** — this is the rung most tempted to add one; if a summarizer variant is
needed for articulation digests, it must reuse the existing summarizer role.
Public surface changes if a `frame`/`pack` inspection view ships ⇒ wheel-smoke
pins in-commit.

---

### Rung 7 — Wounds, falls, and succession

**Discharges:** S-13, S-14 (as re-founded by H1), S-15, S-16, S-17, S-20 (full
totality), A-7 at the frame entry, D-7 in the drift table.

**Entry artifacts:** Rung 6's DELIVERY; `DECISIONS.md` answers to D-1 (crisis)
and D-6 (comparative succession).

**Exit artifacts:** the five tranche artifacts; a RESULTS.md segment carrying
§13's residue **verbatim** — "a wounded background with no arriving rival frames
forever… and never declared irreplaceable" (T-8).

**Work:**
- Wounds: nothing new is built. A fail verdict on the subject's own
  observation-valued commitment already yields a demonstrative warrant and a
  refuted status. The rung's job is to prove standing is untouched.
- The second cascade entry condition wired into Rung 2's machinery: a consulted
  assertion leaving unrefuted standing marks every problem carrying it, with
  fall-grade (`premise refuted`) or revocation-grade (`premise unaccredited`).
- Batch translation offers (§9.8): groups of orphans may be materialized
  together — attention only.
- Succession as ordinary discrimination, with the **one proper render
  exception**: the succession pack suppresses the incumbent's frame slice and
  renders both articulation digests, so the trial of a frame is framed by
  neither party (incumbent-judge bias).
- Anomaly conservation: `accounts-for` makes the successor claim the incumbent's
  wounds as its own commitments; the successor's scope statement fixes the
  incumbent's residual validity domain, leaving a bounded-validity assertion —
  instrument standing, authored by the successor, attackable like anything.

**Gate proves:**
- **Prop 9.6 (wound persistence):** a wound changes status(b) and does not change
  standing(b) — the direct consequence of Law 9.4, tested end to end.
- **Prop 9.7, now complete:** both entry conditions, one marking function.
- **§9.7's two grades** distinguished by the two-pass labels with **no new
  machinery** — that absence is the assertion under test.
- **N3 at scale:** a thousand-problem cascade retires, translates and finds
  independent, and not one resolution asserts insolubility.
- **Live-run gate (L-6):** a fall staged on a live root; judged on typed
  outcomes only.

**Estimated size:** 500–700 lines.

**Frozen-surface forecast:** surface 3 forecast contact, additive (a cascade-
integrity check); grant in advance. Others zero.

---

### Rung 8 — Rent, nomination constants, the authority audit, capture integration

**Discharges:** S-7, S-17 (residual-domain authorship), S-21, G-4, G-5, T-7,
P-10.

**Entry artifacts:** Rung 7's DELIVERY, plus the measurements Rungs 5 and 7
produced.

**Exit artifacts:** the five tranche artifacts; a RESULTS.md segment stating
every empirical constant with the measurement that set it, and stating plainly
which are still undefended.

**Work:**
- **Rent (§9.3)** as an explicit criterion set on promotion: a candidate
  background must be `active(b)` with observation-valued commitments wherever its
  scope is empirical, and must be ARTICULATED (vocabulary, enumerated
  assumptions, commitments) — because assumption ids are what departures declare
  against and commitments are what wounds violate.
- **The authority audit (§9.9) as an executable replay program**, not a prose
  assurance: standing is derived (C4), content not type (C3), absent from label
  computation (C5), and every realizing object — assertion, reach case, subject's
  commitments, succession rulings — is attackable and reinstateable (N1, P6).
  **It must be able to FAIL**, or it is decoration (`docs_verify --audit`'s own
  standard: a check that cannot fail is refused).
- **Capture integration (G-4, G-5):** the frame slice is the strongest
  conditioning the calculus ever applies, so promotion events are logged with
  before/after conditioning diagnostics — "the capture cost of elevation is
  measured, not vibed" — and the existing `capture/` instruments extend to the
  new surface.
- **T-7 honesty:** `K_frame`, scope-predicate budgets, slice budgets and orphan
  scheduling ship as `Config` knobs with recorded defaults and a measurement
  plan. The calculus defends none of them and neither does this program.

**Gate proves:** §9.9 as a passing audit that has been shown to fail when
seeded with a violation; G-5's before/after diagnostics present on every
promotion event; and the program's closing honesty obligation — every constant
named, with its evidence or with an explicit "unmeasured".

**Estimated size:** 400–600 lines.

**Frozen-surface forecast:** none beyond `Config` knobs and their
`_versioned_source_config_data` lines.

---

## 4. Frozen-surface forecast, consolidated (R17)

| Rung | S1 digests | S2 harness | S3 verification | S4 manifest | S5 qualification | Public surface |
|---|---|---|---|---|---|---|
| 1 vocabulary | — | — | — | — | — | — |
| 1b signal contract | — | — | — | — | — (adds no role) | — |
| 2 premise channel | — | — | **additive** | — (Config only) | — | — |
| 3 deletion | — | — | — | — | — | — |
| 4 frame assertions | — | — | **additive** | — (Config only) | — | **changes** |
| 5 promotion | — | — | — | — (Config only) | — | — |
| 6 render + departures | — | — | — | — (Config only) | — | possible |
| 7 falls + succession | — | — | **additive** | — (Config only) | — | — |
| 8 rent + audit | — | — | — | — (Config only) | — | — |

"Additive" means: new checks appended; **no existing record format altered**;
grant requested in the rung's SPEC.md before any code is written; blast-radius
disclosure run at every `[COMMIT]` checkpoint.

**The one number that governs all of it:** zero committed roots may change
verdict at any rung. The instrument is `python tools/root_sweep.py`, run before
and after, compared byte-for-byte.

---

## 5. Calculus propositions, and the rung whose gate proves each

| Proposition | Proved at |
|---|---|
| Prop 9.1 (rigidity dilemma) | Rung 1 — recorded as rationale; it is an argument, not a testable behavior |
| Law 9.4 / 9.4′ (mention law) | Rung 2 (attributions), Rung 4 (frame assertions) |
| Prop 9.6 (wound persistence) | Rung 7 |
| Prop 9.7 (cascade totality) | Rung 2 (premise entry), completed Rung 7 (frame entry) |
| Remark 9.5 (default-consult closure) | Rung 5 |
| Prop 12.1 (total computability) | Rung 5 (criteria within budget), re-proved by every rung's replay determinism |
| Prop 12.2 (no confirmation, no credence) | already true; no rung may weaken it |
| Thm 12.3 (no absorbing status) | Rung 4 (frame assertions inherit every exit), Rung 2 (retirement is reversible) |
| Prop 12.4 (axis independence) | Rung 4 |
| Prop 12.5 (standing never adjudicates) | Rung 4, re-proved at the render layer in Rung 6 |
| Prop 12.6 (knowledge is a view) | Rung 5 **only if** `DECISIONS.md` D-4 says build it |
| N1, N3 | Rung 2 (problem layer), Rung 4 (frame assertions) |
| P4 both halves | Rung 5 |
| P11 | the whole program; nothing before Rung 7 discharges it |

---

## 6. Parked absorption, by rung (R19)

| Park | Rung | Half absorbed |
|---|---|---|
| P4 — evidence citability | 6 | render half (what an inherited-context problem may cite). P4b's quote wording stays parked |
| P5 — conviction criteria | 2 | **answered** — option C, reachability narrows via premise-criticism and negative case law; A/B/D rejected in Rung 2's SPEC with reasons |
| P6 — anti-relapse degradation | 2 | typed operational finding when the gate is unarmed. The refuse-to-start policy question stays with P6 |
| the signal-contract design | 1 + **1b** | **fully absorbed.** Clause (6)'s CLAUDE.md design law lands in Rung 1; the typed registry, seat-instance keying, interface pin, topology matrix, open-loop notice, INV document and both REC recipes land in Rung 1b. Supplied by the operator 2026-08-14 (REQUEST.md Amendment 2); it was never in this repository, which is why the original search could not find it |
