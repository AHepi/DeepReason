# Diagnosis: crash-recovery re-checks EVERY admitted criticism work item, including already-completed atomic decomposition children, through a handler built only for the batch payload shape

Primary cause: `Scheduler._recover_workflow_prefixes` (`src/deepreason/
scheduler/scheduler.py:303-377`), the very first action `Scheduler.run`
takes on every invocation including a `continue`, builds
`admitted_effect_candidates` from EVERY `transaction_work` item whose
`task_kind` is `CRITICISM` or `SCRATCH_AUTHORING` and whose current
attempt has an admitted admission (lines 311-324) — with no check of
whether that item's `terminal` is already set, and no check of
whether it is a BATCH item or an ATOMIC CHILD of a contract
decomposition. Every such item that is not `WorkflowTaskKind.CONJECTURE`
is then dispatched (lines 362-372) to `recover_nonconjecture_admission`
(`workflow/nonconjecture_recovery.py`), which for `task_kind ==
CRITICISM` routes UNCONDITIONALLY (lines 1028-1032) to
`_criticism_contract` (line 643) — a handler whose very first line
(644) asserts `payload.get("schema") == "criticism.semantic-task.v1"`,
the BATCH shape only. An atomic child's own preparation carries
`contract_id == "critic.atomic-target.v1"` and
`task_payload_value["schema"] == "contract-decomposition-child.v1"`,
which fails that assertion immediately and raises
`NonConjectureRecoveryAuthorityError("unknown critic task")` — even
though the item is ALREADY fully completed and needs no recovery
action at all. `atomic_recovery.recover_atomic_child_output` is the
function that DOES know how to read an atomic child's shape (it is
what the ordinary live dispatch path, `rules/crit.py:344-346,582-584`,
calls), but nothing in `_recover_workflow_prefixes`'s CONJECTURE/else
branch ever reaches it.

Evidence:
- `experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/
  failed-epoch1-run-8c77c6588485304d1f73416318c62949/run-status.json`
  -> `{"message":"unknown critic task","phase":"stop","state":"failed",
  "stop_reason":"operational_failure",...}` — matches the exact string
  raised by `nonconjecture_recovery.py:644`, confirming which
  `_authority` check fired (non-code, record evidence).
