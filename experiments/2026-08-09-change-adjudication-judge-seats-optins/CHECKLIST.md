# Checklist for: adjudication / judge-seats / legacy-criticism / schools opt-ins
State: next=45 blockers=none (Parts A+B+C+D+D2+B2 complete; Part E steps 42-44b complete -- BOTH independent school-seat levers now fully wired: conjecture-side `--school-seat` (Step 44) and criticism-side `--criticism-seat` (Step 44b, reusing the renamed `_school_seat_route_ensemble` helper and `parse_school_seat_flags`, its own `criticism-seat-bindings.yaml` persistence file, and `engaged_criticism_policy`'s new `seat_map` keyword), each with its own master-gate/prerequisite refusal tests and CLI round-trip tests; full gate + full docs_verify both 0 failed; next is Step 45, the Consequence-A regression test; diff-budget base a942f404c, 743/1600)
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
- [x] 27. (S2a, R1) Close the two ungated mint sites: add the same master
      check to `imports.py::register_epistemic_import_failure` and
      `rules/experiment.py::relevance_trial`, defaulting closed (i.e.
      when the flag is False, these two paths behave as if authority is
      `observe_only` too, closing the gap SPEC.md's §2(a) measured).
      done-when: two new tests,
      `test_imports.py::test_import_failure_gated_by_adjudication_master_flag`
      and
      `test_experiment.py::test_relevance_trial_gated_by_adjudication_master_flag`,
      both pass.

      **Filename correction:** the second test lives in
      `tests/test_properties.py` (where every other `relevance_trial`
      exercise already lives), not `test_experiment.py` (a different
      mechanism file — generators, not properties).

      **Design decisions made while implementing (not silently typed
      in):**
      - `register_epistemic_import_failure` gained a required `config`
        parameter (threaded from its one caller, `resolve_for_design`,
        which already had it in scope). Gated closed: records scrutiny
        (critic artifact, no warrant, `["scrutiny", design, critic]`
        Measure — reusing the identical registered signal `crit.py`'s
        own `observe_only` path uses) instead of an unconditional
        warrant. One pre-existing test
        (`test_epistemic_import_failure_uses_evidence_on_validity_node`)
        exercised the warrant path directly without a config argument;
        updated to pass `Config(ADJUDICATION_STATUS_AUTHORITY_ENABLED=True)`,
        restoring the exact reachability it always tested.
      - `relevance_trial` gated closed: dispatches NO judge at all (zero
        tokens) and leaves the property's `Status` untouched rather than
        forcing non-activation. Discovered mid-test-writing that
        `active_properties()`'s own docstring makes "ACCEPTED is the
        entire activation gate" — a property mechanically admitted by
        `checker_wf` stays reported as active even with no fresh
        relevance confirmation, since nothing REFUTES it either. This is
        the correct observe_only analog ("target status untouched"), not
        a gap — my first test draft asserted the wrong thing
        (`active_properties() == []`) and was corrected before
        finalizing. A new registered signal, `property-relevance-
        declined`, records the decline (inputs: `[signal, property
        artifact id]`).
      - Collateral: same predicted-reachability pattern as Step 26 hit
        FIVE more `Config()` call sites across
        `tests/test_properties.py` (4, via the shared `_activated_
        property` helper) and `tests/test_evidence_view.py` (1), plus
        `tests/test_judge_ensemble_boundary.py`'s cross-family-guard test
        (which needs to actually REACH `adapter.require_cross_family_
        judges()` to test it, now gated behind the flag too). All
        6 got `ADJUDICATION_STATUS_AUTHORITY_ENABLED=True` added.

      **`docs_verify.py` run proactively (now standard practice), found
      two more things:**
      1. `SEAM-adjudication-x-authority.md:92`'s own check explicitly
         says it "pins TODAY's state, and it is expected to be updated —
         not deleted — by whatever change gates them" (its own `How to
         change it` item 4). Rewrote the prose and check to state the
         fix and the specific design point it asked to be settled: these
         two sites read the flag DIRECTLY (not routed through
         `trial_authority_for`/`argumentative_authority_mode`, since
         neither is a `workload_profile == "text"` judgement). Also
         updated the earlier "Argumentative mints with no gate at all"
         table row to match.
      2. `SUB-harness.md`/`SUB-rules.md`/`SUB-scheduler.md` all reference
         `tests/test_signals.py::test_every_emitted_signal_is_registered`,
         which failed: `property-relevance-declined` was an unregistered
         signal tag. Registered it in `signals.py` alongside the other
         criticism-authority signals (`scrutiny`/`trial-declined`/etc).

      ```
      $ python -m pytest tests/test_imports.py::test_import_failure_gated_by_adjudication_master_flag tests/test_properties.py::test_relevance_trial_gated_by_adjudication_master_flag -q
      2 passed in 0.59s
      $ python -m pytest tests/test_imports.py tests/test_properties.py tests/test_evidence_view.py tests/test_judge_ensemble_boundary.py tests/test_experiment.py tests/test_signals.py -q
      59 passed in 28.76s
      $ python tools/docs_verify.py
      docs_verify [full]: 53 documents, 852 checks, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason/imports.py src/deepreason/rules/experiment.py src/deepreason/signals.py tests/test_imports.py tests/test_properties.py tests/test_evidence_view.py tests/test_judge_ensemble_boundary.py
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason/imports.py": 22, "src/deepreason/rules/experiment.py": 14, "src/deepreason/signals.py": 6, "tests/test_imports.py": 29, "tests/test_properties.py": 65, "tests/test_evidence_view.py": 3, "tests/test_judge_ensemble_boundary.py": 8}, "total_insertions": 147, "ceiling": 1600, "verdict": "WITHIN"}
      ```
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
- [x] 29. (S2a, C9) Qualification-subject-exclusion test for this field,
      same shape as Step 20.

      Lives in `tests/test_reusable_qualification.py` (Step 20's file),
      right after its `LEGACY_CRITICISM_ENABLED` sibling. Simpler than
      Step 20's — this flag has zero manifest-visible downstream effect
      at all (Step 28's own pop-line comment), so no `criticism_policy`
      compile-update is needed to make the test meaningful.

      ```
      $ python -m pytest tests/test_reusable_qualification.py::test_adjudication_status_authority_flag_excluded_from_subject_digest -q
      1 passed in 0.26s
      ```
- [x] 30. (S2a, R1) Solo-law regression test: with the master flag True
      and a genuinely single-model-family run, `single_family_trial`
      remains reachable (not accidentally gated away by this change).
      done-when:
      `tests/test_text_authority_policy.py::test_single_family_trial_reachable_under_master_gate`
      passes.

      **Filename correction, and a scope clarification found reading
      the existing evidence before writing (not assumed):** lives in
      `tests/test_prose_refutation_boundaries.py`, next to
      `_single_family_trial_adapter` and
      `test_a_single_model_run_refutes_by_prose_end_to_end`, the file
      that already carries every `single_family_trial` fixture. That
      neighboring test proves LIVE end-to-end reachability (a warrant
      mints) but calls `run_argument_trial_from_case` directly with
      `authority="status"` — it never reads `ARGUMENTATIVE_AUTHORITY` or
      the new master flag at all, so it is unaffected by this gate and
      does not by itself prove solo-law compliance for THIS step.
      Separately, `test_the_config_only_path_cannot_satisfy_the_cross_
      school_guarantee` (fixed in Step 26) already shows the bare
      Config-only direct-helper path structurally cannot supply a critic
      school in a solo run — `single_family_trial` was NEVER reachable
      through that specific path even before this flag existed. Given
      both of those, the meaningful, honest claim this step's own
      wording asks for ("not accidentally gated away by THIS change") is
      at the resolution layer: `crit._authority(config)` must still
      return `single_family_trial`, not silently downgrade it to
      `observe_only`, when the master flag is True on a genuinely
      single-family adapter. Wrote exactly that, with
      `is_single_family_run(adapter.leases) is True` asserted alongside
      it so "genuinely single-family" is proven, not assumed.

      **Second mid-step discovery, this file's `docs_verify.py` habit
      paying off again:** `test_a_passing_formal_commitment_now_resists_
      prose` (R21) set `ARGUMENTATIVE_AUTHORITY=SINGLE_FAMILY_AUTHORITY`
      WITHOUT the master flag — before Step 26, this reached the trial
      attempt and formal-backing immunity genuinely intercepted it; with
      the master flag now defaulting the call to `observe_only` before
      ever attempting a trial, the test's own assertion
      (`not harness.state.att`) still happened to hold, but for the
      WRONG reason (no trial attempted at all, not formal-backing
      immunity actually firing) — a silently weakened test that was
      still green. Caught rereading the file's full
      `SINGLE_FAMILY_AUTHORITY` usage list while writing this step's own
      test, not by a failing check. Added
      `ADJUDICATION_STATUS_AUTHORITY_ENABLED=True` to restore the real
      test conditions R21 needs.

      ```
      $ python -m pytest tests/test_prose_refutation_boundaries.py::test_single_family_trial_reachable_under_master_gate -q
      1 passed in 0.18s
      $ python -m pytest tests/test_prose_refutation_boundaries.py -q
      46 passed in 3.39s
      $ python tools/docs_verify.py
      docs_verify [full]: 53 documents, 852 checks, 4 workers
      docs_verify: 0 failed
      ```
- [x] 31. (S2a) Map update, same commit: `docs/map/CON-authority.md`
      gains a row for `ADJUDICATION_STATUS_AUTHORITY_ENABLED` and a note
      in its "How to add a new authority mode" table that this is now the
      master reachability gate all six existing knobs sit behind.
      done-when: `python tools/docs_verify.py` 0 failed.

      **Real section name is "Where to change what"** (CHECKLIST's "How
      to add a new authority mode" doesn't exist as a heading).

      **Major discovery writing this row — the claim "all six knobs sit
      behind this gate" was FALSE when I went to write it, not merely
      undocumented:** SPEC.md's own §2(a) design text explicitly names
      `ENGAGED_CRITICISM_AUTHORITY` as one of the gated knobs ("it only
      permits an operator to set ARGUMENTATIVE_AUTHORITY/
      ENGAGED_CRITICISM_AUTHORITY/etc. away from observe_only"), but
      Steps 26-27's implementation only gated `rules/crit.py::_authority`
      and the two mint sites — `preparation.py::build_preparation_
      manifest` still passed `config.ENGAGED_CRITICISM_AUTHORITY`
      straight through to `engaged_criticism_policy` unconditionally,
      meaning an operator could ALREADY compile `defended_trial` into
      the manifest without ever setting the master flag. Fixed now,
      before writing a map claim that would have been false: the
      `authority=` argument is `config.ENGAGED_CRITICISM_AUTHORITY` only
      when `ADJUDICATION_STATUS_AUTHORITY_ENABLED` is True, else
      `"observe_only"`. Two new tests prove both directions —
      `test_engaged_criticism_authority_inert_without_the_master_gate`
      and `::_reachable_with_the_master_gate` (the latter checked at the
      argument-passing layer via monkeypatch, not a full manifest
      compile: `defended_trial` also requires two cross-family judge
      seats, a separate unrelated compile-time guard
      `build_preparation_manifest`'s single-profile broadcast cannot
      supply regardless of this flag — that combination is Part D's
      seat-diversity territory).

      ```
      $ python -m pytest tests/test_v6_engaged_public_defaults.py -q
      14 passed in 17.43s
      $ python -m pytest tests/test_v6_engaged_public_defaults.py tests/test_v6_policy_preset.py tests/test_reusable_qualification.py tests/test_text_authority_policy.py -q
      80 passed in 37.56s
      $ python tools/docs_verify.py
      docs_verify [full]: 53 documents, 852 checks, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason/preparation.py tests/test_v6_engaged_public_defaults.py docs/map/CON-authority.md
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason/preparation.py": 11, "tests/test_v6_engaged_public_defaults.py": 217, "docs/map/CON-authority.md": 3}, "total_insertions": 231, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 32. (S2a) [COMMIT] Subsystem ring:
      `python -m pytest tests/test_text_authority_policy.py tests/test_imports.py tests/test_experiment.py tests/test_run_manifest.py -q`.
      "N passed, 0 failed" (paste). Diff budget, commit, push.

      Widened to every file touched or newly relevant across Part C
      (16 files), not just the four originally named.

      ```
      $ python -m pytest tests/test_text_authority_policy.py tests/test_imports.py tests/test_experiment.py tests/test_run_manifest.py tests/test_run_manifest_v4.py tests/test_criticism_authority.py tests/test_prose_refutation_boundaries.py tests/test_judge_ensemble_boundary.py tests/test_evidence_view.py tests/test_properties.py tests/test_v6_engaged_public_defaults.py tests/test_v6_policy_preset.py tests/test_reusable_qualification.py tests/test_signals.py tests/test_v6_nonconjecture_recovery.py tests/test_manifest_integration.py tests/test_workload_formal.py -q
      325 passed in 129.34s
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason": 208, "tests": 714, "docs/map": 98}, "total_insertions": 1020, "ceiling": 1600, "verdict": "WITHIN"}
      ```

---

## PART D — Judge seats opt-in
(S: SPEC.md §2(b); R2, R6, R10, C3, C7)

- [x] 33. (S2b, R2) Reader/default test FIRST:
      `tests/test_judge_ensemble_boundary.py::test_judge_seats_disabled_by_default_is_byte_identical`
      — `Config().JUDGE_SEATS_ENABLED is False`, existing judge-dispatch
      tests unmodified. done-when: fails only on missing attribute.

      File and test name both correct.

      ```
      $ python -m pytest tests/test_judge_ensemble_boundary.py::test_judge_seats_disabled_by_default_is_byte_identical -q
      AttributeError: 'Config' object has no attribute 'JUDGE_SEATS_ENABLED'
      1 failed in 0.10s
      ```
- [x] 34. (S2b, R2) Add `JUDGE_SEATS_ENABLED: bool = False`,
      `JUDGE_SUMMONS_PER_CYCLE: int = 0`, `JUDGE_SUMMONS_COOLDOWN: int = 4`
      to `config.py`, modeled on `ADVISORY_TRIALS_PER_CYCLE`/`DISC_COOLDOWN`'s
      existing shape (`config.py:401,441-442`). done-when: Step 33's
      attribute half passes.

      Placed right before `ADVISORY_TRIALS_PER_CYCLE` (the master gate
      ahead of the field it's most conceptually adjacent to), matching
      how `ADJUDICATION_STATUS_AUTHORITY_ENABLED` was placed ahead of
      `ARGUMENTATIVE_AUTHORITY` in Step 25.

      ```
      $ python -m pytest tests/test_judge_ensemble_boundary.py::test_judge_seats_disabled_by_default_is_byte_identical -q
      1 passed in 0.07s
      ```
- [x] 35. (S2b, R2) [COMMIT] Gate every current judge-dispatch site on
      `JUDGE_SEATS_ENABLED`: `scheduler.py:1116-1117` (rubric-trial
      `has_role("judge")` check), `scheduler.py:2167-2168` (audit-step),
      the property-step fail-closed check, AND the non-text-workload
      forced-`TrialAuthority.STATUS` path in `authority.py:101-102` (the
      one gap SPEC.md's measurement found with NO existing suppression) —
      when False, none of these dispatch regardless of workload_profile or
      rubric criteria present. done-when: a new test
      `tests/test_scheduler.py::test_judge_dispatch_gated_off_even_for_nontext_workload_with_rubric_criteria`
      passes. Diff budget check, commit, push.

      Four dispatch sites gated with direct `config.JUDGE_SEATS_ENABLED`/
      `self.config.JUDGE_SEATS_ENABLED` reads: the `_criticize` rubric-trial
      branch (`scheduler.py:1116`), `_audit_step`'s early return
      (`scheduler.py:2158`), `_property_step`'s early return
      (`scheduler.py:2276`), and `authority.py::trial_authority_for`'s
      non-text branch (was an unconditional `TrialAuthority.STATUS` with no
      suppression at all — now `OBSERVE_ONLY` unless `JUDGE_SEATS_ENABLED`).

      **Collateral (predicted reachability, same pattern as Part C):** every
      pre-existing test that exercised judge dispatch without setting the
      new flag broke and got it added to its `Config(...)`/`SimpleNamespace`
      construction — `test_properties.py`,
      `test_workload_formal.py`, `test_rotation.py` (both the shared
      `_starvation_setup` helper and one standalone construction),
      `test_chaos_invariants.py::test_disagreeing_ensemble_and_weak_defender`,
      and `test_v6_scheduler_model_phase_deferral.py`'s two v6-defer tests
      (`test_v6_experiment_and_property_design_defer_before_provider`,
      `test_v6_audit_vision_and_lazy_hv_defer_without_dispatch` — these use
      bare `SimpleNamespace` config doubles that lack the field entirely, so
      the fix is the field added to the namespace, not a `getattr` default,
      matching every other collateral fix in this tranche).

      **Map staleness (docs_verify.py), all now fixed:** `CON-authority.md`
      and `SEAM-adjudication-x-authority.md` each had a check asserting
      `trial_authority_for(Config(), ...) == STATUS` for non-text
      workloads — now `OBSERVE_ONLY` at the default, `STATUS` only with
      `JUDGE_SEATS_ENABLED=True` (both checks and their prose updated).
      `run_manifest.py::_versioned_source_config_data` gained unconditional
      pop-lines for the three new fields (`JUDGE_SEATS_ENABLED`,
      `JUDGE_SUMMONS_PER_CYCLE`, `JUDGE_SUMMONS_COOLDOWN`), same pattern as
      Steps 19/26 — this alone fixed `SEAM-manifest-x-schools.md`,
      `SUB-application.md`, and `SUB-scheduler.md`'s pytest-backed checks
      (their config-hash-adjacent test rings were failing on the new field
      leaking into pinned goldens). `SEAM-scheduler-x-rules.md`'s pinned
      config-field-reference count moved `(12, 29)` → `(12, 30)` (the new
      `JUDGE_SEATS_ENABLED` read at the scheduler-side gate sites; the
      `rules/` count and the `FUZZ_N` intersection are unchanged).

      ```
      $ python -m pytest tests/test_v6_scheduler_model_phase_deferral.py -q
      10 passed in 1.53s
      $ python -m pytest tests/test_judge_ensemble_boundary.py tests/test_scheduler.py tests/test_properties.py tests/test_workload_formal.py tests/test_rotation.py tests/test_chaos_invariants.py tests/test_v6_scheduler_model_phase_deferral.py tests/test_run_manifest_v4.py tests/test_foreign_criticism_policy_c3.py -q
      93 passed in 25.06s
      $ python -m pytest tests/test_v6_engaged_public_defaults.py tests/test_v6_only_manifest_loading.py tests/test_runtime_workload_integration.py tests/test_process_metadata.py tests/test_run_manifest_scratch_bridge.py tests/test_run_manifest.py tests/test_jolt_trigger_pilot.py tests/test_compact_profiles.py -q
      177 passed in 27.12s
      $ python tools/docs_verify.py
      docs_verify [full]: 53 documents, 852 checks, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason": 243, "tests": 792, "docs/map": 111}, "total_insertions": 1146, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 36. (S2b, R6/R10) Throttle wiring: `JUDGE_SUMMONS_PER_CYCLE`/
      `JUDGE_SUMMONS_COOLDOWN` are STATIC caps only (Amendment 5's
      benching — no signal-adaptive behavior in this tranche). Wire them
      identically to how `ADVISORY_TRIALS_PER_CYCLE`/`DISC_COOLDOWN`
      already cap their respective counters, applied at whichever judge
      dispatch site(s) Step 35 gated. done-when:
      `tests/test_budget.py::test_judge_summons_per_cycle_cap` and
      `::test_judge_summons_cooldown` both pass.

      New `Scheduler._judge_summons_admitted(key)` helper: a per-cycle
      counter (`_judge_summons_this_cycle`, reset in `step()`, modeled on
      `_advisory_trials_this_cycle`) plus a per-target cooldown dict
      (`_judge_summons_last`, modeled on `_disc_last`). Consulted at all
      three `JUDGE_SEATS_ENABLED` dispatch sites from Step 35: the rubric-
      trial branch (keyed `artifact.id:commitment.id`), `_audit_step`
      (keyed `"audit:run"`, checked after its v6-defer check so a deferred
      audit never spends real-dispatch budget), and `_property_step`
      (keyed `problem.id:cid`, checked right before `propose_properties`
      for the same reason). Both fields default to preserve exactly zero
      judge activity (`JUDGE_SUMMONS_PER_CYCLE=0`) even with
      `JUDGE_SEATS_ENABLED=True`, per SPEC.md's own prediction — an
      operator must set a nonzero rate too.

      **Collateral (predicted reachability, same pattern as every prior
      part):** `test_properties.py::test_scheduler_conjectures_ground_
      truth_and_kills_the_trap` and `test_chaos_invariants.py::test_
      disagreeing_ensemble_and_weak_defender` set `JUDGE_SEATS_ENABLED=
      True` but not the new per-cycle cap; both got `JUDGE_SUMMONS_PER_
      CYCLE` added to their `Config(...)`.

      **Test design note:** both new tests call `scheduler._criticize`
      directly rather than driving a full `run()` — VS_K>1 rivals on one
      problem spawn discrimination, an existing judge-dispatch path
      outside Step 35's scope (pairwise trials, not rubric/audit/
      property-relevance) that isn't throttled by this gate at all and
      would contaminate a call-count assertion trying to isolate it. Each
      admitted rubric trial also consults BOTH cross-family judge seats
      (`require_cross_family_judges`), so the counters in these tests are
      2x/4x the number of trials, not the number of judge calls 1:1 — the
      tests' comments spell this out explicitly rather than leaving a
      "why 2, why 4" for a future reader to re-derive.

      **Map staleness fixed in the same commit:**
      `SEAM-scheduler-x-rules.md`'s pinned scheduler-side config-field-
      read count moved `(12, 30)` → `(12, 32)` for the two new
      `config.JUDGE_SUMMONS_PER_CYCLE`/`config.JUDGE_SUMMONS_COOLDOWN`
      reads (the `rules/` count and the `FUZZ_N` intersection unchanged).
      A first `docs_verify.py` run genuinely caught this stale check —
      not a false alarm — confirming the check still does its job.

      ```
      $ python -m pytest tests/test_budget.py -q
      11 passed in 0.62s
      $ python -m pytest tests/test_judge_ensemble_boundary.py tests/test_scheduler.py tests/test_properties.py tests/test_workload_formal.py tests/test_rotation.py tests/test_chaos_invariants.py tests/test_v6_scheduler_model_phase_deferral.py tests/test_budget.py tests/test_imports.py tests/test_experiment.py -q
      91 passed in 29.09s
      $ python tools/docs_verify.py
      docs_verify [full]: 53 documents, 852 checks, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason": 271, "tests": 902, "docs/map": 111}, "total_insertions": 1284, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 37. (S2b, R2) Reconciliation test with the cross-family gate (solo
      law): `JUDGE_SEATS_ENABLED=True` on a genuinely single-model-family
      run still refuses typed (`SECOND_JUDGE_FAMILY_REQUIRED`) at the same
      layer it does today — this opt-in does not bypass that guarantee.
      done-when:
      `tests/test_run_manifest.py::test_judge_seats_opt_in_does_not_bypass_cross_family_requirement`
      passes (extends the existing
      `test_cross_family_rubric_policy_fails_preflight_for_one_family`
      pattern).

      No production code change: this step's finding IS that
      `compile_run_manifest`'s cross-family check already ignores
      `Config.JUDGE_SEATS_ENABLED` entirely (the two gates are wired at
      genuinely separate layers — one compile-time judge-diversity
      guarantee in `run_manifest.py`, one runtime dispatch gate in
      `scheduler.py` — with no code path connecting them), so the new
      test passes unmodified against the existing implementation. Same
      config shape as `test_cross_family_rubric_policy_fails_preflight_
      for_one_family` (`_config()`: two identical `family="gemma"` judge
      routes), plus `JUDGE_SEATS_ENABLED = True` set directly on the
      Config instance before compiling.

      ```
      $ python -m pytest tests/test_run_manifest.py::test_judge_seats_opt_in_does_not_bypass_cross_family_requirement tests/test_run_manifest.py::test_cross_family_rubric_policy_fails_preflight_for_one_family -q
      2 passed in 0.18s
      $ python -m pytest tests/test_run_manifest.py -q
      66 passed in 0.75s
      $ python tools/docs_verify.py --fast
      docs_verify [fast]: 53 documents, 852 checks, 850 reused, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason": 271, "tests": 922, "docs/map": 111}, "total_insertions": 1304, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 38. (S2b, R2) `_versioned_source_config_data` pop-lines for all
      three new fields, unconditional. Qualification-subject-exclusion
      test for all three (same shape as Step 20, one assertion per
      field).

      The pop-lines (`JUDGE_SEATS_ENABLED`, `JUDGE_SUMMONS_PER_CYCLE`,
      `JUDGE_SUMMONS_COOLDOWN`) already landed in Step 35's commit
      (`f57cf13dc`), pulled forward while fixing that step's
      `SEAM-manifest-x-schools.md`/`SUB-application.md`/`SUB-scheduler.md`
      docs_verify failures — noted there, not re-done here. This step
      adds the qualification-subject-exclusion test only: new
      `test_judge_seats_fields_excluded_from_subject_digest` in
      `tests/test_reusable_qualification.py`, modeled on
      `test_adjudication_status_authority_flag_excluded_from_subject_
      digest` (same shape: never written to the manifest at all, so no
      `criticism_policy`-style legitimate downstream difference to carve
      out, unlike `test_legacy_criticism_flag_excluded_from_subject_
      digest`'s `criticism_policy=None` override) — one assertion per
      field, all three raw Config names absent from the payload's JSON.

      ```
      $ python -m pytest tests/test_reusable_qualification.py::test_judge_seats_fields_excluded_from_subject_digest -q
      1 passed in 0.31s
      $ python -m pytest tests/test_reusable_qualification.py -q
      36 passed in 17.90s
      $ python tools/docs_verify.py --fast
      docs_verify [fast]: 53 documents, 852 checks, 851 reused, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason": 271, "tests": 948, "docs/map": 111}, "total_insertions": 1330, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 39. (S2b) CLI/operator-facing surface: the flag's help text (or
      setup-time confirmation prompt) surfaces the judge-audit evidence
      summary named in SPEC.md §2(b) (11.9% sensitivity under strict
      default, 47.5-60% false-conviction under loosened voting,
      self-preference/verbosity bias unmeasured) — a static string
      constant, not new research. done-when:
      `tests/test_cli.py::test_judge_seats_flag_surfaces_evidence_warning`
      passes.

      **Filename correction (same pattern as Steps 20/21/33):**
      `tests/test_cli.py` does not exist. Real home:
      `tests/test_cli_setup_seats.py` (already exercises `setup`'s
      optional flags, `--seat` in particular — the closest existing
      precedent for an opt-in `setup` flag).

      **No CLI flag existed anywhere for `JUDGE_SEATS_ENABLED` before this
      step** (unlike `LEGACY_CRITICISM_ENABLED`/
      `ADJUDICATION_STATUS_AUTHORITY_ENABLED`, which likewise have none —
      both are set via `--config`'s YAML profile only). Added a new
      `--judge-seats` flag to `setup_cmd` in `cli/main.py`, scoped
      narrowly to disclosure per the step's own wording ("the flag's help
      text (or setup-time confirmation prompt) surfaces...", never "and
      persists the flag") — `setup_wizard` writes only the provider/route
      profile, not general `Config` toggles, so `JUDGE_SEATS_ENABLED`
      itself is still set the same way every other Part A-D flag is: via
      `--config`'s YAML profile. `--judge-seats` is a pure acknowledgement
      gate: it prints the same `JUDGE_SEATS_EVIDENCE_SUMMARY` constant
      that's baked into its own `--help` text, satisfying the step's
      "help text (or setup-time confirmation prompt)" wording via BOTH
      channels rather than picking one. Not passing `--judge-seats`
      prints nothing extra — the disclosure is opt-in-triggered, not
      forced on every `setup` run.

      **Trap found and fixed while writing the `--help` test:** argparse's
      `HelpFormatter` performs `%`-substitution
      (`%(default)s`-style) on every action's help string, so the
      evidence text's literal `%` characters (`11.9%`, `47.5%`, `60%`)
      crashed `format_help()` with `TypeError: not enough arguments for
      format string` until escaped to `%%` — but ONLY in the argparse
      `help=` copy; the setup-time `print()` uses the unescaped constant,
      since `print()` does no such substitution and printing the escaped
      copy would show literal `%%` to the operator.

      ```
      $ python -m pytest tests/test_cli_setup_seats.py -q
      5 passed in 0.25s
      $ python -m pytest tests/test_cli_setup_seats.py tests/test_easy.py tests/test_v6_only_cli_admission.py -q
      115 passed, 1 skipped in 1.80s
      $ python tools/docs_verify.py --fast
      docs_verify [fast]: 53 documents, 852 checks, 782 reused, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason": 311, "tests": 997, "docs/map": 111}, "total_insertions": 1419, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 40. (S2b) Map update, same commit: `docs/map/CON-seats.md` gains a
      row noting `JUDGE_SEATS_ENABLED` as the master judge-dispatch gate,
      distinct from (and upstream of) `require_cross_family_judges`'s
      diversity guarantee.

      Added to the "Where it lives" table, next to the other
      `judge`/seat-routing rows, cross-referencing the exact dispatch
      sites Step 35 gated. No new `check:` line — a descriptive pointer
      row, matching the convention most other rows in this table already
      follow (not every row carries its own independent check).

      ```
      $ python tools/docs_verify.py --fast
      docs_verify [fast]: 53 documents, 852 checks, 852 reused
      docs_verify: 0 failed
      ```
- [x] 41. (S2b) [COMMIT] Subsystem ring:
      `python -m pytest tests/test_judge_ensemble_boundary.py tests/test_budget.py tests/test_scheduler.py tests/test_run_manifest.py tests/test_cli.py -q`.
      "N passed, 0 failed" (paste). Diff budget, commit, push.

      `tests/test_cli.py` substituted with `tests/test_cli_setup_seats.py`
      (Step 39's filename correction).

      ```
      $ python -m pytest tests/test_judge_ensemble_boundary.py tests/test_budget.py tests/test_scheduler.py tests/test_run_manifest.py tests/test_cli_setup_seats.py -q
      93 passed in 2.54s
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason": 311, "tests": 997, "docs/map": 112}, "total_insertions": 1420, "ceiling": 1600, "verdict": "WITHIN"}
      ```

      **Part D (judge seats opt-in) complete: steps 33-41.**

---

## PART E — Schools opt-in
(S: SPEC.md §2(d); R5, C6)

- [x] 42. (S2d, R5) Reader/default test FIRST:
      `tests/test_run_manifest.py::test_school_seats_disabled_by_default_is_byte_identical`
      — `Config().SCHOOL_SEATS_ENABLED is False`, `SchoolExecutionPolicyV1.mode`
      stays `conditioning_only`-only-constructible (no `route_bound`
      reachable) when False.

      Two assertions: `Config().SCHOOL_SEATS_ENABLED is False` (fails now
      on missing attribute, until Step 43) and a pin that neither shipped
      v6 control-plane preset (`v6_policy.py`'s `conservative`/`engaged`)
      ever constructs `route_bound` — true today independent of this
      flag (`compile_run_manifest` requires an explicit
      `control_plane_policy` for schema v4+; nothing currently GATES a
      hand-supplied `route_bound` one, so this pin covers what actually
      reaches operators through the shipped presets, and Step 44 is where
      an explicit gate refusing an ungated `route_bound` policy — if that
      turns out to be needed — gets designed).

      **Diff-budget base switch (same pattern as Part D2):** the
      `81d08e5f0` base is now 1773/1600 (EXCEEDED) with Parts A-D2's
      cumulative diff. Part E now measures against `a942f404c` (the last
      Part D2 commit) — 16/1600 against the new base.

      ```
      $ python -m pytest tests/test_run_manifest.py::test_school_seats_disabled_by_default_is_byte_identical -q
      AttributeError: 'Config' object has no attribute 'SCHOOL_SEATS_ENABLED'
      1 failed in 0.28s
      ```
- [x] 43. (S2d, R5) Add `SCHOOL_SEATS_ENABLED: bool = False` to
      `config.py`.

      Placed right after `JUDGE_SUMMONS_COOLDOWN`, matching the existing
      run of master-gate fields. **Same pop-line trap as Steps 19/26/35
      (recorded, not re-litigated):** adding the bare field alone broke
      two pinned canonical-hash goldens
      (`test_legacy_manifest_hashes_are_stable_after_v3_install`) the
      moment it existed, since `_versioned_source_config_data` echoes
      every `Config` field into the v1-v3 source hash by default. Fixed
      immediately by adding the pop-line in the same commit (pulling
      that half of Step 48 forward, same as Step 35 did for Part D's
      three fields) — Step 48 now only needs the qualification-subject-
      exclusion test.

      ```
      $ python -m pytest tests/test_run_manifest.py tests/test_config.py -q
      84 passed in 0.67s
      $ python -m pytest tests/test_reusable_qualification.py -q
      36 passed in 15.99s
      $ python tools/docs_verify.py --fast
      docs_verify [fast]: 53 documents, 852 checks, 755 reused, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py a942f404c --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "a942f404c", "against": null, "areas": {"src/deepreason": 16, "tests": 16, "docs/map": 0}, "total_insertions": 32, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 44. (S2d, R5, revised by Amendment 11/R27 — SPEC.md addendum S18)
      [COMMIT] Add the `--seat school-N=<profile>` CLI surface (parallel
      in shape to `seat_bindings.py`'s existing `--seat GROUP=PATH`, per
      §5.5 Road B — reusing the manifest's own school-keyed shape, NOT
      extending `seat_bindings.py::GROUP_ROLES`), gated on
      `SCHOOL_SEATS_ENABLED`: CONJECTURE-SIDE ONLY (Amendment 11 corrects
      the original "and/or" coupling to criticism — a school is a
      conjecture-side tool; criticism's attachment is Step 44b, fully
      independent). Populates
      `SchoolExecutionPolicyV1(mode="route_bound", ...)`; never touches
      `CriticismPolicyV1`. done-when:
      `tests/test_run_manifest.py::test_seat_school_flag_produces_route_bound_policy`
      passes. Diff budget check, commit, push.

      **Flag-name correction (checked before writing, not silently
      assumed):** the CHECKLIST's own wording names `--seat
      school-N=<profile>`, but `--seat` already exists for role-group
      bindings (`GROUP=PATH`, Rung S3) and a school id is not a group —
      handing `school-1=<path>` to the existing `--seat` flag would either
      collide with `SEAT_BINDING_GROUP_UNKNOWN` or, worse, silently be
      accepted as a new "group" name if the vocabulary check were ever
      loosened. Implemented as a SEPARATE flag, `--school-seat
      school-N=PATH`, mirroring `--seat`'s shape exactly but keeping the
      two vocabularies (role groups vs. school ids) structurally
      un-collidable — matching `seat_bindings.py`'s own design note (this
      tranche, Step 44's persistence layer) that school seats are "not a
      GROUP_ROLES concept."

      **Filename correction (same pattern as Steps 16/20 — checked, not
      assumed):** the test lives in
      `tests/test_v6_engaged_public_defaults.py`, not
      `tests/test_run_manifest.py` — that file already holds every other
      `build_preparation_manifest`-level default/opt-in test this tranche
      added (Part B/B2/D's tests), and `test_run_manifest.py` builds
      `RunManifest` objects directly with no `build_preparation_manifest`
      fixture at all.

      **What was built**, in commit order:
      - `src/deepreason/v6_policy.py`: `route_bound_school_execution_policy(default_endpoint_id, *, seat_map=None)`
        — binds every seeded public school's `conjecturer` seat to a real
        route (`SchoolExecutionPolicyV1(mode="route_bound", ...)`), taking
        a pre-resolved `seat_map: {school_id: (seat, endpoint_id)}` rather
        than bare endpoint-id strings (see mid-step discovery below for
        why).
      - `src/deepreason/preparation.py`: `_conjecturer_school_seat_ensemble`
        builds a genuine multi-seat `conjecturer` route list (seat 0 =
        the default profile; each distinct school-seat profile gets one
        new seat, deduplicated by `endpoint_id`) and the matching
        `seat_map`; `build_preparation_manifest` gained a `school_seats:
        Mapping[str, ProviderProfileV1] | None` parameter that (a) raises
        typed `RunManifestError("SCHOOL_SEATS_DISABLED", ...)` when
        `school_seats` is given without `Config.SCHOOL_SEATS_ENABLED`
        (defense-in-depth alongside the CLI's own gate), and (b) when
        enabled, overrides `control_plane_policy.school_execution` with
        the route-bound policy — `criticism_policy` is untouched in every
        case, matching the conjecture-only design.
      - `src/deepreason/seat_bindings.py`: a new, SEPARATE persistence file
        (`school-seat-bindings.yaml`, not `seat-bindings.yaml`) and three
        functions (`school_seat_bindings_path`, `parse_school_seat_flags`,
        `resolve_school_seats`) reusing only the generic YAML `{key:
        path}` round-trip (`load_seat_bindings`/`write_seat_bindings`) —
        deliberately NOT extending `GROUP_ROLES`/`parse_seat_flags`, per
        the CHECKLIST's own instruction (school ids carry no role set).
      - `src/deepreason/cli/main.py`: `setup_cmd.add_argument("--school-seat",
        action="append", ...)`, and a handler block parallel to the
        existing `--seat` block that calls `parse_school_seat_flags` +
        `write_seat_bindings` against `school_seat_bindings_path()`.
      - Threaded into the one production call site that resolves seat
        bindings before calling `build_preparation_manifest`
        (`preparation.py`'s `RunPreparationService`-shaped class method):
        `school_seats = resolve_school_seats(environ=self._environ,
        home=self._home)`, passed through as `school_seats=school_seats or
        None` — the run manifest a live `reason` run actually compiles now
        reflects any persisted school-seat bindings, not just the unit-test
        path.
      - `src/deepreason/config.py`: corrected `SCHOOL_SEATS_ENABLED`'s
        comment, stale since Step 43 (written before Amendment 11 split
        the two levers) — it no longer claims the flag gates conjecture-
        and criticism-side routing "together, not either in isolation";
        it now names both levers as independent, sharing only the master
        gate.

      **Mid-step discovery #1 (found while implementing, not in the
      original SPEC.md sketch):** a first version of
      `route_bound_school_execution_policy` took bare `school_seats:
      Mapping[str, str]` (school_id → endpoint_id) and always bound
      `seat=0`. This failed `V4_SCHOOL_ENDPOINT_MISMATCH` —
      `SchoolRoleBindingV1`'s validator requires `binding.endpoint_id ==
      manifest.roles[binding.role][binding.seat].endpoint_id`, i.e. the
      binding must resolve against a REAL route at that seat index in the
      compiled manifest, not an arbitrary string. Fixed by redesigning
      `school_seats` to carry real `ProviderProfileV1` objects (matching
      `seat_bindings`'s existing shape) and adding
      `_conjecturer_school_seat_ensemble` to build a genuine multi-seat
      route list plus a `seat_map` the policy function binds against
      directly — bindings now always match the actual compiled route list
      by construction, not by convention.

      **Mid-step discovery #2 (`docs_verify.py` run proactively, per the
      lesson recorded at Step 13a):** `SEAM-manifest-x-schools.md`'s
      exhaustive "school"+"RunManifest" file-census check moved twice
      during this step — 21→22 when `preparation.py` gained `school_seats`
      (fixed earlier, Step 44's core-mechanism sub-pass), then 22→23 when
      `cli/main.py`'s new `--school-seat` help text put the word "school"
      next to that file's pre-existing "RunManifest" mentions (help text
      for `config compile`/`inspect`). Fixed by updating the count to 23
      and adding a new sentence naming `cli/main.py` as a further miss "in
      the other direction" (names both words, enforces no binding — it
      only parses and persists). The seam's OTHER check (the "every
      `SchoolExecutionPolicyV1` constructed anywhere in `src/` is
      `conditioning_only`" trap) was already updated to its post-Step-44
      shape during the core-mechanism sub-pass and needed no further
      change here. `python tools/docs_verify.py` (full, not `--fast`):
      0 failed after both fixes.

      ```
      $ python -m pytest tests/test_v6_engaged_public_defaults.py::test_seat_school_flag_produces_route_bound_policy tests/test_v6_engaged_public_defaults.py::test_seat_school_flag_refuses_without_the_master_gate -q
      2 passed in 0.51s
      $ python -m pytest tests/test_v6_engaged_public_defaults.py tests/test_run_manifest.py tests/test_run_manifest_v4.py tests/test_foreign_school_criticism_scheduler_c3.py tests/test_criticism_school_execution_c3.py tests/test_reusable_qualification.py tests/test_qualification_per_seat.py tests/test_cli_setup_seats.py tests/test_seat_bindings.py tests/test_config.py -q
      213 passed in ~55s
      $ python tools/docs_verify.py --fast
      docs_verify [fast]: 53 documents, 852 checks, 851 reused, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py a942f404c --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "a942f404c", "against": null, "areas": {"src/deepreason": 241, "tests": 199, "docs/map": 46}, "total_insertions": 486, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 44b. (S2d, R27 — SPEC.md addendum S18, new step, not in the
      original plan) [COMMIT] Add the `--criticism-seat school-N=<profile>`
      CLI surface: criticism-side ONLY, independent of Step 44's flag —
      "the criticism seats are primed by a school," the operator's own
      phrase. Requires `LEGACY_CRITICISM_ENABLED=False` already set
      (criticism must be school-routed at all before a per-school distinct
      route is meaningful); refuses clearly and typed if legacy criticism
      is still active, rather than silently no-op. Populates a per-school
      distinct `endpoint_id` in `CriticismPolicyV1.bindings` (today's
      `engaged_criticism_policy` shares one endpoint across every school's
      binding; this lets one named school's binding diverge). done-when: a
      new `tests/test_run_manifest.py` test proves (a) the flag produces a
      distinct binding for the named school when legacy criticism is off,
      and (b) a clear, typed refusal when legacy criticism is still the
      active default. Diff budget check, commit, push.

      **Filename correction (same pattern as Steps 16/20/44 — checked, not
      assumed):** the tests live in `tests/test_v6_engaged_public_defaults.py`,
      alongside Step 44's own tests — same rationale as before
      (`build_preparation_manifest`-level default/opt-in tests all live
      there; `test_run_manifest.py` builds `RunManifest` objects directly,
      no `build_preparation_manifest` fixture).

      **Refactor before extending (checked, not duplicated):** Step 44's
      `_conjecturer_school_seat_ensemble` (`preparation.py`) already did
      everything this step needs for the `argumentative_critic` role — it
      never referenced "conjecturer" internally, it just builds a generic
      route ensemble + `school_id -> (seat, endpoint_id)` map from a
      profile and a `{school_id: ProviderProfileV1}` mapping. Renamed to
      `_school_seat_route_ensemble` (role-agnostic name, docstring
      updated to name both callers) and reused for both levers, rather
      than pasting a near-identical `_argumentative_critic_school_seat_ensemble`
      copy. No test referenced the old private name, so the rename has no
      collateral.

      **What was built**, mirroring Step 44's shape on the criticism side:
      - `src/deepreason/v6_policy.py`: `engaged_criticism_policy` gained an
        optional `seat_map: Mapping[str, tuple[int, str]] | None = None`
        keyword (backward compatible — every existing caller passes
        nothing and gets the byte-identical shared-seat-0 policy); when
        given, resolves each school's binding the same way
        `route_bound_school_execution_policy` already does.
      - `src/deepreason/preparation.py`: `_config_for_profile` gained
        `criticism_seats`, extending `Config.roles["argumentative_critic"]`
        into a multi-seat list via `_school_seat_route_ensemble` exactly
        like the conjecturer role does. `build_preparation_manifest`
        gained `criticism_seats`, with TWO typed refusals checked before
        any manifest is compiled: `SCHOOL_SEATS_DISABLED` (shared master
        gate, checked first — same code Step 44 uses, now guarding
        `school_seats or criticism_seats`) and the new
        `CRITICISM_SEATS_REQUIRE_SCHOOL_ROUTED_CRITICISM` (fires only when
        the master gate is already open but `LEGACY_CRITICISM_ENABLED` is
        still True). `criticism_policy`'s construction now threads a
        `criticism_seat_map` into `engaged_criticism_policy`;
        `control_plane_policy.school_execution` is completely untouched
        by this parameter, proving the independence directly (Step 44's
        own test proves the mirror image).
      - `src/deepreason/seat_bindings.py`: a THIRD, separate persistence
        file (`criticism-seat-bindings.yaml`, distinct from both
        `seat-bindings.yaml` and `school-seat-bindings.yaml`) —
        `criticism_seat_bindings_path`/`resolve_criticism_seats`, reusing
        the EXISTING `parse_school_seat_flags` for parsing (the
        `school-N=PATH` shape and validation are identical for both
        levers; only the flag name and the file it writes to differ, so
        no second parser was needed).
      - `src/deepreason/cli/main.py`: new `--criticism-seat
        school-N=PATH` flag (separate from `--school-seat`, per the
        SEPARATE-persistence design) and a parallel setup-handler block.
      - Threaded into the SAME production call site Step 44 already
        wired: `criticism_seats = resolve_criticism_seats(...)`, passed
        as `criticism_seats=criticism_seats or None`.

      **Collateral fix (found running the full sweep, not silently
      patched):** `test_engaged_criticism_authority_reachable_with_the_master_gate`
      monkeypatches `engaged_criticism_policy` with a fake
      `_capturing_policy(endpoint_id, *, authority="observe_only")` to spy
      on the `authority` argument; `engaged_criticism_policy`'s new
      `seat_map` keyword broke the call (`build_preparation_manifest`
      always passes it now). Fixed by widening the fake's signature to
      accept and forward `seat_map=None` — the test's actual assertion
      (which `authority` value reached the call) is unchanged.

      ```
      $ python -m pytest tests/test_v6_engaged_public_defaults.py -q
      20 passed in 16.72s
      $ python -m pytest tests/test_v6_engaged_public_defaults.py tests/test_run_manifest.py tests/test_run_manifest_v4.py tests/test_foreign_school_criticism_scheduler_c3.py tests/test_criticism_school_execution_c3.py tests/test_reusable_qualification.py tests/test_qualification_per_seat.py tests/test_cli_setup_seats.py tests/test_seat_bindings.py tests/test_config.py -q
      202 passed in 53.10s
      $ python -m pytest tests/test_scheduler.py tests/test_v6_scheduler_model_phase_deferral.py tests/test_config_referee.py tests/test_v6_live_repair_transactions.py tests/test_v6_nonconjecture_recovery.py tests/test_prose_refutation_boundaries.py tests/test_model_firewall.py -q
      129 passed in 79.16s
      $ python tools/docs_verify.py --fast
      docs_verify [fast]: 53 documents, 852 checks, 776 reused, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py a942f404c --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "a942f404c", "against": null, "areas": {"src/deepreason": 360, "tests": 337, "docs/map": 46}, "total_insertions": 743, "ceiling": 1600, "verdict": "WITHIN"}
      ```
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

## PART D2 — Content-blind same-model judge ensembles (Amendment 9, R22/R24, SPEC.md addendum S14-S16)

Inserted after Part F, before Part G's final gate, using letter-suffixed
step numbers to avoid renumbering the rest of this checklist. S16's exact
manifest-field shape (57d/57e) is NOT yet operator-confirmed — 57a-57c
proceed first (zero frozen-surface risk, self-justifying regardless of
57d/57e's final shape); 57d onward are a named, scoped grant per
REQUEST.md's Amendment 9 clarification, but the CONCRETE mechanism
(`rubric_policy` third literal vs. a separate manifest field) is a design
choice worth the operator seeing before it lands, per this tranche's own
"SPEC before CHECKLIST before code" discipline for anything reaching
`run_manifest.py` beyond a pop-line.

- [x] 57a. (S15) Reader/pinning test FIRST: a new test proving the JUDGE
      pack (`informal/trial.py::_judge_pack`'s rendered output) never
      names an author, model, family, or school — the judge-facing twin
      of `tests/test_prose_refutation_boundaries.py::test_the_criticism_
      prompt_never_names_an_author_or_a_school` (R9), which already pins
      this property for the CRITIC pack but not the judge pack. done-when:
      a new test in `tests/test_judge_ensemble_boundary.py` (or
      `test_prose_refutation_boundaries.py`, executor's judgment on best
      home) passes against CURRENT code with no production change — this
      step is pure verification that S15's read-only finding holds,
      turned into an enforced invariant.

      Home: `tests/test_judge_ensemble_boundary.py` (already has the
      `_trial_fixture`/`_trial_adapter` rubric-trial scaffolding this
      test needed; adding it next to R9's sibling file would have meant
      duplicating that scaffolding for no benefit). New
      `test_judge_pack_never_names_an_author_school_or_model`: a target
      artifact carries a distinctive `Provenance(school="school-
      distinctive-xyz")`; a new `_prompt_capturing_endpoint` helper
      records the RAW prompt text (not just the calling model, unlike
      the existing `_counting_endpoint`) each judge seat receives from
      `run_trial`; asserts the school id and the labels "school",
      "author", "provenance", "conjecturer", "gemma", "qwen" are all
      absent from both judge prompts. Passed on the first run against
      unmodified production code — confirms S15's read-only finding
      (`_judge_pack` interpolates only rubric/precedents/target text/
      case/answer; `TEMPLATES["judge"]` is fixed boilerplate;
      `school_id`/`endpoint_lease` are routing-only params never spliced
      into prompt text) was correct, and now that property is an
      enforced invariant rather than an unpinned observation — the
      prerequisite S16's frozen-surface relaxation (steps 57c-57e) can
      safely build on.

      ```
      $ python -m pytest tests/test_judge_ensemble_boundary.py::test_judge_pack_never_names_an_author_school_or_model -q
      1 passed in 0.11s
      $ python -m pytest tests/test_judge_ensemble_boundary.py -q
      6 passed in 0.16s
      $ python tools/docs_verify.py --fast
      docs_verify [fast]: 53 documents, 852 checks, 849 reused, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py 81d08e5f0 --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "81d08e5f0", "against": null, "areas": {"src/deepreason": 311, "tests": 1053, "docs/map": 112}, "total_insertions": 1476, "ceiling": 1600, "verdict": "WITHIN"}
      ```
**S16 REVISED (operator, 2026-08-10, "The switch needs to be exposed to
CLI is all. Otherwise it's not a setting."):** the Config-field design
below is dropped. Read together with the existing `require_cross_school_
judge_ensemble` substitute (`llm/firewall.py:361+`, unlocked structurally
by configuring `school_judge_bindings` — no separate boolean flag gates
it), the correct shape is the SAME kind of structural substitute, keyed
off the manifest's/adapter's own frozen route shape rather than a
separately-threaded Config boolean: `require_cross_family_judge_ensemble`
accepts EITHER cross-family diversity OR (≥2 judge seats AND every seat
is the exact same `(provider, model_id)`) — narrower than
`is_single_family_run` per `is_single_model_run`'s own existing docstring
("two different models of one family are one family and two models"),
so the existing `test_trial_rejects_invalid_direct_ensemble_before_any_
endpoint_call`'s `same_family_pair=True` case (two DIFFERENT model
strings, `gemma-test-a`/`gemma-test-b`, same family) is UNCHANGED by this
— it is not the same model, so it still correctly rejects; VERIFIED, not
merely argued, before writing 57c. The ONLY genuinely new CLI surface
needed is the construction lever that lets an operator reach "single
model, ≥2 judge seats" at all (SPEC's Road C, never reachable today) --
that lever IS "the switch."

- [x] 57b. (S16, R24) [COMMIT] New `--blind-same-model-judges` boolean
      flag on `deepreason config compile` (`cli/main.py`, next to
      `--judge-family`; mutually exclusive with it — both requesting a
      second judge route is ambiguous, refuse with a clear error rather
      than silently prioritizing one). Threads into
      `compile_run_manifest(..., blind_same_model_judges: bool = False)`:
      in `single_model` mode, when set and `"judge"` is a configured
      role and `judge_family` is not also given, `roles["judge"] =
      (exact, exact)` (two references to the SAME frozen `Route`) instead
      of requiring `--judge-family`. done-when: a new
      `tests/test_run_manifest.py` test compiles a manifest this way and
      asserts `manifest.roles["judge"] == (exact, exact)` (or equivalent
      route-identity assertion).

      **Diff-budget base switch (SPEC.md's own "Budget (Part D2,
      estimate)" note, executed now):** the shared `81d08e5f0` base
      reached 1595/1600 with this step's diff — 5 lines of headroom,
      about to be exceeded by 57c/57d. Per SPEC.md's own plan ("a fresh
      1,600-line ceiling for this addendum's own diff-budget base commit,
      to be set at Part D2's first step"), Part D2 now measures against
      `1079c86ed` (the Steps 40-41 commit, immediately after Part D
      finished) instead — 175/1600 against the new base. All Part D2
      steps from here use this base; Parts A-D's own totals against
      `81d08e5f0` are unaffected and already recorded in their own steps.

      argparse mutual-exclusivity checked at both layers: the CLI handler
      (clear stderr message, exit 1, no partial manifest written) and
      `compile_run_manifest` itself (`RunManifestError`, for any
      programmatic caller that bypasses the CLI). Four new tests: two at
      the `compile_run_manifest` layer
      (`test_blind_same_model_judges_gives_judge_a_second_identical_seat`,
      `test_blind_same_model_judges_conflicts_with_judge_family`), two at
      the CLI/`main()` layer
      (`test_cli_blind_same_model_judges_flag_reaches_the_compiled_
      manifest`, `test_cli_judge_family_and_blind_same_model_judges_
      conflict`) — the CLI-layer pair is what actually proves R25 ("the
      switch needs to be exposed to CLI"), not just the function-level
      parameter.

      **Editing mistake caught before commit:** an early `Edit` call's
      `old_string` match ended mid-test, silently orphaning
      `test_cli_compiles_and_inspects_only_explicit_complete_v6`'s last
      two assertions (a `config inspect` round-trip) into whatever new
      test followed. Caught by re-running the full file (`70 passed`)
      only after noticing an unrelated assertion failure inside a test
      that never should have contained it, then confirmed via `git diff`
      showing an unintended deletion — fixed by restoring those two lines
      to their original test before this commit, verified the diff is
      now purely additive (`git diff | grep '^-'` empty beyond the
      hunk header).

      ```
      $ python -m pytest tests/test_run_manifest.py -q
      70 passed in 1.02s
      $ python -m pytest tests/test_run_manifest.py tests/test_run_manifest_v4.py tests/test_cli_setup_seats.py tests/test_v6_only_cli_admission.py tests/test_schema_v3_consumers.py -q
      187 passed in 3.24s
      $ python tools/diff_budget.py 1079c86ed --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "1079c86ed", "against": null, "areas": {"src/deepreason": 39, "tests": 136, "docs/map": 0}, "total_insertions": 175, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 57c. (S16, R24) [COMMIT] `llm/firewall.py::require_cross_family_
      judge_ensemble` (runtime) and `RunManifest`'s own `rubric_policy ==
      "require_cross_family"` model-validator (compile-time,
      `run_manifest.py:1516-1526`) both gain the structural same-model
      substitute described above. New positive-path tests in
      `tests/test_judge_ensemble_boundary.py` (runtime: a direct
      `LLMAdapter` with two IDENTICAL-model judge endpoints mints) and
      `tests/test_run_manifest.py` (compile-time: a manifest built via
      57b's flag validates clean under `rubric_policy="require_cross_
      family"`, the default). done-when: both new tests pass AND
      `tests/test_judge_ensemble_boundary.py::test_trial_rejects_invalid_
      direct_ensemble_before_any_endpoint_call` (both parametrizations)
      AND `tests/test_run_manifest.py::test_cross_family_rubric_policy_
      fails_preflight_for_one_family` pass UNMODIFIED (per the note
      above — same-family-different-model stays rejected).

      **Fourth enforcement site found, not three** (SPEC.md's S14 census
      corrected again): `compile_run_manifest` itself has its OWN
      pre-check (`run_manifest.py:3227-3240`, function-level, raising
      before the `RunManifest` object is even constructed) — separate
      from the `RunManifest.model_validator` at `:1516-1526` this step
      originally named. Both needed the identical structural-substitute
      edit; missed on the first pass, caught immediately by
      `test_blind_same_model_judges_satisfies_require_cross_family_
      default` failing against the unpatched second site, fixed before
      commit.

      **Three more collateral fixes, all in
      `tests/test_prose_refutation_boundaries.py`** (not predicted by
      SPEC.md's S14/S16 — a genuine gap in that census, found only by
      running the full ring): its `_lease(family, seat=0)` test helper
      derived `model_id` from `family` ALONE, so two same-family calls
      were also, coincidentally, two same-MODEL calls under the old code
      — harmless before this step (family was the only diversity axis
      that mattered), but three tests explicitly constructing
      `_lease("glm"), _lease("glm")` to prove "same family, no
      cross-school binding, must still refuse" now accidentally
      satisfied the NEW same-model substitute instead of hitting the
      rejection they were pinning. Fixed at the helper (`model_id` now
      varies with `seat` too, so two DIFFERENT seats of one family are
      genuinely different models — matching how every other same-family
      fixture in this tranche, e.g. `gemma-test-a`/`gemma-test-b`, was
      already built) plus one caller
      (`test_the_cross_family_gate_is_untouched_by_the_cross_school_
      sibling`) that called `_lease("glm")` twice with NO seat argument
      at all (both defaulting to seat 0, so the helper fix alone
      couldn't differentiate them) — given explicit `seat=0`/`seat=1`.
      No assertion weakened: every one of these three tests still proves
      exactly what its docstring claims, against a fixture that now
      actually exercises that claim instead of accidentally drifting
      onto R24's new path.

      **Docs_verify trap:** the first version of `require_cross_family_
      judge_ensemble`'s new docstring named `compile_run_manifest`
      literally, tripping `SEAM-llm-x-manifest.md`'s own checked
      invariant that `src/deepreason/llm/` never references
      `run_manifest.py`'s construction/persistence functions (a layering
      boundary: `llm/` is beneath `run_manifest.py`, not the reverse).
      Reworded to "the manifest-compile CLI" — same information, no
      forbidden identifier.

      ```
      $ python -m pytest tests/test_judge_ensemble_boundary.py tests/test_model_firewall.py tests/test_run_manifest.py tests/test_run_manifest_v4.py tests/test_prose_refutation_boundaries.py -q
      164 passed in 13.14s
      $ python tools/docs_verify.py --fast
      docs_verify [fast]: 53 documents, 852 checks, 782 reused, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py 1079c86ed --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "1079c86ed", "against": null, "areas": {"src/deepreason": 87, "tests": 194, "docs/map": 0}, "total_insertions": 281, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 57d. (S16, R24) [FROZEN SURFACE — run_manifest.py, Amendment 9
      grant] The `defended_trial`/V4 criticism-policy
      `V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED` check
      (`run_manifest.py:2819-2834`) gains the identical structural
      substitute, reading the same `manifest.roles["judge"]` shape 57b's
      flag can now produce (no separate CLI lever needed for THIS site —
      `criticism_policy` is Config/YAML-driven only for every other
      knob in this tranche, e.g. `ENGAGED_CRITICISM_AUTHORITY`,
      `LEGACY_CRITICISM_ENABLED`; this one follows the same precedent).
      done-when: an equivalent same-model `defended_trial` manifest
      (built via 57b's flag) compiles clean; the existing cross-family
      case stays provably unchanged.

      No existing test named `V4_CRITICISM_CROSS_FAMILY_JUDGES_REQUIRED`
      directly (grep confirmed) — the one existing `defended_trial`
      compile test (`tests/test_v6_manifest_defended_trial.py::test_v6_
      defended_trial_fails_at_manifest_compile_not_during_dispatch`)
      already used cross-family judge routes (different seats -> its
      `_route` helper varies both family and model by seat), so it was
      unaffected and needed no collateral edit. New test
      `test_v6_defended_trial_accepts_same_model_judges_past_the_cross_
      family_gate`: two judge routes built from the identical `_route(
      "judge-same", 9)` call (same seat reused, so same family AND
      model) now reach the NEXT check
      (`V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED`) instead of
      being stopped by the cross-family gate first — same
      "which error type survives" proof technique already used in
      `test_prose_refutation_boundaries.py`'s school-substitute tests, since
      fully satisfying a v6 transaction contract just to prove this one
      gate passed would be substantial unrelated fixture work.

      ```
      $ python -m pytest tests/test_v6_manifest_defended_trial.py tests/test_criticism_school_execution_c3.py tests/test_foreign_criticism_policy_c3.py tests/test_v6_engaged_public_defaults.py tests/test_prose_refutation_boundaries.py -q
      81 passed in 30.81s
      $ python -m pytest tests/test_run_manifest.py tests/test_run_manifest_v4.py tests/test_judge_ensemble_boundary.py tests/test_model_firewall.py -q
      118 passed in 1.25s
      $ python tools/docs_verify.py --fast
      docs_verify [fast]: 53 documents, 852 checks, 754 reused, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py 1079c86ed --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "1079c86ed", "against": null, "areas": {"src/deepreason": 103, "tests": 232, "docs/map": 0}, "total_insertions": 335, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 57e. (S16) CLI/map updates, same commits as 57b-57d:
      `--blind-same-model-judges`'s own `--help` text states the
      blindness guarantee it relies on (cross-reference 57a's pinned
      invariant); `docs/map/CON-authority.md`/`CON-seats.md` gain rows
      for the new flag, `require_cross_family_judge_ensemble`'s
      structural substitute, and its relationship to the existing
      cross-school substitute.

      The `--help` text half already landed in Step 57b's commit
      (`ad9e339d1`) — written alongside the flag itself, cross-
      referencing `test_judge_pack_never_names_an_author_school_or_
      model` by name. This step adds the two map rows: `CON-authority.md`
      ("Where it lives", next to the trial-authority call sites) and
      `CON-seats.md` ("Where it lives", directly under the
      `JUDGE_SEATS_ENABLED` row Step 40 added), each naming all four
      relaxed sites and cross-referencing the existing cross-school
      substitute's identical no-separate-flag shape. No new `check:`
      needed — descriptive pointer rows, same convention as their
      neighbors.

      ```
      $ python tools/docs_verify.py --fast
      docs_verify [fast]: 53 documents, 852 checks, 852 reused
      docs_verify: 0 failed
      $ python tools/diff_budget.py 1079c86ed --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "1079c86ed", "against": null, "areas": {"src/deepreason": 103, "tests": 232, "docs/map": 2}, "total_insertions": 337, "ceiling": 1600, "verdict": "WITHIN"}
      ```
- [x] 57f. (all) [COMMIT] Subsystem ring:
      `python -m pytest tests/test_judge_ensemble_boundary.py tests/test_prose_refutation_boundaries.py tests/test_run_manifest.py tests/test_model_firewall.py -q`.
      "N passed, 0 failed" (paste). Diff budget, commit, push.

      Widened to every file touched or newly relevant across Part D2 (10
      files), not just the four originally named — matching the same
      widening convention Step 32 used for Part C.

      ```
      $ python -m pytest tests/test_judge_ensemble_boundary.py tests/test_prose_refutation_boundaries.py tests/test_run_manifest.py tests/test_model_firewall.py tests/test_run_manifest_v4.py tests/test_v6_manifest_defended_trial.py tests/test_criticism_school_execution_c3.py tests/test_foreign_criticism_policy_c3.py tests/test_v6_engaged_public_defaults.py tests/test_cli_setup_seats.py -q
      204 passed in 26.89s
      $ python tools/docs_verify.py
      docs_verify [full]: 53 documents, 852 checks, 4 workers
      docs_verify: 0 failed
      $ python tools/diff_budget.py 1079c86ed --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "1079c86ed", "against": null, "areas": {"src/deepreason": 103, "tests": 232, "docs/map": 2}, "total_insertions": 337, "ceiling": 1600, "verdict": "WITHIN"}
      ```

      **Part D2 (content-blind same-model judge ensembles) complete:
      steps 57a-57f.**

---

## PART B2 — Flip LEGACY_CRITICISM_ENABLED's shipped default (Amendment 11, R27/R28)

Corrects Amendment 10's too-coupled reading (R26) mid-Part-E: a school is
a conjecture-side attractor-minimization tool; criticism stays a generic,
structurally separate operator, only ever optionally "primed" by a
school as an explicit attachment — never automatically coupled. R28
resolves the operator's "legacy should be the default" as reading (b): a
genuine flip of the already-shipped `engaged` v6 preset's default, not
merely a rule for Part E's new opt-in. `LEGACY_CRITICISM_ENABLED=False`
remains fully supported as the explicit opt-back-in to school-routed
criticism — "That's a configuration option," the operator's own words.

- [x] 58a. (Amendment 11, R28) [COMMIT] Flip
      `Config.LEGACY_CRITICISM_ENABLED`'s default from `False` to `True`
      in `config.py`. done-when: `Config().LEGACY_CRITICISM_ENABLED is
      True` and `build_preparation_manifest`'s default `criticism_policy`
      is `None`.

      **Collateral (predicted, same pattern as every default change this
      tranche has made, but larger — this flips an EXISTING shipped
      default, not merely a new opt-in defaulting closed):**
      `tests/test_v6_engaged_public_defaults.py` — 4 tests fixed:
      - `test_public_manifest_enables_scratch_and_binds_all_four_schools`
        split into `test_public_manifest_enables_scratch_with_legacy_
        criticism_by_default` (new default: `criticism_policy is None`,
        schools still seeded for CONJECTURE via `N_SCHOOLS`, checked
        independently of criticism bindings) and `test_public_manifest_
        binds_all_four_schools_when_school_routed_criticism_is_enabled`
        (the full pre-flip assertion set, now under an explicit
        `LEGACY_CRITICISM_ENABLED=False` override).
      - `test_legacy_criticism_disabled_by_default_is_byte_identical`
        renamed to `test_legacy_criticism_enabled_by_default_is_byte_
        identical`, its claim rewritten to state the NEW default rather
        than deleted — the byte-identical coverage moves to the flipped
        value, per this tranche's own "never claim more than the record
        shows" discipline.
      - `test_engaged_criticism_authority_inert_without_the_master_gate`
        and `::_reachable_with_the_master_gate` (Part C) both needed an
        added `LEGACY_CRITICISM_ENABLED=False` override: `ENGAGED_
        CRITICISM_AUTHORITY` only matters on the school-routed path (it's
        `engaged_criticism_policy`'s `authority=` argument), so without
        the override `criticism_policy` is `None` and these tests could
        no longer exercise what they're actually testing.
      - `test_legacy_criticism_enabled_routes_to_school_free_circuit`
        needed no change — it already forced the flag `True` explicitly,
        now redundant with the default but still a legitimate defense-
        in-depth check that the flag itself works.

      **A second, genuinely different collateral class, found only by
      running the qualification-battery test file (not predicted by any
      SPEC text):** `tests/test_qualification_per_seat.py::test_single_
      profile_home_qualify_output_is_byte_identical_to_pre_s4` compares
      live `deepreason qualify` output byte-for-byte against
      `experiments/2026-08-06-change-qualification-per-seat-s4/before-
      qualify.json`, a PERMANENT HISTORICAL fixture from an entirely
      different, already-delivered tranche (Rung S4/role-seat-separation)
      — `qualification_subject_digest` hashes the compiled manifest's
      actual content, so it legitimately diverged the moment `criticism_
      policy`'s shape changed. Fixed by excluding just that one field
      from the byte-identical comparison (dated, explained inline) rather
      than editing the historical fixture, which must stay an unedited
      snapshot of Rung S4's own deliverable — every other field still
      compares strict, still proving Rung S4 itself changed nothing.

      **Map update, same commit:** `docs/map/CON-authority.md`'s
      `LEGACY_CRITICISM_ENABLED` row updated to state the new default and
      cite Amendment 11/R28.

      ```
      $ python -m pytest tests/test_v6_engaged_public_defaults.py -q
      15 passed in 15.51s
      $ python -m pytest tests/test_qualification_per_seat.py tests/test_reusable_qualification.py tests/test_schema_v3_consumers.py tests/test_seat_bindings_record.py -q
      58 passed in 234.93s
      $ python -m pytest tests/test_v6_engaged_public_defaults.py tests/test_qualification_per_seat.py tests/test_reusable_qualification.py tests/test_schema_v3_consumers.py tests/test_seat_bindings_record.py tests/test_run_manifest.py tests/test_criticism_authority.py -q
      149 passed in 256.35s
      $ python tools/docs_verify.py --fast
      docs_verify [fast]: 53 documents, 852 checks, 852 reused
      docs_verify: 0 failed
      $ python tools/diff_budget.py a942f404c --ceiling 1600 --paths src/deepreason tests docs/map
      {"result_type": "DIFF_BUDGET_RESULT_V1", "base": "a942f404c", "against": null, "areas": {"src/deepreason": 22, "tests": 98, "docs/map": 1}, "total_insertions": 121, "ceiling": 1600, "verdict": "WITHIN"}
      ```

      **Part B2 (LEGACY_CRITICISM_ENABLED default flip) complete.**

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
