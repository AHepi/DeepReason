# Validation for: "Prose can refute" + the single-family path

Run against `fd0c30ed` (all 16 CHECKLIST.md steps checked). Every acceptance
check in SPEC.md was re-run here in item order, including ones a step already
ran: steps prove local progress, this phase proves the assembled whole.

## Acceptance checks

### S1 (R1) — `trial_authority_for` no longer discards the computed mode

Run against the **corrected** clause recorded in SPEC.md's append-only S1
amendment, not the clause as originally planned. Both are reported.

    -- the knob is READ for every surface (not computed and discarded) --
       reads mode: True
       branches on it: True
       rubric          knob=calibrated_status verified=False -> observe_only
       pairwise        knob=calibrated_status verified=False -> observe_only
       infrastructure  knob=calibrated_status verified=False -> observe_only
    -- non-text unchanged --
       code  -> status
       math  -> status
       None  -> status

**PASS** against the corrected clause. The original clause ("varies with the
config knob") is NOT met and deliberately so: meeting it deletes the
calibration-receipt precondition, which the operator's answer to Q-B under
reading (a) kept. Verified consistent with that answer: SPEC.md Q-B states
"Under (a) it is untouched", the operator answered "keep the current path",
and `tests/test_text_authority_policy.py:166` failed under the literal
implementation. The gate is load-bearing — `ops.py:141` and
`scheduler.py:1022,1761` call this function with no manifest, so the preflight
that refuses an unverified receipt never runs for them. **The correction is
consistent with the operator's own instruction; the literal clause was not.**

### S2 (R2) — the prose-refutation path is reachable

    test_a_single_family_run_can_refute_by_prose_end_to_end PASSED
    test_the_same_run_under_the_old_mode_refutes_nothing PASSED
    test_the_minting_critic_carries_a_school_other_than_the_targets PASSED
    3 passed, 24 deselected in 0.23s

    single_family_run: True      len(state.att)   : 1
    judge families   : {'mock:glm'}   target status: refuted
    bound schools    : ('school-0', 'school-1')   warrant type: argumentative

**PASS.** `len(state.att) >= 1` and `Status.REFUTED` from a target carrying no
evaluable commitment, with an ARGUMENTATIVE warrant — so the defeat is prose,
not the mechanical channel A7 leaves alone. The same fixture under
`observe_only` leaves the graph unmoved, which is what rules out the fixture
rather than the mode being the cause.

### S3 (R3, R5, R6) — the refuting endpoint gets the full argument

    test_the_refuting_endpoint_is_given_the_whole_argument PASSED

**PASS.** One test carries all four clauses against a ~10 KB target rendered at
`token_budget=1200`: the complete text, no `HARNESS PACK EXCERPT` marker, every
id in `target.interface.refs`, and no `SCR_` handle or scratch section.

### S4 (R4) — the formal/informal boundary

**FAIL on the first clause.** Measured, not argued:

    no commitment at all               evaluable=None  att=1 status=refuted
    rubric: (not evaluable)            evaluable=False att=1 status=refuted
    predicate: (EVALUABLE)             evaluable=True  att=1 status=refuted

S4 accepts on "prose refutation of a target with an evaluable commitment is
refused with a typed reason". A target carrying `predicate:'chorale' in content`
— `programs.evaluable` True — is refuted by prose, `att=1`. Not refused.

The second clause passes: a target carrying no evaluable commitment is refuted.

A refusal DOES exist, and it is typed, but it sits at a different line:

    execution_backed: True
    att= 0 status= accepted
    typed measure records: ['arg-crit-overridden-by-execution']

**Cause: A1 names the wrong function, and SPEC.md contradicts itself about
which.** S4's own "before" line says `execution_backed`; its "after" and
"accept" lines say evaluable. These are different sets —
`execution_backed` requires a commitment in `oracle.EXEC_PROGRAMS` (exec /
property / dataset_oracle) that currently passes, while `programs.evaluable`
admits any `predicate:` or known `program:`. The implemented line is
`execution_backed`, at five call sites, and it is consulted before the
authority branch so no mode can reach past it.

**This is an interpretation the operator must settle, and it is not obvious
which way.** Widening the guard to `evaluable` would protect predicate-committed
targets from prose — which REDUCES what prose can refute, in direct tension with
R2 ("Prose can refute"). Against that: `packs.py`'s own
`_MACHINE_EVAL_NOTE` tells the critic that predicate- and program-evaluated
commitments are "checked by the harness DETERMINISTICALLY" and that a case must
not claim one is violated — which is the codebase calling them formal. So R4's
"formal claims" plausibly covers them, and today they are unprotected.

### S5 (R5, R6) — the separation is asserted, not assumed

    test_the_criticism_rule_imports_no_scratch_module PASSED
    test_the_criticism_rule_touches_scratch_only_as_an_ordering_fence PASSED
    test_the_criticism_pack_cannot_be_given_scratch PASSED
    test_the_defended_trial_imports_no_scratch_module PASSED
    test_no_scratch_identifier_reaches_a_warrant_or_an_attack_edge PASSED

**PASS.**

### S6 (C3, C2) — nothing retroactive

    roots BEFORE=42 AFTER=42
    only in BEFORE: none      only in AFTER : none
    valid: 0 changed          att: 0 changed
    epistemic_passed: 0 changed   blind: 0 changed   ERROR: 0 changed

    $ diff -q sweep_BEFORE.txt sweep_AFTER.txt
    BEFORE and AFTER sweeps are BYTE-IDENTICAL

**PASS.** Full gate 0 failed, below.

### S7 (R13, R15, R16) — the single-family predicate

    test_the_single_family_predicate_fails_closed_on_no_leases PASSED
    test_the_single_family_predicate_reads_every_role_not_just_judges PASSED

**PASS.** True for one family, False for two, False for an empty lease set.

### S8 (R14, R15, R8) — a cross-school ensemble, single-family only

    test_the_cross_school_ensemble_accepts_one_family_with_two_schools PASSED
    test_the_cross_school_ensemble_raises_on_one_family_and_one_school PASSED
    test_the_cross_school_ensemble_does_not_count_an_unverifiable_binding PASSED
    test_the_cross_family_gate_is_untouched_by_the_cross_school_sibling PASSED
    test_configuring_school_bindings_does_not_reach_the_gate_with_two_families PASSED
    test_the_cross_school_gate_governs_only_a_single_family_run PASSED

The cross-family gate's own tests are unchanged: the tranche's complete test
footprint is two files, and neither is a cross-family test —

    tests/test_pack_prefix.py                 |  26 +-
    tests/test_prose_refutation_boundaries.py | 848 +++++++++++++++++++++++++

**PASS as specified ("selectable"), with a material limit on what that buys.**
No production `LLMAdapter` construction passes `school_judge_bindings` —
`llm/adapter.py:1467` is the only one — so `_select_judge_ensemble` always falls
back to cross-family in a live run. The architecture is complete, proven
offline, and unreachable from any ladder. SPEC.md asked for selectability and
got it; it never asked for the wiring, and nothing in R7-R17 does either.

### S9 (R7-intent, R14) — the author's own school stays excluded

    test_a_school_can_never_be_scheduled_to_criticise_its_own_work PASSED
    test_the_planner_leaves_a_single_school_run_with_no_eligible_critic PASSED
    test_the_minting_critic_carries_a_school_other_than_the_targets PASSED

**PASS**, at four layers: planner subtraction, target-record refusal,
assignment refusal, and the school stamped on the artifact a warrant hangs from.

### S10 (R9) — nothing new at the model boundary

    test_the_criticism_prompt_cannot_vary_with_the_authority_mode PASSED
    test_the_criticism_prompt_never_names_an_author_or_a_school PASSED

**PASS.** Byte-identity across modes is structural: the criticism packs accept
no `config`/`authority`/`mode`/`trial_authority` parameter, so no mode can
reach them. Stronger than rendering twice and comparing.

### S11 (R15, C3, C2) — off by default, existing roots do not move

**PASS.** Default `observe_only` unchanged; 42-root sweep byte-identical (S6);
`run_manifest.py` UNTOUCHED, so no manifest schema, no qualification subject
digest, no replay record format.

### S12 (R5, R6) — the scratchpad stays out of the new path

**PASS.** S5's assertions plus S3's `SCR_`/`scratch` exclusion on the rendered
pack under the new mode.

## Full gate

    3270 passed, 7 skipped in 559.34s (0:09:19)

**PASS — 0 failed.** 3243 at tranche start, 3270 now.

C2 audited rather than asserted: the tranche's entire test footprint is two
files. `test_prose_refutation_boundaries.py` is new (848 lines). The 8 deleted
lines in `test_pack_prefix.py` are the single existing assertion changed
anywhere, at step 9, and it now asserts strictly MORE — the whole target body
byte-for-byte where it previously accepted a head/tail excerpt. SPEC.md's S3
predicted that change in advance. **No assertion was weakened.**

## Record-behavior preservation

`llm/packs.py` and `rules/crit.py` are readers of the record, so the spot-check
is required:

    experiments/bronze_flat_2026-07-13/deepseek-v4-pro   valid=True epistemic_passed=True  att=11
    experiments/live_jolt_2026-07-31/.../failed-epoch1-run-b4d6dfda  valid=True epistemic_passed=False att=0

Known-good root: **unchanged**. Defect-era root: **unchanged**. Both match the
step-1 baseline exactly, as does every other root (S6 byte-identity).

Frozen surfaces audited directly:

    src/deepreason/capabilities/state.py -> UNTOUCHED
    src/deepreason/harness.py            -> UNTOUCHED
    src/deepreason/run_manifest.py       -> UNTOUCHED
    src/deepreason/invariants.py         -> UNTOUCHED

## Requirement sweep

- **R1** "Get rid of that requirement" — demonstrated by S1. The hard-return is
  gone and the mode is read; the receipt gate the operator kept (Q-B) stands.
- **R2** "Prose can refute" — demonstrated by S2. First attack edge from a prose
  case in this codebase.
- **R3** "access to the full argument" — demonstrated by S3.
- **R4** "only formal claims in formal prose require formal refutation" —
  **PARTIALLY demonstrated.** Holds for execution-backed targets (typed
  refusal). Does NOT hold for predicate-committed targets, which are formal by
  the codebase's own account and are refutable by prose today. See S4.
- **R5/R6** scratchpad separation — demonstrated by S5, S12, S3.
- **R7** "same school criticisms" — `superseded-by:R14` for its literal sense,
  recorded in REQUEST.md's contradiction section before any code was written;
  retained for intent (schools as the vehicle), demonstrated by S8.
- **R8** "leverage the schools architecture to create and mint criticisms" —
  demonstrated by S8 + S9's minting-critic assertion. A6 read as reusing the
  existing warrant path; no new record type, confirmed by S6/S11.
- **R9** "stateless endpoints don't have access to who created the artifact" —
  demonstrated by S10.
- **R10** "figure out what actually exists first; feasibility and risks" —
  satisfied by FEASIBILITY.md, which gated R7/R8 before any design.
- **R11** "report without technical terms" — FEASIBILITY.md.
- **R12** "use subagents" — used for the feasibility survey.
- **R13** "designed for single family runs" — demonstrated by S7, S8.
- **R14** "as long as a critic isn't from the same school, it's fine" —
  demonstrated by S9 at four layers.
- **R15** "only active if a single model is running the entire harness" —
  demonstrated by S7 and S8's negative case (two families present, bindings
  configured and satisfiable, cross-family still governs).
