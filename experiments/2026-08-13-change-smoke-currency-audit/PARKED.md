# Parked: follow-on scope from the smoke-currency-audit tranche

Not fixed here — REQUEST.md R10 scopes this tranche to instrument/pin
staleness only. Each item below is a ready-to-paste prompt for a fresh
orchestrator tranche, not a promise this session made.

## P1 — root_sweep.py per-root throughput has degraded generally, beyond the one named hang root

> Route through `deepreason-orchestrator` (dr-set-goal → dr-diagnose →
> dr-reproduce → dr-propose-fix → dr-implement-fix → dr-verify-outcome).
> Context: the 2026-08-13 smoke-currency-audit tranche
> (`experiments/2026-08-13-change-smoke-currency-audit/CHECKLIST.md`,
> Step 4) ran `tools/root_sweep.py`'s per-root logic serially, exactly as
> committed (excluding only the one already-known-and-parked hang root,
> `experiments/live_tri_2026-07-27/run-c5ab654afd1b4aa131aede83bdca0f03`),
> and found individual roots taking 30-125 SECONDS EACH — e.g.
> `experiments/2026-08-09-overnight-omnibus/block-a-criticism-symmetry/
> home-cross/runs/run-bf30545893db661ec4d3c8da3a3f7f65` took 125.7s,
> `experiments/2026-08-04-change-rung5-dumb-alternative-backend/ab-home/
> runs/run-9a6be78e1e79184a0bd89923b957586c` took 47.5s. A 45-minute
> wall-clock guard killed the serial run at 34/102 roots. No prior
> committed VALIDATION.md/RESULTS.md reports per-root timing this slow
> for `root_sweep.py` (the closest precedent, `experiments/2026-08-13-
> change-defended-trial-wiring/VALIDATION.md`, reports only the
> aggregate "SWEEP COMPLETE: 103 roots" with no elapsed time). Goal:
> diagnose WHY per-root cost has grown this large — candidates to check
> first per `dr-diagnose`'s record-before-code rule: whether
> `verify_root_report` or `Harness(root, read_only=True)`'s replay cost
> is now doing asymptotically more work per event (e.g. an O(n^2) pass
> introduced by a recent `harness.py`-adjacent change), whether specific
> LARGE roots (the `overnight-omnibus`, `corpus-enrichment-patrol-pilot`,
> and `live_research_2026-07-29` families dominate the slow end) are
> simply proportionally bigger than when the instrument was last timed,
> or whether it's an environment/container difference (disk I/O,
> `git`-adjacent subprocess calls inside a check) rather than a code
> regression. If a real regression is found, fix READERS only per
> CLAUDE.md's frozen-surface rule (verification.py, harness.py are
> frozen surfaces — read `INV-frozen-surfaces.md` before touching
> either). If no regression is found (roots have just gotten bigger),
> record that finding and consider whether `tools/root_sweep.py` itself
> should gain a `--jobs` flag mirroring `tools/docs_verify.py`'s, since
> the smoke-currency-audit tranche's own scratch parallelization (4
> worker processes, `concurrent.futures.ProcessPoolExecutor`, one root
> per read-only task) cut a projected ~100-minute run to well under 30
> minutes with zero verdict drift versus the serial baseline — evidence
> that parallelizing is safe, not just fast.
