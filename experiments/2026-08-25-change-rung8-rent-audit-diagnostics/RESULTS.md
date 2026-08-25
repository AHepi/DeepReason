<!-- honest ledger. Every number here is a pasted command output or a value
     read out of the tree. Residue is stated at the end, not smoothed. -->
# RESULTS — Rung 8: rent, the authority audit, capture integration, the §14 diagnostics

Date: 2026-08-25 · Branch `claude/rung-8-closing-calculus-xgxyzt` ·
Base `origin/main` at `462d6091d` (Rung 7 delivered) · The v2 calculus
program's **closing rung**.

---

## 1. What this rung added that the harness could not do before

Six numbers about its own reasoning, computed over a fixed span of the log
rather than over a stopwatch; a measurement of what elevating a background
costs in conditioning; a criterion that makes a background pay rent in
attackable surface before it may frame anything; and a program that executes
§9.9's authority claims and has been shown to fail when they are violated.

Everything here prices ATTENTION. Nothing here reaches a label, and that is
exhibited rather than asserted — see §4.

---

## 2. The closing honesty obligation (T-7, R7)

> Nomination thresholds, scope predicates, slice budgets, and orphan
> scheduling are empirical constants; both failure directions are measurable
> from the log, and none is defended here.
> — `docs/COMPUTABLE_CALCULUS.md` §13

**Every constant the v2 calculus program introduced, with its evidence or with
the word `unmeasured`.** "Unmeasured" is not a confession; it is the accurate
word, and the ladder asked for it explicitly rather than for a defence.

| constant | value | rung | evidence |
|---|---|---|---|
| `K_FRAME` | 2 | 5 | **reasoned, not measured.** Two is the floor at which "spanning distinct lineages" means anything at all: one lineage is the run's own descent from its seed, which every artifact in a single-question run shares. The argument is in `config.py`; no measurement sets it |
| `PROMOTION_ENVIRONMENT_MAX` | 64 | 5 | **unmeasured.** A bound is REQUIRED (Prop 12.1 needs a declared one) but 64 is not derived from anything. What the cap drops is recorded in the certificate's `truncated` list, so the cost of a wrong value is visible rather than silent |
| `PROMOTION_STEPS` | 4 000 | 5 | **unmeasured.** Lives in `extra["spec"]`, inside the commitment's content address, so a verdict cannot move without the commitment moving |
| `SCOPE_MAX_DEPTH` | 16 | 4 → knob at 8 | **unmeasured, and never approached.** No committed root carries a scope document anywhere near it |
| `SCOPE_MAX_NODES` | 512 | 4 → knob at 8 | **unmeasured**, same |
| `ARTICULATION_DIGEST_CHARS` | 400 | 6 | **unmeasured.** Truncation is disclosed in-band, so a reader can see the cap bit |
| `_ATTACKER_HEAD_CHARS` | 120 | 6 | **unmeasured** |
| `FRAME_SLICE_ATTACKERS` | 5 | 6 → knob at 8 | **unmeasured.** The cap states itself in-band wherever it bites, so a quiet frame and a truncated one are distinguishable |
| `FRAME_SLICE_DEPARTURES` | 4 | 6 → knob at 8 | **unmeasured**, same |
| `CAPTURE14_WINDOW` (`m`) | 200 | 8 | **unmeasured.** §14 fixes no `m`. Chosen so a window spans several cycles on the run shapes this tree produces (the epoch3 configuration reached 69 accepted artifacts in 2 cycles). That is a sizing argument, not evidence |
| `CAPTURE14_AGE_FLOOR` (`h`) | 50 | 8 | **unmeasured.** §14.3 fixes no `h`. Chosen so "old" is roughly a quarter of a window |
| `CAPTURE14_PRECISION` | 6 | 8 | **declared, and not measurable.** A10 requires a FIXED precision, not a justified one. The value travels in every payload so a reader re-derives without it |
| `CAPTURE14_SC_CEILING` | 0.5 | 8 | **unmeasured** |
| `CAPTURE14_ENTER_K` | 2 | 8 | **unmeasured.** Mirrors `raw_flags`'s existing `sum(ritual_conditions) >= 2`, which is itself unmeasured — so this is consistency with an undefended number, not evidence |
| `CAPTURE14_EXIT_K` | 0 | 8 | **structural, not empirical.** Any value below `ENTER_K` gives hysteresis; `Config` refuses a value at or above it. 0 is the strictest recovery available |
| `SLICE_WIDENING` | 2 | 8 | **unmeasured** |
| **orphan scheduling** | — | 2/7 | **THERE IS NO CONSTANT, and that is the honest entry.** `Scheduler._select_problem`'s rank tuple carries `p.id in orphaned` as a BOOLEAN tie-break, after the seed term and after the wound count. There is no weight to tune and therefore nothing to defend. §13 lists orphan scheduling among its empirical constants; on this tree it is not one |

