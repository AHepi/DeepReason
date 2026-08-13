# CHECKLIST.md — defended_trial criticism authority wired into v6

State: executing.

Each step's done-criterion is pasted into the commit that closes it.

1. [ ] **WorkflowTaskKind.DEFENDED_TRIAL_STEP** — add the enum member to
   `workflow/models.py`. Done-criterion: `python -c "from deepreason.workflow.models import WorkflowTaskKind; WorkflowTaskKind.DEFENDED_TRIAL_STEP"` succeeds.
2. [ ] **`_v6_transactional_trial_call` helper** — add to `informal/trial.py`,
   per SPEC.md §3. Done-criterion: importable, `python -c "from deepreason.informal.trial import _v6_transactional_trial_call"`.
3. [ ] **Wire the defender call, `_judge_all`, `_paraphrase_screen`** in
   `informal/trial.py` per SPEC.md §3 (manifest detection, `step`/
   `step_prefix` threading, rubric/pairwise call sites unchanged). Done-criterion:
   `python -m pytest tests/test_trial_accounting.py tests/test_argumentative_trial.py -q` (or
   whatever the existing trial test files are named — confirmed by a repo
   search at execution time) still green, proving no behavior change to the
   non-v6 path.
4. [ ] **R7 manifest surface-4 widening** — `run_manifest.py::
   _route_seat_behavioral_contract_assignments` grants defender/judge/
   variator role seats a wire contract. Done-criterion: a compiled v6
   manifest with defender/judge routes configured resolves
   `resolve_route_seat_behavioral_capability(manifest, role="defender",
   ...)` without raising.
5. [ ] **R5 offline regression** — new
   `tests/test_v6_defended_trial_transaction_wiring.py` proving a defender
   call and a judge call each dispatch carrying a `dispatch_authorization`
   (mock endpoint), per SPEC.md §5. Done-criterion: file green in isolation.
6. [ ] **R2 recovery fix** — `workflow/nonconjecture_recovery.py`:
   `_criticism_contract`'s two authority gates widen to accept
   `defended_trial`/`trial_required`/`single_family_trial`;
   `_recover_criticism_effect` resolves the real authority instead of the
   `"observe_only"` hardcode. `rules/crit.py::_crit_argumentative_batch_result`
   gains the `adapter is None` typed-deferral branch (SPEC.md §2). Done-criterion:
   the two new recovery tests (step 7) plus the existing
   `test_criticism_contract_refuses_recovery_without_a_school_when_dispatch_authority_is_not_observe_only`
   — this existing test's NAME and refusal shape must be reconsidered: it
   currently asserts a `dispatch_authority="trial_required"` recovery is
   refused outright; after R2 this becomes recoverable (deferred, not
   refused). Update the test to match the new, intended behavior, noting
   the change in the test's own docstring (never silently deleting a
   contradicted assertion).
7. [ ] **R2/R4 regression tests** — two new tests in
   `tests/test_v6_nonconjecture_recovery.py`: observe_only resumes
   observe_only (extend existing), defended_trial resumes as
   defended_trial via typed deferral (new). Done-criterion: both green.
8. [ ] **R3 compile-gate conversion** — `run_manifest.py::
   _validate_v6_capability_policy`'s `V6_DEFENDED_TRIAL_TRANSACTION_CONTRACT_REQUIRED`
   raise becomes a `CompileNoticeV1`-emitting non-refusal (moved into
   `_production_routes_are_concrete` where `_emit_deduped` is in scope, per
   the `SECOND_JUDGE_FAMILY_REQUIRED` precedent) — ONLY after step 6 is
   green. Done-criterion: `RunManifest.model_validate(...)` with
   `criticism_policy.authority == "defended_trial"` on schema v6 no longer
   raises; `compile_notices` is empty (fully wired, no residual sub-case)
   or names the residual gap if one remains.
9. [ ] **`[COMMIT]` checkpoint 1** — `python tools/diff_budget.py` against
   SPEC.md §7's ceiling; `python -m pytest tests/test_v6_defended_trial_transaction_wiring.py tests/test_v6_nonconjecture_recovery.py tests/test_workflow_reducer_c0.py -q` (the ring). Commit, push.
10. [ ] **Map docs** — `docs/map/SUB-workflow.md` and
    `docs/map/SUB-adjudication.md` staleness check; update in the same
    commit if content changed (R9). `python tools/docs_verify.py`.
11. [ ] **Root sweep** — `python tools/root_sweep.py` (or the targeted
    `verify_root_report` on a known-good v6 root, per REQUEST.md R7's LAW
    clause) before/after comparison, byte-identical.
12. [ ] **Full gate** — `python -m pytest tests/ -q -n 4`; compare against
    known baselines (REQUEST.md R11): 1 pre-existing `test_bronze_report`
    failure, 5 known-flaky MCP-thread tests under `-n 4`. 0 unexplained
    failures.
13. [ ] **`docs_verify` full** — `python tools/docs_verify.py`; compare
    against known baseline (3 pre-existing `CON-run-identity.md`
    shallow-clone failures).
14. [ ] **`[COMMIT]` checkpoint 2** — commit, push.
15. [ ] **R6 guarded live attempt** — compile and launch the ladder per
    REQUEST.md R6's exact config; judge typed outcomes only.
16. [ ] **R10 errata check** — confirm no committed document claims
    defended_trial already works on v6 (docs/ERRATA.md tail already read
    at session start through E24; recheck after any doc edits this tranche
    made).
17. [ ] **dr-validate-change** — VALIDATION.md against every acceptance
    check in SPEC.md §5 plus the full gate.
18. [ ] **dr-deliver-change** — DELIVERY.md, R-by-R reconciliation, PROOF
    pasted, final commit and push.
