# LADDER — the v2 implementation program

Deliverable 2 (REQUEST.md R16–R17). Each rung is **one tranche**, routed through
`dr-change-orchestrator`, with its own REQUEST/SPEC/CHECKLIST/VALIDATION/
DELIVERY. Rows cited as `S-3`, `D-2`, `P-11` etc. are `RECONCILIATION.md` drift
rows.

**REVISED 2026-08-15 under the operator's law of 2026-08-14** (CLAUDE.md, "Old
runs owe the future nothing; new versions optimise for new functions",
`main@003d57ffa`). The obligation that previously governed every rung —

> ~~Every committed run root replays byte-unchanged, at every rung.~~

— is **RETIRED**. No rung owes a replay-byte-unchanged proof over historical
roots, an old-root sweep as a gate, or a reader-widening-only design. Record
formats, digests and readers may change freely where the calculus is better
served by a clean shape than an additive one.

**The invariant that replaces it, and its scope boundary:**

> A CURRENT-version run's record stays typed, append-only, and replayable by
> the code that wrote it. Within-version integrity is the epistemology itself
> ("the record is the only admissible evidence") and is untouched.

Old roots remain in git history as artifacts of their own version. A new ERROR
line in a sweep because a format moved on is the law working, not a finding
(`docs/AUDIT_BASELINES.md`, sweep scope).

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
| *(signal contract — added by Amendment 2, placement argued in `RECONCILIATION.md` §2L)* | **1b**, with clause (6)'s design law in **1**. DELIVERED IN TWO PARTS: 1b-i (declaration side: SC-1, SC-3, SC-6) landed 2026-08-15; 1b-ii (consumption side: SC-2, SC-4, SC-5) is parked ready-to-send at `experiments/2026-08-15-change-rung1b-signal-contract/PARKED.md` |
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
2. ~~`python tools/root_sweep.py`~~ — **removed as a gate obligation** by the
   2026-08-14 law. A rung that changes a CURRENT-version reader may still run it
   to see what moved; nothing requires the result to be empty.
3. `python tools/docs_verify.py` (FULL, not `--fast`) — the map moves in the
   same commit as the code.
4. `python scripts/wheel_smoke.py` and `python -u
   scripts/wheel_operational_smoke.py` — **only** required at rungs that change
   the public surface (console entry points, MCP tool set + schema sha), which
   is Rungs 4 and 6; those rungs update the pins in the SAME commit.
5. `python tools/blast_radius.py --files ...` at each `[COMMIT]` checkpoint, and
   `python tools/diff_budget.py` against the rung's ledgered ceiling.

**Frozen-surface discipline, program-wide — RE-FOUNDED under the new law.**
Three of the five surfaces still receive **zero** contact across the program,
but for a DIFFERENT reason than before. The old reason was cross-version
compatibility, which is retired. The reason that survives is within-version
coherence: a run's own record must be replayable by the code that wrote it, and
a mid-program change to how state is applied or digested breaks the runs of the
version making the change. Where a row below previously said "additive only
because old roots must still read", it now says what the calculus actually
wants:

| Surface | Forecast across all eight rungs |
|---|---|
| 1. `capabilities/state.py` digests | **zero contact.** Standing is not a capability; nothing in §9 flows through the proposal/work-order maps |
| 2. `harness.py` event application | **zero contact — and now for the right reason.** Retirement and the orphan resolutions are ARTIFACTS, not new event rules. That was previously justified as what kept this surface untouched for old roots; re-examined under the new law, it is what the CALCULUS wants independently: Prop 9.7's own proof says "resolutions exist only as registered problem-closures", and a closure that is a registered artifact is attackable (P6, N1) while a closure that is an event rule is not. The conclusion is unchanged; the reason it survives re-choosing is that it was never really a compatibility concession |
| 3. `invariants.py` / `verification/` formats | **free to change shape.** The reader-widening-only constraint existed for old roots and is retired: a rung may give `verify_root` the record format the calculus wants rather than the one that would also have parsed a 2026-07 root. Rungs 2, 4 and 7 have forecast contact and still request the grant IN ADVANCE in their own SPEC.md — the surface is still frozen against CASUAL change, just no longer against SHAPE change. `INV-frozen-surfaces.md`'s own Trap still applies: "A STOP already written in prose is not a STOP that was obeyed" |
| 4. Manifest schemas AND validators | **zero contact by design.** Every new per-run mode goes on `Config`, per `INV-frozen-surfaces.md`'s own guidance. **Trap, ledgered:** a new top-level `Config` field is not done until `_versioned_source_config_data` in `run_manifest.py` has an explicit line for it, for EVERY schema version — the `ENGAGED_CRITICISM_AUTHORITY` incident. Rungs 2, 4, 5, 6, 7, 8 each add knobs and each carry this line in their checklist |
| 5. Qualification subject digests | **zero contact, conditional on one rule: the v2 program adds NO new LLM role.** The frame slice is a pack SECTION; departures are candidate CONTENT; promotion and succession use the existing conjecturer / critic / judge / variator roles. A new role would change the pair inventory, change every subject digest, and cost a ~14-minute battery rerun per home. Any rung that thinks it needs a new role must STOP and ask |
| frozen-adjacent `route_fingerprint` | zero contact |

