# Instruments run at the implementation boundary

## Full gate

    python -m pytest tests/ -q -n 4
    5178 passed, 6 skipped in 1362.84s (0:22:42)   # the fix
    5178 passed, 6 skipped in 1354.94s (0:22:34)   # after the E87 correction

0 failed both times. The 6 skips are the environment-conditional neural-weight tests the
suite already carries.

## Ring, while iterating (run before the gate, all green)

    python -m pytest tests/test_embedder.py -q                       22 passed
    python -m pytest tests/test_signals.py tests/test_signal_contract.py \
      tests/test_results_command.py tests/test_manifest_integration.py \
      tests/test_scratch_similarity.py tests/test_managed_path_config_read.py \
      tests/test_narrate.py -q                                       89 passed
    python -m pytest tests/test_scheduler.py tests/test_llm.py \
      tests/test_report.py -q                                        23 passed

## Mutation proof of the new regression tests

Two mutations, each reverting one half of the fix, each run against the new
tests:

- emission removed from `ops.make_embedder` →
  `3 failed, 19 passed` (the three new record-side tests)
- `embedder_line` stops quoting the recorded cause →
  `1 failed, 21 passed` (the reader-side test)
- restored → `22 passed`

The two guard tests (`test_the_two_hashing_causes_never_both_fire`,
`test_a_run_on_the_neural_backend_records_neither_cause`) pass before and after
by design: they pin what must NOT change, so they cannot be mutation-proven
against this fix and are not claimed to be.

## Reproduction, inverted

    python -u experiments/2026-09-09-neural-embedder-fallback/repro_embedder_drop.py
    pre-fix : exit 0, VERDICT: defect PRESENT   (REPRO_OUTPUT.txt)
    post-fix: exit 1, VERDICT: defect ABSENT    (REPRO_OUTPUT_POSTFIX.txt)

## Wheel smoke

    python scripts/wheel_smoke.py
    wheel smoke passed: isolated V6-only contents, clean imports, exact entry
    points, module parity, MCP registration, and exact MCP schemas

Not required by this fix's change sites (no packaging surface is touched); run
anyway because `application/results.py` sits behind the MCP `run_result` tool.
Its FIRST invocation died in `pip`'s build-dependency install before reaching
any repository code; the immediate retry passed. Recorded as a transient, not
as a result, because a failure that never reached the code under test is not
evidence about it.

## docs_verify

    python tools/docs_verify.py           9 failed
    python tools/docs_verify.py --audit   1 finding

The new `SUB-llm.md` Traps check passes; it is in neither list. All nine
failures are in documents this tranche does not touch — `SEAM-llm-x-rules.md`,
`CON-run-identity.md` (three git-history rows, the shallow-clone class the
baseline names), `INV-frozen-surfaces.md` (three), `SEAM-scratch-x-workflow.md`,
`CON-successor-questions.md`. `docs/AUDIT_BASELINES.md` records 5 or 6 on this
container's shallow clone as of 2026-08-31, so four of these post-date that
baseline. NOT investigated and NOT fixed here: a pre-existing failure this
tranche did not cause is a finding to report, not work to absorb. Reported to
the operator; the audit family owns re-baselining.

The single `--audit` finding is `SEAM-llm-x-rules.md:54`, the malformed-check
row the baseline already names as the one finding keeping `--audit` above zero.

## Diff budget

    python tools/diff_budget.py origin/main --ceiling 150 --paths \
      src/deepreason/ops.py src/deepreason/signals.py \
      src/deepreason/views/narrate.py src/deepreason/application/results.py
    {"total_insertions": 81, "ceiling": 150, "verdict": "WITHIN"}
