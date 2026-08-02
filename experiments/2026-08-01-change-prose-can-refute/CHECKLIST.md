# Checklist for: "Prose can refute" + the single-family path

Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per `dr-execute-step` invocation.

## Standing prohibition for EVERY step

No step may add or alter a manifest field, a state digest, event application
order, a qualification subject, or a replay-validation record format.
SPEC.md's budget says **frozen surfaces touched: none**. A step that turns out
to need one STOPS and reports; it does not proceed. Authority stays on
`Config` (`config.py`), never on the run manifest — that is the whole reason
this tranche is not a frozen-surface change.

## Call sites established before planning (so steps name real targets)

- `llm/adapter.py:609-613` `require_cross_family_judges` is the ONLY caller of
  `require_cross_family_judge_ensemble` (`llm/firewall.py:261`).
- `rules/crit.py:1287-1300` is the authority gate: `observe_only` observes,
  `trial_required` calls `run_argument_trial_from_case` from
  `deepreason.informal.trial`.
- `rules/crit.py:56` `_POLICY_AUTHORITIES = {"observe_only", "defended_trial"}`
  and `:87` maps `defended_trial` -> `trial_required`. Two vocabularies exist;
  any new value must be added consistently or deliberately not at all.

---

- [x] 1. (S6, S11) Capture the 42-root BEFORE baseline to the session
      scratchpad, recording per root: `valid`, `epistemic_checks_passed`,
      `len(state.att)`, and the count of `adjudication-blindness` findings.
      files: none (read-only script in the scratchpad)
      done-when: ~~the baseline file has 42 lines and `grep -c ERROR` is 0~~
      **CORRECTED at execution — the second clause was mis-specified.**
      done-when: 42 lines, and every ERROR line is
      `UnsupportedRunManifestVersionError` (the known pre-v6 set)

      Output:

          SWEEP COMPLETE: 42 roots -> .../scratchpad/sweep_BEFORE.txt
          lines: 42
          ERROR count: 11
          valid=False: 5 | blind=1: 26 | att>0: 5

          $ grep ERROR sweep_BEFORE.txt | cut -d: -f1 | sort | uniq -c
               11 UnsupportedRunManifestVersionError

      Why the criterion was wrong, recorded rather than quietly fixed: 11 of
      42 roots being unopenable pre-v6 was established three separate times
      earlier this session (INVESTIGATION.md, the adjudication-blindness
      GOAL.md, FEASIBILITY.md) and I wrote `0` into the criterion anyway. The
      first clause passed unchanged; the second is corrected to what the fact
      always was, and all 11 are verified to be the single expected exception
      type rather than assumed. The substance of the step — one complete,
      reusable baseline — is achieved, and the script is saved for verbatim
      re-run at step 15.

      Baseline shape for later comparison: 5 roots `valid=False`, 26 carrying
      `adjudication-blindness`, 5 with any attacks.

- [x] 2. (S5, S12) [COMMIT] Write the scratchpad-separation assertions:
      no scratch id in any warrant, attack edge, criticism pack or judge pack,
      and `rules/crit.py` imports nothing from `deepreason.scratch`.
      files: `tests/test_prose_refutation_boundaries.py` (new)
      done-when: `pytest tests/test_prose_refutation_boundaries.py -q -k scratch`
      reports all passed (these should be GREEN today; they pin, not fix)

      Output:

          $ pytest tests/test_prose_refutation_boundaries.py -q -k scratch
          .....                                        [100%]
          5 passed in 0.10s

      Five assertions, GREEN as predicted — they pin the boundary rather than
      move it:

        - `rules/crit.py` imports no `deepreason.scratch` module. The whole
          module is AST-walked, not grepped at the header, because a
          function-local import would pass a header check and still couple the
          two.
        - `rules/crit.py`'s only scratch mentions are `scratch_fence_seq`
          (lines 342, 583) — transactional ordering, not content. Any other
          scratch name appearing there now fails.
        - The criticism packs cannot be GIVEN scratch: `render_conj_pack` takes
          `scratch_context` (packs.py:322, correctly — conjecture is where the
          workshop belongs) and `render_crit_pack` / `render_batch_crit_pack`
          have no such parameter. Enforced by signature, so no future caller
          can pass one without changing this contract.
        - `informal/trial.py` imports no scratch module. This is the last link
          before a sustained prose case can change a status, so it is authority
          chain proper.
        - `rules/warrants.py` and `adjudication/edges.py` import no scratch
          module — the narrowest part of the chain.

- [x] 3. (S10) Write the prompt byte-identity assertion: for identical inputs
      the rendered criticism and judge prompts are byte-identical with the new
      mode enabled and disabled, and contain no author or school label.
      files: `tests/test_prose_refutation_boundaries.py`
      done-when: the test exists and is RED only because the new mode value
      does not exist yet (paste the error naming the unknown value)

      Output:

          $ pytest tests/test_prose_refutation_boundaries.py -q
          E  ValidationError: 1 validation error for Config
          E  ARGUMENTATIVE_AUTHORITY
          E    Input should be 'observe_only' or 'trial_required'
          1 failed, 7 passed in 16.62s

      RED for exactly one reason: the value does not exist yet. Everything
      else is green.

      **Byte-identity is proved STRUCTURALLY, not empirically, and that is a
      stronger result than the step asked for.** The first draft rendered the
      pack twice under two authorities and compared. That test was confused:
      `render_crit_pack` takes `(target_id, state, commitments, blobs,
      token_budget)` and no config or authority argument at all, so there was
      nothing for the mode to vary. The assertion is now that the criticism
      packs accept no `config`/`authority`/`mode`/`trial_authority` parameter,
      which makes byte-identity a property of the signature rather than a
      lucky observation, and fails if a future parameter lets a mode through.

      The first draft also failed for a second, unrelated reason — it rebuilt
      the same fixture root twice on one path. Diagnosed rather than assumed:
      a probe confirmed `_engaged_root` IS reusable twice in one process
      (2 passed), so the fixture was sound and the test was not.