**Standing-law obligations inherited by every rung** (`RECONCILIATION.md` §2K):
all-configs compile (L-1), lifecycle operations reach every run (L-2), a solo
run can do everything (L-3), no outcome weighted on conjecture kind (L-4), no
seat decides evidence (L-5).

---

## 3. The rungs

**Execution order ≠ listing order, as of 2026-08-15.** The rungs below are
listed in DEPENDENCY order. Execution now follows the operator's own board —
"Rung 3 next, alone; then problem subjects; P4 before any live judgment; A19
queued behind it" — which agrees with the external advice's recommended tranche
order. Concretely:

| # | Tranche | State |
|---|---|---|
| 1 | **Rung 3a** — H1's deletion, alone | **DELIVERED** 2026-08-15 |
| 2 | **Rung 3c** — the claim substrate + companion problem subjects (R59, R60) | next |
| 3 | **P4** — three-layer citable evidence (R62) | after 3c |
| 4 | **Rung 3b** — frame-separation | immediately before Rung 4, because its subject (a consulted frame assertion) does not exist until then |
| 5 | Rungs 4–8, then Rung D | as listed |

`A19` — Rung 2's live pilot — sits behind P4 by R62 and is not scheduled here.


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

**Entry artifacts:** Rung 1's DELIVERY; `DECISIONS.md` answers to D-2 (siren —
Road B, answered) and D-3 (**A: derived**, answered 2026-08-15). Both are in
hand; Rung 2 is unblocked.

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

### Rung 3a — Delete the spawn trigger (H1) — **NEXT, and ALONE**

**SPLIT 2026-08-15.** Rider 2 placed the frame-separation invariant at Rung 3;
Rider 5 then said the successor-loop removal "is the next step, alone", and the
advice it comes from is explicit — "the first code tranche should therefore do
ONLY this". Both riders stand; they cannot both be one tranche. The split
honours each: H1's deletion ships alone as **3a**, and frame-separation becomes
**3b**, below. Nothing is dropped and no requirement moves rung.

The split is also the better shape independently: frame-separation constrains
CONSULTED FRAME ASSERTIONS, and no frame assertion exists until Rung 4. 3a
deletes something live today; 3b constrains something that does not yet exist.

**Discharges:** H1 (D-2 in the drift table), EC-1 and EC-2 errata candidates.

**Entry artifacts:** Rung 2's DELIVERY (the replacement must exist first);
`DECISIONS.md` answer to D-1 (crisis problem).

**Exit artifacts:** the five tranche artifacts; updated `docs/map/SUB-rules.md`
(the successor-inheritance row and the `rsplit("Original problem: ")` note) and
`DR-SEAM-ontology-x-rules` (its `test_successor_descriptions_do_not_nest` check)
— **in the same commit**, since map documents move with the code and are not
errata; the two errata entries themselves, minted against a freshly re-checked
ledger tail (E29 was next free at `50e2397a9`).

**Work (RE-CHOSEN TWICE, 2026-08-15):** remove the SUCCESSOR branch from
`scan_spawns`. **The enum member is KEPT** — see the withdrawal below.

