# LEDGER — 2026-08-25 post-program close-out audit

Date: 2026-08-25 (UTC)
Model: claude-opus-5
HEAD sha: 853bf705cca96e97c22d193df5b1889511bd92c4
Baselines-file sha: eac1b17b527ec6dfe4992b7a3d9cc81ba03610d8
Comparison copy: `experiments/2026-08-13-audit/`

## Scope

Seven dimensions, not five. PART 1 is the standard audit family
(broken, dead, docs-drift, spec-drift, goal-trace) against
`docs/AUDIT_BASELINES.md` as it stands on main. PART 2 and PART 3 are
guided censuses added by the operator's close-out instruction, whose
purpose is a DELETION DECISION:

> "all experiments and tests need to be audited so I can get rid of
> them."

READ-ONLY everywhere. This audit deletes nothing; it rows verdicts and
writes ready-to-send deletion prompts.

## Activation

Prior `ACTIVATION.md` in this clone is `experiments/2026-08-13-audit/
ACTIVATION.md`, recorded for model `claude-sonnet-5`. This run is
`claude-opus-5` — a model change, so per the router's activation rule
each worker GATE is re-proven red once. See `ACTIVATION.md`.

## Findings

| id | dimension | target | gate | verdict | proof file | disposition |
|---|---|---|---|---|---|---|
| A1 | activation/spec-drift | fabricated term `ZzFabricatedSpecTermQqq` | pass | spec-orphan (planted, zero hits) | proof/activation-spec-drift.txt | activation |
| A2 | activation/goal-trace | fabricated law "Every conjecture must rhyme" | pass | unenforced (planted, both scans empty) | proof/activation-goal-trace.txt | activation |
| A3 | activation/dead | `verify_root` rowed as candidate-dead | pass (refused) | referenced (planted row refused by step 2) | proof/activation-dead.txt | activation |
| A4 | activation/broken | planted false assert in a copied test | pass | broken (planted, restored) | proof/activation-broken.txt | activation |
| A5 | activation/docs-drift | numeral edited in a map prose claim | pass | see proof (red or blind, both valid) | proof/activation-docs-drift.txt | activation |
| B1 | broken | full pytest gate — 4162 passed, 6 skipped, 0 failed | pass | baseline | proof/broken-gate.txt | baseline |
| B2 | broken | `docs_verify` full — 64 docs, 1069 checks, 3 failed | pass | baseline (shallow clone, cause confirmed) | proof/docs-full.txt | baseline |
| B3 | broken | `wheel_smoke` — exit 0 | pass | baseline | proof/wheel-smoke.txt | baseline |
| B4 | broken | `wheel_operational_smoke` | pass | see broken.md | proof/wheel-operational-smoke.txt | baseline |
| B5 | broken | root sweep | n/a | RETIRED 2026-08-22 — not run | proof/broken-sweep.txt | baseline |
| B6 | broken | `treadle doctor` | blocked | not-runnable (venv absent + no credential) | proof/treadle-doctor.txt | parked (P6) |
| B7 | broken | cycle soak | blocked | not-run (no live launch in this tranche) | proof/cycle-soak.txt | baseline |
| DD1 | docs-drift | `docs_verify` full | pass | baseline | proof/docs-full.txt | baseline |
| DD2 | docs-drift | `docs_verify --audit` — 0 findings | pass | baseline | proof/docs-audit.txt | baseline |
| DD3 | docs-drift | `docs_verify --links` — 0 dangling | pass | baseline | proof/docs-links.txt | baseline |
| DD4 | docs-drift | `docs_verify --stale` — 8 documents (was 0) | pass | stale-stamp | proof/docs-stale.txt | baseline (advisory) |
| DD5 | docs-drift | `docs/MINI_PLAN.md` cites a missing evidence file | pass | drifted | proof/docs-claim-verification.txt | parked (already 2026-08-13 P4) |
| DD6 | docs-drift | `docs/ADMISSION_SPEC.md` "v1 IMPLEMENTED" | pass | covered | proof/docs-claim-verification.txt | baseline |
| DD7 | docs-drift | `docs/RESEARCH_BACKEND.md` "tranche 1 IMPLEMENTED" | pass | covered | proof/docs-claim-verification.txt | baseline |
| SD1 | spec-drift | `ContextRequest` | pass | spec-orphan | proof/spec-orphan-wordbound.txt | parked (P2) |
| SD2 | spec-drift | `codec:json` | pass | spec-orphan | proof/spec-orphan-wordbound.txt | parked (P2) |
| SD3 | spec-drift | `novel-case` | pass | spec-orphan | proof/spec-orphan-wordbound.txt | parked (P2) |
| SD4 | spec-drift | `workflow-resume-decision.v1` | pass | spec-orphan | proof/spec-orphan-wordbound.txt | parked (P2) |
| SD5 | spec-drift | `R_t` | pass | covered | proof/spec-orphan-wordbound.txt | baseline |
| SD6 | spec-drift | `deepreason.config.load` | pass | covered | proof/spec-orphan-wordbound.txt | baseline |
| SD7 | spec-drift | CLI flags 34/76 spec-silent | pass | spec-silent (batched) | proof/tree-cli-flags-silent.txt | parked (P3) |
| SD8 | spec-drift | config fields 65/89 spec-silent (+14) | pass | spec-silent (batched) | proof/tree-config-fields-silent.txt | parked (P3) |
| SD9 | spec-drift | typed strings 144/148 spec-silent (+26) | pass | spec-silent (batched) | proof/tree-error-strings-silent.txt | parked (P3) |
| SD10 | spec-drift | CLI-flag match rule 74-vs-34 | pass | method artifact, NOT a delta | proof/spec-method.txt | baseline |
| L1 | goal-trace | Formalism is an option | pass | enforced | proof/goal-L1.txt | baseline |
| L2 | goal-trace | Seats change GENERATED not EVIDENCE | pass | enforced (was partially) | proof/goal-L2.txt | baseline (improved) |
| L3 | goal-trace | Solo run with everything on | pass | enforced | proof/goal-L3.txt | baseline |
| L4 | goal-trace | Tokens are cheap, the agent is not | pass | process-law | proof/goal-L4.txt | baseline |
| L5 | goal-trace | All configurations allowed | pass | enforced (was partially) | proof/goal-L5.txt | baseline (improved) |
| L6 | goal-trace | Operations available to every configuration | pass | enforced (NEW law) | proof/goal-L6.txt | baseline |
| L7 | goal-trace | Old runs owe the future nothing | pass | enforced (NEW law) | proof/goal-L7.txt | baseline |
| L8 | goal-trace | Signal registry is a CONTRACT | pass | enforced (NEW law) | proof/goal-L8.txt | baseline |
| GT1 | goal-trace | `dr-drive-harness` + `dr-spec-change` require the retired root sweep | pass | drifted (skill vs standing operator ruling) | proof/goal-L7.txt | parked (P1) |
| CE1 | census/experiments | 152 directories rowed: 82 KEEP, 18 EXTRACT-THEN-PRUNE, 52 PRUNE | pass | census complete | experiments-census.md | parked (P4) |
| CE2 | census/experiments | 60 open park items inside the 18 EXTRACT rows | pass | must be re-homed before deletion | proof/census-citation-cost.txt | parked (P4 stage 1) |
| CE3 | census/experiments | 105 prose citations from KEEP rows into PRUNE rows | pass | cost neither gate can see | proof/census-citation-cost.txt | baseline (priced, not blocking) |
| CE4 | census/experiments | 25 map `check:` lines execute against `experiments/` roots | pass | KEEP rows are load-bearing | proof/census-keep-is-load-bearing.txt | baseline |
| CD1 | census/docs | 131 files rowed: 104 KEEP, 14 KEEP-UNTIL-ABSORBED, 13 PRUNE-CANDIDATE | pass | census complete | docs-census.md | parked (P5) |
| CD2 | census/docs | `docs/map/` (64 files) rows KEEP wholesale | pass | self-authenticating | docs-census.md | baseline |
