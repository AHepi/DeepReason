# Verification

## Criterion (a) — FAILS AS WRITTEN, and the criterion was wrong

    $ python -c "from deepreason.invariants import verify_root_report; ...
        print(r.integrity_valid, sum(1 for f in r.integrity if f.check=='workflow-call-pairing'))"
    False 0

The pairing count went 2 -> 0: the defect is fixed. But `integrity_valid` is
still `False`, and GOAL.md demanded `True`. The remaining finding is the whole
story:

    integrity | run-result-verification | terminal
      RunResult v2 records an integrity-invalid verification summary

`run-result.json` carries the run's own `verification.summary.v2`, written at
terminal time:

    integrity_valid: false
    finding_counts: {integrity: 2, completion: 49, operational: 18, ...}

So the root durably asserts its own invalidity, and the checker compares the
live verdict against that recorded assertion. **A reader fix cannot make an
already-written root claim it was valid**, because the claim is in the
append-only record. That is correct behaviour, not a shortfall — CLAUDE.md's
"the record is law" applies to a run's self-report exactly as it applies to
everything else.

The criterion was therefore unachievable the moment the run terminated, and I
wrote it anyway in `dr-set-goal`. It should have asked for zero
`workflow-call-pairing` findings, which is the thing the fix can affect, and
said explicitly that the terminal self-report is immutable. **The criterion is
NOT amended here.** Rewriting a success criterion after seeing the result is
moving the goalposts, and this file records the failure instead so the operator
decides.

## Criterion (b) — PASS

Identical script, pre-fix baseline captured with pre-fix code, re-run after:

    lines before/after: 42 / 42
    ERROR lines: 0 before, 0 after

    19c19
    < .../run-b4d6dfda0c20676a864a051fbc97bda4 integrity=False security=True pairing=2
    ---
    > .../run-b4d6dfda0c20676a864a051fbc97bda4 integrity=False security=True pairing=0

Exactly one line differs, on exactly one field, on exactly the target root. All
41 other roots byte-identical — including `failed-epoch1-run-b4d6dfda…`,
the turmite root, and the four roots that were already `integrity=False` for
unrelated reasons (`selfstudy` epochs 1-3, `wide/run-0c3ce902`,
`jolt_architecture_2026-07-16`). No previously-valid root was invalidated and
no previously-invalid root was silently made valid.

## Criterion (c) — PASS

    before (REPRO.md):  7 passed, 2 failed
    after:              11 passed

The two `test_merge_whose_child_was_repaired_verifies_clean` parametrisations
inverted. `test_the_repaired_child_slot_really_names_repair_work` still passes
at both positions, so the inversion is not a fixture that quietly stopped
repairing. All three pre-existing fail-closed negatives still pass, including
`test_merge_conj_bound_to_non_child_work_fails_closed`, which FIX.md named in
advance as the test that would expose a false positive.

## Criterion (d) — PASS

    $ pytest tests/ -q -n 4
    3238 passed, 7 skipped in 644.91s

0 failed. No assertion weakened anywhere; the two fixtures that changed were
extended, not relaxed.

## No committed run root modified

    $ git status --porcelain | grep -E "runs/|/home/"
    (none)

## Verdict: PASS on the defect, FAIL on criterion (a) as written

The mechanism DIAGNOSIS.md named is fixed and the fix is contained: 2 -> 0
pairing findings on the target root, zero movement on 41 others, offline
regression inverted, gate green. Runs written from now on will not carry this
finding.

The historical root stays `integrity_valid: False` forever, because it recorded
that verdict about itself. Whether that is acceptable, or whether the tranche
should have targeted something else, is the operator's call — see Residue.

## Residue (honest)

- **`run-b4d6dfda0c20676a864a051fbc97bda4` is still not replay-valid** and
  cannot be made so by any reader change. Only a fresh run of that question
  would produce a clean root. Not attempted: GOAL.md required no live proof,
  and a relaunch is a different tranche.
- **GOAL.md's criterion (a) was mis-specified by me.** Recorded, not amended.
  Any future goal touching an already-terminated root must distinguish live
  findings from the terminal self-report.
- **The new helper's parent guards are untested behaviour.** All three
  fail-closed conditions FIX.md promised require a preparation record naming a
  parent the writer would not name, and preparations load through a
  digest-verified object store, so any such edit raises `corrupt object record`
  and fails closed on `workflow-decision` before the pairing check runs
  (measured; pinned by `test_a_tampered_repair_preparation_fails_closed`). The
  `contract_id` / `route_lease` / `target_refs` branches are therefore
  defence-in-depth against a future WRITER change, not against a forged record,
  and no test exercises them. They are copied verbatim from the writer's own
  check (`workflow/replay.py:713-723`) rather than invented.
- **Repair chains deeper than one hop, and more than one repaired slot per
  batch, are untested.** The live run has exactly one repaired child per
  affected merge, both at index 1 of their chain; the fixture reproduces one
  repaired slot at a time. The walk is written to handle both (bounded `seen`
  set, loop rather than single hop) but nothing proves it.
- **Attribution stands from the prior investigation, not from this tranche:**
  the defect is pre-existing, unmodified since `1de1f690` (2026-07-26).
- **PARKED.md holds nine unrelated findings**, including the `run-status.json`
  reporting defaults that caused this run's outcome to be misreported, and the
  `OBSERVE_ONLY` text-workload authority under which no text run can attack
  anything. Those are candidate next tranches, not part of this one.