**WITHDRAWN, on evidence found while executing this rung:** the plan below said
to delete `SpawnTrigger.SUCCESSOR` too, and overruled the external advice for
saying otherwise. A census found a SECOND, LIVE producer that has nothing to do
with `scan_spawns` — `easy.py::seed_component` stamps `trigger: "successor"` on
a staged-pipeline component REPAIR problem, from two call sites in
`workflows/website.py`. Deleting the member breaks that path, and fixing it
would drag a whole subsystem into a tranche the operator said must ship ALONE.
The advice's recommendation therefore lands, for a stronger reason than the
advice gave: it argued from old-root parsability, which the 2026-08-14 law had
already retired, while the real reason is a producer nobody had counted.
Delivered in `experiments/2026-08-15-change-rung3a-h1-successor-deletion/`.

The previous design kept the enum member as a dead reader so that committed
roots carrying `trigger: "successor"` would still parse — an additive shape
chosen *only* for old-root compatibility, which is exactly what the rider tells
this program to re-choose. Under the 2026-08-14 law those roots are artifacts of
their own version and are owed nothing. Deleting the member is the clean shape:
the v2 trigger vocabulary then says what v2 actually does, and a reader of the
enum is not left wondering which members are live. Old roots stop parsing under
v2 readers, and that is the law working.

~~**The external advice DISAGREES here and is overruled**~~ — **the advice was
RIGHT and this paragraph is withdrawn.** It is kept struck rather than deleted
because the reasoning failure is the reusable part: the overruling argument was
sound about the law (old roots really are owed nothing) and simply never asked
whether anything CURRENT still produced the value. A compatibility question and
a liveness question look alike and are not, and only one of them survives a law
that retires compatibility.

**ADDED 2026-08-15 by RIDER 5 (R63) — this rung is NEXT, and ALONE.** The
external advice checked the tree and found the refuted⇒successor loop still in
`scan_spawns` with no frontier regression; the operator's disposition for that
finding is "it is the next step, alone" (`RECONCILIATION.md` §2P). Nothing else
rides in this tranche.

**The decisive regression, from the advice verbatim, plus its mutation proof:**

```python
before = set(h.state.problems)
refute(candidate)
scan_spawns(h, config)
assert set(h.state.problems) == before
```

Restoring the old loop must FAIL this test — a mutation proof, not an
assertion, because a deletion is exactly the change whose test can pass
vacuously. The gate also proves every OTHER structural spawn trigger still
fires, so "nothing spawns" cannot masquerade as success.

**Gate proves:** no calculus proposition — a deletion proves absence of loss:
- **the frontier-delta measurement** on root `8e22d0431fd2b98d`: the 16 SUCCESSOR
  problems disappear from a re-run's shape and nothing else moves;
- **P7 untouched:** `Conj` is still gated on `Π ≠ ∅`;
- **P8 untouched:** refuted candidates, their warrants, failed commitments,
  verdicts and traces all survive;
- **no addressability lost:** every problem addressable before the deletion is
  addressable after — the deleted successor was a copy of its parent's criteria
  under a new id;
- ~~root sweep byte-identical~~ — retired with the compatibility law. What the
  gate proves instead is that a v2 run's OWN record round-trips: spawn, replay,
  and re-derive the frontier with the trigger gone.

**Estimated size:** 150–250 lines (deletion + regression tests + map + errata).

**Axioms this rung proves or preserves (R47):** preserves **A1**, **A3**, **A7**.
It proves none — a deletion proves absence of loss, not a new invariant.

**Frozen-surface forecast:** none. The enum shrinks, which under the old law
would have been a stored-value compatibility break and is now simply the
vocabulary matching the behaviour.

---

### Rung 3b — The frame-separation invariant

**Discharges:** R43, R64. Split out of Rung 3 so H1 could ship alone (above).

**Entry artifacts:** Rung 3a's DELIVERY.

**ADDED 2026-08-15 by RIDER 2 (R43) — a REQUIRED invariant: frame-separation.**

The mention law is **necessary but not sufficient** for wound persistence. The
Computable Calculus claimed persistence followed from the frame assertion merely
MENTIONING its subject; the Formalization (§7) shows that in a globally
connected Dung graph a new attack on the subject can propagate through
pre-existing attack cycles and move the assertion's label indirectly. What is
actually needed is a graph condition:

