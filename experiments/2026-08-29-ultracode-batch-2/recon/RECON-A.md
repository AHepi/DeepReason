# RECON-A — LANE A — CHECKPOINT HARDENING (P2 law, limbs 2 and 3)

Read-only reconnaissance, batch 2, produced before any lane work. Every claim cites file:line.

## Summary

Reconnaissance only; nothing was modified. The operator's 2026-08-29 P2 law (CLAUDE.md:519-535) has three limbs. Limb one is HALF shipped, not whole: token-meter exhaustion already terminates cleanly as `budget_exhausted` with a typed, resumable STOPPED receipt, but the reservation-denial half that P2 was actually opened about — `WorkBudgetDenied` — still escapes to `operational_failure`, and two committed roots prove it at HEAD. Limb two (A1) fails on 16 of 59 committed roots: every failure terminal writes the complete checkpoint FILE set (checkpoint.json, workflow-checkpoint.json, run-stop.json, REPLAY_VALIDATION.json, run-result.json, progress.jsonl) yet records no STOPPED lifecycle receipt, so `prepare_continuation` refuses `CONTINUE_TYPED_STOP_REQUIRED` — demonstrated end-to-end on two of them. Limb three (A2) is wholly unimplemented: neither `continue` nor `amend` consults the replay verdict at all. 16 of 59 committed roots pass `amend`'s exact gate while their own published `REPLAY_VALIDATION.json` says `valid: false`, and two of them were driven through `prepare_continuation` on copies and ACCEPTED. Worse for the design: on 4 of those 16 the stored verdict is not even tamper-evident — forging `valid: true` into `REPLAY_VALIDATION.json` moved nothing, because `derive_terminal_authority` skips `_validate_result_projection_binding` whenever the published result equals the fail-closed pending projection. Cost of the alternative is measured: `verify_root` takes 15.2 s on a 300-event root and 146.7 s on a 3 751-event root.

## Facts

- **The P2 law's three limbs are stated verbatim in CLAUDE.md and this lane owns limbs two and three.**
  - CLAUDE.md:527-535 — "a budget denial on an exhausted budget terminates as `budget_exhausted` (clean), never `operational_failure`; EVERY terminal — clean or failed — must leave checkpoints sufficient for relaunch, and a stop that cannot assure continuability is itself a defect (a \"corrupted stop\"); and `continue`/`amend` are gated on the record verifying intact — a run whose record fails replay validation or carries unresolved containment-breach evidence is REFUSED continuation with a typed refusal. Security boundary, not a convenience: tampering with a record must not buy a resumable run."

- **The operator's own words for the law are recorded verbatim and include the security clause this lane must satisfy.**
  - CLAUDE.md:521-526 — "clean stop. with an assurance that continuing is possible. Too often an operational failure overlooks securing enough checkpoints to allow relaunches or forgets to ensure continuing is possible that trigger corrupted stops. On that note, checkpoints need to be hardned. I don't want a jailbroken run to be continuable."

- **LIMB ONE, the half that DID ship: a budget-exhausted stop is typed as clean and declared resumable, decided by an owner ruling on 2026-07-27 — an earlier lifecycle tranche, not this one.**
  - src/deepreason/workflow/lifecycle.py:25-28 — "# Owner decision 4a (2026-07-27): a budget-exhausted public run is a typed,\n# quiescent stop and continues under a fresh explicit budget, exactly like a\n# converged one.  Failure terminals stay non-resumable.\nRESUMABLE_STOP_REASONS = frozenset({\"converged\", \"budget_exhausted\"})"

- **LIMB ONE mechanism, shipped: token-meter exhaustion breaks the cycle loop rather than crashing, and the absent scheduler reason defaults the terminal to budget_exhausted.**
  - src/deepreason/scheduler/scheduler.py:3205-3207 — "except TokenBudgetExceeded as e:\n                # Budget exhaustion is a logged stop, never a crash: state is\n                # consistent (Adj runs inside every registration)." and src/deepreason/application/text_runs.py:393-397 — "scheduler_reason = result.get(\"stop_reason\")\n    stop_reason = (\n        \"operator_cancelled\"\n        if cancelled\n        else scheduler_reason or \"budget_exhausted\"\n    )"

- **LIMB ONE mechanism, shipped: an exhaustion terminal records a typed STOPPED lifecycle receipt so the stop is continuable, and records a typed refusal when it cannot.**
  - src/deepreason/application/text_runs.py:407-412 — "if stop_reason == \"budget_exhausted\":\n            # A typed STOPPED lifecycle receipt makes the exhaustion a\n            # continuable terminal (owner decision: budget stops on public\n            # runs are resumable).  A root that cannot take the receipt (no\n            # owned control plane, unfinished workflow authority) keeps the\n            # bare fail-closed stop AND records why" — the call is at :414-416, `stop, lifecycle_refusal = _record_exhaustion_lifecycle_stop(...)`

- **LIMB ONE, the half that did NOT ship: P2's own question was about a WorkBudgetDenied reservation denial, and the tranche that surfaced it deliberately did not change which terminal such a run reaches.**
  - experiments/2026-08-28-fix-swallowed-terminal-lifecycle-refusal/P2_OPERATOR_DECISION.md:9-11 — "**When a run's token budget denies a work reservation, is that an OPERATIONAL FAILURE — or is it just the budget running out?**" and :91-93 — "Tranche 1 stopped a REFUSAL being swallowed. It did not change which terminal any run reaches"

- **MEASURED AT HEAD: the WorkBudgetDenied half is still unfixed — two committed roots ended `failed` / `operational_failure` with `error_type: WorkBudgetDenied`.**
  - experiments/2026-08-24-change-rung7-wounds-falls-succession/run/run-status.json — state `failed`, stop_reason `operational_failure`, message "token budget denied transactional work sha256:55c2af9e..."; run-result.json error_type `WorkBudgetDenied`. Same shape at experiments/2026-08-22-change-epoch3-second-lineage/failed-attempt2-run-bb045538.../run-status.json. Probe output recorded this session.

- **The denial is raised only after a durable typed terminal is appended, which is why P2's evidence favours the clean-stop reading.**
  - src/deepreason/workflow/transaction.py:691-692 — "class WorkBudgetDenied(RuntimeError):\n    \"\"\"Raised after a durable ``budget_denied`` terminal was appended.\"\"\"" and src/deepreason/workflow/transaction_service.py:402 — "raise WorkBudgetDenied(terminal) from error"

- **The closed stop-reason vocabulary is seven literals in one place.**
  - src/deepreason/runtime/stop.py:16-24 — "StopReason = Literal[\n    \"completed\",\n    \"converged\",\n    \"stuck\",\n    \"budget_exhausted\",\n    \"operator_cancelled\",\n    \"operational_failure\",\n    \"workload_terminal\",\n]"

- **Only three of those seven are ever emitted by the deterministic StopController; `workload_terminal` has no producer anywhere in src/.**
  - src/deepreason/runtime/stop.py:184 `return StopDecision(stop=True, reason="completed")`, :188 `reason="converged"`, :209 `reason="stuck"`; `grep -rn "workload_terminal" --include=*.py src/` returns exactly one line, src/deepreason/runtime/stop.py:23, the Literal member itself.

- **There is ONE terminalization function; every configuration path that runs the scheduler ends there.**
  - src/deepreason/application/text_runs.py:364 `def terminalize_text_run(` with docstring at :375-377 — "Every configuration path that runs the scheduler ends here, because a second copy of this sequence is a second copy that drifts"