Bands the Rung 8 controller REUSES rather than introduces —
`ATTACK_ENTROPY_FLOOR` 0.2, `CRIT_DEBT_CEILING` 0.5, `LAMBDA_FLOOR` 0.3,
`MIN_ATTACKS_FOR_RITUAL` 5 — are §11's, and they were undefended before this
rung and are undefended after it. Reusing them means a calibration lands once
for both instrument families; it does not make them measured.

**Sixteen constants. One measurement between them, and it is a reasoned floor
rather than an observation.** The calculus defends none of them and neither
does this program. `SPEC.md` §8 states what would measure each; none of it ran
here, and the plan is the deliverable rather than the numbers.

---

## 3. The V-6 reconciliation, decided and executed (R13)

**Decision: a DISTINCT FAMILY. Neither Rung 2 signal was re-founded.**

The collision turned out to be three-way rather than two-way, which is the
measurement that decided it:

| population | reads | declared? |
|---|---|---|
| `criticism.attack-target-entropy.v1` (Rung 2) | the whole standing `att` relation, after closure | yes |
| `capture14.attack-target-entropy.v1` (§14.2, Rung 8) | only `carry_add` — attacks newly carried inside `W_m(n)` | yes |
| `capture/detection.py::adjudicator_metrics` | four same-named quantities over an EVENT window | **no** — never emitted |

Four reasons, three of them measurements: `problem.thrash.v1` has no §14
counterpart at all, so "re-found them" was never available for both; the log
records `att_add` and `carry_add` as separate relations, so these are two
quantities rather than two readings of one; changing what a declared `.v1`
means while its name stays put is the drift the registry exists to prevent;
and the third population would have been left untouched by any re-founding.

**Executed, not merely decided.** Each registry entry names the other from its
own side; `DR-INV-signal-contract` carries the three-population table; and a
check asserts `detection.py` emits no measure, so wiring those four undeclared
fails the gate. The decision is also a TEST — on one record, with the window
moved past both carriages, §14.2 goes absent while the shipped signal still
reads 1.0:

```
::test_attack_target_entropy_reads_newly_carried_attacks   PASSED
```

---

## 4. The axiom ledger, and the program's CLOSING LEDGER (R16)

### 4a. What Rung 8 answers for

| axiom | Rung 8's part | evidence |
|---|---|---|
| **A9** — render, measures, diagnostics and knowledge views act only through attention | **PROVED** (the diagnostics half; Rung 6 proved the render half) | Theorem 14.1 exhibited by a differential and mutation-proven twice |
| **A10** — all ordering, evaluation, sampling and serialization are canonical | **PROVED**, and for the first time as an explicit POLICY rather than a by-product | `ROUND_HALF_EVEN` at a stated precision; values emitted as fixed-precision decimal STRINGS; absence as `none` |
| **A1** — append-only log, state a pure fold | **PRESERVED** | the audit is a pure read; the conditioning pair and the owed-`after` set are derived from the log, so a reopened harness owes exactly what it owed |
| **A2** — finite-budget deterministic verdicts | **PRESERVED, where it was one line from being lost** | the scope bound travels inside the certificate, not on live `Config` |

### 4b. The v2 program, rung by rung

| axiom | proved at | preserved by |
|---|---|---|
| A1 log/fold | already true — Rung 1 records it | every rung, **8** included |
| A2 finite-budget verdicts | already true | every rung; **8** kept a knob out of a verdict |
| A3 grounded pass then support pass | already true | 2, 3, 4, 6 |
| A4 standing derived, never in status | **4** | 5, 6, 7, **8** — and 8 makes it EXECUTABLE as §9.9's C4/C5 clauses |
| A5 mention-not-dependence | **2** (attributions), **4** (frame assertions) | 3b |
| A6 frame-separation on consulted assertions | **3b** | 4, 7 |
| A7 problems immutably record pose-time assertions | **4** | 6, 7 |
| A8 reach spawns, never labels | **5** | **8** |
| A9 attention-only render/measures/diagnostics | **6** (render), **8** (diagnostics) | 2, 5, D |
| A10 canonical everything | already true | every rung; **8** states it as policy |
| Ax 4.1 Genesis Inertness | stated at **4** | every rung; **8** reads provenance only in `EGR`'s evidence leg, which is a diagnostic and not an appraisal |

