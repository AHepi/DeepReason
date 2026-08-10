# Checklist for: adjudication / judge-seats / legacy-criticism / schools opt-ins
State: next=3 blockers=none
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

Map ids (preflight, re-affirmed from SPEC.md's own header plus Road E's
newly-scoped territory): `DR-CON-seats`, `DR-SUB-adjudication`,
`DR-CON-authority`, `DR-CON-schools`, `DR-INV-frozen-surfaces`,
`DR-SEAM-adjudication-x-authority`, `DR-SEAM-manifest-x-schools`,
`DR-SEAM-schools-x-scratch` — plus, for Road E specifically (not named in
SPEC.md's original frozen-surface forecast, added here from a fresh map
read): `DR-SUB-scheduler` (owns `_arg_crit`, `_defer_untransactional_v6_phase`,
`_maybe_config_referee` — the exact precedent Road E extends) and the
`scheduler x workflow` seam (coupling 16, undocumented as a written
`SEAM-*.md` file — `docs/map/INDEX.md`'s matrix confirms no
`DR-SEAM-scheduler-x-workflow.md` exists yet; Step 1 below reads the two
subsystems directly since no seam document exists to read first).

Diff budget: computed ceiling **1,600 lines** (Road E ~600: new contract
type + scheduler wiring + recovery handling + tests; four opt-ins ~180
each = 720: Config field + gate + tests + qual-exclusion test per opt-in;
static signal-read surface ~180; map-doc updates ~100, co-committed with
their behavior per rule 4c). Per REQUEST.md C10 (Amendment 2), an actual
overrun does not stop execution — `tools/diff_budget.py` runs at every
`[COMMIT]` step regardless, and the real cumulative total is reported at
delivery, not pre-judged here.

