# Goal: a decomposition merge that contains a repaired child must verify

Class: defect

Observed: `run-b4d6dfda0c20676a864a051fbc97bda4` (jolt epoch 3, state
`completed`, 851 events) is not replay-valid. `verify_root_report(root)`
returns `integrity_valid: False` with exactly two findings, both
`check: "workflow-call-pairing"`:

    event seq=245: Conj outputs are not uniquely admitted by their provider attempt
    event seq=386: Conj outputs are not uniquely admitted by their provider attempt

The run recorded the same two findings about itself at write time —
`REPLAY_VALIDATION.json` `verification.violations` contains these two and
nothing else — so today's reader agrees with the reader of 2026-08-01 and the
disagreement is not a drift in the checker.

This contradicts a documented guarantee. `_decomposition_merge_admits`
(`src/deepreason/invariants.py:503`) states in its own docstring that it honors
"the same join the replay validator enforces". The writer's replay validator
(`src/deepreason/workflow/replay.py`) accepts this run's completions; the reader
does not. One of the two is wrong about a merge shape both are meant to agree
on, and the record cannot be both valid and invalid.

Prior investigation is committed at
`experiments/live_jolt_2026-07-31/INVESTIGATION.md`. It establishes ATTRIBUTION
only — the defect is PRE-EXISTING, not introduced by the current tranche
(`verify_root_report` byte-identical across 42 roots at the pre-tranche baseline
and at HEAD; the helper unmodified since `1de1f690`, 2026-07-26). Its proposed
cause is NOT carried into this goal; `dr-diagnose` derives the cause from the
record.

Success criterion (machine-decidable):

    (a) python -c "from deepreason.invariants import verify_root_report; \
        import pathlib; \
        r=verify_root_report(pathlib.Path('experiments/live_jolt_2026-07-31/home/runs/run-b4d6dfda0c20676a864a051fbc97bda4')); \
        print(r.integrity_valid, sum(1 for f in r.integrity if f.check=='workflow-call-pairing'))"
        expected: True 0

    (b) The same verdict sweep over EVERY root under experiments/ that
        verify_root_report can open, captured before and after the change:
        expected: exactly one root's verdict differs (the one above); every
        other root byte-identical, including the count of roots that error.

    (c) A regression test that fails on the current reader and passes after,
        whose docstring names run-b4d6dfda0c20676a864a051fbc97bda4.
        expected: it fails before the change and passes after.

    (d) pytest tests/ -q -n 4
        expected: 0 failed. No assertion weakened.

In scope:
  - `src/deepreason/invariants.py` (the controller-v3 history checker only)
  - `tests/` (one regression test and, if needed, its fixture)
  - `experiments/2026-08-01-fix-decomposition-merge-pairing/` (tranche artifacts)

NOT in scope: `src/deepreason/workflow/replay.py`. It is the nearest tempting
neighbour — if reader and writer disagree it is natural to reach for either
side — but CLAUDE.md is explicit that the fix goes in the READER so existing
roots stay valid, and a writer change would move what gets recorded rather than
what gets accepted. No replay-validation RECORD FORMAT may change either.

Also NOT in scope, already parked: the zero-adjudication findings from the same
investigation (the `run-status.json` reporting defaults, the `OBSERVE_ONLY`
text-workload authority, the ritual detector's `MIN_ATTACKS_FOR_RITUAL=5`
blindness, and criteria seeding on the v6 text path). They are separate defects
in separate subsystems; see `PARKED.md`.

Budget: <=150 changed lines, 1 commit, ~2 hours

Stop conditions inherited from orchestrator: yes
