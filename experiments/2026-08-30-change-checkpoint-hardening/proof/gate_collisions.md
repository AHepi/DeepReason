# GATE COLLISIONS — the integrity gate was built, measured, and NOT shipped

SPEC.md items S1-S4 specify an integrity gate: `prepare_continuation` and
`amend` re-derive the record through `verify_root` and refuse typed. It was
implemented exactly as specified (commit `5fccb1e91`, reverted in the commit
that carries this file), and the gate WORKED: on a copy of committed root
`experiments/2026-08-13-defect-controller-steering-inert/failed-epoch1-run-8e22d0431fd2b98d`
with one flipped endpoint byte it raised
`CONTINUE_RECORD_NOT_VERIFIED: attempt-route, frozen-route` and
`AMEND_RECORD_NOT_VERIFIED`, while the intact copy passed through to its
pre-existing `CONTINUE_TYPED_STOP_REQUIRED`. Those transcripts are
`RED-checkpoint-hardening.txt` and `GREEN-checkpoint-hardening.txt`.

Then the ring was run, and it turned EIGHT tests red. SPEC.md predicted ONE
(P-FIX-1). SPEC.md's own pre-registered rule for this situation (P-FIX-3) says
such a failure is either a fixture defect to fix, or "evidence the gate is
wrong, which is a STOP and a re-plan", and that it is NEVER grounds for
weakening an assertion and never grounds for exempting test roots from the
gate. Three of the eight cannot be fixed as fixtures without changing what
they assert. So: STOP, and the gate is parked (PARKED.md F9).

    PYTHONPATH=<worktree>/src python -m pytest \
      tests/test_continuation.py tests/test_amendment_epochs.py \
      tests/test_amendment_chain_integrity.py \
      tests/test_lifecycle_operation_parity.py tests/test_results_command.py \
      tests/test_terminal_lifecycle_refusal_is_recorded.py \
      tests/test_calculus_standing.py \
      tests/test_v6_resumed_terminal_revalidation.py \
      tests/test_v6_terminal_commitment_authority.py \
      tests/test_workflow_resume_lifecycle_c4.py tests/test_error_catalog.py \
      -q -p no:randomly --tb=line

    8 failed, 174 passed in 1036.65s (0:17:16)

## The eight, classified by whether a fixture repair could fix them