- [x] 4. (S9) Write the author-school exclusion assertion: no criticism
      assignment is ever produced whose critic school equals its target's
      school, under both the old and the new mode.
      files: `tests/test_prose_refutation_boundaries.py`
      done-when: the old-mode half passes today (paste it); the new-mode half
      is RED for the same unknown-value reason as step 3

      Output:

          $ pytest tests/test_prose_refutation_boundaries.py -q
          1 failed, 9 passed in 2.65s
          (the 1 is still test_the_single_family_authority_value_exists,
           RED on the missing ARGUMENTATIVE_AUTHORITY value — unchanged
           from step 3; both new assertions PASS)

      The exclusion turns out to hold THREE times over, not once, so all
      three layers are pinned rather than the one the step assumed:

        1. `plan_foreign_criticism` computes
           `sorted(set(bindings) - {target.owner_school_id})` — the author is
           subtracted from the eligible set by construction.
        2. `ForeignCriticismTargetV1._owner_is_not_completed` refuses a record
           that lists the owner among completed critics.
        3. The assignment's `_selected_school_is_eligible` refuses to be
           constructed with the owner in `eligible_school_order`.

      Also pinned: with ONE school, the planner yields an empty eligible set.
      That is the degenerate case the single-family path must not paper over —
      with nobody but the author available the correct outcome is no
      criticism, not self-criticism.

      This is why R14 matters and why it is asserted rather than assumed: it
      is the operator's answer to the feasibility survey's worst finding, that
      a point of view criticising its own work is close to marking its own
      homework and that withholding shared context does not buy independence.

- [x] 5. (S7) [COMMIT] Add the single-family predicate, derived from immutable
      leases exactly as `require_cross_family_judge_ensemble` derives families.
      files: `src/deepreason/llm/firewall.py`
      done-when: a new test shows True for one family, False for two, False for
      an empty lease set (fails closed) — paste all three

      Output:

          $ python -m pytest tests/test_prose_refutation_boundaries.py \
                -k single_family_predicate -v
          test_the_single_family_predicate_fails_closed_on_no_leases PASSED
          test_the_single_family_predicate_reads_every_role_not_just_judges PASSED
          2 passed, 10 deselected in 0.04s

      All three cases the criterion named, as asserted:

          is_single_family_run({})                               is False
          is_single_family_run({"judge": ()})                    is False
          is_single_family_run({"judge": (glm, glm)})            is True
          is_single_family_run({"judge": (glm,),
                                "conjecturer": (qwen,)})         is False

      `_lease_families` folds families exactly as
      `require_cross_family_judge_ensemble` does — `.strip().casefold()` off the
      immutable lease's route, blanks dropped so an unset field cannot
      masquerade as a distinct family. That gate is unmodified; the shared
      derivation is duplicated rather than refactored out of it, because step 6
      requires `git diff` to show zero changed lines inside it.

      Two departures from the literal criterion, both widening it:

        - "False for two" is asserted as **False for two families across
          DIFFERENT ROLES**, not two judge seats. R15 says "a single model is
          running the ENTIRE harness", so the predicate reads every leased seat,
          not the judge role the cross-family gate reads. A run whose judges
          share a family while its conjecturer does not is a multi-family run
          and must not qualify — that is the case asserted.
        - The empty case is asserted twice: no roles at all, and a role present
          with no seats. Both are "we could not tell", which is not "we
          checked", and neither may unlock the substitute guarantee.

      Environment note (not a step outcome): the container lost its editable
      install between steps, and the `pytest` first on PATH is now a uv-tool
      shim that cannot see the package. `pip install -e . --break-system-packages`
      plus `python -m pytest` is the working invocation; later steps use it.

