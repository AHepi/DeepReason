# FIX — the caller decides, the decision is a registered policy, and the ceiling still wins

## The shape, in one sentence

`_arg_crit` gains the arm its foreign-school sibling already has; what that
arm DOES is chosen by one `Config` field resolved through a small registered
policy module; and a refusal on a spent ceiling still leaves the pass
untouched, so the cycle loop above can end the run cleanly.

## R1 — the arm

Inside `_arg_crit`'s batch loop, `WorkBudgetDenied` is caught and read with
`budget_denial_exhausted` — the same reader the cycle loop uses, so there is
one answer to "is the ceiling spent" and not two.

- **Spent → re-raise, always, whatever the policy says.** This is not
  configurable and must not become configurable: the operator's law of
  2026-08-29 makes an exhausted budget a clean `budget_exhausted` terminal,
  and the cycle loop is where that is decided.
- **Not spent → the policy decides**, and whatever it decides, the record says
  what went uncriticised.

## R2 — the policy, as configuration

`Config.CRITICISM_BUDGET_DENIAL_POLICY`, resolved by a new module
`runtime/criticism_budget_policy.py` on the shape `runtime/seat_retirement.py`
already uses: a closed value set, a default, and a `resolve_policy` that
**never raises and never refuses** — an unknown id falls back to the default
and discloses (the all-configurations law of 2026-08-12).

| value | what the run does with a batch the budget refuses | effect on token allocation |
|---|---|---|
| `shrink-the-batch.v1` (default) | halve the batch and try again, down to single targets; drop only what still will not fit | re-allocates the remaining tokens into smaller calls that DO fit, so work that would have been abandoned is done |
| `drop-the-batch.v1` | drop the whole batch, carry on | leaves those tokens for later cycles instead |
| `stop-the-run` | today's behaviour: the refusal ends the run | spends nothing more |

`stop-the-run` is a gate being switched to its strict setting, so selecting it
emits a typed warning and never silence — the ungated-seats law of
2026-08-28, and the same mechanism `seat.retirement-disabled.v1` uses.

**Why `shrink` is the default.** It is the setting that does the most work
with money the run already has, and the operator's success law of 2026-09-03
measures a run by error eliminated rather than by finishing tidily. It also
subsumes `drop`: a single target that still will not fit is dropped, so R1
holds under the default without a second setting.

**Why the field is criticism-specific and says so in its name.** The same
missing arm exists on four other roads. Each has a different right answer and
a different record obligation, and naming this field for criticism keeps it
from silently claiming to govern them. Parked, not fixed.

## The record — what went uncriticised

`runtime/criticism_dispatch.py` carries a CLOSED outcome vocabulary whose
docstring says a new road "has to add a member here rather than inherit
`complete` by silence, which would license an absence nobody measured". So
this adds one: `OUTCOME_CUT_TOKEN_BUDGET = "cut:token-budget"`, distinct from
the existing `cut:budget`, which means the per-cycle TARGET cap rather than
money. The reader (`views/evidence_states.py`) special-cases only
`OUTCOME_COMPLETE`, so a new member is safe by construction — everything else
already means "this pass did not run in full".

The batch loop also starts naming the targets it ACTUALLY dispatched. Today it
reports `eligible[:dispatched]`, which names the wrong artifacts when an early
batch is dropped and a later one succeeds. That is harmless today because only
a `complete` pass licenses reading the names — but under `shrink` a pass can
partly succeed, and the loop being rewritten is the place to stop guessing.

## Frozen surfaces — one CONTACT, by the documented recipe

`tools/blast_radius.py` returns `"frozen_surface_verdict": "CONTACT"`, ONE row,
`DIRECT`, on surface 4: `run_manifest.py`.

That row is the `data.pop("CRITICISM_BUDGET_DENIAL_POLICY", None)` line in
`_versioned_source_config_data`. It is not an exception to the surface, it is
the surface's own documented recipe: `INV-frozen-surfaces.md` states that a
`Config` field is NOT DONE without that line, because `Config` is serialized
into every manifest's `engine_config_json` and hashed into
`source_config_hash`, which the qualification subject embeds. Without the pop,
every qualification subject digest moves and every home owes a ~14-minute
battery.

The operator's instruction — "ensure config is plugged in so that it can
affect token allocation during a run" — is the authority for the field. The
pop is the recipe's obligatory second half.

Two riders the recipe's own Traps demand, both honoured:

- The pop is **UNCONDITIONAL and at four spaces**. Scoping such a pop to a
  schema range was refuted by two v5 goldens in 2026-08-26, and an
  eight-space guard-scoped pop passes a naive substring check while the hash
  has already moved.
- Preservation is **measured, not argued**. `proof/digests.py` prints the
  manifest's `source_config_hash` and `sha256`;
  `proof/digests_before.txt` and `proof/digests_after.txt` must diff EMPTY on
  those two lines.

Nothing else is touched: no schema, no validator, no Pydantic model, no record
object kind, no stop reason.

## What the tests must prove

`tests/test_criticism_budget_denial_policy.py`:

1. **R1**: a refusal with budget remaining leaves the cycle alive under the
   default, and the pass declares `cut:token-budget` naming what it skipped.
2. **The boundary**: a refusal on a spent ceiling still leaves `_arg_crit`
   under every policy value, including `stop-the-run` — the ceiling is not
   configurable.
3. **R2 is LIVE, measured**: one real `TokenMeter`, one scenario, two settings
   of the one field — `drop-the-batch.v1` and `shrink-the-batch.v1` — produce
   DIFFERENT `meter.total` and different numbers of criticised targets. A
   branch test would not satisfy the operator's words; a number from the meter
   does.
4. **Every value is reachable**, an unknown value falls back and never
   refuses, and `stop-the-run` emits its typed warning.
5. **No digest moves** (the `proof/` captures, plus the existing
   `INV-frozen-surfaces` check style asserting the key never reaches
   `engine_config_json`).

Each mutation-proven.

## Diff budget

Production code: ~45 lines in a new policy module, ~35 in `_arg_crit`, 2 in
`config.py`, 3 in `run_manifest.py`, 4 in `criticism_dispatch.py`. Under the
150-line stop condition.