- **TERMINAL PATH 1 — scheduler-decided stop (`completed`/`converged`/`stuck`): the receipt is written by the scheduler, and terminalize_text_run then reads the file the scheduler wrote.**
  - src/deepreason/scheduler/scheduler.py:3165-3169 calls `self._record_stop(decision, metrics, controller_state_before)`; `_record_stop` at :3058 builds the STOPPED lifecycle via `build_stopped_lifecycle` (:3107) and persists at :3126 `persist_stop_record(self.harness.root, stop_record)`. src/deepreason/application/text_runs.py:398-399 — "if scheduler_reason and not cancelled:\n        stop = json.loads((root / \"run-stop.json\").read_text())"

- **TERMINAL PATH 2 — budget exhaustion with no scheduler reason: typed STOPPED receipt attempted, bare stop written if refused.**
  - src/deepreason/application/text_runs.py:402-435 — the `else:` branch, `if stop_reason == "budget_exhausted": stop, lifecycle_refusal = _record_exhaustion_lifecycle_stop(...)`, then `if stop is None:` writes the bare `write_stop_record(root, reason=stop_reason, ...)`

- **TERMINAL PATH 3 — operator cancellation: reason is forced to `operator_cancelled`, which is NOT in RESUMABLE_STOP_REASONS, and it never takes the exhaustion branch.**
  - src/deepreason/application/text_runs.py:394-397 — `stop_reason = ("operator_cancelled" if cancelled else scheduler_reason or "budget_exhausted")`; :407 gates the typed receipt on `stop_reason == "budget_exhausted"` only

- **TERMINAL PATH 4 — interrupted terminalization recovered: a durable stop with no commitment is REUSED, never re-written.**
  - src/deepreason/application/text_runs.py:400 — `elif (recovered := _recoverable_typed_stop(harness, root)) is not None:` with `_recoverable_typed_stop` defined at :326 — "This root's own typed stop, when one was recorded but never committed."

- **TERMINAL PATH 5 — worker exception before any harness exists: NO stop record, NO checkpoint, only run-result.json.**
  - src/deepreason/application/text_runs.py:1521-1524 — "except (Exception, SystemExit) as error:\n            if harness is None:\n                try:\n                    _atomic_json(\n                        root / \"run-result.json\", ..." — the branch returns at :1548 with `stop_reason="operational_failure"` on progress and writes no run-stop.json and no checkpoint.json

- **TERMINAL PATH 6 — worker exception after the terminal commitment already exists: the run reports failure and writes nothing more.**
  - src/deepreason/application/text_runs.py:1552-1566 — "if harness.workflow_state.current_terminal_commitment is not None:" ... `message="TERMINAL_PUBLICATION_RECOVERY_REQUIRED", stop_reason="operational_failure"` then `return`

- **TERMINAL PATH 7 — the ordinary worker failure: a full checkpoint set IS written, but through `write_stop_record` with NO lifecycle transition, so no STOPPED receipt exists.**
  - src/deepreason/application/text_runs.py:1573-1600 — `harness.record_measure(inputs=["run-stop", ..., "operational_failure", ...])`, `stop = write_stop_record(root, reason="operational_failure", ...)`, `_atomic_json(root / "checkpoint.json", {...})`, `payload = finalize_terminal_result(harness, manifest, payload)` — `build_stopped_lifecycle` is never called on this path

- **TERMINAL PATH 8 — `finalize_stopped_root`, the repair for a root that ran and never wrote a terminal; it appends and refuses to republish.**
  - src/deepreason/application/text_runs.py:583 `def finalize_stopped_root(root: Path | str) -> dict[str, Any]:` with :618-622 — "if authority.current_valid:\n        raise ValueError(\n            \"FINALIZE_ALREADY_TERMINAL: this root already stands at a valid typed terminal stop\"" and :623-628 `FINALIZE_AUTHORITY_UNAVAILABLE` for any status other than `current_open_uncommitted`

- **CONTINUE's precondition is a typed STOPPED receipt or an open resume decision; a stop reason alone is never enough.**
  - src/deepreason/runtime/continuation.py:363-364 — "else:\n        raise ValueError(\"CONTINUE_TYPED_STOP_REQUIRED\")" — reached when `terminal is None and current_resume is None` (:218-220 read `harness.workflow_state.terminal_lifecycle_decision` and `.current_resume_decision`)

- **CONTINUE's second precondition is the resumable-reason set, enforced inside the lifecycle builder.**
  - src/deepreason/workflow/lifecycle.py:299-300 — "if terminal.deterministic_decision.reason not in RESUMABLE_STOP_REASONS:\n        raise ValueError(\"terminal stop reason does not authorize continuation\")" — wrapped by continuation.py:294-295 into `CONTINUE_NOT_AUTHORIZED: {error}`

- **AMEND's ONLY terminal precondition is `derive_terminal_authority(...).current_valid` — it consults no replay verdict and no stop reason.**
  - src/deepreason/amendment/apply.py:111-115 — "def _require_terminal_stop(root: Path, manifest) -> None:\n    from deepreason.runtime.terminal_authority import derive_terminal_authority\n\n    authority = derive_terminal_authority(root, manifest=manifest)\n    if authority.current_valid:\n        return" ; called once at :416 `_require_terminal_stop(root, parent_manifest)`

- **CENSUS POPULATION: 59 committed run roots, all schema v6, all under experiments/. (`git ls-files | grep run-status.json` returns 60; one is the loose evidence file experiments/2026-08-21-fix-wheel-smoke-reason-stage/evidence/run-e9d4bb16-run-status.json, not a root.)**
  - Census run this session over `git ls-files`-tracked `*/run-status.json` parents, via deepreason.application.results.results_summary: population 59, schema_version {'6': 59}. Saved at /tmp/claude-0/-home-user-DeepReason/b8393a97-3019-567c-8c83-f06948695f48/scratchpad/census.json

- **CENSUS — the (state, stop_reason, amend_ready) triples over all 59 roots.**
  - Census output: ('completed','budget_exhausted',True) 23; ('failed','operational_failure',False) 16; ('completed','budget_exhausted',False) 13; ('running',ABSENT:NO_STOP_RECORD,False) 4; ('running','budget_exhausted',False) 1; ('completed','converged',True) 1; ('running','operational_failure',False) 1. Totals: amend_ready True 24, False 35.

- **CENSUS — the stored replay verdict across the same 59 roots: 39 valid, 16 INVALID, 4 with no REPLAY_VALIDATION.json.**
  - Census output: `stored verification.valid: {'True': 39, 'False': 16, 'ABSENT:NO_REPLAY_VALIDATION_JSON': 4}`; `verification.source: {'stored': 55, 'ABSENT:...': 4}` — confirming the reader takes the stored path, never a re-derivation, unless asked.

- **CENSUS — the actual amend gate, measured per root: 54 of 59 roots return `current_valid_committed`, 4 return `current_open_uncommitted`, 1 returns `invalid_incomplete`.**
  - derive_terminal_authority probe this session, saved at /tmp/claude-0/-home-user-DeepReason/b8393a97-3019-567c-8c83-f06948695f48/scratchpad/authority.json: authority_status {'current_valid_committed': 54, 'current_open_uncommitted': 4, 'invalid_incomplete': 1}

- **A2 GAP, THE HEADLINE NUMBER: 16 of 59 committed roots pass `amend`'s exact gate while their own published REPLAY_VALIDATION.json says `valid: false`. Twelve of the sixteen also carry a resumable stop reason.**
  - Cross-tab of authority.json: `current_valid=True AND stored_replay_valid=False` -> 16 roots (12 stop_reason budget_exhausted, 4 operational_failure). Listed in full in the probe output; e.g. experiments/live_tri_2026-07-27/run-6dab80d615a437a8b3fa489a279df847 (violations: 4x foreign-criticism) and experiments/2026-08-02-stress-triplet/home-triage/runs/run-0a3e93d6e8031e2e6d1d21dde2fa93cc (violations: attached-evidence).

