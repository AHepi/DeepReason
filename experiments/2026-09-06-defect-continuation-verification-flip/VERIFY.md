# Verification: the two verdicts now agree, and both condemned roots re-derive clean

Goal (GOAL.md): decide which of the two `attempt-validity` verdicts over events
142, 215 and 295 is correct, and make the two agree.

**Answer, as DIAGNOSIS.md called it and as the fix now enforces it: R-STRICT.**
The events were always sound; the check was too strict after a resume. R-WEAK
survives in the narrow form the diagnosis stated and this tranche did NOT fix:
a record whose own stats list open work orders still verifies `valid: true`.
That is PARKED as P1 and untouched here — `_continuation_authority` was not
read for change and not modified.

## What changed

`src/deepreason/invariants.py`, inside `_controller_v3_history`, under the
operator's grant of 2026-09-09 ("do it") recorded in FIX.md's Grant section and
ledgered at `docs/map/INV-frozen-surfaces.md` surface 3.

`_is_patch_repair_semantic_rejection(row, admission)` — which demanded a
durable `repair.semantic-task.v1` patch chain before a non-admitted call could
carry a wire-valid attempt — is replaced by `_is_semantic_rejection(row)`,
which reads the call's attempt trace and nothing else. 19 insertions, 33
deletions, one file. Transport failures are still decided first; the
proposal-receipt and legacy-chain precedence in `_expected_call_outcome` still
runs afterwards. No record format, no new check name, no `verification/` file.

## The success criterion, run

### 1. The reproduction

`repro.py` asserts the DEFECT is present, so it exits 0 while the defect stands
and 1 once it is gone. Both states measured on this branch:

    unfixed tree (HEAD before the code commit):
      admitted   violations=0  outstanding_work_orders=[]
      abandoned  violations=0  outstanding_work_orders=['sha256:08d73cf5…']
      closed     violations=1  outstanding_work_orders=[]
                 attempt-validity: event seq=11: failed call must contain no valid attempt, got [0]
      REPRODUCED                                              (exit 0)

    fixed tree:
      admitted   violations=0  outstanding_work_orders=[]
      abandoned  violations=0  outstanding_work_orders=['sha256:08d73cf5…']
      closed     violations=0  outstanding_work_orders=[]
      NOT REPRODUCED                                          (exit 1)

Stated plainly because the instruction said "red before, green after": the
scaffold's exit code runs the other way by construction. The RED-before /
GREEN-after artifact is the committed regression below, not `repro.py`.

### 2. The committed regression — `tests/test_attempt_validity_semantic_rejection.py`

Four tests over one canonical v6 root in three states (`admitted`,
`abandoned`, `closed`), built through the real machinery:

| test | what it pins |
|---|---|
| `test_an_abandoned_work_order_and_its_honest_closure_verify_the_same` | the defect as the disagreement it produced: all three states verify with zero violations, and the abandoned root still NAMES its open work order (the fix does not hide it) |
| `test_a_wire_valid_reply_refused_on_its_semantics_is_a_semantic_rejection` | the classification itself: the closed call leaves `failure_call_seqs` for `semantic_rejection_call_seqs` |
| `test_a_non_admitted_call_with_no_wire_valid_reply_stays_a_failure` | the check does not go blind: a trace whose final attempt never parsed keeps `FAILURE_REQUIRED` |
| `test_a_valid_attempt_that_is_not_the_final_one_is_still_condemned` | the widened route is a category, not a blanket permission: a second valid attempt still violates `attempt-validity` |

    python -m pytest tests/test_attempt_validity_semantic_rejection.py -q
    -> 4 passed

**Mutation proof, both directions.**

    predicate REVERTED (git checkout of invariants.py; the unfixed tree):
      3 failed, 1 passed
      FAILED test_an_abandoned_work_order_and_its_honest_closure_verify_the_same
      FAILED test_a_wire_valid_reply_refused_on_its_semantics_is_a_semantic_rejection
      FAILED test_a_valid_attempt_that_is_not_the_final_one_is_still_condemned

    predicate OVER-WIDENED (`return True`):
      1 failed, 3 passed
      FAILED test_a_non_admitted_call_with_no_wire_valid_reply_stays_a_failure

### 3. The two committed roots — re-derived, neither root touched

Both stored `REPLAY_VALIDATION.json` files are unchanged on disk; the table
reports the STORED verdict beside the RE-DERIVED one and why they differ.

| root | stored `REPLAY_VALIDATION.json` | re-derived before | re-derived after |
|---|---|---|---|
| ARM R `run-c3f3bf10bc57d63e224a9f1c68bf1057` | `valid: false`, 3 × `attempt-validity` (seqs 142, 215, 295) | identical: 3 × `attempt-validity` | **0 violations** |
| `run-9a6be78e1e79184a0bd89923b957586c` (2026-08-04) | `valid: false`, 1 × `attempt-validity` (seq 17) | identical: 1 × `attempt-validity` | **0 violations** |

**Why stored and re-derived differ:** the stored file is a verdict WRITTEN BY
AN EARLIER VERSION of the reader, at the moment each run terminalized, and a
committed root is never edited. The re-derived verdict is this version's
reading of the same, unchanged bytes. The operator's 2026-08-14 law is what
makes that legal rather than a contradiction: old roots owe the future nothing,
and a new reader may read them differently. Nothing in either root moved — the
three ARM R events remain byte-identical, and no file under either root was
written.

**`deepreason results --json --verify`, and the one violation that does NOT
go away.** The instrument the brief names counts more than `verify_root` does:

