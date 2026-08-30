# Checklist for: successor questions — optional to propose, routed by pluggable destination, minting gated off-by-default

State: next=DONE blockers=Q1, Q3, Q5 (see PARKED.md); S14/S15/S19/S20/S24 are
NOT in this lane's scope and are not attempted here.
Map ids this plan was built on: DR-SEAM-rules-x-scratch, DR-SEAM-ontology-x-rules,
DR-CON-problem-layer-lifecycle, DR-CON-criticism-source, DR-CON-scheduler-ranking,
DR-INV-signal-contract, DR-INV-frozen-surfaces, DR-CON-successor-questions (new).
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.

Every command below was run with
`PYTHONPATH=/home/user/dr-lanes/lane-B/src` — the box's editable install points
at `/home/user/DeepReason/src`, so an unqualified `python -m pytest` in this
worktree would measure the OTHER checkout. Recorded here because a measurement
taken against the wrong tree is not a measurement.

- [x] 0. (all) Baseline the two guard files BEFORE any edit, so anything red
      afterwards is this tranche's doing.
      done-when: `python -m pytest tests/test_decommissioned_pipeline_stays_out.py tests/test_h1_no_spawn_from_refutation.py tests/test_signals.py tests/test_signal_contract.py -q` -> 0 failed
      OUTPUT: `29 passed in 5.34s`

- [x] 1. (S1) Add the OPTIONAL `successor_question: str | None = None` field to
      `ArgumentativeCriticOutput` and `BatchCase`.
      done-when: the S1 accept command exits 0
      OUTPUT: `S1 ACCEPT exit 0`

- [x] 2. (S2) Mirror the field on `CompactCritic` and `BatchCriticCaseWireV2`
      and thread both `compile()` maps.
      done-when: the dynamic Critic-wire scratch-name check exits 0 AND the four
      wire test files pass AND both committed subject-digest pins pass unedited
      OUTPUT: `SEAM-wire-scratch OK`; `56 passed in 1.63s`; `2 passed in 0.77s`

- [x] 3. (S5) Write `src/deepreason/successor/registry.py`: the versioned
      destination registry, its gate row, `resolve`, `register_destination`,
      `writer_for`, `unknown_destination_notices`, `minting_notices`.
      done-when: the S5 SimpleNamespace accept command exits 0
      OUTPUT: `S5 ACCEPT ok`

- [x] 4. (S9) Write `src/deepreason/successor/route.py`: the default scratchpad
      destination, registered against its declaration.
      done-when: a routed question creates one block whose provenance names the
      problem; an absent field records nothing
      OUTPUT: `block: sha256:908983b76aa6b p-1 ScratchActor.LLM`; `absent-field: nothing recorded, seq 0 0`

- [x] 5. (S13) Write `src/deepreason/successor/mint.py`: the ONE SUCCESSOR
      producer, outside `rules/`, gated OFF by default.
      done-when: `python -c "import inspect; from deepreason.rules.spawn import scan_spawns; assert 'SpawnTrigger.SUCCESSOR' not in inspect.getsource(scan_spawns)"` exits 0 AND `git diff --stat -- src/deepreason/rules/spawn.py` is empty
      OUTPUT: both hold; `spawn.py` is absent from `git status`

- [x] 6. (S6) Write `src/deepreason/successor/__init__.py`: the declared
      interface.
      done-when: the `__all__` equality assertion exits 0
      OUTPUT: `S6 ACCEPT ok`

- [x] 7. (S10) Declare the two receipt signals in `signals.py` with a REAL unit
      and staleness.
      done-when: `python -m pytest tests/test_signal_contract.py tests/test_signals.py -q` -> 0 failed
      OUTPUT: `19 passed in 4.71s`

- [x] 8. (S16) Rewrite the INERT VOCABULARY comment in `ontology/problem.py`;
      enum member name and value unchanged.
      done-when: the pinned member-list assertion exits 0
      OUTPUT: `S16 ACCEPT ok`

