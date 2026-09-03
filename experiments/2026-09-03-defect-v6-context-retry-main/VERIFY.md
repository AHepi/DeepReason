# VERIFY — the fix against GOAL.md's success criterion

Four criteria were written in GOAL.md before any code moved. Each is
answered here with the command that answers it, not with a summary.

## 1. The regression file is byte-identical to the originating commit

    $ git show 06b0d9fd9:tests/test_scheduler_v6_context_plan_retry.py | sha256sum
    03c84608a418455df5ea341d5ead01fde65c7c0c8ddfedd6fe00069d37c68858  -
    $ sha256sum tests/test_scheduler_v6_context_plan_retry.py
    03c84608a418455df5ea341d5ead01fde65c7c0c8ddfedd6fe00069d37c68858  tests/...

**PASS.**

## 2. Mutation proof, ON MAIN

5 passed → (pre-fix retry line restored) 2 failed / 3 passed → (fix
restored) 5 passed, with the test file's sha256 identical at every
step. Full transcript in `mutation.log`; table and the failing
assertion in REPRO.md §Results.

**PASS**, and it matches the result the originating commit recorded on
its own tree, which is what makes the transplant a transplant rather
than a new claim.

## 3. Full gate

<!-- GATE -->

## 4. docs_verify

<!-- DOCSVERIFY -->

## What is NOT proven here, stated plainly

- **No live run was made.** The proof is offline and structural. The
  live evidence this fix answers to is the two roots in DIAGNOSIS.md,
  both of which predate the fix; nothing in this tranche demonstrates
  a v6 run surviving a stale context on a provider. The next v6 ladder
  that fires the scratchpad is the live test, and it is not owed by
  this tranche.
- **The reachability condition is unchanged.** `ConjectureContextStale`
  is still raised from the same three sites in `scratch/conjecture.py`,
  and the retry is still reachable only when the scratchpad is live.
  This fix makes that retry survivable; it does not make the stale
  context less likely, and no claim is made that it should.
- **The originating branch carries more than this.** Only the two
  files came across. Whatever else `claude/model-profile-registry-opkgal`
  holds is untouched by this tranche and is not asserted to be sound
  or unsound here.
