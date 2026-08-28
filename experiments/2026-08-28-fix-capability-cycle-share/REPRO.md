# REPRO — the defect, demonstrated offline

Phase: `dr-reproduce`. Reads DIAGNOSIS.md. Smallest offline artifact; no live
run, no provider call, no credential.

## The artifact

Four tests appended to the owning suite, `tests/test_wander_cap.py`, under the
heading `--- P12: capability cycles, the denominator, and the silence ---`.

The driver is the honest part. CAPABILITY cycles call the real
`Scheduler.step()`; only `_simulation_capability_step` is stubbed, to exactly
its observable contract — the `cycle` heartbeat the shipped one emits at
`scheduler.py:1802/1950/2030`, and `True` to claim the cycle. So the branch
that early-returns runs as it ships. SELECTION cycles are driven the way the
suite's existing `_drive` drives them (select, emit, advance), because
`step()`'s selection path continues into conjecture and this fixture binds no
seats.

## The control arm reproduces epoch 1 bit-for-bit

Before claiming anything about the broken path, the fixture is shown to
reproduce the working one. `test_the_offline_spawner_reproduces_epoch_1_bit_for_bit`
drives 12 cycles with zero capability cycles at floor `0.5` and asserts the
share trajectory equals epoch 1's committed one, verbatim from
`probes/q3_cycle_accounting.json`:

    1.000000 1.000000 0.500000 0.333333 0.500000 0.400000
    0.500000 0.428571 0.500000 0.444444 0.500000 0.454545

with 5 throttles and the first disclosure string
`wander-cap.v1: seed-lineage share 0.3333 below floor 0.5000`. It PASSES today
and must keep passing: it is this tranche's S3 pin, not a demonstration of the
defect.

## The defect, demonstrated

`test_capability_cycles_do_not_dilute_the_floor` drives epoch 6's shape —
4 selection cycles and 20 capability cycles at floor `0.5` — and fails RED:

    assert 4 == 24
      where 4 = len([... '1.000000' ... '1.000000' ... '0.500000' ... '0.333333' ...])

24 cycle heartbeats, `scheduler._cycles == 24`, and **four** readings. Exactly
the live shape: the same four values epoch 6 recorded, then twenty cycles of
silence.

`test_the_denominator_is_order_independent` interleaves the same counts
(selection, then five capability, four times over) and fails RED showing the
dilution directly:

    assert 4 == 24
      where 4 = len([... '1.000000' ... '0.166667' ... '0.166667' ... '0.166667' ...])

`0.166667` is `1/6`: the one seeded cycle worked so far, over a denominator
that has swallowed five capability cycles. This is the arithmetic the audit
called "a reading that means something nobody chose" — and it is what the
policy would act on if the early return were simply deleted without deciding
the accounting question first.

## The fourth test guards the fix, not the defect

`test_a_capability_cycle_discloses_without_inventing_a_throttle` passes both
before and after by design. Before, vacuously (there are no capability-cycle
records at all). After, it is the guard that emitting a reading every cycle
did not also turn twenty cycles of one experiment into twenty throttling
decisions, or twenty policy artifacts.

## RED output, verbatim

`proof-repro-red.txt`, committed beside this file:

    2 failed, 2 passed, 16 deselected in 0.38s
    FAILED tests/test_wander_cap.py::test_capability_cycles_do_not_dilute_the_floor
    FAILED tests/test_wander_cap.py::test_the_denominator_is_order_independent

No production code has changed at this point.
