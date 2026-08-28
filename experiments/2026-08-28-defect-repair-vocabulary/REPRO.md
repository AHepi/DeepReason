# Reproduction

Form: unit-test (offline, deterministic stub; no provider, no network)

Artifact: `tests/test_v6_repair_mode_vocabulary.py`, four tests, driven from
a root built by `tests/test_v6_engaged_repair_verification.py::_engaged_root`
— the existing engaged-repair fixture, reused rather than re-minted, extended
by one parameter (`repair_kind`) so a child's FIRST provider response can be
made unparseable instead of parseable-but-invalid. That one bit is the whole
difference between the two repair modes:

  - parseable-but-invalid first response  -> a JSON baseline exists ->
    `V6PatchRepairSession.turn` returns `mode="patch"` with a canonical
    pointer list (`llm/repair.py:1575-1596`)
  - UNPARSEABLE first response            -> no baseline can be parsed ->
    the one whole-object retry is the only turn available ->
    `mode="whole_object_syntax"`, `authorized_pointers=()`
    (`llm/repair.py:1598-1614`)

The root the fixture produces carries exactly the structural signature the
committed census records for this mode
(`probes/q5_repair_payloads.json`: every `whole_object_syntax` row has
`authorized_pointers: []` and `repair_index: 1`):

    conjecture 0 contract-decomposition-child.v1  candidate-slot-005  rejected
    repair     1 repair.semantic-task.v1  whole_object_syntax  []     completed

Current output (pre-fix tree at 2a5e984c8 + the fixture parameter and the test
file; `python -m pytest tests/test_v6_repair_mode_vocabulary.py -q`):

    F.FF                                                              [100%]
    __ test_whole_object_syntax_repair_child_recovers_instead_of_killing_the_run ___
    >       (output, call), repair_payload = _recover(whole_object_root, REPAIRED_SLOT)
    tests/test_v6_repair_mode_vocabulary.py:79: in _recover
        recover_atomic_child_output(harness, manifest, service, child, contract),
    src/deepreason/workflow/atomic_recovery.py:69: in recover_atomic_child_output
        _pointers, repaired = _repair_authority(
    src/deepreason/workflow/nonconjecture_recovery.py:1002: in _repair_authority
        _authority(mode in {"patch", "full"}, "repair mode is invalid")
    E   deepreason.workflow.nonconjecture_recovery.NonConjectureRecoveryAuthorityError: repair mode is invalid

    3 failed, 1 passed
      FAILED ...::test_whole_object_syntax_repair_child_recovers_instead_of_killing_the_run
      FAILED ...::test_the_recovery_authority_admits_exactly_what_the_producer_can_write
             (ImportError: V6_REPAIR_TASK_MODES does not exist yet)
      FAILED ...::test_no_mode_name_survives_that_nothing_emits
             (assert '"full"' not in source -> found at
              `{"patch", "full"}, "repair mode is invalid")`)
      PASSED ...::test_patch_repair_child_still_recovers_through_its_own_branch

Confirms diagnosis: yes — the raise comes from
`nonconjecture_recovery.py:1002`, reached through
`atomic_recovery.py:69`, over a payload whose `mode` is
`whole_object_syntax`; the `patch` sibling built from the SAME fixture with
the SAME call recovers cleanly in the same run of the same file, so the
rejection is on the mode string and nothing else.

**Audit residue item 3 is settled, and settled twice.** The prediction was that
the traceback would name `recover_atomic_child_output` and not
`recover_nonconjecture_admission`. It does, at
`src/deepreason/workflow/atomic_recovery.py:69`. This agrees with the record
read in DIAGNOSIS.md: epoch 5's `run-result.json` shows the failure under a
CONJECTURER-seat decomposition (`role: "conjecturer"`, `source_contract_id:
"conjecturer.turn.v6"`, `atomic_contract_id:
"conjecturer.atomic-candidate.v1"`) with `work_kind: "schema_repair"` children
hanging off `work_kind: "atomic_child"` parents — the parent/child chain
`recover_atomic_child_output` walks (`descendants[-1]` among
`repair.semantic-task.v1` items whose `parent_work_id` is the child's own id).
`recover_nonconjecture_admission`, the other reader, terminalizes NON-conjecture
work and is not on this path.

Post-fix expectation:

    4 passed

specifically:
  - `test_whole_object_syntax_repair_child_recovers_instead_of_killing_the_run`
    returns a compiled `ConjectureTurnV6` whose candidate content is the
    repair's own raw response (`"atomic mechanism 5"`), no patch applied,
    with the payload assertions (`mode`, empty pointers, `repair_index == 1`)
    still holding — so a fixture that stopped producing the killing shape
    cannot make this test pass quietly.
  - `test_patch_repair_child_still_recovers_through_its_own_branch` keeps
    passing AND still shows the patch APPLIED (`typicality == 0.5` where the
    baseline carried `2.0`), which is what stops the fix from degenerating
    into "return the raw value for every mode".
  - the two vocabulary tests pass because the reader consumes
    `V6_REPAIR_TASK_MODES` by import and the string `"full"` is gone from
    `nonconjecture_recovery.py`.

Production code untouched in this phase: the only non-test edits are the
`repair_kind` parameter on the fixture helper
(`tests/test_v6_engaged_repair_verification.py`) and the new test file.

## One finding this phase turned up, recorded here because it changes a step

GOAL.md success criterion (4) asked whether `scripts/cycle_soak.py` can provoke
a repair offline. Measured, not assumed:

    python -u scripts/cycle_soak.py --case epoch3 --cycles 8 --induce-repairs 2
    -> exit 0; D1-seat-contract disposition "covered" (not "partial"),
       detail {"repairs": 1, "distinct_contracts": ["conjecturer.turn.v6"]}
       induced_schemas ["ReasoningConjecturerTurnWireV6"]

So the schema-invalid stub mode the brief asked to ADD already exists on main
(`install_repair_inducer`, `--induce-repairs N`, landed cfe8d111c). It is not
sufficient, and the shortfall is exactly this defect's mode. Reading the soak
root's own records:

    objects/workflow-work-preparation-v1  -> 1 repair.semantic-task.v1 payload,
                                             mode "patch"

The inducer returns `{"soak_induced_repair": <title>}` — well-formed JSON, so a
baseline always parses and the session can only ever take the PATCH turn. The
mode that kills runs, `whole_object_syntax`, is still unreachable offline. The
soak work in this tranche is therefore a small addition to the existing
instrument (an unparseable induction), not a second one.
