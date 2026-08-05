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

---

## Amendment 1 — a fourth change site, and it is a defect I introduced

`dr-implement-fix` rule 1: a site FIX.md missed is amended before the
work continues, not typed in silently.

With the qualify stage fixed, the run advanced to `STAGE_MCP_INITIALIZE`
and failed `_assert_exact_tools` with "MCP tool inventory drifted".
Cause: **my own careless pin update in the preceding smoke tranche.**

`EXPECTED_MCP_TOOLS` is a `set` in `wheel_smoke.py` but an ordered
`tuple` in `wheel_operational_smoke.py`, and `_assert_exact_tools`
compares `tuple(tool["name"] for tool in tools) != EXPECTED_MCP_TOOLS`
— order-sensitive. When I added `amend_run` and `run_findings` I
APPENDED them in both files. That is correct for a set and wrong for a
tuple: the live server emits them at positions 5-6, immediately after
`run_result`.

    live  : ... run_result, run_findings, amend_run, continue_run, ...
    my pin: ... run_result, continue_run, ... get_request_requirements,
            amend_run, run_findings
    same members: True     ordered match: False

`wheel_smoke.py` passed throughout because its set comparison cannot see
order — which is why the error surfaced only here, one stage later, and
only after the shadowing and qualify defects were cleared out of the
way.

Change site 4: `scripts/wheel_operational_smoke.py` `EXPECTED_MCP_TOOLS`
— move the two names to their server-emitted positions. Verified after:
ordered match True, schema sha match True.

**Not converted to a set.** Order here is genuinely part of the pinned
public facade — `EXPECTED_MCP_SCHEMA_SHA256` already hashes the tools
array, which is a JSON list, so order is pinned regardless; the tuple
comparison just reports order drift with a clearer message than a sha
mismatch would. This pin is the same-commit pin rule working as
intended, and unlike the 840/280 numerals it is not a fact with an
expiry date — it is the declared surface, which is supposed to be
updated deliberately when the surface changes.

Correction to my own earlier report: when I said the two added tools
were "verified as intended surface rather than rubber-stamped", that was
true of their MEMBERSHIP and said nothing about their POSITION. The
membership check was sound; the ordering was not checked at all, and one
of the two instruments could not have caught it.

## Amendment 2 — a fifth site: T2's residue coming true

T2's VERIFY recorded, as honest residue: "Not proven: that these three
were the ONLY places the smoke drops evidence. Three were found by
needing them; a systematic audit of every `except` in the file was not
done." That residue has now cashed out.

With the tool order fixed, the run advanced to
`STAGE_CONTINUATION_REJECTION` and failed with
`failure_kind: assertion_failed` and **no diagnostic block at all**.
Cause: **ten** sites raise `OperationalSmokeFailure(...,
failure_kind=FAILURE_ASSERTION)` DIRECTLY — a typed failure, not a bare
`AssertionError` — plus the `_MCPToolResponseError` subclass. They are
caught by `except OperationalSmokeFailure as error: failure = error`,
which T2 left silent because T2 fixed the `except AssertionError` path
beside it.

Change site 5: report a traceback for typed failures too. The exception
is payload-free by design and carries no message, so the traceback is
the only thing that can name WHICH check raised — the record already
holds the stage and kind, and neither locates a line.

This is completing T2's stated goal ("fix all three so the instrument
reports what happened when it fails") on a path T2's enumeration missed,
not new scope for T1. It is declared here rather than typed in silently
because it is a change to a file this tranche was already editing for a
different reason, and `dr-implement-fix` rule 1 applies.
