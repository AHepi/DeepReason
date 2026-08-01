---
name: dr-reproduce
description: Demonstrate a diagnosed DeepReason cause with the smallest offline artifact — a failing test or a minimal script against the committed record. Use after DIAGNOSIS.md, before any fix.
---

# Reproduce the cause

Input: DIAGNOSIS.md's falsifiable prediction. Output: REPRO.md plus one
runnable artifact that shows the defect NOW (and will show its absence
after the fix). You still change no production code.

## Choose the cheapest sufficient form, in this order

1. **Record replay** — the defect is already capted in a committed run
   root: a script that runs `verify_root(<root>)` or walks the log and
   prints the violating fact. Zero live cost; deterministic.
2. **Offline unit reproduction** — construct the minimal state in a
   test: register the same problems/artifacts/policies the record
   shows and assert the wrong behavior happens. Reuse existing test
   helpers (`_prepare_run`, controller fixtures, `_policy` builders)
   from the nearest `tests/test_*.py`; do not invent new scaffolding
   when a helper exists.
3. **Minimal in-memory check** — a 20-line python3 heredoc proving the
   mechanism (e.g. round-trip a receipt through `canonical_json` and
   show key order changes). Acceptable as evidence, but pair it with
   form 1 or 2 for the regression artifact.

NEVER reproduce by launching a live provider run. Live runs are for
`dr-verify-outcome`, at most once, and only if the goal demands it.

## Fidelity rules

- The reproduction must mirror the live conditions the record shows,
  not a convenient simplification. If admission auto-accepted
  import-role artifacts before cycle 0, your fixture registers those
  artifacts too. A reproduction that passes for a different reason
  than the live failure will approve a wrong fix.
- One assertion states the DEFECT (currently failing or currently
  printing the violation), phrased so it inverts cleanly post-fix.
- Respect frozen-record invariants in fixtures: one manifest sha per
  capability chain, constant fence seqs within a proposal's chain —
  fixture WellFormednessError means your fixture is wrong, not the
  harness.

## REPRO.md template

    # Reproduction
    Form: record-replay | unit-test | in-memory
    Artifact: <path (test id) or inline command>
    Current output: <paste the failing/violating output, trimmed>
    Confirms diagnosis: yes — <one line linking output to mechanism>
    Post-fix expectation: <exact output/assertion after a correct fix>

If the reproduction REFUTES the diagnosis: write that in REPRO.md,
commit, and return to the orchestrator routing back to `dr-diagnose`.
A refuted diagnosis is a successful phase, not a failure.

## Exit criteria

- REPRO.md + artifact committed and pushed.
- The artifact demonstrably shows the defect today (output pasted).
- Production code untouched.
- Return to the orchestrator.
