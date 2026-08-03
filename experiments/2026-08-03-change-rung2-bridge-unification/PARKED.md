# Parked — noticed or deferred during this tranche, deliberately not done

- **R1's literal instruction ("change BridgeConfig's defaults") itself,
  as a future possibility.** This tranche did NOT flip `BridgeConfig`'s
  shared class-level defaults (`mode="legacy_thesis"`,
  `max_schema_repair_attempts=2`, `max_grounding_repair_attempts=4`,
  `output_section_limit=32`) to match the engaged preset's values —
  Amendment 1 records the operator's explicit choice not to, because
  those defaults are load-bearing for every bare `Config()` construction
  (a pinned test, `test_safe_defaults_are_bounded_and_features_remain_
  opt_in`, and the `deepreason config compile` CLI path). If the
  operator later decides the SHARED default really should change (e.g.
  because `legacy_thesis` is judged genuinely obsolete rather than a
  deliberate safe fallback), that is a separate, explicit future
  decision — not something this tranche implements or recommends.

- **Rung 2's remaining inventory candidates, unchanged from tranche 1's
  own PARKED.md**: Group C's env-var-sourced switches
  (`DEEPREASON_SIMULATION_RUNNER`, `DEEPREASON_RESEARCH_ALLOWLIST`/
  `_MAX_REQUESTS`/`_MAX_SOURCES`, `DEEPREASON_CONFIG_REFEREE`) and Group
  D's `STANCE_LIBRARY` (content, not a switch). Neither addressed by
  this tranche; still the operator's call for any future tranche.

- **`docs/map/CON-authority.md`'s "Adjacent, not authority" section
  placement.** This claim about `engaged_bridge_source()` lives in a
  document titled "Authority — who may change a Status," which it is
  not about. It is placed there because `CON-authority.md` is the only
  established `Owns:` home for `v6_policy.py`/`preparation.py`
  (from tranche 2), and creating a new document for one small hygiene
  fix would be disproportionate. If rung 2 (or a later rung) adds a
  THIRD unrelated claim to these same two files, that would be a signal
  worth acting on — a dedicated "preset construction" document might
  earn its keep at that point. Not created here; noted for whoever
  next finds themselves in the same position.

- **No structural guard against a future `BridgeConfig`-bypassing
  regression.** Nothing prevents a future edit to `engaged_bridge_
  source()` from reverting to a bare literal dict again — the two tests
  (the pre-existing exact-dict check and this tranche's new
  built-through-`BridgeConfig` check) would catch VALUE drift but a
  reviewer could still hand-edit the function back to a literal without
  either test failing, as long as the literal's values still matched.
  No stronger enforcement (e.g. an AST-level check forbidding a bare
  dict literal as the return statement) was designed or requested;
  noted as a possible future hardening, not built here.