### 4c. What the v2 program leaves DELIBERATELY open

Not a list of failures. Each of these was seen, priced, and left.

1. **Rung D — proof debt and Duhem localization.** Unnumbered and
   operator-scheduled by design. Its **D2** is the parked half: the operator's
   own siren case answered Road B at Rung 2, and the *localization* criticism —
   "the fault in this bundle is member m" — is not built. The rule it must not
   break is written down: blame assignment stays non-automatic.
2. **P4b — the quote wording.** P4's citability landed 2026-08-16; the wording
   half of it stayed parked and still is.
3. **The IAF / uncertain-edge layer.** PARKED here as P1, with its price and
   with its unpaid caveat sequenced first (re-run the battery on post-Rung-7
   roots BEFORE scoping the diagnostic). The measurement's verdict stands:
   whole-graph stability certificates are worthless on these graphs
   (97.71 % of candidate edges relevant, `k = 0` on 0 of 96 roots) and
   seed-targeted ones are cheap and meaningful (96.15 % irrelevant to the
   seed). Building it here would have cost 250–350 insertions on a tranche
   already over its ceiling, and would have validated a design on a corpus
   76 of whose 96 roots have an EMPTY attack relation.
4. **§13's residue, verbatim** from `docs/COMPUTABLE_CALCULUS.md`:

   > Capture instruments detect stalled dynamics; a consensus ossified around
   > a shared blind spot is invisible from inside, and only the exogenous
   > anchors bear on it, which is why the grounding floor is load-bearing
   > rather than decorative. Nomination thresholds, scope predicates, slice
   > budgets, and orphan scheduling are empirical constants; both failure
   > directions are measurable from the log, and none is defended here.
   > Succession neutrality is symmetric exposure, not neutrality. And a
   > wounded background with no arriving rival frames forever — refuted,
   > indicted in every pack, unreplaced, and never declared irreplaceable
   > (N3). The calculus keeps the crisis visible and the succession problem
   > open; it cannot force the successor into existence. That is not a gap in
   > the machinery. It is what the growth of knowledge is like.

   Rung 8 changes nothing in that paragraph and could not have. It SHIPS the
   capture instruments the first sentence is about, and the first sentence is
   the reason they are not more than they are: the six detect stalled
   dynamics, and a run whose generator, critics, evidence interpretation and
   standards share one blind spot reads healthy on all six.

---

## 5. What remains unproven

Stated as residue, not smoothed.

1. **Nothing in this rung has run live.** The operator's own launch conditions
   said this rung launches nothing, and it did not. Every §14 number in this
   tranche comes from hand-built fixtures or from replaying committed roots.
   No live run has ever emitted `capture14.*`, and what the six will read on a
   real glm-5.2 run is **unknown**.
2. **The hysteresis controller has never entered `diversify` on a real
   record.** Every entry in the tests is forced by a config whose bands are set
   to trip. Whether the shipped bands ever fire — or fire constantly — is
   unmeasured, and it is the same question as `CAPTURE14_ENTER_K`'s.
3. **`SC`'s behavioural signature is a design choice, not a measurement.**
   §14 says "commitment-verdict vector, declared relations, problem lineage";
   the decision to enter relations as ROLE COUNTS rather than as targets is
   forced (targets make every signature unique and SC identically 0), but no
   measurement says role counts are the right granularity.
4. **`EGR`'s three anchor kinds are a reading of §14.6, not a derivation.**
   Budgeted program check, import-role evidence, and an appellate ruling
   recognised by content. A fourth kind of genuine external contact would be
   scored as a closed loop until someone adds it.
5. **The G-5 `after` record measures one cycle of conditioning.** A frame whose
   effect on the stream appears over ten cycles is not measured by it. The
   pair is a boundary comparison, and it is named as one.
6. **The audit's C5 differential revokes GRANTS, not conditioning.** It proves
   standing does not reach a label. It does not — and cannot — prove that what
   the frame slice showed did not change what was conjectured, which is
   precisely the conditioning G-4 is about and precisely what a diagnostic
   rather than a proof is for.
7. **The blast-radius gate returned eleven false frozen-surface contacts** for
   this tranche (PARKED P2). Semantic contact was disproved by direct
   measurement, but a disclosure instrument that cries wolf eleven times is
   one a twelfth, real finding can hide inside.

Accepted does not mean true. These are the record's numbers, not the world's.
