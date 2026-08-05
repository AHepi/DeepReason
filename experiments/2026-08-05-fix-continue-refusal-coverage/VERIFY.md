# Verification

## Verdict: **PASS**

## Criterion commands + output, run at `a65e8578`, each instrument alone

    $ python -m pytest tests/ -q -n 4
    3340 passed, 7 skipped in 610.88s (0:10:10)
    -> PASS (0 failed; 3339 + exactly the one test added)

    $ python tools/docs_verify.py
    docs_verify [full]: 51 documents, 816 checks, 4 workers
    docs_verify: 0 failed
    $ python tools/docs_verify.py --audit
    docs_verify --audit: 0 finding(s)
    -> PASS

    $ python -m pytest tests/test_continuation.py -q
    5 passed in 12.93s
    -> PASS (4 existing, unedited, plus the new guard)

GOAL.md's second criterion was a mutation proof rather than a command,
and it is the one that matters here — the test passes today because the
product is correct, so a green run proves nothing on its own.

## The mutation proof, re-run under `pytest` rather than as a script

FIX.md required both mutations to be re-run against the committed test,
because assertion mechanics differ under `pytest`. Both kill it, through
the intended and DIFFERENT assertions:

| mutation | failing assertion |
|---|---|
| `RESUMABLE_STOP_REASONS` widened to include `operational_failure` | `AssertionError: no committed root carries a non-resumable stop; the refusal has lost its witness` |
| `continuation.py:352` raises `CONTINUE_NOT_AUTHORIZED` | `AssertionError: failed-epoch1-run-0d1f88e1… stopped on 'operational_failure' and was refused for the wrong reason: CONTINUE_NOT_AUTHORIZED` |
| restored | `1 passed in 8.30s` |

`git status --porcelain src/` was clean after each restore, so no
product file was left mutated.

**Both are recorded because neither substitutes for the other**, and
this was measured rather than assumed. The instruction proposed proving
the test via the frozenset widening; taken as a proof OF THE REFUSAL
that is vacuous. With the selection held fixed and only the frozenset
widened, baseline and mutant both returned
`CONTINUE_TYPED_STOP_REQUIRED: 5, other/accepted: 0`. The reason is
structural: line 352 is reached when `terminal_lifecycle_decision is
None`, and `RESUMABLE_STOP_REASONS` is consulted at `lifecycle.py:273`
inside `build_resumed_lifecycle`, which only runs when a terminal
decision exists. On these roots the frozenset is never read. It kills
the artifact only through the SELECTION, which reads the same frozenset
— a real property worth having, and a different claim.

## Budget ceiling, checked against the actual diff

    $ git diff --numstat | awk '{a+=$1; d+=$2} END {print a, d, a+d}'
    87 insertions, 9 deletions, 96 changed lines   (ceiling 150)

First application of the rule added at `132bdbb9`. Under the ceiling, so
no stop fired — and unlike the previous tranche, the number was taken
from `git diff --stat` rather than from the plan-time estimate (~74).
The estimate was low by ~30%, which is exactly the gap an
estimate-only ceiling cannot see.

## Historical roots re-checked: not applicable, and no root was touched

The change adds a test and edits a map document. No reader, validator,
guard or authority rule moves, so `INV-frozen-surfaces`'s root-sweep
trigger does not fire.

The stronger claim, which this tranche must make because it OPENS
committed roots: **no committed root was modified.** Every witness is
`shutil.copytree`'d into a `TemporaryDirectory` before
`prepare_continuation` sees it, because that function constructs a
writable `Harness` (`continuation.py:210`) before reaching the refusal.
The gate ran the test 1× and `tests/test_continuation.py` 3× more during
implementation; `git status --porcelain experiments runs` is empty.

## What the guard actually protects, stated precisely

A change that stops the facade refusing a run holding neither a terminal
lifecycle decision nor a resume decision now fails `pytest`, not only
CI's wheel-smoke job. That is the exposure W1 named: the defect the
previous tranche fixed survived nine days behind a green gate because
its only witness was a script no gate runs.

What the guard does NOT protect, and no test in the repo does:

- **that a terminal WITH a receipt but a non-resumable reason is
  refused.** That is a different guard (`lifecycle.py:273`, "terminal
  stop reason does not authorize continuation"), and no committed root
  witnesses it — all 16 roots carrying a receipt stopped on
  `budget_exhausted`, which is resumable. Recorded as **X1**.
- **the continuation half.** Its only end-to-end witness remains the
  operational smoke. `DR-SUB-application`'s Traps entry says so
  explicitly rather than reading as fully resolved.

## Map obligations discharged

`docs/map/SUB-application.md`'s Traps entry was REWRITTEN, not replaced,
per `SCHEMA.md`: it keeps the full history of the original trap, marks
the refusal half fixed with its date, tranche and covering test, and
states plainly that the continuation half is still uncovered by the
gate. Its `check:` gained the new nodeid, so the document is verified by
the test it describes.

Its `Verify:` line was re-run in full before the fix commit: 137 passed
/ 1 skipped, then 38 passed.

`Verified-at:` advances to `a65e8578` in the VERIFICATION commit, not
the fix commit — I set it there and it lagged. The map CONTENT moved
with the code as required (the Traps entry is in `a65e8578`); only the
stamp trailed by one commit, and it now names the commit whose checks
were actually re-run. Recorded rather than silently corrected, because
"advance the stamp only if you re-ran the checks" is the rule it exists
to serve and a stamp nobody notices is stale is how it decays.

## Residue (honest)

- **X1 — the receipt-present, reason-non-resumable path is unguarded.**
  Found while choosing witnesses. See above; needs a constructed
  fixture, since no committed root can witness it.
- **The witness set is 5 and can only grow by a run failing.**
  `operational_failure` roots accumulate when runs break, which is not
  something to wish for. If the class were ever pruned from the repo the
  guard fires — correctly — but the fix would then be to construct a
  witness, not to delete the test.
- **The selection trusts `run-stop.json`'s `reason` field.** A root
  whose stop record disagreed with its own replayed state would be
  mis-selected. Nothing suggests one exists, and the refusal assertion
  would fail loudly rather than pass, so the failure mode is legible
  rather than silent.
- **Carried, untouched**: W2 (unmeasured cancel race), W3 (six smoke
  stages with one green observation each), V2, V4, U1, U3, T3, T4, S2,
  S3, P1a, P1b, P1e, P7.
