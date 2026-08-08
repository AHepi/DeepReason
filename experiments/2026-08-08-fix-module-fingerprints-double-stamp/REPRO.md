# Reproduction

Form: record-replay (the failing test itself, run against the
committed record — no fixture needed; the defect is already captured
in `experiments/2026-08-05-testphase-live-validation/home-testphase/
runs/run-a518e33a75507207633f864ba6a864b1`, a continued root).

Artifact:
    python -m pytest tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after -q

Current output:

    F                                                                        [100%]
    =================================== FAILURES ===================================
    ______ test_absence_is_valid_before_the_feature_and_presence_valid_after _______
    ...
        for root in stamped:
    >       (payload,) = recorded_module_fingerprints(Harness(root, read_only=True))
            ^^^^^^^^^^
    E       ValueError: too many values to unpack (expected 1)

    tests/test_module_fingerprints.py:90: ValueError
    =========================== short test summary info ============================
    FAILED tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after
    1 failed in 78.27s (0:01:18)

Second check, confirming DIAGNOSIS.md's falsifiable prediction part
(b) — the two stamps on the offending root are byte-identical, i.e.
the same payload was legitimately re-emitted by the per-instance
writer guard across the continuation boundary, not two disagreeing
payloads (which would instead have pointed at a writer defect):

    python3 -c "
    from deepreason.harness import Harness
    from deepreason.module_events import recorded_module_fingerprints
    root = 'experiments/2026-08-05-testphase-live-validation/home-testphase/runs/run-a518e33a75507207633f864ba6a864b1'
    payloads = recorded_module_fingerprints(Harness(root, read_only=True))
    print('count:', len(payloads))
    for p in payloads:
        print('digest:', p.digest, 'modules:', [(m.registry, m.module_id) for m in p.modules])
    print('all digests equal:', len({p.digest for p in payloads}) == 1)
    "

Output:

    count: 2
    digest: ebe196411351a47abb87716a534c7d4e3cbd7b2648c4b29d1fb3cede4ce1825d modules: [('school-population', 'default')]
    digest: ebe196411351a47abb87716a534c7d4e3cbd7b2648c4b29d1fb3cede4ce1825d modules: [('school-population', 'default')]
    all digests equal: True

Confirms diagnosis: yes — both halves of the falsifiable prediction
hold. (a) the test fails today with the exact ValueError DIAGNOSIS.md
predicted, on the exact root PARKED.md/REQUEST.md/SPEC.md name; (b)
the two stamps are byte-identical, matching S6 audit2's seat-bindings
finding exactly (same digest, same content, both survive
`Scheduler._module_fingerprints_recorded`'s per-instance reset across
`deepreason continue`'s fresh `Scheduler` construction) — this is the
writer legitimately re-emitting the SAME answer, not disagreeing
answers, which is the signature DIAGNOSIS.md said would rule the
writer defect back IN had it been found. It was not found.

Post-fix expectation: `python -m pytest
tests/test_module_fingerprints.py::
test_absence_is_valid_before_the_feature_and_presence_valid_after -q`
passes, asserting — for every stamped root — at least one payload
(never a single-unpack), all payloads well-formed
(`schema_ == "module-fingerprints.v1"`, non-empty `modules`, non-empty
`digest`), matching the partition-claim shape S5's sibling
`test_seat_bindings_record.py` already uses for the identical
mechanism. `run-a518e33a75507207633f864ba6a864b1`'s 2 stamps continue
to be read, not rejected or silently truncated to the first/last.
