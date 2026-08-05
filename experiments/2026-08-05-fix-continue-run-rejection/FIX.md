# Fix: give each half of owner decision 4a its own subject — a cancelled run for the refusal, the budget-exhausted run for the continuation

Guarantee restored: **the operational smoke proves both halves of
`2d4ca2e1` end to end — the installed facade still refuses to continue a
run carrying no typed STOPPED receipt, AND it does continue a
budget-exhausted one.**

The operator's direction, taken literally: (a) is reachable, so FIX.md
does both. `(b)` alone would delete the refusal proof; `(a)` alone would
leave the new behaviour unwitnessed.

## The shape this fix takes, and why it is small

`_assert_non_resumable_rejection` **does not change**. It already accepts
byte-for-byte what the cancelled run returns
(`"ValueError: CONTINUE_TYPED_STOP_REQUIRED"`, REPRO.md). The stale
thing was never the assertion — it was the SUBJECT the stage pointed it
at. So the refusal half is a re-pointing, and no assertion is weakened
to reach green: the existing one starts passing for the right reason.

**No new stage constant.** `ALLOWED_FAILURE_STAGES` is pinned by
`tests/test_wheel_operational.py:3314`, and the failure record's `stage`
is a closed vocabulary. Both subjects reuse existing stages —
`STAGE_CONTINUATION_REJECTION` for the refusal, `STAGE_CONTINUATION_RESUME`
for the witness — so the vocabulary is untouched and that pin keeps
passing unedited.

## Change sites (exhaustive)

1. **`scripts/wheel_operational_smoke.py` ~3391-3417** — re-point
   `STAGE_CONTINUATION_REJECTION` off `first_run_id` and onto a fresh
   cancelled subject, driven entirely through MCP:
   - `start_run` with `{"budget": {"cycles": 12, "token_budget": 200000}}`;
   - poll `run_status` until `cycle >= 1`, then `cancel_run`;
   - `_poll_terminal` to a terminal; assert `state == "cancelled"` and
     `stop_reason == "operator_cancelled"` — if the subject did not
     cancel, the stage must fail rather than silently test something
     else;
   - `tool_error("continue_run", …)` → `_assert_non_resumable_rejection`
     **(unchanged)**;
   - assert `run_result` is byte-identical before and after, and
     `run_status` is still `cancelled` — the refused continuation
     changed nothing. This preserves the existing
     "rejected continuation changed the terminal result" assertion,
     moved to the subject it now applies to.
2. **NEW `_assert_continuation_accepted(payload)`** (beside
   `_assert_non_resumable_rejection`, ~line 2059) — asserts the handle
   shape DIAGNOSIS.md captured verbatim: `state == "running"`,
   `result_operation == "run_result"`,
   `status_operation == "run_status"`, and `run_id` echoing the subject.
   This is the operator's "the response body you just captured is the
   shape of that assertion".
3. **`scripts/wheel_operational_smoke.py`, after the parity checks on
   `first_run_id`** — the continuation witness, under
   `STAGE_CONTINUATION_RESUME`: `tool("continue_run", …)` on the
   budget-exhausted `first_run_id` → `_assert_continuation_accepted`,
   then `_poll_terminal` to a terminal and `_assert_committed_terminal`.
   Polling to a terminal is not decoration: it leaves the home settled
   so `_assert_durable_replay(home, first_run_id)` at line 3587 still
   validates a quiescent root, and it makes the replay assertion
   STRONGER — it now validates a run that was continued.
4. **`_assert_no_incremental_provider_calls` baselines** — the existing
   `calls_before_retrieval` / `calls_before_rejection` baselines are
   re-scoped so each still brackets only work that must spend nothing.
   The witness in site 3 legitimately spends provider calls and is
   excluded from those brackets rather than having the brackets
   loosened.
5. **`tests/test_wheel_operational.py`** — ADD (not edit) a unit test
   for `_assert_continuation_accepted`, mirroring the existing
   `test_operational_smoke_requires_exact_non_resumable_rejection`:
   the captured body passes; a body with `state != "running"`, a
   mismatched `run_id`, or a missing operation key raises. Mutation-
   proven before it is committed.
6. **`docs/map/SUB-application.md` Traps** — one entry, in the same
   commit as the code. `2d4ca2e1`'s behaviour is already documented
   there; what is not documented is that its only END-TO-END witness
   lives outside the map, under `scripts/`, and that the decision
   changed a property an out-of-map instrument asserted. New check:

       check: grep -q '"cancel_run"' scripts/wheel_operational_smoke.py
              && grep -q "_assert_continuation_accepted" scripts/wheel_operational_smoke.py

   It fails if either half of the coverage is removed. `Verified-at:`
   advances only if that document's checks are actually re-run.

## The margin constraint, stated as design rather than left to luck

`cancel_run`'s own schema says the harness observes cancellation "only
at the next safe completed-cycle boundary". The subject must therefore
hold cycles in reserve when the cancel is issued, or the run can reach
its own terminal first and land on `budget_exhausted` — which would make
the stage flaky in exactly the direction that HIDES the defect (a
budget-exhausted subject continues, so the refusal assertion fails
loudly rather than silently, but intermittently). REPRO.md requested 12
cycles and cancelled at the first observed boundary, terminating at
cycle 2: ten cycles of margin. The implementation keeps that ratio and
asserts the observed `stop_reason` rather than assuming it.

## Open design point, to be settled by measurement at implement time