- **R16** "the architecture to distinguish single and many should already
  exist" — confirmed against the codebase in REQUEST.md before proceeding.
- **R17** "Read claude.md before running" — done, in full, before the amendment.

Constraints:

- **C1** never touch run-root records or replay validation — held; frozen-surface
  audit above, S6 byte-identity.
- **C2** full gate 0 failed, no assertion weakened — held; audited above.
- **C3** no existing replay-valid root invalidated — held; 0 of 42 roots moved.
- **C4/C8** don't ask permission unless out of scope — held; A4 and the S1
  correction were recorded as stated assumptions/amendments and executed, not
  raised as blocking questions.
- **C5** route work through the skill families — held; every phase ran through
  `dr-change-orchestrator`.
- **C6** re-read CLAUDE.md — done.
- **C7** feasibility report in plain prose — FEASIBILITY.md.

## Assumptions carried (surface these at delivery)

- **A1** — **WRONG, and this is the FAIL.** "formal claims" read as
  `programs.evaluable`; the implemented line is `execution_backed`, which is
  narrower. Predicate-committed targets are unprotected.
- **A2** prospective only — verified by S6/S11 (0 of 42 roots moved).
- **A3** "the full argument" = complete text + declared `Interface.refs`,
  explicitly not scratch — implemented and verified by S3.
