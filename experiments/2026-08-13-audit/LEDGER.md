# LEDGER — 2026-08-13 audit

Date: 2026-08-13 (UTC)
Model: claude-sonnet-5
HEAD sha: 51f16b92f8170c352775887076dfa92882651a60
Baselines-file sha: 16f9e569c3a3deb48ad6cc25d8534e3f3d3dd4a7

This is the first `dr-audit-orchestrator` run in this clone for this
model id — no prior `ACTIVATION.md` under this skill family exists
(the only earlier tranche matching `*audit*`,
`experiments/2026-08-11-errata-checkpoint-audit/`, predates this
skill family and used a different, ad-hoc report format). Activation
required.

## Findings

| id | dimension | target | gate | verdict | proof file | disposition |
|---|---|---|---|---|---|---|
| A1 | activation/broken | `test_catalog_covers_46_entries` (planted) | pass | broken (planted, restored) | proof/activation-broken-red.txt | activation |
| A2 | activation/dead | `lookup` (planted candidate-dead) | pass (refused) | referenced (planted refused) | proof/activation-dead.txt | activation |
| A3 | activation/docs-drift | `docs/map/SUB-scheduler.md:97` (planted) | pass (blind, valid per spec) | baseline (planted, restored) | proof/activation-docs-drift.txt | activation |
| A4 | activation/spec-drift | `FAKE_NONEXISTENT_SPEC_TERM_XYZ` (planted) | pass | spec-orphan (planted, removed) | proof/activation-spec-drift.txt | activation |
| A5 | activation/goal-trace | "all conjectures must rhyme" (planted) | pass | unenforced (planted, removed) | proof/activation-goal-trace.txt | activation |
| B1 | broken | full pytest gate | pass | baseline | proof/broken-pytest.txt | baseline |
| B2 | broken | docs_verify (default) | pass | baseline | proof/broken-docsverify.txt | baseline |
| B3 | broken | wheel_smoke.py | pass | baseline | proof/broken-wheelsmoke.txt | baseline |
| B4 | broken | wheel_operational_smoke.py | pass | baseline | proof/broken-wheeloperational.txt | baseline |
| B5 | broken | root_sweep.py census | pass | baseline (unchanged reader) | proof/broken-sweep-comparison-2026-08-12.txt | baseline |
| B6 | broken | root_sweep.py CLI vs dr-audit-broken's documented invocation | pass | broken | proof/broken-sweep.txt | parked |
