# Spec for: checkpoints need to be hardened, and a jailbroken run must not be continuable
Traces: every item cites R/C numbers. Untraceable items are bugs.

This is a DESIGN-AND-STOP spec: the Measurements and Options sections are
filled, because the request's central question (Q2 — which verdict the gate
trusts) is a security fork that must be priced before code, not after.

## Map preflight (resolved ids, carried from REQUEST.md)

`DR-CON-run-identity` (owns `application/text_runs.py`,
`runtime/continuation.py`, `amendment/apply.py`), `DR-SUB-application` (owns
`application/`, `runtime/`), `DR-SUB-amendment` (owns `amendment/`),
`DR-SUB-workflow` (READ ONLY — `RESUMABLE_STOP_REASONS` is not touched),
`DR-SUB-verification` (CONSUMED ONLY — frozen surface 3), `DR-SUB-scheduler`
(READ ONLY, out of cone). Two map FINDINGS recorded in REQUEST.md: INDEX.md
routes to none of `SUB-application`/`SUB-amendment`/`SUB-periphery`, and the
seams this work joins (application x verification, amendment x verification)
are undocumented on both sides, so the "read the seam first" rule had nothing
to read.

## Items

S1 (R8, R9, C1) — the CONTINUE integrity gate.
    files: `src/deepreason/runtime/continuation.py`
    before: `prepare_continuation` consults no replay verdict at any point.
      Measured (M4): it ACCEPTED 3 of 6 committed roots whose own published
      `REPLAY_VALIDATION.json` says `valid: false`, returning
      `continuation seq=0`; the other 3 were refused for an unrelated reason
      (`CONTINUE_TYPED_STOP_REQUIRED`), not for their record.
    after: after the last existing precondition (`_assert_no_live_lock`) and
      BEFORE the function's first write (the `run-stops/` archive), the record
      is re-derived through `verify_root` (Option B, see Options). Any
      violation — or any exception raised by the verifier, because a record
      the verifier cannot read is not a record that verified — raises
      `ValueError("CONTINUE_RECORD_NOT_VERIFIED: <sorted check names>")`, a
      20th member of the file's existing 19-code bare-`ValueError` vocabulary.
      Position rationale: last, so every existing typed refusal keeps its own
      code and its own witnesses; before any write, so a refused root is
      byte-unchanged.
    accept: `python -m pytest tests/test_checkpoint_hardening.py::test_one_flipped_log_byte_turns_a_continue_into_a_typed_integrity_refusal -q` -> ends `1 passed`
    accept: `python -c "import pathlib; s=pathlib.Path('src/deepreason/runtime/continuation.py').read_text(); assert 'CONTINUE_RECORD_NOT_VERIFIED' in s; assert 'verify_root' in s"` -> exit 0

S2 (R8, R9) — the AMEND integrity gate.
    files: `src/deepreason/amendment/apply.py`
    before: `_require_terminal_stop` is amend's WHOLE terminal precondition and
      tests only `derive_terminal_authority(...).current_valid`. Measured (M4):
      it PASSED on 6 of 6 driven replay-invalid committed roots.
    after: the same re-derivation runs inside `_require_terminal_stop`, AFTER
      its existing authority check, raising a 23rd `AmendmentError` code
      `AMEND_RECORD_NOT_VERIFIED` whose message names the violated checks.
      Order rationale: authority first, so `AMEND_NOT_AT_TERMINAL` keeps its
      three existing test witnesses and nothing is shadowed.
    accept: `python -c 'import re,pathlib; d=pathlib.Path("src/deepreason/amendment"); codes=set(); [codes.update(re.findall(r"AmendmentError\(\s*\"([A-Z][A-Z_]+)\"", (d/n).read_text())) for n in ("apply.py","state.py","models.py")]; assert len(codes)==23, sorted(codes); assert "AMEND_RECORD_NOT_VERIFIED" in codes'` -> exit 0
    accept: `python -m pytest tests/test_checkpoint_hardening.py::test_one_flipped_log_byte_turns_an_amend_into_a_typed_integrity_refusal -q` -> ends `1 passed`