> **Definition 7.2 (frame-separation).** A consulted frame assertion `f` with
> subject `b` is separated when `Comp(f) ∩ Comp(b) = ∅` in the UNDIRECTED graph
> obtained from `att ∪ dep` by forgetting edge directions. **Mention edges are
> excluded from that graph**, which is what makes the invariant satisfiable at
> all: reach records supporting `f` must MENTION rather than DEPEND on the
> subject, or refuting the subject revokes the reach case.

The design ENFORCES component-separation, and this rung's gate proves **Theorem
7.3's precondition** rather than assuming it — i.e. it exhibits the separation,
not merely the mention. Rung 7 then gets to invoke the theorem instead of
re-arguing it.

This lands before Rung 4 rather than inside it because it is a constraint on how
the frame layer may be BUILT, and Rung 4 is where it would first be violated.

**R64 — what a violation DOES.** A frame that fails separation becomes
**UNCONSULTABLE, with a typed diagnostic — never a manufactured refutation.**
An unmet engineering invariant is a reason to stop trusting a frame; it is not
a reason to invent a defeat for it. Putting a fabricated verdict on the graph
to record a code fault would make the record lie about epistemics in order to
report a bug, and the record is the only admissible evidence this system has.

**Gate proves:** the separation invariant HOLDS for every consulted assertion
the rung can construct, and that a constructed violation yields the typed
unconsultable diagnostic and **no attack edge, no warrant, no label change**.

**Estimated size:** 80–140 lines.

**Axioms this rung proves or preserves (R47):** proves **A6** (consulted frame
assertions satisfy frame-separation) and its precondition **A5** (mention, not
depend); preserves **A1**, **A3**.

**Frozen-surface forecast:** none.

---

### Rung 4 — Frame assertions and the standing view

**Discharges:** S-1, S-3, S-5, S-6, S-10, O-9, O-10, T-3, T-4, T-5.

**Entry artifacts:** Rung 3b's DELIVERY; `DECISIONS.md` D-5 answered **A: a fixed
finite DSL**, reusing the `declarative_numeric_v1` shape (v1.6).

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

**Entry artifacts:** Rung 4's DELIVERY; `DECISIONS.md` D-6 answered **A:
program-first `accounts-for`, judges optional** — succession works solo, and a
rubric ruling is admitted only through the existing trial guard.

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
- **`accounts-for` implements the STRONG succession relation** (RIDER 4 / R57,
  drift row E-3; Formalization §3.5 via R46). A good rival covering the same
  explicanda is NOT a strict successor. Four parts, all required:
  **recovery** (`X(e) ⊆ X(e')`, or an unrefuted account of why `e` worked over
  its restricted domain), **rigidity** (the successor is no easier to vary over
  the shared explicanda), **non-immunization** (no proper functional component
  of `e'` is removable while preserving every registered accounting and
  criticism outcome — this is what rejects ad-hoc riders mechanically), and a
  **strictness witness** (at least one of recovery, criticism survival, or
  rigidity is STRICT). Building the weak form and strengthening it later ships
  a program that admits non-successors, and this tranche has already paid twice
  for exactly that ordering.
- Remark 9.5's default-consult closure: criteria instantiated at registration
  generate demonstrative program warrants BEFORE the renderer's next
  consultation, and the renderer consults only assertions addressed to promotion
  problems.
- Pin the mechanism-load-bearing criterion into the root battery for empirical
  scopes, reusing `µ_struct` (P-4). **As a criterion, never a gate** (C5).
- ~~**Complete `active(a)` = `crit(a) ∧ mod(a)`**~~ **— DONE AT RUNG 2, and on a
  different definition.** `measures/demarcation.py` now holds
  `demarcated(a) = crit(a) ∧ load(a)` per Formalization §12.2, which supersedes
  §6's `active`/`mod` (R54). What this rung still owes is §12.2's closing
  clause, which Rung 2 could not meet because premises carry no scope object:
  **for empirical scopes, at least one commitment must be observation-valued**
  (drift row S-5). The stale text below is kept struck rather than deleted so a
  reader of an earlier plan finds out here why the tree does not match it.
  ~~§9.3's rent law is written in terms of `active(b)`; `measures/demarcation.py`
  holds two stubs that raise `NotImplementedError` with no importers; this rung
  completes `mod` and wires `active` into the promotion criteria.~~ Every clause
  of that plan is now false: the stubs are gone, the predicate is
  `demarcated`, and Rung 2 completed both readings. The cost question it raised
  — whether the sampled half is affordable per promotion — is still live, and
  Rung 2's answer transfers: cache per subject, one sample for the life of the
  run, and record a typed abstention when the variator seat is absent.

