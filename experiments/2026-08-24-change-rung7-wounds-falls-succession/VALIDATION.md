# VALIDATION — Rung 7: wounds, falls, and succession

Validates only; patches nothing. Every row cites the acceptance check
`SPEC.md` named and the command that produced its evidence.

**VERDICT: PASS.**

## 0. The gate, at the boundary

| Instrument | Result | Against base `053c129ac` |
|---|---|---|
| `python -m pytest tests/ -q -n 4` | **4080 passed, 6 skipped, 0 failed** (1085.92s) | base: 3974 passed, 2 failed (both `-n 4` MCP-thread flakes) |
| `python tools/docs_verify.py` (FULL) | **64 documents, 1047 checks, 3 failed** — all three `CON-run-identity.md`, shallow clone | base: the same 3 |
| `python tools/docs_verify.py --links` | **0 dangling references**, 64 documents | — |
| `python tools/docs_verify.py --audit` | **0 findings** — no check this tranche added is one that cannot fail | — |
| `python scripts/wheel_smoke.py` | passed | unchanged |
| `python -u scripts/wheel_operational_smoke.py` | exit 0 | unchanged |
| `python scripts/cycle_soak.py --case epoch3` | exit 0 (clean), 4/4 death assertions PASS | unchanged |
| `tools/blast_radius.py` | `CONTACT` — surface 3 only, every row a reader the grant names | as forecast |
| `tools/diff_budget.py --ceiling 700` | **EXCEEDED**, 1027 src insertions | disposed, REQUEST.md Amendment 1 |

**0 real failures.** The two `-n 4` MCP-thread flakes the operator named at
baseline passed in this run as well. The three `docs_verify` failures are the
operator's own stated baseline, confirmed rather than assumed:
`git rev-parse --is-shallow-repository` is `true`, the clone holds 85 commits,
and `git cat-file -t 1637e808` returns "Not a valid object name" for the
revision the check pins.

**Three OTHER doc checks failed first, and all three were mine** — the
`fail()` count pin (220 → 223), the parsed rank tuple, and a `consultability`
check that grepped for a STRING where its claim was about CALLERS. Each was
moved with the code in its own commit; none was worked around.

## 1. Requirements

| # | Requirement | Verdict | Evidence |
|---|---|---|---|
| R1 | Wounds: build nothing, prove standing is untouched | **PASS** | `tests/test_calculus_wound_persistence.py` (6), MUTATION PROVEN — CHECKLIST step 4 |
| R2 | The second cascade entry, in Rung 2's machinery, ONE marking function | **PASS** | `tests/test_calculus_cascade_frame_entry.py` (14) |
| R3 | Batch translation offers, attention only | **PASS** | `tests/test_premise_batch_offers.py` (11) |
| R4 | Succession as ordinary discrimination + the ONE render exception | **PASS** | `tests/test_calculus_succession.py` (14) |
| R5 | Anomaly conservation | **PASS** | `tests/test_calculus_anomaly_conservation.py` (8) |
| R6 (Q2a) | Both orders of the two articulation digests | **PASS** | `::test_the_program_road_judges_both_orders`, `::test_the_rubric_road_is_handed_the_articulation_digests` |
| R7 (Q2b) | Order-disagreement is a typed NO-VERDICT, never a tiebreak | **PASS** | `::test_a_constructed_order_disagreement_is_a_no_verdict` |
| R8 (Q2c) | Criterion order fixed or randomized, and WHICH recorded | **PASS** | `::test_the_criterion_order_is_recorded_and_is_fixed` |
| R9 (Q2d) | The per-trial FLIP RATE, first-class | **PASS** | `::test_the_flip_rate_is_a_field_not_a_derivation` and 3 more |
| R10 | The 700 ceiling is NOT re-baselined (Amendment 1) | **PASS** | DELIVERY.md carries the overrun and its breakdown |

## 2. What the gate had to prove