| root | before | after |
|---|---|---|
| ARM R | `violations: 4` (integrity 4) | `violations: 1` (integrity 1) |
| 2026-08-04 | `violations: 2` (integrity 2) | `violations: 1` (integrity 1) |

The residual one, on both roots, is `run-result-verification` — "RunResult v2
records an integrity-invalid verification summary". It is not a reading of the
events at all: `verification/report.py` reads the verdict the run itself STORED
in its own `RunResult` record when it terminalized, and that stored summary
says integrity-invalid. Zero is therefore unreachable on these two roots
without editing them, which the brief forbids and which this tranche would
refuse anyway. **`verify_root`'s own violations list is empty on both**, and
that is the check the goal, the stored file, and the fix are all about. Both
roots still report `valid: false` overall for that one derived finding.

### 4. The census — no currently-clean root changes verdict

PENDING — a check-name-and-detail census over every committed root carrying a
`log.jsonl` (94 of them) is running on both trees: the fixed tree in place, and
the unfixed tree from a `git worktree` at this branch's pre-fix head with
`PYTHONPATH` pointed at its own `src/`. The diff of the two is pasted here when
it lands. What it is meant to settle: FIX.md's claim that no currently-clean
root can become dirty, because `SEMANTIC_REJECTION` accepts
`valid_indexes in ([], [len(trace) - 1])` where `FAILURE_REQUIRED` accepts only
`[]`.

## What this does NOT show

- It does not decide what an open work order SHOULD mean for `valid`. PARKED
  as P1, untouched: `_continuation_authority` was not modified.
- It does not touch the stop label (P8), the organiser seat, the measure, or
  ARM R itself. No run was re-run; no live call was made.
- It does not prove the real closures are byte-identical in construction to the
  stub's: they reference a compact-recovery authority written earlier in the
  same run where the stub commits its own. The shape the check reads — a
  non-admitted admission over a wire-valid attempt — is the same, and both
  committed roots are verified directly above, which is the stronger evidence.

## The cost, measured rather than argued

FIX.md priced road A's cost in words: "the check loses one tripwire … a record
claiming that a wire-valid reply was semantically rejected is refused; after,
it is accepted as an ordinary semantic rejection." That prediction landed on a
committed test.
`tests/test_v6_engaged_repair_verification.py::test_fabricated_valid_attempt_on_wire_invalid_turn_fails_closed`
plants `valid: true` on a wire-invalid parent turn and asserted that
`attempt-validity` refuses it. After the fix nothing refuses it: `verify_root`
returns zero violations and the report is `integrity_valid`, measured directly.

The test is KEPT and INVERTED rather than deleted, renamed
`test_fabricated_valid_attempt_on_a_wire_invalid_turn_is_no_longer_refused`,
with the grant and both run ids in its docstring — so the tripwire's absence is
pinned, and restoring it is a deliberate act that turns the test red rather
than a silent regression. This is the one assertion in the gate that this
tranche weakened, it was predicted by the design document the operator granted,
and it is stated here so the grant's price is on the record and not only in the
argument for it.

## The gate

PENDING — `python -m pytest tests/ -q -n 4` is running. The brief names three
pre-existing failures in `tests/test_organiser_seat.py` that predate this
branch (a parallel window is fixing them); they will be reported by name and
not counted as this tranche's. `docs/AUDIT_BASELINES.md` also names five tests
flaky under `-n 4` (three in `tests/test_mcp_run.py`, two in
`tests/test_mcp_scratch_bridge.py`, thread-join timing), green on a serial
re-run.

Rings already run green on the fixed tree, all at 0 failed:

    tests/test_attempt_validity_semantic_rejection.py              4 passed
    tests/test_v6_controller3_replay_verification.py               (with the below)
    tests/test_v6_engaged_repair_verification.py                  15 passed together
    tests/test_v6_nonconjecture_recovery.py
    tests/test_v6_repair_mode_vocabulary.py
    tests/test_v6_transport_failure_pairing.py
    tests/test_split_leg_recording.py                             56 passed together
    tests/test_invariant_call_outcomes.py
    tests/test_v6_verification_transactions.py
    tests/test_replay.py
    tests/test_cli_verifiers.py
    tests/test_verify_workload_roots.py                           19 passed together

The four new map checks were executed through `docs_verify`'s own runner and
all four exit 0 (`SEAM-llm-x-verification.md:173` 9.1 s, `:362` 5.0 s,
`INV-frozen-surfaces.md:322` 37.9 s, `:330` 0.7 s).

## Verdict

PENDING — the criterion is met on every instrument run so far; the verdict line
is written when the gate and the census land.

## Residue (honest)

- P1 is untouched and stays parked: a record whose own stats list open work
  orders still verifies `valid: true`, and `_continuation_authority` still
  reads only lifecycle decisions. Not read for change, not modified.
- P2 partly landed: the seam gained the ONE agreement this defect broke. The
  other three clauses (admitted, dropped, transport_failure) stay parked.
- FIX.md estimated "~10 changed lines in one file"; the delivered change is 19
  insertions and 33 deletions — a net reduction, most of the insertions being
  the new predicate's docstring. Well inside GOAL.md's 150-line budget.
- One tripwire was traded away, measured and pinned (see the section above).

## Errata

`docs/ERRATA.md` E81 — "both roots go clean" is true of `verify_root` and false
of `deepreason results --verify`, which still reports one violation on each
from a stored `RunResult` summary that cannot move without editing a committed
root.