- **A4** R14 supersedes R7's literal sense; the guarantee is cross-SCHOOL.
  **Load-bearing for the whole extension** — if the operator meant literal
  same-school criticism, S8/S9 invert.
- **A5** "a single model" = one route FAMILY across the run's leases, not one
  model id and not one seat.
- **A6** "mint criticisms" = make the existing path completable, not a new
  warrant kind — held; no new record type.
- **A7** the mechanical-checking defeat channel left untouched — held, and S2
  asserts the warrant is ARGUMENTATIVE so the demo does not rely on it.

## Verdict: FAIL

Scoped to **one acceptance clause, S4's first**. Everything else passes: 11 of
12 spec items, the full gate at 0 failed, zero movement across all 42 roots,
and no frozen surface touched.

**FAIL detail.** S4 accepts on "prose refutation of a target with an evaluable
commitment is refused with a typed reason". Measured: a target carrying
`predicate:'chorale' in content` (`programs.evaluable` True) is refuted by
prose, `att=1`, not refused. The suspected step is not an implementation step —
no code is missing or broken. The defect is in SPEC.md itself: A1 identified the
formal/informal line as `programs.evaluable`, while S4's own "before" line names
`execution_backed`, and the two describe different sets. Step 8 found and
recorded this; it could not resolve it, because resolving it changes what runs
may do.