Ordering (operator's explicit requirement, REQUEST.md Amendment 5/C13):
Road E first (S: R13/Road E) → the four opt-in surfaces, each reader
before writer (S2a/R1, S2c/R3 — folds Road E's circuit into an
operator-facing switch, S2b/R2, S2d/R5) → the static signal-read surface
(R15) → map documents in the same commit as the behavior they describe.

---

## PART A — Road E: the pre-school criticism circuit's v6 transaction contract
(S: SPEC.md "R13 (Amendment 4)"/Road E; R13, R3)

- [x] 1. (R13) Read `src/deepreason/workflow/transaction_service.py`
      (`InquiryTransactionService` and neighbors), `src/deepreason/referee.py`'s
      `run_config_referee` (`:455-...`) in full, and
      `src/deepreason/workflow/nonconjecture_recovery.py`'s
      `_config_referee_contract`/`_recover_config_referee_effect`
      (`:538-660`). Confirm in a short written note (pasted as this step's
      output, not a new file) which existing classes/functions Road E
      reuses verbatim (expect: `InquiryTransactionService`,
      `RouteLeaseRefV1`, `WorkflowTaskKind`, the durable
      `harness.workflow_state.transaction_work`/`harness.blobs` machinery),
      and confirm affirmatively that none of `harness.py`,
      `capabilities/state.py`, `invariants.py`, or `run_manifest.py`
      SCHEMA fields need to change to build a new contract this way — only
      a new contract-id constant (mirroring
      `CONFIG_REFEREE_CONTRACT_V1 = "config-referee.v1"`) and a new
      payload schema string (e.g. `"legacy-argumentative-criticism.v1"`).
      done-when: the note explicitly confirms zero contact with the four
      named files above, or names exactly what contact is required (in
      which case this is a STOP per REQUEST.md Amendment 5's un-forecast
      rule, not a step to continue past).

      **Design note (done-criterion output):**

      Reused verbatim, zero changes: `InquiryTransactionService`
      (`.prepare`, `.issue`/`.reserve_dispatch`/`.finalize_dispatch`,
      `.record_provider_attempt`, `.record_semantic_admission`,
      `.terminate`, `.repair_schema_failure`) — all generic v6
      transaction primitives with no criticism-specific logic;
      `RouteLeaseRefV1`, `WorkflowTaskKind` (Road E dispatches under the
      SAME `WorkflowTaskKind.CRITICISM` kind config_referee already uses,
      `referee.py:553`); `route_fingerprint`, `select_lease` from
      `llm/firewall.py`; `harness.record_transaction_transition`,
      `harness.blobs.put`, `harness.workflow_state.transaction_work` — all
      pre-existing generic harness API, no new method.

      `run_config_referee` (`referee.py:493-508`) is the EXACT dispatch
      template: `if criticism is not None: resolve_school_role_lease(...)
      else: critic_school_id = None; select_lease(adapter.leases,
      "argumentative_critic", 0)`. This is already the
      `criticism_policy=None` fallback shape Road E needs — config_referee
      already handles the school-free case for ITS OWN dispatch. Road E's
      new dispatch function for `crit_argumentative_batch`'s plain branch
      follows this identical shape.

      Recovery — NOT directly reusable, confirmed by reading
      `_criticism_contract` (`nonconjecture_recovery.py:643-718`) in full:
      it hard-requires `manifest.criticism_policy is not None` (line 649,
      `_authority(policy is not None, "manifest does not authorize
      criticism")`) and resolves a `critic_school_id` against
      `policy.bindings` (line 651-653) — this is the SCHOOL-ROUTED
      recovery path only, structurally incompatible with a
      `criticism_policy=None` circuit. Confirmed the correct insertion
      point instead: `recover_nonconjecture_admission`
      (`nonconjecture_recovery.py:1036-1052`) already special-cases
      `payload.get("schema") == "config-referee.semantic-task.v1"` AHEAD
      OF the generic `WorkflowTaskKind.CRITICISM` fallback that reaches
      `_criticism_contract`. Road E needs the identical shape: a new
      special-cased branch for
      `payload.get("schema") == "legacy-argumentative-criticism.v1"`,
      inserted ahead of the same generic fallback, with its own
      `_legacy_arg_criticism_contract`/`_recover_legacy_arg_criticism_effect`
      pair (Step 5) — NOT a reuse of `_criticism_contract`/
      `_recover_criticism_effect`.

      **Frozen-surface confirmation**: zero contact with `harness.py`
      (only pre-existing public methods called, none added),
      `capabilities/state.py` (unrelated — simulation/research proposal
      state, never imported by any file read in this step),
      `invariants.py`/replay-validation formats (unchanged — replay reads
      whatever the harness recorded generically, no new format), or any
      `run_manifest.py` SCHEMA field (`RunManifest`, `RunManifestError`,
      `resolve_route_seat_behavioral_capability`,
      `resolve_route_seat_base_profile` are READ-ONLY imports already used
      by this exact file for config_referee; no new Pydantic model field).
      Confirmed: proceed, no STOP.
- [x] 2. (R13) Write the new contract-id constant and payload schema
      module-level declaration in `src/deepreason/rules/crit.py` (co-located
      with `crit_argumentative_batch`, the function it will wrap), mirroring
      `referee.py:332`'s `CONFIG_REFEREE_CONTRACT_V1` pattern exactly:
      `LEGACY_ARG_CRITICISM_CONTRACT_V1 = "legacy-argumentative-criticism.v1"`.
      done-when: `python -c "from deepreason.rules.crit import LEGACY_ARG_CRITICISM_CONTRACT_V1; assert LEGACY_ARG_CRITICISM_CONTRACT_V1 == 'legacy-argumentative-criticism.v1'"`
      exits 0.

      ```
      $ python -c "from deepreason.rules.crit import LEGACY_ARG_CRITICISM_CONTRACT_V1; assert LEGACY_ARG_CRITICISM_CONTRACT_V1 == 'legacy-argumentative-criticism.v1'; print('OK')"
      OK
      ```
- [ ] 3. (R13) Write the failing test FIRST (rule 1: test precedes the
      change it guards): a new test in `tests/test_v6_scheduler_model_phase_deferral.py`
      asserting that, given a manifest with `criticism_policy=None` and
      schema_version 6, and at least one eligible admitted-and-accepted
      target, `Scheduler._arg_crit` dispatches a live
      `crit_argumentative_batch` call (via the new transaction contract)
      INSTEAD of recording a `"v6-model-phase-deferred.v1","argumentative-criticism"`
      marker. done-when: `python -m pytest tests/test_v6_scheduler_model_phase_deferral.py::test_legacy_argumentative_criticism_dispatches_under_v6 -q`
      currently FAILS (red, confirming the test exercises code that does
      not exist yet) — paste the failure output.

      **STOP — contradiction with the tree found before the test could even
      be usefully written.** Per dr-execute-step's own rule ("Mid-step
      discoveries... if the change cannot land without them, back through
      dr-spec-change as an amendment — never just typed in") and Amendment
      6's "all stop conditions live": this is not typed in silently.

      `crit_argumentative_batch` (`rules/crit.py:1341-1356` signature,
      guard at `:1372-1379`) is NOT the simple dispatch function Step 1's
      design note and SPEC.md's R13/Road E assumed. Read in full just now:

      ```python
      active_v6 = False
      if run_manifest is not None:
          run_manifest = RunManifest.model_validate(run_manifest)
          active_v6 = run_manifest.schema_version == 6
      if active_v6 and (endpoint_lease is None or critic_school_id is None):
          raise ValueError("v6 criticism requires one manifest-bound school route")
      ```
      (`rules/crit.py:1372-1379`) — the function ITSELF refuses a v6,
      school-free call, independent of the scheduler's own defer logic.
      And its `active_v6` branch (`rules/crit.py:1436-1456+`) is not a
      thin wrapper around `InquiryTransactionService` — it directly
      constructs the transactional payload inline, hard-coupled to schools:
      ```python
      if active_v6:
          assert endpoint_lease is not None
          assert critic_school_id is not None
          ...
          expected_strong_payload = {
              "schema": "criticism.semantic-task.v1",
              "critic_school_id": critic_school_id,
              ...
          }
      ```
      (`rules/crit.py:1436-1456`) — `"criticism.semantic-task.v1"` is the
      exact schema string `nonconjecture_recovery.py::_criticism_contract`
      (Step 1's note) checks for, confirming this whole branch — not just
      the recovery side — is school-routing-specific by construction, and
      the transactional dispatch itself is likely another 100+ lines deep
      in this same branch (not yet fully read).

      **Decision needed, one sentence**: does Road E's school-free circuit
      reuse `crit_argumentative_batch` by widening its existing `active_v6`
      branch to accept a second, non-school dispatch shape (new kwarg,
      new payload schema, real regression risk to the live school-routed
      path this function already serves), or does it dispatch
      independently via a smaller, parallel function that calls
      `adapter.call(..., dispatch_authorization=...)` directly — closer to
      `run_config_referee`'s own shape — at the cost of duplicating
      `crit_argumentative`'s case-observation/counterexample/authority-gate
      logic for the school-free case?

      **Road A — widen `crit_argumentative_batch`'s existing `active_v6`
      branch.** Add an explicit, typed alternative to the
      `endpoint_lease is None or critic_school_id is None` guard: a new
      keyword (e.g. `legacy_v6_dispatch: bool = False`) that, when True,
      permits `critic_school_id is None` and routes the `active_v6` branch
      through the new `"legacy-argumentative-criticism.v1"` payload schema
      instead of `"criticism.semantic-task.v1"`. Reuses the real,
      already-tested case/counterexample/authority-gate logic
      (`crit_argumentative`'s body, shared by both branches) — the
      original design intent. Cost: touches a function
      `tests/test_foreign_school_criticism_scheduler_c3.py` and the live
      school-routed path depend on daily; every existing test in that file
      must still pass byte-identically after the change (regression risk
      is real, not hypothetical, given how deeply `critic_school_id`
      threads through the `active_v6` branch's payload construction).
      Diff size for this branch alone is larger than CHECKLIST.md's
      original ~600-line Road E estimate assumed for the whole road.

      **Road B — dispatch independently, parallel to `crit_argumentative_batch`.**
      A new, smaller function in `rules/crit.py` (or scheduler-adjacent)
      that follows `run_config_referee`'s shape exactly: build the pack via
      the EXISTING `render_crit_pack`/`render_batch_crit_pack` (reused,
      read-only), then dispatch through `InquiryTransactionService`
      directly with the new `LEGACY_ARG_CRITICISM_CONTRACT_V1`/
      `"legacy-argumentative-criticism.v1"` payload, calling
      `adapter.call(..., dispatch_authorization=authorized, ...)` inline
      rather than through `crit_argumentative`'s shared body. Cost: does
      NOT reuse `crit_argumentative`'s counterexample-grounding/
      execution-supremacy/authority-gate sequence — that logic (roughly
      `rules/crit.py:1229-1326`) would need to be duplicated or factored
      into a shared helper both the school-routed and school-free paths
      call, which is itself new design work SPEC.md never scoped. Zero
      regression risk to the existing school-routed path (touches no
      shared code), but the "reuses the already-written dispatch function"
      claim in SPEC.md's R13/Road E and CHECKLIST.md's original pricing
      (`~600 lines`, "the dispatch function... already written and
      exercised daily") is not accurate under this road — the true cost is
      closer to writing a second, smaller version of `crit_argumentative`.

      **Recommendation**: Road A, but the diff-budget ceiling this
      tranche computed (1,600 lines total, ~600 for Road E) needs revising
      upward once the exact shape of the widened `active_v6` branch is
      known — this is new information C10/Amendment 2's "report the final
      total at delivery" pre-authorization does not resolve on its own,
      because it is a SCOPE question (which of two designs to build, with
      real regression-risk difference), not a budget-overrun question.
      Amendment 6's "all stop conditions live" governs: this is a stop for
      operator words, not a judgment call this skill invocation makes
      unilaterally.

      Left unchecked. Returning to the orchestrator per dr-execute-step's
      exit criteria (step failed/contradicted the tree).
- [ ] 4. (R13) [COMMIT] Wire `scheduler.py::_arg_crit`'s plain
      (`criticism_policy is None`) branch: replace the unconditional
      `self._defer_untransactional_v6_phase("argumentative-criticism", ...)`
      + `continue` (at the schema_version==6 check inside the batch loop,
      `scheduler.py:1247-1257`) with a call through the new
      `LEGACY_ARG_CRITICISM_CONTRACT_V1` transaction, following
      `_maybe_config_referee`'s dispatch shape exactly (fail-to-default:
      an unreachable provider or a transport/schema-repair failure drops
      into diagnostics via the SAME `except (SchemaRepairError, EndpointError)`
      pattern already present in this method's non-v6 branch — never
      raises the whole run). done-when: Step 3's test now PASSES; paste
      `python -m pytest tests/test_v6_scheduler_model_phase_deferral.py::test_legacy_argumentative_criticism_dispatches_under_v6 -q`
      output ending "1 passed". Then run
      `python tools/diff_budget.py $(git merge-base HEAD origin/main) --ceiling 1600`
      and paste its output before committing.
- [ ] 5. (R13) Recovery handling: extend
      `workflow/nonconjecture_recovery.py` with a
      `_legacy_arg_criticism_contract`/`_recover_legacy_arg_criticism_effect`
      pair mirroring `_config_referee_contract`/`_recover_config_referee_effect`
      exactly, dispatched from the same generic recovery switch (keyed on
      `payload.get("schema") == "legacy-argumentative-criticism.v1"`).
      done-when: a new test
      `tests/test_v6_scheduler_model_phase_deferral.py::test_legacy_argumentative_criticism_recovers_after_interruption`
      (simulating a crash mid-transaction, then reopening the root)
      passes.
- [ ] 6. (R13) Reader test (partition claim): assert the
      `v6-model-phase-deferred.v1` marker is STILL correctly emitted for
      every OTHER legacy phase (`hv-floor`, `hv-spot-check`, `rubric-trial`)
      — i.e. Step 4's change is scoped to exactly the
      `"argumentative-criticism"` phase and does not accidentally
      un-defer anything else. done-when:
      `python -m pytest tests/test_v6_scheduler_model_phase_deferral.py -q`
      passes in full (paste the summary line).
- [ ] 7. (R13) Map update, same commit as the behavior (rule 4c): edit
      `docs/map/SUB-scheduler.md`'s row "A legacy model phase v6 cannot
      yet dispatch | `_defer_untransactional_v6_phase` at the phase's call
      site" to note the `"argumentative-criticism"` phase is now an
      EXCEPTION (dispatches via `LEGACY_ARG_CRITICISM_CONTRACT_V1` instead
      of deferring), citing this tranche. Add a `Traps` entry naming this
      tranche's run id once Step 4/6's tests exist, per the map's own
      "every fix earns a Traps entry" rule. done-when:
      `python tools/docs_verify.py` reports 0 failed for `SUB-scheduler.md`.
- [ ] 8. (R13) [COMMIT] Subsystem test ring:
      `python -m pytest tests/test_scheduler.py tests/test_v6_scheduler_model_phase_deferral.py tests/test_config_referee.py -q`.
      done-when: output ends "N passed, 0 failed" (paste it). Run
      `python tools/diff_budget.py $(git merge-base HEAD origin/main) --ceiling 1600`,
      paste output, commit with message citing R13/Road E, push with
      retry.

---

## PART B — Legacy-criticism-paths opt-in
(S: SPEC.md §2(c) as revised by R13/Road E; R3, C3, C8)

This is the operator-facing switch that makes ordinary (`setup`/`prepare`)
runs able to reach Road E's now-working circuit, instead of only the
low-level `deepreason compile` path reaching it.

- [ ] 9. (S2c, R3) Reader/default test FIRST: a new test
      `tests/test_preparation.py::test_legacy_criticism_disabled_by_default_is_byte_identical`
      asserting `Config().LEGACY_CRITICISM_ENABLED is False` and that
      `build_preparation_manifest(...)`'s output `manifest.criticism_policy`
      is UNCHANGED (still `engaged_criticism_policy(...)`) when the field
      is at its default. done-when: the test currently FAILS only because
      `LEGACY_CRITICISM_ENABLED` does not exist yet (paste the
      `AttributeError`).
- [ ] 10. (S2c, R3) Add `LEGACY_CRITICISM_ENABLED: bool = False` to
      `src/deepreason/config.py`, adjacent to the other authority-family
      knobs (`ARGUMENTATIVE_AUTHORITY` etc., `config.py:365-401`), with a
      docstring-comment naming what it does: when True, ordinary
      manifest-building routes criticism through the school-free circuit
      Road E built instead of the school-routed one.
      done-when: Step 9's test now passes for the default-False half;
      paste output.
- [ ] 11. (S2c, R3) [COMMIT] Wire `preparation.py::build_preparation_manifest`
      (`:387-396`) so that when `config.LEGACY_CRITICISM_ENABLED` is True,
      it passes `criticism_policy=None` to `compile_run_manifest` instead
      of `criticism_policy=engaged_criticism_policy(...)`. done-when: a
      second assertion in Step 9's test file,
      `test_legacy_criticism_enabled_routes_to_school_free_circuit`,
      confirms `manifest.criticism_policy is None` when the flag is True
      — paste `python -m pytest tests/test_preparation.py -k legacy_criticism -q`
      ending "2 passed". Run `python tools/diff_budget.py $(git merge-base HEAD origin/main) --ceiling 1600`,
      paste, commit, push.
- [ ] 12. (S2c, C3) Add the `_versioned_source_config_data` pop-line for
      `LEGACY_CRITICISM_ENABLED` in `run_manifest.py`, UNCONDITIONALLY for
      every schema version, per the `ENGAGED_CRITICISM_AUTHORITY` trap
      (`docs/map/INV-frozen-surfaces.md:185-208`) — this is the named,
      forecast frozen-surface-4-adjacency contact from SPEC.md's own
      forecast; see the CHECKLIST STOP's grant request below before this
      step executes. done-when:
      `python -m pytest tests/test_run_manifest.py -k canonical_shapes_and_hashes -q`
      still passes (proves the new field does not silently enter any
      pinned hash), paste output.
- [ ] 13. (S2c, C9/surface-5 forecast) Qualification-subject-exclusion
      test: assert `LEGACY_CRITICISM_ENABLED` does NOT appear in
      `qualification_subject_payload`'s output (it gates dispatch routing,
      not provider identity, per SPEC.md's frozen-surface forecast).
      done-when: a new assertion in
      `tests/test_qualification.py::test_legacy_criticism_flag_excluded_from_subject_digest`
      passes.
- [ ] 14. (S2c, R3) End-to-end integration test: with
      `LEGACY_CRITICISM_ENABLED=True` on an ordinary `build_preparation_manifest`-built
      manifest, a scheduler run with an eligible target actually dispatches
      a live `crit_argumentative_batch` call through Road E's contract (not
      deferred). done-when:
      `python -m pytest tests/test_scheduler.py -k legacy_criticism_end_to_end -q`
      passes.
- [ ] 15. (S2c) Map update, same commit: add a row to
      `docs/map/CON-authority.md`'s "Where it lives" table for
      `LEGACY_CRITICISM_ENABLED`, and cross-reference from
      `docs/map/CON-seats.md` (which owns `preparation.py`) noting the new
      Config-driven branch in `build_preparation_manifest`. done-when:
      `python tools/docs_verify.py` reports 0 failed for both documents.
- [ ] 16. (S2c) [COMMIT] Subsystem ring:
      `python -m pytest tests/test_preparation.py tests/test_run_manifest.py tests/test_qualification.py tests/test_scheduler.py -q`.
      done-when: "N passed, 0 failed" (paste). Diff budget check, commit,
      push.

---

## PART C — Adjudication opt-in
(S: SPEC.md §2(a); R1, C3)

- [ ] 17. (S2a, R1) Reader/default test FIRST:
      `tests/test_text_authority_policy.py::test_adjudication_status_authority_disabled_by_default_is_byte_identical`
      — `Config().ADJUDICATION_STATUS_AUTHORITY_ENABLED is False`, and
      every existing authority test in this file still passes unmodified
      (proving the new gate changes nothing when False). done-when: fails
      only on the missing attribute (paste).
- [ ] 18. (S2a, R1) Add `ADJUDICATION_STATUS_AUTHORITY_ENABLED: bool = False`
      to `config.py`. done-when: Step 17's attribute-existence half
      passes.
- [ ] 19. (S2a, R1) [COMMIT] Wire the master gate: in `authority.py`'s
      resolution functions (`argumentative_authority_mode`,
      `trial_authority_for`, and the `AuthoritySurface`-keyed lookups),
      when `config.ADJUDICATION_STATUS_AUTHORITY_ENABLED` is False, force
      the resolved mode to `observe_only`/`TrialAuthority.OBSERVE_ONLY`
      regardless of the underlying knob's configured value (`ARGUMENTATIVE_AUTHORITY`
      etc. remain settable, but inert unless this master flag is True) —
      this is the concrete reading that makes R1 an actual opt-in rather
      than a no-op, since the six knobs are independently settable today.
      done-when: a new test
      `test_text_authority_policy.py::test_master_gate_forces_observe_only_even_when_trial_configured`
      (sets `ARGUMENTATIVE_AUTHORITY="trial_required"` AND
      `ADJUDICATION_STATUS_AUTHORITY_ENABLED=False`, asserts the run still
      only produces scrutiny observations, never a warrant) passes. Diff
      budget check, commit, push.
- [ ] 20. (S2a, R1) Close the two ungated mint sites: add the same master
      check to `imports.py::register_epistemic_import_failure` and
      `rules/experiment.py::relevance_trial`, defaulting closed (i.e.
      when the flag is False, these two paths behave as if authority is
      `observe_only` too, closing the gap SPEC.md's §2(a) measured).
      done-when: two new tests,
      `test_imports.py::test_import_failure_gated_by_adjudication_master_flag`
      and
      `test_experiment.py::test_relevance_trial_gated_by_adjudication_master_flag`,
      both pass.
- [ ] 21. (S2a, C3) `_versioned_source_config_data` pop-line for
      `ADJUDICATION_STATUS_AUTHORITY_ENABLED`, unconditional across schema
      versions. done-when: canonical-hash goldens still pass (same command
      as Step 12).
- [ ] 22. (S2a, C9) Qualification-subject-exclusion test for this field,
      same shape as Step 13.
- [ ] 23. (S2a, R1) Solo-law regression test: with the master flag True
      and a genuinely single-model-family run, `single_family_trial`
      remains reachable (not accidentally gated away by this change).
      done-when:
      `tests/test_text_authority_policy.py::test_single_family_trial_reachable_under_master_gate`
      passes.
- [ ] 24. (S2a) Map update, same commit: `docs/map/CON-authority.md`
      gains a row for `ADJUDICATION_STATUS_AUTHORITY_ENABLED` and a note
      in its "How to add a new authority mode" table that this is now the
      master reachability gate all six existing knobs sit behind.
      done-when: `python tools/docs_verify.py` 0 failed.
- [ ] 25. (S2a) [COMMIT] Subsystem ring:
      `python -m pytest tests/test_text_authority_policy.py tests/test_imports.py tests/test_experiment.py tests/test_run_manifest.py -q`.
      "N passed, 0 failed" (paste). Diff budget, commit, push.

---

## PART D — Judge seats opt-in
(S: SPEC.md §2(b); R2, R6, R10, C3, C7)

- [ ] 26. (S2b, R2) Reader/default test FIRST:
      `tests/test_judge_ensemble_boundary.py::test_judge_seats_disabled_by_default_is_byte_identical`
      — `Config().JUDGE_SEATS_ENABLED is False`, existing judge-dispatch
      tests unmodified. done-when: fails only on missing attribute.
- [ ] 27. (S2b, R2) Add `JUDGE_SEATS_ENABLED: bool = False`,
      `JUDGE_SUMMONS_PER_CYCLE: int = 0`, `JUDGE_SUMMONS_COOLDOWN: int = 4`
      to `config.py`, modeled on `ADVISORY_TRIALS_PER_CYCLE`/`DISC_COOLDOWN`'s
      existing shape (`config.py:401,441-442`). done-when: Step 26's
      attribute half passes.
- [ ] 28. (S2b, R2) [COMMIT] Gate every current judge-dispatch site on
      `JUDGE_SEATS_ENABLED`: `scheduler.py:1116-1117` (rubric-trial
      `has_role("judge")` check), `scheduler.py:2167-2168` (audit-step),
      the property-step fail-closed check, AND the non-text-workload
      forced-`TrialAuthority.STATUS` path in `authority.py:101-102` (the
      one gap SPEC.md's measurement found with NO existing suppression) —
      when False, none of these dispatch regardless of workload_profile or
      rubric criteria present. done-when: a new test
      `tests/test_scheduler.py::test_judge_dispatch_gated_off_even_for_nontext_workload_with_rubric_criteria`
      passes. Diff budget check, commit, push.
- [ ] 29. (S2b, R6/R10) Throttle wiring: `JUDGE_SUMMONS_PER_CYCLE`/
      `JUDGE_SUMMONS_COOLDOWN` are STATIC caps only (Amendment 5's
      benching — no signal-adaptive behavior in this tranche). Wire them
      identically to how `ADVISORY_TRIALS_PER_CYCLE`/`DISC_COOLDOWN`
      already cap their respective counters, applied at whichever judge
      dispatch site(s) Step 28 gated. done-when:
      `tests/test_budget.py::test_judge_summons_per_cycle_cap` and
      `::test_judge_summons_cooldown` both pass.
- [ ] 30. (S2b, R2) Reconciliation test with the cross-family gate (solo
      law): `JUDGE_SEATS_ENABLED=True` on a genuinely single-model-family
      run still refuses typed (`SECOND_JUDGE_FAMILY_REQUIRED`) at the same
      layer it does today — this opt-in does not bypass that guarantee.
      done-when:
      `tests/test_run_manifest.py::test_judge_seats_opt_in_does_not_bypass_cross_family_requirement`
      passes (extends the existing
      `test_cross_family_rubric_policy_fails_preflight_for_one_family`
      pattern).
- [ ] 31. (S2b, R2) `_versioned_source_config_data` pop-lines for all
      three new fields, unconditional. Qualification-subject-exclusion
      test for all three (same shape as Step 13, one assertion per
      field).
- [ ] 32. (S2b) CLI/operator-facing surface: the flag's help text (or
      setup-time confirmation prompt) surfaces the judge-audit evidence
      summary named in SPEC.md §2(b) (11.9% sensitivity under strict
      default, 47.5-60% false-conviction under loosened voting,
      self-preference/verbosity bias unmeasured) — a static string
      constant, not new research. done-when:
      `tests/test_cli.py::test_judge_seats_flag_surfaces_evidence_warning`
      passes.
- [ ] 33. (S2b) Map update, same commit: `docs/map/CON-seats.md` gains a
      row noting `JUDGE_SEATS_ENABLED` as the master judge-dispatch gate,
      distinct from (and upstream of) `require_cross_family_judges`'s
      diversity guarantee.
- [ ] 34. (S2b) [COMMIT] Subsystem ring:
      `python -m pytest tests/test_judge_ensemble_boundary.py tests/test_budget.py tests/test_scheduler.py tests/test_run_manifest.py tests/test_cli.py -q`.
      "N passed, 0 failed" (paste). Diff budget, commit, push.

---

## PART E — Schools opt-in
(S: SPEC.md §2(d); R5, C6)

- [ ] 35. (S2d, R5) Reader/default test FIRST:
      `tests/test_run_manifest.py::test_school_seats_disabled_by_default_is_byte_identical`
      — `Config().SCHOOL_SEATS_ENABLED is False`, `SchoolExecutionPolicyV1.mode`
      stays `conditioning_only`-only-constructible (no `route_bound`
      reachable) when False.
- [ ] 36. (S2d, R5) Add `SCHOOL_SEATS_ENABLED: bool = False` to
      `config.py`.
- [ ] 37. (S2d, R5) [COMMIT] Add the `--seat school-N=<profile>` CLI
      surface (parallel in shape to `seat_bindings.py`'s existing `--seat
      GROUP=PATH`, per §5.5 Road B — reusing the manifest's own
      school-keyed shape, NOT extending `seat_bindings.py::GROUP_ROLES`),
      gated on `SCHOOL_SEATS_ENABLED`: when set, populates
      `SchoolExecutionPolicyV1(mode="route_bound", ...)` (conjecture side)
      and/or per-school distinct `endpoint_id`s in
      `CriticismPolicyV1.bindings` (criticism side) at manifest-compile
      time. done-when:
      `tests/test_run_manifest.py::test_seat_school_flag_produces_route_bound_policy`
      passes. Diff budget check, commit, push.
- [ ] 38. (S2d, C6) Consequence-A regression test (must stay inert, per
      the map's own pinned invariant): binding two schools to two distinct
      models does not change `foreign_schools` computation in
      `plan_foreign_criticism`. done-when:
      `tests/test_foreign_school_criticism_scheduler_c3.py::test_distinct_school_models_do_not_change_foreign_coverage_count`
      passes.
- [ ] 39. (S2d, C6) Consequence-B disclosure (Road A, approved — no code
      change to `firewall.py`): a regression test PROVING the documented
      side effect is real and unchanged in shape (so a future reader knows
      it is expected, not a regression): enabling school seats with
      distinct models flips `is_single_model_run` to False for the whole
      run and can newly require `require_cross_family_judges()` on an
      untouched `judge` role. done-when:
      `tests/test_judge_ensemble_boundary.py::test_school_seat_diversity_flips_single_model_predicate_for_judge_role`
      passes (this test's existence and passing IS the "disclosure" —
      it's the executable proof backing the operator-facing help text
      Step 40 writes).
- [ ] 40. (S2d) CLI operator-facing surface: `--seat school-N=<profile>`'s
      help text names Consequence B explicitly (a school-seat opt-in that
      adds route diversity anywhere in the run's role table can revoke the
      argument trial's cross-school substitute for the judge role) —
      static string, not new research. done-when:
      `tests/test_cli.py::test_school_seat_flag_surfaces_single_model_warning`
      passes.
- [ ] 41. (S2d, C3) `_versioned_source_config_data` pop-line for
      `SCHOOL_SEATS_ENABLED`. Qualification-subject-exclusion test (same
      shape as Step 13).
- [ ] 42. (S2d) Solo-law/qualification-cost disclosure: help text also
      names the qualification-battery cache-miss cost
      (`docs/map/SEAM-manifest-x-schools.md:137-144`) of moving a school
      to a different seat. done-when: same test file as Step 40 gains an
      assertion for this string.
- [ ] 43. (S2d) Map update, same commit: `docs/map/SEAM-manifest-x-schools.md`
      gains a note that `route_bound` mode is no longer dormant-in-every-
      shipped-configuration — it is now reachable via
      `SCHOOL_SEATS_ENABLED`, still defaulting off. Update the seam's own
      "Every `SchoolExecutionPolicyV1` constructed anywhere in `src/` is
      `conditioning_only`" check to account for the new (default-off)
      exception.
- [ ] 44. (S2d) [COMMIT] Subsystem ring:
      `python -m pytest tests/test_run_manifest.py tests/test_foreign_school_criticism_scheduler_c3.py tests/test_judge_ensemble_boundary.py tests/test_cli.py -q`.
      "N passed, 0 failed" (paste). Diff budget, commit, push.

---

## PART F — Static signal-read surface
(S: REQUEST.md R15; SPEC.md DECISION SHEET header note)

Strictly a READ aggregation over already-existing, already-live signals —
no new event/record type, no mid-run consumption (Amendment 5's benching
holds).

- [ ] 45. (R15) Reader test FIRST: a new module
      `src/deepreason/signals_read.py` does not exist yet; write
      `tests/test_signals_read.py::test_signal_snapshot_shape` asserting
      the shape of a new typed `SignalSnapshotV1` (fields: latest
      config-critique verdict via `referee.py::latest_config_critique`,
      per-phase `v6-model-phase-deferred` counts via a new small helper
      reading `verification/report.py`'s existing
      `_deferred_model_phase_findings` output, and the run's `TokenMeter.snapshot()`)
      against a fixture root. done-when: fails only on the missing module
      (paste `ModuleNotFoundError`).
- [ ] 46. (R15) [COMMIT] Implement `signals_read.py::read_signal_snapshot(root)`
      — pure aggregation, read-only, no mid-run wiring, consumable from
      `report`/`audit`/CLI tooling at run boundaries only. done-when:
      Step 45's test passes. Diff budget check, commit, push.
- [ ] 47. (R15) Wire `read_signal_snapshot` into the existing
      `verification/report.py` report output (an additive field, not a
      new report shape) so `deepreason status`/`report` surfaces it.
      done-when: `tests/test_verification_report.py::test_report_includes_signal_snapshot`
      passes.
- [ ] 48. (R15) Register the new marker's signal name in
      `src/deepreason/signals.py` if `read_signal_snapshot` introduces any
      new literal signal string (closing the exact "escapes the signal
      registry" trap `docs/map/SUB-scheduler.md`'s Traps section already
      names for `v6-model-phase-deferred.v1` — do NOT silently repeat that
      trap for a new marker). done-when:
      `python -c "from deepreason.signals import is_known; assert is_known('<new-marker-name>')"`
      exits 0, if a new marker was introduced; if none was (pure
      aggregation of existing markers only), this step's done-criterion is
      "no new literal signal string was introduced" — confirm by grep and
      paste the (empty) result.
- [ ] 49. (R15) Map update, same commit: add a row to
      `docs/map/SUB-scheduler.md` or a new small doc for
      `signals_read.py` (executor's judgment at execution time on whether
      this warrants its own `SUB-*.md` or a row in an existing one — flag
      for the operator if genuinely ambiguous, per dr-ask-the-right-question,
      rather than guessing).
- [ ] 50. (R15) [COMMIT] Subsystem ring:
      `python -m pytest tests/test_signals_read.py tests/test_verification_report.py tests/test_signals.py -q`.
      "N passed, 0 failed" (paste). Diff budget, commit, push.

---

## PART G — Gate and delivery

- [ ] 51. (all) Map check: `python tools/docs_verify.py`. done-when: 0
      failed, and `python tools/docs_verify.py --audit` reports 0
      findings.
- [ ] 52. (all) Frozen-surface diff confirmation: `git diff` against the
      pre-tranche base touches ONLY the surfaces named in the CHECKLIST
      STOP's grant request below (`run_manifest.py`'s
      `_versioned_source_config_data` pop-lines, additive only) — no
      other line in `capabilities/state.py`, `harness.py`'s event
      application, `invariants.py`, or any manifest schema/validator.
      done-when: `git diff --stat $(git merge-base HEAD origin/main) -- src/deepreason/capabilities/state.py src/deepreason/harness.py src/deepreason/invariants.py` is empty, AND
      `git diff $(git merge-base HEAD origin/main) -- src/deepreason/run_manifest.py`
      shows ONLY `.pop(...)` line additions inside
      `_versioned_source_config_data` (paste the diff for visual
      confirmation).
- [ ] 53. (all) Full gate: `python -m pytest tests/ -q -n 4`. done-when:
      output ends "N passed, 0 failed" (paste it; expect ~3100+N given
      the new tests this tranche adds).
- [ ] 54. (all) Wheel smoke instruments (per CLAUDE.md — no gate runs
      these automatically, but this tranche adds new CLI flags/console
      surface, so re-run and re-pin if changed):
      `python scripts/wheel_smoke.py` and
      `python -u scripts/wheel_operational_smoke.py`. done-when: both
      exit 0; if the public surface pin changed (new `--seat school-N`,
      new flags), the pin update is folded into this same step's diff, not
      a separate trailing one.
- [ ] 55. (all) [COMMIT] Root sweep (guard rule from
      `docs/map/INV-frozen-surfaces.md`, since this tranche touches a
      reader-adjacent area — Road E changes what dispatches, not what a
      committed root MEANS, but the instrument is cheap insurance):
      `python tools/root_sweep.py post-tranche-sweep.txt`. done-when: no
      root's `valid` or `att` changed versus the pre-tranche baseline
      (paste the diff, expect byte-identical).
- [ ] 56. (all) [COMMIT] Final push and clean-tree confirmation:
      `git status --porcelain` empty AND branch head matches
      `origin/claude/adjudication-judge-seats-optins-4nb7ov`. done-when:
      both conditions hold (paste `git status --porcelain` — empty — and
      `git rev-parse HEAD origin/claude/adjudication-judge-seats-optins-4nb7ov`
      — identical hashes).

---

# CHECKLIST STOP — frozen-surface grant request (per REQUEST.md Amendment 5/C13)

Per the operator's explicit instruction, every frozen-surface contact
SPEC.md's own forecast already named is presented here as a named, scoped
grant request — not assumed, not silently taken. This checklist authorizes
NOTHING by itself; dr-execute-step may not touch any of the below until the
operator grants it, mirroring the R19 pattern (`experiments/2026-08-07-change-seats-in-record-s5/REQUEST.md:432-440`).

**Requested grant 1 — `run_manifest.py`, `_versioned_source_config_data`
only.** Exactly one class of touch, repeated five times (once per new
`Config` field this tranche adds: `LEGACY_CRITICISM_ENABLED`,
`ADJUDICATION_STATUS_AUTHORITY_ENABLED`, `JUDGE_SEATS_ENABLED`,
`JUDGE_SUMMONS_PER_CYCLE`, `JUDGE_SUMMONS_COOLDOWN`, `SCHOOL_SEATS_ENABLED`
— six fields total): an unconditional `.pop("<FIELD_NAME>", None)` line
inside `_versioned_source_config_data`, for every schema version, per the
`ENGAGED_CRITICISM_AUTHORITY` trap already paid for in this exact file
(`docs/map/INV-frozen-surfaces.md:185-208`). Nothing else in
`run_manifest.py` — no schema field, no validator, no `Literal` widened.
Steps 12, 21, 31 (x3), 41 depend on this grant.

**Everything else this checklist plans is confirmed, by Step 1's design
note and the frozen-surface forecast SPEC.md already carries, to touch
NONE of the five frozen surfaces** (`capabilities/state.py`, `harness.py`
event application, `invariants.py`/replay-validation formats, `run_manifest.py`
SCHEMA/validators beyond the one named pop-line class above, and
`route_fingerprint`) — Road E's new transaction contract reuses existing
generic `workflow/transaction_service.py` machinery with no changes to any
of these; every opt-in is a `Config` field consulted at an existing mint
or dispatch site.

**Any contact this checklist's steps are found to require, during
execution, that is NOT one of the two paragraphs above is a hard STOP per
Amendment 5's own rule — not a judgment call for `dr-execute-step` to
make.**

Commit and push this file, then STOP for operator review. No
`dr-execute-step` invocation runs against this checklist until the
operator has reviewed it and, specifically, granted or amended Requested
grant 1 above.