| # | Claim | Verdict | Evidence |
|---|---|---|---|
| G1 | Prop 9.6 END TO END, mutation proven | **PASS** | 6 tests; the mutation kills 3 — CHECKLIST step 4 pastes RED, restore and GREEN |
| G2 | Prop 9.7 complete: both entries, one marking function, second mechanism ABSENT | **PASS** | `::test_both_entries_reach_one_marking_function`, `::test_there_is_no_second_marking_mechanism` (a source scan: exactly one function names a grade constant) |
| G3 | Two grades from the two-pass labels, NO new machinery | **PASS** | `::test_no_grade_is_stored_anywhere`, `::test_the_two_grades_come_from_the_two_pass_labels` |
| G4 | N3 at scale: 1000 problems, all three resolutions, no insolubility verdict | **PASS** | `tests/test_cascade_n3_at_scale.py` (7), green under `-n 4` |
| G5 | Q2a-d present, with a CONSTRUCTED order-disagreement case | **PASS** | `tests/test_calculus_succession_trial.py` (19) |
| G6 | LIVE GATE L-6, judged on typed outcomes only | **PASS** | `l6-typed-outcomes.json` — mark with grade, cascade fires, `verify_root` 0 violations |
| G7 | Axiom ledger: A6 and A9 PRESERVED; §13's residue verbatim | **PASS** | `tests/test_calculus_axioms_rung7.py` (7); RESULTS.md carries the residue |

## 3. Constraints

| # | Constraint | Verdict | Evidence |
|---|---|---|---|
| C-FROZEN | Surface 3 additive, granted in SPEC.md BEFORE code; all others zero; NO new LLM role | **PASS** | 87 and 1 insertions, **0 deletions**; census shows surface 3 only; `qualification_digest` consumers EMPTY; the succession trial uses the existing `judge` seat and works with none |
| C-PUBLIC | Public surface unchanged, no re-pin | **PASS** | both smokes green; `wheel_smoke_pins` EMPTY in the census |
| C-SIZE | 500-700 estimated; STOP above ~900 | **STOPPED, then disposed** | 1027 actual; the tranche stopped at the step-9 checkpoint and put three priced roads to the operator, who chose "continue and disclose" (Amendment 1) |
| C-GATE | Ring while iterating, full gate at the boundary, docs_verify full | **PASS** | §0 |
| C-MAP | Map moves in the same commits | **PASS** | 9 map documents moved with their code; `docs/ERRATA.md` E51 recorded |
| C-PUSH | Commit and push every phase boundary | **PASS** | 10 commits, each pushed with retry |
| C-D1 | Crisis is a RENDER state only; no standing-layer spawn trigger | **PASS** | `::test_no_crisis_problem_spawn_trigger_was_built`, `::test_a_wound_still_spawns_nothing`; the rank term is attention only |
| C-D6 | Program-first `accounts-for`; judges optional | **PASS** | `::test_succession_runs_with_no_judge_seat_at_all`; a rubric ruling enters only through the existing `pairwise_discriminate` guard |

## 4. What FAILED during validation, and what it cost

Recorded because a validation that reports only its successes is a validation
nobody can calibrate.

1. **The live gate failed twice before it passed**, and both failures were
   mine rather than the harness's. The first launched a config the cycle soak
   had not covered (glm-5.2 then qualified at the SHALLOW tier). The second
   staged the fall on a STOPPED root, and `verify_root` refused it with
   `TERMINAL_POST_HORIZON_EVENT_UNAUTHORIZED` — correctly, as a truncated
   replay proves: the run as it stopped had 0 violations, so the post-horizon
   writes were the staging's.

2. **My own gate script hid that failure**, by comparing violation counts
   before and after staging when "before" already carried the violation from a
   partial earlier attempt. A delta test returned PASS on a dirty record. The
   shipped driver tests the ABSOLUTE count, which is what L-6 says.

3. **The gate caught an undeclared signal mid-tranche.**
   `succession.trial-flip-rate.v1` was emitted before it was declared, and
   `test_every_emitted_signal_is_registered` failed on it. Declared through the
   typed channel per `DR-REC-add-signal`.

4. **A structural test caught a second grading site.** The first
   `orphan_causes` compared grade STRINGS to decide which cause explains a
   mark — a second place where a grade was being decided, which is exactly what
   "one marking function" forbids. Precedence is now expressed on the label.

5. **The N3-at-scale file was order-dependent** and would have passed serially
   and failed under `-n 4`, the gate's own configuration. Rewritten
   order-independent and verified under `-n 4`.

None of the five was worked around; each moved the code or the check.

**`--audit` returns 0 findings**, which is the result that matters most for
the `cascade-integrity` limbs: that instrument exists to refuse checks that
cannot fail, and limb 2 was written specifically to survive it — it re-derives
its obligation from the exits and σ instead of asking the marking function on
both sides.

## 5. Residue carried to delivery

`RESULTS.md` §"What remains unproven" carries five items in full. The two a
reader should not miss: every succession proof here is OFFLINE — no live run
has yet produced two rival frame assertions on one promotion problem, so the
succession pack and the trial record have never been exercised by a model —
and the flip rate has no measured value on this harness yet, only an
instrument that will report one.
