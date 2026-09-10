# Goal: the solo-model criticism-authority road either reaches a run or stops being declared

Class: defect

Observed: `ARGUMENTATIVE_AUTHORITY="single_family_trial"` is a declared value of
a closed `Config` Literal and a member of `rules/crit.py::_TRIAL_MODES`, and the
cross-school judge substitute it selects (`llm/firewall.py::
require_cross_school_judge_ensemble`, `LLMAdapter.school_judge_bindings`) has no
production caller and no admissible manifest, so no launchable one-model
configuration can complete an argumentative trial through it. Evidence, all
committed and read-only:
`experiments/2026-09-09-change-d8-criticism-experiment/SPEC.md` M6 (three
independent gates, each cited to a committed check or map Trap) and its PARKED.md
P1; `docs/map/CON-schools.md` Traps
("`ARGUMENTATIVE_AUTHORITY=single_family_trial` cannot complete a trial";
"Mistaking `require_cross_school_judge_ensemble` for the live guarantee") and the
check at `docs/map/CON-schools.md:151` which PINS the isolation;
`docs/map/SEAM-manifest-x-schools.md` ("There is no manifest surface for a judge
school, so the cross-school judge ensemble is unreachable"). The documented
guarantee it contradicts is the operator's design law of 2026-08-09, ledgered in
CLAUDE.md: "A solo run with everything on should be an option. That's what solo
run option should always have been," read operationally as "designs gated on
multi-family judge ensembles need a solo-compatible road."

Success criterion (machine-decidable) — ONE of the two roads, chosen by the
operator at the FIX.md stop; nothing in between:

  Road (a) WIRE IT
      python -m pytest tests/test_solo_criticism_authority.py -q
      expected: passing tests proving (i) a one-model configuration with
      `ARGUMENTATIVE_AUTHORITY=single_family_trial` and a judge-school binding
      dispatches a trial through the cross-school judge substitute and mints an
      argumentative warrant that becomes an attack edge, and (ii) the typed
      disclosure for the switched gate is on the record; both mutation-proven.
      python tools/docs_verify.py
      expected: 0 failed, with the two `CON-schools.md` checks that pin the
      current isolation rewritten to pin the new behaviour.
      python -m pytest tests/ -q -n 4
      expected: 0 failed.

  Road (b) RETIRE IT
      python -c "import typing; from deepreason.config import Config; assert 'single_family_trial' not in typing.get_args(Config.model_fields['ARGUMENTATIVE_AUTHORITY'].annotation)"
      expected: exit 0, and `single_family_trial` absent from
      `rules/crit.py::_TRIAL_MODES` and the adapter's dead parameter deleted.
      grep -q "single_family_trial" docs/ERRATA.md
      expected: exit 0 — an erratum recording that the 2026-08-09 law's solo road
      is served instead by a cross-family judge ensemble on a
      generation-seat-uniform configuration.
      python tools/docs_verify.py ; python -m pytest tests/ -q -n 4
      expected: 0 failed each.

In scope: `src/deepreason/llm/adapter.py`, `src/deepreason/run_manifest.py`
(frozen surface 4 — grant required), `src/deepreason/llm/firewall.py`
(frozen-adjacent `route_fingerprint`), plus `tests/` and `docs/map/`.

NOT in scope: `src/deepreason/informal/trial.py`'s trial mechanics themselves,
`rules/crit.py` beyond the `_TRIAL_MODES` membership under road (b),
`capabilities/state.py`, `harness.py`, `invariants.py`, `verification/`,
`qualification.py`. The nearest tempting neighbour explicitly refused: widening
`CriticismPolicyV1.authority`'s `defended_trial` road, or making judge seats
school-routable in general. Anything else found is PARKED.

Map ids resolved (map preflight, read in this order): `DR-INV-frozen-surfaces`
(surface 4 and the frozen-adjacent `route_fingerprint`), then the seam
`DR-SEAM-manifest-x-schools`, then `DR-CON-schools`, `DR-SUB-manifest`,
`DR-SUB-llm`, `DR-CON-warrants-and-attacks`, `DR-CON-criticism-source`,
`DR-CON-authority`.

Budget: <=150 changed lines, 1 commit for the code, <n> hours; a mandatory STOP
at FIX.md for the frozen-surface-4 grant and the operator's choice of road.

Stop conditions inherited from orchestrator: yes
