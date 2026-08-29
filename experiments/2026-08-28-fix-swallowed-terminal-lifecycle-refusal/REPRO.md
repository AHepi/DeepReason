# REPRO — the smallest offline demonstration, run in this window

No provider, no credential, ~98 s. Committed artifacts:
`proof/soak-report-epoch3-c3.json`, `proof/q4_before.json`,
`proof/before_results.txt`, `proof/before_continue.txt`.

## The recipe

```
python -u scripts/cycle_soak.py --case epoch3 --cycles 3 --keep --out <dir>
python experiments/2026-08-28-audit-run-problems/probes/q4_lifecycle_surfaces.py <dir>/run
python -m deepreason results <dir>/run | tail -4
export DEEPREASON_LOOPBACK_SMOKE_KEY=$(python -c \
  "import sys;sys.path.insert(0,'scripts');from wheel_operational_smoke import TEST_CREDENTIAL;print(TEST_CREDENTIAL)")
python -m deepreason --root <dir>/run continue --budget cycles=2 --token-budget 50000
```

**Case-name correction, recorded rather than silently fixed.** P6's recipe
names `--case pt1`. That case does not exist on `main`
(`--list-cases` gives `epoch3, pr1, pc1, pc2, pc2b, split-legs,
reach-rich`). `epoch3` — the solo glm-5.2 shape across all 11 canonical
roles — reproduces the defect identically and is used throughout.

**A second, unrelated defect met on the way, PARKED not fixed.**
`--case pc1` cannot build at all on `main`:
`V6_SIMULATION_TOOLCHAIN_REQUIRED: policy must bind one frozen toolchain`
from `run_manifest.py:3845`, raised inside
`experiments/2026-08-25-change-constructive-frontier/build_manifest_pc1.py:125`.
Recorded in `PARKED.md`; out of this tranche's cone (`run_manifest.py` is a
frozen surface and belongs to the manifest tranche).

## The result — the two surfaces, on one fresh root

```
run-status.json      state=completed  stop_reason=budget_exhausted  token_spend=139356
workflow_state       terminal_lifecycle_decision=None   lifecycle_decisions=0
                     outstanding_work_order_ids = 11 items
                     terminal_commitment_present=True
REPLAY_VALIDATION    valid, 0 violations

$ deepreason results <root>
  stands at a valid typed terminal: yes (terminal epoch 0)
  stop reason is resumable: yes
  ready for `deepreason amend` / `deepreason continue`: yes      <-- claim

$ deepreason --root <root> continue --budget cycles=2 --token-budget 50000
  CONTINUE_TYPED_STOP_REQUIRED                          (rc=1)   <-- refusal
```

`q4_before.json` states it as one boolean: `"surfaces_disagree": true`.

## What the reproduction establishes, and what it does not

ESTABLISHES: the defect is live on `main` at 90b1347f4, reachable offline,
on a SOLO configuration, in 98 seconds. The audit's finding is not
history — it is reproducible on demand.

DOES NOT ESTABLISH: that outstanding workflow authority *should* permit
continuation. This tranche does not ask that question (P2).
