# Goal: give `CONTINUE_TYPED_STOP_REQUIRED` a regression the full gate runs
Class: regression-risk
Observed: `CONTINUE_TYPED_STOP_REQUIRED` is raised at exactly one site,
`src/deepreason/runtime/continuation.py:352`, and **no test the gate runs
exercises it.** Repo-wide the string appears four times:

    src/deepreason/runtime/continuation.py:352   the raise site
    scripts/wheel_operational_smoke.py:2061-2062 the smoke's matcher
    tests/test_wheel_operational.py:1383         a unit test OF that matcher

The third is `test_operational_smoke_requires_exact_non_resumable_rejection`,
which feeds two strings to `_assert_non_resumable_rejection` and checks
which are accepted. It never calls `prepare_continuation`, never builds a
run root, and would keep passing if the product stopped refusing
entirely.

The only end-to-end witness is `scripts/wheel_operational_smoke.py`,
which **no `pytest` run executes** — it runs solely in CI's wheel-smoke
job. Evidence:
`experiments/2026-08-05-fix-continue-run-rejection/PARKED.md` W1 and
`VERIFY.md`.

This is not a hypothetical exposure. It is how the defect that tranche
just fixed survived from 2026-07-27 to 2026-08-05: `2d4ca2e1` changed
what a budget-exhausted stop authorizes, the full gate stayed green
throughout, and the only instrument that would have objected was red for
an unrelated reason the whole time.

Success criterion (machine-decidable):

    python -m pytest tests/ -q -n 4
    -> ends "0 failed" (3339 today) with at least one NEW test that
       calls prepare_continuation on a root carrying no typed STOPPED
       receipt and asserts ValueError("CONTINUE_TYPED_STOP_REQUIRED")

    # mutation proof, run before the test is committed
    remove or weaken continuation.py:352 -> the new test FAILS
    restore                              -> the new test PASSES

    python tools/docs_verify.py
    -> "docs_verify: 0 failed"

In scope (2):
- `tests/` — the new regression, in the file the map already routes to
  for this code (`DR-SUB-application`'s Verify line runs
  `tests/test_continuation.py`; the resumable twin lives in
  `tests/test_v6_resumed_terminal_revalidation.py`). Which of the two
  hosts it is a `dr-propose-fix` decision, not a goal decision.
- `docs/map/SUB-application.md` — its Traps entry currently says the
  smoke is the only witness. If that stops being true, the entry moves
  in the same commit.

NOT in scope: **`src/` — nothing.** `2d4ca2e1` is a named owner decision
and the current behaviour is correct; this tranche adds coverage, not
behaviour. If writing the test appears to require a product change, that
is a finding to report, not a licence to make one. Also not in scope:
W2 (the unmeasured cancel race) and W3 (the six stages with one green
observation each) — both stay parked.

Budget: <=150 changed lines, 1 commit, ~2 hours.
Stop conditions inherited from orchestrator: yes — including the
~150-line ceiling, which the previous tranche exceeded without stopping.
That is a recorded process failure and is not to be repeated: if the
estimate moves past the ceiling, the plan is re-presented before the
code is written.

## On the class, stated rather than finessed

`dr-set-goal` says only `defect` tranches may proceed to implementation
without explicit operator approval. This is `regression-risk`: nothing
is broken, and the behaviour IS documented (`2d4ca2e1`,
`DR-SUB-application`'s Traps) — what is missing is a guard. Recording it
as `defect` to unlock implementation would be a convenient
misclassification.

The approval that class requires is already given: the operator said
"W1 next", and W1's parked entry states the goal, the method and the end
state. That is the authority this tranche runs on.

## Map preflight (resolved ids)

- `DR-SUB-application` — `Owns: … src/deepreason/runtime/`, so it owns
  `continuation.py`. Its Traps section already carries the two entries
  this work sits between: the `_record_exhaustion_lifecycle_stop` entry
  (owner decision 4a) and the entry the previous tranche added, which
  says in as many words that the smoke is the only end-to-end witness.
  Its `Verify:` line runs `tests/test_continuation.py`, so a regression
  placed there is re-run whenever that document is verified.
- `DR-CON-run-identity` — start-vs-continue dispatch; read for the
  vocabulary distinction between `RUN_ALREADY_STARTED` (occupancy) and
  the continuation refusals.
- `DR-INV-frozen-surfaces` — read. None of the five names the
  continuation dispatch. A test-only change touches none of them, and
  the root sweep is not the instrument for a change that adds a test.

### Carried map finding, still open

`application × periphery` remains an unwritten seam and is absent from
`INDEX.md`'s matrix entirely; `SUB-application.md`, `SUB-periphery.md`
and `SUB-amendment.md` are on disk but routable from no `INDEX.md`
table. Recorded at the previous tranche's preflight, unchanged here, and
still parked — this tranche has no reason to touch either.

## The trap this tranche must not fall into

A test that reaches `CONTINUE_TYPED_STOP_REQUIRED` by monkeypatching
`_record_exhaustion_lifecycle_stop` to return `None`, or by handing
`prepare_continuation` a hand-built state, would pass and prove almost
nothing: it would assert that a function raises when told to. The
refusal is worth guarding because a REAL run can still reach that state
— `text_runs.py` records the typed receipt only inside the
`budget_exhausted` branch, so an operator cancellation falls through to
the bare fail-closed stop. `dr-reproduce` must show the state arising
from a run, not from a fixture asserting it into existence.