**Gate proves:**
- **E-3 / R57, the STRONG succession relation:** a rival that recovers the
  incumbent's explicanda and nothing more is REFUSED as a successor — the test
  that would pass under the weak reading and must fail under this one. Plus one
  case per additional clause: an easier-to-vary rival refused on rigidity, a
  rival with an excisable idle part refused on non-immunization, and a rival
  meeting every clause non-strictly refused for want of a strictness witness.
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

**ADDED 2026-08-15 by RIDER 2 (R44) — the THIRD exit grade: contestation.**

The Computable Calculus claims a consulted frame assertion exits standing in
exactly two ways. The Formalization (§8.2) shows that is true only under an
extra axiom the source never states:

> `FrameDecisive(L): ℓ_L(f) ≠ S` for every promotion-addressed frame assertion.

**Do NOT adopt it.** Three grades, honestly, keyed to the label the assertion
lands on:

| grade | label | what it means |
|---|---|---|
| **fall** | `R` (refuted) | the frame assertion itself is defeated — a comparative succession warrant or a direct warranted attack |
| **revocation** | `SU` (suspended-unsupported) | accreditation lost — one or more reach records supporting the promotion case ceased to be unrefuted |
| **contestation** | `S` (suspended / undecided) | unresolved attack under grounded semantics — nobody has won |

`fall` and `revocation` are provably disjoint (Theorem 8.1). `contestation` is
the one the two-exit claim silently assumed away, and adopting `FrameDecisive`
to keep the claim would be choosing a tidy theorem over the calculus's own
label set. A frame in contestation is neither defeated nor accredited, and the
render must say so rather than round it to either neighbour.

**Gate proves:**
- **all three grades are reachable**, each by its own registration, and the
  render distinguishes them — the anti-`FrameDecisive` check;
- **L-5 / Prop 12.5, at the render layer:** the strongest available form — two
  runs over the same graph, one with the frame slice and one without, produce
  identical labels. A slice that changed a label would be a seat deciding
  evidence.
- **L-4 / the R-g guardrail:** an undeclared departure is criticizable; a
  declared one carries no penalty in rank, admission or acceptance.
- **C1:** the slice is a deterministic render; the same problem and state
  produce byte-identical packs.
- Token economy: the slice fits the pack budget; the allocation is logged.

**Estimated size:** 300–450 lines, **plus 60–100 for the third grade and its
render.**

**Axioms this rung proves or preserves (R47):** proves **A9** (render acts only
through attention); preserves **A3**, **A4**, **A10**.

**Frozen-surface forecast:** surface 5 zero **only because no new role is
added** — this is the rung most tempted to add one; if a summarizer variant is
needed for articulation digests, it must reuse the existing summarizer role.
Public surface changes if a `frame`/`pack` inspection view ships ⇒ wheel-smoke
pins in-commit.

---

### Rung 7 — Wounds, falls, and succession

**Discharges:** S-13, S-14 (as re-founded by H1), S-15, S-16, S-17, S-20 (full
totality), A-7 at the frame entry, D-7 in the drift table.

