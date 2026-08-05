# Diagnosis: the contract-pair inventory and the maximum's formula BOTH changed on 2026-07-27, hours after the pins were written — and both changes are correct

Primary cause: two deliberate commits on 2026-07-27 moved the two inputs
the smoke's qualify-stage numerals depend on, and neither updated the
smoke. `9fabac69` (02:32) enabled the grounded two-stage bridge in the
engaged public preset, growing the contract-pair inventory from 14 pairs
to 15. `f49dc48a` (17:02) changed
`production_qualification_maximum_provider_calls` from
`return sum(block_costs)` to
`return sum(block_costs) + re_exercise_allowance`, adding a bounded
re-draw for up to `PRODUCTION_PAIR_RE_EXERCISE_LIMIT` (3) failing pairs.
The 840 pin was written at 06:18 (`5e69c64d`) — between the two — so it
was correct when written and stale by the same evening. Neither change
is a regression.

## Ground truth, measured

Cleared the qualification cache in the retained venv and re-qualified
against the loopback fixture:

    maximum expected provider calls: 1140        (smoke pins 840)
    Qualification tier: full
    Qualification state: ready
    total_calls = 300   qualification_calls = 80   errors = 0
                                                  (smoke pins 280 / 80)

Qualification SUCCEEDS. `qualification_calls` matches its pin exactly;
zero provider errors; 300 actual calls sit well inside the 1140 budget.
Only the smoke's two numerals disagree with reality.

## The arithmetic closes exactly

The completed qualification bundle lists **15** pairs (was 14):

    conjecturer.atomic-candidate.v1   conjecturer.turn.v6
    batch-critic.v2                   critic.atomic-target.v1
    groundingverdictwirev1.direct.v1
    scratch.block.compact.v1          scratch.block.minimal.v1
    scratch.cluster-guide.compact.v1  scratch.cluster-guide.minimal.v1
    scratch.link.compact.v1           scratch.link.minimal.v1
    bridge.composition.v2             bridge.composition-batch.v1
    bridge.ledger.v3                  bridge.ledger-batch.v1

Solving `sum(block_costs) + top-3 allowance = 1140` over 15 pairs gives
2 pairs at 20x5, 8 at 20x3 and 5 at 20x2:

    sum(block_costs)      = 200 + 480 + 200 = 880
    re_exercise_allowance = 100 + 100 + 60  = 260   (3 largest blocks)
    announced maximum     = 880 + 260       = 1140

against the smoke's comment, which describes 2x20x5 + 8x20x3 + 4x20x2 =
840 over 14 pairs with no allowance. The delta is precisely one added
bridge-class pair (+40 to the sum) and the new allowance (+260):
840 + 40 + 260 = 1140.

The clean pass follows from the same inventory: 15 pairs x 20 cases =
**300**, which is exactly what the fixture recorded. The comment's
"one clean pass makes exactly 14 x 20 = 280" was true of a 14-pair
inventory.

## Correction to an earlier reading

The previous tranche recorded that two bridge contracts appeared to take
"2 calls per case", suggesting they might be repairing on every case —
a possible regression. **That reading was wrong.** The fixture counts by
WIRE TITLE, not by pair, and two pairs can share one title:
`bridge.composition.v2` + `bridge.composition-batch.v1` both emit
`BoundBridgeCompositionWireV2` (20 + 20 = 40), and the two ledger pairs
both emit `ClaimLedgerWireV2` (40). With `errors = 0` and
`total_calls = 300 = 15 x 20`, **no pair repairs at all** — every
contract qualifies on its first draw. The "2 calls per case" appearance
was two pairs sharing a title.

Evidence:
- `git log --format="%h %ad" --date=iso` over the three commits:
  `9fabac69` 02:32 (280 pin), `5e69c64d` 06:18 (840 pin), `f49dc48a`
  17:02 (formula change); `git merge-base --is-ancestor 5e69c64d
  f49dc48a` confirms the ordering.
- `git show f49dc48a -- src/deepreason/qualification.py`:
  `- return sum(` / `+ return sum(block_costs) + re_exercise_allowance`.
- The completed bundle's 15 pairs; the loopback counts
  `{total_calls: 300, qualification_calls: 80, errors: []}`.

Implicated code (2 sites, both in the instrument):
- `scripts/wheel_operational_smoke.py` — `if notice is None or
  int(notice.group(1)) != 840`
- `scripts/wheel_operational_smoke.py` — `if counts != {"qualification_calls": 80,
  "total_calls": 280}`

Falsifiable prediction: replacing both numerals with expectations
DERIVED from the qualification bundle and the installed wheel's own
constants makes the qualify stage pass without any numeral, and would
still fail if a provider error occurred, if a pair failed to qualify, or
if actual calls exceeded the announced budget.

Ruled out: **regression.** `9fabac69` ("Enable the grounded two-stage
bridge in the engaged public preset") and `f49dc48a` ("Qualify
stochastic providers on capability, not on one draw") are both
deliberate feature work, the latter directly implementing the repo's own
stated position that provider behaviour is stochastic across identical
runs (CLAUDE.md, "Live runs"). Qualification reaches `tier: full`,
`state: ready`, zero errors. Nothing in `src/` needs to change, so
frozen surface 5 is not touched.
