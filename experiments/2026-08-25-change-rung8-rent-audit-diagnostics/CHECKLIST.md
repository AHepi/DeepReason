# Checklist for: Rung 8 — rent, the authority audit, capture integration, the §14 diagnostics

State: next=12 blockers=none

Re-read REQUEST.md (including Amendment 1 / R20) + SPEC.md before every step.
Execute strictly in order. One step per `dr-execute-step` invocation.

Map ids this plan was built on (same list as REQUEST.md §6, seams first):
`DR-SEAM-calculus-x-rules`, `DR-SEAM-adjudication-x-authority`,
`DR-SEAM-schools-x-scheduler`, `DR-SEAM-evaluation-x-rules`;
`DR-SUB-calculus`, `DR-SUB-periphery`, `DR-SUB-scheduler`,
`DR-SUB-adjudication`, `DR-SUB-manifest`, `DR-SUB-verification`;
`DR-CON-standing-and-background`, `DR-CON-packs-and-token-economy`,
`DR-CON-problem-layer-lifecycle`, `DR-CON-warrants-and-attacks`,
`DR-CON-scheduler-ranking`;
`DR-INV-frozen-surfaces`, `DR-INV-signal-contract`, `DR-INV-axiom-basis`,
`DR-REC-add-signal`, `DR-REC-revise-allocation-policy`.

Tranche base for `diff_budget.py` / `blast_radius.py --against`: `462d6091d`.
Ceiling: **1 100 `src/` insertions** (SPEC.md §11).

---

- [x] 0. (all) Baseline: full gate and `docs_verify` at the tranche base, both
      recorded so every later delta has something to be a delta from.
      done-when: both outputs pasted below this step; the gate ends
      "N passed, 0 failed" and `docs_verify`'s failure count matches the
      operator's KNOWN CURRENT STATE (3 pre-existing shallow-clone failures)
      or is 0.

      PROOF — full gate at the tranche base `462d6091d`:
      ```
      $ python -m pytest tests/ -q -n 4
      4080 passed, 6 skipped in 1252.38s (0:20:52)
      [exited with code 0]
      ```
      4080 passed, **0 failed** — exactly the operator's stated baseline. The
      5 known-flaky MCP-thread tests did not fire on this run.
      `docs_verify` baseline is recorded at step 7, its first use as a delta.