- [x] 6. (S8) Add `require_cross_school_judge_ensemble`: >=2 judge seats from
      >=2 distinct SCHOOLS. `require_cross_family_judge_ensemble` is NOT
      modified.
      files: `src/deepreason/llm/firewall.py`
      done-when: accepts one family + two schools; raises on one family + one
      school; and `git diff` shows zero changed lines inside
      `require_cross_family_judge_ensemble`

      Output:

          $ python -m pytest tests/test_prose_refutation_boundaries.py \
                -q -k "cross_school or cross_family or single_family_predicate"
          ......                                        [100%]
          6 passed, 10 deselected in 0.06s

      Third clause, proved by bytes rather than by reading the diff — the diff
      is additive but its hunk header names the neighbouring function, which is
      exactly the kind of thing an eye slides over:

          $ python - <<'PY'   # AST-extract the gate at HEAD and in the tree
          cross-family gate byte-identical to HEAD: True
          bytes: 640 -> 640
          PY

      That is also pinned as a test (`..._cross_family_gate_is_untouched...`):
      one family raises `SECOND_JUDGE_FAMILY_REQUIRED`, two families are
      accepted. The `git diff` clause is a one-time check; the test survives it.

      **Where school identity comes from, established rather than assumed.**
      Neither `EndpointLease` nor `Route` carries a school
      (`firewall.py:201-206` — role, seat, route, and nothing else), and two
      schools may legitimately share one route. So the new gate cannot read
      school off a lease the way the family gate reads family off one. School
      is manifest-owned: `SchoolRoleBindingV1` (`run_manifest.py:467`) binds
      `school_id` + `role` + `seat` + `endpoint_id`, and its `role` field is an
      open `^[a-z][a-z0-9_]*$`, so `judge` bindings are expressible in
      `CriticismPolicyV1.bindings` today with no schema change. The gate
      therefore takes `(leases, bindings)` — the same immutability guarantee,
      from the other immutable source. **No manifest field was added**; the
      standing prohibition holds.

      Two things the step did not ask for, both narrowing:

        - A binding whose `endpoint_id` disagrees with the seat it names is not
          counted. That is `resolve_school_role_lease`'s own
          `SCHOOL_ROUTE_ENDPOINT_MISMATCH` check (`firewall.py:489`) applied
          here: coverage that cannot be verified is absence, not coverage. A
          third test asserts two *nominal* schools with one unverifiable
          binding still raises.
        - A typed sibling stop, `JudgeSchoolEnsemblePolicyError` /
          `SECOND_JUDGE_SCHOOL_REQUIRED`, rather than reusing
          `SECOND_JUDGE_FAMILY_REQUIRED`. The two gates are never both in force
          for one run, so a stop must say which one produced it.

      The seat count and the frozen-lease requirement are unchanged from the
      family gate. Only the dimension along which the two seats must differ
      moves. Nothing calls this yet — step 7 is what selects it.

- [x] 7. (S8) [COMMIT] Make the ensemble choice select cross-school ONLY when
      the single-family predicate holds; cross-family governs otherwise.
      files: `src/deepreason/llm/adapter.py`
      done-when: with two families present the cross-school gate is not
      selected even when configured (paste the assertion); the existing
      cross-family tests still pass

      Output — the assertion the whole extension turns on:

          test_configuring_school_bindings_does_not_reach_the_gate_with_two_families PASSED
          test_the_cross_school_gate_governs_only_a_single_family_run PASSED
          test_the_cross_school_ensemble_accepts_one_family_with_two_schools PASSED
          test_the_cross_school_ensemble_raises_on_one_family_and_one_school PASSED
          test_the_cross_school_ensemble_does_not_count_an_unverifiable_binding PASSED
          test_the_cross_family_gate_is_untouched_by_the_cross_school_sibling PASSED
          test_the_single_family_predicate_fails_closed_on_no_leases PASSED
          test_the_single_family_predicate_reads_every_role_not_just_judges PASSED
          8 passed, 10 deselected in 0.05s

      Existing tests still pass — the ring around every caller of the gate
      (`informal/trial.py`, `informal/audits.py`, `rules/experiment.py`):

          $ python -m pytest tests/ -q -k "adapter or firewall or judge or trial or audits"
          145 passed, 2 skipped, 3121 deselected in 60.70s

      **Why the negative assertion is constructed the way it is.** The two
      judge seats in that test are bound to two DIFFERENT schools, so the
      cross-school gate would have ACCEPTED them. Selection-by-configuration
      would therefore have been silent rather than loud, and a test that merely
      checked "the call still raises" would have proved nothing. What is
      asserted instead is the TYPE of the outcome: two families with bindings
      configured returns the cross-family gate's acceptance, and one family of
      judges under a second-family conjecturer raises
      `SECOND_JUDGE_FAMILY_REQUIRED` — the cross-family code, so cross-school
      was never consulted. That second case is also where S7's whole-run
      predicate earns its keep: judged by the judge role alone it would have
      looked single-family and unlocked the substitute.

      Also pinned, the fallback direction: same single-family topology with
      bindings WITHHELD falls back to the gate it cannot satisfy, not to no
      gate at all. Absence of configuration must not be absence of a check.

      `school_judge_bindings` is a constructor opt-in defaulting to `()`, so
      every existing construction of `LLMAdapter` selects cross-family exactly
      as before. **No manifest field**; the standing prohibition holds.

      Two things recorded rather than silently done:

        - `require_cross_family_judges` KEEPS its name though it may now apply
          the cross-school gate. Renaming it would touch `informal/trial.py`,
          `informal/audits.py` and `rules/experiment.py` at 12 call sites, and
          this step's spec item names `adapter.py` alone. Its docstring states
          the truth instead.
        - The seat/endpoint count mismatch inside it still raises
          `JudgeEnsemblePolicyError` under both gates. That failure is about
          pairing, not about distinctness, so it is not the school gate's stop;
          left as-is deliberately.

