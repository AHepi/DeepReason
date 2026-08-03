# Parked — noticed or deferred during this tranche, deliberately not done

- **Tranche 2 (the `engaged_criticism_policy` switch itself)** — R5-R8,
  explicitly a separate, later tranche per the operator's own split.
  "further switches wait for the operator to pick them" (R4) — this
  tranche does not recommend which inventory candidate goes first beyond
  the one the operator already named.
- **Group B (`BridgeConfig` vs `engaged_bridge_source()`)** — a genuinely
  different-shaped candidate from the named example (a `Config` home
  already exists; the preset bypasses it with an inline dict instead of
  named per-field defaults). Not resolved into a switch here; worth the
  operator's explicit attention before it becomes a tranche, since "wire
  the preset to the existing Config fields" is a different, arguably
  simpler shape of change than "invent a new Config field."
- **Group C's env-var-sourced switches** (`DEEPREASON_SIMULATION_RUNNER`,
  `DEEPREASON_RESEARCH_ALLOWLIST`/`_MAX_REQUESTS`/`_MAX_SOURCES`,
  `DEEPREASON_CONFIG_REFEREE`) — plausibly `Config`-shaped (they already
  flow into the manifest and qualification subject), but converting an
  env-var invocation surface to a `Config` field changes how operators
  invoke the preset, not just where a literal lives — a larger question
  than Group A's literal switches, not decided here.
- **`DEEPREASON_DISABLE_V6_LAUNCHES`/`DEEPREASON_RELEASE_POLICY`** — noted
  in INVENTORY.md as PROBABLY the wrong shape for a `Config` migration at
  all (deliberately launch-only rollback levers, per
  `runtime/launch_policy.py`'s own docstring — "Rollback is deliberately a
  launch-only concern"). Recorded for completeness, not recommended.
- **`STANCE_LIBRARY`** (Group D, `capture/schools.py`) — hard-coded
  outside `config.py` but content curation, not a mode switch (no
  alternative value to choose between). Not recommended as a switch
  candidate; noted only because it is technically "hard-coded" and the
  sweep's own methodology (rung 1's five sockets) surfaced it.
- **An exhaustive, unbounded scan of every hard-coded constant in
  `src/deepreason/`** (125k lines) beyond the bounded sweep (preset files
  + rung 1's five sockets + `config.py`) — SPEC.md's A1 explicitly scoped
  this; a broader sweep is available on request.
