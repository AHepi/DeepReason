# Dimension: goal trace (operator design laws vs enforcement)

Census: `proof/goal-laws.txt`, re-derived from CLAUDE.md §"Operator design
laws". A law counts as ENFORCED only when a mechanism would visibly fail if
the law were violated. Prose restating a law enforces nothing.

**The law count moved 5 → 8 since 2026-08-13.** L6, L7 and L8 are new and
have never been traced before.

| id | law | verdict | mechanism | test | proof | disposition |
|---|---|---|---|---|---|---|
| L1 | Formalism is an option, never an obligation | enforced | `formally_backed` (`rules/warrants.py:61`), consumed by `oracle.py`, `informal/trial.py:920`, `rules/relatedness.py`, `programs.py` | `tests/test_oracle.py`, `tests/test_prose_refutation_boundaries.py` | proof/goal-L1.txt | baseline |
| L2 | Seats change GENERATED, never EVIDENCE | **enforced** (was `partially-enforced`) | `seat_bindings.py` + `seat_events.py`, `harness.py`, `scheduler/scheduler.py` | `tests/test_seats_evidence_law.py` — written FOR this law and citing `experiments/2026-08-13-audit/goal-trace.md` row L2 in its docstring | proof/goal-L2.txt | **delta — improved** |
| L3 | A solo run with everything on must be an option | enforced | `is_single_model_run` (`llm/firewall.py:341`), `adapter.py:675`, `informal/trial.py:904`, `run_manifest.py` single-model seeding | `tests/test_judge_ensemble_boundary.py`, `tests/test_run_manifest.py`, `tests/test_calculus_succession_trial.py` | proof/goal-L3.txt | baseline |
| L4 | Tokens are cheap; the agent is not | process-law | n/a — governs agent working style | n/a | proof/goal-L4.txt | baseline (enforced by CLAUDE.md §Build and test and the `dr-drive-harness` skill) |
| L5 | All configurations should be allowed | **enforced** (was `partially-enforced`) | `CompileNoticeV1` (`run_manifest.py:1191`) + the `compile_notices` sink | `tests/test_all_configs_allowed_remainder.py` — the named remainder test the prior audit's park asked for | proof/goal-L5.txt | **delta — improved** |
| L6 | Operations are available to every configuration | enforced | ONE RUN PATH: `TextRunApplicationService.start_manifest_run` (`application/text_runs.py:752`), the single CLI caller at `cli/main.py:3006`, shared `terminalize_text_run` | `tests/test_lifecycle_operation_parity.py`, `tests/test_single_run_path.py` | proof/goal-L6.txt | **NEW law — baseline** |
| L7 | Old runs owe the future nothing | enforced | `UnsupportedRunManifestVersionError` (`run_manifest.py:100,4221`) is the typed refusal that MAKES old roots unreadable-by-design; the SCOPE BOUNDARY half (within-version replay) is pinned by the `verify_root` test family | `verify_root` asserted across 12+ test files incl. `tests/test_replay_reasoning.py`, `tests/test_bridge_events_replay.py` | proof/goal-L7.txt | **NEW law — baseline, with one finding (GT1)** |
| L8 | The signal registry is a CONTRACT | enforced | `signals.py` (registry + staleness), `allocation.py:144 open_loop_signals` (the disclose-never-die notice), `controller.py:132/204` seat-INSTANCE keying, `docs/map/INV-signal-contract.md` | `tests/test_signal_contract.py`, `tests/test_allocation_signal_consumption.py` | proof/goal-L8.txt | **NEW law — baseline** |

## Findings

**GT1 — a skill contradicts a standing operator ruling (L7).** The operator
retired the root sweep as an instrument on 2026-08-22, and CLAUDE.md §Build
and test states that no tranche, gate, audit or grant may require it. Two
skills still instruct the reader to run it:

- `.claude/skills/dr-drive-harness/SKILL.md:139` — names it, with the full
  gate, under "Instruments that prove you broke nothing:
  `python tools/root_sweep.py` — no committed root's verdict may move".
- `.claude/skills/dr-spec-change/SKILL.md:79` — treats it as a live baseline
  instrument.

`dr-audit-broken` and `docs/AUDIT_BASELINES.md` both carry the retirement
correctly, so the contradiction is confined to those two files. Consequence
is wasted agent time and a re-imposed obligation the operator abolished, not
a wrong verdict anywhere. Parked as **P1**.

## Laws added since the last audit

L6 (2026-08-13), L7 (2026-08-14), L8 (2026-08-14) — all three traced here
for the first time, all three `enforced`.

**Count line: 8 laws, 7 enforced, 1 process-law, 0 unenforced,
0 partially-enforced. 2 improved since 2026-08-13 (L2, L5). 1 finding parked.**