- [x] 8. (S4) Confirm the formal/informal boundary needs no code change:
      demonstrative outcomes are already status-changing under every mode and
      `programs.evaluable` is already the line (A1).
      files: `tests/test_prose_refutation_boundaries.py`
      done-when: a test shows prose cannot alter a target carrying an evaluable
      commitment, and can alter one that carries none — under the new mode

      Output:

          $ python -m pytest tests/test_prose_refutation_boundaries.py \
                -q -k "formal_boundary or execution_guard or refused_by_type"
          ...                                           [100%]
          3 passed, 18 deselected in 0.52s

      **The step's own premise is half wrong, and correcting it is the
      finding.** The boundary needs no code change — that part holds. But it is
      NOT `programs.evaluable`, as A1 assumed. The line the code enforces is
      `execution_backed` (`rules/warrants.py:24`), consulted at five sites
      including `rules/crit.py:1233` and `informal/trial.py:610`:

        - `execution_backed` = the target carries >=1 commitment whose eval is
          in `oracle.EXEC_PROGRAMS` (exec / property / dataset_oracle) AND
          every one of them currently passes.
        - `programs.evaluable` = any `predicate:` or any known `program:`.

      These are different sets. A `predicate:` commitment is `evaluable` and is
      not execution-backed, so **a target carrying only predicate commitments is
      open to prose refutation today, and remains so under the new mode.**
      Whether R4's "formal claims" is meant to cover those is the operator's
      call, not an assumption to act on: widening the guard would change what
      every existing run may do. Parked in PARKED.md, asserted as-is in the
      test so the current line is pinned either way.

      **Why this is proved by ORDER rather than by running the new mode.** The
      step asked for the assertion "under the new mode", which does not exist
      until step 10. Running it under one mode would in any case only show that
      mode. Instead: in `rules/crit.py` the `execution_backed` guard is
      consulted strictly before `if authority == "observe_only"` is ever
      evaluated, and in `informal/trial.py` the guard `_decline`s with the typed
      reason `execution-backed` before any seat spends. No authority value —
      including one not yet written — can reach past a guard above the branch.
      A future mode added below the guard is still caught; a guard moved below
      the branch fails the test. That is stronger than what the step asked for,
      and it is why this step is GREEN today rather than RED pending step 10.

      S4's acceptance clause "refused with a typed reason" is met by
      `_decline(harness, target_id, "execution-backed", diagnostics)` — the
      refusal is attributable in the record rather than looking like a case
      that merely failed to persuade.

- [x] 9. (S3) Give the refuting endpoint the full argument: the target's
      complete text (no excerpt marker) and its declared `Interface.refs`
      support chain. Scratch stays out (R5/R6).
      files: `src/deepreason/llm/packs.py`
      done-when: for a target exceeding the old budget the pack contains the
      whole text, no `HARNESS PACK EXCERPT` marker, every id in
      `target.interface.refs`, and no `SCR_` handle

      Output — all four clauses in one test, against a ~10 KB target rendered
      at `token_budget=1200`:

          $ python -m pytest tests/test_prose_refutation_boundaries.py \
                -q -k whole_argument
          .                                             [100%]
          1 passed, 21 deselected in 0.08s

          $ python -m pytest tests/ -q -k "pack or crit or trial or audits"
          213 passed, 2 skipped, 3057 deselected in 107.34s

      **Why removing the budget is safe rather than reckless.** The `target`
      section was already `droppable=False, compressible=False`, and
      `packs/allocate.py:76` states the rule: "A non-droppable, non-compressible
      section is retained in full even when it exceeds its declared target."
      So the allocator was never what truncated the argument — the pre-pass
      `_document_excerpt` call was. Removing it lets the existing mandatory-
      section guarantee apply to the target as it already applies to criteria
      and output contracts. An oversize prompt now surfaces as a typed envelope
      failure at dispatch (`RequestEnvelopeExceeded`), which is a visible stop
      rather than a quietly partial case.

      The support chain is rendered in two sections, deliberately:

        - `target-support-chain` (ids + roles) is exact and non-droppable. A
          chain missing an entry reads as a chain that has none, which would
          misstate the argument the critic is answering.
        - `target-support-content` (heads of the referents) is droppable and
          compressible. Losing it costs detail; losing the declaration would
          change what is being claimed.

      **One existing test was updated, and SPEC.md predicted it.**
      `test_long_critic_target_preserves_labeled_tail_instead_of_fake_truncation`
      asserted the excerpt marker's presence. S3's acceptance clause says "no
      `HARNESS PACK EXCERPT` marker", so this is the fixture-update CLAUDE.md
      permits, not an assertion weakened to get green — the replacement asserts
      strictly more: the whole body arrives byte-for-byte, and the pack still
      ends with the directive. Its docstring records why the excerpt existed
      (compact critics refuting valid designs for "ending abruptly") and why
      the new behaviour satisfies that concern more strongly: nothing is
      unshown, so no label is needed to explain an omission away.

      Two findings parked rather than fixed here:

        - `render_batch_crit_pack` still prefix-clips (`packs.py:594`) — the
          very truncation the excerpt helper existed to prevent, and now the
          only crit path where R3 is unmet. S3 names `render_crit_pack` alone.
        - `_document_excerpt` consequently has no caller. Kept, not deleted: it
          is the right tool for the batch path if the operator extends R3 there.