**Routing.** Back to `dr-plan-steps`, but the input it needs is one operator
word, not a plan:

- **(a) `execution_backed` is the intended line.** No code change. A1 is amended
  and S4's acceptance restated against the real line, which then passes on the
  evidence already gathered. This keeps prose's reach as wide as R2 asks.
- **(b) R4 covers predicate- and program-evaluated commitments too.** The guard
  widens from `execution_backed` to `programs.evaluable`, protecting more
  targets from prose. This narrows what prose can refute — a step back from R2 —
  and changes behaviour for every existing run, so it needs its own tranche with
  its own before/after sweep.

I have not chosen. (a) is the smaller reading and consistent with R2; (b) is the
more literal reading of R4's word "formal". They differ in what the harness is
permitted to do, which is the operator's call and not an implementation detail.

---

# VALIDATION ROUND 2 — after amendments 5-6 and steps 17-26

Round 1's verdict was FAIL, scoped to S4's first acceptance clause. That clause
is now implemented, and two further amendments (R18-R22) added S13-S20. Every
acceptance check is re-run here against `e86b10f0`.

## Acceptance checks

S1-S3, S5-S12: **unchanged and re-run PASS.** The 44-assertion inventory below
covers them; nothing in steps 17-26 touched `authority.py`, `config.py`,
`packs.py` or the scratchpad boundary.

### S4 (R4, R21) — the formal/informal boundary — **now PASS**

Round 1 measured a target carrying `predicate:'chorale' in content` being
refuted by prose, `att=1`. R21 ("they are both formal") selected the wider
line. Re-measured:

    passing predicate: (FORMAL)     att=0 status=accepted
    rubric: only (informal)         att=1 status=refuted
    ONLY program:json-wf            att=1 status=refuted

Row 1 is the clause that failed. Rows 2 and 3 confirm the line did not widen
past what R21 selects. **The FAIL is closed.**

### S13 (R19) — a single-MODEL predicate — PASS

    test_the_single_model_predicate_is_narrower_than_the_family_one PASSED
    test_the_single_model_predicate_reads_every_position PASSED
    test_the_single_model_predicate_fails_closed_on_no_leases PASSED

True for one model everywhere; **False for two models sharing one family**;
False for an empty lease set. `is_single_family_run` unmodified and still
passing its own assertions.

### S14 (R18, R20) — cross-school CRITICISM is the substitute — PASS

    single-model, critic school-1 (differs)  att=1 refuted warrant=argumentative
    single-model, critic school-0 (SAME)     att=0 declined=same-school-critic
    single-model, NO critic school           att=0 declined=no-critic-school
    TWO models (glm-4 second seat)           RAISED SECOND_JUDGE_FAMILY_REQUIRED