S3 (R9, C3) — the tamper proof, as a one-byte differential on ONE committed root.
    files: `tests/test_checkpoint_hardening.py` (new)
    before: nothing anywhere proves that a tampered record is refused.
    after: two copies of
      `experiments/2026-08-13-defect-controller-steering-inert/failed-epoch1-run-8e22d0431fd2b98d`
      (64 events, stored verdict `valid: true`, `verify_root` 3.07 s — M6).
      The INTACT copy reaches its pre-existing later refusal
      (`CONTINUE_TYPED_STOP_REQUIRED`), proving the new gate let it through.
      The copy with ONE flipped byte in `log.jsonl` raises
      `CONTINUE_RECORD_NOT_VERIFIED`. Same root, one byte, two different typed
      codes — the differential IS the proof, and neither outcome can be
      obtained by a fixture asserting a state into existence. The same pair is
      driven through `_require_terminal_stop` for `AMEND_RECORD_NOT_VERIFIED`.
      Copies only, never the original (the file's own established rule).
    accept: `python -m pytest tests/test_checkpoint_hardening.py -q` -> ends `N passed`, `0 failed`
    accept: `git status --porcelain experiments/` -> empty after the run

S4 (R8, C3) — the witness regression selected from the record, not from a list.
    files: `tests/test_checkpoint_hardening.py`
    before: the 16-root gap (M2) has no test.
    after: a test selects witnesses by the PROPERTY that causes the refusal —
      a committed root whose own `REPLAY_VALIDATION.json` says
      `valid: false` — guards with `assert witnesses` so a shrinking
      population trips the test instead of silently emptying it, bounds the
      driven subset by log length (a runtime budget, stated as one, because
      `verify_root` is O(run length) — M6), copies each root, and asserts both
      verbs refuse typed. The bound is not the property: the guard asserts the
      full witness population is non-empty before the bound is applied.
    accept: `python -m pytest tests/test_checkpoint_hardening.py::test_every_replay_invalid_committed_root_is_refused_by_both_verbs -q` -> ends `1 passed`

S5 (R7, R3, R4) — the ordinary worker-failure terminal records its own
    uncontinuability, typed.
    files: `src/deepreason/application/text_runs.py`
    before: the worker's ordinary failure branch writes `run-stop.json`,
      `checkpoint.json`, `run-result.json` and a `progress.jsonl` line, and
      records NOTHING about whether the root can be picked up again.
      `deepreason results` reports `lifecycle_refusal:
      ABSENT:NO_LIFECYCLE_REFUSAL_RECORD`. Measured (M2): 16 committed roots
      stand in exactly this state; 15 of the 16 carry no continuation
      authority at all.
    after: that branch builds `_refusal("TERMINAL_LIFECYCLE_NOT_TAKEN_FAILURE_TERMINAL",
      ...)` carrying `stop_reason` and
      `continue_refusal="CONTINUE_TYPED_STOP_REQUIRED"`, puts it on the
      `run-result.json` payload under the existing
      `terminal_lifecycle_refusal` key, and passes its code to
      `progress.emit(..., terminal_lifecycle_refusal=...)`. NO schema change
      is needed or made: `RunResultV2` is `extra="allow"` and
      `ProgressEvent.terminal_lifecycle_refusal` already exists with a default
      — the exhaustion path (`text_runs.py` `_record_exhaustion_lifecycle_stop`
      and its `progress.emit`) already ships exactly this shape, and this item
      only extends it to the terminal that had nothing.
    accept: `python -m pytest tests/test_checkpoint_hardening.py::test_a_failure_terminal_records_why_it_cannot_be_continued -q` -> ends `1 passed`

S6 (R7, R3, R4) — the no-harness failure terminal, which writes no checkpoint
    at all, says so.
    files: `src/deepreason/application/text_runs.py`
    before: the `if harness is None:` branch writes `run-result.json` and a
      progress line and NOTHING else — no `run-stop.json`, no
      `checkpoint.json`. This is the operator's "corrupted stop" in its purest
      form: a terminal from which no relaunch is possible and which does not
      say so.
    after: the same `terminal_lifecycle_refusal` shape carries
      `TERMINAL_NO_CHECKPOINT_WRITTEN` with `error_type`, on both
      `run-result.json` and the progress line.
    accept: `python -m pytest tests/test_checkpoint_hardening.py::test_a_terminal_that_wrote_no_checkpoint_records_that_fact -q` -> ends `1 passed`

S7 (R8, R9, C4) — the reader answers from the verdict it is holding.
    files: `src/deepreason/application/results.py`
    before: `results_summary` computes `_verification(root, replay, result,
      verify=verify)` and then calls `_terminal(replay, stop, result,
      harness)`, which reads `replay.get("valid")` — the STORED verdict — even
      when the operator passed `--verify`. So `deepreason results --verify`
      can print `amend_ready: true` for a root whose re-derived verdict is
      invalid and whose `amend` (after S2) refuses.
    after: `results_summary` passes the already-computed `verification` dict
      into `_terminal`, which reads `verification["valid"]`. The default path
      is behaviour-identical by construction — `_verification`'s stored branch
      already returns exactly `bool(replay.get("valid"))` — so no existing
      assertion moves; the `--verify` path becomes exact. This is the rule
      `DR-SUB-application`'s Traps already states (the reporting verb reads
      the ACTING verb's own predicate) applied without adding a second copy of
      the predicate.
    accept: `python -m pytest tests/test_results_command.py -q` -> ends `0 failed`
    accept: `python -m pytest tests/test_results_command.py::test_terminal_readiness_answers_the_rederived_verdict_under_verify -q` -> ends `1 passed`

S8 (C5) — the map moves in the same commits as the code.
    files: `docs/map/SUB-amendment.md`, `docs/map/CON-run-identity.md`,
      `docs/map/SUB-application.md`
    before: `SUB-amendment.md`'s prose says "twenty-two typed, durable refusal
      codes" and its check asserts `len(codes)==22`; `CON-run-identity.md`'s
      "what `continue` demands before resuming" row names no integrity
      precondition; `SUB-application.md`'s P6 Traps entry says the P2 question
      is open.
    after: `SUB-amendment.md` — prose to "twenty-three", check to `==23` with
      `AMEND_RECORD_NOT_VERIFIED` added to the required-subset assertion, and
      the "Which run states may be amended at all" row names the integrity
      precondition. `CON-run-identity.md` — a new rule paragraph for the
      integrity gate with a check that goes RED if either gate is removed, and
      a Traps entry naming this tranche and the measured 16-root gap.
      `SUB-application.md` — rows for the two failure-terminal records and the
      reader change, and the P6 Traps entry REWRITTEN (never deleted, per
      `SCHEMA.md` rule 7) to say which half of P2 this tranche closed and
      which halves remain parked.
    accept: `python tools/docs_verify.py` -> `0 failed` beyond the
      `docs/AUDIT_BASELINES.md` expected set, compared BY DOCUMENT AND CLASS,
      not by line number (the baseline's line numbers are already stale);
      delta ZERO against the 9 this shallow container reports.
    accept: each new/changed `check:` line run standalone -> exit 0

S9 (R9, C3, artifact) — the census and the probes are committed instruments,
    not prose.
    files: `experiments/2026-08-30-change-checkpoint-hardening/proof/`
    before: the numbers this spec rests on exist only in a reconnaissance
      document.
    after: `census.py`/`census.json` (the 59-root census), `forge_probe.py`/
      `forge.json` (tamper-evidence), `gate_probe.py`/`gate_probe.json` (what
      the two verbs do today), `verify_cost.py`/`verify_cost.json` (the price
      of re-deriving), and `MEASUREMENTS.md` stating every figure with the
      command that produced it. All read-only against committed roots; all
      copy before any write.
    accept: `python experiments/2026-08-30-change-checkpoint-hardening/proof/census.py` -> exit 0, prints `population: 59`
    accept: `git status --porcelain experiments/` -> empty after all four run

## Assumptions (operator may override)

A1 (Q1): failure terminals STAY NON-RESUMABLE. R7 is read as requiring that a
terminal which cannot assure continuability RECORD that fact typed, not as
widening `RESUMABLE_STOP_REASONS`. Smallest reading that does not overturn C6,
an owner decision of 2026-07-27 whose comment says "Failure terminals stay
non-resumable" in as many words. The widening question is parked, not decided
(see Parked forks F1).

A2 (Q2): the gate RE-DERIVES through `verify_root` (Option B). Chosen on the
measurements, not on taste — see Options. It is also the only option under
which S3's proof obligation (one flipped log byte -> typed refusal) can be
met at all, because the stored verdict is a CACHE of a verdict over the log
and says nothing about a log altered after it was written.

A3 (Q3): "checkpoints sufficient for relaunch" for a terminal that by A1 may
never relaunch means the terminal records, typed, WHY it cannot be continued —
the operator's "corrupted stop" made visible rather than made resumable. This
is a reading; their words do not settle it.

A4 (Q4): limb three is scoped to REPLAY VALIDITY ALONE. The
containment-breach clause names a record type that does not exist (M8) and
building it means entering frozen surface 3, which is not granted. Stated
plainly here so the tranche never claims to have closed R8 whole.

A5 (Q5): the integrity gate is a REFUSAL BY CONSTRUCTION, not a per-run
switchable gate. R9 calls it a security boundary, and the 2026-08-28
optional-gates law names run-BEHAVIOUR gates (qualification, criticism
authority, judge invocation, admission screens) — not record integrity. If the
operator reads that law as covering this gate too, the switch is a small
follow-on, not a rework.

A6 (cone): `src/deepreason/runtime/continuation.py` is written by S1 although
the lane brief's cone list names only `application/text_runs.py`,
`application/results.py`, `workflow/lifecycle.py`, `amendment/`, tests,
`docs/map` and the tranche directory. The same brief's scope paragraph names
the CONTINUE gate as "the core deliverable" and demands the tampered-root
proof on `continue`, which is unbuildable without it. `continuation.py` is not
a frozen surface (M7 verdict CLEAR) and is owned by two of this tranche's own
map ids. Recorded as a discrepancy in the brief, disposed by building what the
brief's prose requires. `workflow/lifecycle.py` IS in the granted cone and is
deliberately NOT touched (A1).

## Questions for operator (STOP if non-empty)

The directing brief binds this tranche to "STOPS BUBBLE, NEVER RESOLVE
IN-BATCH ... Write the STOP brief and continue with everything else" and
"DELIVER EVERYTHING NOT BLOCKED" (C8). That instruction and this section's
"STOP if non-empty" rule point opposite ways. This spec follows the brief: the
forks below are listed in full, each with the reason it does not block any
S-item, and every S-item is buildable without an answer to any of them. None
is resolved here.

See "Parked forks" below — F1 through F7, all bubbled with evidence.

## Parked forks (bubbled, not decided here)

F1 — OPERATOR-LEVEL. Does R7 require failure terminals to become RESUMABLE?
    Evidence: 16 committed roots stand at `failed`/`operational_failure` with
    the complete checkpoint FILE set (`checkpoint.json`,
    `workflow-checkpoint.json`, `run-stop.json`, `REPLAY_VALIDATION.json`,
    `run-result.json`, `progress.jsonl`) and cannot be continued; 15 of the 16
    carry no continuation authority at all (M2). Two readings, both honest:
    (a) R7 means the FILES must be there and they are — the tranche's job is
    to record the uncontinuability, which is A1/S5; (b) R7 means "sufficient
    for relaunch" literally and the widening of `RESUMABLE_STOP_REASONS` is
    owed. (b) overturns C6, an owner decision. Cannot be decided in-batch:
    it is a change to what a failure MEANS, not to how one is recorded.
    Needs: the operator's word on (a) vs (b).

F2 — OUT OF CONE, limb one's unshipped half. A `WorkBudgetDenied` reservation
    denial still terminates as `operational_failure`, not `budget_exhausted`.
    Verified this session: `experiments/2026-08-24-change-rung7-wounds-falls-succession/run`
    and `experiments/2026-08-22-change-epoch3-second-lineage/failed-attempt2-run-bb045538...`
    both report `state: failed`, `stop_reason: operational_failure`,
    `error_type: WorkBudgetDenied`. The fix lives in
    `src/deepreason/scheduler/scheduler.py` (whose `Scheduler.run` except
    clauses do not name `WorkBudgetDenied`) and `src/deepreason/workflow/`.
    Cannot be built here: outside the granted cone, and R6 is another lane's
    limb. Needs: a tranche with the scheduler cone.

F3 — OUT OF CONE, a second corrupted-stop path one layer down.
    `Scheduler._record_stop` calls `build_stopped_lifecycle` with no handler
    for `UnfinishedWorkflowAuthorityError`, while
    `application/text_runs.py` catches exactly that and records a typed
    refusal. So a CONTROLLER-decided stop holding unfinished authority becomes
    an untyped `operational_failure` — the same defect P6 fixed on the
    exhaustion path, unmirrored. S5/S6 close the application-layer half only.
    Needs: the scheduler cone.

F4 — FROZEN SURFACE 3, and the reason limb three is scoped. "Unresolved
    containment-breach evidence" (R8) has no typed form. Searched this session
    (M8): 77 `containment` hits across `src/deepreason/`, every one a limit, a
    timeout or a free-text `sandbox_abort` trace string
    (`verification/simulation.py`, `verification/runner.py`,
    `verification/lean.py`, `v6_policy.py`); no event kind, no `verify_root`
    check, no receipt field. The nearest typed structure is
    `verification/report.py`'s `_SECURITY_CHECKS`, a closed seven-name set
    (`attempt-route`, `capability-authority`,
    `capability-compiled-authority`, `capability-grant`,
    `capability-work-order`, `frozen-route`, `school-route`) — none about
    containment, and that file is frozen surface 3. Creating the record type
    means editing it. NOT GRANTED, NOT REQUESTED here (this tranche needs no
    such edit). Needs: the operator's decision to open a separate tranche with
    a written surface-3 grant, or to accept limb three as replay-validity
    only.

F5 — MAP REPAIR, another lane's territory. `docs/map/INDEX.md`'s subsystem
    table omits `SUB-application.md`, `SUB-amendment.md` and
    `SUB-periphery.md`, so the mandated map preflight cannot route to the two
    documents covering this lane; and the application x verification /
    amendment x verification seams are undocumented on both sides. Recorded in
    REQUEST.md with its measured grep. Not fixed here: `INDEX.md` is outside
    this cone.

F6 — READER SEMANTICS, pre-existing, not created by this tranche.
    `results.py`'s `amend_ready` requires `stop_reason_resumable`, which
    `amend` does NOT require — so the reader says `amend_ready: false` on the
    16 failed roots that `amend` actually accepts (M2). S7 does not touch
    this: it fixes WHICH VERDICT the reader reads, not what `amend_ready`
    means. Changing the meaning is a reader-contract change with 6 keys pinned
    by an exact-set assertion in `tests/test_results_command.py`, and it needs
    a decision about whether the field names a verb or a lifecycle state.

F7 — ONE STRANDED COMMITTED ROOT, the operator's "corrupted stop" in the
    flesh, re-derived this session (M2):
    `experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a`
    -> `authority_status: invalid_incomplete`, `detail_code:
    TERMINAL_REPLAY_VALIDATION_BINDING_INVALID`, `stored_replay_valid: true`.
    `amend` refuses it (`AMEND_NOT_AT_TERMINAL`) and `finalize` refuses it
    (`FINALIZE_AUTHORITY_UNAVAILABLE` requires `current_open_uncommitted`).
    No verb can touch it. This tranche does not add a repair verb — that is a
    new operation, not a hardening — and does not edit the committed root.

## The four populations, and what this tranche does with each (R7, A3)

Measured over all 59 committed roots (M1, M2). Every root is in exactly one
bucket.

| # | population | what the record shows | this tranche |
|---|---|---|---|
| 24 | `amend_ready: true` (23 `completed`/`budget_exhausted` + 1 `completed`/`converged`) | valid typed terminal, resumable reason, continuation authority | CLOSED — nothing owed; after S1/S2 they still pass, and their verdicts are re-derived rather than assumed |
| 16 | `failed`/`operational_failure` | complete checkpoint FILE set, no STOPPED receipt, 15 of 16 with no continuation authority; e.g. `experiments/2026-08-24-change-rung7-wounds-falls-succession/run` | PARTLY CLOSED — S5 makes new terminals of this shape SAY they cannot be continued; whether they should BECOME continuable is F1, parked |
| 4 | `current_open_uncommitted` (`running`, no stop record) — `2026-08-26-pc2-rematch/{run_h3,retired-transport-timeout180-...,retired-truncation-cap32768-...}` and `live_research_2026-07-29/selfstudy/runs/failed-epoch4-run-9175f0ec...` | never reached a terminal; `finalize_stopped_root` is the existing repair | PARKED — `finalize` already covers them; this tranche adds nothing and breaks nothing |
| 1 | `invalid_incomplete` — `live_research_2026-07-29/selfstudy/runs/failed-epoch2-run-9175f0ec...` | neither amendable nor finalizable | PARKED as F7 — recorded by name, not repaired |

13 of the 24-bucket's siblings (`completed`/`budget_exhausted`/`amend_ready:
false`) sit inside the 16-root A2 gap or lack continuation authority; they are
counted in the gap row of M2 rather than given a bucket of their own, because
their disposition is S1/S2's, not S5's.

## Out of scope (explicit)

- Widening `RESUMABLE_STOP_REASONS` — not requested; F1.
- The `WorkBudgetDenied` terminal — not requested of this lane; F2.
- `scheduler.py`'s unhandled `UnfinishedWorkflowAuthorityError` — not
  requested; F3, out of cone.
- Creating a typed containment-breach record or a new `_SECURITY_CHECKS`
  member — not requested, and frozen surface 3; F4.
- Repairing `docs/map/INDEX.md`, or writing the application x verification and
  amendment x verification seam documents — not requested; F5.
- Changing what `amend_ready` MEANS — not requested; F6.
- A repair verb for the one stranded root, or any edit to a committed root —
  not requested, and committed roots are evidence; F7.
- Making the integrity gate switchable per run — not requested; A5.
- Any change to `verify_root`'s findings, checks or output shape — frozen
  surface 3, consumed only.

## Frozen-surface contact forecast

none expected — checked against `docs/map/INV-frozen-surfaces.md` and computed
by `tools/blast_radius.py`, not asserted. Command run this session:

    python tools/blast_radius.py \
      --files src/deepreason/runtime/continuation.py \
              src/deepreason/amendment/apply.py \
              src/deepreason/application/text_runs.py \
              src/deepreason/application/results.py \
      --symbols prepare_continuation _require_terminal_stop \
                terminalize_text_run _terminal

Its own rows, pasted verbatim, and disposed one by one:

    "frozen_surface_contacts": []
    "frozen_adjacent_contacts": []
    "frozen_surface_verdict": "CLEAR"
    "reachability": [{"symbol": "prepare_continuation", "status_current": "REACHABLE", "status_base": null, "direction": null},
                     {"symbol": "_require_terminal_stop", "status_current": "REACHABLE", "status_base": null, "direction": null},
                     {"symbol": "terminalize_text_run", "status_current": "REACHABLE", "status_base": null, "direction": null},
                     {"symbol": "_terminal", "status_current": "REACHABLE", "status_base": null, "direction": null}]
    "consumers": {"qualification_digest": [], "wheel_smoke_pins": []}
    "disclosure_summary": "This change touches none of the five frozen surfaces. ..."

Disposition, row by row:
- `frozen_surface_contacts: []` — NO GRANT IS REQUESTED and none is needed.
  This tranche CONSUMES `verify_root` by import and edits nothing in
  `src/deepreason/invariants.py` or `src/deepreason/verification/`.
- `frozen_adjacent_contacts: []` — `route_fingerprint` is not reached.
- reachability, all four REACHABLE, none `UNKNOWN` — no unresolved entry, so
  no STOP on that ground. (A superset run that also declared
  `RESUMABLE_STOP_REASONS` returns `UNKNOWN` for it, because the gate resolves
  CALL paths and a module-level `frozenset` has none. That symbol was dropped
  from the declaration because this tranche does not modify it — A1 — and the
  fact is recorded here rather than left out.)
- `qualification_digest: []` and `wheel_smoke_pins: []` — no digest pin and no
  packaging pin is in the blast radius; no console entry point, MCP tool or
  wheel-layout pin moves, so the wheel smokes are not owed.

Belt and braces, to be re-run at every [COMMIT] step and at delivery — noting
that this command's regex misses `src/deepreason/verification/`, which is half
of surface 3, so it is a backstop and not the boundary:

    git diff --name-only origin/main...HEAD | grep -qE "capabilities/state\.py|/harness\.py|/invariants\.py|/run_manifest\.py|/qualification\.py|llm/firewall\.py"

expected: no match (exit 1). The authoritative check is the seven-path list in
CLAUDE.md plus `tools/blast_radius.py` above.

## Blast-radius census

Every consumer `tools/blast_radius.py` reported, none omitted.

TESTS (3 files):
- `prepare_continuation` -> 38 hits across `tests/test_amendment_epochs.py`,
  `tests/test_calculus_standing.py`, `tests/test_continuation.py`,
  `tests/test_lifecycle_operation_parity.py`,
  `tests/test_v6_resumed_terminal_revalidation.py`,
  `tests/test_v6_terminal_commitment_authority.py`,
  `tests/test_wheel_operational.py`,
  `tests/test_workflow_resume_lifecycle_c4.py` -> MUST NOT MOVE, with ONE
  named exception (below). Every one of these drives a FRESH in-test root,
  which a correct gate passes.
- `tests/test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation`
  -> EXPECTED TO MOVE. See "Predicted fixture changes".
- `_terminal` -> 4 hits in `tests/test_website_state_machine.py` -> MUST NOT
  MOVE: a NAME COLLISION. The gate greps by symbol name; that file's
  `_terminal` is the website state machine's, not `results.py`'s.
- `src/deepreason/application/results.py` -> `tests/test_error_catalog.py:66`
  -> MUST NOT MOVE: an error-catalogue census over the module, not over
  `_terminal`.

MAP CHECKS (5 documents, 48 hits):
- `docs/map/SUB-amendment.md:100, :135, :139, :174, :183, :186, :211` ->
  :135/:183 (the `_require_terminal_stop` rows) and the code-count check
  EXPECTED TO MOVE (S8); the rest MUST NOT MOVE.
- `docs/map/CON-run-identity.md:4, :49, :56, :161, :168, :224, :251, :260` ->
  :49/:224 (the `continue` rows) EXPECTED TO MOVE (S8); the rest MUST NOT
  MOVE.
- `docs/map/SUB-application.md:78, :111, :130, :146, :147, :176, :188, :206,
  :208, :216, :267, :278, :304, :330, :347, :355, :366, :376, :386, :400,
  :405, :407, :421, :428, :469, :483, :491` -> the P6 Traps entry and the
  `terminalize_text_run`/`results_summary` rows EXPECTED TO MOVE (S8); the
  rest MUST NOT MOVE.
- `docs/map/SEAM-scheduler-x-workflow.md:152` and `docs/map/SUB-workflow.md:199`
  -> MUST NOT MOVE: both name `prepare_continuation` from the workflow side,
  and this tranche adds a precondition without changing the resume contract
  they assert.
- `docs/map/SUB-scheduler.md:63` -> MUST NOT MOVE: names `text_runs.py` from
  the scheduler side; F3 is parked, not built.

Line numbers above are today's and will drift; they are the census, not the
address. `grep` is the address (`SCHEMA.md`).

## Predicted fixture changes (recorded BEFORE the edit, per C4)

P-FIX-1: `tests/test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation`.
    Its `_non_resumable_committed_roots()` witness predicate selects committed
    roots whose stop reason is outside `RESUMABLE_STOP_REASONS`. After S1, a
    witness that is ALSO replay-invalid is refused by the earlier integrity
    gate with `CONTINUE_RECORD_NOT_VERIFIED` instead of the
    `CONTINUE_TYPED_STOP_REQUIRED` this test targets. Measured (M4): 3 of the
    6 driven replay-invalid roots take exactly that branch today.
    LEGITIMATE because the change is to the WITNESS PREDICATE, not to the
    assertion: the test keeps demanding the exact string
    `CONTINUE_TYPED_STOP_REQUIRED`, and gains one more exclusion clause
    alongside the one it already carries for the same reason (roots with a
    non-empty `continuations.jsonl` are excluded because
    `prepare_continuation` "takes its 'already resumed' branch for this root
    ... not the CONTINUE_TYPED_STOP_REQUIRED branch this test targets"). The
    file's own established pattern; the guard `assert witnesses` stays, so
    emptying the set fails loudly.
    NOT LEGITIMATE and will not be done: relaxing the assertion to accept
    either code.

P-FIX-2: none predicted in `tests/test_results_command.py`. S7's default path
    is behaviour-identical by construction, and the exact-set assertion on the
    six `terminal` keys is preserved because S7 adds no key. A NEW test is
    added for the `--verify` path. If the exact-set assertion moves, that is
    unpredicted drift and a STOP, not a fixture update.

P-FIX-3: UNPREDICTED-BY-NAME, PREDICTED-BY-CLASS. Any existing test whose
    FRESH in-test root does not pass `verify_root` will now fail at S1/S2.
    None is known to exist; the class is recorded so it cannot be mistaken for
    noise. Disposition rule, fixed here in advance: such a failure is either
    (a) a genuine defect in that fixture's record — fix the fixture, or (b)
    evidence the gate is wrong — which is a STOP and a re-plan. It is NEVER
    grounds for weakening an assertion (C4), and never grounds for exempting
    test roots from the gate.

P-FIX-4: RUNTIME, not correctness. S1 adds one `verify_root` per
    `prepare_continuation` call and S2 one per `amend`. Measured cost on the
    smallest committed roots (M6): 0.69 s at 27 events, 3.07 s at 64, 8.10 s
    at 114. With 38 `prepare_continuation` call sites in the suite, the
    predicted added gate time is tens of seconds, not minutes. VALIDATION.md
    must record the measured before/after wall clock of the ring files rather
    than assert it.

## Measurements

All taken this session, in this worktree, one instrument at a time. The box is
shared with four other lanes; the census and the two probes were run with no
other instrument of this lane running, and the timings in M6 are therefore an
upper bound, not a clean-room figure.

M1: `python experiments/2026-08-30-change-checkpoint-hardening/proof/census.py`
    ->
        population: 59
        schema_version: {'6': 59}
        triples (state | stop_reason | amend_ready):
          completed | budget_exhausted | True  -> 23
          failed | operational_failure | False  -> 16
          completed | budget_exhausted | False  -> 13
          running | {'absent': True, 'reason': 'NO_STOP_RECORD'} | False  -> 4
          running | budget_exhausted | False  -> 1
          completed | converged | True  -> 1
          running | operational_failure | False  -> 1
        amend_ready: {'False': 35, 'True': 24}
        stored_replay_valid: {'True': 39, 'False': 16, 'ABSENT:NO_REPLAY_VALIDATION_JSON': 4}
        verification_source: {'stored': 55, 'ABSENT:...': 4}
    — supports the four-population table and the claim that the reader takes
    the stored path for 55 of 59 roots and never re-derives unasked.

M2: the same run's authority columns ->
        authority_status: {'current_valid_committed': 54, 'current_open_uncommitted': 4, 'invalid_incomplete': 1}
        A2 gap (authority valid AND stored replay invalid): 16
        A1 failed without continuation authority: 15
        finalize population (current_open_uncommitted): 4
        stranded (neither amend nor finalize): 1
          experiments/live_research_2026-07-29/selfstudy/runs/failed-epoch2-run-9175f0ecb055e57455af3c50df153c5a
    — supports the 16-root gap (S1/S2/S4), the 15-of-16 figure in S5, F7's
    named root, and the four-population table. NOTE, and it is a correction to
    the reconnaissance this lane was handed: 15, not 16, of the failed roots
    lack continuation authority. The exception is
    `experiments/2026-08-08-live-two-seat-ab-s6/home-s6/runs/failed-epoch1-run-8c77c6588485304d1f73416318c62949`,
    which carries a resume decision from an earlier continuation. Recorded
    rather than rounded.

M3: `python experiments/2026-08-30-change-checkpoint-hardening/proof/forge_probe.py`
    ->
        population: 16
        forge DETECTED on: 12
        forge UNDETECTED on: 4
          experiments/2026-08-02-stress-triplet/home-triage/runs/run-0a3e93d6e8031e2e6d1d21dde2fa93cc
          experiments/2026-08-04-change-rung5-dumb-alternative-backend/rr-home/runs/run-9a6be78e1e79184a0bd89923b957586c
          experiments/2026-08-08-corpus-enrichment-patrol-pilot/home/runs/run-e3f4f7007c50fe7e09b301d31851c3e7
          experiments/live_research_2026-07-29/selfstudy/runs/completed-epoch3-run-9175f0ecb055e57455af3c50df153c5a
        outcomes: {'invalid_incomplete / TERMINAL_REPLAY_VALIDATION_BINDING_MISMATCH': 12, 'current_valid_committed / None': 4}
    — REFUTES Option A. Forging `valid: true` into a copy's
    `REPLAY_VALIDATION.json`, written in CANONICAL bytes so the attacker is
    the one the law names rather than one caught on formatting, moves nothing
    on 4 of the 16 roots: `derive_terminal_authority` skips
    `_validate_result_projection_binding` whenever the published result equals
    the fail-closed pending projection. A pretty-printed forge is caught on
    all 16 by `TERMINAL_REPLAY_VALIDATION_NONCANONICAL`; that measures the
    probe, not the binding, and is why the probe was strengthened.

M4: `python experiments/2026-08-30-change-checkpoint-hardening/proof/gate_probe.py`
    ->
        run-e542c3c1 (294 ev)  amend: PASSED   continue: REFUSED CONTINUE_TYPED_STOP_REQUIRED
        run-9a6be78e (388 ev)  amend: PASSED   continue: ACCEPTED seq=0
        run-d17935a4 (550 ev)  amend: PASSED   continue: ACCEPTED seq=0
        completed-epoch2-run-9e9812fe (561 ev)  amend: PASSED  continue: ACCEPTED seq=0
        run-faa5feae (581 ev)  amend: PASSED   continue: REFUSED CONTINUE_TYPED_STOP_REQUIRED
        failed-epoch1-run-9175f0ec (594 ev)  amend: PASSED  continue: REFUSED CONTINUE_TYPED_STOP_REQUIRED
    — the A2 gap, driven rather than read: `amend` PASSED on 6 of 6
    replay-invalid roots; `continue` ACCEPTED 3 of 6 and refused the other 3
    for a reason that has nothing to do with their records. Supports S1, S2,
    S4 and P-FIX-1.

M5: the same run's re-derived verdicts ->
        run-e542c3c1: ['foreign-criticism' x5]
        run-9a6be78e: ['attempt-validity']
        run-d17935a4: ['foreign-criticism' x4]
        completed-epoch2-run-9e9812fe: ['foreign-criticism' x3]
        run-faa5feae: ['foreign-criticism' x3]
        failed-epoch1-run-9175f0ec: ['run-input']
    — the re-derived verdict AGREES with each root's stored `valid: false` on
    all six, so Option B is not stricter than the record's own published
    judgement; it is the same judgement, recomputed. Supports A2.

M6: `python experiments/2026-08-30-change-checkpoint-hardening/proof/verify_cost.py`
    ->
           27 events     0.69s    25.7 ms/event  2026-08-26-pc2-rematch/run_h3
           62 events     1.80s    29.0 ms/event  retired-truncation-cap32768-run-58fb0d20
           64 events     3.07s    48.0 ms/event  failed-epoch1-run-8e22d0431fd2b98d
          114 events     8.10s    71.0 ms/event  failed-epoch3-run-8e22d0431fd2b98d
          188 events    11.38s    60.5 ms/event  failed-epoch1-run-0d1f88e1
          294 events    17.23s    58.6 ms/event  run-e542c3c1
          300 events    18.88s    62.9 ms/event  run-5a771259
    plus, from the same instrument's larger siblings in M4: 388 ev 16.27 s,
    550 ev 21.57 s, 594 ev 32.40 s.
    — the price of Option B, and the reason S3's fixture is the 64-event root
    (3.07 s) rather than a large one. Consistent in order of magnitude with
    the reconnaissance figures this lane was handed (15.2 s at 300 events,
    146.7 s at 3 751), which are cited but not re-run: a 147-second
    measurement is not worth the box time when the shape is already
    established.

M7: `python tools/blast_radius.py --files ... --symbols ...` (full command and
    output pasted in the Frozen-surface contact forecast above) ->
    `"frozen_surface_verdict": "CLEAR"`, `"frozen_surface_contacts": []`,
    `"frozen_adjacent_contacts": []`.
    — supports A6 and the no-grant-requested disposition.

M8: `grep -rn "containment" --include=*.py src/deepreason/ | wc -l` -> `77`,
    every hit a limit, timeout or free-text `sandbox_abort` trace string; and
    `sed -n '119,129p' src/deepreason/verification/report.py` -> the closed
    seven-name `_SECURITY_CHECKS` set, none about containment.
    — supports A4 and F4: R8's containment clause has no record to gate on.

M9: `grep -n -iE "application|amendment|periphery" docs/map/INDEX.md` -> four
    unrelated lines (pasted in REQUEST.md); `ls docs/map/ | grep -E
    "application|amendment|periphery"` -> the three documents exist.
    — supports F5 and REQUEST.md's FINDING 1.

## Options (Q2 — which verdict the integrity gate trusts)

A: trust the stored `REPLAY_VALIDATION.json` `valid` field.
   files: continuation.py, apply.py. frozen contact: none. ~15 lines. cost:
   ~0 ms.
   REJECTED — cites M3. On 4 of the 16 measured gap roots a canonical forge of
   `valid: true` is UNDETECTED, so a tamperer who edits one file buys a
   resumable run. That is the exact sentence R9 forbids. It also cannot meet
   S3's proof obligation at all: the stored verdict is a cache of a verdict
   over the log and is unchanged by a log byte flip, so "alter one byte, watch
   continue refuse" would fail under this option.

B: re-derive through `verify_root`.
   files: continuation.py, apply.py. frozen contact: NONE — `verify_root` is
   imported and called, never edited (M7). ~54 lines across both. cost: 0.69 s
   at 27 events to 32.40 s at 594 (M6); the reconnaissance figure for a
   3 751-event root is 146.7 s.
   CHOSEN — cites M3, M4, M5, M6. It is the only option that reads the thing
   the law is about (the record) rather than a claim about it, the only one
   under which S3's one-byte proof can exist, and M5 shows it does not
   second-guess the record: on all six driven roots the re-derived verdict
   equals the stored one. Its cost is real and is priced in P-FIX-4 rather
   than waved at. The verbs it slows are OPERATOR-INITIATED and once-per-run:
   `continue` and `amend` each precede a run that lasts minutes to hours, and
   the operator's own words rank the security above the latency.

C: trust the stored verdict AND require that its terminal binding was
   validated, refusing typed when it was not.
   files: continuation.py, apply.py, and — the reason it is not chosen —
   either an import of `terminal_authority.py`'s private
   `_validate_result_projection_binding` / `_replay_validation_base`, or a
   second copy of the binding rule outside the module that owns it. ~40 lines.
   cost: ~0 ms.
   REJECTED, but the CHEAPEST DEFENSIBLE ALTERNATIVE if Option B's latency
   proves unacceptable — cites M3. It closes the 4-root hole M3 measured, and
   it is sound against a forged VERDICT FILE. It is NOT sound against a
   tampered LOG, because nothing in it re-reads the log; it would satisfy R8's
   letter and only part of R9. Recorded here with its numbers so the operator
   can choose it knowingly rather than have it chosen for them.

## Budget

Itemized, then summed by machine (never restated by hand):

    src/deepreason/runtime/continuation.py      28
    src/deepreason/amendment/apply.py           26
    src/deepreason/application/text_runs.py     34
    src/deepreason/application/results.py       14
    tests/test_checkpoint_hardening.py (new)   150
    tests/test_continuation.py                  20
    tests/test_results_command.py               30
    docs/map/CON-run-identity.md                22
    docs/map/SUB-application.md                 26
    docs/map/SUB-amendment.md                   10

    $ python3 -c "print(28+26+34+14+150+20+30+22+26+10)"
    360

~360 changed lines, 2 commits. Over the ~300 threshold, so the split is
proposed here rather than discovered at delivery, as two ORDERED commits
inside this one tranche (each self-contained, each carrying its own map move,
each gated):

    commit A (S1-S4, S8 amendment+run-identity halves):
      $ python3 -c "print(28+26+100+20+22+10)"
      206
    commit B (S5-S7, S8 application half):
      $ python3 -c "print(34+14+50+30+26)"
      154

DIFF-BUDGET CEILING held to at every [COMMIT] step: **400 insertions** over
`--paths src tests docs/map` (360 estimated plus ~11% headroom). The tranche
directory is excluded from the ceiling by pathspec — it is evidence and
narrative, not diff. `python tools/diff_budget.py <tranche-base> --ceiling 400
--paths src tests docs/map` must read `WITHIN` at every [COMMIT]; `EXCEEDED` is
a STOP decided above this lane, per the batch-1 record.

Frozen surfaces touched: none (M7, verdict CLEAR). No grant requested, none
needed.

Rubric: 6/6 yes
  - every R has a spec item with a machine-decidable accept? YES — R1/R2/R6a
    are recorded SHIPPED with citations and owed nothing; R6b is explicitly
    deferred to F2 with its evidence; R3/R4/R7 -> S5, S6; R8/R9 -> S1, S2, S3,
    S4, S7 (R8's containment half deferred to F4 with A4 stating it plainly).
  - blast-radius census pasted (or pasted-empty) and every hit classified?
    YES — 3 test targets and 5 map documents, every hit EXPECTED TO MOVE or
    MUST NOT MOVE, including the `_terminal` name collision.
  - frozen-surface contact forecast recorded? YES — `tools/blast_radius.py`'s
    own rows pasted verbatim and disposed one by one; verdict CLEAR.
  - every mechanism the request names traced to code it actually reaches?
    YES — except "containment-breach evidence", which reaches no code because
    none exists (M8), stated as A4/F4 rather than glossed over.
  - DESIGN-AND-STOP: every claim measured, every option priced? YES — M1-M9;
    Options A/B/C each priced in lines, cost and measured coverage gap.
  - nothing in the spec untraceable to an R/C number? YES — the anti-invention
    pass moved F1-F7 out of Items and into Parked forks, and every S-item
    carries its R/C numbers.
