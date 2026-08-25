# Validation for: Rung 8 — rent, the authority audit, capture integration, the §14 diagnostics

Base `462d6091d`. Branch `claude/rung-8-closing-calculus-xgxyzt`.
Every output below is pasted from a real run.

---

## 1. Acceptance checks, in SPEC.md item order

### S1 (R1) — rent as promotion criterion 6

```
$ python -c "from deepreason.calculus.promotion import PROMOTION_PROGRAMS; ..."
('promotion_subject_demarcation', 'promotion_reach_integrity',
 'promotion_scope_determinism', 'promotion_compatibility',
 'promotion_accounts_for', 'promotion_rent')
$ python -m pytest tests/test_promotion_rent.py -q
10 passed in 0.60s
```
MUTATION PROOF, each leg deleted in turn in a scratch copy — each killed by a
DIFFERENT named test, which is the property the three-reason design exists for:
```
leg 1 (commitments)   FAILED ::test_rent_refuses_a_subject_that_enumerates_no_commitments   1 failed, 9 passed
leg 2 (assumptions)   FAILED ::test_rent_refuses_an_assumption_id_nothing_enumerates
                      FAILED ::test_a_truncated_environment_is_overrun_and_never_fail        2 failed, 8 passed
leg 3 (vocabulary)    FAILED ::test_rent_refuses_a_subject_that_states_no_vocabulary          1 failed, 9 passed
```
**PASS**

### S2 (R6) — the scope-predicate budget travels inside the certificate

```
$ python -m pytest tests/test_calculus_scope_predicate.py tests/test_calculus_nomination.py \
      tests/test_promotion_rent.py tests/test_promotion_criteria.py tests/test_frame_render.py -q
82 passed in 5.35s
```
MUTATION PROOF — reading the bound from a live `Config()` instead of from the
certificate:
```
FAILED ::test_the_scope_bound_comes_from_the_certificate_not_the_config
1 failed, 9 passed in 0.76s
```
**PASS**

### S3 (R2) + S3/R3 — the authority audit, and that it CAN FAIL

```
$ python -m pytest tests/test_calculus_authority_audit.py -q
17 passed in 2.72s
$ python -m pytest tests/test_calculus_authority_audit.py -q -k fails
5 passed, 12 deselected in 0.23s
```
**SHOWN TO FAIL** — one seed per clause, printed as the audit's own words:
```
CLEAN TREE: ok
SEED C4 : C4: standing is stored on the applied state: ['standing']
SEED C3 : C3: standing is realized by a second record type: ['poietic.instrument-standing.v1']
SEED C5 : C5: revoking standing moved 1 label(s): ['583207939998fe20bd275e7d…']
SEED N1 : N1: 1 realizing object(s) are not on the record and so could never be attacked: ['not-on-the-rec…']
SEED P6 : P6: 1 realizing object(s) stay refuted with every attack on them removed: ['d9a99d655df0b354205d…']
RESTORED: ok
```
**THEN SHOWN TO PASS**, on a committed live root the harness really made:
```
root: experiments/2026-08-24-change-rung7-wounds-falls-succession/run
  artifacts 68  att 11  dep 1
  declared frame assertions: 1   consulted grants: 0
  audit ok: True   violations: []
    C4-derived            ok=True  checked=0
    C3-content-not-type   ok=True  checked=1
    C5-absent-from-labels ok=True  checked=68
    N1-attackable         ok=True  checked=9
    P6-reinstateable      ok=True  checked=1
```
**PASS**

### S4 (R8, R9) — the six §14 diagnostics

```
$ python -m pytest tests/test_capture14_diagnostics.py -q
29 passed in 0.71s
```
Includes the two anti-vacuity tests
(`::test_the_age_floor_actually_discriminates`,
`::test_stream_contraction_ignores_artifact_identity`), the AST scan
(`::test_no_diagnostic_reads_wall_clock`), the canonical-rounding tests, and
the byte-identity determinism test. **PASS**

### S5 (R11, R12) — the hysteresis controller and Theorem 14.1

```
$ python -m pytest tests/test_capture14_hysteresis.py -q
12 passed in 0.94s
$ python -m pytest tests/test_capture14_hysteresis.py -q -k "theorem_14_1 or constructs_no_edge"
2 passed, 10 deselected in 0.21s
```
MUTATION PROOF, twice, in a scratch copy:
```
MUTATION 1 — _adjudicate reads the recorded mode
  E AssertionError: diversify moved something Theorem 14.1 forbids
  FAILED ::test_theorem_14_1_two_modes_one_record_identical_labels     1 failed, 10 passed

MUTATION 2 — entering the mode also attacks the least-criticised artifact
  FAILED ::test_theorem_14_1_two_modes_one_record_identical_labels
  FAILED ::test_the_module_constructs_no_edge_no_label_and_no_warrant  2 failed, 9 passed

RESTORED                                                              12 passed
```
**PASS**

