# PART 3 — the docs census

The operator's target: the test and experiment REPORTS that accumulated
in `docs/` — notes, reports, proposals, snapshots — "a lot of data with
no structure."

Every file under `docs/` is rowed, `docs/proposals/` and `docs/map/`
included. **No sampling.** Count: **131** files, of which **64** are
`docs/map/`.

Four questions per row; the FIRST that fires decides:

- **Q-D1 LIVING AUTHORITY?** The spec series and its amendments, the
  theory stack, `ERRATA.md`, `AUDIT_BASELINES.md`, the monitor
  handover, `OLLAMA_CLOUD_OPERATIONS.md`, and anything CLAUDE.md or a
  skill loads or cites = KEEP, citation given.
- **Q-D2 REFERENCED?** `grep` over `CLAUDE.md`, `.claude/skills/`,
  `docs/map/`, `src/`, `tests/`, `tools/` (plus `scripts/`,
  `README.md`) for the filename, then again for the stem — CLAUDE.md
  cites several of these WITHOUT the `.md` suffix, so a filename-only
  scan under-reports. A hit ONLY from another PRUNE-rowed document is
  noted, not a KEEP.
- **Q-D3 CONSUMED RESEARCH NOTE?** For each `docs/RESEARCH_*.md`,
  whether every header consumption point has LANDED, or any still
  gates future work.
- **Q-D4 SUPERSEDED SNAPSHOT OR REPORT?** Dated one-time reports and
  implemented proposals whose content a later ledger absorbed =
  PRUNE-CANDIDATE with the absorption citation. A report nothing
  absorbed is rowed KEEP-UNTIL-ABSORBED.

**`docs/map/` rows KEEP wholesale, as expected.** It is
self-authenticating: every load-bearing claim carries an executable
`check:` line, and the map tranches maintain it. Map documents are also
densely cross-referenced by each other — the six returning no filename
hit (`CON-problem-layer-lifecycle`, `INV-signal-contract`,
`SEAM-schools-x-scheduler`, `SUB-amendment`, `SUB-application`,
`SUB-periphery`) are all reached by stem, because `INDEX.md` routes by
`DR-` id rather than by filename.

## Counts

| verdict | files |
|---|---|
| KEEP | 104 |
| KEEP-UNTIL-ABSORBED | 14 |
| PRUNE-CANDIDATE | 13 |

## The table