**Entry artifacts:** Rung 6's DELIVERY; `DECISIONS.md` D-1 answered **A: crisis
is a render state only** — no standing-layer spawn trigger; the incumbent's
promotion problem stays on the frontier, ranked by wound count (attention only).
D-6 answered **A** as above.

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
- **ADDED 2026-08-15 by RIDER 2 (R48) — §14's formulas become THE diagnostic
  definitions.** Six, each a deterministic function of a fixed sequence-number
  WINDOW `W_m(n)` and never of wall-clock time:

  | name | what it measures | shape |
  |---|---|---|
  | **SC** | stream contraction | `1 − (N_eff − 1)/(N − 1)` over behavioral signatures, `N_eff = 1/Σp_z²` |
  | **ATH** | attack-target entropy | normalized Shannon entropy of NEWLY CARRIED attacks over their targets |
  | **Debt** | criticism debt | fraction of old unrefuted artifacts with no live attackers, above an age floor `h` |
  | **RR** | reinstatement rate | `R→U` label changes per criticism registration |
  | **VAR** | validity-node attack rate | new attacks on warrant-validity artifacts / all new attacks |
  | **EGR** | exogenous grounding ratio | live warrants whose validity lineage terminates in budgeted checks, evidence or rulings, rather than a closed judgment loop |

  Two obligations ride with them. **Canonical rounding and a declared fixed
  precision are part of the policy**, not an implementation detail (A10). And
  **the hysteresis controller (§14.7) may alter lineage quotas, render slices,
  retrieval balance, critic budgets and variation budgets, and may NOT add or
  remove attack edges, dependency edges, or labels** — Theorem 14.1 is what this
  rung's gate must exhibit, not assume.

  **Reconciliation obligation, rowed as V-6:** the two signals shipped at Rung 2
  (`problem.thrash.v1`, `criticism.attack-target-entropy.v1`) predate this
  adoption and are NOT these formulas — the shipped ATH reads the whole standing
  attack relation, §14.2 reads a window of newly carried attacks. This rung
  either re-founds them on §14 or declares them a distinct family. Leaving two
  things called attack-target entropy is the worse option.

**Gate proves:** §9.9 as a passing audit that has been shown to fail when
seeded with a violation; G-5's before/after diagnostics present on every
promotion event; and the program's closing honesty obligation — every constant
named, with its evidence or with an explicit "unmeasured".

**Estimated size:** 400–600 lines, **plus 200–300 for the six §14 diagnostics,
their window policy and the hysteresis controller.**

**Axioms this rung proves or preserves (R47):** proves **A9** (diagnostics act
only through attention — Theorem 14.1) and **A10** (canonical rounding and
sampling); preserves **A1**, **A2**.

**Frozen-surface forecast:** none beyond `Config` knobs and their
`_versioned_source_config_data` lines.

---

### Rung D (unnumbered, unscheduled) — proof debt and Duhem localization

**ADDED 2026-08-15 by RIDER 4 (R55, R56).** Deliberately unnumbered: it is not
Rung 9, because the operator schedules it and a number would imply it follows
Rung 8. It is written here rather than left in a wish-list so that the end of
Rung 8 is a KNOWN state rather than an assumed-complete one.

**Discharges:** drift rows E-1 and E-2.

**Entry artifacts:** operator scheduling. No rung blocks on it and it blocks no
rung.

**Work, in outline only — a rung is specced by its own tranche, not here:**
- **Proof debt (E-1):** a receipt format `KERNEL_CHECK / OPEN_CERTIFICATES /
  AXIOM_DEBT` travelling with every derived judgment, itemized and attackable,
  with dependents invalidated ON RECOMPUTATION rather than retroactively. The
  harness already does this for one class — warrants carry validity nodes — so
  the work is generalisation, and the first design question is which derived
  judgments are in scope (labels? measures? render decisions?).
- **Duhem localization (E-2):** bundle-level problematicity projects to a member
  only through a standing localization criticism, which is an ordinary
  attackable artifact. Structurally the premise channel's cousin: an attribution
  says "π presupposes X", a localization says "the fault in this bundle is m".
  Reuse `premises.py`'s shape rather than re-deriving it.

**What it must NOT do:** make blame assignment automatic in the name of
convenience. Both rows exist because the automatic version is the tempting one.

---

## 4. Frozen-surface forecast, consolidated (R17)

| Rung | S1 digests | S2 harness | S3 verification | S4 manifest | S5 qualification | Public surface |
|---|---|---|---|---|---|---|
| 1 vocabulary | — | — | — | — | — | — |
| 1b signal contract | — | — | — | — | — (adds no role) | — |
| 2 premise channel | — | — | **additive** | — (Config only) | — | — |
| 3a H1 deletion | — | — | — | — | — | — |
| 3b frame separation | — | — | — | — | — | — |
| 4 frame assertions | — | — | **additive** | — (Config only) | — | **changes** |
| 5 promotion | — | — | — | — (Config only) | — | — |
| 6 render + departures | — | — | — | — (Config only) | — | possible |
| 7 falls + succession | — | — | **additive** | — (Config only) | — | — |
| 8 rent + audit | — | — | — | — (Config only) | — | — |

