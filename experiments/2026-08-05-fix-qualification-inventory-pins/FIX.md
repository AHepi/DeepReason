# Fix: derive the qualify stage's expectations from the inventory instead of pinning them

Guarantee restored: **the operational smoke asserts that qualification
completed, spent no more than it announced, and made exactly one clean
pass over whatever the contract-pair inventory currently holds — without
naming a single number that the inventory can invalidate.**

## Change sites (exhaustive)

1. `scripts/wheel_operational_smoke.py`, qualify stage — replace
   `int(notice.group(1)) != 840` and
   `counts != {"qualification_calls": 80, "total_calls": 280}` with
   derived assertions:
   - the notice EXISTS and parses to a positive integer (the announced
     maximum), otherwise the run cannot be judged at all;
   - `total_calls == qualified_pairs * cases_per_pair`, both read at run
     time — one clean pass over the live inventory;
   - `total_calls <= announced_maximum` — within the announced budget;
   - `qualification_calls > 0` — the qualification-case marker still
     reaches the fixture;
   - the fixture recorded no provider errors.
2. NEW `_qualified_inventory(...)` — returns `(pair count, cases per
   pair)`. The pair count is read from the qualification bundle the run
   just wrote; the per-pair case count from the INSTALLED wheel's own
   `PRODUCTION_CASES_PER_PAIR`. Neither is written down here.
3. NEW `_provider_errors(path)` — the fixture's recorded errors, so
   "zero provider errors" is asserted rather than assumed.

## Why not re-pin 840 -> 1140 and 280 -> 300

Because the numerals are not the claim. They are `sum(20 x per-pair
repair grant) + top-3 re-exercise allowance` and `pairs x cases`
evaluated against one particular inventory, and the inventory is MEANT
to move: enabling the grounded two-stage bridge took it 14 -> 15 pairs
(`9fabac69`), and granting stochastic providers a bounded re-draw added
the allowance (`f49dc48a`) — both correct, both on 2026-07-27, both
hours after the pins were written. Re-pinning would restate the same
expiring claim one inventory later, and this stage has already broken
twice that way. It is the identical defect this session fixed in the
root-census readers and the MCP tool pins.

The operator's instruction is explicit on both halves: "Do NOT hand-edit
numerals without the inventory answer", and — the inventory answer being
"correct behaviour" — "make the smoke derive its expectations from the
inventory, or assert the property the numerals stood in for."

## Same-commit pin rule

No numeric pin survives in this stage, so nothing is left needing to
name what it derives from. The surviving comment states the derivation
and the history, so the next reader learns why a number would be wrong
here rather than helpfully adding one.

## Regression artifact

`python -u scripts/wheel_operational_smoke.py` must exit 0 — for the
first time in this container's history. The assertions must still be
able to fail: a provider error, a pair failing to qualify, a call count
that is not one clean pass, or spend above the announced maximum each
raise with a message naming the discrepancy (T2 makes those messages
visible).

## Existing tests at risk

`tests/test_wheel_operational.py` (108 tests). None asserts on 840, 280
or the qualify stage's expectations — `grep -n "840\|280" ` over that
file returns no such assertion. They must pass UNEDITED.

## Explicitly not changed

- **`src/` — nothing.** The inventory diagnosis says correct behaviour,
  not regression, so frozen surface 5 (qualification subject digests) is
  untouched.
- **T3/T4/S2/S3, U1** — parked; U1 explicitly stays parked per the
  operator.

## Estimated diff

~70 lines in 1 file. Under the 150-line budget.

## Approval gate

Class `defect`, <=150 lines, no frozen surface, no `src/` change.
**Proceeds to `dr-implement-fix`.**