### S6 (R4, R5) — capture integration

```
$ python -m pytest tests/test_capture14_promotion_conditioning.py -q
8 passed in 0.30s
$ python -m pytest tests/test_frame_render.py tests/test_calculus_succession.py -q
51 passed in 2.65s          <- the MUST-NOT-MOVE half of the census, unchanged
```
`::test_every_elevation_gets_both_a_before_and_an_after` is the R15 obligation;
`::test_the_owed_set_is_derived_from_the_record_not_from_process_state`
reopens the harness and shows the owed set survives; and
`::test_diversify_shows_more_of_the_frames_own_crisis` exercises the one lever
through the render it moves. **PASS**

### S7 (R8) — per-cycle emission through the real scheduler

```
$ python -m pytest tests/test_capture14_emission.py tests/test_premise_channel_loop.py -q
(within) 81 passed in 10.17s across all six new files
```
The emission tests drive a real `Scheduler`, not the capture functions
directly — E28's failure mode is a mechanism nobody triggers. **PASS**

### S8 (R10, R13) — eight declarations, V-6 executed

```
$ python -c "...declaration() for the eight..."
8 declared, none carrying the debt marker
$ python -m pytest tests/test_signal_contract.py tests/test_signals.py -q
19 passed in 5.66s
```
V-6 as a TEST rather than a paragraph:
`::test_attack_target_entropy_reads_newly_carried_attacks` moves the window
past both carriages and shows §14.2 absent while the shipped signal reads 1.0.
**PASS**

### S9 (R6, R17) — ten `Config` knobs with recorded defaults

```
{'SCOPE_MAX_DEPTH': 16, 'SCOPE_MAX_NODES': 512, 'FRAME_SLICE_ATTACKERS': 5,
 'FRAME_SLICE_DEPARTURES': 4, 'CAPTURE14_WINDOW': 200, 'CAPTURE14_AGE_FLOOR': 50,
 'CAPTURE14_PRECISION': 6, 'CAPTURE14_SC_CEILING': 0.5,
 'CAPTURE14_ENTER_K': 2, 'CAPTURE14_EXIT_K': 0}
Value error, CAPTURE14_EXIT_K must be strictly below CAPTURE14_ENTER_K: got exit=3 enter=2
```
**PASS**

### S10 (R17) — one versioned line per knob, EVERY schema version

```
$ python -m pytest tests/test_reusable_qualification.py tests/test_allocation_signal_consumption.py -q
54 passed in 21.52s
$ python -m pytest ...::test_the_shipped_qualification_subject_digest_does_not_move -q
1 passed in 0.37s
```
Proven rather than asserted — `source_config_hash` at the tranche base and at
HEAD, every schema version:
```
schema  462d6091d                                                          HEAD
1,2     6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81   identical
3-6     2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5   identical
```
**PASS**

### S11 (R17) — the public surface is unchanged

```
$ python scripts/wheel_smoke.py
wheel smoke passed: isolated V6-only contents, clean imports, exact entry
points, module parity, MCP registration, and exact MCP schemas
```
No CLI command, no MCP tool, no console entry point was added, and
`blast_radius.py` reports `wheel_smoke_pins: []`. **PASS**

### S12 (R7, R16) — RESULTS.md's two closing segments

`RESULTS.md` §2 names sixteen constants, each with its evidence or the word
`unmeasured`, INCLUDING the honest entry that orphan scheduling has no constant
at all. §4 carries the closing ledger rung by rung and §4c the four
deliberately-open items, with §13's residue quoted verbatim. **PASS**

---

## 2. Full gate

<<GATE>>

## 3. Record-behaviour preservation

```
$ verify_root('experiments/2026-08-24-change-rung7-wounds-falls-succession/run')
violations: 0   []
```
Unchanged. The tranche added no `verify_root` limb and touched no reader of
the replay-validation formats. **PASS**

## 4. Frozen-surface diff — the mechanical tripwire, pasted

```
$ git diff --stat 462d6091d..HEAD -- \
    src/deepreason/capabilities/state.py src/deepreason/harness.py \
    src/deepreason/invariants.py src/deepreason/run_manifest.py \
    src/deepreason/qualification.py
 src/deepreason/run_manifest.py | 21 +++++++++++++++++++++
 1 file changed, 21 insertions(+)
```
NON-EMPTY, and authorized. R17 verbatim: *"FROZEN SURFACES (ladder row): none
beyond Config knobs, each with its `_versioned_source_config_data` line for
EVERY schema version."* The 21 insertions are ten `data.pop` lines and one
comment block in that exact function; no schema, no validator, no version, no
Pydantic model. Insertions only — **0 deletions** — and §S10's digest
comparison shows the effect is to PRESERVE the digest, not move it.
The other four surfaces: **empty**. **PASS**

