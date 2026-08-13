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
| D1 | dead | __init__.py | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-__init__-symbols.txt, proof/dead-__init__-candidates.txt | baseline |
| D2 | dead | __main__.py | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-__main__-symbols.txt, proof/dead-__main__-candidates.txt | baseline |
| D3 | dead | adjudication | pass | 1 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-adjudication-symbols.txt, proof/dead-adjudication-candidates.txt | parked |
| D4 | dead | admission | pass | 10 candidate-dead, 2 dynamic-ref (see dead.md) | proof/dead-admission-symbols.txt, proof/dead-admission-candidates.txt | parked |
| D5 | dead | amendment | pass | 17 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-amendment-symbols.txt, proof/dead-amendment-candidates.txt | parked |
| D6 | dead | application | pass | 46 candidate-dead, 5 dynamic-ref (see dead.md) | proof/dead-application-symbols.txt, proof/dead-application-candidates.txt | parked |
| D7 | dead | assets | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-assets-symbols.txt, proof/dead-assets-candidates.txt | baseline |
| D8 | dead | authority.py | pass | 5 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-authority-symbols.txt, proof/dead-authority-candidates.txt | parked |
| D9 | dead | brain | pass | 21 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-brain-symbols.txt, proof/dead-brain-candidates.txt | parked |
| D10 | dead | bridge | pass | 77 candidate-dead, 22 dynamic-ref (see dead.md) | proof/dead-bridge-symbols.txt, proof/dead-bridge-candidates.txt | parked |
| D11 | dead | browser.py | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-browser-symbols.txt, proof/dead-browser-candidates.txt | baseline |
| D12 | dead | canonical.py | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-canonical-symbols.txt, proof/dead-canonical-candidates.txt | baseline |
| D13 | dead | capabilities | pass | 7 candidate-dead, 5 dynamic-ref (see dead.md) | proof/dead-capabilities-symbols.txt, proof/dead-capabilities-candidates.txt | parked |
| D14 | dead | capture | pass | 5 candidate-dead, 1 dynamic-ref (see dead.md) | proof/dead-capture-symbols.txt, proof/dead-capture-candidates.txt | parked |
| D15 | dead | cli | pass | 69 candidate-dead, 1 dynamic-ref (see dead.md) | proof/dead-cli-symbols.txt, proof/dead-cli-candidates.txt | parked |
| D16 | dead | compat_eval.py | pass | 9 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-compat_eval-symbols.txt, proof/dead-compat_eval-candidates.txt | parked |
| D17 | dead | config.py | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-config-symbols.txt, proof/dead-config-candidates.txt | baseline |
| D18 | dead | conjecture_events.py | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-conjecture_events-symbols.txt, proof/dead-conjecture_events-candidates.txt | baseline |
| D19 | dead | conjecture_turn.py | pass | 1 candidate-dead, 1 dynamic-ref (see dead.md) | proof/dead-conjecture_turn-symbols.txt, proof/dead-conjecture_turn-candidates.txt | parked |
| D20 | dead | control_events.py | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-control_events-symbols.txt, proof/dead-control_events-candidates.txt | baseline |
| D21 | dead | controller.py | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-controller-symbols.txt, proof/dead-controller-candidates.txt | baseline |
| D22 | dead | easy.py | pass | 10 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-easy-symbols.txt, proof/dead-easy-candidates.txt | parked |
| D23 | dead | error_catalog.py | pass | 1 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-error_catalog-symbols.txt, proof/dead-error_catalog-candidates.txt | parked |
| D24 | dead | evidence | pass | 8 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-evidence-symbols.txt, proof/dead-evidence-candidates.txt | parked |
| D25 | dead | experiments | pass | 46 candidate-dead, 8 dynamic-ref (see dead.md) | proof/dead-experiments-symbols.txt, proof/dead-experiments-candidates.txt | parked |
| D26 | dead | findings.py | pass | 1 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-findings-symbols.txt, proof/dead-findings-candidates.txt | parked |
| D27 | dead | frozen.py | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-frozen-symbols.txt, proof/dead-frozen-candidates.txt | baseline |
| D28 | dead | harness.py | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-harness-symbols.txt, proof/dead-harness-candidates.txt | baseline |
| D29 | dead | imports.py | pass | 6 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-imports-symbols.txt, proof/dead-imports-candidates.txt | parked |
| D30 | dead | indexes.py | pass | 2 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-indexes-symbols.txt, proof/dead-indexes-candidates.txt | parked |
| D31 | dead | informal | pass | 16 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-informal-symbols.txt, proof/dead-informal-candidates.txt | parked |
| D32 | dead | intake_form.py | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-intake_form-symbols.txt, proof/dead-intake_form-candidates.txt | baseline |
| D33 | dead | invariants.py | pass | 7 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-invariants-symbols.txt, proof/dead-invariants-candidates.txt | parked |
| D34 | dead | jolts.py | pass | 10 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-jolts-symbols.txt, proof/dead-jolts-candidates.txt | parked |
| D35 | dead | llm | pass | 89 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-llm-symbols.txt, proof/dead-llm-candidates.txt | parked |
| D36 | dead | locking.py | pass | 6 candidate-dead, 2 dynamic-ref (see dead.md) | proof/dead-locking-symbols.txt, proof/dead-locking-candidates.txt | parked |
| D37 | dead | log | pass | 1 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-log-symbols.txt, proof/dead-log-candidates.txt | parked |
| D38 | dead | loop.py | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-loop-symbols.txt, proof/dead-loop-candidates.txt | baseline |
| D39 | dead | manifest.py | pass | 6 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-manifest-symbols.txt, proof/dead-manifest-candidates.txt | parked |
| D40 | dead | mcp_help.py | pass | 2 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-mcp_help-symbols.txt, proof/dead-mcp_help-candidates.txt | parked |
| D41 | dead | mcp_registration.py | pass | 0 candidate-dead, 1 dynamic-ref (see dead.md) | proof/dead-mcp_registration-symbols.txt, proof/dead-mcp_registration-candidates.txt | baseline |
| D42 | dead | mcp_scratch_bridge.py | pass | 20 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-mcp_scratch_bridge-symbols.txt, proof/dead-mcp_scratch_bridge-candidates.txt | parked |
| D43 | dead | mcp_server.py | pass | 9 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-mcp_server-symbols.txt, proof/dead-mcp_server-candidates.txt | parked |
| D44 | dead | measures | pass | 7 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-measures-symbols.txt, proof/dead-measures-candidates.txt | parked |
| D45 | dead | module_events.py | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-module_events-symbols.txt, proof/dead-module_events-candidates.txt | baseline |
| D46 | dead | ontology | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-ontology-symbols.txt, proof/dead-ontology-candidates.txt | baseline |
| D47 | dead | ops.py | pass | 1 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-ops-symbols.txt, proof/dead-ops-candidates.txt | parked |
| D48 | dead | oracle.py | pass | 9 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-oracle-symbols.txt, proof/dead-oracle-candidates.txt | parked |
| D49 | dead | oracle_sandbox.py | pass | 5 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-oracle_sandbox-symbols.txt, proof/dead-oracle_sandbox-candidates.txt | parked |
| D50 | dead | packs | pass | 2 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-packs-symbols.txt, proof/dead-packs-candidates.txt | parked |
| D51 | dead | preparation.py | pass | 6 candidate-dead, 2 dynamic-ref (see dead.md) | proof/dead-preparation-symbols.txt, proof/dead-preparation-candidates.txt | parked |
| D52 | dead | programs.py | pass | 15 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-programs-symbols.txt, proof/dead-programs-candidates.txt | parked |
| D53 | dead | provider_profile.py | pass | 3 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-provider_profile-symbols.txt, proof/dead-provider_profile-candidates.txt | parked |
| D54 | dead | qualification.py | pass | 6 candidate-dead, 2 dynamic-ref (see dead.md) | proof/dead-qualification-symbols.txt, proof/dead-qualification-candidates.txt | parked |
| D55 | dead | readiness.py | pass | 1 candidate-dead, 2 dynamic-ref (see dead.md) | proof/dead-readiness-symbols.txt, proof/dead-readiness-candidates.txt | parked |
| D56 | dead | referee.py | pass | 2 candidate-dead, 2 dynamic-ref (see dead.md) | proof/dead-referee-symbols.txt, proof/dead-referee-candidates.txt | parked |
| D57 | dead | report.py | pass | 4 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-report-symbols.txt, proof/dead-report-candidates.txt | parked |
| D58 | dead | research | pass | 4 candidate-dead, 2 dynamic-ref (see dead.md) | proof/dead-research-symbols.txt, proof/dead-research-candidates.txt | parked |
| D59 | dead | rules | pass | 35 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-rules-symbols.txt, proof/dead-rules-candidates.txt | parked |
| D60 | dead | run_manifest.py | pass | 28 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-run_manifest-symbols.txt, proof/dead-run_manifest-candidates.txt | parked |
| D61 | dead | runtime | pass | 29 candidate-dead, 1 dynamic-ref (see dead.md) | proof/dead-runtime-symbols.txt, proof/dead-runtime-candidates.txt | parked |
| D62 | dead | scheduler | pass | 1 candidate-dead, 1 dynamic-ref (see dead.md) | proof/dead-scheduler-symbols.txt, proof/dead-scheduler-candidates.txt | parked |
| D63 | dead | scratch | pass | 17 candidate-dead, 6 dynamic-ref (see dead.md) | proof/dead-scratch-symbols.txt, proof/dead-scratch-candidates.txt | parked |
| D64 | dead | seat_bindings.py | pass | 1 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-seat_bindings-symbols.txt, proof/dead-seat_bindings-candidates.txt | parked |
| D65 | dead | seat_events.py | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-seat_events-symbols.txt, proof/dead-seat_events-candidates.txt | baseline |
| D66 | dead | shallow.py | pass | 2 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-shallow-symbols.txt, proof/dead-shallow-candidates.txt | parked |
| D67 | dead | shallow_fitness.py | pass | 2 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-shallow_fitness-symbols.txt, proof/dead-shallow_fitness-candidates.txt | parked |
| D68 | dead | signals.py | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-signals-symbols.txt, proof/dead-signals-candidates.txt | baseline |
| D69 | dead | signals_read.py | pass | 2 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-signals_read-symbols.txt, proof/dead-signals_read-candidates.txt | parked |
| D70 | dead | simulation | pass | 5 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-simulation-symbols.txt, proof/dead-simulation-candidates.txt | parked |
| D71 | dead | skills | pass | 15 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-skills-symbols.txt, proof/dead-skills-candidates.txt | parked |
| D72 | dead | status_display.py | pass | 1 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-status_display-symbols.txt, proof/dead-status_display-candidates.txt | parked |
| D73 | dead | storage | pass | 4 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-storage-symbols.txt, proof/dead-storage-candidates.txt | parked |
| D74 | dead | ui | pass | 1 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-ui-symbols.txt, proof/dead-ui-candidates.txt | parked |
| D75 | dead | unification | pass | 0 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-unification-symbols.txt, proof/dead-unification-candidates.txt | baseline |
| D76 | dead | v6_policy.py | pass | 1 candidate-dead, 2 dynamic-ref (see dead.md) | proof/dead-v6_policy-symbols.txt, proof/dead-v6_policy-candidates.txt | parked |
| D77 | dead | verification | pass | 18 candidate-dead, 3 dynamic-ref (see dead.md) | proof/dead-verification-symbols.txt, proof/dead-verification-candidates.txt | parked |
| D78 | dead | views | pass | 25 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-views-symbols.txt, proof/dead-views-candidates.txt | parked |
| D79 | dead | webapp.py | pass | 5 candidate-dead, 1 dynamic-ref (see dead.md) | proof/dead-webapp-symbols.txt, proof/dead-webapp-candidates.txt | parked |
| D80 | dead | workflow | pass | 38 candidate-dead, 5 dynamic-ref (see dead.md) | proof/dead-workflow-symbols.txt, proof/dead-workflow-candidates.txt | parked |
| D81 | dead | workflows | pass | 9 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-workflows-symbols.txt, proof/dead-workflows-candidates.txt | parked |
| D82 | dead | workloads | pass | 24 candidate-dead, 0 dynamic-ref (see dead.md) | proof/dead-workloads-symbols.txt, proof/dead-workloads-candidates.txt | parked |
| D83 | dead | dr-audit-dead methodology (outside-file-only scan misses same-file callers) | pass | 821/836 candidate-dead rows are same-file-only false positives; see dead.md Methodology finding | dead.md | parked |
| DD1 | docs-drift | docs_verify (default, full) | pass | baseline | proof/docs-full.txt | baseline |
| DD2 | docs-drift | docs_verify --audit | pass | baseline | proof/docs-audit.txt | baseline |
| DD3 | docs-drift | docs_verify --links | pass | baseline | proof/docs-links.txt | baseline |
| DD4 | docs-drift | docs_verify --stale | pass | baseline | proof/docs-stale.txt | baseline |
| DD5 | docs-drift | docs/ADMISSION_SPEC.md Status line | pass | baseline | proof/docs-unchecked-claims.txt | baseline |
| DD6 | docs-drift | docs/MINI_PLAN.md Status line | pass | drifted | proof/docs-unchecked-claims.txt | parked |
| DD7 | docs-drift | docs/SMALL_MODEL_COMPATIBILITY.md header claim | pass | drifted | proof/docs-unchecked-claims.txt | parked |
| DD8 | docs-drift | docs/RESEARCH_BACKEND.md Status line | pass | drifted (already errata E20) | proof/docs-unchecked-claims.txt | baseline |
| DD9 | docs-drift | docs/EXPERIMENT_PROGRAM_2026-07.md claim | pass | not mechanically checkable | proof/docs-unchecked-claims.txt | noted |
| SD1 | spec-drift | ContextRequest (spec) vs ContextRequestV1 (code) | pass | spec-orphan | proof/spec-orphan-detail.txt | parked |
| SD2 | spec-drift | R_t (spec notation) | pass | covered | proof/spec-orphan-detail.txt | baseline |
| SD3 | spec-drift | codec:json | pass | spec-orphan | proof/spec-orphan-detail.txt | parked |
| SD4 | spec-drift | deepreason.config.load | pass | covered | proof/spec-orphan-detail.txt | baseline |
| SD5 | spec-drift | novel-case | pass | spec-orphan | proof/spec-orphan-detail.txt | parked |
| SD6 | spec-drift | positions.accepted | pass | covered | proof/spec-orphan-detail.txt | baseline |
| SD7 | spec-drift | workflow-resume-decision.v1 (3-way spelling drift) | pass | spec-orphan | proof/spec-orphan-detail.txt | parked |
| SD8 | spec-drift | CLI flags (34/75 spec-silent) | pass | spec-silent, batched | proof/tree-cli-flags.txt | parked |
| SD9 | spec-drift | config fields (51/75 spec-silent) | pass | spec-silent, batched | proof/tree-config-fields.txt | parked |
| SD10 | spec-drift | typed strings: manifest-generation V3-V6 (28/118) | pass | spec-silent, batched | proof/tree-typed-strings.txt | parked |
| SD11 | spec-drift | typed strings: preparation/managed-run (20/118) | pass | spec-silent, batched | proof/tree-typed-strings.txt | parked |
| SD12 | spec-drift | typed strings: run-input/manifest-file (11/118) | pass | spec-silent, batched | proof/tree-typed-strings.txt | parked |
| SD13 | spec-drift | typed strings: routing/bridge presentation (9/118) | pass | spec-silent, batched | proof/tree-typed-strings.txt | parked |
| SD14 | spec-drift | typed strings: credential/path-safety (9/118) | pass | spec-silent, batched | proof/tree-typed-strings.txt | parked |
| SD15 | spec-drift | typed strings: judge-family/seats (6/118) | pass | spec-silent, batched | proof/tree-typed-strings.txt | parked |
| SD16 | spec-drift | typed strings: remainder (35/118) | pass | spec-silent, batched | proof/tree-typed-strings.txt | parked |
| L1 | goal-trace | Formalism is an option, never an obligation | pass | enforced | proof/goal-L1.txt | baseline |
| L2 | goal-trace | Seats change GENERATED, never EVIDENCE | pass | partially-enforced | proof/goal-L2.txt | parked |
| L3 | goal-trace | A solo run with everything on must be an option | pass | enforced | proof/goal-L3.txt | baseline |
| L4 | goal-trace | Tokens are cheap; the agent is not | pass | process-law | proof/goal-L4.txt | baseline |
| L5 | goal-trace | All configurations should be allowed | pass | partially-enforced | proof/goal-L5.txt | parked |
