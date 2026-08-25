# DELIVERY — Rung 7: wounds, falls, and succession

Branch: `claude/rung-7-calculus-wounds-falls-pc3urk`
Base: `origin/main` at `053c129ac` (Rung 6 delivered)
`VALIDATION.md` verdict: **PASS**

## 1. Requirement by requirement, against the operator's verbatim words

### R1 — "WOUNDS: nothing new is built… this rung PROVES standing is untouched by it (Prop 9.6)"

**DELIVERED as a proof, and nothing was built.** A wound is still a fail verdict
on the subject's own observation-valued commitment, minted through the tree's
one warrant constructor. Six proofs, at every layer a wound could have reached.

```
tests/test_calculus_wound_persistence.py ......   6 passed in 0.36s
```

MUTATION PROOF — a clause making a refuted subject lose its own standing:

```
FAILED ::test_a_wound_changes_status_and_leaves_standing_untouched
FAILED ::test_the_wound_renders_in_frame_across_the_scope
FAILED ::test_many_wounds_still_leave_standing_untouched
3 failed, 3 passed in 0.38s
```
restored, then `6 passed in 0.36s`. The three the mutation does NOT kill are
exactly the ones a label-only test would have been satisfied by.

### R2 — "THE SECOND CASCADE ENTRY… one marking function, both entries, no second mechanism"

**DELIVERED.** `premise_orphaned` now collects `(problem, label)` pairs from
both entries and applies ONE grading step. The absence is asserted structurally:

```
tests/test_calculus_cascade_frame_entry.py ..............   14 passed
::test_there_is_no_second_marking_mechanism
    assigning == ['premises.py::premise_orphaned']
```

### R3 — "BATCH TRANSLATION OFFERS (§9.8)… attention only"

**DELIVERED.** `batch_translation_offers` groups open orphans by CAUSE.

```
tests/test_premise_batch_offers.py ...........   11 passed
::test_offering_registers_nothing_and_moves_no_label
::test_declining_every_offer_costs_nothing
```

### R4 — "SUCCESSION as ordinary discrimination, with THE ONE render exception"

**DELIVERED.** The discrimination spawn is untouched; the exception is one site.

```
tests/test_calculus_succession.py ..............   14 passed
::test_the_suppression_is_one_site      calling == ['frame_slices']
::test_the_two_candidates_are_presented_identically
::test_the_candidates_are_ordered_by_content_not_by_arrival
```

### R5 — "ANOMALY CONSERVATION… instrument standing, authored by the successor, attackable like anything"

**DELIVERED as a proof; the machinery shipped at Rungs 4-5.**

```
tests/test_calculus_anomaly_conservation.py ........   8 passed
::test_the_successor_claims_the_incumbents_wounds_as_mentions
::test_a_fallen_subject_keeps_framing_its_granted_domain
::test_the_residual_grant_is_attackable_like_anything
```

### R6-R9 — Q2a, Q2b, Q2c, Q2d

**ALL FOUR DELIVERED**, in the trial record.

```
tests/test_calculus_succession_trial.py ...................   19 passed
Q2a ::test_the_program_road_judges_both_orders
    ::test_the_rubric_road_is_handed_the_articulation_digests
Q2b ::test_a_constructed_order_disagreement_is_a_no_verdict   (CONSTRUCTED)
Q2c ::test_the_criterion_order_is_recorded_and_is_fixed
Q2d ::test_the_flip_rate_is_a_field_not_a_derivation
    ::test_an_empty_rate_cannot_be_read_as_a_clean_one
```

### R10 (Amendment 1) — the ceiling is NOT re-baselined

**HONOURED.** §3 below carries the overrun and its breakdown.

## 2. What the gate proved

```
G1 Prop 9.6 end to end, MUTATION PROVEN            PASS
G2 Prop 9.7 complete, second mechanism ABSENT      PASS
G3 two grades, two-pass labels, no new machinery   PASS
G4 N3 at scale: 1000 problems, no insolubility     PASS  (7 passed, -n 4 green)
G5 Q2a-d with a constructed order-disagreement     PASS
G6 LIVE GATE L-6                                   PASS
G7 A6 and A9 preserved; §13's residue verbatim     PASS
```

**G6, the live gate, in full** — a fall staged on a live root, judged on typed
outcomes only:

```
subject (model-written): {"claim":"The nocturnal urban heat island is
                          primarily an energy-bal…
PROP 9.6 LIVE   subject REFUTED · assertion ACCEPTED · standing unchanged
                marks after the wound: {}   · frame still renders: true
THE FALL        assertion REFUTED · fallen_frames [{grade:"fall"}]
                marks {question-4dd62735…: "premise-refuted"}
                batch_offers [{grade:"premise-refuted", size:1}]
verify_root     0 violations
```