- [x] 10. (S1, S11) [COMMIT] Stop discarding the computed text authority mode,
      and add the single-family authority value to `Config`. Default unchanged
      at `observe_only`. No manifest field.
      files: `src/deepreason/authority.py`, `src/deepreason/config.py`
      done-when: ~~`trial_authority_for` varies with the knob for every
      `AuthoritySurface`~~ **CORRECTED at execution — see SPEC.md's S1
      amendment.** done-when: `trial_authority_for` READS the knob for every
      `AuthoritySurface` and routes on it, with `calibrated_status` gated on a
      verified receipt; non-text still returns `STATUS`; and
      `grep -rn "ARGUMENTATIVE_AUTHORITY\|require_distinct_families"
      src/deepreason/run_manifest.py` shows no new field

      Output:

          rubric          knob=calibrated_status  verified=False -> observe_only
          pairwise        knob=calibrated_status  verified=False -> observe_only
          infrastructure  knob=calibrated_status  verified=False -> observe_only
          non-text  -> status
          default   -> observe_only
          new value -> single_family_trial

          $ grep -rn "ARGUMENTATIVE_AUTHORITY|require_distinct_families" \
                src/deepreason/run_manifest.py
          495:    require_distinct_families: bool
          515:  if self.require_distinct_models or self.require_distinct_families:
          2703: if school_policy.require_distinct_families:

          $ git diff --stat HEAD -- src/deepreason/run_manifest.py
          (empty)

      All three `require_distinct_families` hits pre-date this tranche and are
      the proposing-side school policy SPEC.md already cited; `run_manifest.py`
      is untouched and `ARGUMENTATIVE_AUTHORITY` appears in it nowhere.
      **No manifest field, no state digest, no replay format.**

          $ python -m pytest tests/ -q -k authority -n 4
          191 passed, 2 skipped in 44.70s

      **The done-criterion as planned would have deleted a safeguard the
      operator explicitly kept, and that is why it is corrected rather than
      met.** Implemented literally — knob varies, so `calibrated_status`
      returns `STATUS` — the run of the authority ring failed on
      `test_unverified_calibrated_infrastructure_review_is_observe_only`
      (`tests/test_text_authority_policy.py:166`). That test is right: SPEC.md
      asked Q-B ("does R1 also remove the calibration-receipt precondition?")
      and answered "under (a) it is untouched", and the operator chose (a).

      The gate is load-bearing on a path with no preflight. `ops.py:141`
      `review_infrastructure` and `scheduler.py:1022,1761` call
      `trial_authority_for` with no manifest, so
      `text_status_authority_issues` — which refuses an unverified receipt —
      never runs for them. The unconditional return was the only thing standing
      between a reference string in a config file and live status authority.

      So S1 lands as: the mode is honoured and no longer discarded, and
      `calibrated_status` is refused by a NAMED predicate,
      `calibration_receipt_is_verified(config)`, returning False until a
      verifier exists. Behaviour is unchanged. What changes is that the block is
      one identified gate with one attachment point, instead of a computed
      value thrown away — which is what made the surface knob unreadable in the
      first place, and is the shape already parked as a defect class.
      Recorded as an append-only amendment to SPEC.md S1, not typed in
      silently; overturning it is one operator word and a separate decision
      from R1-R4.

      S11's half landed as planned: `ARGUMENTATIVE_AUTHORITY` gains
      `single_family_trial`, default unchanged at `observe_only`, and
      `authority.py` gains `_TRIAL_AUTHORITIES` so every policy check that
      applies to `trial_required` applies to the new value too — both route
      through the same defended trial and differ only in which ensemble gate
      the run's topology makes available.

- [x] 11. (S1, S11) Reconcile the two authority vocabularies at
      `rules/crit.py:56,87` (`_POLICY_AUTHORITIES` vs `_ARGUMENTATIVE_VALUES`)
      so the new value is accepted consistently or deliberately excluded.
      files: `src/deepreason/rules/crit.py`, `src/deepreason/authority.py`
      done-when: a test asserts the same value is accepted by both, or that the
      new value is rejected by the manifest-bound path with a typed reason

      Output — the second branch of the criterion, DELIBERATELY EXCLUDED:

          $ python -m pytest tests/test_prose_refutation_boundaries.py \
                -q -k "config_only or routes_to_the_same"
          ..                                            [100%]
          2 passed, 22 deselected in 0.17s

          $ python -m pytest tests/ -q -k "crit or authority or scheduler" -n 4
          366 passed, 2 skipped in 90.53s

      **The choice between the criterion's two branches is forced, and by the
      standing prohibition rather than by taste.** `_POLICY_AUTHORITIES` mirrors
      `CriticismPolicyV1.authority`, which is
      `Literal["observe_only", "defended_trial"]` at `run_manifest.py:535` — a
      manifest field. Admitting a third value there changes the manifest schema
      and every qualification subject digest derived from it, and makes roots
      that are replay-valid today read against a schema they were not written
      under. That is precisely what CLAUDE.md calls wrong by definition. So the
      new value is Config-only, and the manifest-bound path refuses it.

      The refusal now names which vocabulary the value belongs to
      (`ARGUMENTATIVE_AUTHORITY_NOT_MANIFEST_BOUND: ... is a Config-only mode
      and cannot be frozen into a criticism policy`) rather than only reporting
      that it is unknown — a caller hitting this needs to know the value is
      real and misplaced, not misspelled. `defended_trial` and `observe_only`
      still resolve exactly as before, asserted alongside.

      Routing: both authority branches in `rules/crit.py` (1313, 1837) now read
      `if authority in _TRIAL_MODES`, so the new mode reaches the IDENTICAL
      defended trial rather than a parallel one. A6 reads "mint criticisms" as
      making the existing path completable, not as inventing a second route to
      a warrant, and a second trial call would have been exactly that. Which
      ensemble that trial then demands is decided downstream by route topology
      in `adapter._select_judge_ensemble`; the criticism rule decides only
      observe-or-try, and knows nothing about families or schools.

      The test asserts the literal string `if authority == "trial_required":`
      no longer appears anywhere in the module, so a third branch added later
      cannot silently reintroduce the split.