All four clauses. The fourth is what makes S13's narrowing load-bearing.

### S15 (R20) — exposure with nothing configured — PASS

    test_the_substitute_is_exposed_by_build_adapter_with_nothing_configured PASSED
    test_nothing_the_operator_configures_can_turn_the_substitute_on PASSED

Built by the production factory from a §15 role table. No constructor
argument, no Config value, no manifest field. A two-model adapter handed every
opt-in the old design offered still reports False, and the guard's
neighbourhood in `trial.py` contains no `config` reference — so a qualifying
run cannot opt out either.

### S16-S20 — nothing retroactive, hole shut, gate green — PASS

    roots BEFORE=42 AFTER=42 | valid: 0 changed | att: 0 changed
    epistemic_passed: 0 changed | blind: 0 changed | ERROR: 0 changed
    diff -q sweep_BEFORE.txt sweep_AFTER2.txt -> BYTE-IDENTICAL

    test_a_structural_program_confers_no_formal_backing PASSED
    test_a_structural_only_target_is_still_refutable_by_prose PASSED
    test_the_forbidden_case_form_still_refuses_a_predicate PASSED

## Full gate

    3287 passed, 7 skipped in 842.84s (0:14:02)

**0 failed.** 3243 at tranche start.

The first run of this gate FAILED 2, and that is recorded at CHECKLIST step 23
rather than overwritten, together with the process error that caused it
(step 21 changed trial behaviour; only the assertions step 21 added were
re-run). Both failures were in tests written earlier in this tranche. Neither
was resolved by weakening an assertion: they were rewired to the path that
carries a critic school, keeping every assertion they made, and a new test
pins the limit the failure exposed.

C2 audited across the WHOLE tranche — two existing test files touched:

    tests/test_pack_prefix.py                 |   26 +-
    tests/test_prose_refutation_boundaries.py | 1386 +++++++++++++++++++++

`test_pack_prefix.py` asserts strictly more than before (whole target body
byte-for-byte, where it accepted an excerpt) and SPEC.md's S3 predicted it.

## Record-behavior preservation

    capabilities/state.py -> UNTOUCHED    harness.py       -> UNTOUCHED
    run_manifest.py       -> UNTOUCHED    invariants.py    -> UNTOUCHED

Two byte-identical 42-root sweeps: step 15 (before any permission changed) and
step 24 (after the formal line widened and the ensemble precondition changed
shape). C1 and C3 hold.

## Requirement sweep — amendments 5 and 6

- **R18** "It should be cross school criticism" — S14. Also CLOSES A4: the
  operator confirmed the cross-school reading, so it is settled, not assumed.
- **R19** "only work for single model runs" — S13, and S14's fourth row.
- **R20** "exposed whenever a single model is occupying all positions" — S15,
  through the production factory with nothing configured.
- **R21** "they are both formal" — S4, now PASS.
- **R22** "a conjecture endpoint might not fill out the form properly" —
  S17/S19. Traced to `workloads/models.py:105` and `skeleton.py:30-45`, and
  shut: `program:json-wf` confers nothing, `predicate:` stays un-authorable.
- **C9** "you didn't listen" — the failure was re-opening A4 after the operator
  settled it. Recorded in REQUEST.md so the delivery report states confirmed
  assumptions as facts rather than re-surfacing them as choices.

## Assumptions carried

A8 (single MODEL, not family) · A9 (cross-school CRITICISM, not a judge
ensemble — **load-bearing**) · A10 (the judge gate retained, unused) ·
A11 (evaluable AND substantive — inverts if structural programs should immunise).

A1 is now SUPERSEDED by R21 and is no longer carried.

## Verdict: PASS

Three items require an operator decision and are recorded in PARKED.md rather
than taken. None blocks the verdict; two would change future work.

1. **`ARGUMENTATIVE_AUTHORITY=single_family_trial` is dead weight.** It cannot
   complete a trial (step 26), and R20 makes it redundant in principle. Removing
   it reverts part of steps 10-11.
2. **The 11.6%.** 148 of 1279 recorded artifacts become prose-immune; one root
   goes 79 -> 31 refutable.
3. **`render_batch_crit_pack` still prefix-clips**, so R3 is unmet on that path.