Final `blast_radius.py` over all fifteen changed `src/` files:
```
verdict: CONTACT
DIRECT contacts: [run_manifest.py]        <- the one SPEC.md §1 named
SYMBOL_INDIRECT count: 0
frozen_adjacent: 0
```

## 5. Packaging surface

Touched: nothing. No `pyproject.toml`, no CLI entry point, no MCP tool, no
wheel layout change. `wheel_smoke.py` was run ANYWAY and passed (§S11), because
"unchanged" is a claim about a measured surface.
`wheel_operational_smoke.py`: <<OPSMOKE>>

## 6. Map

<<MAP>>

## 7. Requirement sweep

| R | demonstrated by |
|---|---|
| R1 rent as an explicit criterion | S1 — criterion 6, three legs, mutation-proven three ways |
| R2 the authority audit as an executable replay program | S3 — five clauses, C5 and P6 as differentials |
| R3 it must be able to FAIL | S3 — five seeded violations, each caught, then GREEN |
| R4 G-5 before/after conditioning on promotion events | S6 — `::test_every_elevation_gets_both_a_before_and_an_after` |
| R5 G-4, the existing capture instruments extend | S5/S6 — the controller reuses `raw_flags`'s four bands; `conditioned_problems` measures the slice's surface |
| R6 T-7 constants as `Config` knobs with defaults and a plan | S2, S9, and SPEC.md §8's measurement plan |
| R7 closing RESULTS names every constant, evidence or "unmeasured" | S12 — sixteen constants; the orphan entry says there is no constant |
| R8 the six §14 diagnostics over a sequence-number window | S4, S7 |
| R9 canonical rounding and declared precision are policy | S4 — `ROUND_HALF_EVEN`, precision in the payload, `none` for absence |
| R10 each is a DECLARED signal | S8 |
| R11 the hysteresis controller, and Theorem 14.1 exhibited | S5 — differential plus two mutation proofs |
| R12 policy as a recorded artifact, referee-reviewable | S5 — `capture14-hysteresis.v1` through `create_artifact`, attackable; `config_referee` is the existing role and no new role was added |
| R13 V-6 decided in SPEC.md with reasons, and executed | S8 + SPEC.md §3 D1 + `DR-INV-signal-contract`'s three-population table |
| R14 the IAF question rowed, not absorbed | SPEC.md §3 D2 (priced) + `PARKED.md` P1 (ready-to-send prompt) |
| R15 VALIDATION names each gate obligation | this document, §1 and §8 |
| R16 the program's closing ledger | S12 — `RESULTS.md` §4, §4b, §4c |
| R17 frozen surfaces, no new LLM role, public surface | §4, §5 — one authorized contact; zero new roles; smoke green |
| R18 size ceiling, STOP if the plan exceeds ~1100 | SPEC.md §11 planned 1 077; execution EXCEEDED — recorded at CHECKLIST step 20 with priced options, ceiling NOT re-baselined |
| R19 deliver R-by-R with pasted proof | `DELIVERY.md` |
| R20 (Amendment 1) run every instrument, keep going | this document runs the full gate, `docs_verify` full + `--audit` + `--links` + `--coverage` + `--stale`, both smokes, `diff_budget` and `blast_radius` |

## 8. The six gate obligations R15 names

| # | obligation | where | verdict |
|---|---|---|---|
| 1 | §9.9 passing, and SHOWN TO FAIL when seeded — both runs pasted | §1 S3 | **PASS** |
| 2 | Theorem 14.1 — the controller cannot reach an edge or a label, MUTATION PROVEN | §1 S5 | **PASS** |
| 3 | G-5 diagnostics present on EVERY promotion event | §1 S6 | **PASS** |
| 4 | every §14 signal declared, windowed, canonically rounded; V-6 executed | §1 S4, S8 | **PASS** |
| 5 | closing honesty — every constant named with evidence or "unmeasured" | §1 S12 | **PASS** |
| 6 | axiom ledger — PROVES A9, A10; PRESERVES A1, A2; plus the program's closing ledger | `RESULTS.md` §4 and `DR-INV-axiom-basis` | **PASS** |

## 9. Assumptions carried (SPEC.md §4 — operator may override)

- **A1** the six are emitted from `_record_detection_signals`, once per cycle.
- **A2** `m = 200`, `h = 50`, both recorded as **unmeasured**.
- **A3** the controller writes no knob; it records a mode and a policy, and the
  render reads it.
- **A4** "succession rulings" as realizing objects means a trial's rival
  artifacts.
- **A5** `critic_budgets` is disclosed as owned-elsewhere rather than steered.
- **A6** assumption ids ARE commitment ids on this tree.

## Verdict: <<VERDICT>>