- [x] 12. (S2) [COMMIT] Show the end-to-end result offline: a single-family run
      with the new mode produces `len(state.att) >= 1` and at least one
      `Status.REFUTED`, from a criticism whose target carries no evaluable
      commitment and whose critic school differs from the target's.
      files: `tests/test_prose_refutation_boundaries.py`
      done-when: that test passes (paste it)

      Output:

          test_a_single_family_run_can_refute_by_prose_end_to_end PASSED
          test_the_same_run_under_the_old_mode_refutes_nothing PASSED
          test_the_minting_critic_carries_a_school_other_than_the_targets PASSED
          3 passed, 24 deselected in 0.22s

      The typed record the demo produces, printed rather than described:

          single_family_run: True
          judge families   : {'mock:glm'}
          bound schools    : ('school-0', 'school-1')
          len(state.att)   : 1
          target status    : refuted
          warrant type     : argumentative

      **This is the first attack edge any prose case has produced in this
      codebase.** The baseline at step 1 was 26 of 42 roots carrying
      `adjudication-blindness` — criticism executed, zero attacks, every
      artifact vacuously ACCEPTED.

      Three guards on the claim, because "it went red" is not by itself
      evidence for S2:

        - **The refutation is prose, not machinery.** CHECKLIST's own risk note
          says that if the defeat came from the mechanical-checking channel the
          step has NOT demonstrated S2. The warrant is asserted to be
          `ARGUMENTATIVE`, and the target's only commitment is `rubric:`, which
          `programs.evaluable` rejects and no oracle can run. Printed above as
          `warrant type: argumentative`.
        - **The mode is what changed, not the fixture.** The identical target
          and identical adapter under `observe_only` leave `state.att` empty and
          the target ACCEPTED, with the case still recorded as scrutiny. Without
          this the first test could have been passing for the wrong reason.
        - **The minting critic's school differs from the target's**, asserted on
          the artifact the warrant hangs from rather than only where the
          assignment was planned (step 4).

      **The fixture failed first, and the predicate was right.** The initial
      adapter gave the judges `glm-test` and left critic/defender on the default
      mock model, and `is_single_family_run` returned False. That is R15 working
      as specified — "a single model is running the ENTIRE harness" — and it is
      the case step 5 deliberately widened the predicate to catch. Every seat
      now carries one model id.

      **RESIDUE — what this does NOT show.** The one production adapter factory
      (`llm/adapter.py:1467`) does not pass `school_judge_bindings`, so no live
      run can select the cross-school gate today: the architecture is complete
      and proven offline, and unwired. The natural source is
      `run_manifest.criticism_policy.bindings` filtered to `role == "judge"`,
      but nothing in R7-R17 or S7-S12 asks for that wiring, and adding it would
      change gate selection for every v6 run carrying judge bindings. Parked
      rather than typed in. Related: in a v6 manifest run authority comes from
      `CriticismPolicyV1.authority` (`scheduler.py:1321`), so such a run reaches
      this same trial through `defended_trial` and never reads the Config value
      — `single_family_trial` is the direct-helper switch, and route topology is
      what selects the ensemble in both cases.

- [x] 13. (S3, S10) Re-run steps 3 and 4's assertions now that the mode exists.
      files: none
      done-when: the whole of `tests/test_prose_refutation_boundaries.py`
      passes, including the byte-identity halves that were RED

      Output:

          $ python -m pytest tests/test_prose_refutation_boundaries.py -q
          ...........................                   [100%]
          27 passed in 2.74s

      The specific assertion that was RED from step 3 through step 9, and the
      author/school halves it was guarding:

          test_the_single_family_authority_value_exists PASSED
          test_the_criticism_prompt_never_names_an_author_or_a_school PASSED
          test_the_planner_leaves_a_single_school_run_with_no_eligible_critic PASSED

      `test_the_single_family_authority_value_exists` was written at step 3
      precisely so the structural assertions could not pass vacuously against a
      mode that did not exist. It is now GREEN for the reason it was written to
      wait for — `Config(ARGUMENTATIVE_AUTHORITY="single_family_trial")`
      validates — which retroactively makes steps 3, 4 and 8's structural
      claims claims about a real mode.

      Nothing was re-run "to check": the file grew from 11 assertions at step 4
      to 27, and all 27 pass together, so the byte-identity and author-school
      properties hold in the presence of the whole change rather than only
      before it.

- [x] 14. (all) Full gate: `pytest tests/ -q -n 4`
      done-when: output ends "N passed, 0 failed" — paste it. No assertion
      weakened anywhere (C2).

      Output:

          $ python -m pytest tests/ -q -n 4
          3270 passed, 7 skipped in 557.78s (0:09:17)

      **0 failed.** 3243 at the start of this tranche, 3270 now — 27 added, none
      removed.

      C2 ("Never weaken an assertion to get green"), accounted for explicitly.
      Exactly one existing assertion changed anywhere in the tranche:
      `tests/test_pack_prefix.py`'s excerpt test at step 9. It asserts strictly
      MORE than before — the whole target body byte-for-byte, where it
      previously accepted a head/tail excerpt — and SPEC.md's S3 predicted the
      change in advance ("no `HARNESS PACK EXCERPT` marker"). Every other test
      in the repository is untouched.

      Note on the invocation: `python -m pytest`, not bare `pytest`. The
      container's PATH now resolves `pytest` to a uv-tool shim that cannot see
      the editable install, which reports a conftest ImportError rather than a
      test failure.

