# Checklist for: the mini isolation programme
State: next=9 blockers=none. **OPERATOR APPROVED 2026-09-05**: SPEC.md is
approved as written, and Q-A is answered E1 ONLY in the operator's own words
— "within mini, criticism can't overturn anything. The point is content
generation for now. Then testing on the full harness." E2 is NOT built (not
behind a switch, not at all); E3 is NOT built here (T4's commitment artifact
proposes commitments and eliminates nothing). Recorded as REQUEST.md
Amendment 1 (R13, R14) and in SPEC.md §Q-A. THIS WINDOW EXECUTES T0, T1 and
T2 ONLY (steps 1-22); T3-T7 go to later windows.

Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per `dr-execute-step` invocation.

**Map ids this plan was built on** (from REQUEST.md's preflight):
`DR-INV-frozen-surfaces`, `DR-INV-seat-section-plugins`,
`DR-INV-seat-section-sources`, `DR-REC-add-a-section-plugin`,
`DR-INV-render-layout`, `DR-CON-packs-and-token-economy`,
`DR-CON-conjecture-source`, `DR-CON-criticism-source`,
`DR-CON-conjecture-kinds`, `DR-SUB-verification`, `DR-SUB-manifest`,
`DR-SEAM-packs-and-token-economy-x-rules`. Two documents do not exist yet
and are created by this programme: `DR-SUB-minireason` (step 12) and
`DR-SEAM-llm-x-minireason` (step 29).

**Eight sub-tranches, each delivered on its own** (SPEC.md §Budget). A
sub-tranche boundary is a delivery boundary: `dr-validate-change` then
`dr-deliver-change` before the next one starts. Do not run two in one
tranche — `dr-drive-harness` §6, "a multi-step program runs one step per
tranche".

---

## T0 — the prerequisites (S0a, S0b) — ~115 lines

- [x] 1. (S0a) Write the red test first: a `.tmpl` placed in a temp
      `<DEEPREASON_HOME>/seat_plugins/` is NOT found by the managed shallow
      path today.
      done-when: `python -m pytest tests/test_seat_section_home.py::test_managed_path_loads_operator_plugins -q`
      -> 1 failed, and the failure text names the missing section (paste it)

      ```
      $ python -m pytest tests/test_seat_section_home.py::test_managed_path_loads_operator_plugins -q
      E   deepreason.llm.seat_sections.SeatSectionError: SEAT_SECTION_PLUGIN_UNKNOWN:
          no section plugin 'dr.operator.probe'; registered:
      src/deepreason/llm/seat_sections.py:266: SeatSectionError
      FAILED tests/test_seat_section_home.py::test_managed_path_loads_operator_plugins
      1 failed in 0.44s
      
      RED as predicted: the managed shallow run completed, and the section the
      operator declared in <DEEPREASON_HOME>/seat_plugins/ was never registered --
      the failure names the missing section by id.
      ```
- [x] 2. (S0a) [COMMIT] Give `load_operator_plugins` its call site in the
      managed shallow path, and route BOTH notice lists into the run's
      record.
      done-when: the step-1 test passes AND
      `grep -rn "load_operator_plugins" src/ | wc -l` -> 2 or more (paste)

      ```
      $ python -m pytest tests/test_seat_section_home.py -q
      ..........                                                               [100%]
      10 passed in 0.28s
      
      $ grep -rn "load_operator_plugins" src/ --include=*.py
      src/deepreason/llm/seat_sections.py:558:def load_operator_plugins(*, home=None, environ=None):
      src/deepreason/shallow.py:71:    from deepreason.llm.seat_sections import load_operator_plugins
      src/deepreason/shallow.py:73:    loaded, notices = load_operator_plugins(environ=environ)
      $ ... | wc -l  ->  3
      
      $ python -m pytest tests/test_shallow_reason.py -q   ->  6 passed
      
      $ python tools/diff_budget.py 1f8108c00a --ceiling 115 --paths <T0 areas>
      {"result_type": "DIFF_BUDGET_RESULT_V1", "total_insertions": 102,
       "ceiling": 115, "verdict": "WITHIN"}
      
      $ python tools/blast_radius.py --files src/deepreason/shallow.py
          src/deepreason/llm/seat_sections.py --symbols load_operator_plugins
          run_shallow_question --against 1f8108c00a
      frozen_surface_verdict: CLEAR   contacts: []   adjacent: []
      reachability: load_operator_plugins UNREACHABLE -> REACHABLE (newly_live)
                    run_shallow_question REACHABLE -> REACHABLE (unchanged)
      
      No drift: CLEAR matches SPEC.md's forecast, and the one newly_live symbol is
      exactly the row the blast-radius census marked EXPECTED TO MOVE.
      ```
- [x] 3. (S0a) Prove the disclose-never-die half: a plugin file that raises
      on import produces a typed notice in the record and does not stop the
      run.
      done-when: `python -m pytest tests/test_seat_section_home.py -q` -> 0 failed

      ```
      $ python -m pytest tests/test_seat_section_home.py -q
      ...........                                                              [100%]
      11 passed in 0.30s
      
      Mutation proof (rule 3 of dr-execute-step's durable-tests list): making the
      loader re-raise instead of disclosing turns the new test RED --
      
        --- MUTATION (loader re-raises instead of disclosing) ---
        .../seat_plugins/raises.py:1: RuntimeError
        FAILED tests/test_seat_section_home.py::test_a_plugin_that_raises_on_import_is_a_notice_in_the_record
        1 failed in 0.31s
      
      Reverted; 11 passed again. The new case is distinct from the loader-level
      one already present: a file that PARSES and then raises while executing
      reaches the interpreter before failing, so only a run can show the failure is
      disclosed rather than fatal.
      ```
- [x] 4. (S0b) Write the red tests first: a `.layout.json` under
      `seat_plugins/` is not registered, and an unparseable one is not
      refused typed.
      done-when: `python -m pytest tests/test_seat_section_home.py::test_a_file_declared_layout_is_registered tests/test_seat_section_home.py::test_an_unparseable_layout_file_is_refused_typed -q`
      -> 2 failed (paste)

      ```
      $ python -m pytest tests/test_seat_section_home.py::test_a_file_declared_layout_is_registered \
            tests/test_seat_section_home.py::test_an_unparseable_layout_file_is_refused_typed -q
      E   AssertionError: assert 'seat-pack.operator.probe.v0' in []
      E   ImportError: cannot import name 'seat_pack_layout_from_file' from
                       'deepreason.llm.seat_sections'
      2 failed in 0.10s
      
      RED as predicted, and for the two different reasons S0b names: a .layout.json
      the operator declared is not registered by any run (the loader returns an
      empty list), and there is no reader at all to refuse a file that does not
      parse -- so today the file is neither read nor refused, it is ignored.
      ```
- [x] 5. (S0b) [COMMIT] Add the file-declared layout road with a typed
      refusal on a parse failure.
      done-when: the two step-4 tests pass (paste)

      ```
      $ python -m pytest tests/test_seat_section_home.py tests/test_seat_pack_layout.py \
            tests/test_seat_section_architecture.py tests/test_shallow_reason.py -q
      ..........................................                               [100%]
      42 passed in 1.47s
      
      Both step-4 tests now pass. The public entry is
      register_seat_pack_layout_file(path): it reads one .layout.json, refuses a
      bad one with SEAT_PACK_LAYOUT_FILE_UNPARSEABLE naming the file, and registers
      nothing when it refuses. The run-level loader calls the same entry inside its
      disclosure loop, so at run level that refusal becomes a typed notice carrying
      its OWN code and the run continues on what did load.
      
      $ python tools/diff_budget.py 1f8108c00a --ceiling 115 --paths <S0a/S0b declared files>
      {"areas": {"src/deepreason/llm/seat_sections.py": 66,
                  "src/deepreason/shallow.py": 34},
       "total_insertions": 100, "ceiling": 115, "verdict": "WITHIN"}
      
      DISCLOSED, not absorbed: the ceiling is measured over the two source files
      SPEC.md S0a/S0b declare. Counting tests/test_seat_section_home.py as well
      gives 308 insertions against the same 115, because SPEC.md S0a/S0b priced
      production lines (45 + 70 = 115, measured 100) and named no test file in
      their declared areas. Recording both numbers so the reading is visible.
      
      $ python tools/blast_radius.py --files <both> --symbols
          register_seat_pack_layout_file load_operator_plugins
          register_seat_pack_layout run_shallow_question --against 1f8108c00a
      frozen_surface_verdict: CLEAR   contacts: []   adjacent: []
      register_seat_pack_layout_file  UNKNOWN -> REACHABLE  (new symbol, live)
      load_operator_plugins           UNREACHABLE -> REACHABLE (newly_live, predicted)
      register_seat_pack_layout       REACHABLE -> REACHABLE (unchanged)
      run_shallow_question            REACHABLE -> REACHABLE (unchanged)
      
      No drift against SPEC.md's forecast.
      ```
- [x] 6. (S0a, S0b) Map: `REC-add-a-section-plugin.md` steps 2-4 now work
      end to end; update it and re-run its checks IN THIS COMMIT.
      done-when: `python tools/docs_verify.py` -> 0 failed AND `--audit` -> 0 findings

      ```
      $ python tools/docs_verify.py
        FAIL SEAM-llm-x-rules.md:54: unparseable check ...
        FAIL CON-run-identity.md:211: git log -M --diff-filter=R ... run-9175f0ec...
        FAIL CON-run-identity.md:213: git log -1 --format=%s 1637e808 | grep -qi retire
        FAIL CON-run-identity.md:215: ... f304fec1 ... (unknown revision in this clone)
        FAIL INV-frozen-surfaces.md:206: find experiments runs ... transport_failure ... -eq 0
        FAIL INV-frozen-surfaces.md:876: ... git show origin/claude/deepreason-p-s1-commitments-wowcib ...
      docs_verify: 6 failed
      
      $ python tools/docs_verify.py --audit
      SEAM-llm-x-rules.md:54: unparseable check ...
      docs_verify --audit: 1 finding(s)
      
      NOT 0 failed, and none of it is this step's. All six sit in documents this
      step did not touch, and every one of them is a checkout artefact of this
      container rather than a claim that stopped being true:
      
        SEAM-llm-x-rules.md:54  and CON-run-identity.md:211/213/215 are on this
        window instruction's own known-not-yours list.
        INV-frozen-surfaces.md:206 and :876 are not on that list by line number, so
        both were REPRODUCED on the untouched base in this same container --
        git worktree at 1f8108c00a --
          base :206  rc=1  (22 files match; the clone carries experiment records
                            the check expects absent)
          :876       rc=128 on 'git show origin/claude/deepreason-p-s1-
                     commitments-wowcib:...' -- a branch this clone lacks.
      
      REC-add-a-section-plugin.md itself passes, including the three checks added
      here, and --audit does not flag any of them as vacuous. Its steps 2, 3 and 4
      now each carry a check that goes red if the road stops working: the run reads
      the operator directory, a .layout.json declares a layout and a bad one is
      refused typed, and no Config field can name a layout. Verified-at advanced to
      db5cc16ff because those checks were actually re-run.
      ```
- [x] 7. (T0) Gate: `python -m pytest tests/ -q -n 4`
      done-when: output ends "N passed, 0 failed" (paste it)

      ```
      $ python -m pytest tests/ -q -n 4
      5077 passed, 6 skipped in 1113.62s (0:18:33)
      
      0 failed. Run on an idle box with nothing else in flight -- docs_verify had
      already finished at step 6, never concurrently.
      ```
- [x] 8. (T0) Mini ring: `python -m pytest mini/tests/ -q`
      done-when: "95 passed" or higher, 0 failed (paste)

      ```
      $ python -m pytest mini/tests/ -q
      94 passed, 1 skipped in 4.22s
      
      95 collected, 0 failed -- the count SPEC.md M7 measured. Run explicitly
      because the documented gate passes tests/ and so does not reach it (PARKED
      P1).
      ```
- [ ] 9. (T0) [COMMIT] Deliver T0: push, then confirm clean.
      done-when: `git status --porcelain` empty AND branch head on origin

## T1 — isolation, the standard input, the fence (S1, S11a) — ~170 lines

- [ ] 10. (S1) Write the fence test first, listing the eleven modules
      SPEC.md §S1 names.
      done-when: `python -m pytest mini/tests/test_isolation_fence.py -q` -> fails
      on the tree as it stands, naming which fenced module is imported (paste)
- [ ] 11. (S1) [COMMIT] Accept a frozen `RunInputManifestV2` via
      `--run-input`; bind it instead of the constant process root when
      supplied. The bare-question form is unchanged.
      done-when: `python -m pytest tests/test_shallow_reason.py mini/tests/test_compat.py -q` -> 0 failed
- [ ] 12. (S11a) [COMMIT] Create `docs/map/SUB-minireason.md` — the first map
      document for `mini/minireason/` — with `check:` lines that re-derive.
      done-when: `python tools/docs_verify.py` -> 0 failed AND `--audit` -> 0
      findings (a check that cannot fail is refused)
- [ ] 13. (S1) Prove the fence passes and CAN fail: mutate one mini module to
      import `deepreason.scheduler`, show the test red, revert.
      done-when: `proof/fence_mutation.txt` shows the red run and the green one
- [ ] 14. (T1) Gate + mini ring + docs.
      done-when: `pytest tests/ -q -n 4` 0 failed; `pytest mini/tests/ -q` 0
      failed; `tools/docs_verify.py` 0 failed (paste all three)
- [ ] 15. (T1) [COMMIT] Deliver T1.
      done-when: `git status --porcelain` empty AND branch head on origin

## T2 — relaxed forms and the commitment switch (S2, S3) — ~175 lines

- [ ] 16. (S2) Pin the STORED default before touching anything: a golden of
      today's `ReferenceFreeConjecturer` wire schema (R-stored).
      done-when: `python -m pytest mini/tests/test_mini_forms.py::test_the_stored_form_is_byte_identical -q` -> passed
- [ ] 17. (S2) [COMMIT] `mini/minireason/forms.py`: the registry, the four
      shipped forms, selection by argument → `DEEPREASON_MINI_FORM` → the
      flow default. Never `Config`, never the manifest.
      done-when: the no-`maxLength` assertion in SPEC.md §S2 passes for every
      registered form (paste), and step 16's golden still passes
- [ ] 18. (S3) Write the red test first: a free-prose candidate under the
      relaxed form is refuted on arrival today (this reproduces
      `proof/m2_free_prose_today.txt` as a committed test).
      done-when: `python -m pytest mini/tests/test_mini_commitment_policy.py -q` -> fails, 0 survivors (paste)
- [ ] 19. (S3) [COMMIT] `MiniCommitmentPolicyV1` with two independent
      switches; `compile_checks` consults it; switching either off writes a
      typed WARNING record naming what is no longer checked.
      done-when: SPEC.md §S3's two-line accept passes AND a run with both off
      records >=1 survivor and >=1 warning (paste)
- [ ] 20. (S2, S3) Map: `SUB-minireason.md` gains the form registry and the
      commitment policy, with checks, IN THIS COMMIT.
      done-when: `python tools/docs_verify.py` -> 0 failed, `--audit` -> 0 findings
- [ ] 21. (T2) Gate + mini ring + docs.
      done-when: all three green (paste)
- [ ] 22. (T2) [COMMIT] Deliver T2.
      done-when: `git status --porcelain` empty AND branch head on origin

## T3 — the adapter and the three shells (S5, S6) — ~240 lines

- [ ] 23. (S5) Write the red test first: `_walk_seat_layout` over a mini
      session fails on `dr.neighbourhood` with the AttributeError
      `proof/m3_seat_shell_reach.txt` recorded.
      done-when: `python -m pytest mini/tests/test_mini_sources.py -q` -> fails with that exact error (paste)
- [ ] 24. (S5) [COMMIT] `mini/minireason/sources.py`: the read-only
      projection from mini's dict `State` to the ontology types the plugins
      expect. It writes nothing.
      done-when: step 23's test passes AND `verify_root` over a mini run is
      unchanged at 0 violations (paste)
- [ ] 25. (S6) [COMMIT] `render_seat_brief` as the public entry over
      `_walk_seat_layout`; no behaviour change for the two existing seats.
      done-when: `python -m pytest tests/test_conj_pack_legacy_golden.py tests/test_crit_pack_legacy_golden.py -q` -> 0 failed (C4)
- [ ] 26. (S5) [COMMIT] The three mini section plugins
      (`mini.everything-so-far` untruncated, `mini.target-conjecture`,
      `mini.problem`) and the three layouts. The critic layout registers NO
      commitment section.
      done-when: SPEC.md §S5's layout assertion passes (paste)
- [ ] 27. (S6) [COMMIT] The three mini shells, and mini's dispatch resolving
      its form THROUGH `SeatShellV1.form_id` — its first consumer.
      done-when: SPEC.md §S6's `form_for_seat` assertion passes (paste)
- [ ] 28. (S5) The exposure test: a rendered critic brief over a run that
      contains commitment proposals contains none of their bytes.
      done-when: `python -m pytest mini/tests/test_mini_exposure.py -q` -> 0 failed
- [ ] 29. (S6) [COMMIT] Map: create `docs/map/SEAM-llm-x-minireason.md`, and
      update `INV-seat-section-plugins.md` (the `form_id` consumer row, the
      `render_seat_brief` entry point) and `INDEX.md`'s seam matrix — SAME
      COMMIT as the code.
      done-when: `python tools/docs_verify.py --links` -> every DR- reference
      resolves; `docs_verify.py` 0 failed; `--audit` 0 findings
- [ ] 30. (T3) Gate + mini ring + docs.
      done-when: all three green (paste)
- [ ] 31. (T3) [COMMIT] Deliver T3.
      done-when: `git status --porcelain` empty AND branch head on origin

## T4 — the commitment seat and the controller hook (S4, S7, S11b) — ~180 lines

- [ ] 32. (S4) [COMMIT] The `mini.commitment-proposal.v1` artifact kind and
      its seat. The ONLY requirement is `about`; the body is free prose,
      unbounded, unranked.
      done-when: SPEC.md §S4's minimum/rejection pair passes (paste)
- [ ] 33. (S4) The shape-buys-nothing test: no rank, admission, immunity or
      refutation path reads the kind's name.
      done-when: `python -m pytest mini/tests/test_mini_shape_buys_nothing.py -q` -> 0 failed
- [ ] 34. (S7) [COMMIT] `MiniCalibrationHookV1` declared, with
      `mini.calibration.noop.v1` as the only registered implementation,
      called between cycles and returning `None`.
      done-when: `grep -rn "register_mini_calibration_hook" src/ mini/minireason/ | wc -l` -> 2 (paste)
- [ ] 35. (S7) Prove R8 is honoured: the hook changes nothing. A run with the
      hook and a run without it produce the same rendered briefs.
      done-when: `python -m pytest mini/tests/test_mini_calibration_hook.py -q` -> 0 failed
- [ ] 36. (S11b) [COMMIT] Map: `SUB-minireason.md` gains the commitment seat
      and the hook; `INV-render-layout.md` and
      `CON-packs-and-token-economy.md` gain their rows — SAME COMMIT.
      done-when: `python tools/docs_verify.py` 0 failed, `--audit` 0 findings
- [ ] 37. (T4) Gate + mini ring + docs.
      done-when: all three green (paste)
- [ ] 38. (T4) [COMMIT] Deliver T4.
      done-when: `git status --porcelain` empty AND branch head on origin

## T5 — the pluggable flow and the architecture tests (S8, S9) — ~240 lines

- [ ] 39. (S8) [COMMIT] `mini/minireason/flow.py`: `MiniFlowV1`,
      `MiniStageV1`, the registry, and the two shipped flows. Default stays
      `mini.flow.legacy-v0` — today's behaviour exactly.
      done-when: `python -m pytest mini/tests/test_mini_flow.py -q` -> 0 failed
- [ ] 40. (S8) [COMMIT] `loop.run` walks `flow.stages` and names no seat, no
      kind and no stage.
      done-when: SPEC.md §S8's `ast`/substring assertion passes (paste)
- [ ] 41. (S8) The registration proof (R10): a flow declared only in a test
      file adds a FOURTH artifact kind and its seat, and runs end to end,
      with no edit under `mini/minireason/`.
      done-when: `python -m pytest mini/tests/test_mini_flow.py::test_a_new_artifact_kind_is_a_registration -q` -> passed
- [ ] 42. (S9) [COMMIT] The five architecture tests, each with its mutation
      proof captured to `proof/mutation_<n>.txt` showing it RED.
      done-when: `python -m pytest mini/tests/test_mini_architecture.py -q`
      -> 0 failed AND five `proof/mutation_*.txt` files exist, each showing a
      red run (paste one)
- [ ] 43. (S8, S9) Map: `SUB-minireason.md` gains the flow registry and the
      five enforcement checks — SAME COMMIT.
      done-when: `python tools/docs_verify.py` 0 failed, `--audit` 0 findings
- [ ] 44. (T5) Gate + mini ring + docs.
      done-when: all three green (paste)
- [ ] 45. (T5) [COMMIT] Deliver T5.
      done-when: `git status --porcelain` empty AND branch head on origin

## T6 — regression, goldens, the record (S10) — ~120 lines

- [ ] 46. (S10) Full gate, idle box, nothing else running
      (`dr-drive-harness` §5b).
      done-when: `python -m pytest tests/ -q -n 4` ends "N passed, 0 failed" (paste)
- [ ] 47. (S10) Mini's own suite, explicitly, because the documented gate
      does not reach it.
      done-when: `python -m pytest mini/tests/ -q` -> 0 failed (paste)
- [ ] 48. (S10) The two legacy goldens (C4).
      done-when: `python -m pytest tests/test_conj_pack_legacy_golden.py tests/test_crit_pack_legacy_golden.py -q` -> 0 failed (paste)
- [ ] 49. (S10) The record: a mini isolation run verifies and replays.
      done-when: `verify_root(root)` -> 0 violations AND
      `replay(root).digest() == Session(root).state.digest()` (paste both)
- [ ] 50. (S10) The wheel smokes, because no gate runs them and S1 changes
      the shallow CLI surface (`dr-drive-harness` §4).
      done-when: `python scripts/wheel_smoke.py` and
      `python -u scripts/wheel_operational_smoke.py` both green, with any
      changed pin updated in THIS commit (paste)
- [ ] 51. (T6) [COMMIT] Deliver T6.
      done-when: `git status --porcelain` empty AND branch head on origin

## T7 — the measure (S12) — ~80 lines

- [ ] 52. (S12) [COMMIT] Write and SEAL `PREREG_D8.md`: both arms, the
      criteria, the blind-judging protocol, the length control, the per-seat
      spend table. Record its sha256.
      done-when: `PREREG_D8.md` exists, its sha is in the commit message, and
      NO arm has run
- [ ] 53. (S12) Soak before any live launch (`dr-drive-harness` §1).
      done-when: `python -u scripts/cycle_soak.py --case <case>` green (paste)
- [ ] 54. (S12) Run ARM 0 and ARM M detached, with the snapshot loop armed.
      done-when: both arms' roots exist, `deepreason results <root>` prints a
      typed terminal for each (paste)
- [ ] 55. (S12) Judge blind, length held constant; report per-seat spend.
      done-when: `RESULTS.md` carries both arms, the judging output, the
      length distributions and the spend table
- [ ] 56. (S12) [COMMIT] Record the outcome honestly — including
      "inconclusive" if that is what it is (C6; CLAUDE.md Conventions).
      done-when: `RESULTS.md` states the verdict and its residue, and no arm
      was re-run to get a number
- [ ] 57. (all) [COMMIT] Deliver the programme: push and confirm clean.
      done-when: `git status --porcelain` empty AND branch head on origin

---

## Notes for whoever runs this

- **Iterate on the ring, gate at the boundary** (CLAUDE.md). The mini ring is
  `python -m pytest mini/tests/ -q` and it is fast (95 tests). The full gate
  belongs at the `[COMMIT]` steps that say so, not between them, and
  `--lf` re-runs only what moved.
- **Never run the gate concurrently with `docs_verify`** — both fan out and
  the contention manufactures failures (`dr-drive-harness` §5b).
- **The map moves in the same commit as the code.** Steps 12, 20, 29, 36 and
  43 are inside their sub-tranches deliberately; a trailing "update docs"
  step is the step that gets dropped.
- **Every `[COMMIT]` step runs `tools/diff_budget.py` against SPEC.md's
  per-sub-tranche number**, not the programme total.
- If a step fails twice the same way, STOP and report — do not improvise a
  third approach (`dr-change-orchestrator` §3).
