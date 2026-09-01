# Goal: defended-trial intent cannot compile silently to observation-only authority with empty trial grants
Class: defect
Observed: On `claude/deepreason-p-s1-commitments-wowcib`, `build_manifest_ps1.py:264-290` compiled a configuration requesting defended-trial criticism without a `criticism_policy`; the resulting manifest resolved criticism as `observe_only` and carried empty trial contracts, converting 140 of 147 genuine attacks per root into scrutiny observations.
Success criterion (machine-decidable):
    `python -m pytest tests/test_judge_canary_compile_gap.py -q`
    Exit 0: the old silent state is reproduced on the anchored base; the fixed compiler derives/delivers defended-trial policy with non-empty trial grants whenever the configuration explicitly requests it, while an explicit `observe_only` selection remains unchanged; and a one-cycle deterministic canary records defender, judge 0, and judge 1 provider dispatches in order, or records the first typed refusal verbatim as its registered terminal outcome.
In scope: (1) compilation behavior in `src/deepreason/run_manifest.py` under the forecast frozen-surface disposition; (2) the fresh tranche reproduction/canary and its focused regression test; (3) `DR-SUB-manifest`, `DR-CON-authority`, and `DR-CON-criticism-source` map records for this compilation seam.
NOT in scope: `rules/crit.py`, `informal/trial.py`, `config.py`, any other frozen surface, committed P-S1 evidence, bridge/frontier/scheduler selection, successor/scratch/premises, the jailbreak-gate-owned application/workflow/result files, or live R4/provider claims without a separately frozen and pushed preregistration plus an operator-supplied key.
Budget: <=150 implementation/test/map changed lines, 1 code commit plus mandatory phase/evidence commits, 5 hours
Stop conditions inherited from orchestrator: yes