- **A2 GAP, PROVEN AT THE AMEND GATE: `_require_terminal_stop` raises nothing on a root whose stored verdict is invalid.**
  - Direct probe this session against src/deepreason/amendment/apply.py::_require_terminal_stop on the two roots above: "stored replay valid: False violations: ['foreign-criticism' x4] / _require_terminal_stop: PASSED" and "stored replay valid: False violations: ['attached-evidence'] / _require_terminal_stop: PASSED"

- **A2 GAP, PROVEN END-TO-END AT THE CONTINUE GATE: `prepare_continuation` ACCEPTED two replay-invalid committed roots (on temporary copies; the originals were not touched).**
  - Probe this session: experiments/2026-08-02-stress-triplet/home-triage/runs/run-0a3e93d6e8031e2e6d1d21dde2fa93cc — "stored replay valid: False | violations: ['attached-evidence'] | stop: budget_exhausted / prepare_continuation ACCEPTED a replay-INVALID root; continuation seq = 0"; same result for experiments/2026-08-04-change-rung5-dumb-alternative-backend/rr-home/runs/run-9a6be78e1e79184a0bd89923b957586c (violations: ['attempt-validity'])

- **A2 DESIGN HAZARD: the stored verdict is NOT uniformly tamper-evident. Forging `valid: true` and an empty violations list into REPLAY_VALIDATION.json was DETECTED on 12 of the 16 gap roots and UNDETECTED on 4.**
  - Forge probe this session (saved at .../scratchpad/forge.json): Counter({('invalid_incomplete','False','TERMINAL_REPLAY_VALIDATION_BINDING_MISMATCH'): 12, ('current_valid_committed','True','None'): 4}). The four undetected are run-0a3e93d6e8031e2e6d1d21dde2fa93cc, run-9a6be78e1e79184a0bd89923b957586c, run-e3f4f7007c50fe7e09b301d31851c3e7 and completed-epoch3-run-9175f0ecb055e57455af3c50df153c5a.

- **A2 DESIGN HAZARD, CAUSE LOCATED AND PROVEN: `derive_terminal_authority` skips `_validate_result_projection_binding` entirely whenever the published result equals the fail-closed PENDING projection.**
  - src/deepreason/runtime/terminal_authority.py:782-798 — "pending_result = _pending_terminal_result(expected_result)\n        if result == pending_result:\n            pass\n        elif (\n            result == expected_result\n            and not _public_terminal_projection_required(draft)\n        ):\n            ...\n        else:\n            _validate_result_projection_binding(" ; branch probe this session: run-0a3e93d6 -> "result == pending_result : True ... -> binding validated : False", run-6dab80d6 -> "result == pending_result : False ... -> binding validated : True"

- **A1 GAP, PROVEN: a failure terminal writes EVERY checkpoint file and is still not continuable, because no STOPPED lifecycle receipt exists. 16 of 59 roots are in this state.**
  - Probe this session on copies of experiments/2026-08-24-change-rung7-wounds-falls-succession/run and experiments/live_research_2026-07-29/wide/runs/run-0c3ce902cc5bca75a709b04e2473d100: all six of checkpoint.json, workflow-checkpoint.json, run-stop.json, REPLAY_VALIDATION.json, run-result.json, progress.jsonl present -> "prepare_continuation REFUSED: ValueError CONTINUE_TYPED_STOP_REQUIRED" on both. Census: 16 roots at ('failed','operational_failure'), all with continuation_authority False.

- **A1 — the 16 failed roots ARE amendable even though they are not continuable, because amend's gate ignores the stop reason.**
  - authority.json filter `stop_reason=='operational_failure' and current_valid` -> 16 roots, e.g. experiments/2026-08-13-defect-controller-steering-inert/failed-epoch1-run-8e22d0431fd2b98d and experiments/2026-08-26-pc2-rematch/run. Contrast src/deepreason/workflow/lifecycle.py:299-300, which is what stops `continue`.

- **A1 — 4 roots never reached a terminal at all and are the `finalize` population.**
  - authority.json, authority_status `current_open_uncommitted`: experiments/2026-08-26-pc2-rematch/retired-transport-timeout180-run-42ad288038dd606c, .../retired-truncation-cap32768-run-58fb0d20488be869, experiments/2026-08-26-pc2-rematch/run_h3, experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch4-run-9175f0ecb055e57455af3c50df153c5a. All four lack checkpoint.json, workflow-checkpoint.json, REPLAY_VALIDATION.json and run-result.json.

- **A1 — exactly ONE committed root is genuinely stranded today: neither amendable nor finalizable. This is the operator's "corrupted stop" in the flesh.**
  - authority.json: experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a -> authority_status `invalid_incomplete`, detail_code `TERMINAL_REPLAY_VALIDATION_BINDING_INVALID`, stored_replay_valid True. `amend` refuses AMEND_NOT_AT_TERMINAL (apply.py:128); `finalize` refuses FINALIZE_AUTHORITY_UNAVAILABLE (text_runs.py:623-628, which requires status == current_open_uncommitted).

- **A1 — a SECOND uncovered corrupted-stop path exists in the scheduler: `_record_stop` calls `build_stopped_lifecycle` with no handler for its typed refusal, so a controller-decided stop holding unfinished authority becomes an operational_failure rather than a recorded refusal.**
  - src/deepreason/scheduler/scheduler.py:3107-3121 calls `build_stopped_lifecycle(...)` bare, while src/deepreason/application/text_runs.py:306-313 catches it — "except UnfinishedWorkflowAuthorityError as refused:\n        return None, _refusal(\n            UnfinishedWorkflowAuthorityError.code, str(refused), ...". The type exists at src/deepreason/workflow/lifecycle.py:31-54 with `code = "STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY"`.

- **The READER is already STRICTER than the ACTOR: `deepreason results` refuses to call a replay-invalid root amend-ready, while `amend` accepts it. This is the P6 defect inverted.**
  - src/deepreason/application/results.py:501 — `valid_terminal = bool(replay and replay.get("valid") and has_binding)` and :521-523 — "\"amend_ready\": bool(\n            valid_terminal and resumable is True and authority is True\n        )". Census: all 16 gap roots report amend_ready False, yet all 16 pass derive_terminal_authority.

- **The results reader reads the STORED verdict by default and re-derives only on `--verify`; the stored file is the cheap sufficient check the doc already recommends.**
  - src/deepreason/application/results.py:391-400 — "def _verification(\n    root: Path, replay: dict | None, result: dict | None, *, verify: bool\n) -> dict[str, Any]:\n    \"\"\"The `verify_root` verdict: stored by default, re-derived only on demand.\n\n    Re-deriving replays the whole log, which is O(run length); the stored record is the run's own published verdict" ; CLI flag at src/deepreason/cli/main.py:553-556, help "re-derive the verify_root verdict instead of reading the stored one"

- **COST OF RE-DERIVING, MEASURED: verify_root is 15.2 s on a 300-event root and 146.7 s on a 3 751-event root; verify_root_report is roughly twice that.**
  - Timing probe this session: "run-5a771259557378224bd68591483817be events=  300  verify_root= 15.24s violations=  0  verify_root_report= 28.67s valid=True" and "run  events= 3751  verify_root=146.74s violations=  0  verify_root_report=223.56s valid=True"

- **verify_root's contract: it returns a flat dict of typed findings plus stats, and it writes nothing.**
  - src/deepreason/invariants.py:926-928 — "def verify_root(root: Path, meter_total: int | None = None) -> dict:\n    \"\"\"Run every invariant over the session at ``root``. Returns\n    {\"violations\": [{\"check\", \"detail\"}, ...], \"stats\": {...}}.\"\"\""