The witness continues `first_run_id` under a budget. `{"cycles": 1,
"token_budget": 1}` would make the resumed run re-exhaust almost
immediately and cost nearly nothing, but a 1-token budget is untested
and may fail for an unrelated reason. `dr-implement-fix` measures the
smallest budget that produces a clean terminal and uses that; if the
minimum misbehaves, it falls back to `{"cycles": 1, "token_budget":
100000}` and records which was chosen and why. No numeral is pinned as
an expectation either way — the assertions are on the handle shape and
the terminal, not on a count.

## Regression artifact

REPRO.md's artifact must INVERT in the sense that matters: it currently
demonstrates the refusal on a cancelled run and acceptance on a
budget-exhausted one while the smoke exits 1; after the fix the same two
behaviours hold and the smoke exits 0.

New conditions this fix must be tested against, beyond the goal's four
criteria:

- the cancelled subject actually reaches `state == "cancelled"` with
  `stop_reason == "operator_cancelled"` — asserted in-stage, so a
  cancel that loses its race fails the smoke instead of degrading it;
- the refused continuation leaves `run_result` byte-identical;
- `_assert_continuation_accepted` rejects a non-error body that is the
  wrong shape (mutation-proven, site 5);
- `_assert_durable_replay(home, first_run_id)` still passes on the
  now-continued run.

## Existing tests at risk

`grep -n "non_resumable\|ALLOWED_FAILURE_STAGES\|CONTINUE_TYPED" tests/`
returns three relevant sites, and **all three must keep passing
UNEDITED**:

| test | why it is safe |
|---|---|
| `test_operational_smoke_requires_exact_non_resumable_rejection` (:1381) | asserts `_assert_non_resumable_rejection`'s string matching, which this fix does not touch |
| the `ALLOWED_FAILURE_STAGES` equality pin (:3314) | no stage constant is added or removed |
| the 108 tests of `tests/test_wheel_operational.py` | the fix adds a helper and re-points a stage in `main()`; no existing helper's signature or behaviour changes |

If any of them moves, the fix is wrong as implemented and is reverted
rather than accommodated — the rule this session already had to apply
once, at `31480e5f`.

## Explicitly not changed

- **`src/` — nothing.** The diagnosis rules regression out: `2d4ca2e1`
  is a named owner decision, gate-enforced and documented. Changing the
  product to satisfy an instrument would be backwards.
- **No frozen surface.** None of the five names the continue dispatch or
  the MCP facade, and this alters what a FUTURE run may do, not how a
  PAST run verifies — so the root sweep is not the instrument and is not
  run.
- **`_assert_non_resumable_rejection`** — the tempting neighbour. It
  looks like the stale thing and is not; widening it to accept a
  non-error would delete the refusal proof outright.
- **V2** (set-vs-tuple `EXPECTED_MCP_TOOLS` duplication) — stays parked
  per the operator. This fix does not touch either pin: `cancel_run` is
  already in both.

## Estimated diff

~100 lines across 3 files (`scripts/wheel_operational_smoke.py` ~75,
`tests/test_wheel_operational.py` ~20, `docs/map/SUB-application.md`
~8). Under the 150-line budget.

---

## Amendment 1 — a seventh change site, and a helper FIX.md described but did not name

`dr-implement-fix` rule 1: a site FIX.md missed is amended before the
work continues, not typed in silently. Two items, both found by running
the ring.

### 7. `tests/test_wheel_operational.py:4145` — the tracked-client census

    assert source.count("= _new_mcp_client(") == 6

The rejection stage's cancelled subject needs its own MCP client, which
makes it 7. The full gate ring returned
`1 failed, 108 passed` on `test_every_operational_mcp_child_uses_tracked_construction`
— a failure **FIX.md's "Existing tests at risk" table did not predict**,
because that table was built by grepping
`non_resumable|ALLOWED_FAILURE_STAGES|CONTINUE_TYPED` and source-census
pins match none of those.

**Updated to 7, not rewritten.** This is deliberately NOT treated as the
expiring-form-pin class this session fixed twice (the root censuses, the
MCP tool pins). The distinction: a root census counts committed evidence
that accumulates on its own, so the number expires without anyone
touching it. This counts constructions in ONE file that only change when
someone edits that file — the same shape as `EXPECTED_MCP_TOOLS`, a
declared surface under the same-commit pin rule. The guard it enforces —
no MCP child escapes `_new_mcp_client` and therefore the shutdown list —
is preserved exactly by 6 → 7, and would be weakened by loosening it to
an inequality. The sibling pins at :4132 (`= _run_reason(` == 3) and
:4144 (`MCPClient(` == 1) are unaffected and stay as they are: this
change adds no reason command and no direct construction.

### A helper implementing site 1's described behaviour

Site 1 specified "poll `run_status` until `cycle >= 1`, then
`cancel_run`". That is implemented as a named helper,
`_await_cancellable_cycle`, beside `_poll_terminal`, rather than inline
in `main()`. Recorded here because it is a new location in the file even
though it is the same change site's logic; it adds no behaviour site 1
did not specify. It raises rather than proceeds if the subject has
already left `starting`/`running`, so a lost cancel race fails the stage
instead of silently substituting a continuable stop.

## Approval gate

Class `defect` (GOAL.md), estimate <=150 lines, no frozen surface, no
`src/` change, and the operator has already directed this exact shape
("FIX.md should do both"). **Proceeds to `dr-implement-fix`.**
