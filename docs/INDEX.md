# docs/ — navigation index

`docs/` holds ~100 files with no single naming convention (measured
2026-08-11, `experiments/2026-08-11-spec-drift-measurement/
DOCS_REORG_PROPOSAL.md`). This page is a pointer layer only — it adds
no facts of its own and moves nothing. If this page and the document it
points to ever disagree, the pointed-to document is right; fix this
page's link, not the other way around.

## Reference — what the system IS

- **[`docs/map/INDEX.md`](map/INDEX.md)** — the code map: what each
  package owns, entry points, state, and how packages meet. Start here
  for any question about how the CODE actually works. Distinct from
  this file: `docs/map/` describes `src/deepreason/`; this page
  describes `docs/` itself.
- **[`docs/map/INV-frozen-surfaces.md`](map/INV-frozen-surfaces.md)** —
  the five things you may not change without explicit operator
  approval. Read before designing any change.
- The harness spec series (normative, append-only amendment chain —
  never edit an earlier file, only add a new one):
  [`harness-spec-v1.3.md`](harness-spec-v1.3.md) (base) →
  [`v1.4-amendment.md`](harness-spec-v1.4-amendment.md) →
  [`v1.5-amendment.md`](harness-spec-v1.5-amendment.md) →
  [`v1.6-amendment.md`](harness-spec-v1.6-amendment.md) →
  [`v1.7-amendment.md`](harness-spec-v1.7-amendment.md). Read ALL
  amendments; each says explicitly what it does and does not change.
- Standalone behavioral specs: [`CONTROLLER_SPEC.md`](CONTROLLER_SPEC.md),
  [`ADMISSION_SPEC.md`](ADMISSION_SPEC.md).

## Explanation — why things are the way they are

Per-tranche narrative lives in `experiments/<date>-<slug>/RESULTS.md`,
NOT here — this index does not duplicate that list, since experiment
tranches are created continuously and a static copy would go stale
immediately. Standalone technical reports that predate that convention
still live at top level:
[`STATE_OF_THE_THEORY.md`](STATE_OF_THE_THEORY.md),
[`TOKEN_ECONOMY.md`](TOKEN_ECONOMY.md),
[`BASIN_REPORT.md`](BASIN_REPORT.md),
[`CAN_LLMS_EXPLORE.md`](CAN_LLMS_EXPLORE.md),
[`MINI_STRESS_REPORT.md`](MINI_STRESS_REPORT.md),
[`AUTONOMICS_REPORT.md`](AUTONOMICS_REPORT.md),
[`STRESS_INSIGHTS.md`](STRESS_INSIGHTS.md),
[`OPERATOR_DIAGNOSIS.md`](OPERATOR_DIAGNOSIS.md),
[`REPORT.md`](REPORT.md).

Relocated: **`PATROL_DETERMINISM_REPORT.md`** moved 2026-08-11 to
[`experiments/2026-08-08-corpus-enrichment-patrol-pilot/PATROL_DETERMINISM_REPORT.md`](../experiments/2026-08-08-corpus-enrichment-patrol-pilot/PATROL_DETERMINISM_REPORT.md)
— its own opening line named that one directory as its exclusive data
source, an unambiguous origin (`experiments/2026-08-11-spec-drift-
measurement/DOCS_REORG_PROPOSAL.md` step 3).

The other four reports above stayed at `docs/` top level rather than
moving — each was checked against the same "traces unambiguously to
one origin directory" test and failed it, or is otherwise blocked:

- **`BASIN_REPORT.md`** stayed: cited by code/test comments
  (`src/deepreason/config.py`, `src/deepreason/capture/ladder.py`,
  `src/deepreason/capture/detection.py`, `tests/test_orbit.py`) —
  moving it would strand those comments' relative paths, which the
  reorg proposal names as a hard never-move constraint. Its own
  evidence also spans loose top-level `experiments/` files rather
  than one dated directory.
- **`CAN_LLMS_EXPLORE.md`** stayed: its cited evidence
  (`experiments/basin_study_prereg.yaml`,
  `experiments/results/mini_creativity_report.json`,
  `experiments/results/mini_smoke_report.json`) spans several loose
  top-level files, not one dated experiment directory.
- **`MINI_STRESS_REPORT.md`** stayed: its cited evidence
  (`experiments/results/mini_chaos_report.json`,
  `experiments/results/mini_gauntlet_report.json`) is likewise loose,
  and the report itself says it "predates MiniReason's shared-kernel
  consolidation" — no single current tranche produced it.
- **`AUTONOMICS_REPORT.md`** stayed: its cited evidence
  (`experiments/solo_autonomics_design.md`) is one loose design file,
  not a dated experiment directory.

