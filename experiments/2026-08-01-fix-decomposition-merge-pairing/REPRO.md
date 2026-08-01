# Reproduction

Form: unit-test (offline)

Artifact:
  `tests/test_v6_engaged_repair_verification.py::test_merge_whose_child_was_repaired_verifies_clean`
  parametrised `[first-child]` (slot 0) and `[latest-child]` (slot 5), plus the
  guard `::test_the_repaired_child_slot_really_names_repair_work`.

Record replay was available and cheaper, but it cannot be the durable artifact:
`experiments/live_jolt_2026-07-31/home/` is gitignored, so a test that reads
that root would pass vacuously on any fresh checkout. The offline fixture is
built instead by extending `_engaged_root` (the `1de1f690` fixture) with a
`repair_child` parameter that makes one atomic child's first response
wire-invalid, so the harness re-dispatches that child as
`repair.semantic-task.v1` and the completion names the repair in that slot.

Both positions are exercised deliberately. Slot 5 is the LATEST child, whose
provider call the merge marker names, so a repair there moves the marker as
well as the payload schema — if the diagnosis had been wrong about which gate
fails, the two positions would not behave identically.

Current output:

    $ python -m pytest tests/test_v6_engaged_repair_verification.py -q
    FAILED ...::test_merge_whose_child_was_repaired_verifies_clean[first-child]
    FAILED ...::test_merge_whose_child_was_repaired_verifies_clean[latest-child]
    2 failed, 7 passed

    E  AssertionError: assert [{'check': 'w...der attempt'}] == []
    E    Left contains one more item: {'check': 'workflow-call-pairing',
    E     'detail': 'event seq=64: Conj outputs are not uniquely admitted by
    E                their provider attempt'}

A probe over the same fixture, before the tests were formalised:

    repair_child=None   integrity_valid True   findings []
                        child schemas: [child, child, child, child, child, child]
    repair_child=0      integrity_valid False  findings ['event seq=64: ...']
                        child schemas: [repair, child, child, child, child, child]
    repair_child=5      integrity_valid False  findings ['event seq=64: ...']
                        child schemas: [child, child, child, child, child, repair]

Confirms diagnosis: yes — the finding appears if and only if a completion names
a `repair.semantic-task.v1` work item in some slot, at either end of the batch,
and the message is verbatim the one the live root carries at Conj seq 245/386.

Two controls make the reproduction load-bearing rather than incidental:

  - `test_the_repaired_child_slot_really_names_repair_work` PASSES today. It
    asserts the fixture actually produced a repair-named slot, so the failing
    assertion above cannot be blamed on a fixture that quietly stopped
    repairing. Without it the regression could go green post-fix while
    exercising nothing.
  - The three existing fail-closed negatives
    (`..._bound_to_non_latest_child_fails_closed`,
    `..._bound_to_non_child_work_fails_closed`,
    `..._fabricated_valid_attempt_on_wire_invalid_turn_fails_closed`) all still
    pass, so the exemption has not been loosened by the fixture change itself.

Post-fix expectation:

    $ python -m pytest tests/test_v6_engaged_repair_verification.py -q
    9 passed

with `test_the_repaired_child_slot_really_names_repair_work` still passing (the
shape is still produced) and all three fail-closed negatives still passing (the
exemption did not widen beyond the repair chain).

Production code untouched: `git diff --stat -- src/` is empty at this phase.