- **The report sibling is a separate module and re-channels those findings into five dimensions of which only two decide validity.**
  - src/deepreason/verification/report.py:1135-1148 — "def verify_root_report(\n    root: Path | str,\n    meter_total: int | None = None,\n    *,\n    allow_missing_terminal: bool = False,\n    _include_stored_verification: bool = True,\n) -> VerificationReportV2:" ; :93 `return self.integrity_valid and self.security_valid`. A thin re-export lives at src/deepreason/invariants.py:4451-4459.

- **REPLAY_VALIDATION.json is written by CALLERS out of verify_root's return value, not by the verifier; its schema is `replay-validation.v1`.**
  - src/deepreason/runtime/terminal_authority.py:23 `_REPLAY_VALIDATION_NAME = "REPLAY_VALIDATION.json"` and :1192-1207 `def _fresh_replay_validation(root: Path)` -> `{"schema": "replay-validation.v1", "manifest_digest": ..., "valid": not verification["violations"], "verification": verification}`

- **The stored verdict is bound to the run's terminal by a digest over its own base — which is what makes it tamper-evident where the binding is actually checked.**
  - src/deepreason/runtime/terminal_authority.py:423-425 — "replay_validation_digest=sha256_hex(\n            canonical_json(_replay_validation_base(replay_validation))\n        )" ; validated at :430-453 `_validate_result_projection_binding`, which raises `TERMINAL_REPLAY_VALIDATION_BINDING_MISMATCH` when observed != expected

- **"CONTAINMENT-BREACH EVIDENCE" has no typed record in this repo today. There is no event kind, no verify_root check and no receipt field that records a sandbox escape; the only durable containment identity is the worker source digest, and abort reasons are free-text trace strings.**
  - `grep -rn "containment" --include=*.py src/deepreason/` returns only limit/prefix/abort-string sites: src/deepreason/verification/simulation.py:378 `"sandbox_abort": "worker terminated by resource containment"`, :442 `"trace": {"sandbox_abort": "resource containment"}`, src/deepreason/verification/runner.py:174/185/196/209 similar. The nearest typed structure is the security CHANNEL, whose membership is a closed seven-name set at src/deepreason/verification/report.py:119-129 — "_SECURITY_CHECKS = frozenset(\n    {\n        \"attempt-route\",\n        \"capability-authority\",\n        \"capability-compiled-authority\",\n        \"capability-grant\",\n        \"capability-work-order\",\n        \"frozen-route\",\n        \"school-route\",\n    }\n)" — none of which is about containment.

- **The one containment boundary that IS enforced lives in a single module and is a guard over untrusted source, not a record of a breach.**
  - src/deepreason/sandbox_guard.py:1-2 — "\"\"\"The ONE definition of the untrusted-code attribute boundary." and :91 `def forbidden_attribute(name: str) -> bool:`. The 2026-08-27 escape is written up at docs/map/SUB-verification.md:159-176 and its grant at docs/map/INV-frozen-surfaces.md ("Granted contact, 2026-08-27 — the sandbox attribute boundary (the escape fix)").

- **HOUSE STYLE, refusal #1 (amend): a typed code carried on a ValueError subclass, message formatted `"{code}: {message}"`.**
  - src/deepreason/amendment/state.py:40-46 — "class AmendmentError(ValueError):\n    \"\"\"A typed, durable reason an amendment cannot be read or applied.\"\"\"\n\n    def __init__(self, code: str, message: str):\n        super().__init__(f\"{code}: {message}\")\n        self.code = code"