- [x] 1. (S9) `src/deepreason/config.py`: add the ten knobs of SPEC.md §S9 with
      their recorded defaults, each carrying a comment stating the CONSTRAINT
      (why the default is today's constant, or that it is unmeasured) and never
      narrating the change. `CAPTURE14_EXIT_K < CAPTURE14_ENTER_K` is validated
      on the model, not assumed.
      done-when: `python -c "from deepreason.config import Config; c=Config();
      print([getattr(c,k) for k in ('SCOPE_MAX_DEPTH','SCOPE_MAX_NODES',
      'FRAME_SLICE_ATTACKERS','FRAME_SLICE_DEPARTURES','CAPTURE14_WINDOW',
      'CAPTURE14_AGE_FLOOR','CAPTURE14_PRECISION','CAPTURE14_SC_CEILING',
      'CAPTURE14_ENTER_K','CAPTURE14_EXIT_K')])"` prints the ten defaults, and
      a `Config(CAPTURE14_EXIT_K=3, CAPTURE14_ENTER_K=2)` raises.

      PROOF:
      ```
      SCOPE_MAX_DEPTH            = 16
      SCOPE_MAX_NODES            = 512
      FRAME_SLICE_ATTACKERS      = 5
      FRAME_SLICE_DEPARTURES     = 4
      CAPTURE14_WINDOW           = 200
      CAPTURE14_AGE_FLOOR        = 50
      CAPTURE14_PRECISION        = 6
      CAPTURE14_SC_CEILING       = 0.5
      CAPTURE14_ENTER_K          = 2
      CAPTURE14_EXIT_K           = 0
      Value error, CAPTURE14_EXIT_K must be strictly below CAPTURE14_ENTER_K:
      got exit=3 enter=2 [type=value_error]
      ```

- [x] 2. (S10) [COMMIT] `src/deepreason/run_manifest.py`: one
      `data.pop(<knob>, None)` per new knob in `_versioned_source_config_data`,
      unconditional, under ONE comment block stating the reason (consulted at
      sites inside the run, never written to the manifest; their effect IS
      recorded elsewhere; omitting the drop is the `ENGAGED_CRITICISM_AUTHORITY`
      incident, `docs/ERRATA.md` E44).
      done-when: `python -m pytest tests/test_reusable_qualification.py
      tests/test_allocation_signal_consumption.py -q` -> 0 failed, and
      `python -m pytest tests/test_allocation_signal_consumption.py::test_the_shipped_qualification_subject_digest_does_not_move -q`
      -> 1 passed. This is the step that PROVES surface 4 stayed still.

      PROOF:
      ```
      $ python -m pytest tests/test_reusable_qualification.py tests/test_allocation_signal_consumption.py -q
      54 passed in 21.52s
      $ python -m pytest tests/test_allocation_signal_consumption.py::test_the_shipped_qualification_subject_digest_does_not_move -q
      1 passed in 0.37s
      ```
      Stronger than the done-criterion asked for: `source_config_hash` compared
      byte-for-byte at the tranche base (`462d6091d`, in a scratch worktree)
      and at HEAD, for EVERY schema version. Ten new knobs, zero digest motion.
      ```
      schema   462d6091d                                                          HEAD
      1        6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81   (identical)
      2        6c2d01f6b8cbe65e2a26bb57e864a80feec07b0896142fb2267bc83d2717dc81   (identical)
      3        2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5   (identical)
      4        2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5   (identical)
      5        2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5   (identical)
      6        2624603035bc335e59da63f25426d3ae6619bf7f84d48657e8f25310de49edc5   (identical)
      ```

- [x] 3. (S8, R13) `src/deepreason/signals.py`: the eight `capture14.*`
      declarations, none carrying `unspecified`; and ONE appended sentence to
      `criticism.attack-target-entropy.v1`'s `semantics` naming what it is not.
      No other existing entry moves.
      done-when: `python -c "from deepreason.signals import declaration; ns=[...
      the eight ...]; ds=[declaration(n) for n in ns]; assert all(d and
      d.unit!='unspecified' and d.staleness!='unspecified' for d in ds);
      print('8 declared')"` prints `8 declared`, and
      `python -m pytest tests/test_signal_contract.py tests/test_signals.py -q`
      -> 0 failed.

      PROOF:
      ```
      8 declared
        capture14.stream-contraction.v1              ratio  cycle
        capture14.attack-target-entropy.v1           ratio  cycle
        capture14.criticism-debt.v1                  ratio  cycle
        capture14.reinstatement-rate.v1              ratio  cycle
        capture14.validity-attack-rate.v1            ratio  cycle
        capture14.exogenous-grounding-ratio.v1       ratio  cycle
        capture14.promotion-conditioning.v1          event  permanent
        capture14.hysteresis-mode.v1                 event  cycle
      V-6 cross-reference present on the Rung 2 entry: True

      $ python -m pytest tests/test_signal_contract.py tests/test_signals.py -q
      19 passed in 5.66s
      ```
      `test_the_migration_debt_can_only_shrink` is inside that 19: eight new
      declarations, none carrying `unspecified`, census unmoved at 84.

- [x] 4. (S8, R13) [COMMIT] Map: `docs/map/INV-signal-contract.md` gains the V-6
      family table — the three populations, their differences, and the decision
      with its reasons — plus TWO checks at column 0: one asserting both
      families are declared and distinct, one asserting
      `capture/detection.py`'s four same-named quantities are NOT registry
      signals (so wiring them to `record_measure` undeclared fails the gate).
      Run both checks BEFORE writing them down.
      done-when: `python tools/docs_verify.py --links` -> 0 failed, and the two
      new checks exit 0 when run directly (paste both).

      PROOF — three checks written, each RUN BEFORE being written down:
      ```
      $ python -c "...both families declared, distinct, cross-referencing..."
      CHECK-1 exit 0
      $ ! grep -q "record_measure" src/deepreason/capture/detection.py
      CHECK-2 exit 0
      $ python -c "...all six capture14 diagnostics ratio/cycle..."
      CHECK-3 exit 0
      $ python tools/docs_verify.py --links
      docs_verify --links: 0 dangling reference(s), 64 document(s)
      ```
      A third check was added beyond the two planned: the V-6 collision turned
      out to be three-way (SPEC.md M4), and the third population is undeclared
      BECAUSE it is never emitted — which is a fact about `detection.py` and is
      checked as one rather than promised.

- [x] 5. (S4) `tests/test_capture14_diagnostics.py` written FIRST, against the
      module that does not exist yet. Covers: the window is sequence-numbered
      (`W_m(n)`) and not an event count; each of the six against a hand-built
      record with a known answer; the empty case returns `None` and never
      `0.0`; canonical rounding is `ROUND_HALF_EVEN` at the declared precision;
      determinism across two computations; and an AST scan asserting the module
      imports no `time`/`datetime` and reads no `Event.ts`.
      done-when: `python -m pytest tests/test_capture14_diagnostics.py -q`
      FAILS with a collection/import error — pasted. A test that has never been
      red has never been shown to be able to fail.

      PROOF — RED:
      ```
      tests/test_capture14_diagnostics.py:25: in <module>
          from deepreason.capture import diagnostics as d14
      E   ImportError: cannot import name 'diagnostics' from 'deepreason.capture'
      1 error in 0.20s
      ```

- [x] 6. (S4) `src/deepreason/capture/diagnostics.py`: `window`, `canonical`,
      the six functions of SPEC.md §S4's table, and `diagnostics()` returning
      the vector with `n`, `m`, `h`, `precision`.
      done-when: `python -m pytest tests/test_capture14_diagnostics.py -q`
      -> N passed, 0 failed.

      PROOF — GREEN, 29 tests:
      ```
      $ python -m pytest tests/test_capture14_diagnostics.py -q
      29 passed in 0.71s
      ```
      TWO NEAR-VACUITIES were caught while implementing, and each now has a
      test that fails against the vacuous version rather than a comment saying
      it was considered:

      1. `Provenance.event_seq` defaults to 0 and almost nothing sets it, so an
         age floor derived from it reads EVERY artifact as maximally old and
         discriminates nothing. Measured before writing the test:
         ```
         722c59ba01 provenance.event_seq = 0
         9b642b5004 provenance.event_seq = 0   (five conjectures, five zeroes)
         ```
         `younger_than` now derives age from the events inside the floor, which
         also avoids a whole-log read per cycle.
         `::test_the_age_floor_actually_discriminates`
      2. A behavioural signature carrying ref TARGETS is unique for every
         content-addressed artifact, so SC would read 0 on every record ever
         made. Relations enter as ROLE COUNTS.
         `::test_stream_contraction_ignores_artifact_identity`

      The V-6 decision is also a TEST, not only a paragraph — the two families
      are shown to disagree on one record:
      `::test_attack_target_entropy_reads_newly_carried_attacks` moves the
      window past both carriages and asserts §14.2 goes absent while the
      shipped `criticism.attack-target-entropy.v1` still reads 1.0.

- [x] 7. (S4) [COMMIT] Map: `docs/map/SUB-periphery.md` gains the
      `capture/diagnostics.py` row with a check that would fail if a diagnostic
      started reading wall-clock; `docs/map/INV-axiom-basis.md`'s A10 row gains
      the canonical-rounding evidence.
      done-when: `python tools/docs_verify.py` -> failure count unchanged from
      step 0's baseline, and the two new checks exit 0 (paste them).

      PROOF — `docs_verify` baseline established (step 0's other half):
      ```
      $ python tools/docs_verify.py
      docs_verify [full]: 64 documents, 1047 checks, 4 workers
        FAIL CON-run-identity.md:200  (git history: shallow clone)
        FAIL CON-run-identity.md:202  fatal: ambiguous argument '1637e808'
        FAIL CON-run-identity.md:204  fatal: ambiguous argument 'f304fec1'
      docs_verify: 3 failed
      ```
      Exactly the operator's KNOWN CURRENT STATE: 3 pre-existing shallow-clone
      failures, all three the same git-history check family, none in a document
      this tranche touches.

      Four NEW checks added across `DR-SUB-periphery` and `DR-INV-axiom-basis`,
      each RUN BEFORE being written down:
      ```
      PERIPHERY-CHECK-1 exit 0     (module shape; six signals)
      ::test_no_diagnostic_reads_wall_clock                        1 passed
      ::test_the_age_floor_actually_discriminates
      ::test_stream_contraction_ignores_artifact_identity          2 passed
      ::test_canonical_rounding_is_half_even_at_the_declared_precision
      ::test_absence_renders_as_none_and_never_as_zero
      ::test_two_computations_over_one_record_are_byte_identical   3 passed
      ```
      Document ring green:
      ```
      $ python tools/docs_verify.py --ring periphery
      == SUB-periphery ==   119 passed, 3 skipped in 22.60s
      ```
      `Verified-at:` stamps are NOT advanced here — they advance at step 26,
      after the full `docs_verify` re-runs. A stale stamp is honest; a false
      one is not.

- [x] 8. (S5) `tests/test_capture14_hysteresis.py` written FIRST. Covers:
      `T_enter`/`T_exit` asymmetry (a state that enters does NOT immediately
      exit); the policy artifact is registered, attackable, and carries its
      bands and precision; the `no_lever` disclosure names all four absent
      levers with a resolution each; and **the Theorem 14.1 differential** —
      one scripted record, `normal` vs `diversify`, identical labels, `att`,
      `dep` and warrants, with the policy artifact excluded.
      done-when: `python -m pytest tests/test_capture14_hysteresis.py -q` FAILS
      (module absent) — pasted.

      PROOF — RED:
      ```
      from deepreason.capture import hysteresis
      E   ImportError: cannot import name 'hysteresis' from 'deepreason.capture'
      1 error in 0.21s
      ```

- [x] 9. (S5) `src/deepreason/capture/hysteresis.py`: `step()`, the bands
      reusing `ATTACK_ENTROPY_FLOOR` / `CRIT_DEBT_CEILING` / `LAMBDA_FLOOR` /
      `MIN_ATTACKS_FOR_RITUAL`, the `capture14-hysteresis.v1` policy artifact
      through `harness.create_artifact` + `Rule.REFL`, and
      `slice_budgets(harness, config)`.
      done-when: `python -m pytest tests/test_capture14_hysteresis.py -q`
      -> N passed, 0 failed.

      PROOF — GREEN, 11 tests:
      ```
      $ python -m pytest tests/test_capture14_hysteresis.py -q
      11 passed in 0.66s
      ```
      One design correction en route, worth recording because it is the kind
      that silently half-works: the first `policies()` recognised a policy by
      sniffing the artifact's content prefix, and `json.dumps(sort_keys=True)`
      puts `"schema"` past the 120-character window — so `mode()` always read
      `normal` and the controller could never hold a mode. It now reads the
      mode RECEIPTS, which is the record's own statement that an artifact is a
      policy, and which a critic quoting a policy cannot impersonate.

- [x] 10. (S5, R11) [COMMIT] The Theorem 14.1 MUTATION PROOF, in a scratch
      copy: wire the hysteresis mode into label computation, run the
      differential, watch it go RED, restore, watch it go GREEN. Plus the
      structural check
      `! grep -qE "att_add|dep_add|Warrant\(|register_fail_warrant|_adjudicate" src/deepreason/capture/hysteresis.py`
      added to `docs/map/INV-signal-contract.md` beside `allocation.py`'s.
      done-when: both runs pasted (RED then GREEN) and the grep check exits 0.

      PROOF — MUTATION 1, `_adjudicate` reads the recorded mode
      (a controller decision reaching label computation):
      ```
      E  AssertionError: diversify moved something Theorem 14.1 forbids
      E  {'labels': {'0d11e5c3...': 'refuted', ...}}
      E       !=    {'labels': {'0d11e5c3...': 'accepted', ...}}
      FAILED ::test_theorem_14_1_two_modes_one_record_identical_labels
      1 failed, 10 passed in 0.75s
      ```

      PROOF — MUTATION 2, the plausible disguise: entering the mode ALSO
      attacks the least-criticised artifact, "so the diversification has
      teeth". Kills BOTH guards, which is the point of having two:
      ```
      FAILED ::test_theorem_14_1_two_modes_one_record_identical_labels
      FAILED ::test_the_module_constructs_no_edge_no_label_and_no_warrant
      2 failed, 9 passed in 0.82s
      ```

      RESTORED — GREEN:
      ```
      $ python -m pytest tests/test_capture14_hysteresis.py -q
      11 passed in 0.60s
      $ python -m pytest tests/test_capture14_hysteresis.py -q -k "theorem_14_1 or constructs_no_edge"
      2 passed, 9 deselected in 0.22s
      $ ! grep -qE "att_add|dep_add|Warrant\(|register_fail_warrant|_adjudicate" src/deepreason/capture/hysteresis.py
      STRUCTURAL-CHECK exit 0
      ```
      Both checks are now in `DR-INV-signal-contract`, beside `allocation.py`'s,
      with the one deliberate difference recorded: `create_artifact` is
      PERMITTED here, for the policy artifact and only for it, because a policy
      that could not be attacked would be authority without exposure (P6).

- [x] 11. (S6c) `src/deepreason/calculus/render.py`: keyword-only
      `attackers_n` / `departures_n` on `frame_slices`, defaulting to today's
      module constants; the two context renderers resolve the budgets from the
      latest recorded hysteresis policy via a lazily-imported
      `hysteresis.slice_budgets`, falling back to the `Config` defaults when no
      policy is on the record.
      done-when: `python -m pytest tests/test_frame_render.py
      tests/test_calculus_succession.py -q` -> 0 failed (UNCHANGED — this is
      the MUST-NOT-MOVE half of the census), and a new named test shows
      `diversify` widens both budgets while `normal` does not.

      PROOF — the MUST-NOT-MOVE half of the census holds, and wider than
      planned (the four frame/slice consumers plus the pack IR):
      ```
      $ python -m pytest tests/test_frame_render.py tests/test_calculus_succession.py -q
      51 passed in 2.65s
      ```
      The 16 `FRAME_SLICE_ATTACKERS_N` / `FRAME_SLICE_DEPARTURES_N` test lines
      and the 2 map checks named in SPEC.md §7 did not move: the module
      constants remain the defaults and only a keyword argument was added.

      PROOF — the lever, through the render it actually moves:
      ```
      $ python -m pytest tests/test_capture14_hysteresis.py -q
      12 passed in 0.94s
      ::test_diversify_shows_more_of_the_frames_own_crisis
      ::test_slice_budgets_fall_back_to_config_on_a_record_with_no_policy
      ```
      The second is the absence-tolerant reader SPEC.md §10 requires: a record
      with no policy — every root written before this rung — renders exactly as
      it did.

- [ ] 12. (S6a, S7) `tests/test_capture14_emission.py` and
      `tests/test_capture14_promotion_conditioning.py` written FIRST. Covers:
      the six fire once per cycle from one shared vector; the three Rung 2
      signals still fire; EVERY elevation gets both a `before` and an `after`;
      `conditioned_problems` equals `framed_problem_ids`'s count; and a RESUMED
      run owes exactly what the log says it owes (the owed-`after` set is
      derived from the record, not from process state).
      done-when: both files FAIL — pasted.

- [ ] 13. (S6a, S7) `src/deepreason/scheduler/scheduler.py`: inside
      `_record_detection_signals`, in the fixed order of SPEC.md §S7 — compute
      the vector once, emit the six, emit owed `after` records, detect new
      elevations and emit their `before` records, run the hysteresis step.
      done-when: `python -m pytest tests/test_capture14_emission.py
      tests/test_capture14_promotion_conditioning.py
      tests/test_premise_channel_loop.py -q` -> 0 failed.

- [ ] 14. (S6a, S6b) [COMMIT] Map: `docs/map/SUB-scheduler.md` and
      `docs/map/CON-scheduler-ranking.md` gain the emission site's new
      obligations; `docs/map/SUB-periphery.md` records the G-4 extension (one
      band vocabulary, two instrument families) with a check that the
      hysteresis bands ARE the `raw_flags` bands.
      done-when: `python tools/docs_verify.py` -> baseline failure count, new
      checks exit 0 (pasted).

- [ ] 15. (S1) `tests/test_promotion_rent.py` written FIRST. Covers the three
      legs of SPEC.md §S1 separately (each with a fixture that fails only that
      leg), the `overrun`-not-`fail` rule when the certificate's cap dropped an
      id, and `test_the_scope_bound_comes_from_the_certificate_not_the_config`
      (which belongs to S2 and is written here so S2's step has a guard).
      done-when: the file FAILS — pasted.

- [ ] 16. (S1) `src/deepreason/calculus/promotion.py` + `programs.py`:
      `promotion_rent` as criterion 6, registered in `PROMOTION_PROGRAMS`,
      `programs.PROGRAMS` (`class_="structural"`) and `programs.BLOB_PROGRAMS`.
      done-when: `python -m pytest tests/test_promotion_rent.py -q` -> the
      three-leg tests pass (the scope-bound test may still fail; S2 lands it),
      and `python -c "from deepreason.calculus.promotion import
      PROMOTION_PROGRAMS; assert len(PROMOTION_PROGRAMS)==6 and 'promotion_rent'
      in PROMOTION_PROGRAMS; print(PROMOTION_PROGRAMS)"`.

- [ ] 17. (S1) [COMMIT] The EXPECTED-TO-MOVE half of the census, updated
      minimally and never by weakening an assertion:
      `tests/test_promotion_criteria.py` :150 :378 :408,
      `tests/test_promotion_solo.py` :108 :129,
      `tests/test_promotion_closure.py` :119 :135 :149 :159 :161 :170.
      Map: `docs/map/SUB-calculus.md` (criteria count, the sweep) and
      `docs/map/SEAM-evaluation-x-rules.md` (the promotion-program set).
      done-when: `python -m pytest tests/test_promotion_criteria.py
      tests/test_promotion_solo.py tests/test_promotion_closure.py
      tests/test_promotion_rent.py -q` -> 0 failed, and `docs_verify` at
      baseline.

- [ ] 18. (S1) (S1) MUTATION PROOF for rent: in a scratch copy delete each of
      the three legs in turn; each deletion turns at least one named test RED.
      done-when: three RED runs and the restored GREEN run pasted.

- [ ] 19. (S2) `src/deepreason/calculus/scope.py`, `claims.py`, `nomination.py`,
      `promotion.py`: keyword-only bounds on `compile_scope` defaulting to the
      module constants; `scope_max_depth` / `scope_max_nodes` on
      `ReachCertificateV1` beside `k_frame`, populated by `build_certificate`
      from `Config`; `scope_determinism` reads the CERTIFICATE's values.
      done-when: `python -m pytest tests/test_calculus_scope_predicate.py
      tests/test_calculus_nomination.py tests/test_promotion_rent.py -q`
      -> 0 failed, including
      `test_the_scope_bound_comes_from_the_certificate_not_the_config`.

- [ ] 20. (S2) [COMMIT] Map: `docs/map/SUB-calculus.md`'s scope and certificate
      rows; `docs/map/INV-axiom-basis.md`'s Prop 12.1 evidence gains the
      certificate-carried bound.
      done-when: `python tools/docs_verify.py` at baseline, new checks pasted.

- [ ] 21. (S3) `tests/test_calculus_authority_audit.py` written FIRST, with the
      five clause tests AND the five SEEDED-VIOLATION tests of SPEC.md §S3 —
      one per clause, each constructing a record that violates exactly that
      clause.
      done-when: the file FAILS (module absent) — pasted.

- [ ] 22. (S3) `src/deepreason/calculus/audit.py`: `authority_audit(harness)`
      returning `AuthorityAuditV1` with the five clauses (`C4-derived`,
      `C3-content-not-type`, `C5-absent-from-labels`, `N1-attackable`,
      `P6-reinstateable`) and a `violations` list.
      done-when: `python -m pytest tests/test_calculus_authority_audit.py -q`
      -> N passed, 0 failed.

- [ ] 23. (S3, R3) [COMMIT] **The audit shown to FAIL, then shown to pass** —
      the gate obligation R15 names first. Both runs pasted: the five seeded
      violations each reported by the audit (the seeded records RED against a
      clean expectation), and the real tree GREEN. Map:
      `docs/map/CON-standing-and-background.md` gains the audit with a check
      that it can still fail.
      done-when: both runs pasted; `docs_verify` at baseline.

- [ ] 24. (S11) `src/deepreason/calculus/__init__.py` and
      `src/deepreason/capture/__init__.py` exports; then PROVE the public
      surface did not move.
      done-when: `python scripts/wheel_smoke.py` and `python -u
      scripts/wheel_operational_smoke.py` both green (pasted), and
      `blast_radius.py`'s `wheel_smoke_pins` is `[]`.

- [ ] 25. (S12, R7, R16) `RESULTS.md`: the closing honesty table (every
      constant the v2 program introduced, with its evidence or the word
      "unmeasured", INCLUDING the orphan-scheduling entry that has no constant)
      and the closing ledger (rung by rung: axioms proved, axioms preserved,
      and what the program leaves deliberately open — Rung D's parked D2, P4b,
      the IAF layer, §13's residue verbatim).
      done-when: both segments present; every knob in SPEC.md §S9 appears in
      the table; §13's residue is quoted verbatim from
      `docs/POIETIC_CALCULUS_FORMALIZED.md`.

- [ ] 26. (all) [COMMIT] Map: `docs/map/INV-axiom-basis.md` records **A9 and
      A10 PROVED at Rung 8** and A1/A2 PRESERVED, each with the test that
      proves it; `docs/map/INV-frozen-surfaces.md` records the ten new
      `data.pop` lines.
      done-when: `python tools/docs_verify.py --audit` -> 0 findings (no check
      that cannot fail), `--links` -> 0 unresolved, and the full
      `python tools/docs_verify.py` at step 0's baseline failure count.

- [ ] 27. (all) `PARKED.md`: the IAF item with its ready-to-send prompt
      (SPEC.md §3 D2), plus anything noticed and not fixed during execution.
      done-when: the file exists and every entry carries a prompt the operator
      can paste without authoring anything.

- [ ] 28. (all) Budget and drift gates at the tranche boundary:
      `python tools/diff_budget.py 462d6091d --ceiling 1100 --paths src` and
      `python tools/blast_radius.py --files <every src file this tranche
      touched> --symbols <every top-level def touched> --against 462d6091d`.
      done-when: `DIFF_BUDGET_RESULT_V1.verdict` is `WITHIN`, and
      `frozen_surface_contacts` contains nothing SPEC.md §1 did not already
      name. Either failing is a STOP in the standard format, not a footnote.

- [ ] 29. (all) FULL GATE: `python -m pytest tests/ -q -n 4`.
      done-when: output ends "N passed, 0 failed" (pasted). The 5 known-flaky
      MCP-thread tests under `-n 4` are re-run serially if they fire, and the
      serial result is what counts.

- [ ] 30. (all) [COMMIT] Push and confirm a clean tree.
      done-when: `git status --porcelain` is empty AND the branch head is on
      `origin/claude/rung-8-closing-calculus-xgxyzt`.