- Same root's `log.jsonl`, replayed read-only (`Harness(root,
  read_only=True).workflow_state`): exactly ONE
  `contract_decomposition_activated`/`_completed` pair (seqs 47, 64);
  its two child work items
  (`sha256:82f77c8...17f9`, `sha256:25a6793...eb13`) both show
  `task_kind=WorkflowTaskKind.CRITICISM`,
  `contract_id="critic.atomic-target.v1"`,
  `task_payload_value["schema"]="contract-decomposition-child.v1"`,
  `provider_attempts[0].outcome="provider_result"`,
  `admissions[0].outcome="admitted"`, AND `terminal.status="completed"`
  with `reason_code="atomic_critic_output_admitted"` — i.e. BOTH are
  already fully resolved, yet both satisfy
  `_recover_workflow_prefixes`'s `admitted_effect_candidates` filter
  exactly (task_kind + admitted admission; the filter never reads
  `item.terminal`).
- The log's own tail (seqs 1173-1178) shows the causal order directly:
  1173 `lifecycle_stopped` / 1174 `terminal_committed` (the ORIGINAL
  clean `budget_exhausted` stop) -> 1175 `lifecycle_resumed` (the
  `continue` command's own resume decision, committed successfully) ->
  1176 `Measure run-resume` -> 1177 `Measure run-stop` (reason
  `operational_failure`, matching `run-status.json`'s message) -> 1178
  `terminal_committed` (the new FAILED terminal). `Scheduler.run`
  calls `_recover_workflow_prefixes()` as literally its first
  statement (`scheduler.py:2739`), immediately after the resume
  decision lands — the crash happens inside that first call, before
  any new cycle runs.

Implicated code (max 3 sites, per the record):
1. `src/deepreason/scheduler/scheduler.py:311-324` —
   `admitted_effect_candidates` sweep has no atomic-child exclusion
   and never reads `item.terminal`.
2. `src/deepreason/scheduler/scheduler.py:348-372` — the recovery
   dispatch branches only on `task_kind == CONJECTURE`; there is no
   branch for an atomic decomposition child, which should reach
   `atomic_recovery.recover_atomic_child_output` the way
   `rules/crit.py` reaches it on the live path.
3. `src/deepreason/workflow/nonconjecture_recovery.py:643-644` —
   `_criticism_contract` accepts only the batch payload shape and has
   no fallback for an atomic child's `contract-decomposition-child.v1`
   shape.

Symptom 2, connected: `tests/test_continuation.py::
test_a_stop_with_no_typed_receipt_refuses_continuation` fails on this
SAME committed root because the crash already committed a `lifecycle_
resumed` decision (seq 1175) before failing — so the root is no longer
"a stop with NO typed receipt" (the category the failing test's own
witness-scan is built to find and assert refuses with
`CONTINUE_TYPED_STOP_REQUIRED`, `runtime/continuation.py:352`). It is
a stop WITH a receipt whose recovery crashed. A later default `continue`
attempt on it takes the `elif current_resume is not None:` branch
(`continuation.py:312-326`) and — because the new attempt's request
parameters (cycles/tokens/etc.) do not byte-match the original crashed
attempt's recorded resume decision — refuses
`CONTINUE_RESUME_RECOVERY_MISMATCH` instead. This is a THIRD outcome
category ("resumable stop, receipt exists, but its recovery never
settled") the test's binary resumable/non-resumable model does not
name. Fixing symptom 1 prevents this from happening to any FUTURE run,
but cannot retroactively change what this byte-frozen, already-crashed
fixture's own log already recorded — so FIX.md must decide, with
evidence, whether the test's own witness-selection should exclude (or
separately classify) a root in this state, per GOAL.md's own
instruction not to silently patch the assertion.

Falsifiable prediction (what `dr-reproduce` must show):
1. `deepreason --root <scratch-copy-of-fixture> continue` reproduces
   the IDENTICAL crash: `NonConjectureRecoveryAuthorityError("unknown
   critic task")`, terminal `state: "failed"`, `stop_reason:
   "operational_failure"` — deterministic, since the log is frozen and
   the mechanism above requires no live provider judgment, only replay.
2. A synthetic minimal root (mock-endpoint `Scheduler`, no live
   provider, the S5-era construction pattern) holding exactly one
   `WorkflowTaskKind.CRITICISM` transaction-work item shaped as an
   ALREADY-TERMINALIZED atomic decomposition child (`contract_id=
   "critic.atomic-target.v1"`, payload `schema=
   "contract-decomposition-child.v1"`, admission `outcome="admitted"`,
   `terminal.status="completed"`) plus a resumable `budget_exhausted`
   stop, must raise the SAME `NonConjectureRecoveryAuthorityError
   ("unknown critic task")` the instant `_recover_workflow_prefixes`
   (equivalently, `continue`) runs against it — isolating the
   mechanism without the full fixture or any provider call.

Ruled out: PARKED P3's own literal wording ("more pending") read as
"an INCOMPLETE atomic child must still be outstanding for the crash to
fire" — checked directly against this fixture's own record and refuted:
the one recorded decomposition is FULLY resolved
(`contract_decomposition_completed` at seq 64, both children
`terminal_status: "completed"`), and the crash mechanism fires anyway,
on ANY criticism atomic child ever admitted, pending or not. The
refined mechanism above (ANY admitted criticism atomic child, complete
or incomplete) is the one `dr-reproduce`'s synthetic root must
demonstrate, not P3's narrower original reading. Also ruled out (per
S6 P3's own text, reconfirmed against the code read here): a `--seat`
interaction — neither `_recover_workflow_prefixes`'s filter nor
`_criticism_contract`'s assertion branches on seat or route identity;
both act purely on `task_kind` and payload/contract shape.
