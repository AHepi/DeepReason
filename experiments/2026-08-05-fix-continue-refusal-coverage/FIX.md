# Fix: turn the record-replay reproduction into a gate test in `tests/test_continuation.py`

Guarantee restored: **`CONTINUE_TYPED_STOP_REQUIRED` is guarded by a
test the full gate runs, so a change that stops the facade refusing a
run with no typed STOPPED receipt fails `pytest` rather than only CI's
wheel-smoke job.**

Nothing about the product changes. The reproduction PASSES today; the
mutation proof, not the pass, is what makes it a guard.

## Change sites (exhaustive)

1. **`tests/test_continuation.py`** — one new test,
   `test_a_stop_with_no_typed_receipt_refuses_continuation`, holding
   REPRO.md's artifact. Placed here, not in
   `tests/test_v6_resumed_terminal_revalidation.py`, for one concrete
   reason: `DR-SUB-application`'s `Verify:` line runs
   `tests/test_continuation.py`, so the new guard is re-executed
   whenever that map document is re-verified, and the document's Traps
   entry about this refusal is checked by the thing it describes.
2. **`tests/test_continuation.py` imports** — `shutil`, `subprocess`,
   `tempfile`, `Path`, and `RESUMABLE_STOP_REASONS` from
   `deepreason.workflow.lifecycle`. The file currently imports none of
   these.
3. **`docs/map/SUB-application.md` Traps** — the entry added by the
   previous tranche says the refusal "has NO product test anywhere in
   the gate" and that "the smoke is the only end-to-end witness". Half
   of that stops being true in this commit. Per `SCHEMA.md` a Traps
   entry is never deleted, only rewritten to say when it was fixed: the
   entry keeps its history and gains the date and the covering test.
   Its `check:` gains the new nodeid.

## Witness selection, and the one thing it must not become

Selection is by property — `run-stop.json`'s `reason` not in
`RESUMABLE_STOP_REASONS` — never by root name. Two properties follow
that a name-based list would not have:

- it cannot silently drift as roots are added or retired;
- it is defined against the PRODUCT's own notion of resumability, so a
  change that reclassifies these stops empties the set and trips the
  guard instead of leaving the test passing over nothing.

The non-empty guard's message names the loss explicitly — *"no committed
root carries a non-resumable stop; the refusal has lost its witness"* —
because a zero-witness pass is the failure mode this whole class of test
has (the expired-census defect this session fixed twice).

**Not reused: `_committed_roots()` from
`tests/test_module_fingerprints.py`.** It selects on `/log.jsonl` and
lives in a module about fingerprint stamps; importing across test
modules to share a four-line `git ls-files` would couple two unrelated
guards, and this one needs `run-stop.json` rather than `log.jsonl`.
Recorded because `dr-reproduce` says reuse existing helpers, and this is
a deliberate departure rather than an oversight.

## Cost, and why the cheap selection is also the correct one

Measured in REPRO.md: selecting by opening a `Harness` per root costs
**63.3 s** (28 full replays) and yields 12 witnesses; selecting from
`run-stop.json` costs **0.11 s** and yields 5. The test uses the second.

That is not merely cheaper. The expensive form reads
`terminal_lifecycle_decision is None` — the exact condition the code
under test branches on — so it would assert the product's own logic back
at it. The cheap form selects on an independent fact (what reason the
run stopped for) and lets the REFUSAL do the work: a witness that
somehow carried a receipt would raise a different error and fail loudly,
not be quietly skipped.

Total added gate time ~8 s against a 707 s gate.

## Regression artifact

REPRO.md's artifact, as a test. Both mutations must keep killing it, and
they must keep killing it through DIFFERENT assertions:

| mutation | expected failure |
|---|---|
| widen `RESUMABLE_STOP_REASONS` to include `operational_failure` | the non-empty witness guard |
| `continuation.py:352` raises a different error | the per-witness refusal assertion |

Re-run both after the test is in `tests/`, not only as the standalone
script, since the assertion mechanics differ under `pytest`.

## Existing tests at risk

`grep` for the names this change touches gives three, and **all three
must keep passing UNEDITED**:

| test | why it is safe |
|---|---|
| the 4 existing tests in `tests/test_continuation.py` | the new test adds imports and a function; it shares no fixture and mutates no module state |
| `test_operational_smoke_requires_exact_non_resumable_rejection` | unchanged; it tests the smoke's string matcher |
| `tests/test_module_fingerprints.py` | `_committed_roots()` is NOT imported or altered |

No source-census pin is in play: this tranche adds no MCP client, no
reason command and no stage constant. That was the site the previous
tranche's risk table missed, so it was checked explicitly this time —
`grep -n "\.count(" tests/*.py` over the files being touched returns
nothing in `test_continuation.py`.

## Explicitly not changed

- **`src/` — nothing.** GOAL.md forbids it and nothing here asks for it.
  If the test cannot be written without a product change, that is a
  finding to report, not a licence.
- **The 7 receipt-less `budget_exhausted` roots** — the tempting extra
  witnesses. They reach the same raise, but their reason is now
  resumable, so including them would tie the witness set to a
  historical accident instead of a property.
- **W2, W3, V2, V4** — parked, untouched.
- **No frozen surface.** A test-only change touches none of the five,
  and the root sweep is not the instrument for adding a test. No
  committed root is modified: every witness is copied to a temp
  directory first.

## Budget ceiling — checked against the ACTUAL diff before the commit

GOAL.md sets **<=150 changed lines**. Estimate: ~55 lines in
`tests/test_continuation.py`, ~14 in `docs/map/SUB-application.md`,
~5 import lines — **~74 total**.

Per `132bdbb9`, the ceiling is compared to `git diff --stat` immediately
before committing, not to this estimate. If the actual diff exceeds 150,
that is a STOP with priced options, not a footnote. The previous tranche
landed 193 against the same ceiling with no stop firing, which is the
recorded miss that rule exists to close.

## Approval gate

Class `regression-risk`, so `dr-set-goal` would normally stop after this
document and report. The operator's direction ("W1 next", plus W1's
parked entry stating goal, method and end state) is the approval that
class requires, and the shape proposed here — record replay, property
selection, non-empty guard, two mutations — is the shape they specified.
**Proceeds to `dr-implement-fix`.**
