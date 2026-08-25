# PART 2 — the experiments census

Operator's authority, verbatim:

> "all experiments and tests need to be audited so I can get rid of them."


Every directory under `experiments/` is rowed. **No sampling.** Count:
**152** directories (`ls -d experiments/*/` = 153, minus this
audit's own tranche directory = 152).

Four mechanical questions per row, in precedence order — the FIRST one
that fires decides the verdict:

- **Q-E1 REFERENCED?** `grep` over `tests/`, `src/`, `scripts/`,
  `tools/`, `docs/map/` for the directory's path. Any hit = KEEP.
  Run in TWO shapes and unioned, because one shape alone under-reports:
  a literal-path grep, and a basename grep that catches both the
  tranche-name citation style (`Regression (tranche
  2026-08-16-change-embedder-auto-install)`) and paths a script
  CONSTRUCTS rather than spells (`scripts/e31_benchmark/build_demo.py`
  joins `"experiments" / "e31_demo_benchmark"`). Path-only = 74 hits;
  the union = 79. The 5-row difference is exactly those two styles.
- **Q-E2 OPEN PARKS?** Enumerated items in the directory's `PARKED.md`,
  and whether a LATER tranche's execution artifact
  (`DELIVERY.md`/`VALIDATION.md`/`VERIFY.md`/`FIX.md`/`CHECKLIST.md`,
  or `docs/ERRATA.md`) cites that `PARKED.md`. A citation from another
  `PARKED.md` is a CARRY-FORWARD, not an execution — the item is still
  open, just re-parked. Self-directory citations are excluded. Open
  items = EXTRACT-THEN-PRUNE, never plain PRUNE.
- **Q-E3 NAMED BY AUTHORITY?** Named by path in `CLAUDE.md`,
  `docs/AUDIT_BASELINES.md`, or a `.claude/skills/` file = KEEP.
- **Q-E4 SUPERSEDED NARRATIVE?** Whether a later tranche or
  `docs/ERRATA.md` absorbed the RESULTS. Supporting evidence for PRUNE,
  never decisive. Git history keeps every byte, so a PRUNE row loses
  nothing that cannot be recovered by `git show`.

## Counts

| verdict | directories |
|---|---|
| KEEP | 82 |
| EXTRACT-THEN-PRUNE | 18 |
| PRUNE | 52 |
| **leaving the tree (EXTRACT + PRUNE)** | **70** |

**60 open park items** sit inside the 18
EXTRACT-THEN-PRUNE directories. Those are the items that MUST be re-homed
before any deletion runs. (191 open park items exist repo-wide; the
remainder live in KEEP directories and stay where they are.)

## The table

| # | directory | Q-E1 referenced | Q-E2 parks | Q-E3 authority | Q-E4 absorbed | verdict | deciding reason |
|---|---|---|---|---|---|---|---|
| 1 | `2026-07-30-change-amendment-epochs` | n — — | 4 item(s) OPEN (no execution citation) | — | later:2026-07-30-fix-citation-quote-check | **EXTRACT-THEN-PRUNE** | Q-E2 4 open park item(s) |
| 2 | `2026-07-30-fix-citation-quote-check` | n — — | 1 item(s) OPEN (no execution citation) | — | later:2026-07-30-fix-sandbox-contract | **EXTRACT-THEN-PRUNE** | Q-E2 1 open park item(s) |
| 3 | `2026-07-30-fix-sandbox-contract` | n — — | 1 item(s) OPEN (no execution citation) | — | — | **EXTRACT-THEN-PRUNE** | Q-E2 1 open park item(s) |
| 4 | `2026-07-31-change-critic-seats-and-thinking` | n — — | no PARKED.md | — | later:2026-07-31-schema-sweep | **PRUNE** | Q-E1/E2/E3 all negative |
| 5 | `2026-07-31-schema-sweep` | n — — | no PARKED.md | — | later:2026-08-09-overnight-omnibus | **PRUNE** | Q-E1/E2/E3 all negative |
| 6 | `2026-08-01-change-prose-can-refute` | Y — tests/test_pack_prefix.py:73: experiments/2026-08-01-change-prose-can-refute/S | 8 item(s) OPEN (no execution citation) | — | later:2026-08-09-change-adjudication-judge-seats-optins | **KEEP** | Q-E1 referenced |
| 7 | `2026-08-01-fix-adjudication-blindness` | n — — | 14 item(s); executed-cite: experiments/2026-08-01-change-prose-can-refute/DELIVERY.md | — | later:2026-08-01-change-prose-can-refute | **PRUNE** | Q-E1/E2/E3 all negative |
| 8 | `2026-08-01-fix-decomposition-merge-pairing` | n — — | 9 item(s) OPEN (no execution citation) | — | later:2026-08-01-fix-adjudication-blindness | **EXTRACT-THEN-PRUNE** | Q-E2 9 open park item(s) |
| 9 | `2026-08-02-map-falsification` | n — — | 6 item(s) OPEN (no execution citation) | — | later:2026-08-02-stress-triplet | **EXTRACT-THEN-PRUNE** | Q-E2 6 open park item(s) |
| 10 | `2026-08-02-stress-triplet` | Y — tests/test_attached_evidence_citation.py:4:The triage run of experiments/2026- | no PARKED.md | — | ERRATA later:2026-08-03-fix-attached-evidence-integrity | **KEEP** | Q-E1 referenced |
| 11 | `2026-08-03-change-driving-skill` | n — — | 3 item(s) OPEN (no execution citation) | — | later:2026-08-03-change-rung1-sockets-on-paper | **EXTRACT-THEN-PRUNE** | Q-E2 3 open park item(s) |
| 12 | `2026-08-03-change-executor-errata` | n — — | no PARKED.md | — | — | **PRUNE** | Q-E1/E2/E3 all negative |
| 13 | `2026-08-03-change-modularisation-handover` | n — — | no PARKED.md | — | — | **PRUNE** | Q-E1/E2/E3 all negative |
| 14 | `2026-08-03-change-question-skill` | n — — | no PARKED.md | — | — | **PRUNE** | Q-E1/E2/E3 all negative |
| 15 | `2026-08-03-change-rung1-sockets-on-paper` | n — — | 6 item(s) OPEN (no execution citation) | — | ERRATA later:2026-08-03-change-rung2-config-inventory | **EXTRACT-THEN-PRUNE** | Q-E2 6 open park item(s) |
| 16 | `2026-08-03-change-rung2-bridge-unification` | n — — | 4 item(s) OPEN (no execution citation) | — | — | **EXTRACT-THEN-PRUNE** | Q-E2 4 open park item(s) |
| 17 | `2026-08-03-change-rung2-config-inventory` | n — — | 6 item(s) OPEN (no execution citation) | — | later:2026-08-03-change-rung2-bridge-unification | **EXTRACT-THEN-PRUNE** | Q-E2 6 open park item(s) |
| 18 | `2026-08-03-change-rung2-engaged-criticism-switch` | Y — docs/map/INV-frozen-surfaces.md:406: (`experiments/2026-08-03-change-rung2-eng | 3 item(s) OPEN (no execution citation) | — | later:2026-08-09-change-adjudication-judge-seats-optins | **KEEP** | Q-E1 referenced |
| 19 | `2026-08-03-change-rung3-registry-in-front-of-school-population` | Y — docs/map/SEAM-schools-x-scheduler.md:38:(`experiments/2026-08-03-change-rung3- | 5 item(s) OPEN (no execution citation) | — | — | **KEEP** | Q-E1 referenced |
| 20 | `2026-08-03-change-rung3b-registry-call-site-migration` | Y — docs/map/SEAM-schools-x-scheduler.md:40:(`experiments/2026-08-03-change-rung3b | 9 item(s) OPEN (no execution citation) | — | ERRATA | **KEEP** | Q-E1 referenced |
| 21 | `2026-08-03-fix-attached-evidence-integrity` | Y — docs/map/SEAM-periphery-x-verification.md:113: `experiments/2026-08-03-fix-att | 4 item(s); executed-cite: docs/ERRATA.md | dr-set-goal/dr-diagnose skill example | ERRATA later:2026-08-12-change-skills-overhaul | **KEEP** | Q-E1 referenced |
| 22 | `2026-08-04-change-rung4-module-fingerprints` | Y — tests/test_module_fingerprints.py:4:``experiments/2026-08-04-change-rung4-modu | 7 item(s) OPEN (no execution citation) | — | ERRATA later:2026-08-04-change-rung7-authority-as-declared-policy | **KEEP** | Q-E1 referenced |
| 23 | `2026-08-04-change-rung5-dumb-alternative-backend` | Y — tests/test_rung5_alternative_backend.py:4:``experiments/2026-08-04-change-rung | 7 item(s) OPEN (no execution citation) | — | ERRATA later:2026-08-04-change-rung6-plugin-conformance | **KEEP** | Q-E1 referenced |
| 24 | `2026-08-04-change-rung6-plugin-conformance` | n — — | no PARKED.md | — | later:2026-08-04-change-rung7-authority-as-declared-policy | **PRUNE** | Q-E1/E2/E3 all negative |
| 25 | `2026-08-04-change-rung7-authority-as-declared-policy` | Y — docs/map/SEAM-adjudication-x-authority.md:142:`experiments/2026-08-04-change-r | 5 item(s) OPEN (no execution citation) | — | later:2026-08-05-fix-expired-census-readers | **KEEP** | Q-E1 referenced |
| 26 | `2026-08-04-change-spec-judgment-guardrails` | n — — | no PARKED.md | — | later:2026-08-04-change-rung6-plugin-conformance | **PRUNE** | Q-E1/E2/E3 all negative |
| 27 | `2026-08-04-change-workflow-guardrails` | n — — | no PARKED.md | — | — | **PRUNE** | Q-E1/E2/E3 all negative |
| 28 | `2026-08-05-change-budget-ceiling-at-commit` | n — — | no PARKED.md | — | later:2026-08-08-change-rung-g1-actual-diff-budget | **PRUNE** | Q-E1/E2/E3 all negative |
| 29 | `2026-08-05-change-smoke-instrument-visibility` | n — — | no PARKED.md | — | later:2026-08-05-fix-expired-census-readers | **PRUNE** | Q-E1/E2/E3 all negative |
| 30 | `2026-08-05-change-unstick-guardrails` | n — — | no PARKED.md | — | — | **PRUNE** | Q-E1/E2/E3 all negative |
| 31 | `2026-08-05-fix-continue-refusal-coverage` | Y — tests/test_continuation.py:135: """Regression (V1, tranche 2026-08-05-fix-cont | PARKED.md present, 0 enumerated items | — | later:2026-08-05-fix-resumable-reason-guard-coverage | **KEEP** | Q-E1 referenced |
| 32 | `2026-08-05-fix-continue-run-rejection` | Y — docs/map/SUB-application.md:349: 2026-08-05 (tranche `2026-08-05-fix-continue- | 1 item(s) OPEN (no execution citation) | — | later:2026-08-05-fix-continue-refusal-coverage | **KEEP** | Q-E1 referenced |
| 33 | `2026-08-05-fix-expired-census-readers` | Y — docs/map/SEAM-manifest-x-schools.md:331:`experiments/2026-08-05-fix-expired-ce | 1 item(s); executed-cite: docs/ERRATA.md | — | ERRATA later:2026-08-08-fix-module-fingerprints-double-stamp | **KEEP** | Q-E1 referenced |
| 34 | `2026-08-05-fix-loopback-fixture-daemon` | n — — | PARKED.md present, 0 enumerated items | — | ERRATA later:2026-08-05-fix-qualification-inventory-pins | **PRUNE** | Q-E1/E2/E3 all negative |
| 35 | `2026-08-05-fix-qualification-inventory-pins` | n — — | PARKED.md present, 0 enumerated items | — | later:2026-08-05-fix-continue-run-rejection | **PRUNE** | Q-E1/E2/E3 all negative |
| 36 | `2026-08-05-fix-resumable-reason-guard-coverage` | Y — docs/map/SUB-workflow.md:196: `2026-08-05-fix-resumable-reason-guard-coverage` | PARKED.md present, 0 enumerated items | — | later:2026-08-05-fix-continue-refusal-coverage | **KEEP** | Q-E1 referenced |
| 37 | `2026-08-05-fix-smoke-entry-point-reader` | n — — | 5 item(s) OPEN (no execution citation) | — | later:2026-08-05-fix-continue-run-rejection | **EXTRACT-THEN-PRUNE** | Q-E2 5 open park item(s) |
| 38 | `2026-08-05-fix-smoke-failure-reporting` | n — — | PARKED.md present, 0 enumerated items | — | later:2026-08-05-fix-qualification-inventory-pins | **PRUNE** | Q-E1/E2/E3 all negative |
| 39 | `2026-08-05-testphase-live-validation` | n — — | no PARKED.md | — | ERRATA later:2026-08-06-change-qualification-per-seat-s4 | **PRUNE** | Q-E1/E2/E3 all negative |
| 40 | `2026-08-06-change-qualification-per-seat-s4` | Y — tests/test_qualification_per_seat.py:5:Regression (experiments/2026-08-06-chan | 2 item(s); executed-cite: experiments/2026-08-08-change-pipeline-census-d1/VALIDATION.md | — | later:2026-08-07-change-seats-in-record-s5 | **KEEP** | Q-E1 referenced |
| 41 | `2026-08-06-change-seat-binding-design-s2` | n — — | no PARKED.md | — | later:2026-08-06-change-qualification-per-seat-s4 | **PRUNE** | Q-E1/E2/E3 all negative |
| 42 | `2026-08-06-change-seat-binding-wired-s3` | n — — | 1 item(s); executed-cite: experiments/2026-08-08-change-pipeline-census-d1/VALIDATION.md | — | later:2026-08-06-change-qualification-per-seat-s4 | **PRUNE** | Q-E1/E2/E3 all negative |
| 43 | `2026-08-06-change-seat-census-s1` | Y — docs/map/CON-seats.md:200:`experiments/2026-08-06-change-seat-census-s1/CENSUS | 3 item(s); executed-cite: experiments/2026-08-08-change-pipeline-census-d1/VALIDATION.md | — | later:2026-08-06-change-qualification-per-seat-s4 | **KEEP** | Q-E1 referenced |
| 44 | `2026-08-07-change-seats-in-record-s5` | Y — tests/test_seat_bindings_record.py:5:``experiments/2026-08-07-change-seats-in- | PARKED.md present, 0 enumerated items | — | later:2026-08-08-change-grounded-overlay-o2 | **KEEP** | Q-E1 referenced |
| 45 | `2026-08-08-change-grounded-overlay-o1` | n — — | no PARKED.md | — | ERRATA later:2026-08-08-change-grounded-overlay-o2 | **PRUNE** | Q-E1/E2/E3 all negative |
| 46 | `2026-08-08-change-grounded-overlay-o2` | n — — | no PARKED.md | — | ERRATA later:2026-08-09-overnight-omnibus | **PRUNE** | Q-E1/E2/E3 all negative |
| 47 | `2026-08-08-change-load-dials-d4` | n — — | no PARKED.md | — | later:2026-08-10-change-blast-radius-analysis | **PRUNE** | Q-E1/E2/E3 all negative |
| 48 | `2026-08-08-change-pipeline-census-d1` | Y — docs/map/CON-conjecture-kinds.md:19:`experiments/2026-08-08-change-pipeline-ce | 3 item(s) OPEN (no execution citation) | — | later:2026-08-08-change-grounded-overlay-o1 | **KEEP** | Q-E1 referenced |
| 49 | `2026-08-08-change-pipeline-design-d2` | Y — docs/map/CON-seats.md:203:by D2 rev 2 (`experiments/2026-08-08-change-pipeline | PARKED.md present, 0 enumerated items | — | later:2026-08-08-change-load-dials-d4 | **KEEP** | Q-E1 referenced |
| 50 | `2026-08-08-change-rung-g1-actual-diff-budget` | n — — | 1 item(s) OPEN (no execution citation) | — | later:2026-08-10-change-blast-radius-analysis | **EXTRACT-THEN-PRUNE** | Q-E2 1 open park item(s) |
| 51 | `2026-08-08-corpus-enrichment-patrol-pilot` | Y — tests/test_v6_transaction_qualification.py:1056: """P-CEPP-1 (experiments/2026 | PARKED.md present, 0 enumerated items | — | ERRATA later:2026-08-08-change-grounded-overlay-o1 | **KEEP** | Q-E1 referenced |
| 52 | `2026-08-08-fix-l1-continue-resumable-crash` | n — — | no PARKED.md | — | ERRATA later:2026-08-08-change-grounded-overlay-o1 | **PRUNE** | Q-E1/E2/E3 all negative |
| 53 | `2026-08-08-fix-module-fingerprints-double-stamp` | Y — tests/test_module_fingerprints.py:90: ``experiments/2026-08-08-fix-module-fing | no PARKED.md | — | later:2026-08-08-change-grounded-overlay-o1 | **KEEP** | Q-E1 referenced |
| 54 | `2026-08-08-live-two-seat-ab-s6` | Y — tests/test_l1_continue_resumable_crash.py:16:committed fixture ``experiments/2 | 3 item(s); executed-cite: experiments/2026-08-08-change-pipeline-census-d1/VALIDATION.md | — | ERRATA later:2026-08-08-change-grounded-overlay-o1 | **KEEP** | Q-E1 referenced |
| 55 | `2026-08-08-parked-bronze-census-env` | n — — | 6 item(s); executed-cite: experiments/2026-08-09-change-hard-question-set/VALIDATION.md | — | later:2026-08-09-change-hard-question-set | **PRUNE** | Q-E1/E2/E3 all negative |
| 56 | `2026-08-09-change-adjudication-judge-seats-optins` | n — — | PARKED.md present, 0 enumerated items | — | ERRATA later:2026-08-10-change-blast-radius-analysis | **PRUNE** | Q-E1/E2/E3 all negative |
| 57 | `2026-08-09-change-errata-sweep-and-automation` | n — — | 1 item(s) OPEN (no execution citation) | — | — | **EXTRACT-THEN-PRUNE** | Q-E2 1 open park item(s) |
| 58 | `2026-08-09-change-fix-p-cepp-1-dual-mode-wiring` | Y — docs/map/SUB-manifest.md:238: `experiments/2026-08-09-change-fix-p-cepp-1-dual | 2 item(s) OPEN (no execution citation) | — | later:2026-08-12-change-all-configs-allowed | **KEEP** | Q-E1 referenced |
| 59 | `2026-08-09-change-hard-question-set` | n — — | PARKED.md present, 0 enumerated items | — | later:2026-08-11-errata-checkpoint-audit | **PRUNE** | Q-E1/E2/E3 all negative |
| 60 | `2026-08-09-change-judge-evidence-review` | n — — | 2 item(s); executed-cite: experiments/2026-08-13-change-results-retrieval-surface/VALIDATION.md | AUDIT_BASELINES pytest-gate note | later:2026-08-09-change-adjudication-judge-seats-optins | **KEEP** | Q-E3 AUDIT_BASELINES pytest-gate note |
| 61 | `2026-08-09-change-llm-probe-apparatus` | n — — | no PARKED.md | — | ERRATA | **PRUNE** | Q-E1/E2/E3 all negative |
| 62 | `2026-08-09-cp1m-stratification-retrodiction` | n — — | no PARKED.md | — | later:2026-08-09-change-fix-p-cepp-1-dual-mode-wiring | **PRUNE** | Q-E1/E2/E3 all negative |
| 63 | `2026-08-09-overnight-omnibus` | n — — | no PARKED.md | — | ERRATA later:2026-08-08-change-grounded-overlay-o1 | **PRUNE** | Q-E1/E2/E3 all negative |
| 64 | `2026-08-09-parked-full-power-matrix` | n — — | PARKED.md present, 0 enumerated items | — | — | **PRUNE** | Q-E1/E2/E3 all negative |
| 65 | `2026-08-10-change-blast-radius-analysis` | Y — tests/test_blast_radius.py:3:Regression motivation: experiments/2026-08-10-cha | 1 item(s) OPEN (no execution citation) | dr-capture-request skill example | ERRATA later:2026-08-12-change-skills-overhaul | **KEEP** | Q-E1 referenced |
| 66 | `2026-08-11-change-docs-reorg-steps-3-4` | n — — | 1 item(s) OPEN (no execution citation) | — | — | **EXTRACT-THEN-PRUNE** | Q-E2 1 open park item(s) |
| 67 | `2026-08-11-change-qualification-messages-s4b` | Y — tools/render_form_dr1.py:85:`experiments/2026-08-11-change-qualification-messa | PARKED.md present, 0 enumerated items | — | later:2026-08-11-change-remove-token-ceiling | **KEEP** | Q-E1 referenced |
| 68 | `2026-08-11-change-remove-token-ceiling` | n — — | no PARKED.md | — | — | **PRUNE** | Q-E1/E2/E3 all negative |
| 69 | `2026-08-11-change-spec-v17-and-docs-index` | n — — | no PARKED.md | — | later:2026-08-11-change-docs-reorg-steps-3-4 | **PRUNE** | Q-E1/E2/E3 all negative |
| 70 | `2026-08-11-errata-checkpoint-audit` | n — — | no PARKED.md | — | later:2026-08-11-program-closeout | **PRUNE** | Q-E1/E2/E3 all negative |
| 71 | `2026-08-11-program-closeout` | n — — | no PARKED.md | — | later:2026-08-11-change-spec-v17-and-docs-index | **PRUNE** | Q-E1/E2/E3 all negative |
| 72 | `2026-08-11-spec-drift-measurement` | n — — | no PARKED.md | — | later:2026-08-11-change-docs-reorg-steps-3-4 | **PRUNE** | Q-E1/E2/E3 all negative |
| 73 | `2026-08-11-sweep-smoke-currency` | n — — | no PARKED.md | — | ERRATA later:2026-08-11-change-spec-v17-and-docs-index | **PRUNE** | Q-E1/E2/E3 all negative |
| 74 | `2026-08-12-change-all-configs-allowed` | Y — docs/map/SUB-manifest.md:212: (`experiments/2026-08-12-change-all-configs-allo | 4 item(s) OPEN (no execution citation) | CLAUDE.md all-configs law | ERRATA later:2026-08-13-audit | **KEEP** | Q-E1 referenced |
| 75 | `2026-08-12-change-skills-overhaul` | n — — | 2 item(s); executed-cite: experiments/2026-08-12-change-skills-parked-followups/DELIVERY.md | — | later:2026-08-12-change-skills-parked-followups | **PRUNE** | Q-E1/E2/E3 all negative |
| 76 | `2026-08-12-change-skills-parked-followups` | n — — | no PARKED.md | — | ERRATA | **PRUNE** | Q-E1/E2/E3 all negative |
| 77 | `2026-08-12-live-grounded-extension-expansion` | Y — tests/test_single_run_path.py:7:``experiments/2026-08-12-live-grounded-extensi | 2 item(s) OPEN (no execution citation) | — | ERRATA later:2026-08-13-change-lifecycle-operation-parity | **KEEP** | Q-E1 referenced |
| 78 | `2026-08-13-audit` | Y — tests/test_seats_evidence_law.py:14:(`experiments/2026-08-13-audit/goal-trace. | 13 item(s) OPEN (no execution citation) | — | later:2026-08-14-change-calculus-reconciliation-v2 | **KEEP** | Q-E1 referenced |
| 79 | `2026-08-13-change-calibration-receipt-notice` | Y — tests/test_manifest_integration.py:207: (SPEC.md Addendum 1, experiments/2026- | 1 item(s) OPEN (no execution citation) | — | later:2026-08-13-change-smoke-currency-audit | **KEEP** | Q-E1 referenced |
| 80 | `2026-08-13-change-defended-trial-wiring` | n — — | no PARKED.md | — | later:2026-08-13-change-smoke-currency-audit | **PRUNE** | Q-E1/E2/E3 all negative |
| 81 | `2026-08-13-change-lifecycle-operation-parity` | n — — | 7 item(s) OPEN (no execution citation) | CLAUDE.md ops-parity law | ERRATA later:2026-08-12-live-grounded-extension-expansion | **KEEP** | Q-E3 CLAUDE.md ops-parity law |
| 82 | `2026-08-13-change-results-retrieval-surface` | Y — tests/test_results_command.py:4:(experiments/2026-08-13-change-results-retriev | 3 item(s) OPEN (no execution citation) | — | ERRATA later:2026-08-14-change-calculus-reconciliation-v2 | **KEEP** | Q-E1 referenced |
| 83 | `2026-08-13-change-single-run-path-unification` | Y — tests/test_v6_only_cli_admission.py:380: (`experiments/2026-08-13-change-singl | 2 item(s) OPEN (no execution citation) | CLAUDE.md ops-parity law | ERRATA later:2026-08-13-defect-controller-steering-inert | **KEEP** | Q-E1 referenced |
| 84 | `2026-08-13-change-smoke-currency-audit` | n — — | 1 item(s); executed-cite: experiments/2026-08-14-change-rung1-vocabulary-groundwork/VALIDATION.md | — | later:2026-08-13-change-lifecycle-operation-parity | **PRUNE** | Q-E1/E2/E3 all negative |
| 85 | `2026-08-13-defect-controller-steering-inert` | Y — docs/map/SUB-scheduler.md:186: (`experiments/2026-08-13-defect-controller-stee | 3 item(s) OPEN (no execution citation) | — | ERRATA later:2026-08-14-change-rung1-vocabulary-groundwork | **KEEP** | Q-E1 referenced |
| 86 | `2026-08-14-change-calculus-reconciliation-v2` | Y — docs/map/INV-axiom-basis.md:16:itself (`experiments/2026-08-14-change-calculus | 3 item(s) OPEN (no execution citation) | CLAUDE.md signal-registry law | ERRATA later:2026-08-14-change-rung1-vocabulary-groundwork | **KEEP** | Q-E1 referenced |
| 87 | `2026-08-14-change-rung1-vocabulary-groundwork` | n — — | 3 item(s) OPEN (no execution citation) | — | — | **EXTRACT-THEN-PRUNE** | Q-E2 3 open park item(s) |
| 88 | `2026-08-15-change-rung1b-signal-contract` | Y — docs/map/INV-signal-contract.md:231: `experiments/2026-08-15-change-rung1b-sig | 1 item(s) OPEN (no execution citation) | — | later:2026-08-14-change-calculus-reconciliation-v2 | **KEEP** | Q-E1 referenced |
| 89 | `2026-08-15-change-rung2-premise-channel` | n — — | 1 item(s) OPEN (no execution citation) | — | — | **EXTRACT-THEN-PRUNE** | Q-E2 1 open park item(s) |
| 90 | `2026-08-15-change-rung3a-h1-successor-deletion` | n — — | 1 item(s) OPEN (no execution citation) | — | ERRATA later:2026-08-14-change-calculus-reconciliation-v2 | **EXTRACT-THEN-PRUNE** | Q-E2 1 open park item(s) |
| 91 | `2026-08-15-change-rung3c-claim-substrate` | n — — | no PARKED.md | — | — | **PRUNE** | Q-E1/E2/E3 all negative |
| 92 | `2026-08-15-change-rung3d-website-remnant` | n — — | 1 item(s); executed-cite: experiments/2026-08-16-defect-manifest-sha-doc-coupling/VERIFY.md | — | ERRATA later:2026-08-16-defect-manifest-sha-doc-coupling | **PRUNE** | Q-E1/E2/E3 all negative |
| 93 | `2026-08-16-change-configs-complete-seats-test` | Y — tests/test_all_configs_allowed_remainder.py:14:Tranche: experiments/2026-08-16 | 4 item(s) OPEN (no execution citation) | — | ERRATA | **KEEP** | Q-E1 referenced |
| 94 | `2026-08-16-change-embedder-auto-install` | Y — tests/test_results_command.py:633: """Implements R8 of tranche 2026-08-16-chan | 2 item(s); executed-cite: experiments/2026-08-16-change-configs-complete-seats-test/DELIVERY.md | — | ERRATA later:2026-08-12-live-grounded-extension-expansion | **KEEP** | Q-E1 referenced |
| 95 | `2026-08-16-change-p4-citable-evidence` | Y — docs/map/SEAM-rules-x-workflow.md:354: (`experiments/2026-08-16-change-p4-cita | no PARKED.md | — | later:2026-08-14-change-calculus-reconciliation-v2 | **KEEP** | Q-E1 referenced |
| 96 | `2026-08-16-defect-manifest-sha-doc-coupling` | Y — tests/test_single_run_path.py:664: `experiments/2026-08-16-defect-manifest-sha | 1 item(s) OPEN (no execution citation) | — | ERRATA later:2026-08-15-change-rung3d-website-remnant | **KEEP** | Q-E1 referenced |
| 97 | `2026-08-21-change-rung1b-ii-signal-consumption` | Y — docs/map/INV-signal-contract.md:147:(`experiments/2026-08-21-change-rung1b-ii- | 5 item(s); executed-cite: docs/ERRATA.md | — | ERRATA | **KEEP** | Q-E1 referenced |
| 98 | `2026-08-21-change-rung3b-frame-separation` | Y — src/deepreason/calculus/separation.py:22:(`experiments/2026-08-21-change-rung3 | 3 item(s) OPEN (no execution citation) | — | ERRATA later:2026-08-22-change-rung4-frame-assertions | **KEEP** | Q-E1 referenced |
| 99 | `2026-08-21-fix-wheel-smoke-reason-stage` | Y — docs/map/SUB-verification.md:247: `experiments/2026-08-21-fix-wheel-smoke-reas | 2 item(s) OPEN (no execution citation) | AUDIT_BASELINES Wheel smokes | ERRATA | **KEEP** | Q-E1 referenced |
| 100 | `2026-08-21-measure-reach-firing` | Y — tests/test_reflexive_discipline.py:457: (experiments/2026-08-21-measure-reach- | 3 item(s); executed-cite: experiments/2026-08-22-reach-structural-programs-fix/FIX.md | — | ERRATA later:2026-08-22-change-epoch3-second-lineage | **KEEP** | Q-E1 referenced |
| 101 | `2026-08-22-audit-scalarization` | n — — | 3 item(s) OPEN (no execution citation) | — | — | **EXTRACT-THEN-PRUNE** | Q-E2 3 open park item(s) |
| 102 | `2026-08-22-change-epoch3-second-lineage` | Y — tests/test_promotion_nomination_live.py:4:`experiments/2026-08-22-change-epoch | 6 item(s); executed-cite: docs/ERRATA.md | — | ERRATA later:2026-08-23-change-cycle-soak-instrument | **KEEP** | Q-E1 referenced |
| 103 | `2026-08-22-change-reach-p5-rulings` | Y — tests/test_reflexive_discipline.py:418: experiments/2026-08-22-change-reach-p5 | 2 item(s) OPEN (no execution citation) | — | later:2026-08-21-measure-reach-firing | **KEEP** | Q-E1 referenced |
| 104 | `2026-08-22-change-rung4-frame-assertions` | Y — docs/map/SEAM-adjudication-x-authority.md:62:`experiments/2026-08-22-change-ru | 3 item(s) OPEN (no execution citation) | — | ERRATA | **KEEP** | Q-E1 referenced |
| 105 | `2026-08-22-change-rungd-proof-debt-localization` | Y — docs/map/CON-proof-debt-and-localization.md:21: `experiments/2026-08-22-change | 1 item(s) OPEN (no execution citation) | — | ERRATA later:2026-08-23-treadle-pilot | **KEEP** | Q-E1 referenced |
| 106 | `2026-08-22-change-two-call-seat-protocol` | Y — docs/map/INV-frozen-surfaces.md:201:`experiments/2026-08-22-change-two-call-se | 2 item(s) OPEN (no execution citation) | — | ERRATA later:2026-08-23-audit-invention-inventory | **KEEP** | Q-E1 referenced |
| 107 | `2026-08-22-fix-repair-patch-transport` | Y — tests/test_v6_patch_repair_and_wire.py:707:# experiments/2026-08-22-fix-repair | 2 item(s) OPEN (no execution citation) | — | ERRATA | **KEEP** | Q-E1 referenced |
| 108 | `2026-08-22-fix-route-lease-maxtokens` | Y — tests/test_route_lease_maxtokens_tuning.py:14:Evidence: ``experiments/2026-08- | 1 item(s) OPEN (no execution citation) | — | ERRATA later:2026-08-22-live-reach-rich-run | **KEEP** | Q-E1 referenced |
| 109 | `2026-08-22-live-reach-rich-run` | Y — tests/test_reflexive_discipline.py:318: experiments/2026-08-22-live-reach-rich | 5 item(s); executed-cite: docs/ERRATA.md | — | ERRATA later:2026-08-22-change-epoch3-second-lineage | **KEEP** | Q-E1 referenced |
| 110 | `2026-08-22-measure-grounded-flip-rate` | Y — docs/map/SUB-adjudication.md:65:which is the mistake `experiments/2026-08-22-m | 3 item(s) OPEN (no execution citation) | — | later:2026-08-25-change-rung8-rent-audit-diagnostics | **KEEP** | Q-E1 referenced |
| 111 | `2026-08-22-reach-structural-programs-fix` | Y — tests/test_reflexive_discipline.py:290: """Regression (tranche experiments/202 | 3 item(s) OPEN (no execution citation) | — | ERRATA later:2026-08-22-change-reach-p5-rulings | **KEEP** | Q-E1 referenced |
| 112 | `2026-08-23-audit-invention-inventory` | n — — | no PARKED.md | — | — | **PRUNE** | Q-E1/E2/E3 all negative |
| 113 | `2026-08-23-change-cycle-soak-instrument` | n — — | 2 item(s) OPEN (no execution citation) | CLAUDE.md Live runs + AUDIT_BASELINES Cycle soak | later:2026-08-24-change-rung7-wounds-falls-succession | **KEEP** | Q-E3 CLAUDE.md Live runs + AUDIT_BASELINES Cycle soak |
| 114 | `2026-08-23-fix-reservation-bound-authority` | Y — docs/map/SEAM-llm-x-workflow.md:292: `experiments/2026-08-23-fix-reservation-b | 2 item(s) OPEN (no execution citation) | — | ERRATA | **KEEP** | Q-E1 referenced |
| 115 | `2026-08-23-treadle-pilot` | Y — tools/treadle/VENDORED.md:4:2026-08-23 for `experiments/2026-08-23-treadle-pil | 1 item(s) OPEN (no execution citation) | CLAUDE.md Third lane: treadle | — | **KEEP** | Q-E1 referenced |
| 116 | `2026-08-24-change-rung5-promotion-criteria` | n — — | 4 item(s) OPEN (no execution citation) | — | ERRATA later:2026-08-24-change-rung6-frame-render-departures | **EXTRACT-THEN-PRUNE** | Q-E2 4 open park item(s) |
| 117 | `2026-08-24-change-rung6-frame-render-departures` | Y — src/deepreason/llm/packs.py:318: (`experiments/2026-08-24-change-rung6-frame-r | 1 item(s) OPEN (no execution citation) | — | ERRATA later:2026-08-24-change-rung7-wounds-falls-succession | **KEEP** | Q-E1 referenced |
| 118 | `2026-08-24-change-rung7-wounds-falls-succession` | Y — tests/test_calculus_authority_audit.py:317: `experiments/2026-08-24-change-run | 4 item(s) OPEN (no execution citation) | — | ERRATA later:2026-08-25-change-rung8-rent-audit-diagnostics | **KEEP** | Q-E1 referenced |
| 119 | `2026-08-25-change-rung8-rent-audit-diagnostics` | Y — docs/map/INV-signal-contract.md:175:(`experiments/2026-08-25-change-rung8-rent | 4 item(s) OPEN (no execution citation) | — | — | **KEEP** | Q-E1 referenced |
| 120 | `autonomous_inquiry_preflight_2026-07-16` | n — — | no PARKED.md | — | — | **PRUNE** | Q-E1/E2/E3 all negative |
| 121 | `bronze_feedback_v1_superseded_2026-07-14` | n — — | no PARKED.md | — | later:2026-08-04-change-rung4-module-fingerprints | **PRUNE** | Q-E1/E2/E3 all negative |
| 122 | `bronze_flat_2026-07-13` | Y — scripts/bronze_counterfactuals.py:30: "deepseek-v4-pro": Path("experiments/bro | no PARKED.md | — | ERRATA later:2026-08-01-change-prose-can-refute | **KEEP** | Q-E1 referenced |
| 123 | `bronze_pilot_2026-07-14` | Y — tests/test_migration_compat.py:35: "experiments/bronze_pilot_2026-07-14", | no PARKED.md | — | later:2026-08-06-change-qualification-per-seat-s4 | **KEEP** | Q-E1 referenced |
| 124 | `bronze_repertoire_v2_2026-07-14` | n — — | no PARKED.md | — | later:2026-08-06-change-qualification-per-seat-s4 | **PRUNE** | Q-E1/E2/E3 all negative |
| 125 | `court_calibration_items` | Y — scripts/court_calibration_run.py:24:PAIRS = REPO / "experiments/court_calibrat | no PARKED.md | — | later:experiments/court_calibration_v1_prereg.yaml | **KEEP** | Q-E1 referenced |
| 126 | `court_calibration_run` | Y — scripts/court_calibration_run.py:8:Checkpoint: experiments/court_calibration_r | no PARKED.md | — | later:results | **KEEP** | Q-E1 referenced |
| 127 | `court_cross_run` | Y — scripts/experiment_e_placement.py:44: "dsflash": REPO / "experiments/court_cro | no PARKED.md | — | later:experiments/bronze_court_cross_v1_prereg.yaml | **KEEP** | Q-E1 referenced |
| 128 | `critic_spec_items` | Y — scripts/critic_spec_corpus.py:17:Outputs (experiments/critic_spec_items/): | no PARKED.md | — | later:experiments/defended_trial_v1_prereg.yaml | **KEEP** | Q-E1 referenced |
| 129 | `critic_spec_run` | Y — scripts/critic_spec_corpus.py:20:Ledger: experiments/critic_spec_run/token_usa | no PARKED.md | — | later:results | **KEEP** | Q-E1 referenced |
| 130 | `defended_trial_run` | Y — scripts/defended_trial_score.py:7:(experiments/defended_trial_run/), computes  | no PARKED.md | — | later:results | **KEEP** | Q-E1 referenced |
| 131 | `e02_t1_items` | Y — scripts/circularity_check.py:81:UNKNOWN = REPO / "experiments/e02_t1_items/unk | no PARKED.md | — | later:2026-08-09-change-judge-evidence-review | **KEEP** | Q-E1 referenced |
| 132 | `e02_t2_items` | Y — scripts/circularity_check.py:82:CLEAN = REPO / "experiments/e02_t2_items/clean | no PARKED.md | — | later:experiments/e02_t3_judge_zoo_prereg.yaml | **KEEP** | Q-E1 referenced |
| 133 | `e02_t2b_run` | Y — scripts/e02_t2b_readjudicate.py:30:Budget: 120,000 tokens (UsageLedger, experi | no PARKED.md | — | — | **KEEP** | Q-E1 referenced |
| 134 | `e02_t3_run` | Y — scripts/circularity_check.py:58: experiments/e02_t3_run/judgments.jsonl) by >= | no PARKED.md | — | later:experiments/e02_t3_run_live.out | **KEEP** | Q-E1 referenced |
| 135 | `e31_demo_benchmark` | Y — scripts/e31_benchmark/build_demo.py:36:DEFAULT_OUT = _REPO_ROOT / "experiments | no PARKED.md | — | — | **KEEP** | Q-E1 referenced |
| 136 | `gemma4_dna_unattended_2026-07-12` | Y — tests/test_migration_compat.py:29: "experiments/gemma4_dna_unattended_2026-07- | no PARKED.md | — | later:2026-08-06-change-qualification-per-seat-s4 | **KEEP** | Q-E1 referenced |
| 137 | `gemma4_dna_unattended_3_2026-07-12` | Y — scripts/e01_run.py:29: "experiments/gemma4_dna_unattended_3_2026-07-12", | no PARKED.md | — | later:2026-08-06-change-qualification-per-seat-s4 | **KEEP** | Q-E1 referenced |
| 138 | `glm_judge_2026-07-14` | Y — scripts/glm_theory_census.py:18:ROOT = Path("experiments/glm_judge_2026-07-14" | no PARKED.md | — | later:2026-08-06-change-qualification-per-seat-s4 | **KEEP** | Q-E1 referenced |
| 139 | `jolt_architecture_2026-07-16` | Y — tests/fixtures/jolt_derived_acceptance.json:3: "source_root": "experiments/jol | no PARKED.md | — | later:2026-08-01-fix-decomposition-merge-pairing | **KEEP** | Q-E1 referenced |
| 140 | `live_20b_schema_2026-07-31` | n — — | no PARKED.md | — | — | **PRUNE** | Q-E1/E2/E3 all negative |
| 141 | `live_coin_canonicity_2026-07-31` | n — — | no PARKED.md | — | later:2026-08-06-change-qualification-per-seat-s4 | **PRUNE** | Q-E1/E2/E3 all negative |
| 142 | `live_coin_thinkingoff_2026-07-31` | n — — | no PARKED.md | — | later:2026-07-31-change-critic-seats-and-thinking | **PRUNE** | Q-E1/E2/E3 all negative |
| 143 | `live_compare_2026-07-28` | n — — | no PARKED.md | — | later:2026-08-01-fix-adjudication-blindness | **PRUNE** | Q-E1/E2/E3 all negative |
| 144 | `live_engaged_2026-07-27` | Y — tests/test_adjudication_blindness.py:55: "experiments/live_engaged_2026-07-27/ | no PARKED.md | — | later:2026-08-01-fix-adjudication-blindness | **KEEP** | Q-E1 referenced |
| 145 | `live_gemma4_schema_2026-07-31` | n — — | no PARKED.md | — | — | **PRUNE** | Q-E1/E2/E3 all negative |
| 146 | `live_jolt_2026-07-31` | Y — docs/map/SEAM-adjudication-x-rules.md:237:`check: grep -q "harness._oracle_pen | no PARKED.md | — | later:2026-08-01-change-prose-can-refute | **KEEP** | Q-E1 referenced |
| 147 | `live_research_2026-07-29` | Y — docs/map/SEAM-schools-x-scratch.md:96:`check: python -c "import json,pathlib,c | no PARKED.md | CLAUDE.md Environment (snapshot_loop.sh) | ERRATA later:2026-07-30-change-amendment-epochs | **KEEP** | Q-E1 referenced |
| 148 | `live_tri_2026-07-27` | Y — tests/test_adjudication_blindness.py:53:_BLIND_ROOT = Path("experiments/live_t | no PARKED.md | AUDIT_BASELINES root_sweep (historical) | later:2026-08-01-fix-adjudication-blindness | **KEEP** | Q-E1 referenced |
| 149 | `live_turmite_2026-07-31` | n — — | no PARKED.md | — | later:2026-08-08-change-pipeline-census-d1 | **PRUNE** | Q-E1/E2/E3 all negative |
| 150 | `results` | Y — tests/test_judge_battery.py:72: (tmp_path / "experiments/results/judge_battery | no PARKED.md | — | ERRATA later:2026-07-31-change-critic-seats-and-thinking | **KEEP** | Q-E1 referenced |
| 151 | `schema_comparator_run` | Y — scripts/schema_comparator_run.py:7:experiments/schema_comparator_run/<critic>. | no PARKED.md | — | — | **KEEP** | Q-E1 referenced |
| 152 | `tier_v_checkers` | n — — | no PARKED.md | — | later:2026-08-09-change-hard-question-set | **PRUNE** | Q-E1/E2/E3 all negative |