- **HOUSE STYLE, refusal #1 END-TO-END — definition, raise site, and three tests that assert it.**
  - RAISE: src/deepreason/amendment/apply.py:128-134 — "raise AmendmentError(\n        \"AMEND_NOT_AT_TERMINAL\",\n        \"amendment requires a run standing at a valid typed terminal stop \"\n        f\"(terminal authority is {authority.status}...\". TESTS: tests/test_amendment_epochs.py:420-422 — "with pytest.raises(AmendmentError, match=\"AMEND_NOT_AT_TERMINAL\"):\n        amend_run(root, reshape_question=RESHAPED_QUESTION)\n    assert not (root / \"run-epochs\").exists()"; tests/test_lifecycle_operation_parity.py:254-256 — "assert raised.value.code == \"AMEND_NOT_AT_TERMINAL\"\n    assert \"current_open_uncommitted\" in str(raised.value)"; tests/test_amendment_chain_integrity.py:423-424 — "assert refusal.value.code == \"AMEND_NOT_AT_TERMINAL\"\n    assert \"staged epoch 1\" in str(raised.value)". The code count is pinned at 22 by docs/map/SUB-amendment.md:26.

- **HOUSE STYLE, refusal #2 (continue): a bare `ValueError("CONTINUE_*")`, 19 codes, with a regression test that draws its witnesses from committed roots rather than fixtures — the exact pattern lane A's new tests should copy.**
  - 19 codes by `grep -rohE '"CONTINUE_[A-Z_]+' src/deepreason/runtime/continuation.py | sort -u`. Witness pattern at tests/test_continuation.py:134-166 — "The witnesses are committed roots that really stopped -- today five operational_failure roots, e.g. failed-epoch1-run-9175f0ec -- not fixtures asserting the state into existence." ... "assert str(raised.value) == \"CONTINUE_TYPED_STOP_REQUIRED\"" — and it copies each root to a tempdir first: "# A copy, never the original: prepare_continuation opens a writable Harness before it reaches the refusal, and a committed root is evidence whose contents never change."

- **HOUSE STYLE, a typed refusal that is RECORDED rather than raised — the direct precedent for A1's "corrupted stop" record.**
  - src/deepreason/application/text_runs.py:36 `TERMINAL_LIFECYCLE_REFUSAL_SCHEMA = "deepreason-terminal-lifecycle-refusal-v1"`, built at :222-230 `def _refusal(code, detail, **facts)` returning `{"schema": ..., "code": code, "detail": detail[:2_000], **facts}`, carried onto the terminal at :464 `"terminal_lifecycle_refusal": lifecycle_refusal,` and onto the progress stream at :1517-1519. Its optional progress field is at src/deepreason/runtime/progress.py:63-65 — "# The code of a STOPPED lifecycle receipt this terminal could not take.\n    # Optional with a default, so every progress line written before the field existed still validates"

- **RunResultV2 is `extra="allow"`, which is how `terminal_lifecycle_refusal` rides the terminal without a schema change — the same road is open to a continuability record.**
  - src/deepreason/application/models.py:1200-1207 — "class RunResultV2(BaseModel):\n    \"\"\"Typed v6 terminal envelope; workload-specific fields remain extensible.\"\"\"\n\n    model_config = ConfigDict(extra=\"allow\", frozen=True, strict=True)"

- **The map's own record of why the reader/actor split matters, and the explicit note that P2 was left open by that tranche.**
  - docs/map/SUB-application.md (Traps) — "Note what the fix deliberately does NOT do: it does not let the run continue. Whether unfinished authority ought to block continuation is an open question for the operator (parked P2); this surface only stopped hiding that it does. The reader's rule generalises past this defect — when two verbs answer one question, the reporting verb reads the ACTING verb's own predicate"

- **MAP GAP: docs/map/INDEX.md's subsystem table does NOT list SUB-application.md, SUB-amendment.md or SUB-periphery.md, although all three documents exist — so the mandated map preflight cannot route to the two documents that actually cover this lane.**
  - `grep -n -i "application|amendment|periphery" docs/map/INDEX.md` returns only :46 (SUB-harness "event application"), :54 (SUB-bridge "grounded-application bridge"), :129 and :136 (the periphery x verification seam row). `ls docs/map/` lists SUB-application.md, SUB-amendment.md and SUB-periphery.md.

- **MAP GAP: the seam this lane's work actually joins — application x verification, and amendment x verification — is undocumented on BOTH sides, so the "read the seam before the subsystems" rule has nothing to read.**
  - docs/map/SUB-application.md:6 `Seams-undocumented: application x bridge, application x run-identity, application x scratch, application x verification, application x workflow` and its seam table row — "application x verification | undocumented | plausible: the V6 admission gate (`_admit_v6_root`) refuses a tampered or historical root ... whether it calls into `verify_root` itself or only manifest-level checks is not confirmed here"; docs/map/SUB-amendment.md:6 `Seams-undocumented: ... amendment x verification`

- **The covering map documents that DO exist and their Owns lines, which fix the cone.**
  - docs/map/CON-run-identity.md:4 `Owns: src/deepreason/preparation.py, src/deepreason/application/text_runs.py, src/deepreason/runtime/continuation.py, src/deepreason/runtime/progress.py, src/deepreason/amendment/apply.py, src/deepreason/amendment/models.py, src/deepreason/amendment/state.py, src/deepreason/ui/status.py`; docs/map/SUB-application.md:4 `Owns: src/deepreason/application/, src/deepreason/workflows/, src/deepreason/cli/, src/deepreason/runtime/, ...`; docs/map/SUB-workflow.md:4 `Owns: src/deepreason/workflow/`; docs/map/SUB-verification.md:4 `Owns: src/deepreason/invariants.py, src/deepreason/verification/, src/deepreason/signals_read.py`

- **FROZEN SURFACE 3 covers both files this lane must CONSUME and never edit.**
  - docs/map/INV-frozen-surfaces.md — "### 3. Replay-validation record formats — `invariants.py`, `verification/`\n\n`verify_root` and the epistemic-check report. Their output shape is compared across runs and across time; a format change silently reinterprets every stored verdict."

- **The frozen-surface tripwire the fan-in will run: a negated git-diff check naming all seven paths.**
  - docs/map/INV-frozen-surfaces.md — "`check: ! git diff --name-only origin/main...HEAD | grep -qE \"capabilities/state\\.py|/harness\\.py|/invariants\\.py|/run_manifest\\.py|/qualification\\.py|llm/firewall\\.py\"`"

- **The root sweep is retired as an instrument, so this lane owes no sweep; targeted regression tests on committed roots are the required proof instead.**
  - CLAUDE.md:246-249 — "The root sweep is RETIRED as an instrument (operator ruling 2026-08-22: \"it just wastes time\"). No tranche, gate, audit, or frozen-surface grant may require sweeping committed roots"

- **docs_verify baseline this lane's fan-in must compare against.**
  - docs/AUDIT_BASELINES.md:25-26 — "**docs_verify** (`python tools/docs_verify.py`): **1212 checks over 69 documents; 6 failed on a full clone, 9 on a shallow one.**"


## Files

- `/home/user/DeepReason/CLAUDE.md` (read) — The P2 law verbatim at :519-535 is the tranche's only authority; REQUEST.md must quote it exactly. Also carries the retired-sweep ruling (:246) and the gate discipline.
- `/home/user/DeepReason/src/deepreason/runtime/continuation.py` (read-write) — PRIMARY A2 SITE. `prepare_continuation` (:372) is the only route from a stopped root to a runnable one. The integrity gate belongs immediately after `_assert_amendment_committed(root_path)` at :381 and before the manifest load — the same position and shape as the existing `_assert_*` guards, so the refusal lands before any Harness is opened. Add `CONTINUE_RECORD_NOT_VERIFIED` (name TBD) to the existing 19-code CONTINUE_* vocabulary.
- `/home/user/DeepReason/src/deepreason/amendment/apply.py` (read-write) — PRIMARY A2 SITE. `_require_terminal_stop` (:111-134) is amend's whole terminal precondition and consults no replay verdict. The gate goes here or beside its single call site at :416, as a 23rd AmendmentError code. Note the message-building precedent at :121-134 (it appends a staged-epoch note, so the new refusal should compose the same way).
- `/home/user/DeepReason/src/deepreason/application/text_runs.py` (read-write) — PRIMARY A1 SITE. `terminalize_text_run` (:364) is the ONE terminal route; the four failure emits are at :1521 (no harness), :1552 (commitment exists), :1573-1600 (ordinary failure) and the success path at :1503. The failure path at :1573-1600 writes every checkpoint file but never calls `build_stopped_lifecycle`, which is exactly the A1 gap. `_record_exhaustion_lifecycle_stop` (:232) and `_refusal` (:222) are the shapes to reuse for a typed continuability record. `finalize_stopped_root` (:583) is the existing repair verb.
- `/home/user/DeepReason/src/deepreason/workflow/lifecycle.py` (read-write) — `RESUMABLE_STOP_REASONS` (:28) decides which terminals continue at all; `build_resumed_lifecycle` (:299-300) is where a non-resumable reason is refused; `UnfinishedWorkflowAuthorityError` (:31-54) is the typed refusal A1 must record rather than lose. Any widening of the resumable set is a design fork, not a work item — see stops.
- `/home/user/DeepReason/src/deepreason/application/results.py` (read-write) — The reporting surface must not drift from the new actor predicates. `_terminal` (:484-527) computes amend_ready from valid_typed_terminal + stop_reason_resumable + continuation_authority; `_verification` (:391-448) reads the stored verdict. After the gate lands, this reader must read the ACTING verb's own predicate (the rule SUB-application.md's Traps already states) rather than a second copy of it.
- `/home/user/DeepReason/src/deepreason/runtime/terminal_authority.py` (read) — CONSUME ONLY (owned by DR-SUB-application, but the risk is high). `derive_terminal_authority` (:703) is the predicate both gates rest on; `_fresh_replay_validation` (:1192) shows the exact stored-verdict shape; `_validate_result_projection_binding` (:430) is the tamper check; :782-798 is the branch that SKIPS it. Read before designing which verdict source the gate trusts.
- `/home/user/DeepReason/src/deepreason/invariants.py` (read) — CONSUME ONLY — FROZEN SURFACE 3. `verify_root` at :926 is the function the gate consumes. Any edit here is a STOP.
- `/home/user/DeepReason/src/deepreason/verification/report.py` (read) — CONSUME ONLY — FROZEN SURFACE 3. `verify_root_report` (:1135), `_SECURITY_CHECKS` (:119-129) and the validity rule at :93. Relevant because a containment-breach finding, if one is ever typed, would have to enter through `_SECURITY_CHECKS` — which this lane may NOT edit.
- `/home/user/DeepReason/src/deepreason/runtime/stop.py` (read) — The closed StopReason vocabulary (:16-24) and the three reasons StopController actually emits (:184, :188, :209). Establishes the exhaustive terminal-state list without re-deriving it.
- `/home/user/DeepReason/src/deepreason/runtime/progress.py` (read-write) — `ProgressEvent` (:34-65) is where a typed corrupted-stop code would surface to a watcher, following the `terminal_lifecycle_refusal` precedent at :63-65 (optional with a default, so older progress lines still validate under extra="forbid"). Owned by DR-CON-run-identity and DR-SUB-application; in cone.
- `/home/user/DeepReason/src/deepreason/application/models.py` (read) — `RunResultV2` (:1200-1255) is extra="allow", which is how a new typed record rides the terminal without a schema change. Its `_derived_terminal_fields` validator constrains what may be added.
- `/home/user/DeepReason/src/deepreason/cli/main.py` (read) — `_cmd_amend` (:2648), `_cmd_continue` (:2695), `_cmd_finalize` (:2673) — how each refusal reaches the operator (printed verbatim to stderr, exit 1). Confirms a new typed code needs no CLI change to surface, but the help text at :553-556 documents --verify.
- `/home/user/DeepReason/src/deepreason/scheduler/scheduler.py` (read) — READ ONLY, OUT OF CONE. `_record_stop` (:3058-3130) calls `build_stopped_lifecycle` with no handler for UnfinishedWorkflowAuthorityError — the second corrupted-stop path. `Scheduler.run`'s except clauses (:3169, :3187, :3205) show WorkBudgetDenied is NOT among them. Cite as a stop, do not edit.
- `/home/user/DeepReason/tests/test_continuation.py` (read-write) — Holds the exact test pattern to copy: `_non_resumable_committed_roots` (:93) selects witnesses from committed roots via the product's own constant, and `test_a_stop_with_no_typed_receipt_refuses_continuation` (:134) copies each to a tempdir before asserting the typed refusal. The 12 replay-invalid resumable roots are the new witness set.
- `/home/user/DeepReason/tests/test_lifecycle_operation_parity.py` (read-write) — Owns `_bind_v6_root` (:91), `_launch_through_cli` (:125), `_manifest_launched_root` (:149) and `_open_root` (:155) — the fixtures every lifecycle test in this area reuses, and the home of test_interrupted_run_still_refuses_amend_not_at_terminal (:245).
- `/home/user/DeepReason/tests/test_terminal_lifecycle_refusal_is_recorded.py` (read) — The closest sibling tranche's tests (P6). Its docstring states the exact scope boundary this lane inherits — 'Nothing here asserts that unfinished workflow authority OUGHT to permit continuation — that question is open and belongs to the operator (P2).'
- `/home/user/DeepReason/tests/test_results_command.py` (read-write) — Guards the reader's amend_ready and stored-verdict behaviour (test_verification_reads_the_stored_verdict_and_does_not_replay, test_terminal_readiness_answers_the_amend_question). Both are named in SUB-application.md check lines, so any reader change must move them and the map together.
- `/home/user/DeepReason/tests/test_amendment_epochs.py` (read-write) — Home of test_amendment_refuses_a_run_that_is_not_at_a_terminal_stop (:404) — where a new AMEND integrity refusal test belongs, and the file SUB-amendment.md's 'Which run states may be amended at all' row names.
- `/home/user/DeepReason/tests/test_amendment_chain_integrity.py` (read) — The 22-code AmendmentError inventory is pinned by a docs check that counts them; adding a 23rd code turns docs/map/SUB-amendment.md:26 RED unless that check moves in the same commit.
- `/home/user/DeepReason/docs/map/CON-run-identity.md` (read-write) — THE covering map document: it Owns text_runs.py, continuation.py and all three amendment modules. Its 'The rules it obeys' section already enumerates what `continue` demands (with a `check:` listing six CONTINUE_ codes) — a new precondition must be added there with a check that would fail if the gate regressed.
- `/home/user/DeepReason/docs/map/SUB-application.md` (read-write) — Owns application/ and runtime/. Its 'Where to change what' table has the rows for terminalize_text_run, prepare_continuation and results_summary; its Traps section carries the P6 entry that explicitly parks P2. Must gain the A1/A2 rows and a Traps entry naming this tranche.
- `/home/user/DeepReason/docs/map/SUB-amendment.md` (read-write) — Owns amendment/. Line 26 carries the executable check asserting exactly 22 AmendmentError codes — it must move in the same commit as a 23rd. 'Which run states may be amended at all' is the row to update.
- `/home/user/DeepReason/docs/map/INV-frozen-surfaces.md` (read) — Read BEFORE designing. Surface 3 (invariants.py, verification/) is what this lane consumes and may not touch; the git-diff tripwire at the end of the 2026-08-27 grant is what the fan-in runs.
- `/home/user/DeepReason/docs/map/SUB-verification.md` (read) — States verify_root's contract and that REPLAY_VALIDATION.json is written by callers, not by the verifier — the fact that decides where the gate may read a verdict from.
- `/home/user/DeepReason/docs/map/INDEX.md` (read) — The mandated map preflight entry point. Note it does NOT route to SUB-application.md or SUB-amendment.md (see facts) — record that in the tranche's first artifact rather than concluding the documents do not exist.
- `/home/user/DeepReason/experiments/2026-08-28-fix-swallowed-terminal-lifecycle-refusal/P2_OPERATOR_DECISION.md` (read) — The question the operator was answering, with its own re-derived evidence table (two committed roots, their token spend, and the four-way disposition). REQUEST.md should trace the law back to this brief.
- `/home/user/DeepReason/experiments/2026-08-29-ultracode-batch-2/` (read) — Batch container. SETUP.md holds the measured baselines (origin/main 84514a028, offline by construction, xdist and jsonschema installed by hand) and the binding rule that a parked STOP is pushed at the moment it is parked.
- `/home/user/DeepReason/experiments/2026-08-30-change-checkpoint-hardening/` (new) — The tranche directory: REQUEST.md (the law verbatim, numbered requirements, and the map ids), SPEC.md (per-requirement acceptance checks plus the frozen-surface disposition), CHECKLIST.md, VALIDATION.md, DELIVERY.md, plus proof/ holding the census, the authority probe, the forge probe and the timing measurements this reconnaissance produced.

