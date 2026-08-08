# Parked — found during Rung S5 (seats in the typed record), not fixed

## P1/P3 — pre-existing full-gate failure, not caused by this tranche

**Where found:** step 25, running `pytest tests/ -q -n 4` after all of
this tranche's code landed (and re-confirmed during `dr-validate-change`
on a second, independent full-gate run).

**What's broken:**
`tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after`
fails with `ValueError: too many values to unpack (expected 1)` on
continued root `run-a518e33a75507207633f864ba6a864b1`, which carries 2
`module_fingerprints` payloads where the test's own
`(payload,) = recorded_module_fingerprints(...)` line assumes exactly 1.

**Already diagnosed, not this tranche's finding:** the identical failure
tracked as P1/P3 in every one of Rungs S1-S4's own `PARKED.md` files
(`experiments/2026-08-06-change-seat-census-s1/PARKED.md`,
`experiments/2026-08-06-change-seat-binding-wired-s3/PARKED.md`,
`experiments/2026-08-06-change-qualification-per-seat-s4/PARKED.md`).
This rung's own REQUEST.md (C6) additionally records a fresh,
independently-verified candidate root cause not diagnosed by any prior
rung: `Scheduler._module_fingerprints_recorded`
(`scheduler.py:277`) is a PER-INSTANCE guard, reset on every
`Scheduler.__init__`, so `deepreason continue`'s fresh `Scheduler`
construction does not prevent a second stamp on the same root across a
continuation boundary. Recorded as evidence for the next diagnosis, not
diagnosed to a fix here — per this program's own convention, fixing a
pre-existing defect is out of a change-tranche's scope
(`deepreason-orchestrator`'s matter).

**Confirmed unrelated to Rung S5, two ways:**

```
$ git log --oneline 54feb5cc..HEAD -- src/deepreason/harness.py \
    src/deepreason/module_events.py tests/test_module_fingerprints.py \
    src/deepreason/scheduler/scheduler.py
bdc476e8 step 17-21: Scheduler._record_seat_bindings emission site...
4a2b5a5b step 11-13: Harness.record_seat_bindings writer...
```

Two commits touch `harness.py`/`scheduler.py` (expected — Items S5/S7
add the seat-bindings writer and emission site there), but neither
touches `module_events.py` or `tests/test_module_fingerprints.py` at
all, and the diff to `scheduler.py` is purely ADDITIVE beside the
existing mechanism: `self._module_fingerprints_recorded = False` and
`self._record_module_fingerprints()` are byte-unchanged; only a new
`self._seat_bindings_recorded = False` line and a new
`self._record_seat_bindings()` call were added immediately after each.

Second, direct proof: the identical failure reproduces on a fresh
`git worktree` at `54feb5cc` (this tranche's own base commit, before
any of Rung S5's code landed):

```
$ cd /tmp/.../pre-tranche-check   # git worktree add ... 54feb5cc
$ python -m pytest tests/test_module_fingerprints.py::test_absence_is_valid_before_the_feature_and_presence_valid_after -q
FAILED ...  ValueError: too many values to unpack (expected 1)
1 failed in 59.54s
```

**Not fixed here:** same reasoning as every prior rung's own PARKED.md
entry — a harness/continuation-record question, not a
seats-in-the-record question, and already queued for
`deepreason-orchestrator`. Not duplicating the diagnosis a fourth time;
this entry exists only to record that Rung S5's own gate run hit the
same known issue, not a new one, and to carry forward C6's fresh
candidate-root-cause evidence for whichever tranche picks it up next.

**Ready-to-run entry point:** `deepreason-orchestrator`, starting from
`dr-set-goal` with this PARKED.md paragraph plus REQUEST.md's C6 (the
per-instance-guard candidate root cause) as the starting evidence. Map
ids to open: `DR-SEAM-harness-x-verification` (reader/writer
asymmetry), `DR-SUB-scheduler` (`Scheduler.__init__`/`run`'s per-instance
attribute lifecycle).

## No other defects surfaced

Every step of this rung's own CHECKLIST.md landed on the first or
second attempt (the harness.py third-hunk risk at step 11 was traced
and resolved by design, per REQUEST.md R19, not a defect) with no
edited assertion and no fixture weakened. Two budget overruns were
found and disposed of by explicit operator authorization
(REQUEST.md Amendments 2 and 3, R21/R22) — not defects, and not parked,
since both are fully resolved and recorded in VALIDATION.md.