- [x] 15. (S6, S11) Capture the AFTER sweep with the identical script from
      step 1 and diff.
      done-when: no root's `valid` changes and no root's `len(state.att)`
      changes; report any `epistemic_checks_passed` movement as a number

      Output — the same `root_sweep.py`, unedited since step 1:

          SWEEP COMPLETE: 42 roots -> .../scratchpad/sweep_AFTER.txt

          roots BEFORE=42 AFTER=42
          only in BEFORE: none
          only in AFTER : none

          valid:            0 changed
          att:              0 changed
          epistemic_passed: 0 changed
          blind:            0 changed
          ERROR:            0 changed

          $ diff -q sweep_BEFORE.txt sweep_AFTER.txt
          BEFORE and AFTER sweeps are BYTE-IDENTICAL

      **`epistemic_checks_passed` movement: 0 roots.** Reported as the number
      the step asked for rather than as "none", because zero is the claim.

      The field-by-field diff is the weaker check and the byte comparison is
      the stronger one; both are run, and the field diff is kept because it
      would localise a difference if one appeared. The diff script treats a
      root present in one file and absent from the other as a DIFFERENCE rather
      than skipping it — a no-change result computed over an intersection would
      hide exactly the thing a retroactivity check exists to catch. Both
      "only in" lines are empty.

      Unchanged distribution, for the record: 21 roots `valid=True
      epistemic_passed=False`, 11 `UnsupportedRunManifestVersionError` (the
      known pre-v6 set), 5 `valid=True epistemic_passed=True`, 5
      `valid=False`.

      This is S6 and S11's acceptance met: **the change is prospective only.**
      Every existing root verifies to the same verdict, carries the same
      attacks, and passes or fails the same epistemic checks as before — which
      is what C3 requires and what makes the new authority mode a change to
      what future runs may do rather than a reinterpretation of what past runs
      did.

- [x] 16. (all) [COMMIT] Push and confirm clean.
      done-when: `git status --porcelain` is empty AND the branch head is on
      origin

      Output:

          $ git status --porcelain
          (empty)

          local  HEAD: 2f02dfc1137de41b31d2dd23446af28622aa753a
          origin HEAD: 2f02dfc1137de41b31d2dd23446af28622aa753a
          branch head IS on origin

      Twelve commits, one per step, `c1cfb891`..`2f02dfc1` on
      `claude/amendment-epochs-om0ztb`. Every scratch artifact — the sweep
      script, both sweep files, the diff script — lives in the session
      scratchpad and none of it is in the repository.

---

# APPENDED after VALIDATION.md's FAIL and amendments 5-6 (S13-S20)

Steps 1-16 are history and are not rewritten. These continue from 17.
Same standing prohibition: no manifest field, no manifest VALIDATOR, no state
digest, no event application order, no replay record format. A step that turns
out to need one STOPS and reports.

Order rationale: the formal-line work (S17-S19) lands FIRST because it changes
what is protected, and the exposure work (S13-S15) builds a demo whose target
must still be refutable under the new line — running them the other way would
make step 21's demo prove nothing.

- [x] 17. (S17) [COMMIT] Add `formally_backed` beside `execution_backed`:
      carries >=1 EVALUABLE AND SUBSTANTIVE commitment and every such
      commitment currently passes. `execution_backed` unmodified.
      files: `src/deepreason/rules/warrants.py`,
      `tests/test_prose_refutation_boundaries.py`
      done-when: True for a passing `predicate:` target; True for a passing
      exec-oracle target; **False for a target whose only evaluable commitment
      is `program:json-wf`**; False when a qualifying commitment fails — paste
      all four, plus `git diff` showing zero changed lines inside
      `execution_backed`

      Output — all four, with `execution_backed` shown alongside so the
      superset relation is visible rather than claimed:

          passing predicate:              formally_backed=True  execution_backed=False
          passing exec oracle             formally_backed=True  execution_backed=True
          ONLY program:json-wf            formally_backed=False execution_backed=False
          FAILING predicate:              formally_backed=False execution_backed=False

          execution_backed byte-identical to HEAD: True (1947 bytes)

          $ python -m pytest tests/test_prose_refutation_boundaries.py \
                -q -k "formal_backing or structural_program or failing_formal"
          3 passed, 27 deselected in 1.20s

      The third row is R22 made concrete: `program:json-wf` is evaluable and
      passes for anything well-formed, and it is reachable by a model through
      safe skeleton compilation. Under R21 read as "evaluable" it would confer
      immunity. It confers none.

      `_substantive` is reused from `measures/reach.py` rather than copied:
      that module already refuses reach from structural programs for the same
      stated reason — they "prove nothing about the subject". One definition,
      two consumers.