## Work items

### A0 — MAP PREFLIGHT, recorded in REQUEST.md before any design: resolve the work to DR-CON-run-identity (owns text_runs.py, continuation.py, amendment/), DR-SUB-application (owns application/, runtime/), DR-SUB-amendment (owns amendment/), DR-SUB-workflow (owns workflow/) and DR-SUB-verification (CONSUMED, frozen surface 3). Record that INDEX.md routes to none of application/amendment/periphery and that the application x verification and amendment x verification seams are undocumented on both sides, so no seam could be read before the subsystems.

  DONE-CRITERION: REQUEST.md contains the five DR- ids and the two map gaps, each with its file:line citation; `grep -n -i "application|amendment|periphery" docs/map/INDEX.md` output is pasted verbatim in the artifact.

### A1-1 — Ledger the operator's law verbatim from CLAUDE.md:519-535 into REQUEST.md and split it into numbered requirements, marking limb one as SPLIT: R0a (token-meter exhaustion -> clean resumable stop) SHIPPED and cited; R0b (WorkBudgetDenied -> clean stop) NOT shipped, out of cone, bubbled as a stop.

  DONE-CRITERION: REQUEST.md quotes CLAUDE.md:521-535 byte-for-byte, and its R0a row cites src/deepreason/workflow/lifecycle.py:25-28 and src/deepreason/application/text_runs.py:407-416 while its R0b row cites the two committed roots' run-result.json error_type WorkBudgetDenied.

### A1-2 — Commit the reconnaissance evidence as the tranche's baseline: the 59-root census (state, stop_reason, amend_ready, stored verdict), the derive_terminal_authority probe, the forge probe, and the verify_root timing figures. Every later claim about scope compares against these numbers.

  DONE-CRITERION: proof/ contains census.json, authority.json, forge.json plus the scripts that produced them, and MEASUREMENTS.md states: 59 roots; amend_ready 24/35; stored valid 39/16/4-absent; authority 54 current_valid_committed / 4 current_open_uncommitted / 1 invalid_incomplete; 16 roots current_valid with stored valid=false; 12 of those 16 tamper-evident, 4 not; verify_root 15.2 s @300 events, 146.7 s @3751.

### A1-3 — DECIDE AND RECORD the verdict source for the integrity gate, on the measured fork rather than by assertion. Option A: read the stored REPLAY_VALIDATION.json (cheap, but NOT a security boundary on the 4 roots where _validate_result_projection_binding is skipped). Option B: re-derive verify_root (sound everywhere, 15 s to 147 s per invocation). Option C: read the stored verdict AND require the binding to have been validated, refusing typed when it was not. Price each in SPEC.md against the measured numbers.

  DONE-CRITERION: SPEC.md carries the three-option table with the measured cost and the measured coverage gap for each, names the chosen option, and states what the choice does NOT protect against. The 4 undetected roots are listed by path.