"Additive" now means only: the grant is requested in the rung's SPEC.md before
any code is written, and blast-radius disclosure runs at every `[COMMIT]`
checkpoint. **It no longer means "no existing record format altered"** — that
clause was cross-version compatibility and is retired.

**The number that governs all of it, replaced:** ~~zero committed roots may
change verdict at any rung~~ → **a v2 run's own record round-trips: written,
replayed, and re-derived by the code that wrote it.** Each rung's gate proves
that on runs it makes itself, not on runs made by earlier versions.

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
| Prop 12.6 (knowledge is a view) | Rung 5 — **D-4 answered A: build it**, always rendered with its definition inline (`knowledge (unrefuted ∧ active ∧ reach > 0)`), never the bare word |
| N1, N3 | Rung 2 (problem layer), Rung 4 (frame assertions) |
| P4 both halves | Rung 5 |
| P11 | the whole program; nothing before Rung 7 discharges it |

### 5b. The axiom basis, and which rung answers for each (R47, R52)

**ADDED 2026-08-15 by RIDERS 2 and 3.** The Formalization's §17 gives a minimal
axiom set sufficient for its thirteen results; v0.1's Axiom 4.1 joins it from
the foundational source. Together they are the backbone of the v2 `INV-` map
document, **owned by Rung 4** (the first rung that has all four layers to
separate). Every rung's gate names the axioms it PROVES and the axioms it
PRESERVES — an axiom nobody answers for is an axiom nobody is testing.

| Axiom | Statement (compressed) | Proved at | Preserved by |
|---|---|---|---|
| **A1** | the log is append-only; state is a pure fold over it | already true — Rung 1 records it | every rung |
| **A2** | all verdicts are finite-budget deterministic results | already true | every rung |
| **A3** | status = grounded attack pass, then the acyclic support pass | already true | Rungs 2, 3, 4, 6 |
| **A4** | standing is a derived consultation relation and never enters status computation | **Rung 4** | Rungs 5, 6, 7 |
| **A5** | a frame assertion mentions but does not depend on its subject | **Rung 2** (the law, for attributions), **Rung 4** (for frame assertions) | Rung 3b |
| **A6** | consulted frame assertions satisfy frame-separation | **Rung 3b** (R43) | Rungs 4, 7 |
| **A7** | problems immutably record their pose-time frame assertions | **Rung 4** | Rungs 6, 7 |
| **A8** | reach can spawn promotion problems but cannot directly alter labels | **Rung 5** | Rung 8 |
| **A9** | render, measures, diagnostics and knowledge views act only through attention | **Rung 6** (render), **Rung 8** (diagnostics) | Rungs 2, 5 |
| **A10** | all set ordering, numerical evaluation, sampling and serialization are canonical | already true — re-proved by every rung's replay determinism | every rung |
| **Ax 4.1** | **Genesis Inertness** — all appraisal predicates are invariant under permutation of provenance records; origin confers neither warrant nor stigma (v0.1) | **Rung 4**'s `INV-` document states it; **no rung may violate it** | every rung |

Genesis Inertness is the one that will be violated by accident rather than by
design, and always in the same shape: a ranking, a gate or a criterion that
reads WHO or WHAT produced a content instead of what it declares. Attention may
read provenance (`RECONCILIATION.md` V-4); appraisal may not.

---

## 6. Parked absorption, by rung (R19)

| Park | Rung | Half absorbed |
|---|---|---|
| P4 — evidence citability | 6 | render half (what an inherited-context problem may cite). P4b's quote wording stays parked |
| P5 — conviction criteria | 2 | **answered** — option C, reachability narrows via premise-criticism and negative case law; A/B/D rejected in Rung 2's SPEC with reasons |
| P6 — anti-relapse degradation | 2 | typed operational finding when the gate is unarmed. The refuse-to-start policy question stays with P6 |
| the signal-contract design | 1 + **1b** | **fully absorbed.** Clause (6)'s CLAUDE.md design law lands in Rung 1; the typed registry, seat-instance keying, interface pin, topology matrix, open-loop notice, INV document and both REC recipes land in Rung 1b. Supplied by the operator 2026-08-14 (REQUEST.md Amendment 2); it was never in this repository, which is why the original search could not find it |