| # | file | Q-D1 living authority | Q-D2 ref | Q-D2 hit | verdict | deciding reason |
|---|---|---|---|---|---|---|
| 1 | `ADMISSION_SPEC.md` | standalone behavioral spec (docs/INDEX.md Reference) | Y | src/deepreason/oracle.py:899:# Dataset oracle (docs/ADMISSION_SPEC.md §6): claims about admitte | **KEEP** | Q-D1 standalone behavioral spec (docs/INDEX.md Reference) |
| 2 | `AGENT.md` | — | Y | scripts/operator_drive.py:4:The model receives AGENT.md's tool surface + rules + playbook and a | **KEEP** | Q-D2 referenced |
| 3 | `AUDIT_BASELINES.md` | audit-family PRECEDENCE 2 | Y | CLAUDE.md:37: `docs/AUDIT_BASELINES.md`. Rated for inexpensive models — every step | **KEEP** | Q-D1 audit-family PRECEDENCE 2 |
| 4 | `AUTONOMICS_REPORT.md` | — | n | — | **KEEP-UNTIL-ABSORBED** | Q-D4 dated one-time run report (2026-07-05); no later ledger absorbed it |
| 5 | `AUTONOMOUS_SIMULATION_MIGRATION.md` | — | n | — | **KEEP-UNTIL-ABSORBED** | Q-D4 RunManifest v5 migration guide; companion to the above |
| 6 | `BASIN_REPORT.md` | CLAUDE.md Directory map (theory stack) | Y | src/deepreason/config.py:312: # Refuted-attractor orbiting floor (basin study, docs/BASIN_REPOR | **KEEP** | Q-D1 CLAUDE.md Directory map (theory stack) |
| 7 | `CACHE_DESIGN.md` | — | Y | src/deepreason/oracle.py:10:It generalizes what `scripts/cachebench.py` did once by hand (docs/ | **KEEP** | Q-D2 referenced |
| 8 | `CAN_LLMS_EXPLORE.md` | — | n | — | **KEEP-UNTIL-ABSORBED** | Q-D4 standing progress report / call for help; no later ledger absorbed it |
| 9 | `COMPUTABLE_CALCULUS.md` | — | Y | docs/map/CON-standing-and-background.md:36:The argument is Proposition 9.1 of `docs/COMPUTABLE_ | **KEEP** | Q-D2 referenced |
| 10 | `COMPUTABLE_CALCULUS.pdf` | — | n | — | **KEEP** | Q-D2 stem-referenced by docs/map/CON-standing-and-background.md, docs/map/SUB-calculus.md and src/deepreason/status_display.py (the .md twin is the cited artifact; the PDF is its rendering) |
| 11 | `CONTROLLER_SPEC.md` | standalone behavioral spec (docs/INDEX.md Reference) | Y | src/deepreason/controller.py:1:"""Self-calibrating controller (docs/CONTROLLER_SPEC.md) — minim | **KEEP** | Q-D1 standalone behavioral spec (docs/INDEX.md Reference) |
| 12 | `ERRATA.md` | CLAUDE.md session-start read; append-only forever | Y | CLAUDE.md:405: of the old one." See `docs/ERRATA.md` E26). | **KEEP** | Q-D1 CLAUDE.md session-start read; append-only forever |
| 13 | `ERRATA_EXECUTOR.md` | cited by .claude/skills/ | Y | .claude/skills/dr-execute-step/SKILL.md:59: EXCEEDED, never a footnote (`docs/ERRATA_EXECUTOR.m | **KEEP** | Q-D1 cited by .claude/skills/ |
| 14 | `EXPERIMENT_PROGRAM_2026-07.md` | — | Y | scripts/e31_benchmark/__init__.py:1:"""E3.1 ground-truth novelty benchmark builders (docs/EXPER | **KEEP** | Q-D2 referenced |
| 15 | `FORM_DR1_RUN_APPLICATION.md` | — | Y | src/deepreason/mcp_server.py:76: "FORM_DR1_RUN_APPLICATION.md documents) before any provider " | **KEEP** | Q-D2 referenced |
| 16 | `HANDOVER_2026-07-27.md` | — | n | — | **PRUNE-CANDIDATE** | Q-D4 dated session handover, superseded by every later handover |
| 17 | `HANDOVER_2026-08-02.md` | — | n | — | **PRUNE-CANDIDATE** | Q-D4 dated session handover, superseded by HANDOVER_2026-08-03 |
| 18 | `HANDOVER_2026-08-03.md` | — | n | — | **PRUNE-CANDIDATE** | Q-D4 dated session handover; its modularisation-ladder program completed (rungs 1-7 all have tranches) |
| 19 | `HANDOVER_MONITOR_2026-08-06.md` | — | n | — | **PRUNE-CANDIDATE** | Q-D4 superseded by HANDOVER_MONITOR_2026-08-10 (rowed KEEP as the monitor handover) |
| 20 | `HANDOVER_MONITOR_2026-08-10.md` | the monitor handover (close-out brief Q-D1), newest of its series | n | — | **KEEP** | Q-D1 the monitor handover (close-out brief Q-D1), newest of its series |
| 21 | `HIDDEN_LEGACY_INVENTORY.md` | — | n | — | **KEEP** | Q-D4 explicitly a STANDING document, promoted out of its tranche to repo-root by operator-approved SPEC Fork F4 so re-connection priorities can be decided from it |
| 22 | `INDEX.md` | docs navigation pointer layer (routes the whole tree) | Y | CLAUDE.md:14:`DR-SUB-`/`DR-CON-`/`DR-SEAM-` ids from `docs/map/INDEX.md`, read the seam | **KEEP** | Q-D1 docs navigation pointer layer (routes the whole tree) |
| 23 | `JOLT_CONTROL_PLANE_MIGRATION.md` | — | n | — | **KEEP-UNTIL-ABSORBED** | Q-D4 migration guide to the LIVING harness-spec-v1.5-amendment |
| 24 | `LESSONS_LEARNED_2026-08-17.md` | operator-named living reference (close-out brief Q-D4) | n | — | **KEEP** | Q-D1 operator-named living reference (close-out brief Q-D4) |
| 25 | `MINI_PLAN.md` | — | n | — | **KEEP-UNTIL-ABSORBED** | Q-D4 MiniReason construction plan; `deepreason reason --shallow` still ships the MiniReason engine. NOTE: 2026-08-13 audit P4 found its Status line cites two MISSING evidence files — that prompt is still open |
| 26 | `MINI_STRESS_REPORT.md` | — | Y | docs/map/SEAM-adjudication-x-rules.md:247: `docs/MINI_STRESS_REPORT.md` §F4, `tests/test_trial_ | **KEEP** | Q-D2 referenced |
| 27 | `OLLAMA_CLOUD_OPERATIONS.md` | operator-named living authority (close-out brief Q-D1) | n | — | **KEEP** | Q-D1 operator-named living authority (close-out brief Q-D1) |
| 28 | `OPERATOR_DIAGNOSIS.md` | — | Y | src/deepreason/report.py:418: # never arrives) into a visible signal (§12; docs/OPERATOR_DIAGNO | **KEEP** | Q-D2 referenced |
| 29 | `POIETIC_CALCULUS_FORMALIZED.md` | — | Y | docs/map/SUB-calculus.md:132:Definition 7.2 (`docs/POIETIC_CALCULUS_FORMALIZED.md` §7): an asse | **KEEP** | Q-D2 referenced |
| 30 | `POIETIC_CALCULUS_v0.1.md` | — | n | — | **PRUNE-CANDIDATE** | Q-D4 superseded by docs/POIETIC_CALCULUS_FORMALIZED.md (rowed KEEP, referenced); v0.1 self-describes as 'conjecture, not computable as stated' |
| 31 | `REPORT.md` | — | Y | CLAUDE.md:35: spec-drift, goal-trace). Read-only: produces AUDIT_REPORT.md plus a | **KEEP** | Q-D2 referenced |
| 32 | `RESEARCH_BACKEND.md` | — | Y | src/deepreason/capabilities/research.py:8:The two owner decisions (docs/RESEARCH_BACKEND.md) ar | **KEEP** | Q-D3 tranche-2 V6 in-run enablement still gated (V6_RESEARCH_UNAVAILABLE) — a live consumer |
| 33 | `RESEARCH_CONVERGENCE_LOOPS_2026-08-22.md` | — | n | — | **PRUNE-CANDIDATE** | Q-D3 all landed: its Rung 6 point is explicitly SUPERSEDED by RESEARCH_FINDINGS_Q1Q10's Rung 6 point, and Rung 6 landed (2026-08-24-change-rung6-frame-render-departures) |
| 34 | `RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` | — | Y | docs/map/CON-packs-and-token-economy.md:167:`docs/RESEARCH_FINDINGS_Q1Q10_2026-08-22.md` Q1 mea | **KEEP** | Q-D3 live consumers: the IAF layer is an OPEN operator decision on Rung 8 scope; label-flip-rate vs edge-error-rate is 'open item 2 and is OURS to run'; NEAR_DUP_EPS Q8 is a standing hard stop |
| 35 | `RESEARCH_JUDGE_BLINDING_2026-08-22.md` | — | Y | docs/map/CON-packs-and-token-economy.md:95:`docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md` measure | **KEEP** | Q-D3 standing judge-audit evidence base — CLAUDE.md solo-run law requires consulting it before any judge-leaning design |
| 36 | `RESEARCH_PROGRAM_2026-08-22.md` | — | n | — | **PRUNE-CANDIDATE** | Q-D3 the question list itself; Q1-Q10 answered in RESEARCH_FINDINGS_Q1Q10, Q11-Q12 in RESEARCH_SHAPE_CRITIQUE |
| 37 | `RESEARCH_SHAPE_CRITIQUE_2026-08-22.md` | — | n | — | **KEEP** | Q-D3 two OPEN parked design candidates: cross-lineage conjecture recombination, and the protected refinement stratum |
| 38 | `RESEARCH_STRUCTURED_OUTPUT_COERCION_2026-08-22.md` | — | n | — | **KEEP** | Q-D3 three open consumption points: schema hedge-impossibility audit 'ready to route', verdict-enum structured refusal, refusal-tax classification |
| 39 | `RUNTIME_IMPORTS.md` | — | n | — | **PRUNE-CANDIDATE** | Q-D4 documents run-local WEBSITE component-manifest imports; the website remnant was removed by experiments/2026-08-15-change-rung3d-website-remnant |
| 40 | `RUN_PLAN_TEMPLATE.md` | — | n | — | **KEEP-UNTIL-ABSORBED** | Q-D4 a fill-in template, not a report; pairs with docs/AGENT.md (rowed KEEP) |
| 41 | `SCRATCHPAD_GROUNDED_BRIDGE.md` | — | n | — | **KEEP-UNTIL-ABSORBED** | Q-D4 operator guide whose normative half is the LIVING harness-spec-v1.4-amendment; guide, not a dated report |
| 42 | `SELF_IMPROVEMENT.md` | — | n | — | **KEEP-UNTIL-ABSORBED** | Q-D4 driver instructions, pairs with docs/AGENT.md (rowed KEEP) |
| 43 | `SMALL_MODEL_COMPATIBILITY.md` | — | n | — | **KEEP-UNTIL-ABSORBED** | Q-D4 status page. NOTE: 2026-08-13 audit P5 found its named kernel identifier absent from code — that prompt is still open |
| 44 | `STATE_OF_THE_PROGRAM_2026-08-14.md` | — | n | — | **KEEP-UNTIL-ABSORBED** | Q-D4 the close-out brief makes it PRUNE-able ONCE ITS SUCCESSOR EXISTS; no successor state-of-the-program document exists on main, so it is the newest of its kind |
| 45 | `STATE_OF_THE_THEORY.md` | CLAUDE.md Directory map (theory stack) | n | — | **KEEP** | Q-D1 CLAUDE.md Directory map (theory stack) |
| 46 | `STRESS_INSIGHTS.md` | — | n | — | **KEEP-UNTIL-ABSORBED** | Q-D4 dated one-time campaign report (2026-07-04); no later ledger absorbed it |
| 47 | `TOKEN_ECONOMY.md` | CLAUDE.md Directory map (theory stack) | Y | docs/map/CON-packs-and-token-economy.md:296: "docs/TOKEN_ECONOMY.md angle 4"; prefix caching is | **KEEP** | Q-D1 CLAUDE.md Directory map (theory stack) |
| 48 | `TRANCHE_A_AUTONOMOUS_SIMULATION.md` | — | n | — | **KEEP-UNTIL-ABSORBED** | Q-D4 RunManifest v5 guide; normative half lives in the spec series |
| 49 | `TREADLE_ASSEMBLY.md` | — | Y | tools/treadle0.5/BUNDLE.md:165:`docs/TREADLE_ASSEMBLY.md`) a table: module → installed / skippe | **KEEP** | Q-D2 referenced |
| 50 | `harness-spec-v1.3.md` | spec series base (CLAUDE.md Directory map; docs/INDEX.md normative) | Y | src/deepreason/verification/report.py:1052: `docs/harness-spec-v1.3.md` §11.3: "if no test is e | **KEEP** | Q-D1 spec series base (CLAUDE.md Directory map; docs/INDEX.md normative) |
| 51 | `harness-spec-v1.4-amendment.md` | spec amendment (CLAUDE.md: read ALL amendments) | n | — | **KEEP** | Q-D1 spec amendment (CLAUDE.md: read ALL amendments) |
| 52 | `harness-spec-v1.5-amendment.md` | spec amendment (CLAUDE.md: read ALL amendments) | n | — | **KEEP** | Q-D1 spec amendment (CLAUDE.md: read ALL amendments) |
| 53 | `harness-spec-v1.6-amendment.md` | spec amendment (CLAUDE.md: read ALL amendments) | n | — | **KEEP** | Q-D1 spec amendment (CLAUDE.md: read ALL amendments) |
| 54 | `harness-spec-v1.7-amendment.md` | spec amendment (CLAUDE.md: read ALL amendments) | n | — | **KEEP** | Q-D1 spec amendment (CLAUDE.md: read ALL amendments) |
| 55 | `map/CON-authority.md` | — | Y | docs/map/INDEX.md:61:\| `CON-authority.md` \| who may change a Status, and the two authority voca | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 56 | `map/CON-capability-lifecycle.md` | — | Y | docs/map/INDEX.md:64:\| `CON-capability-lifecycle.md` \| typed proposal → admission → work order  | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 57 | `map/CON-conjecture-kinds.md` | — | Y | docs/map/INDEX.md:70:\| `CON-conjecture-kinds.md` \| formal vs informal, where kind is signaled,  | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 58 | `map/CON-conjecture-source.md` | — | Y | docs/map/INDEX.md:66:\| `CON-conjecture-source.md` \| the socket that proposes candidate artifact | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 59 | `map/CON-criticism-source.md` | — | Y | docs/map/INDEX.md:67:\| `CON-criticism-source.md` \| the socket that attacks or scrutinises a tar | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 60 | `map/CON-packs-and-token-economy.md` | — | Y | docs/map/INDEX.md:28:\| know what a pack shows about the frame it is posed in \| `SEAM-calculus-x | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 61 | `map/CON-problem-layer-lifecycle.md` | — | n | cross-referenced within docs/map/ (stem match) | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 62 | `map/CON-proof-debt-and-localization.md` | — | Y | docs/map/INDEX.md:71:\| `CON-proof-debt-and-localization.md` \| what a derived judgment rests on  | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 63 | `map/CON-run-identity.md` | — | Y | docs/map/INDEX.md:63:\| `CON-run-identity.md` \| deterministic run ids, roots on disk, retiring a | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 64 | `map/CON-scheduler-ranking.md` | — | Y | docs/map/INDEX.md:68:\| `CON-scheduler-ranking.md` \| which problem a cycle works on (`Scheduler. | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 65 | `map/CON-schools.md` | — | Y | docs/map/INDEX.md:60:\| `CON-schools.md` \| a stance, a lineage, and sometimes a route \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 66 | `map/CON-seats.md` | — | Y | docs/map/INDEX.md:69:\| `CON-seats.md` \| how a role becomes a provider request: `select_lease`,  | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 67 | `map/CON-standing-and-background.md` | — | Y | docs/map/INDEX.md:27:\| know why an artifact is (or is not) framing its problems \| `CON-standing | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 68 | `map/CON-warrants-and-attacks.md` | — | Y | docs/map/CON-run-identity.md:277: `docs/map/CON-warrants-and-attacks.md` and `docs/map/SUB-adju | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 69 | `map/INDEX.md` | — | Y | CLAUDE.md:14:`DR-SUB-`/`DR-CON-`/`DR-SEAM-` ids from `docs/map/INDEX.md`, read the seam | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 70 | `map/INV-axiom-basis.md` | — | Y | docs/map/INDEX.md:26:\| know which rung answers for a calculus axiom \| `INV-axiom-basis.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 71 | `map/INV-frozen-surfaces.md` | — | Y | CLAUDE.md:15:before the subsystems, and read `INV-frozen-surfaces.md` before designing. | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 72 | `map/INV-signal-contract.md` | — | n | cross-referenced within docs/map/ (stem match) | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 73 | `map/REC-add-signal.md` | — | Y | docs/map/INV-signal-contract.md:64:paydown rule is `REC-add-signal.md` §"paying down the debt": | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 74 | `map/REC-change-a-seam.md` | — | Y | .claude/skills/dr-execute-step/SKILL.md:79: is `docs/map/REC-change-a-seam.md`; how to write on | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 75 | `map/REC-revise-allocation-policy.md` | — | Y | docs/map/INV-signal-contract.md:215:\| revise the allocation policy \| `REC-revise-allocation-pol | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 76 | `map/SCHEMA.md` | — | Y | CLAUDE.md:451:everything else. `docs/map/SCHEMA.md` is the contract for reading and writing | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 77 | `map/SEAM-adjudication-x-authority.md` | — | Y | docs/map/INDEX.md:115:\| — \| adjudication × authority \| `SEAM-adjudication-x-authority.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 78 | `map/SEAM-adjudication-x-rules.md` | — | Y | docs/map/INDEX.md:116:\| — \| adjudication × rules \| `SEAM-adjudication-x-rules.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 79 | `map/SEAM-bridge-x-llm.md` | — | Y | docs/map/INDEX.md:104:\| 16 \| bridge × llm \| `SEAM-bridge-x-llm.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 80 | `map/SEAM-bridge-x-manifest.md` | — | Y | docs/map/INDEX.md:100:\| 21 \| bridge × manifest \| `SEAM-bridge-x-manifest.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 81 | `map/SEAM-calculus-x-rules.md` | — | Y | docs/map/INDEX.md:28:\| know what a pack shows about the frame it is posed in \| `SEAM-calculus-x | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 82 | `map/SEAM-capabilities-x-rules.md` | — | Y | docs/map/INDEX.md:117:\| — \| capabilities × rules \| `SEAM-capabilities-x-rules.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 83 | `map/SEAM-evaluation-x-ontology.md` | — | Y | docs/map/INDEX.md:106:\| 14 \| evaluation × ontology \| `SEAM-evaluation-x-ontology.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 84 | `map/SEAM-evaluation-x-rules.md` | — | Y | docs/map/INDEX.md:97:\| 29 \| evaluation × rules \| `SEAM-evaluation-x-rules.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 85 | `map/SEAM-harness-x-verification.md` | — | Y | docs/map/INDEX.md:118:\| — \| harness × verification \| `SEAM-harness-x-verification.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 86 | `map/SEAM-harness-x-workflow.md` | — | Y | docs/map/INDEX.md:108:\| 11 \| harness × workflow \| `SEAM-harness-x-workflow.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 87 | `map/SEAM-llm-x-manifest.md` | — | Y | docs/map/INDEX.md:98:\| 24 \| llm × manifest \| `SEAM-llm-x-manifest.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 88 | `map/SEAM-llm-x-rules.md` | — | Y | docs/map/INDEX.md:99:\| 22 \| llm × rules \| `SEAM-llm-x-rules.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 89 | `map/SEAM-llm-x-scheduler.md` | — | Y | docs/map/SUB-scheduler.md:225:`check: python -m pytest tests/test_route_lease_maxtokens_tuning. | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 90 | `map/SEAM-llm-x-workflow.md` | — | Y | docs/map/INDEX.md:96:\| 33 \| llm × workflow \| `SEAM-llm-x-workflow.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 91 | `map/SEAM-manifest-x-schools.md` | — | Y | docs/map/INDEX.md:114:\| — \| manifest × schools \| `SEAM-manifest-x-schools.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 92 | `map/SEAM-ontology-x-rules.md` | — | Y | docs/map/INDEX.md:101:\| 18 \| ontology × rules \| `SEAM-ontology-x-rules.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 93 | `map/SEAM-periphery-x-verification.md` | — | Y | docs/map/SEAM-harness-x-verification.md:300:`check: grep -q "artifact.provenance.role == \"impo | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 94 | `map/SEAM-rules-x-scratch.md` | — | Y | docs/map/INDEX.md:102:\| 18 \| rules × scratch \| `SEAM-rules-x-scratch.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 95 | `map/SEAM-rules-x-workflow.md` | — | Y | docs/map/INDEX.md:95:\| 37 \| rules × workflow \| `SEAM-rules-x-workflow.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 96 | `map/SEAM-scheduler-x-rules.md` | — | Y | docs/map/INDEX.md:109:\| 11 \| rules × scheduler \| `SEAM-scheduler-x-rules.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 97 | `map/SEAM-scheduler-x-workflow.md` | — | Y | docs/map/INDEX.md:103:\| 16 \| scheduler × workflow \| `SEAM-scheduler-x-workflow.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 98 | `map/SEAM-schools-x-scheduler.md` | — | n | cross-referenced within docs/map/ (stem match) | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 99 | `map/SEAM-schools-x-scratch.md` | — | Y | docs/map/INDEX.md:113:\| — \| schools × scratch \| `SEAM-schools-x-scratch.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 100 | `map/SEAM-scratch-x-workflow.md` | — | Y | docs/map/INDEX.md:107:\| 13 \| scratch × workflow \| `SEAM-scratch-x-workflow.md` \| | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 101 | `map/SUB-adjudication.md` | — | Y | docs/map/CON-run-identity.md:277: `docs/map/CON-warrants-and-attacks.md` and `docs/map/SUB-adju | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 102 | `map/SUB-amendment.md` | — | n | cross-referenced within docs/map/ (stem match) | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 103 | `map/SUB-application.md` | — | n | cross-referenced within docs/map/ (stem match) | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 104 | `map/SUB-bridge.md` | — | Y | docs/map/INDEX.md:49:\| `SUB-bridge.md` \| the grounded-application bridge: ledger, compose, evid | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 105 | `map/SUB-calculus.md` | — | Y | docs/map/INDEX.md:27:\| know why an artifact is (or is not) framing its problems \| `CON-standing | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 106 | `map/SUB-capabilities.md` | — | Y | docs/map/INDEX.md:47:\| `SUB-capabilities.md` \| simulation and research lifecycles. State digest | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 107 | `map/SUB-evaluation.md` | — | Y | docs/map/INDEX.md:53:\| `SUB-evaluation.md` \| programs, oracles, measures, informal trials — whe | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 108 | `map/SUB-evidence.md` | — | Y | docs/map/INDEX.md:50:\| `SUB-evidence.md` \| attached dossiers, admitted blocks, and byte-checked | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 109 | `map/SUB-harness.md` | — | Y | docs/map/INDEX.md:41:\| `SUB-harness.md` \| the append-only log, event application, state materia | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 110 | `map/SUB-llm.md` | — | Y | docs/map/INDEX.md:45:\| `SUB-llm.md` \| adapter, route firewall, packs, wire contracts, repair, p | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 111 | `map/SUB-manifest.md` | — | Y | docs/map/INDEX.md:52:\| `SUB-manifest.md` \| RunManifest schema and validators, qualification. ** | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 112 | `map/SUB-ontology.md` | — | Y | docs/map/INDEX.md:40:\| `SUB-ontology.md` \| Artifact, Commitment, Warrant, Problem, Interface, E | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 113 | `map/SUB-periphery.md` | — | n | cross-referenced within docs/map/ (stem match) | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 114 | `map/SUB-rules.md` | — | Y | docs/map/INDEX.md:42:\| `SUB-rules.md` \| conjecture, criticism, warrants, spawn, guards — the ep | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 115 | `map/SUB-scheduler.md` | — | Y | docs/map/INDEX.md:44:\| `SUB-scheduler.md` \| problem selection, cycles, budgets, school and capa | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 116 | `map/SUB-scratch.md` | — | Y | docs/map/INDEX.md:46:\| `SUB-scratch.md` \| the imaginative workshop, declared `advisory_non_grou | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 117 | `map/SUB-verification.md` | — | Y | docs/map/INDEX.md:51:\| `SUB-verification.md` \| `verify_root`, replay validation, epistemic chec | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 118 | `map/SUB-workflow.md` | — | Y | docs/map/INDEX.md:48:\| `SUB-workflow.md` \| the v6 transactional work lifecycle, replay, recover | **KEEP** | docs/map — self-authenticating (executable check: lines), maintained by map tranches |
| 119 | `proposals/AMENDMENT_EPOCHS.md` | CLAUDE.md Live runs (amend mechanism) | Y | CLAUDE.md:220: epoch to the stopped one (docs/proposals/AMENDMENT_EPOCHS.md), then | **KEEP** | Q-D1 CLAUDE.md Live runs (amend mechanism) |
| 120 | `proposals/BEHAVIOR_MODES_PREPLAN.md` | CLAUDE.md seats law (modes/packages guardrail) | n | — | **KEEP** | Q-D1 CLAUDE.md seats law (modes/packages guardrail) |
| 121 | `proposals/CALCULUS_IMPLEMENTATION_ADVICE.md` | — | n | — | **KEEP-UNTIL-ABSORBED** | Q-D4 advice document for the calculus program, which is live (v2 reconciliation, Rungs 1-8) |
| 122 | `proposals/CODER_AS_TOOL_PREPLAN.md` | — | n | — | **PRUNE-CANDIDATE** | Q-D4 pre-plan; no tranche cites it and no rung implements it |
| 123 | `proposals/CRITICISM_SYMMETRY_RESEARCH_PREPLAN.md` | — | n | — | **PRUNE-CANDIDATE** | Q-D4 pre-plan; superseded by the shipped criticism-source/prose-can-refute work |
| 124 | `proposals/DETERMINISTIC_GATES_PREPLAN.md` | — | Y | tools/blast_radius.py:82:(docs/proposals/DETERMINISTIC_GATES_PREPLAN.md's own shape rule). | **KEEP** | Q-D2 referenced |
| 125 | `proposals/DUAL_MODE_CONJECTURE_PREPLAN.md` | CLAUDE.md formalism law R-g | Y | CLAUDE.md:331: law. See DUAL_MODE_CONJECTURE_PREPLAN.md R-g for the full binding | **KEEP** | Q-D1 CLAUDE.md formalism law R-g |
| 126 | `proposals/GATES_AND_PACKAGES_PREPLAN.md` | — | n | — | **KEEP-UNTIL-ABSORBED** | Q-D4 pre-plan; its guardrail half is quoted by CLAUDE.md's seats law alongside BEHAVIOR_MODES_PREPLAN |
| 127 | `proposals/GROUNDED_OVERLAY_PREPLAN.md` | — | n | — | **PRUNE-CANDIDATE** | Q-D4 pre-plan implemented by experiments/2026-08-08-change-grounded-overlay-o1 and -o2 |
| 128 | `proposals/HARD_QUESTION_SET_PROMPT.md` | — | n | — | **PRUNE-CANDIDATE** | Q-D4 one-time prompt text, executed by experiments/2026-08-09-change-hard-question-set |
| 129 | `proposals/README.md` | index for docs/proposals/ | Y | .claude/skills/dr-drive-harness/SKILL.md:58:The supported product surface (authority: `README.m | **KEEP** | Q-D1 index for docs/proposals/ |
| 130 | `proposals/RECORD_LIFECYCLE_DEFECT_PLAN.md` | — | n | — | **PRUNE-CANDIDATE** | Q-D4 defect plan; the record-lifecycle parity defect it names was fixed by experiments/2026-08-13-change-lifecycle-operation-parity and -single-run-path-unification |
| 131 | `proposals/ROLE_SEAT_SEPARATION_PLAN.md` | CLAUDE.md seats law S7 | Y | src/deepreason/seat_bindings.py:9:ROLE_SEAT_SEPARATION_PLAN.md`` and ``docs/map/CON-seats.md``) | **KEEP** | Q-D1 CLAUDE.md seats law S7 |
