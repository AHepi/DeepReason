# Diagnosis: the refusal is uncovered because reaching it needs a whole run root, and every offline test either stops at an earlier guard or builds the resumable twin

Primary cause: `CONTINUE_TYPED_STOP_REQUIRED`
(`src/deepreason/runtime/continuation.py:352`) is the final `else` of a
three-way branch that is only evaluated after `prepare_continuation` has
already cleared a stop-digest check, a checkpoint-shape check, a
`checkpoint.json` canonicalisation, a `Harness` open and a
`workflow-checkpoint.json` digest. Nothing reaches it without a
materially complete run root. The two test files that could have covered
it each miss for their own reason:

- `tests/test_continuation.py` (103 lines, 4 tests) builds manifests at
  schema v1 and v3. Those paths refuse EARLIER —
  `test_v3_continuation_requires_checkpoint` asserts exactly that, with
  `CONTINUE_CHECKPOINT_REQUIRED` — so the typed-stop branch is never
  entered.
- `tests/test_v6_resumed_terminal_revalidation.py` builds real v6 roots
  through `TextRunApplicationService`, which is the machinery that
  COULD reach line 352, and every one of its 12 tests constructs a run
  that is meant to resume. `test_budget_exhausted_terminal_is_a_typed_
  resumable_stop` is the closest, and it is the exact inverse: it
  asserts the receipt is PRESENT.

So the branch was never anyone's subject. That is a coverage gap, not a
defect in behaviour — the behaviour is correct and documented.

## The state is not hypothetical: 12 of 28 committed roots are in it

Every git-tracked run root carrying a `run-stop.json`, opened read-only
and grouped by whether it holds a typed STOPPED receipt:

    reason='budget_exhausted'     terminal=yes   resume=NO   n=16
    reason='budget_exhausted'     terminal=NO    resume=NO   n=7
    reason='operational_failure'  terminal=NO    resume=NO   n=5

The 16 are post-`2d4ca2e1` roots carrying the receipt owner decision 4a
introduced. **The other 12 are exactly the state the raise site
guards**, and they are committed evidence, not fixtures.

Two distinct populations, and the difference matters for a durable test:

- **7 `budget_exhausted` roots with no receipt.** These predate
  `2d4ca2e1` (or could not carry the receipt). Their class is FROZEN by
  the append-only principle — a committed root's stop record never
  changes — but the class stops GROWING, because new budget stops now
  get a receipt.
- **5 `operational_failure` roots.** `operational_failure` is not in
  `RESUMABLE_STOP_REASONS` and there is no mechanism that gives it a
  typed receipt, so this class is both frozen and permanent. It is the
  durable witness.

## The reproduction is already in hand, in the cheapest form

`dr-reproduce` ranks record replay first. Seven committed roots copied
to a temp directory and passed to `prepare_continuation(cycles=1,
tokens=10, check_operator_lock=False)`:

    run-f4fa6663e5412d64df943a5a22342baf   budget_exhausted    -> ValueError: CONTINUE_TYPED_STOP_REQUIRED
    failed-epoch1-run-0d1f88e18779b7eb…    operational_failure -> ValueError: CONTINUE_TYPED_STOP_REQUIRED
    run-e542c3c1fc266943e0260c5aa8d7c107   operational_failure -> ValueError: CONTINUE_TYPED_STOP_REQUIRED
    failed-epoch1-run-9175f0ecb055e574…    operational_failure -> ValueError: CONTINUE_TYPED_STOP_REQUIRED
    failed-epoch2-run-9175f0ecb055e574…    operational_failure -> ValueError: CONTINUE_TYPED_STOP_REQUIRED
    run-0c3ce902cc5bca75a709b04e2473d100   operational_failure -> ValueError: CONTINUE_TYPED_STOP_REQUIRED
    run-15a53aca8a6fc66a39f382fc688c5346   budget_exhausted    -> ValueError: CONTINUE_TYPED_STOP_REQUIRED

Seven for seven, the exact raise. Copies, never the originals — a
committed root's contents are never modified, and `prepare_continuation`
writes `continuations.jsonl` on the paths that succeed.

**This satisfies GOAL.md's stated trap.** The goal forbade reaching the
raise by monkeypatching `_record_exhaustion_lifecycle_stop` to return
`None`, on the grounds that such a test asserts only that a function
raises when told to. Nothing is patched here: these are runs that really
stopped, recorded before this tranche existed, and the state arises from
their own history.

## Evidence (record pointers)

- The census above, over `git ls-files experiments runs` filtered to
  `run-stop.json` — 28 roots, read through `Harness(root,
  read_only=True).workflow_state`, comparing
  `terminal_lifecycle_decision` and `current_resume_decision` against
  each root's own `run-stop.json` `reason`.
- `src/deepreason/workflow/lifecycle.py:28` —
  `RESUMABLE_STOP_REASONS = frozenset({"converged", "budget_exhausted"})`;
  `operational_failure` is absent and no code path adds it.
- `src/deepreason/runtime/continuation.py:220-352` — the three-way
  branch: `if terminal is not None` … `elif current_resume is not None`
  … `else: raise ValueError("CONTINUE_TYPED_STOP_REQUIRED")`.
- `experiments/2026-08-05-fix-continue-run-rejection/REPRO.md` — the
  same refusal observed end to end through the installed facade on a
  cancelled run, which is the LIVE path into the same state.

## Implicated code (0 sites)

None. This tranche adds a test; `src/` is correct and is not touched.
The implicated artefact is the absence of a test, and the gap is in
`tests/`.

## Falsifiable prediction (what `dr-reproduce` must show)

    # The refusal must be attributable to the missing receipt, not to an
    # earlier guard that happens to fire on the same roots:
    for each committed root with no terminal lifecycle decision and a
    stop reason outside RESUMABLE_STOP_REASONS:
        prepare_continuation(copy) -> ValueError("CONTINUE_TYPED_STOP_REQUIRED")

    # and the mutation proof, which is what makes it a regression rather
    # than a snapshot:
    delete or weaken continuation.py:352 -> the new test FAILS

If the second half does not hold, the test is passing for some other
reason and does not guard the refusal at all.

## Ruled out

- **That the state only arises from operator cancellation.** The live
  path found in the previous tranche was `cancel_run`, and it would have
  been tempting to build the test around it — expensively, since it
  needs a running worker and a cancellation race. The census refutes the
  premise: 12 committed roots reach the state without any cancellation,
  5 of them through `operational_failure`, which cancellation is not.
- **That a committed root might reach the raise for the wrong reason.**
  Checked directly rather than assumed: the seven probed roots return
  `CONTINUE_TYPED_STOP_REQUIRED` and not
  `CONTINUE_CHECKPOINT_REQUIRED`, `CONTINUE_WORKFLOW_CHECKPOINT_REQUIRED`
  or `CONTINUE_STOP_DIGEST_MISMATCH` — so they clear every earlier guard
  and fail at the intended one.
- **That `src/` is implicated.** `2d4ca2e1` is a named owner decision,
  gate-enforced and documented in `DR-SUB-application`. GOAL.md forbids
  a product change and nothing here asks for one.
