<!-- tranche: 2026-09-04-defect-dead-seat-retirement -->

# Reproduction

**Form:** offline unit reproduction (form 2). No provider, no live run; the
whole thing takes 4.3 seconds.

**Artifact:** `tests/test_dead_seat_retirement.py` —
`test_the_p_a1_shape_runs_on_the_healthy_seat_after_the_dead_one_exhausts` and
`test_a_dead_seat_does_not_kill_the_run_through_the_atomic_recovery_road`.
RED transcript at `proof/repro_red.txt`.

## What the fixture is

P-A1's shape, shrunk from four schools to two, with everything load-bearing
kept real: a bound v6 root, route-bound school execution, two conjecturer
seats on two endpoints, the `conjecturer.turn.v6` → `conjecturer.
atomic-candidate.v1` ladder, the production-contract classification, and P-A1's
own repair grant read off its record (`maximum_schema_repairs` 4,
`maximum_provider_calls` 5). `school-0` is bound to seat 0, whose endpoint
always answers with a valid candidate; `school-1` is bound to seat 1, whose
endpoint never returns valid output. The run is then driven through
`Scheduler.step()`.

## Current output

    $ python -m pytest tests/test_dead_seat_retirement.py -q
    E  AssertionError: one dead seat ended the whole run while a healthy seat
       was answering: RunManifestError: V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY
       at /workflow/insufficient_capability_by_route_seat: route seat has
       terminally exhausted its smallest authorized contract
    E  AssertionError: the atomic-recovery road ended the run on a dead seat:
       ValueError: atomic child is terminally failed
    FAILED tests/test_dead_seat_retirement.py::test_the_p_a1_shape_runs_on_the_healthy_seat_after_the_dead_one_exhausts
    FAILED tests/test_dead_seat_retirement.py::test_a_dead_seat_does_not_kill_the_run_through_the_atomic_recovery_road
    2 failed in 4.34s

Both assertions fire only AFTER two guards that the fixture itself checks: the
dead seat really did exhaust (`insufficient_capability_by_route_seat` carries
its key) and the healthy seat really did complete work. So the failure is the
defect and not a broken fixture.

## Confirms diagnosis: YES, and it found a second road

**The prediction held.** `DIAGNOSIS.md` predicted a `RunManifestError`
containing `V6_ROUTE_SEAT_INSUFFICIENT_CAPABILITY`, on a run whose healthy
seat had completed work and whose budget was untouched. That is exactly the
first test's failure, at scheduler step 1, with one completed turn already
recorded on seat 0 and a 2 000 000-token meter barely touched. The mechanism
is the one the diagnosis named: the per-seat guard in
`InquiryTransactionService.prepare` refuses, and no arm of the school loop
catches a `RunManifestError`.

**And the fixture found a road the live record does not show.** When the dead
seat's next dispatch carries the SAME task payload — which happens whenever the
scheduler re-selects the problem the exhaustion occurred on — `rules/conj.py`
enters its atomic-decomposition recovery branch first, because the exhaustion
left that decomposition incomplete, and
`workflow/atomic_recovery.py:40` raises `ValueError("atomic child is terminally
failed")` **before the insufficient-capability guard is consulted at all**.
P-A1 took the first road rather than this one for a reason the record makes
plain: it had many problems, so the dead seat's next dispatch carried a payload
it had not seen. A one-problem run takes the second road on the very next
cycle.

This is the single most important thing this phase produced, and it constrains
the fix rather than merely decorating it: **a fix wired into the
insufficient-capability guard alone leaves the second road open.** Retirement
has to be decided where the seat is CHOSEN — before `conj` is entered — not
where a dispatch is refused. Both tests are in the committed suite so a fix
that closes one and not the other stays red.

## Post-fix expectation

    $ python -m pytest tests/test_dead_seat_retirement.py -q
    2 passed

with, in both tests, the dead seat still exhausting (the fixture asserts it),
the healthy seat still completing work, and the scheduler completing six cycles
without raising. `dr-implement-fix` adds the remaining GOAL.md clauses —
the typed retirement in `deepreason results`, the all-seats-dead clean stop and
its `continue`, the per-run switch and its warning, and the consumer census —
to this same file.

## What this reproduction does NOT show

- Nothing about the ALL-seats-dead case; that shape is not built yet.
- Nothing about whether the exhaustion SHOULD have happened. The dead seat here
  exhausts on invalid output, where P-A1's exhausted after a transport-fault
  streak on a seat that had qualified 20/20. That difference is real and is
  parked as `PARKED.md` P1, not smuggled into this fix.
- No committed run root was opened for writing; P-A1's root was read read-only
  and is unchanged.