| # | test | what the gate said | class |
|---|---|---|---|
| 1 | `test_continuation.py::test_a_stop_with_no_typed_receipt_refuses_continuation` | `CONTINUE_RECORD_NOT_VERIFIED` where the test wants `CONTINUE_TYPED_STOP_REQUIRED` | PREDICTED (P-FIX-1). Fixable: one more exclusion clause in the witness predicate, assertion untouched. |
| 2 | `test_continuation.py::test_continue_keeps_manifest_and_appends_after_stop` | `CONTINUE_RECORD_NOT_VERIFIED: run-input, run-manifest-hash, terminal-authority` | NOT FIXABLE as a fixture. Its root is a v1 manifest plus a stop record; `verify_root` refuses to OPEN any non-v6 manifest (`UNSUPPORTED_RUN_MANIFEST_VERSION`), so no amount of added files makes it verify. Making it v6 moves it onto the owned-control-plane branch, where a second consecutive `prepare_continuation` is refused — and `second["seq"] == 1` is one of the assertions. |
| 3 | `test_v6_terminal_commitment_authority.py::test_typed_resume_opens_child_epoch_and_preserves_parent` | `CONTINUE_RECORD_NOT_VERIFIED: run-input, run-manifest-hash, terminal-authority` | Fixable IN PRINCIPLE: the fixture writes `run-manifest.json.sha256` (not `run-manifest.sha256`), no `run-input.json`, and never publishes `run-result.json`. Completing it is a real fixture build, and `_root(...)` is shared by ~50 tests in that file. |
| 4 | `test_amendment_epochs.py::test_partial_amendment_refuses_continuation_and_completes_on_rerun` | `AMEND_RECORD_NOT_VERIFIED: ... (amendment-chain, attached-evidence)` | NOT FIXABLE. The test drives the product's own crash-recovery road: a partially applied amendment is completed by re-running `amend`. A partial amendment MAKES the record fail `verify_root` (`amendment-chain`), so gating amend on validity means a crashed amendment can never be completed — a stranded root, which is the very "corrupted stop" the law exists to abolish. |
| 5 | `test_amendment_epochs.py::test_staged_epoch_that_never_reached_the_ledger_is_superseded` | `AMEND_RECORD_NOT_VERIFIED: ... (amendment-chain)` | NOT FIXABLE, same road: the test expects amend to SUCCEED by superseding a staged epoch. |
| 6 | `test_amendment_epochs.py::test_staged_epoch_that_applied_events_refuses_and_names_the_route` | `AMEND_RECORD_NOT_VERIFIED` where the test wants `AMEND_PENDING_CONFLICT` | Fixable by PLACEMENT: `AMEND_PENDING_CONFLICT` is raised later in `_amend_locked` than `_require_terminal_stop`, so the gate shadows it. SPEC.md S2's own stated intent is "nothing is shadowed". |
| 7 | `test_amendment_chain_integrity.py::test_amend_refuses_when_the_manifest_does_not_enable_evidence` | `AMEND_RECORD_NOT_VERIFIED` where the test wants `AMEND_EVIDENCE_NOT_AUTHORIZED` | Fixable by PLACEMENT, same shadowing. |
| 8 | `test_lifecycle_operation_parity.py::test_amend_admits_a_bound_but_unintroduced_source` | `AMEND_RECORD_NOT_VERIFIED: ... (attached-evidence)` | NOT FIXABLE. This is a regression test for a REAL committed run in which six documents were bound into the run identity and never turned into source records. `verify_root` calls that root invalid (`attached-evidence`), and `amend` is the verb that REPAIRS it. Gating amend on validity locks out the repair. |

## What the collisions actually establish

**`verify_root`'s violation set answers a broader question than the law's.**
The law asks whether a record was tampered with. `verify_root` reports every
invariant over the session, including states that are legitimate, transient,
or exactly what the next operator action is about to repair. Three of them are
load-bearing here:

- `amendment-chain` — a staged, uncommitted amendment. The recovery is to
  re-run `amend`, which the gate then forbids.
- `attached-evidence` — a bound source with no source record. The repair is
  `amend --attach`, which the gate then forbids.
- `run-input` / `run-manifest-hash` / `terminal-authority` / `open` — a root
  that is INCOMPLETE rather than tampered with. Every production root that
  reaches a stop has these; two hand-built unit fixtures do not, and one
  cannot (its manifest is v1).

Choosing a NARROWER question than `verify_root`'s — for instance, refusing
only on the SECURITY channel, which is where `frozen-route` and
`attempt-route` live and where a forged record lands — WOULD refuse the
one-byte forge and would not collide with any of the eight. `verify_root`'s
verdict and `verify_root_report`'s `valid` do not differ here: both call every
one of these findings `integrity`. So the narrowing is a genuine DESIGN
decision about what "fails replay validation" means, not a reading of the
existing code, and it belongs to the operator or the monitor. That is F9.

## What DID ship, and why it is not nothing

`deepreason results --verify` now answers `valid_typed_terminal` from the
verdict it actually re-derived (SPEC.md S7). `forge_one_byte.json`, produced by
`forge_one_byte.py` beside this file, is the whole picture in one table: of six
surfaces asked about a one-byte endpoint forgery, exactly one now sees it.

    surface                     intact                     forged
    stored_replay_valid         True                       True
    verify_root_violations      []                         attempt-route, frozen-route
    terminal_authority          current_valid_committed    current_valid_committed
    amend_gate                  PASSED                     PASSED
    results_terminal_default    True                       True
    results_terminal_verify     True                       False   <- S7
    continue_gate               CONTINUE_TYPED_STOP_REQUIRED  (same)

The security clause of the law is therefore NOT satisfied by this tranche, and
this tranche does not claim it is.