- [x] 18. (S18) [COMMIT] Move the three argumentative guards from
      `execution_backed` to `formally_backed`.
      files: `src/deepreason/rules/crit.py`, `src/deepreason/informal/trial.py`
      done-when: a target carrying a passing `predicate:` commitment is refused
      with a typed reason (S4's original first clause, which FAILED at
      validation, now holds); a target carrying none is still refuted; the
      typed reason strings are unchanged from their recorded values

      Output:

          passing predicate: (FORMAL)     att=0 status=accepted
          rubric: only (informal)         att=1 status=refuted
          ONLY program:json-wf            att=1 status=refuted

          $ python -m pytest tests/ -q -n 4 \
                -k "crit or trial or oracle or warrant or audits or loop or workload"
          303 passed, 2 skipped in 40.50s

          $ python -m pytest tests/test_prose_refutation_boundaries.py -q
          34 passed in 3.62s

      Row 1 closes VALIDATION.md's FAIL. Row 3 is R22 shut end to end.

      **ONE guard moved, not three, and the step's own plan was wrong about
      that.** Moving all three broke `test_loop.py::
      test_argumentative_critic_attack_is_observe_only`, and the test was
      right. Diagnosed rather than patched: `pi-tides`' criterion is
      `predicate:'moon' in content`, and problem criteria are instantiated into
      EVERY candidate's interface (`tests/test_loop.py:66`). So widening the
      criticism rule's own guard suppresses the SCRUTINY RECORD for every
      target carrying a passing problem criterion — the case is discarded
      rather than declined. That moves toward adjudication blindness, which is
      the defect the previous tranche existed to detect. R4/R21 are about
      REFUTATION, not about whether a criticism is recorded.

      So `formally_backed` is consulted at exactly ONE site,
      `informal/trial.py:614` — the only point at which a prose case can mint a
      warrant. `rules/crit.py` is byte-identical to HEAD; its two
      `execution_backed` guards are untouched. A test now pins that scrutiny is
      still recorded for a formal target under `observe_only`.

      Blast radius measured across every openable root BEFORE deciding:

          TOTAL artifacts=1279  execution_backed=0  formally_backed=148
          prose-refutable BEFORE: 100.0%   AFTER: 88.4%

      148 of 1279 recorded artifacts (11.6%) carry a passing substantive formal
      commitment and would become immune to prose refutation. It is not uniform:
      one root (`run-9175f0ec`, epoch 3) goes from 79 refutable to 31. Reported
      as a number rather than a reassurance — this is what "they are both
      formal" costs, and it is the operator's call whether that is the intended
      price.

      The decline reason keeps the string `execution-backed`. Renaming it would
      change what recorded roots' diagnostics mean, which C3 forbids.

      One existing assertion updated, and S18 predicted it: step 8's
      `..._is_refused_by_type` asserted the trial's guard is named
      `execution_backed`. It now asserts `formally_backed` and the same typed
      reason — the guard moved, which is the step.

- [ ] 19. (S19) Assert the self-immunisation hole is shut.
      files: `tests/test_prose_refutation_boundaries.py`
      done-when: a target whose ONLY evaluable commitment is a
      model-authorable structural program is still refuted by prose; and
      `ForbiddenCase` still refuses `predicate:` — paste both

- [ ] 20. (S13) [COMMIT] Add `is_single_model_run`: exactly one distinct model
      identity across every leased seat of every role.
      files: `src/deepreason/llm/firewall.py`
      done-when: True for one model across all roles; **False for two models
      sharing one family** (this is what distinguishes it from S7); False for
      an empty lease set; and `is_single_family_run` still passes its own tests

- [ ] 21. (S14) [COMMIT] In a single-model run the trial requires >=2 judge
      seats plus a critic school present and differing from the target's
      author school, instead of the cross-family ensemble.
      files: `src/deepreason/informal/trial.py`
      done-when: single-model + differing schools mints an ARGUMENTATIVE
      warrant; same run with critic school == author school is refused with a
      typed reason; same run with no critic school is refused with a typed
      reason; a two-MODEL run still raises `SECOND_JUDGE_FAMILY_REQUIRED`

- [ ] 22. (S15) [COMMIT] Exposure: selection keys on the predicate alone. No
      constructor argument, Config value or manifest field is required.
      files: `src/deepreason/llm/adapter.py`
      done-when: an adapter built by `build_adapter` itself — not hand-fed
      bindings — with one model on every seat reaches the substitute path;
      with two models it does not

- [ ] 23. (S16, S20) Full gate: `pytest tests/ -q -n 4`
      done-when: output ends "N passed, 0 failed" — paste it

- [ ] 24. (S16, S20) AFTER sweep with the step-1 script; diff against
      `sweep_BEFORE.txt`.
      done-when: no root's `valid` and no root's `att` changes. Widening what
      is PROTECTED can only remove future attack edges, never add edges to
      recorded roots — measured, not assumed.

- [ ] 25. (all) [COMMIT] Push and confirm clean.
      done-when: `git status --porcelain` empty AND branch head on origin

## Coverage

S1 -> 10, 11.  S2 -> 12.  S3 -> 9, 13.  S4 -> 8, 18.  S5 -> 2.  S6 -> 1, 15.
S7 -> 5.  S8 -> 6, 7.  S9 -> 4.  S10 -> 3, 13.  S11 -> 1, 10, 15.  S12 -> 2.
S13 -> 20.  S14 -> 21.  S15 -> 22.  S16 -> 23, 24.  S17 -> 17.  S18 -> 18.
S19 -> 19.  S20 -> 23, 24.

## Risks carried from FEASIBILITY.md that steps must respect

- Step 12 is the one that could break a live run if done wrong: reusing the
  existing criticism-obligation records with author-equals-critic raises before
  the model is contacted. This tranche keeps author != critic (S9), so the
  hazard should not arise — step 4 is what proves it.
- The mechanical-checking defeat channel stays untouched (A7). If step 12's
  refutation turns out to come from that channel rather than from prose, the
  step has NOT demonstrated S2 and must say so.