## 3. Size — the overrun, disclosed (Amendment 1)

**1027 src insertions against a ledgered ceiling of 700.** The ceiling is not
re-baselined, per the operator's chosen road.

| File | Insertions | SPEC estimate |
|---|---|---|
| `calculus/succession.py` | 458 | 240 |
| `premises.py` | 136 | 80 |
| `calculus/standing.py` | 126 | 60 |
| `invariants.py` | 87 | 55 |
| `informal/trial.py` | 66 | 30 |
| `scheduler/scheduler.py` | 58 | 45 |
| `calculus/nomination.py` | 33 | 20 |
| `signals.py` | 32 | 12 |
| `calculus/render.py` | 22 | 20 |
| `calculus/__init__.py` | 8 | 15 |
| `verification/report.py` | 1 | 2 |
| **total** | **1027** | **562** |

Tests (2785) and docs (447) are budgeted separately and are not counted
against it.

**The single cause.** SPEC.md's estimate counted EXECUTABLE lines;
`tools/diff_budget.py` counts INSERTIONS, which includes every docstring,
comment and blank line. On the one new module the two differ by 90 per cent —
241 executable against 458 added, so the executable half was within one line of
the estimate. Rung 6 overran for the identical reason (759 against 560), which
makes this the second recorded occurrence; parked as P4 with a prompt.

## 4. Frozen surfaces

| Surface | Contact | Evidence |
|---|---|---|
| 1 `capabilities/state.py` | **zero** | not in the declared radius |
| 2 `harness.py` | **zero** | marks, offers and the trial record are artifacts and derived views, never event rules |
| 3 `invariants.py` / `verification/` | **GRANTED, ADDITIVE** | 87 + 1 insertions, **0 deletions**; silent on a committed root that predates it |
| 4 manifest schemas AND validators | **zero** | no new `Config` field; module constants only |
| 5 qualification subject digests | **zero** | NO new LLM role; `qualification_digest` consumers EMPTY in the census |
| frozen-adjacent `route_fingerprint` | **zero** | census reports none |
| public surface | **unchanged** | both smokes green; `wheel_smoke_pins` EMPTY |

## 5. The map, and one correction to it

Nine map documents moved in the same commits as their code:
`DR-CON-problem-layer-lifecycle`, `DR-SUB-calculus`,
`DR-CON-standing-and-background`, `DR-SEAM-calculus-x-rules`,
`DR-INV-frozen-surfaces`, `DR-INV-axiom-basis`, `DR-SUB-verification`,
`DR-CON-scheduler-ranking`, `DR-SEAM-scheduler-x-rules`, plus
`DR-SEAM-harness-x-verification`'s count pin.

**`docs/ERRATA.md` E51.** `DR-SUB-verification` claimed the epistemic checks
"are not `verify_root` findings at all". That stopped being true at Rung 4 and
this tranche added the second counterexample. Its check pinned ONE member by
name, and a check that names one member cannot notice the set growing.
Corrected with a check over both partitions.

Three map checks were NARROWED or MOVED, each with its reason written down:
the `fail()` count (220 → 223), the parsed rank tuple (the wound term, with
the ORDER now asserted), and `premises.py`'s `deepreason.calculus` proxy
(narrowed to the claim it was always about). A fourth — `consultability` —
was sharpened from a text grep to a CALLER parse, because rewording the code
to satisfy a proxy would have made the code worse to keep a weaker check
green.

## 6. Residue

`RESULTS.md` carries five unproven items and §13's residue verbatim.
`PARKED.md` carries four items, each with a ready-to-send prompt: the epoch3
config's live `operational_failure` at cycle 2, the fact that no live
succession has ever happened, the undecided
separation-lost-after-consultation case, and the estimate/gate mismatch above.

---

**What happens to a framed problem the day its frame falls:** it is marked
`premise refuted`, it drops in the scheduler's ranking, and it is offered — with
every other problem that shared the frame — as one batch that a single
translation into a better vocabulary could answer; it is not deleted, not
retired, and not called insoluble, and defeating the frame's critic un-marks it
by the same computed predicate that marked it.

**What a succession trial now records that a courtroom would recognize:** which
two accounts were compared and in both orders, on the criteria named in a fixed
order that is written into the record, with a hung verdict entered as a hung
verdict rather than broken by a tiebreak — and, beside it, how often this court
reverses itself when the same two parties merely swap tables.