- [x] 9. (S3) Write `tests/test_successor_law_line.py` and MUTATION-PROVE pins
      1 and 2 RED before writing the claim down.
      done-when: 8 passed; `proof/law_line_pin1_red.txt` and
      `proof/law_line_pin2_red.txt` are non-empty and show the named failure
      OUTPUT: `8 passed in 0.16s`; pin 1 red on a rank-key mutant, pin 2 red on `['rank_bonus']`

- [x] 10. (S8) Write `tests/test_successor_registry.py` and mutation-prove the
      modularity claim.
      done-when: 10 passed; `proof/registry_modularity_red.txt` shows 3 failures
      under a route that branches on the row id
      OUTPUT: `10 passed in 2.03s`; 3 failed under the mutant

- [x] 11. (S11) Write `tests/test_successor_questions.py`, including the
      VISIBILITY measurement through `plan_conjecture_context`.
      done-when: 8 passed; `proof/route_mutants_red.txt` shows four mutants red
      OUTPUT: `8 passed in 0.19s`; link / silence / discard / visibility all red under mutation

- [x] 12. (S17) Write `tests/test_successor_minting.py` and mutation-prove the
      gate.
      done-when: 12 passed; `proof/minting_mutants_red.txt` shows three mutants red
      OUTPUT: `12 passed in 0.17s`

- [x] 13. (S18) Write `tests/test_successor_rank_tie.py`, mirroring the
      committed cycle-0 regression with a SUCCESSOR rival.
      done-when: the new file and `tests/test_controller.py::test_operator_question_outranks_spawns_at_cycle_zero` both pass; `proof/rank_tie_red.txt` shows red with the seed term deleted; `scheduler.py` takes a zero-line diff
      OUTPUT: `4 passed in 0.36s`; 2 failed under the mutant; scheduler.py absent from `git status`

- [x] 14. (S7) Write `docs/map/CON-successor-questions.md` and add its INDEX row.
      done-when: `python tools/docs_verify.py --links` -> 0 dangling
      OUTPUT: `docs_verify --links: 0 dangling reference(s), 71 document(s)`

- [x] 15. (S4, S12, S21, S22, S23) Move the map in the SAME COMMIT as the code:
      the criticism-source row and trap, the rules×scratch amendment and trap,
      H1's amendment and the corrected stale trap, the ontology×rules trap, the
      scheduler-ranking sentence and its honest residue.
      done-when: `python tools/docs_verify.py` names no NEW failing document
      OUTPUT: see VALIDATION.md

- [x] 15b. (S9, S7) FIX A DEFECT THIS TRANCHE'S OWN docs_verify FOUND: two
      file-level counting checks (`SEAM-harness-x-workflow.md:43`,
      `SEAM-scratch-x-workflow.md:44`) went red because `route.py` named
      `harness._workflow_manifest`. Read the scratch policy from the
      CONFIGURATION instead, regenerate the four route mutation transcripts
      against the fixed file, and record the trap in
      `CON-successor-questions.md` with a check that pins both counts.
      done-when: both counts are back at 59 and 48, the new trap check exits 0,
      and the five new test files still pass
      OUTPUT: `harness x workflow = 59`; `scratch x workflow = 48`;
      `NEW TRAP CHECK: exit 0`; the five new files `42 passed in 3.36s`

- [x] 16. (all) Record the PREDICTED fixture red (P-FIX-1) rather than fixing
      it: S19 is gated on Q5, which this lane may not answer.
      done-when: `proof/predicted_red_decommissioned_tripwire.txt` names exactly
      one failing test and one producer line
      OUTPUT: `1 failed, 9 passed`; producer = `src/deepreason/successor/mint.py:88`

- [x] 17. (all) [COMMIT] push, tree clean, and PARKED.md carries every bubbled
      stop as a ready-to-send prompt.
      done-when: `git status --porcelain` is empty AND the branch head is on origin
