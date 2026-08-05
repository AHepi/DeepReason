# Goal: diagnose the contract-pair inventory once, then make the smoke's expectations derive from it
Class: defect
Observed: with failures legible (T2), `scripts/wheel_operational_smoke.py`
fails at `STAGE_QUALIFY` with `failure_kind: assertion_failed` and the
now-visible message **"qualification did not announce the frozen
maximum"** — the FIRST qualify assertion, which pins the announced budget
at `840`. A second pin in the same stage expects
`{"qualification_calls": 80, "total_calls": 280}` and observes
`{"qualification_calls": 80, "total_calls": 300}`.

Both numerals derive from ONE source.
`production_qualification_maximum_provider_calls`
(`src/deepreason/qualification.py:177`) computes:

    block_costs = (PRODUCTION_CASES_PER_PAIR
                   * _contract_schema_repair_grant(manifest, pair).maximum_provider_calls
                   for pair in production_contract_pairs(manifest))
    return sum(block_costs) + sum(largest PRODUCTION_PAIR_RE_EXERCISE_LIMIT block_costs)

and the smoke's own comment reproduces the arithmetic that yields 840
(2 conjecture pairs x 20 x 5, plus 8 pairs x 20 x 3, plus 4 bridge pairs
x 20 x 2), with "one clean pass" giving 14 x 20 = 280. So a change to
the contract-pair inventory — its membership, or any pair's schema
repair grant — moves both numbers at once.

Evidence: `experiments/2026-08-05-fix-smoke-failure-reporting/PARKED.md`
U2; `experiments/2026-08-05-fix-loopback-fixture-daemon/PARKED.md` T1;
preserved artifacts in the session scratchpad (`t1_evidence/`: the
loopback per-contract counts and a completed qualification cache).

Success criterion (machine-decidable):

    python -u scripts/wheel_operational_smoke.py   -> exits 0
    python scripts/wheel_smoke.py                  -> exits 0
    python -m pytest tests/ -q -n 4                -> ends "0 failed"
    python tools/docs_verify.py                    -> "docs_verify: 0 failed"

    # the same-commit pin rule: any surviving pin names what it derives from
    -> every numeric expectation left in the qualify stage either is
       computed from the inventory at run time, or carries an inline
       statement of the derivation it stands for.

In scope (2):
- `scripts/wheel_operational_smoke.py` — the qualify stage's two
  expectations.
- `src/` — ONLY if the inventory diagnosis shows a regression. The
  operator's instruction: "If regression: fix src."

NOT in scope: hand-editing 840 or 280 to whatever today prints. The
operator forbids it explicitly ("Do NOT hand-edit numerals without the
inventory answer"), and it is the same expiring-form-pin defect this
session already fixed twice (the census readers, the MCP tool pins).
U1 (the parallel-load flake) stays parked. T3/T4/S2/S3 stay parked.

Budget: <=150 changed lines, 1 commit, ~2 hours.
Stop conditions inherited from orchestrator: yes.

## The one question this tranche answers

**What changed in the contract-pair inventory since the 840/280 pins
were written, and is that change correct behaviour from the rung program
or a regression?** Everything else follows from the answer. Diagnosing
the two numerals separately would be diagnosing one cause twice.

## Map preflight

`DR-SUB-manifest` owns `run_manifest.py` and qualification;
`DR-INV-frozen-surfaces` surface 5 is "anything altering qualification
subject digests" — read before designing, because the inventory feeds
those digests. `docs/map/` owns nothing under `scripts/` (S3). If the
answer is "regression, fix src", surface 5 is in play and the tranche
stops for operator words before touching it.