## Decisions — proposed, not all accepted

**[`docs/proposals/`](proposals/)** — a pre-acceptance decision queue:
design proposals (`*_PREPLAN.md`, `*_PLAN.md`), each carrying its own
free-text `Status:` header (accepted / superseded / open). Not yet
organized as one-decision-per-file the way an Architecture Decision
Record chain would be — read each file's own `Status:` line, since a
proposal here is not automatically current practice.

New-file-forward naming: from 2026-08-11, brand-new proposals use
`ADR-NNNN-<slug>.md` numbering — see
[`docs/proposals/README.md`](proposals/README.md) for the full
convention. Existing `*_PREPLAN.md`/`*_PLAN.md` files are NOT renamed.

## Corrections — what was found wrong, and where

Neither reference nor explanation nor a decision record: an append-only
ledger of claims a committed document made that the record later
showed to be wrong. Never edits the original claim in place.

- **[`docs/ERRATA.md`](ERRATA.md)** — corrections to ordinary committed
  documents (handovers, map, specs, RESULTS.md).
- **[`docs/ERRATA_EXECUTOR.md`](ERRATA_EXECUTOR.md)** — corrections
  scoped to the less-capable-executor infrastructure (the cross-cutting
  skills, calibration blocks, the 2026-08-03 handover program).

## How-to and operational reference

- [`FORM_DR1_RUN_APPLICATION.md`](FORM_DR1_RUN_APPLICATION.md) — the
  full CLI/config surface, one form per part of a run application.
- [`RUN_PLAN_TEMPLATE.md`](RUN_PLAN_TEMPLATE.md),
  [`SMALL_MODEL_COMPATIBILITY.md`](SMALL_MODEL_COMPATIBILITY.md),
  [`RESEARCH_BACKEND.md`](RESEARCH_BACKEND.md).
- [`AUDIT_BASELINES.md`](AUDIT_BASELINES.md) — expected instrument
  outputs the dr-audit skill family compares against; moves only in
  the same commit as whatever moved a value.
- [`OLLAMA_CLOUD_OPERATIONS.md`](OLLAMA_CLOUD_OPERATIONS.md) —
  operator-supplied provider intelligence (2026-08-12): plan-gated
  account concurrency, 429 disambiguation (queue vs quota), mid-stream
  200-with-error hazard, model-retirement reproducibility rules. Claims
  carry their own [DOCUMENTED]/[INFERRED]/[UNKNOWN] tags; read §8
  before letting any driver retry or parallelize.

## Dated snapshots (one-off, not living references)

[`HANDOVER_2026-07-27.md`](HANDOVER_2026-07-27.md),
[`HANDOVER_2026-08-02.md`](HANDOVER_2026-08-02.md),
[`HANDOVER_2026-08-03.md`](HANDOVER_2026-08-03.md),
[`HANDOVER_MONITOR_2026-08-06.md`](HANDOVER_MONITOR_2026-08-06.md) —
session handoffs frozen at the date in their filename; treat as
history, not current instruction (current instruction is `CLAUDE.md`
and `.claude/skills/`).

## Design and migration notes

[`AUTONOMOUS_SIMULATION_MIGRATION.md`](AUTONOMOUS_SIMULATION_MIGRATION.md),
[`JOLT_CONTROL_PLANE_MIGRATION.md`](JOLT_CONTROL_PLANE_MIGRATION.md),
[`TRANCHE_A_AUTONOMOUS_SIMULATION.md`](TRANCHE_A_AUTONOMOUS_SIMULATION.md),
[`CACHE_DESIGN.md`](CACHE_DESIGN.md),
[`RUNTIME_IMPORTS.md`](RUNTIME_IMPORTS.md),
[`SCRATCHPAD_GROUNDED_BRIDGE.md`](SCRATCHPAD_GROUNDED_BRIDGE.md),
[`SELF_IMPROVEMENT.md`](SELF_IMPROVEMENT.md),
[`MINI_PLAN.md`](MINI_PLAN.md), [`AGENT.md`](AGENT.md),
[`EXPERIMENT_PROGRAM_2026-07.md`](EXPERIMENT_PROGRAM_2026-07.md).

## What never moves

`docs/map/*.md` (854 automated checks, `tools/docs_verify.py`),
`docs/ERRATA.md`, `docs/ERRATA_EXECUTOR.md`, and the harness spec
series are cited by code, tests, or other documents — see
`experiments/2026-08-11-spec-drift-measurement/DOCS_REORG_PROPOSAL.md`
for the full load-bearing-paths evidence. This index adding a link is
the only kind of change made to any of them by this page's existence.
