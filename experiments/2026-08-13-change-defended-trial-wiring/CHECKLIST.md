# CHECKLIST.md — defended_trial criticism authority wired into v6

State: all steps checked.

Each step's done-criterion is pasted into the commit that closed it.

1. [x] **WorkflowTaskKind.DEFENDED_TRIAL_STEP** — added to `workflow/models.py`.
   Done-criterion met: `python -c "from deepreason.workflow.models import WorkflowTaskKind; WorkflowTaskKind.DEFENDED_TRIAL_STEP"` succeeds.
2. [x] **`_v6_transactional_trial_call` helper** — added to `informal/trial.py`.
   Done-criterion met: importable.
3. [x] **Wired the defender call, `_judge_all`, `_paraphrase_screen`** in
   `informal/trial.py`. Done-criterion met:
   `python -m pytest tests/test_trial.py tests/test_trial_accounting.py
   tests/test_judge_ensemble_boundary.py
   tests/test_prose_refutation_boundaries.py
   tests/test_text_authority_policy.py -q` — 111 passed, proving the
   non-v6 (rubric/pairwise) path is byte-for-byte unchanged.
4. [x] **R7 manifest surface-4 widening** — `_route_seat_behavioral_
   contract_assignments` grants defender/judge/variator route seats a
   wire contract, gated on `criticism_policy.authority ==
   "defended_trial"` (narrowed from an initial route-presence design
   after `docs_verify.py` caught it retroactively invalidating historical
   v6 roots — see step 9b). Done-criterion met.
5. [x] **R5 offline regression** — `tests/test_v6_defended_trial_
   transaction_wiring.py`, 2 tests, green in isolation.
6. [x] **R2 recovery fix** — `_criticism_contract`'s two authority gates
   widened; `_recover_criticism_effect` resolves real authority via new
   `_recovered_criticism_authority`; `_crit_argumentative_batch_result`
   gained the `adapter is None` typed-deferral branch. Done-criterion
   met: the renamed/rewritten `test_criticism_contract_recovers_a_
   trial_authorized_dispatch_without_a_school` passes, with its docstring
   stating the behavior change and why.
7. [x] **R2/R4 regression tests** — `test_recovered_observe_only_
   criticism_resumes_observe_only` and `test_recovered_defended_trial_
   criticism_defers_an_attacking_case_instead_of_downgrading_to_
   observe_only`, both green (the latter also proves idempotent
   re-recovery: no duplicate deferral marker).
8. [x] **R3 compile-gate conversion** — `V6_DEFENDED_TRIAL_TRANSACTION_
   CONTRACT_REQUIRED` retired outright (wiring made it moot, no residual
   `CompileNoticeV1` needed). Landed after steps 1-7 were green, per the
   operator's own ordering. `tests/test_v6_manifest_defended_trial.py`
   rewritten to assert successful compilation.
9. [x] **`[COMMIT]` checkpoints** — three commits, all pushed:
   - `d2cfd2846` (steps 1-8, initial wiring) — diff budget EXCEEDED
     (900/104 vs the original 550-line estimate), revised and explained
     in SPEC.md §7 rather than silently absorbed.
   - `1247a1766` — **critical fix found by `docs_verify.py`, not by the
     ring**: the initial route-presence grant design retroactively
     invalidated replay of existing committed v6 roots with judge/
     defender routes configured for unrelated reasons (rubric trials).
     Narrowed to `criticism_policy.authority == "defended_trial"`.
     Verified: all 106 committed roots load with zero errors after the
     fix (`python -c` loop over every `experiments/`/`runs/` root).
   - `733e37db0` — map-doc coupling-count and exact-message
     reconciliation (14 checks `docs_verify.py` flagged as stale after
     the code diff, none a defect — all either counts that genuinely
     moved or an assertion whose expected value changed with the fix).
10. [x] **Map docs** — `docs/map/SUB-workflow.md` (new Traps entry: why
    `DEFENDED_TRIAL_STEP` is absent from `_RECOVERABLE_TASKS`, plus a
    stale test-name fix), `docs/map/SEAM-manifest-x-schools.md` (three
    stale rows), `docs/map/SEAM-harness-x-workflow.md`,
    `docs/map/SEAM-llm-x-manifest.md`, `docs/map/SEAM-llm-x-workflow.md`
    (four checks), `docs/map/SEAM-rules-x-workflow.md` (two checks,
    including the Trap entry documenting R2's own defect, rewritten
    FIXED), `docs/map/SEAM-scratch-x-workflow.md` — all updated in the
    same commits as the code that moved them.
11. [x] **Root sweep** — `python tools/root_sweep.py` ran clean: 103
    roots, 11 ERROR (all `UnsupportedRunManifestVersionError`, the
    documented baseline), 84 `valid=True`, 8 `valid=False` (pre-existing
    deliberately-invalid fixtures). No anomaly. Supplemented by a direct
    load of all 106 committed roots (`Harness(root, read_only=True)`)
    with zero exceptions, which is what caught and proved the fix for
    step 9's critical regression in the first place.
12. [x] **Full gate** — `python -m pytest tests/ -q -n 4`: 3539 passed, 7
    skipped, 1 failed (`test_bronze_report.py::
    test_census_totals_internally_consistent` — the documented
    pre-existing baseline failure). No MCP-thread flakes surfaced this
    run. 0 unexplained failures.
13. [x] **`docs_verify` full** — 3 failed, all `CON-run-identity.md`
    (the documented pre-existing shallow-clone baseline). 0 unexplained.
14. [x] **`[COMMIT]` checkpoint 2** — folded into step 9's three commits;
    all pushed to `origin/claude/v6-defended-trial-wiring-07hs1u`.
15. [x] **R6 guarded live attempt** — NOT ATTEMPTED: no
    `OLLAMA_API_KEY`/provider credentials are available in this
    container (checked `env` and every `experiments/*/env` handover
    path; none present). Per REQUEST.md R6's own text, "the offline
    regression (R5) remains the proof either way" — R5 stands as the
    proof. Recorded honestly as not attempted, not as INCONCLUSIVE (that
    status is for an attempted run where no trial happened to fire).
16. [x] **R10 errata check** — no committed document was found claiming
    defended_trial already worked on v6; every map document that
    mentioned the (then-true) refusal was corrected in the SAME commit
    as the code that made it stop being true (steps 9-10), which is
    ordinary map maintenance per CLAUDE.md's own convention, not an
    errata situation. `docs/ERRATA.md` tail re-read (through E24); no
    entry needed; next free number would be E25 if one ever is.
17. [x] **dr-validate-change** — VALIDATION.md written, PASS.
18. [x] **dr-deliver-change** — DELIVERY.md written, R-by-R
    reconciliation, PROOF pasted, final commit and push.