### A2-1 — Implement the CONTINUE integrity gate in prepare_continuation, positioned with the other fail-closed preconditions (immediately after _assert_amendment_committed at continuation.py:381), raising a new CONTINUE_* code in the house style — a bare ValueError whose whole message is the code, or code plus colon plus detail, matching the existing 19.

  DONE-CRITERION: `python -c "import pathlib; s=pathlib.Path('src/deepreason/runtime/continuation.py').read_text(); assert 'CONTINUE_RECORD_NOT_VERIFIED' in s"` exits 0 (name as chosen in SPEC.md), and a test drives prepare_continuation on a COPY of experiments/2026-08-02-stress-triplet/home-triage/runs/run-0a3e93d6e8031e2e6d1d21dde2fa93cc and asserts the new code where it today returns `continuation seq = 0`.

### A2-2 — Implement the AMEND integrity gate at or beside _require_terminal_stop (apply.py:111-134/:416) as a 23rd AmendmentError code, composing its message the way that function already composes the staged-epoch note.

  DONE-CRITERION: `python -c 'import re,pathlib; d=pathlib.Path("src/deepreason/amendment"); codes=set(); [codes.update(re.findall(r"AmendmentError\(\s*\"([A-Z][A-Z_]+)\"", (d/n).read_text())) for n in ("apply.py","state.py","models.py")]; assert len(codes)==23'` exits 0, and a test asserts `raised.value.code` is the new code when `_require_terminal_stop` is called on a copy of a replay-invalid root that today PASSES.

### A2-3 — Move docs/map/SUB-amendment.md:26's count check from 22 to 23 IN THE SAME COMMIT as A2-2, and add the new precondition to CON-run-identity.md's `continue` rule (whose existing check enumerates six CONTINUE_ codes) with a check that would go red if the gate were removed.

  DONE-CRITERION: `python tools/docs_verify.py` shows the same failure set as docs/AUDIT_BASELINES.md:25-26 (6 full-clone / 9 shallow) with delta ZERO, and the two edited documents' own check lines run green by hand.

### A2-4 — MUTATION PROOF for both gates: run each new regression RED on the unfixed tree before the fix lands, and record the RED output. One mutation per test, per the batch's own standard.

  DONE-CRITERION: proof/ holds the pre-fix RED output for every new test, each showing the assertion that fails and why; the same tests pass at HEAD.

### A2-5 — Add the WITNESS-BASED regression in the tests/test_continuation.py pattern: select the witness roots from the record itself (stored verdict false AND stop reason in RESUMABLE_STOP_REASONS) rather than from a hard-coded list, guard with `assert witnesses` so a shrinking population trips the test instead of silently emptying it, and copy each root to a tempdir before touching it.

  DONE-CRITERION: The new test collects >= 12 witnesses today, fails loudly if the set empties, and every committed root it touches is byte-identical after the run (`git status --short experiments/` empty).

### A1-4 — A1, the corrupted-stop RECORD: make every terminal that cannot assure continuability say so on the record, following the deepreason-terminal-lifecycle-refusal-v1 precedent (a typed dict on run-result.json plus a code on ProgressEvent). Cover the ordinary worker failure path (text_runs.py:1573-1600), which today writes a complete checkpoint set and no receipt, and the no-harness path (:1521), which writes neither.

  DONE-CRITERION: A test drives a run to each failure terminal and asserts run-status.json and run-result.json both carry the typed continuability record with its code; `deepreason results <root>` prints it rather than reporting a bare operational_failure.

### A1-5 — A1, the SCHEDULER-side corrupted stop: record, do not fix here. `_record_stop` (scheduler.py:3107) calls build_stopped_lifecycle with no handler for UnfinishedWorkflowAuthorityError, so a controller-decided stop holding unfinished authority becomes an operational_failure with no trace of the refusal — the same defect P6 fixed on the exhaustion path only. scheduler/ is outside the granted cone.

  DONE-CRITERION: PARKED.md carries the finding with its file:line citation, the contrast against text_runs.py:306-313, and a ready-to-send fix prompt naming the cone it would need.

### A1-6 — A1, the RECONCILIATION the census forces: state in SPEC.md, per bucket, what 'checkpoints sufficient for relaunch' means for each of the four populations — 24 amend-ready roots (nothing owed), 16 failed roots with a full file set and no STOPPED receipt (continue impossible, amend possible), 4 roots with no terminal (finalize is the repair), and 1 stranded root that neither verb can touch. Say for each whether this tranche closes it or parks it.

  DONE-CRITERION: SPEC.md carries the four-bucket table with exact counts and named example roots, and every bucket has an explicit CLOSED or PARKED disposition with its reason.

### A1-7 — Verify the one stranded root by name and record it as the concrete instance of the operator's 'corrupted stop': experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a, authority invalid_incomplete / TERMINAL_REPLAY_VALIDATION_BINDING_INVALID, refused by amend (AMEND_NOT_AT_TERMINAL) and by finalize (FINALIZE_AUTHORITY_UNAVAILABLE requires current_open_uncommitted).

  DONE-CRITERION: A committed probe re-derives that root's authority status and detail code on demand, and RESULTS.md names it as the recorded instance.

### A1-8 — Reconcile the reader with the new actors: after the gates land, results.py's amend_ready must read the ACTING verbs' predicates rather than a second copy, per the rule SUB-application.md's Traps already states. Today the reader is STRICTER than the actor (it refuses the 16 replay-invalid roots the actor accepts) — that inversion must not survive as a second silent disagreement.

  DONE-CRITERION: A test asserts, over the committed roots, that `results_summary(root)['terminal']['amend_ready']` is True exactly where both `_require_terminal_stop` and `prepare_continuation`'s preconditions would pass — no root where the two surfaces disagree.

### Z-1 — Ring, then boundary. Iterate on tests/test_continuation.py, test_amendment_epochs.py, test_lifecycle_operation_parity.py, test_results_command.py, test_terminal_lifecycle_refusal_is_recorded.py; run the full gate only at the phase boundary, with --lf where a prior run exists.

  DONE-CRITERION: `python -m pytest tests/ -q -n 4` reports 0 failed at the fan-in, and the ring-vs-gate invocation counts are recorded in VALIDATION.md.

### Z-2 — Frozen-surface disposition BEFORE any code: run tools/blast_radius.py over the declared file cone and paste its own frozen_surface_contacts rows into SPEC.md, disposing each one by one. This lane expects ZERO contact — it consumes verify_root and edits nothing inside surface 3.

  DONE-CRITERION: `git diff --name-only origin/main...HEAD | grep -qE "capabilities/state\.py|/harness\.py|/invariants\.py|/run_manifest\.py|/qualification\.py|llm/firewall\.py"` returns NOTHING, and SPEC.md carries the blast-radius verdict verbatim.


## Risks

