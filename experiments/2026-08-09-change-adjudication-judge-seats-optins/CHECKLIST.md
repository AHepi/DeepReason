# Checklist for: adjudication / judge-seats / legacy-criticism / schools opt-ins
State: next=27 blockers=none (Parts A+B complete; Step 28 done early)
Re-read REQUEST.md + SPEC.md before every step. Execute strictly in order.
One step per dr-execute-step invocation.

Map ids (preflight, re-affirmed from SPEC.md's own header plus Road E's
newly-scoped territory): `DR-CON-seats`, `DR-SUB-adjudication`,
`DR-CON-authority`, `DR-CON-schools`, `DR-INV-frozen-surfaces`,
`DR-SEAM-adjudication-x-authority`, `DR-SEAM-manifest-x-schools`,
`DR-SEAM-schools-x-scratch` — plus, for Road E specifically (not named in
SPEC.md's original frozen-surface forecast, added here from a fresh map
read): `DR-SUB-scheduler` (owns `_arg_crit`, `_defer_untransactional_v6_phase`,
`_maybe_config_referee` — the exact precedent Road E extends) and
`DR-SUB-workflow` (owns `nonconjecture_recovery.py::_criticism_contract`,
touched by S13e). The `scheduler x workflow` seam (coupling 16) has no
written `SEAM-*.md` file yet — `docs/map/INDEX.md`'s matrix confirms none
exists; Step 1 read the two subsystems directly since no seam document
exists to read first.

