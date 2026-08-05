# Parked — noticed during the T2 tranche, not done

## U1 — a second parallel-load flake, distinct from the documented one

`tests/test_criticism_school_execution_c3.py::test_counterexample_retry_keeps_route_and_demonstrative_school_lineage`
failed once under `pytest -q -n 4` (`assert critic is not None` →
`assert None is not None`, line 211) and passes 3/3 when re-run alone.

Not attributable to any change in this session: across the whole smoke
work, `git diff --stat 9dcb4e99..HEAD -- src tests` is EMPTY — every
diff is under `scripts/` and `experiments/`.

`docs/HANDOVER_2026-08-03.md` documents a different one
(`test_v6_nonconjecture_recovery.py::test_grounded_counterexample_recovery_does_not_invent_override_on_repeat`),
so this is a second instance of the same class rather than a recurrence.
Both involve counterexample/recovery paths, which may or may not be
meaningful.

Suggested disposition: append to the handover's known-flake list, or a
tranche that asks whether the counterexample-retry paths share a
load-sensitive assumption.

## U2 — the T1 lead, sharpened by this tranche's own fix

With failures now legible, the assertion that actually fires in the
qualify stage is **"qualification did not announce the frozen maximum"**
(the FIRST assertion, pinning the announced budget at 840) — not the
call-count assertion (280 vs an observed 300) that the previous
tranche's PARKED T1 predicted. That prediction was an inference from the
stage name, made because the instrument would not say; it was wrong, and
T2 corrected it within minutes of landing.

Both pins are downstream of ONE thing. `production_qualification_maximum_provider_calls`
(`src/deepreason/qualification.py:177`) computes the announced maximum
from the live contract-pair inventory:

    block_costs = 20 cases x per-pair schema-repair grant, per pair
    return sum(block_costs) + sum(largest PRODUCTION_PAIR_RE_EXERCISE_LIMIT blocks)

So the 840 moves whenever the pair inventory or any pair's repair grant
changes — and the same inventory change plausibly explains the observed
300-vs-280 total. T1 should therefore ask its regression-or-correct
question ONCE about the contract inventory, not twice about two
numerals.

Evidence preserved for T1 in the session scratchpad
(`t1_evidence/`): the loopback counts with the per-contract breakdown,
and the qualification cache from a completed run.

Not done here: T1 is the operator's next tranche, explicitly sequenced
after this one.

## U3 — my own measurement discipline, recorded because it recurred three times

Three gate runs this session were corrupted by load I created myself:

1. S1 tranche: the 4-worker gate run concurrently with `docs_verify`,
   which itself spawns up to 16 workers. Reported 3 MCP failures; all
   passed unloaded.
2. T2 tranche: `bkl6y1u8j`'s gate started while `b9jnoxltc`'s gate was
   still running — two 4-worker pytest runs at once. Reported 4 MCP
   failures (`test_mcp_run` ×2, `test_mcp_scratch_bridge` ×2); all four
   passed together on an idle box in 32s.
3. The same S1-era run also surfaced U1's flake, which may or may not
   have the same cause.

Every corrupted run implicated the same family: MCP tests asserting on
`thread.join(timeout=2)`/`(timeout=5)`. They are the load canary of this
suite.

The lesson is not "MCP tests are flaky" — it is that a gate measured
against a box the measurer has loaded is not evidence, exactly as
`DR-SCHEMA` says of measuring during a falsification pass. Before
trusting any gate number: confirm `ps` shows no pytest/docs_verify/smoke
running, and never start a second long instrument while one is in
flight.

Suggested disposition: a line in `CLAUDE.md`'s gate discipline or
`dr-drive-harness`, since this cost three re-runs (~40 minutes) in one
session and the same trap is available to every future session.