- THE BRIEF'S PREMISE IS HALF WRONG, AND THE LANE MUST NOT INHERIT IT. Limb one is shipped only in the narrow reading (token-meter exhaustion). The reservation-denial half that P2 was actually opened about is unfixed at HEAD: two committed roots end `failed`/`operational_failure` with `error_type: WorkBudgetDenied`. If the tranche writes 'limb one already shipped' without that qualification it records a false claim about the record.
- THE STORED VERDICT IS NOT A UNIFORM SECURITY BOUNDARY. Reading REPLAY_VALIDATION.json['valid'] is the cheap gate, and on 12 of the 16 measured roots it is genuinely tamper-evident (forging valid:true yields TERMINAL_REPLAY_VALIDATION_BINDING_MISMATCH). On 4 it is not, because derive_terminal_authority skips _validate_result_projection_binding whenever the published result equals the pending projection (terminal_authority.py:782-798). A gate built on the stored verdict alone satisfies the law's letter and not its security clause ('tampering with a record must not buy a resumable run').
- RE-DERIVING IS SOUND AND EXPENSIVE. verify_root costs 15.2 s on a 300-event root and 146.7 s on a 3 751-event root, and `continue` runs inside a launch the operator is watching. A gate that always re-derives adds minutes to every resume; a gate that never re-derives is defeatable on some roots. The measured middle road (stored verdict PLUS a requirement that the binding was validated) is the option the SPEC must price rather than assume.
- THE READER/ACTOR INVERSION IS EASY TO MAKE WORSE. results.py already refuses to call a replay-invalid root amend-ready while amend accepts it. Fixing only the actor leaves them agreeing by accident; fixing only the reader repeats the exact P6 defect in mirror image. SUB-application.md's Traps states the rule — the reporting verb reads the acting verb's own predicate — and a second copy of the predicate is the failure mode.
- ADDING AN AmendmentError CODE TURNS A MAP CHECK RED. docs/map/SUB-amendment.md:26 asserts `len(codes)==22`. It must move in the same commit, or docs_verify's baseline delta is nonzero at fan-in and the batch cannot tell a rotted check from this lane's own.
- WIDENING RESUMABLE_STOP_REASONS IS NOT A WORK ITEM. It is the single line (workflow/lifecycle.py:28) that decides whether a failed run may resume, set by an owner ruling on 2026-07-27 whose comment explicitly says 'Failure terminals stay non-resumable.' A1's text ('EVERY terminal — clean or failed — must leave checkpoints sufficient for relaunch') is readable as requiring that widening. Read it that way and you overturn an owner decision inside a defect tranche.
- TESTS THAT ASSERT STATE INTO EXISTENCE PROVE NOTHING HERE. The gap is measured on committed roots, so fixtures that synthesise a replay-invalid root can pass while the real population is untouched. tests/test_continuation.py:93-131 already solved this: select witnesses from the record, guard with `assert witnesses`, and copy before touching. Copy that shape, not a fixture.
- COMMITTED ROOTS ARE EVIDENCE AND prepare_continuation WRITES. It opens a writable Harness, appends a RESUMED transition and writes continuations.jsonl before it can refuse. Every probe and every test must copy to a tempdir first; this reconnaissance did, and `git status experiments/` is clean.
- THE MAP PREFLIGHT CANNOT BE PERFORMED AS WRITTEN. INDEX.md routes to neither SUB-application.md nor SUB-amendment.md, and the seam this work joins (application x verification, amendment x verification) is undocumented on both sides. Following the stated rule literally yields 'no covering document' and the wrong conclusion; record the gap instead of concluding the documents are absent.
- CONTAINMENT-BREACH EVIDENCE HAS NO TYPED FORM TO GATE ON. The law names it, and the repo has no event kind, no verify_root check and no receipt field recording one — only free-text `sandbox_abort` trace strings and the worker-source digest. Building the typed form means entering _SECURITY_CHECKS in verification/report.py, which is frozen surface 3 and not granted. That half of limb three cannot be closed inside this cone; it can only be gated on what verify_root already reports.
- A SECOND CORRUPTED-STOP PATH SITS OUTSIDE THE CONE. scheduler.py:3107 calls build_stopped_lifecycle bare, so a controller-decided stop holding unfinished authority still becomes an untyped operational_failure — the exhaustion path's fix at text_runs.py:306-313 was never mirrored there. Closing A1 only in application/ leaves the same defect live one layer down.
- OFFLINE BY CONSTRUCTION. SETUP.md records no OLLAMA_API_KEY and no env file anywhere in this batch, so no live-run evidence is available and none may be claimed. Every number this lane reports must come from committed roots or offline probes.

## Stops (bubble, never resolve in-batch)

- FROZEN SURFACE 3 — src/deepreason/invariants.py and src/deepreason/verification/. This lane CONSUMES verify_root and may not edit either file. If the chosen design needs a new finding, a new check name, a _SECURITY_CHECKS member, or any change to the verdict's shape, that is a STOP requiring a written grant in SPEC.md before code, with tools/blast_radius.py's own contact rows pasted and disposed one by one — the discipline INV-frozen-surfaces.md records for the seven prior grants.
- LIMB ONE'S UNFIXED HALF — WorkBudgetDenied still terminates as operational_failure at HEAD. The fix lives in src/deepreason/scheduler/scheduler.py and src/deepreason/workflow/, both OUTSIDE the granted cone (application/text_runs.py, application/results.py, workflow/lifecycle.py, amendment/, tests, map). P2_OPERATOR_DECISION.md already prices both roads. BUBBLE, with the two committed roots as evidence; do not implement it inside this lane.
- DESIGN FORK, OPERATOR-LEVEL — does A1 require widening RESUMABLE_STOP_REASONS so failure terminals become resumable? The law says every terminal, clean or failed, must leave checkpoints sufficient for relaunch. Today 16 committed roots hold a complete checkpoint set and cannot be continued, by an owner decision of 2026-07-27 whose comment reads 'Failure terminals stay non-resumable.' Overturning that is an operator call, not a tranche's. Park with the census numbers and the two readings stated plainly.
- DESIGN FORK, MONITOR-LEVEL — which verdict source the integrity gate trusts. The measured facts are that the stored verdict is tamper-evident on 12 of 16 gap roots and not on 4, and that re-deriving costs 15 s to 147 s. Option C (stored verdict plus a requirement that the binding was validated) is a genuinely different security posture from Option A, not an implementation detail. Get the disposition in writing in SPEC.md BEFORE the gate is written.
- THE SECOND HALF OF LIMB THREE IS UNBUILDABLE IN THIS CONE — 'unresolved containment-breach evidence' names a record type that does not exist. There is no typed containment-breach event, no verify_root check for one, and no receipt field carrying one; creating it means entering frozen surface 3. Report as a STOP with the searched vocabulary (sandbox_abort trace strings, CONTAINED_WORKER_SHA256, the closed seven-name _SECURITY_CHECKS set) so the operator can decide whether to open a separate tranche or to scope limb three to replay validity alone.
- SCHEDULER-SIDE CORRUPTED STOP — scheduler.py:3107 calls build_stopped_lifecycle with no handler for UnfinishedWorkflowAuthorityError. Same defect class as the P6 fix, one layer down, outside the cone. PARK with a ready-to-send prompt.
- MAP GAP, LANE D TERRITORY — docs/map/INDEX.md's subsystem table omits SUB-application.md, SUB-amendment.md and SUB-periphery.md, so the mandated preflight cannot route to the two documents covering this lane; and the application x verification / amendment x verification seams are undocumented on both sides. Do not fix INDEX.md inside this tranche without a grant; record it, and hand it to the lane that owns map repair.
- P2'S OWN SECOND QUESTION IS STILL OPEN AND THE 2026-08-29 LAW DOES NOT ANSWER IT — whether UNFINISHED WORKFLOW AUTHORITY ought to block continuation. SUB-application.md's Traps and tests/test_terminal_lifecycle_refusal_is_recorded.py's docstring both park it explicitly. The operator's ruling settles the budget-denial question; it says nothing about STOPPED_REFUSES_UNFINISHED_WORKFLOW_AUTHORITY. If a work item starts to depend on that answer, STOP and ask rather than infer it from the law's wording.
- DIFF BUDGET — both withheld lanes of batch 1 stopped on tools/diff_budget.py EXCEEDED, and BATCH.md records that as a stop decided above the lane. This lane touches five source files, two map documents and at least five test files; declare the ceiling in SPEC.md and run the gate at every [COMMIT] step rather than discovering the overshoot at delivery.