Diff budget: computed ceiling **1,600 lines**, UNCHANGED total (SPEC.md's
own Road E revision explicitly keeps it: "this revision reduces one
component of it; does not need to raise the total"). Component estimate,
revised: Road E ~131 (SPEC.md's "R13 Road E — REVISED" Budget section,
`python3 -c "print(2+1+3+1+20+15+4+30+40+15)"` = 131 — down from the
original ~600-line estimate once M1-M5 measured the actual coupling);
four opt-ins ~180 each = 720; static signal-read surface ~180; map-doc
updates ~100. Sums to ~1,131 against the 1,600 ceiling — real headroom,
not just an unexamined round number. Per REQUEST.md C10 (Amendment 2), an
actual overrun does not stop execution — `tools/diff_budget.py` runs at
every `[COMMIT]` step regardless, and the real cumulative total is
reported at delivery, not pre-judged here.

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
- [x] 3. (R13) **STOP, resolved.** `crit_argumentative_batch`'s
      `active_v6` branch was found to hard-require `critic_school_id`
      (`rules/crit.py:1378-1379,1437-1438`), contradicting Step 1's
      design note. Recorded as a stop, priced as Road A/Road B, returned
      to the orchestrator per dr-execute-step's exit criteria. **Resolved
      by REQUEST.md Amendment 7** ("a clean separation between school and
      criticism... they still need to interact") and SPEC.md's "R13 Road E
      — REVISED" section (items S13a-g), which supersedes both originally
      -priced roads with a smaller, measured third option: loosen the
      guards rather than fork a payload schema. done-when: SPEC.md's
      revision is committed (`git log --oneline -1 -- experiments/2026-08-09-change-adjudication-judge-seats-optins/SPEC.md`
      shows the Amendment-7 revision commit) — satisfied, see commit
      `c8f70720e`. Steps 4-14 below replace the original steps 4-8, which
      are deleted (never executed, per the re-planning rule — no history
      to preserve for unexecuted steps).

- [x] 4. (S13g) Revert Step 2: remove the now-superseded
      `LEGACY_ARG_CRITICISM_CONTRACT_V1` constant and its comment from
      `src/deepreason/rules/crit.py` (M2-M5 showed the clean-separation
      design needs no second payload schema). done-when:
      `grep -q LEGACY_ARG_CRITICISM_CONTRACT_V1 src/deepreason/rules/crit.py`
      exits 1 (not found), and
      `python -c "import ast; ast.parse(open('src/deepreason/rules/crit.py').read())"`

      ```
      $ grep -q LEGACY_ARG_CRITICISM_CONTRACT_V1 src/deepreason/rules/crit.py; echo $?
      1
      $ python -c "import ast; ast.parse(open('src/deepreason/rules/crit.py').read())" && echo "syntax OK"
      syntax OK
      ```
      exits 0.
- [x] 5. (S13a) [COMMIT] Narrow `crit_argumentative_batch`'s top-level
      guard (`rules/crit.py:1378-1379`) from `if active_v6 and
      (endpoint_lease is None or critic_school_id is None): raise
      ValueError("v6 criticism requires one manifest-bound school
      route")` to `if active_v6 and endpoint_lease is None: raise
      ValueError("v6 criticism requires a manifest-bound route")`.
      done-when: `python -m pytest tests/test_foreign_school_criticism_scheduler_c3.py -q`
      passes unmodified (paste "N passed, 0 failed" — proves the
      school-routed path is untouched by this narrowing). Run
      `python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason/rules/crit.py`,
      paste output, commit, push.

      ```
      $ python -m pytest tests/test_foreign_school_criticism_scheduler_c3.py -q
      2 passed in 1.30s
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason/rules/crit.py
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason/rules/crit.py": 2}, "total_insertions": 2, "ceiling": 1600, "verdict": "WITHIN"}
      ```
      (Used the true tranche-base commit `81d08e5f0` directly rather than
      computing `git merge-base HEAD origin/main`, which now resolves to
      `origin/main`'s own tip since this branch merged it mid-tranche —
      that computed value would measure zero pre-tranche diff against the
      wrong reference; the intent, diffing against the tranche's start
      point, is what was run. All later `[COMMIT]` steps' done-when text
      below has been updated to cite `81d08e5f0` directly, for the same
      reason.)
- [x] 6. (S13b) Remove `assert critic_school_id is not None`
      (`rules/crit.py:1438`, inside the `active_v6:` block), keeping
      `assert endpoint_lease is not None`. done-when: same test command as
      Step 5 still passes (paste it again — confirms no regression from
      this second, adjacent change).

      ```
      $ python -m pytest tests/test_foreign_school_criticism_scheduler_c3.py -q
      2 passed in 1.16s
      ```

      **Mid-step discovery, per dr-execute-step's own rule ("never just
      typed in"):** re-reading the neighborhood to find this assert's
      exact line surfaced a THIRD, separate school-required guard that
      SPEC.md's M1-M5 measurements missed —
      `_critic_execution` (`rules/crit.py:106-134`, called by both
      `crit_argumentative` and `crit_argumentative_batch` before either
      reaches the `active_v6` branch):
      ```python
      supplied = (
          endpoint_lease is not None,
          critic_school_id is not None,
          critic_school_context is not None,
      )
      if any(supplied) and not all(supplied):
          raise ValueError(
              "school-routed criticism requires endpoint_lease, critic_school_id, "
              "and critic_school_context"
          )
      ```
      Road E's shape (`endpoint_lease` supplied, `critic_school_id`/
      `critic_school_context` both `None`) is exactly the
      `any(supplied) and not all(supplied)` case this raises on — S13a-g
      as specified does NOT make Road E's dispatch actually work; this
      site was missed. Not typed around silently: a SPEC.md addendum
      (S13h) and a new CHECKLIST step (6a, next) follow immediately,
      before Step 7 resumes.

- [x] 6a. (S13h) Reader test FIRST (rule 1): a new test
      `tests/test_v6_scheduler_model_phase_deferral.py::test_critic_execution_permits_endpoint_only_dispatch`
      asserting `_critic_execution(endpoint_lease=<a real EndpointLease>,
      critic_school_id=None, critic_school_context=None)` returns
      `({"endpoint_index": ..., "endpoint_lease": ..., "school_id": None}, "")`
      without raising, AND that the ORIGINAL partial-supply rejection
      (e.g. `endpoint_lease` + `critic_school_id` given, `critic_school_context`
      omitted) still raises `ValueError` with the original message.
      done-when: the test currently FAILS (red — the branch doesn't exist
      yet) — paste the failure output.

      ```
      $ python -m pytest tests/test_v6_scheduler_model_phase_deferral.py::test_critic_execution_permits_endpoint_only_dispatch -q
      ...
      >           raise ValueError(
                      "school-routed criticism requires endpoint_lease, critic_school_id, "
                      "and critic_school_context"
                  )
      E           ValueError: school-routed criticism requires endpoint_lease, critic_school_id, and critic_school_context
      src/deepreason/rules/crit.py:125: ValueError
      1 failed in 0.46s
      ```
- [x] 6b. (S13h) [COMMIT] Implement the branch: in
      `_critic_execution` (`rules/crit.py:106-134`), add one early-return
      before the existing `supplied`/all-or-nothing check: when
      `endpoint_lease is not None and critic_school_id is None and
      critic_school_context is None`, validate
      `endpoint_lease.role == "argumentative_critic"` and return
      `({"endpoint_index": endpoint_lease.seat, "endpoint_lease":
      endpoint_lease, "school_id": None}, "")` — every other combination
      falls through to the existing, unmodified logic. done-when: Step
      6a's test now passes, AND
      `python -m pytest tests/test_foreign_school_criticism_scheduler_c3.py -q`
      still passes (paste both, "N passed, 0 failed" for each). Run
      `python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason/rules/crit.py`,
      paste output, commit, push.

      ```
      $ python -m pytest tests/test_v6_scheduler_model_phase_deferral.py::test_critic_execution_permits_endpoint_only_dispatch tests/test_foreign_school_criticism_scheduler_c3.py -q
      3 passed in 1.19s
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason/rules/crit.py
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason/rules/crit.py": 16}, "total_insertions": 16, "ceiling": 1600, "verdict": "WITHIN"}
      ```

- [x] 7. (S13c) [COMMIT] Widen `_v6_transactional_batch_call`
      (`rules/crit.py:255-262`): change `critic_school_id: str` to
      `critic_school_id: str | None = None`; remove the `if not
      critic_school_id: raise ValueError("transactional criticism
      requires a critic school")` guard at `rules/crit.py:299-300` (keep
      the `endpoint_lease.role != "argumentative_critic"` guard
      immediately above it). done-when:
      `python -m pytest tests/test_v6_live_repair_transactions.py -q`
      passes unmodified (paste "N passed, 0 failed"). Diff budget check
      (same command shape as Step 5, `--paths src/deepreason/rules/crit.py`),
      paste, commit, push.

      ```
      $ python -m pytest tests/test_v6_live_repair_transactions.py -q
      10 passed in 14.40s
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason/rules/crit.py
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason/rules/crit.py": 17}, "total_insertions": 17, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 8. (S13d) Widen `_v6_transactional_atomic_critic_call`
      (`rules/crit.py:522-528`): change `critic_school_id: str` to
      `critic_school_id: str | None = None` (type hint only — M3 found no
      guard to remove here). done-when: same test command as Step 7 still
      passes.

      ```
      $ python -m pytest tests/test_v6_live_repair_transactions.py -q
      10 passed in 13.32s
      ```
- [x] 9. (S13i-1) Reader test FIRST (rule 1): a new test asserting
      `LLMAdapter(...).bound_v6_manifest() is None` before binding, and
      equals the exact manifest object after
      `adapter.bind_v6_authority(harness, manifest)`. done-when: the test
      currently FAILS (red — the accessor doesn't exist yet) — paste the
      failure (`AttributeError`).

      ```
      $ python -m pytest tests/test_v6_scheduler_model_phase_deferral.py::test_llm_adapter_exposes_bound_v6_manifest -q
      AttributeError: 'LLMAdapter' object has no attribute 'bound_v6_manifest'
      1 failed in 0.63s
      ```
- [x] 10. (S13i-1) [COMMIT] Add `LLMAdapter.bound_v6_manifest(self)` to
      `llm/adapter.py`, adjacent to `bind_v6_authority`: `return
      self._v6_authority_manifest` (read-only, no new stored state).
      done-when: Step 9's test passes. Diff budget check
      (`--paths src/deepreason/llm/adapter.py`), paste, commit, push.

      ```
      $ python -m pytest tests/test_v6_scheduler_model_phase_deferral.py::test_llm_adapter_exposes_bound_v6_manifest -q
      1 passed in 0.75s
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason/llm/adapter.py
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason/llm/adapter.py": 5}, "total_insertions": 5, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 11. (S13i-2) [COMMIT] Redefine `policy_call` in BOTH
      `crit_argumentative` and `crit_argumentative_batch`
      (`rules/crit.py`, the two `policy_call = (bool(call_kwargs) or
      argumentative_authority is not None or coverage_observer is not
      None)` sites) to `policy_call = (critic_school_id is not None or
      argumentative_authority is not None or coverage_observer is not
      None)`. done-when:
      `python -m pytest tests/test_foreign_school_criticism_scheduler_c3.py tests/test_prose_refutation_boundaries.py -q`
      passes unmodified (paste "N passed, 0 failed" — M9's proof made
      concrete). Diff budget check, commit, push.

      ```
      $ python -m pytest tests/test_foreign_school_criticism_scheduler_c3.py tests/test_prose_refutation_boundaries.py -q
      47 passed in 4.73s
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason/rules/crit.py
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason/rules/crit.py": 24}, "total_insertions": 24, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 12. (S13i-3) Reader test FIRST (rule 1), the corrected version of
      the original Step-3 test: a new test in
      `tests/test_v6_scheduler_model_phase_deferral.py` named
      `test_legacy_argumentative_criticism_dispatches_under_v6`, asserting
      that given a manifest with `criticism_policy=None` and
      `schema_version=6`, and at least one eligible admitted-and-accepted
      target, `Scheduler._arg_crit` dispatches a live
      `crit_argumentative_batch` call INSTEAD of recording a
      `"v6-model-phase-deferred.v1","argumentative-criticism"` marker —
      with `Scheduler._arg_crit`'s call to `crit_argumentative_batch`
      unmodified (`harness, batch, self.adapter, config`, zero keywords).
      done-when: the test currently FAILS (red) — paste the failure.

      ```
      $ python -m pytest tests/test_v6_scheduler_model_phase_deferral.py::test_legacy_argumentative_criticism_dispatches_under_v6 -q
      AssertionError: assert [] == [((<...Harness...>, ['A'], <..._Adapter...>, namespace(ARG_CRIT_PER_CYCLE=None, RECRIT_STANDING=False, CRIT_BATCH_K=None)), {})]
      1 failed in 0.16s
      ```
- [x] 13. (S13i-3) [COMMIT] Implement self-detection in
      `crit_argumentative_batch`: when `run_manifest`/`endpoint_lease`/
      `critic_school_id` are all their defaults (the scheduler's existing
      call shape), check `adapter.bound_v6_manifest()`; if non-None,
      internally set `run_manifest = adapter.bound_v6_manifest()` and
      `endpoint_lease = select_lease(adapter.leases,
      "argumentative_critic", 0)` (the same fallback `run_config_referee`
      already uses, `referee.py:507-508`) before the existing `active_v6`
      computation; `critic_school_id` stays `None`. Also thread
      `dispatch_authority = authority if critic_school_id is None else
      None` through the `transactional_call` closure into
      `_v6_transactional_batch_call`'s new keyword-only parameter,
      written into `payload["dispatch_authority"]`. If
      `adapter.bound_v6_manifest()` is None, behavior is BYTE-IDENTICAL to
      today. done-when: Step 12's test passes; paste
      `python -m pytest tests/test_v6_scheduler_model_phase_deferral.py::test_legacy_argumentative_criticism_dispatches_under_v6 -q`
      output ending "1 passed", AND
      `python -c "import ast, inspect, textwrap; from deepreason.scheduler.scheduler import Scheduler as S; t = ast.parse(textwrap.dedent(inspect.getsource(S._arg_crit))); calls = [n for n in ast.walk(t) if isinstance(n, ast.Call) and getattr(n.func, 'id', '') == 'crit_argumentative_batch']; assert len(calls) == 1 and not calls[0].keywords; print('OK')"`
      prints OK — this IS `SEAM-scheduler-x-rules.md`'s own checked
      invariant, re-run directly. Diff budget check
      (`--paths src/deepreason/rules/crit.py`), paste, commit, push.

      **Mid-step discovery, checked before writing (not silently
      patched):** `expected_strong_payload`'s incomplete-decomposition
      matching (`crit.py:1466-1474`) is a strict dict `==` against the
      durable `preparation.task_payload_value`; adding
      `"dispatch_authority"` to both the actual payload and this expected
      dict is safe for any transition dispatched by the SAME (new) code
      that later resumes it, but would silently stop recognizing an
      already-durable, not-yet-completed decomposition transition minted
      by OLD (pre-this-step) code as "incomplete" — a real
      resumability/replay-adjacent risk if any committed run root has one.
      Measured directly:
      `grep -rl "critic.atomic-target.v1\|route_seat_contract_decomposition\|V6_CONTRACT_DECOMPOSITION" experiments/*/**/log.jsonl`
      → 0 hits across all 86 `batch-critic.v2`-using committed run roots —
      the atomic-decomposition path (only reachable via a
      `SchemaRepairError` exhaustion during batch criticism) has never
      been exercised by any committed root, so no existing root is at
      risk. Safe to proceed as specced; no CHECKLIST STOP needed. (If this
      ever needs re-verifying against a later corpus of committed roots,
      re-run the same grep.)

      **Step-12/13 done-when correction (found here, not silently
      typed in):** the pasted test still FAILS at this step — the
      scheduler's `_arg_crit` still defers under v6 (its own branch is
      deleted only at Step 13a), so `crit_argumentative_batch` is never
      reached from the scheduler yet. Step 13's own proof is therefore:
      syntax OK, the AST keyword-check (below) passing, and the closely
      coupled `rules/crit.py` test files passing unmodified (proving the
      new parameter/payload field didn't regress existing dispatch). The
      "1 passed" for Step 12's test is deferred to Step 13a's own
      done-when, which already runs the full file.

      ```
      $ python -c "import ast; ast.parse(open('src/deepreason/rules/crit.py').read())"
      # (no output = OK)
      $ python -m pytest tests/test_v6_live_repair_transactions.py tests/test_foreign_school_criticism_scheduler_c3.py tests/test_prose_refutation_boundaries.py -q
      57 passed
      $ python -m pytest tests/test_scheduler.py tests/test_v6_scheduler_model_phase_deferral.py tests/test_config_referee.py tests/test_v6_nonconjecture_recovery.py -q
      1 failed, 51 passed  # only test_legacy_argumentative_criticism_dispatches_under_v6, expected until Step 13a
      $ python -c "import ast, inspect, textwrap; from deepreason.scheduler.scheduler import Scheduler as S; t = ast.parse(textwrap.dedent(inspect.getsource(S._arg_crit))); calls = [n for n in ast.walk(t) if isinstance(n, ast.Call) and getattr(n.func, 'id', '') == 'crit_argumentative_batch']; assert len(calls) == 1 and not calls[0].keywords; print('OK')"
      OK
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason/rules/crit.py
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason/rules/crit.py": 38}, "total_insertions": 38, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 13a. (S13i-4) [COMMIT] Simplify `scheduler.py::_arg_crit`'s plain
      branch: DELETE the `if self.run_manifest is not None and
      self.run_manifest.schema_version == 6: ...
      _defer_untransactional_v6_phase(...) ... continue` block entirely
      — Step 13 makes `crit_argumentative_batch` self-sufficient under
      v6, so this defer is no longer reachable/needed for this phase; the
      existing `crit_argumentative_batch(harness, batch, self.adapter,
      config)` call becomes unconditional, matching every non-v6 schema
      version already. done-when:
      `python -m pytest tests/test_v6_scheduler_model_phase_deferral.py -q`
      passes in full (paste "N passed, 0 failed" — proves the
      `hv-floor`/`hv-spot-check`/`rubric-trial` deferrals are untouched).
      Diff budget check, paste (expect a NET NEGATIVE line count for this
      step), commit, push.

      **Obsolete test found and removed (not silently patched):** deleting
      the defer block breaks `test_v6_local_argumentative_criticism_
      becomes_completion_debt` — its entire premise (v6 + no
      `criticism_policy` ⇒ deferral debt) is the exact defect R19/S13i
      fixes; SPEC.md's S13i-4 explicitly predicted "this defer is no
      longer reachable/needed for this phase," satisfying CLAUDE.md's "may
      be minimally updated only when the fix's design doc predicted it."
      Its replacement, `test_legacy_argumentative_criticism_dispatches_
      under_v6` (Step 12), already covers the corrected behavior for the
      identical scenario, so the obsolete test is DELETED rather than
      inverted into a duplicate.

      **Second, larger mid-step discovery — `python tools/docs_verify.py`
      run proactively before committing (not skipped):** three documents
      broke, one of them a genuine architectural conflict, not mere doc
      staleness:
      1. `SEAM-llm-x-rules.md:49,90` — Step 13's self-detection imported
         `select_lease` directly into `rules/crit.py` to resolve its own
         default route. This SEAM document has its own checked, deliberate
         boundary: `"! grep -rqE \"select_lease|resolve_school_role_lease\"
         ... src/deepreason/rules"` and a banned-symbol AST check — "The
         lease travels one way. The scheduler resolves it, a rule carries
         it, and the adapter re-verifies it." This is a REAL boundary
         violation, the same class of conflict as the original
         SEAM-scheduler-x-rules.md fork (R21), just on the `llm/`x`rules`
         seam instead of `scheduler`x`rules`. Resolved the same way:
         pushed the mechanism one layer down into `llm/adapter.py` (not a
         frozen surface, already touched this tranche) instead of
         `rules/crit.py`. Added `LLMAdapter.bound_v6_default_lease(role,
         seat=0)`, a thin wrapper around the SAME `select_lease` call,
         living entirely on the `llm/` side of the boundary; `crit.py`
         now calls `adapter.bound_v6_default_lease(...)` instead of
         importing `select_lease` itself. Updated `SEAM-llm-x-rules.md`'s
         "Where it is expressed" prose (not a Traps entry, so rewritten
         directly, not marked FIXED) to describe the adapter now also
         resolving its own default lease for the self-dispatch case.
         `rules/crit.py` still imports zero route-resolution primitives;
         both of this seam's checks pass unmodified in shape.
      2. `SEAM-rules-x-workflow.md:186` and `SEAM-scheduler-x-rules.md`/
         `SEAM-scheduler-x-workflow.md` (already fixed inline while
         writing Step 13a's own diff, see below) — stale "argumentative
         criticism becomes typed completion debt" claims and a phase-set
         check asserting `"argumentative-criticism"` still appears among
         `_defer_untransactional_v6_phase`'s call sites. All rewritten to
         state the corrected behavior, each as a Traps "FIXED 2026-08-10"
         rewrite (`docs/map/SCHEMA.md` rule 7: never delete a Traps entry,
         rewrite it to say when it was fixed) where the stale claim lived
         in a Traps section, or a direct prose rewrite where it did not.
      3. `CON-schools.md:167` — a THIRD, PRE-EXISTING staleness from Step
         6b's S13h (missed at the time — `docs_verify.py` was not run
         after that step; caught here instead of compounding further).
         `_critic_execution`'s all-or-nothing pairing check no longer
         covers the school-free endpoint-only case S13h added; updated
         the prose and check to state the corrected three-combination
         shape (no envelope / endpoint-only / paired school-routed).
      `python tools/docs_verify.py` now reports 0 failed (was 4 failed
      before this discovery; re-verified fresh after each fix). Lesson
      recorded for the rest of this CHECKLIST: run `docs_verify.py` at
      every step touching `docs/map`-owned source files, not only at the
      dedicated map-update steps.

      ```
      $ python -m pytest tests/test_v6_scheduler_model_phase_deferral.py -q
      10 passed in 0.83s
      $ python -m pytest tests/test_scheduler.py tests/test_v6_scheduler_model_phase_deferral.py tests/test_config_referee.py tests/test_foreign_school_criticism_scheduler_c3.py tests/test_v6_live_repair_transactions.py tests/test_v6_nonconjecture_recovery.py tests/test_prose_refutation_boundaries.py tests/test_model_firewall.py tests/test_criticism_school_execution_c3.py -q
      133 passed in 78.62s
      $ python tools/docs_verify.py
      docs_verify [full]: 53 documents, 851 checks, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason/scheduler/scheduler.py src/deepreason/rules/crit.py src/deepreason/llm/adapter.py
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason/scheduler/scheduler.py": 0, "src/deepreason/rules/crit.py": 39, "src/deepreason/llm/adapter.py": 13}, "total_insertions": 52, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 14a. (S13e) Reader test FIRST (rule 1): three new tests —
      `tests/test_v6_nonconjecture_recovery.py::test_criticism_contract_recovers_without_a_school`
      (payload's `dispatch_authority` is `"observe_only"` — resolves and
      admits), `::test_criticism_contract_refuses_recovery_without_a_school_when_dispatch_authority_is_not_observe_only`
      (payload's `dispatch_authority` is e.g. `"trial_required"` —
      refuses typed, mirroring the school-routed branch's own `'critic
      authority is not recoverable'` shape), and
      `::test_v6_transactional_batch_call_freezes_dispatch_authority_for_school_free_calls`
      (proves Step 13's dispatch actually writes the resolved authority
      into the payload — not just that recovery reads it correctly).
      done-when: all three currently FAIL (red) — paste all three
      failures.

      **Fixture gap found writing these tests (not silently patched):**
      the shared `_provider_prefix` helper unconditionally built a
      `SchoolRouteReceiptV1(school_id=payload["critic_school_id"], ...)`
      for every `WorkflowTaskKind.CRITICISM` call — `SchoolRouteReceiptV1.
      school_id` is a required, pattern-constrained `str`, so this crashes
      for `critic_school_id=None`. Made the receipt conditional on
      `payload.get("critic_school_id") is not None` (backward compatible:
      every existing school-routed caller is unaffected, verified by the
      full subsystem ring below). Added a parallel `_criticism_prefix_
      school_free` fixture (no `CriticismAssignmentV1` obligation — that
      record type's `critic_school_id` field is ALSO a required pattern
      `str`, confirming the obligation concept is inherently
      school-specific and does not apply to legacy dispatch at all; see
      Step 14b's own discovery about `_criticism_contract`'s
      assignment-cardinality check for the consequence of this).

      **Third test result note:** it PASSES already, not red — Step 13
      already implemented `_v6_transactional_batch_call`'s write side
      (the `dispatch_authority` parameter and `payload["dispatch_authority"]`
      line). This is expected, not a gap: the test still earns its place
      as the WRITE-side proof the other two (READ-side) tests don't cover.

      ```
      $ python -m pytest tests/test_v6_nonconjecture_recovery.py::test_criticism_contract_recovers_without_a_school tests/test_v6_nonconjecture_recovery.py::test_criticism_contract_refuses_recovery_without_a_school_when_dispatch_authority_is_not_observe_only tests/test_v6_nonconjecture_recovery.py::test_v6_transactional_batch_call_freezes_dispatch_authority_for_school_free_calls -q
      FAILED test_criticism_contract_recovers_without_a_school - NonConjectureRecoveryAuthorityError: critic school has no manifest binding
      FAILED test_criticism_contract_refuses_recovery_without_a_school_when_dispatch_authority_is_not_observe_only - AssertionError: Regex pattern did not match. Expected: 'critic authority is not recoverable'. Actual: 'critic school has no manifest binding'
      2 failed, 1 passed in 6.06s
      ```
- [x] 14b. (S13e) [COMMIT] Implement the recovery branch: in
      `nonconjecture_recovery.py::_criticism_contract` (`:643-718`), when
      `payload.get("critic_school_id") is None`, skip the
      `criticism_policy is not None`/binding-lookup requirement
      (`:649-653`), verify `preparation.route_lease` names a route
      present in `manifest.roles.get("argumentative_critic", ())` (any
      seat), and read authority from `payload.get("dispatch_authority")`
      (frozen, NOT live/reconstructed `Config` — see SPEC.md's corrected
      design), refusing typed unless it equals `"observe_only"` — the
      `critic_school_id is not None` branch stays byte-identical.
      done-when: Step 14a's three tests now pass, AND
      `python -m pytest tests/test_v6_nonconjecture_recovery.py -q`
      passes in full (paste "N passed, 0 failed"). Diff budget check
      (`--paths src/deepreason/workflow/nonconjecture_recovery.py`),
      paste, commit, push.

      **Mid-step discovery #1, checked before writing (not silently
      patched):** the ORIGINAL assignment-cardinality check
      (`_authority(len(assignments) == len(targets), "critic assignment
      cardinality differs")` and the loop below it) is itself
      school-obligation-specific machinery — `CriticismAssignmentV1.
      critic_school_id` is ALSO a required, pattern-constrained `str`
      (confirmed reading the model), so the whole per-target-assignment
      concept cannot apply to school-free criticism at all, and the
      self-sufficient dispatch (S13i) always passes an empty
      `transaction_assignment_refs`. Left unguarded, this check would
      ALWAYS raise "critic assignment cardinality differs" for every
      school-free recovery (0 assignments vs N targets), which the
      original SPEC.md/CHECKLIST wording for this step did not anticipate
      — found while writing Step 14a's fixtures, not by inspection. Fixed
      by gating the whole block on `school_id is not None`, with an
      explicit new check on the school-free side
      (`_authority(not assignments, "school-free criticism must carry no
      assignment obligation")`) and its own early return, rather than
      leaving the gap unchecked.

      **Mid-step discovery #2 (a real, pre-existing latent bug this
      tranche's new code path exposed, not introduced by it):**
      `_criticism_contract`'s caller applies the recovered criticism
      effect via two call sites that unconditionally wrapped
      `critic_school_id=str(payload["critic_school_id"])`. For every
      school-routed call before this tranche, `payload["critic_school_id"]`
      was always a real string, so `str(x) == x` was a silent no-op;
      for the new school-free case it is `None`, and `str(None) ==
      "None"` — the critic artifact's `Provenance.school` (itself typed
      `str | None`, correctly) ended up literally the STRING `"None"`
      instead of Python `None`. Caught by Step 14a's own first test
      asserting `critics[0].provenance.school is None`. Both call sites
      (`:338`, `:355`) had the redundant `str(...)` removed —
      `_crit_argumentative_batch_result`/`_apply_counterexample_retry_result`
      already declare `critic_school_id: str | None`, so this is a pure
      bug fix, not a signature change.

      **`docs_verify.py` run proactively before committing (habit from
      Step 13a's lesson):** found one collateral break —
      `SEAM-scheduler-x-rules.md:39` and `SEAM-scheduler-x-workflow.md:39`
      count files that mention both `deepreason.rules` and the literal
      word "scheduler"; discovery #1's explanatory comment in
      `nonconjecture_recovery.py` used the word "scheduler" in prose,
      pushing that file's count over by one (it already imports from
      `deepreason.rules.crit`, unrelated to this step). Reworded the
      comment to avoid the literal word; both counts restored to their
      checked values. `docs_verify.py`: 0 failed after the reword (was 2
      failed).

      ```
      $ python -m pytest tests/test_v6_nonconjecture_recovery.py -q
      24 passed in 48.40s
      $ python -m pytest tests/test_scheduler.py tests/test_v6_scheduler_model_phase_deferral.py tests/test_config_referee.py tests/test_foreign_school_criticism_scheduler_c3.py tests/test_v6_live_repair_transactions.py tests/test_v6_nonconjecture_recovery.py tests/test_prose_refutation_boundaries.py tests/test_model_firewall.py tests/test_criticism_school_execution_c3.py -q
      136 passed in 81.18s
      $ python tools/docs_verify.py
      docs_verify [full]: 53 documents, 851 checks, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason/workflow/nonconjecture_recovery.py tests/test_v6_nonconjecture_recovery.py
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason/workflow/nonconjecture_recovery.py": 44, "tests/test_v6_nonconjecture_recovery.py": 170}, "total_insertions": 214, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 14. (R13) Map update, same commit as the behavior (rule 4c): edit
      `docs/map/SUB-scheduler.md`'s row "A legacy model phase v6 cannot
      yet dispatch | `_defer_untransactional_v6_phase` at the phase's call
      site" to note the `"argumentative-criticism"` phase is now an
      EXCEPTION — it dispatches through the same
      `crit_argumentative_batch`/`"criticism.semantic-task.v1"` path the
      school-routed case uses, with `critic_school_id=None`, rather than
      deferring. Add a short note to `docs/map/SUB-workflow.md` (or
      `docs/map/CON-criticism-source.md`, whichever the map's own
      `Owns:` line assigns `nonconjecture_recovery.py::_criticism_contract`
      to) documenting the new school-optional recovery branch. Add a
      `Traps` entry naming this tranche's run id, per the map's "every fix
      earns a Traps entry" rule. done-when:
      `python tools/docs_verify.py` reports 0 failed.

      Note: this step's own R13/S13a-g map work was already substantially
      done as part of Step 13a's mid-step map-consistency pass (that step
      updated `SEAM-scheduler-x-workflow.md`, `SEAM-scheduler-x-rules.md`,
      `CON-schools.md`, `SEAM-rules-x-workflow.md`, `SEAM-llm-x-rules.md`
      for staleness `docs_verify.py` surfaced directly). This step covers
      the two items that pass specifically named: `SUB-scheduler.md`'s
      table row (this tranche's `Owns:` search confirmed `SUB-workflow.md`
      is the correct target for the recovery-branch note, not
      `CON-criticism-source.md`, which does not exist) and the dedicated
      `_criticism_contract` Traps entry in `SUB-workflow.md`'s Traps
      section (distinct from the S13i Traps entries already added
      elsewhere — this one is specifically about the recovery-side
      school-optional shape, S13e).

      ```
      $ python -c "import inspect; from deepreason.workflow.nonconjecture_recovery import _criticism_contract as C; s = inspect.getsource(C); assert 'if school_id is None:' in s and 'dispatch_authority' in s and 'manifest does not authorize criticism' in s" && python -m pytest tests/test_v6_nonconjecture_recovery.py::test_criticism_contract_recovers_without_a_school tests/test_v6_nonconjecture_recovery.py::test_criticism_contract_refuses_recovery_without_a_school_when_dispatch_authority_is_not_observe_only -q
      2 passed in 4.04s
      $ python tools/docs_verify.py
      docs_verify [full]: 53 documents, 852 checks, 4 workers
      docs_verify: 0 failed
      ```
- [x] 15. (R13) [COMMIT] Subsystem test ring:
      `python -m pytest tests/test_scheduler.py tests/test_v6_scheduler_model_phase_deferral.py tests/test_config_referee.py tests/test_foreign_school_criticism_scheduler_c3.py tests/test_v6_live_repair_transactions.py tests/test_v6_nonconjecture_recovery.py -q`.
      done-when: output ends "N passed, 0 failed" (paste it). Run
      `python tools/diff_budget.py 81d08e5f0 --ceiling 1600`,
      paste output, commit with message citing R13/S13a-g, push with
      retry.

      **Unscoped diff budget is EXCEEDED, expected and pre-authorized
      (Amendment 2: "for any budget-overrun stop in this tranche, the
      answer is 'continue, report the final total at delivery'").**
      Broken down: `src/deepreason` + `tests` = 358 lines (within),
      `docs/map` = 75 lines (within), this tranche's own
      `experiments/2026-08-09-.../` paperwork (REQUEST.md/SPEC.md/
      CHECKLIST.md) = 3455 lines — the unscoped total (3959) is
      dominated by the tranche's own ledger, not code. Road E's own
      forecast (SPEC.md, S13a-i budget notes) was ~186 lines of source;
      actual source contribution (96 in `src/deepreason` alone) is
      UNDER that forecast. Continuing per Amendment 2; final total
      reported at delivery.

      ```
      $ python -m pytest tests/test_scheduler.py tests/test_v6_scheduler_model_phase_deferral.py tests/test_config_referee.py tests/test_foreign_school_criticism_scheduler_c3.py tests/test_v6_live_repair_transactions.py tests/test_v6_nonconjecture_recovery.py -q
      66 passed in 77.06s
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"total": 3959}, "total_insertions": 3959, "ceiling": 1600, "verdict": "EXCEEDED"}
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason tests
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason": 96, "tests": 262}, "total_insertions": 358, "ceiling": 1600, "verdict": "WITHIN"}
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"docs/map": 75}, "total_insertions": 75, "ceiling": 1600, "verdict": "WITHIN"}
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths experiments/2026-08-09-change-adjudication-judge-seats-optins
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"experiments/2026-08-09-change-adjudication-judge-seats-optins": 3455}, "total_insertions": 3455, "ceiling": 1600, "verdict": "EXCEEDED"}
      ```

---

## PART B — Legacy-criticism-paths opt-in
(S: SPEC.md §2(c) as revised by R13/Road E; R3, C3, C8)

This is the operator-facing switch that makes ordinary (`setup`/`prepare`)
runs able to reach Road E's now-working circuit, instead of only the
low-level `deepreason compile` path reaching it.

- [x] 16. (S2c, R3) Reader/default test FIRST: a new test
      `tests/test_preparation.py::test_legacy_criticism_disabled_by_default_is_byte_identical`
      asserting `Config().LEGACY_CRITICISM_ENABLED is False` and that
      `build_preparation_manifest(...)`'s output `manifest.criticism_policy`
      is UNCHANGED (still `engaged_criticism_policy(...)`) when the field
      is at its default. done-when: the test currently FAILS only because
      `LEGACY_CRITICISM_ENABLED` does not exist yet (paste the
      `AttributeError`).

      **Filename correction (checked before writing, not silently
      assumed):** `tests/test_preparation.py` does not exist —
      `grep -rln build_preparation_manifest tests/` finds the real home,
      `tests/test_v6_engaged_public_defaults.py` (its own
      `test_public_manifest_enables_scratch_and_binds_all_four_schools`
      is the exact byte-identical-default pattern this test mirrors).
      Every remaining step in Part B that names `test_preparation.py`
      means this file instead.

      **Architecture note, checked not assumed:** `build_preparation_manifest`
      builds its `Config` internally via `_config_for_profile`, which
      accepts no caller override for fields like this (confirmed reading
      `preparation.py:268-297`) — exactly the same shape
      `ENGAGED_CRITICISM_AUTHORITY` already has (no test anywhere varies
      it through `build_preparation_manifest` either). This matches
      established precedent, not a gap: "operator-facing" in this
      codebase's idiom means a typed Config field read at mint time, not
      necessarily a new CLI flag; Step 18's positive-case test will
      monkeypatch `preparation.Config` the same way any such field would
      need to be exercised.

      ```
      $ python -m pytest tests/test_v6_engaged_public_defaults.py::test_legacy_criticism_disabled_by_default_is_byte_identical -q
      AttributeError: 'Config' object has no attribute 'LEGACY_CRITICISM_ENABLED'
      1 failed in 0.37s
      ```
- [x] 17. (S2c, R3) Add `LEGACY_CRITICISM_ENABLED: bool = False` to
      `src/deepreason/config.py`, adjacent to the other authority-family
      knobs (`ARGUMENTATIVE_AUTHORITY` etc., `config.py:365-401`), with a
      docstring-comment naming what it does: when True, ordinary
      manifest-building routes criticism through the school-free circuit
      Road E built instead of the school-routed one.
      done-when: Step 16's test now passes for the default-False half;
      paste output.

      ```
      $ python -m pytest tests/test_v6_engaged_public_defaults.py::test_legacy_criticism_disabled_by_default_is_byte_identical -q
      1 passed in 0.28s
      ```
- [x] 18. (S2c, R3) [COMMIT] Wire `preparation.py::build_preparation_manifest`
      (`:387-396`) so that when `config.LEGACY_CRITICISM_ENABLED` is True,
      it passes `criticism_policy=None` to `compile_run_manifest` instead
      of `criticism_policy=engaged_criticism_policy(...)`. done-when: a
      second assertion in Step 16's test file,
      `test_legacy_criticism_enabled_routes_to_school_free_circuit`,
      confirms `manifest.criticism_policy is None` when the flag is True
      — paste `python -m pytest tests/test_preparation.py -k legacy_criticism -q`
      ending "2 passed". Run `python tools/diff_budget.py 81d08e5f0 --ceiling 1600`,
      paste, commit, push.

      (File is `tests/test_v6_engaged_public_defaults.py` per Step 16's
      correction.) The positive-case test monkeypatches
      `preparation.Config` to force `LEGACY_CRITICISM_ENABLED=True` into
      `_config_for_profile`'s internally-built Config, per Step 16's own
      architecture note.

      ```
      $ python -m pytest tests/test_v6_engaged_public_defaults.py -k legacy_criticism -q
      2 passed, 9 deselected in 0.34s
      $ python -m pytest tests/test_v6_engaged_public_defaults.py -q
      11 passed in 13.43s
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason/preparation.py src/deepreason/config.py
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason/preparation.py": 6, "src/deepreason/config.py": 5}, "total_insertions": 11, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 19. (S2c, C3) Add the `_versioned_source_config_data` pop-line for
      `LEGACY_CRITICISM_ENABLED` in `run_manifest.py`, UNCONDITIONALLY for
      every schema version, per the `ENGAGED_CRITICISM_AUTHORITY` trap
      (`docs/map/INV-frozen-surfaces.md:185-208`) — this is the named,
      forecast frozen-surface-4-adjacency contact from SPEC.md's own
      forecast; see the CHECKLIST STOP's grant request below before this
      step executes. done-when:
      `python -m pytest tests/test_run_manifest.py -k canonical_shapes_and_hashes -q`
      still passes (proves the new field does not silently enter any
      pinned hash), paste output.

      **Test-name correction:** `-k canonical_shapes_and_hashes` matches 0
      tests in `test_run_manifest.py` (65 deselected) — the actual test is
      `tests/test_run_manifest_v4.py::test_v1_v2_v3_canonical_shapes_and_hashes_remain_byte_identical`.
      Ran that plus every other hash-stability test in both files as a
      broader safety net (used under R16's already-scoped grant for this
      exact `_versioned_source_config_data` pop-line pattern).

      ```
      $ python -m pytest tests/test_run_manifest_v4.py -k canonical_shapes_and_hashes -q
      3 passed, 19 deselected in 0.08s
      $ python -m pytest tests/test_run_manifest.py tests/test_run_manifest_v4.py -q
      87 passed in 0.82s
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason/run_manifest.py
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason/run_manifest.py": 5}, "total_insertions": 5, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 20. (S2c, C9/surface-5 forecast) Qualification-subject-exclusion
      test: assert `LEGACY_CRITICISM_ENABLED` does NOT appear in
      `qualification_subject_payload`'s output (it gates dispatch routing,
      not provider identity, per SPEC.md's frozen-surface forecast).
      done-when: a new assertion in
      `tests/test_qualification.py::test_legacy_criticism_flag_excluded_from_subject_digest`
      passes.

      **Filename correction:** `tests/test_qualification.py` does not
      exist — the real home (found by grepping for
      `qualification_subject_payload`/`_digest` callers) is
      `tests/test_reusable_qualification.py`, which already has the exact
      `_manifest(profile, config_updates=..., **compile_updates)` fixture
      this test needed (`config_updates={"LEGACY_CRITICISM_ENABLED": True},
      criticism_policy=None`). The flag trivially cannot appear in the
      payload — `qualification_subject_payload` only dumps the COMPILED
      MANIFEST's own fields, and `LEGACY_CRITICISM_ENABLED` is a
      Config-only field never written into the manifest (only its effect,
      `criticism_policy` None vs populated, is) — matching Step 19's pop
      line reasoning exactly.

      ```
      $ python -m pytest tests/test_reusable_qualification.py::test_legacy_criticism_flag_excluded_from_subject_digest -q
      1 passed in 0.28s
      $ python -m pytest tests/test_reusable_qualification.py -q
      34 passed in 21.46s
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths tests/test_reusable_qualification.py
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"tests/test_reusable_qualification.py": 21}, "total_insertions": 21, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 21. (S2c, R3) End-to-end integration test: with
      `LEGACY_CRITICISM_ENABLED=True` on an ordinary `build_preparation_manifest`-built
      manifest, a scheduler run with an eligible target actually dispatches
      a live `crit_argumentative_batch` call through Road E's contract (not
      deferred). done-when:
      `python -m pytest tests/test_scheduler.py -k legacy_criticism_end_to_end -q`
      passes.

      **Filename correction (fourth in this Part — noted, not
      re-litigated):** lives in `tests/test_v6_engaged_public_defaults.py`
      as `test_legacy_criticism_end_to_end_dispatches_without_a_school`,
      next to the school-routed sibling test it mirrors
      (`test_public_preset_run_dispatches_school_routed_criticism`), reused
      as the fixture template (real `Harness`/`LLMAdapter`/`MockEndpoint`,
      `Scheduler(harness, adapter, config, run_manifest=manifest)`). Passed
      on the first run — genuine end-to-end confirmation that Road E plus
      the Config-flag plumbing (Steps 16-18) actually dispatches live, with
      no `"v6-model-phase-deferred.v1"` marker, a critic with no school,
      and the durable payload carrying `critic_school_id: None` /
      `dispatch_authority: "observe_only"`.

      ```
      $ python -m pytest tests/test_v6_engaged_public_defaults.py -k legacy_criticism_end_to_end -q
      1 passed, 11 deselected in 2.05s
      $ python -m pytest tests/test_v6_engaged_public_defaults.py -q
      12 passed in 15.58s
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths tests/test_v6_engaged_public_defaults.py
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"tests/test_v6_engaged_public_defaults.py": 149}, "total_insertions": 149, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 22. (S2c) Map update, same commit: add a row to
      `docs/map/CON-authority.md`'s "Where it lives" table for
      `LEGACY_CRITICISM_ENABLED`, and cross-reference from
      `docs/map/CON-seats.md` (which owns `preparation.py`) noting the new
      Config-driven branch in `build_preparation_manifest`. done-when:
      `python tools/docs_verify.py` reports 0 failed for both documents.

      **Collateral break found running the full corpus (not just the two
      named documents):** `SEAM-manifest-x-schools.md:153`'s check greps
      the literal substring `"criticism_policy=engaged_criticism_policy("`
      in `preparation.py` — Step 18's conditional expression
      (`criticism_policy=(None if config.LEGACY_CRITICISM_ENABLED else
      engaged_criticism_policy(...))`) removed that exact substring even
      though the underlying fact the check verifies (this file still
      calls `engaged_criticism_policy` with `config.ENGAGED_CRITICISM_AUTHORITY`)
      remains true. Narrowed the grep to `"else engaged_criticism_policy("`
      — still specific to the real call site, matches the new shape.
      `docs_verify.py`: 0 failed after the fix (was 1 failed).

      ```
      $ python tools/docs_verify.py
      docs_verify [full]: 53 documents, 852 checks, 4 workers
      docs_verify: 0 failed
      ```
- [x] 23. (S2c) [COMMIT] Subsystem ring:
      `python -m pytest tests/test_preparation.py tests/test_run_manifest.py tests/test_qualification.py tests/test_scheduler.py -q`.
      done-when: "N passed, 0 failed" (paste). Diff budget check, commit,
      push.

      (Real filenames per this Part's corrections:
      `test_v6_engaged_public_defaults.py`, `test_run_manifest.py`,
      `test_run_manifest_v4.py`, `test_reusable_qualification.py`,
      `test_scheduler.py`.)

      ```
      $ python -m pytest tests/test_v6_engaged_public_defaults.py tests/test_run_manifest.py tests/test_run_manifest_v4.py tests/test_reusable_qualification.py tests/test_scheduler.py -q
      138 passed in 36.04s
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason": 112, "tests": 432, "docs/map": 78}, "total_insertions": 622, "ceiling": 1600, "verdict": "WITHIN"}
      ```

---

## PART C — Adjudication opt-in
(S: SPEC.md §2(a); R1, C3)

- [x] 24. (S2a, R1) Reader/default test FIRST:
      `tests/test_text_authority_policy.py::test_adjudication_status_authority_disabled_by_default_is_byte_identical`
      — `Config().ADJUDICATION_STATUS_AUTHORITY_ENABLED is False`, and
      every existing authority test in this file still passes unmodified
      (proving the new gate changes nothing when False). done-when: fails
      only on the missing attribute (paste).

      File and test name both correct this time (no correction needed).

      ```
      $ python -m pytest tests/test_text_authority_policy.py::test_adjudication_status_authority_disabled_by_default_is_byte_identical -q
      AttributeError: 'Config' object has no attribute 'ADJUDICATION_STATUS_AUTHORITY_ENABLED'
      1 failed in 0.14s
      ```
- [x] 25. (S2a, R1) Add `ADJUDICATION_STATUS_AUTHORITY_ENABLED: bool = False`
      to `config.py`. done-when: Step 24's attribute-existence half
      passes.

      Placed BEFORE `ARGUMENTATIVE_AUTHORITY` (not "adjacent... after", as
      originally scoped) so the master gate reads first, ahead of the six
      knobs it governs.

      ```
      $ python -m pytest tests/test_text_authority_policy.py::test_adjudication_status_authority_disabled_by_default_is_byte_identical -q
      1 passed in 0.08s
      ```
- [x] 26. (S2a, R1) [COMMIT] Wire the master gate: in `authority.py`'s
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

      **Scope check against SPEC.md before touching `trial_authority_for`
      (not assumed):** its `if workload_profile != "text": return
      TrialAuthority.STATUS` early return is explicitly Part D's job
      (SPEC.md §2(b): "the rubric-authority forced-STATUS path for
      non-text workloads" is closed by `JUDGE_SEATS_ENABLED`, not this
      flag) — left untouched. The gate applies only inside the
      `workload_profile == "text"` branch, and only to
      `argumentative_authority_mode`/`trial_authority_for`'s RETURN
      VALUES, not to `text_authority_mode` itself (used by
      `text_status_authority_issues`/`authority_policy_snapshot` for
      misconfiguration detection — masking a genuine
      `calibrated_status`-without-a-receipt issue behind this flag would
      hide operator errors, not gate authority).
      `argumentative_authority_mode` validates BEFORE applying the gate,
      so a malformed `ARGUMENTATIVE_AUTHORITY` still raises regardless of
      the flag's state.

      ```
      $ python -m pytest tests/test_text_authority_policy.py::test_master_gate_forces_observe_only_even_when_trial_configured -q
      1 passed in 0.28s
      $ python -m pytest tests/test_text_authority_policy.py tests/test_workload_formal.py -q
      24 passed in 1.23s
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason/authority.py tests/test_text_authority_policy.py
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason/authority.py": 22, "tests/test_text_authority_policy.py": 44}, "total_insertions": 66, "ceiling": 1600, "verdict": "WITHIN"}
      ```

      **Major mid-step discovery — `docs_verify.py` run proactively
      (habit from Steps 13a/14b/22), found the first version of this
      step's fix was WRONG, not just incomplete:** the initial
      implementation put the master-gate override INSIDE
      `argumentative_authority_mode` itself. That function has THREE
      callers, not one — `rules/crit.py::_authority` (operational
      dispatch, correctly the gate's target) AND
      `authority.py::text_status_authority_issues` /
      `authority_policy_snapshot` (schema-v2 PREFLIGHT MISCONFIGURATION
      DETECTION and a frozen policy snapshot — both need the DECLARED
      value, gate or no gate). Gating the shared function made preflight
      silently stop detecting "trial_required without a calibration
      receipt" whenever the master flag was off — masking a genuine
      operator misconfiguration, exactly the failure mode Step 26's own
      `trial_authority_for` design already avoided for
      `text_authority_mode`. Caught by `CON-authority.md:194`'s check
      (`test_text_status_authority_requires_calibration_receipt` and
      `test_arbitrary_calibration_receipt_is_unverified` both failed).
      **Fixed** by reverting `argumentative_authority_mode` to always
      return the declared value, and moving the gate to
      `rules/crit.py::_authority` — the one place that actually consumes
      it operationally, matching how `trial_authority_for` was already
      scoped.

      **Collateral test breaks (predicted by this step's own design text
      — "makes R1 an actual opt-in... since the six knobs are
      independently settable today" — so minimally updated, not
      weakened):** three pre-existing tests exercised `trial_required`/
      `single_family_trial` reachability directly through `Config(
      ARGUMENTATIVE_AUTHORITY=...)` without also setting the new master
      flag — `test_criticism_authority.py::test_trial_required_needs_court`,
      `test_prose_refutation_boundaries.py::test_the_new_mode_routes_to_the_same_defended_trial`,
      `::test_the_config_only_path_cannot_satisfy_the_cross_school_guarantee`.
      Each got `ADJUDICATION_STATUS_AUTHORITY_ENABLED=True` added to its
      `Config(...)` construction — restoring the SAME reachability each
      always tested, not changing any assertion.

      **Step 28 pulled forward (not deferred):** `docs_verify.py` also
      surfaced `SEAM-manifest-x-schools.md:302` (pinned v1-v3 canonical
      hash goldens) and `SUB-application.md:165`
      (`test_single_profile_home_qualify_output_is_byte_identical_to_pre_s4`)
      failing — the SAME "new Config field leaks into the pinned hash"
      problem Step 19 already solved for `LEGACY_CRITICISM_ENABLED`, now
      hitting `ADJUDICATION_STATUS_AUTHORITY_ENABLED` between Step 25
      (field added) and Step 28 (pop-line, originally scheduled later).
      Rather than commit with the gate red for two steps, added Step 28's
      pop-line now (see Step 28's own entry below, marked done here).
      `docs_verify.py`: 0 failed after all of the above (was 4 failed).

      ```
      $ python -m pytest tests/test_text_authority_policy.py tests/test_criticism_authority.py tests/test_prose_refutation_boundaries.py tests/test_v6_nonconjecture_recovery.py tests/test_manifest_integration.py tests/test_workload_formal.py tests/test_run_manifest.py tests/test_run_manifest_v4.py tests/test_qualification_per_seat.py tests/test_experiment.py -q
      217 passed in 83.68s
      $ python tools/docs_verify.py
      docs_verify [full]: 53 documents, 852 checks, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason/authority.py src/deepreason/rules/crit.py src/deepreason/config.py src/deepreason/run_manifest.py tests/test_text_authority_policy.py tests/test_criticism_authority.py tests/test_prose_refutation_boundaries.py
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason/authority.py": 24, "src/deepreason/rules/crit.py": 51, "src/deepreason/config.py": 11, "src/deepreason/run_manifest.py": 12, "tests/test_text_authority_policy.py": 44, "tests/test_criticism_authority.py": 5, "tests/test_prose_refutation_boundaries.py": 10}, "total_insertions": 157, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [ ] 27. (S2a, R1) Close the two ungated mint sites: add the same master
      check to `imports.py::register_epistemic_import_failure` and
      `rules/experiment.py::relevance_trial`, defaulting closed (i.e.
      when the flag is False, these two paths behave as if authority is
      `observe_only` too, closing the gap SPEC.md's §2(a) measured).
      done-when: two new tests,
      `test_imports.py::test_import_failure_gated_by_adjudication_master_flag`
      and
      `test_experiment.py::test_relevance_trial_gated_by_adjudication_master_flag`,
      both pass.
- [x] 28. (S2a, C3) `_versioned_source_config_data` pop-line for
      `ADJUDICATION_STATUS_AUTHORITY_ENABLED`, unconditional across schema
      versions. done-when: canonical-hash goldens still pass (same command
      as Step 19).

      Done as part of Step 26 (pulled forward — see that step's own entry
      for the discovery and full proof). `run_manifest.py`'s pop-line
      comment is honest that, unlike `ENGAGED_CRITICISM_AUTHORITY`/
      `LEGACY_CRITICISM_ENABLED`, this field's effect is NEVER manifest-
      visible at all (per the frozen-surfaces law), not merely "already
      visible elsewhere."
- [ ] 29. (S2a, C9) Qualification-subject-exclusion test for this field,
      same shape as Step 20.
- [ ] 30. (S2a, R1) Solo-law regression test: with the master flag True
      and a genuinely single-model-family run, `single_family_trial`
      remains reachable (not accidentally gated away by this change).
      done-when:
      `tests/test_text_authority_policy.py::test_single_family_trial_reachable_under_master_gate`
      passes.
- [ ] 31. (S2a) Map update, same commit: `docs/map/CON-authority.md`
      gains a row for `ADJUDICATION_STATUS_AUTHORITY_ENABLED` and a note
      in its "How to add a new authority mode" table that this is now the
      master reachability gate all six existing knobs sit behind.
      done-when: `python tools/docs_verify.py` 0 failed.
- [ ] 32. (S2a) [COMMIT] Subsystem ring:
      `python -m pytest tests/test_text_authority_policy.py tests/test_imports.py tests/test_experiment.py tests/test_run_manifest.py -q`.
      "N passed, 0 failed" (paste). Diff budget, commit, push.

---

## PART D — Judge seats opt-in
(S: SPEC.md §2(b); R2, R6, R10, C3, C7)

- [ ] 33. (S2b, R2) Reader/default test FIRST:
      `tests/test_judge_ensemble_boundary.py::test_judge_seats_disabled_by_default_is_byte_identical`
      — `Config().JUDGE_SEATS_ENABLED is False`, existing judge-dispatch
      tests unmodified. done-when: fails only on missing attribute.
- [ ] 34. (S2b, R2) Add `JUDGE_SEATS_ENABLED: bool = False`,
      `JUDGE_SUMMONS_PER_CYCLE: int = 0`, `JUDGE_SUMMONS_COOLDOWN: int = 4`
      to `config.py`, modeled on `ADVISORY_TRIALS_PER_CYCLE`/`DISC_COOLDOWN`'s
      existing shape (`config.py:401,441-442`). done-when: Step 33's
      attribute half passes.
- [ ] 35. (S2b, R2) [COMMIT] Gate every current judge-dispatch site on
      `JUDGE_SEATS_ENABLED`: `scheduler.py:1116-1117` (rubric-trial
      `has_role("judge")` check), `scheduler.py:2167-2168` (audit-step),
      the property-step fail-closed check, AND the non-text-workload
      forced-`TrialAuthority.STATUS` path in `authority.py:101-102` (the
      one gap SPEC.md's measurement found with NO existing suppression) —
      when False, none of these dispatch regardless of workload_profile or
      rubric criteria present. done-when: a new test
      `tests/test_scheduler.py::test_judge_dispatch_gated_off_even_for_nontext_workload_with_rubric_criteria`
      passes. Diff budget check, commit, push.
- [ ] 36. (S2b, R6/R10) Throttle wiring: `JUDGE_SUMMONS_PER_CYCLE`/
      `JUDGE_SUMMONS_COOLDOWN` are STATIC caps only (Amendment 5's
      benching — no signal-adaptive behavior in this tranche). Wire them
      identically to how `ADVISORY_TRIALS_PER_CYCLE`/`DISC_COOLDOWN`
      already cap their respective counters, applied at whichever judge
      dispatch site(s) Step 35 gated. done-when:
      `tests/test_budget.py::test_judge_summons_per_cycle_cap` and
      `::test_judge_summons_cooldown` both pass.
- [ ] 37. (S2b, R2) Reconciliation test with the cross-family gate (solo
      law): `JUDGE_SEATS_ENABLED=True` on a genuinely single-model-family
      run still refuses typed (`SECOND_JUDGE_FAMILY_REQUIRED`) at the same
      layer it does today — this opt-in does not bypass that guarantee.
      done-when:
      `tests/test_run_manifest.py::test_judge_seats_opt_in_does_not_bypass_cross_family_requirement`
      passes (extends the existing
      `test_cross_family_rubric_policy_fails_preflight_for_one_family`
      pattern).
- [ ] 38. (S2b, R2) `_versioned_source_config_data` pop-lines for all
      three new fields, unconditional. Qualification-subject-exclusion
      test for all three (same shape as Step 20, one assertion per
      field).
- [ ] 39. (S2b) CLI/operator-facing surface: the flag's help text (or
      setup-time confirmation prompt) surfaces the judge-audit evidence
      summary named in SPEC.md §2(b) (11.9% sensitivity under strict
      default, 47.5-60% false-conviction under loosened voting,
      self-preference/verbosity bias unmeasured) — a static string
      constant, not new research. done-when:
      `tests/test_cli.py::test_judge_seats_flag_surfaces_evidence_warning`
      passes.
- [ ] 40. (S2b) Map update, same commit: `docs/map/CON-seats.md` gains a
      row noting `JUDGE_SEATS_ENABLED` as the master judge-dispatch gate,
      distinct from (and upstream of) `require_cross_family_judges`'s
      diversity guarantee.
- [ ] 41. (S2b) [COMMIT] Subsystem ring:
      `python -m pytest tests/test_judge_ensemble_boundary.py tests/test_budget.py tests/test_scheduler.py tests/test_run_manifest.py tests/test_cli.py -q`.
      "N passed, 0 failed" (paste). Diff budget, commit, push.

---

## PART E — Schools opt-in
(S: SPEC.md §2(d); R5, C6)

- [ ] 42. (S2d, R5) Reader/default test FIRST:
      `tests/test_run_manifest.py::test_school_seats_disabled_by_default_is_byte_identical`
      — `Config().SCHOOL_SEATS_ENABLED is False`, `SchoolExecutionPolicyV1.mode`
      stays `conditioning_only`-only-constructible (no `route_bound`
      reachable) when False.
- [ ] 43. (S2d, R5) Add `SCHOOL_SEATS_ENABLED: bool = False` to
      `config.py`.
- [ ] 44. (S2d, R5) [COMMIT] Add the `--seat school-N=<profile>` CLI
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
- [ ] 45. (S2d, C6) Consequence-A regression test (must stay inert, per
      the map's own pinned invariant): binding two schools to two distinct
      models does not change `foreign_schools` computation in
      `plan_foreign_criticism`. done-when:
      `tests/test_foreign_school_criticism_scheduler_c3.py::test_distinct_school_models_do_not_change_foreign_coverage_count`
      passes.
- [ ] 46. (S2d, C6) Consequence-B disclosure (Road A, approved — no code
      change to `firewall.py`): a regression test PROVING the documented
      side effect is real and unchanged in shape (so a future reader knows
      it is expected, not a regression): enabling school seats with
      distinct models flips `is_single_model_run` to False for the whole
      run and can newly require `require_cross_family_judges()` on an
      untouched `judge` role. done-when:
      `tests/test_judge_ensemble_boundary.py::test_school_seat_diversity_flips_single_model_predicate_for_judge_role`
      passes (this test's existence and passing IS the "disclosure" —
      it's the executable proof backing the operator-facing help text
      Step 47 writes).
- [ ] 47. (S2d) CLI operator-facing surface: `--seat school-N=<profile>`'s
      help text names Consequence B explicitly (a school-seat opt-in that
      adds route diversity anywhere in the run's role table can revoke the
      argument trial's cross-school substitute for the judge role) —
      static string, not new research. done-when:
      `tests/test_cli.py::test_school_seat_flag_surfaces_single_model_warning`
      passes.
- [ ] 48. (S2d, C3) `_versioned_source_config_data` pop-line for
      `SCHOOL_SEATS_ENABLED`. Qualification-subject-exclusion test (same
      shape as Step 20).
- [ ] 49. (S2d) Solo-law/qualification-cost disclosure: help text also
      names the qualification-battery cache-miss cost
      (`docs/map/SEAM-manifest-x-schools.md:137-144`) of moving a school
      to a different seat. done-when: same test file as Step 47 gains an
      assertion for this string.
- [ ] 50. (S2d) Map update, same commit: `docs/map/SEAM-manifest-x-schools.md`
      gains a note that `route_bound` mode is no longer dormant-in-every-
      shipped-configuration — it is now reachable via
      `SCHOOL_SEATS_ENABLED`, still defaulting off. Update the seam's own
      "Every `SchoolExecutionPolicyV1` constructed anywhere in `src/` is
      `conditioning_only`" check to account for the new (default-off)
      exception.
- [ ] 51. (S2d) [COMMIT] Subsystem ring:
      `python -m pytest tests/test_run_manifest.py tests/test_foreign_school_criticism_scheduler_c3.py tests/test_judge_ensemble_boundary.py tests/test_cli.py -q`.
      "N passed, 0 failed" (paste). Diff budget, commit, push.

---

## PART F — Static signal-read surface
(S: REQUEST.md R15; SPEC.md DECISION SHEET header note)

Strictly a READ aggregation over already-existing, already-live signals —
no new event/record type, no mid-run consumption (Amendment 5's benching
holds).

- [ ] 52. (R15) Reader test FIRST: a new module
      `src/deepreason/signals_read.py` does not exist yet; write
      `tests/test_signals_read.py::test_signal_snapshot_shape` asserting
      the shape of a new typed `SignalSnapshotV1` (fields: latest
      config-critique verdict via `referee.py::latest_config_critique`,
      per-phase `v6-model-phase-deferred` counts via a new small helper
      reading `verification/report.py`'s existing
      `_deferred_model_phase_findings` output, and the run's `TokenMeter.snapshot()`)
      against a fixture root. done-when: fails only on the missing module
      (paste `ModuleNotFoundError`).
- [ ] 53. (R15) [COMMIT] Implement `signals_read.py::read_signal_snapshot(root)`
      — pure aggregation, read-only, no mid-run wiring, consumable from
      `report`/`audit`/CLI tooling at run boundaries only. done-when:
      Step 52's test passes. Diff budget check, commit, push.
- [ ] 54. (R15) Wire `read_signal_snapshot` into the existing
      `verification/report.py` report output (an additive field, not a
      new report shape) so `deepreason status`/`report` surfaces it.
      done-when: `tests/test_verification_report.py::test_report_includes_signal_snapshot`
      passes.
- [ ] 55. (R15) Register the new marker's signal name in
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
- [ ] 56. (R15) Map update, same commit: add a row to
      `docs/map/SUB-scheduler.md` or a new small doc for
      `signals_read.py` (executor's judgment at execution time on whether
      this warrants its own `SUB-*.md` or a row in an existing one — flag
      for the operator if genuinely ambiguous, per dr-ask-the-right-question,
      rather than guessing).
- [ ] 57. (R15) [COMMIT] Subsystem ring:
      `python -m pytest tests/test_signals_read.py tests/test_verification_report.py tests/test_signals.py -q`.
      "N passed, 0 failed" (paste). Diff budget, commit, push.

---

## PART G — Gate and delivery

- [ ] 58. (all) Map check: `python tools/docs_verify.py`. done-when: 0
      failed, and `python tools/docs_verify.py --audit` reports 0
      findings.
- [ ] 59. (all) Frozen-surface diff confirmation: `git diff` against the
      pre-tranche base touches ONLY the surfaces named in the CHECKLIST
      STOP's grant request below (`run_manifest.py`'s
      `_versioned_source_config_data` pop-lines, additive only) — no
      other line in `capabilities/state.py`, `harness.py`'s event
      application, `invariants.py`, or any manifest schema/validator.
      done-when: `git diff --stat 81d08e5f0 -- src/deepreason/capabilities/state.py src/deepreason/harness.py src/deepreason/invariants.py` is empty, AND
      `git diff 81d08e5f0 -- src/deepreason/run_manifest.py`
      shows ONLY `.pop(...)` line additions inside
      `_versioned_source_config_data` (paste the diff for visual
      confirmation).
- [ ] 60. (all) Full gate: `python -m pytest tests/ -q -n 4`. done-when:
      output ends "N passed, 0 failed" (paste it; expect ~3100+N given
      the new tests this tranche adds).
- [ ] 61. (all) Wheel smoke instruments (per CLAUDE.md — no gate runs
      these automatically, but this tranche adds new CLI flags/console
      surface, so re-run and re-pin if changed):
      `python scripts/wheel_smoke.py` and
      `python -u scripts/wheel_operational_smoke.py`. done-when: both
      exit 0; if the public surface pin changed (new `--seat school-N`,
      new flags), the pin update is folded into this same step's diff, not
      a separate trailing one.
- [ ] 62. (all) [COMMIT] Root sweep (guard rule from
      `docs/map/INV-frozen-surfaces.md`, since this tranche touches a
      reader-adjacent area — Road E changes what dispatches, not what a
      committed root MEANS, but the instrument is cheap insurance):
      `python tools/root_sweep.py post-tranche-sweep.txt`. done-when: no
      root's `valid` or `att` changed versus the pre-tranche baseline
      (paste the diff, expect byte-identical).
- [ ] 63. (all) [COMMIT] Final push and clean-tree confirmation:
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
Steps 19, 28, 38 (x3), 48 depend on this grant.

**Everything else this checklist plans is confirmed, by Step 1's design
note, Step 3's STOP/Amendment-7 resolution, and the frozen-surface
forecast SPEC.md already carries, to touch NONE of the five frozen
surfaces** (`capabilities/state.py`, `harness.py` event application,
`invariants.py`/replay-validation formats, `run_manifest.py`
SCHEMA/validators beyond the one named pop-line class above, and
`route_fingerprint`) — Road E's revised design (S13a-g) touches only
`rules/crit.py`, `nonconjecture_recovery.py`, and `scheduler.py`, reusing
the EXISTING `"criticism.semantic-task.v1"`/`"batch-critic.v2"`
transactional contract and `workflow/transaction_service.py` machinery
verbatim — no new contract, no new schema; every opt-in is a `Config`
field consulted at an existing mint or dispatch site.

**Any contact this checklist's steps are found to require, during
execution, that is NOT one of the two paragraphs above is a hard STOP per
Amendment 5's own rule — not a judgment call for `dr-execute-step` to
make.**

Commit and push this file, then STOP for operator review. No
`dr-execute-step` invocation runs against this checklist until the
operator has reviewed it and, specifically, granted or amended Requested
grant 1 above.
