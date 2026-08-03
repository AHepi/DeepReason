# Inventory: hard-coded behavior choices that could become named `Config` values
Rung 2, tranche 1 of `docs/HANDOVER_2026-08-03.md`'s modularisation ladder.
Methodology: SPEC.md's bounded sweep — the three preset/policy-shaped
files (`v6_policy.py`, `runtime/launch_policy.py`,
`capabilities/policy.py`), `config.py` read in full as baseline, and rung
1's five mapped sockets cross-checked against their `docs/map/`
documents. Zero `src/` changes; this document is the deliverable.

## Group A — preset-level mode/boolean switches (same shape as the named example)

These gate a discrete behavior choice inside `v6_policy.py`'s `engaged_*`
preset functions, with no `Config` field backing the value at all.

| Candidate | Pointer | Current hard-coded value | Note |
|---|---|---|---|
| Criticism authority | `v6_policy.py::engaged_criticism_policy`, line 212 | `authority="observe_only"` | **The named example (rung 2's own text).** Feeds `CriticismPolicyV1.authority`, a frozen 2-value manifest `Literal` (`observe_only`/`defended_trial`) — `DR-CON-authority`. No `Config` field exists for this specific preset choice (unlike `ARGUMENTATIVE_AUTHORITY`, which governs a *different* code path — the non-manifest-bound direct helpers). |
| School execution mode | `v6_policy.py::engaged_control_plane_policy_v3`, line 115 | `mode="conditioning_only"` | Feeds `SchoolExecutionPolicyV1.mode`, a 2-value manifest `Literal` (`conditioning_only`/`route_bound`) — `DR-CON-schools`. No `Config` field. |
| Conjecture context mode | `v6_policy.py::engaged_control_plane_policy_v3`, line 122 | `mode="harness_plus_model_request"` | Feeds `ConjectureContextPolicyV1.mode` (manifest). The `conservative` preset hard-codes the other value, `"disabled"`, at line 72 — two hard-coded literals for the same field, in two functions, with no `Config` switch between them. |
| Bridge mode | `v6_policy.py::engaged_bridge_source`, line 180 | `"mode": "grounded_two_stage"` | See Group B — a `Config`-typed home (`BridgeConfig.mode`) already exists with a DIFFERENT default (`"legacy_thesis"`). |
| Bridge grounding review | `v6_policy.py::engaged_bridge_source`, line 181 | `"grounding_review": True` | Docstring: "the only source of behavioral authority for the `reviewer_role` seat" — genuinely load-bearing. See Group B: `BridgeConfig.grounding_review` already exists (also defaults `True`, so this one line happens to already agree with Config; it is still hard-coded independently rather than read from it). |

## Group B — a `Config`-typed home already exists, but the preset bypasses it with an inline dict

`config.py` already declares `BridgeConfig` (line 193) as the sanctioned,
typed home for exactly this shape (`mode`, `grounding_review`,
`max_schema_repair_attempts`, `max_grounding_repair_attempts`,
`output_section_limit`, ...). `preparation.py::_config_for_profile` passes
`bridge=engaged_bridge_source()` into `Config(...)` — so the ENGAGED
preset's specific parameter choices are hard-coded as a raw dict in
`v6_policy.py`, one field at a time diverging from `BridgeConfig`'s own
declared defaults, instead of the preset overriding named `Config` fields
directly:

| `BridgeConfig` field (config.py) | Its own default | `engaged_bridge_source()`'s hard-coded value (v6_policy.py:179-185) |
|---|---|---|
| `mode` | `"legacy_thesis"` | `"grounded_two_stage"` |
| `grounding_review` | `True` | `True` (agrees, still independently hard-coded) |
| `max_schema_repair_attempts` | `2` | `1` |
| `max_grounding_repair_attempts` | `4` | `0` |
| `output_section_limit` | `32` | `4` |

This is a DIFFERENT shape of candidate than Group A: the "sanctioned
home" already exists and is already wired into `Config`; what is buried
is which VALUES the engaged preset chooses for it, expressed as an inline
dict literal rather than as named per-field engaged-preset defaults or an
explicit preset-selection mechanism. No `CriticismConfig`/`SchoolConfig`
equivalent exists for Group A's candidates — confirmed by reading
`config.py` in full: only `ScratchpadConfig` and `BridgeConfig` exist as
typed sub-configs (line 144, 193); criticism/school-routing authority has
no parallel.

## Group C — env-var-sourced switches (a parallel mechanism to `Config`, not `Config` itself)

Several `engaged_*` functions read `os.environ` directly (via an
`environ=None` parameter, defaulting to `os.environ`) rather than through
`Config`, yet the resulting value still becomes part of the compiled
manifest and therefore the qualification subject (each docstring says so
explicitly) — the same subject-changing shape a `Config` field would have,
just sourced differently:

| Candidate | Pointer | Env var | Current default |
|---|---|---|---|
| Simulation runner | `v6_policy.py::_contained_runner_opted`, line 230 | `DEEPREASON_SIMULATION_RUNNER` | unset/`"declarative"` (contained is operator-opted) |
| Research allowlist | `v6_policy.py::engaged_research_policy`, line 321 | `DEEPREASON_RESEARCH_ALLOWLIST` | unset (research disabled) |
| Research request/source caps | `v6_policy.py::engaged_research_policy`, lines 334-335 | `DEEPREASON_RESEARCH_MAX_REQUESTS`/`_MAX_SOURCES` | `"6"`/`"3"` (only read if allowlist is set) |
| Config-referee cadence | `v6_policy.py::engaged_config_referee_policy`, line 352 | `DEEPREASON_CONFIG_REFEREE` | unset (referee absent) |
| V6 launch kill switch | `runtime/launch_policy.py::require_v6_launch_allowed`, line 99 | `DEEPREASON_DISABLE_V6_LAUNCHES` | unset (launches enabled) |
| Release policy file | `runtime/launch_policy.py::require_v6_launch_allowed`, line 110 | `DEEPREASON_RELEASE_POLICY` | unset (no policy file consulted) |

Not necessarily migration candidates in the same sense as Group A/B — the
launch-policy pair (`DEEPREASON_DISABLE_V6_LAUNCHES`,
`DEEPREASON_RELEASE_POLICY`) are deliberately operator-facing rollback
levers meant to be flippable WITHOUT touching any per-run `Config`
compilation (this module's own docstring: "Rollback is deliberately a
launch-only concern"), so folding them into `Config` may be the wrong
move entirely — recorded here for completeness, not as an endorsed
candidate. The research/simulation/config-referee env vars are more
plausibly `Config`-shaped (they already flow into the manifest and
qualification subject exactly like a `Config` field would), but converting
an env-var-sourced value to a `Config` field is a different, larger
question than the observe_only-style literal switches in Group A — it
changes how operators invoke the preset, not just where a literal lives.

## Group D — content curation, not a mode switch (different character, noted for completeness)

`STANCE_LIBRARY` (`capture/schools.py`) is 8 hard-coded stance texts,
"closed and globally curated once" per `DR-CON-schools`. This is not a
behavior-choice SWITCH in the sense Group A/B are (there is no
alternative value to choose between — it is fixed reference content, and
`Config.N_SCHOOLS` already controls how many of the 8 are drawn from).
Listed for completeness since it is technically "hard-coded" and lives
outside `config.py`, but it does not fit rung 2's "buried choice becomes
a visible switch" shape and is not recommended as a switch candidate.

## Files checked and found to hold no candidates

`src/deepreason/capabilities/policy.py` — read in full. Entirely frozen
manifest schema DEFINITIONS (Pydantic models: `SimulationCapabilityPolicyV1`,
`ResearchCapabilityPolicyV1`, `ConfigRefereePolicyV1`, etc.) rather than a
place where a running preset makes a hard-coded runtime choice. Field
defaults here (e.g. `enabled: bool = False`) are schema-level defaults —
part of the frozen manifest surface itself (`DR-INV-frozen-surfaces`
surface 4), not a "buried Config choice." Changing one would be a schema
change, explicitly out of bounds for rung 2.

## Rung 1's five sockets, cross-checked against their map documents

`docs/map/CON-schools.md`, `CON-conjecture-source.md`,
`CON-criticism-source.md`, `CON-scheduler-ranking.md`, `CON-authority.md`
(all written in rung 1) already name every `Config` knob each socket
reads (`N_SCHOOLS`, `STANCE_DECAY`, `XEXAM_SHARE`, `LIVENESS_QUEUE`,
`FOCUS_PROBLEM`, `FOCUS_FAMILY`, `INTEGRATION_BUDGET_SHARE`, all five
authority knobs). No additional hard-coded literal surfaced by this
cross-check beyond what Group A/D above already name (`engaged_criticism_
policy`'s authority is `DR-CON-criticism-source`'s socket; `STANCE_LIBRARY`
is `DR-CON-schools`'s).

## Summary — candidates ranked by fit to rung 2's own example shape

1. **`engaged_criticism_policy`'s `authority`** (Group A) — the named
   first candidate; exact match to rung 2's own words and to the
   `ARGUMENTATIVE_AUTHORITY` precedent's shape (no existing `Config` home,
   closed 2-value literal, real behavioral consequence).
2. **School execution `mode`** (Group A) — same shape, same manifest-field
   pattern, no existing `Config` home.
3. **Conjecture context `mode`** (Group A) — same shape; two hard-coded
   literals already exist (one per preset) with no switch selecting them.
4. **Bridge `mode`/`grounding_review`/repair-attempt bounds** (Group B) —
   a different, arguably simpler fix: the `Config` home (`BridgeConfig`)
   already exists; the work is wiring the preset to it rather than
   inventing a new field.
5. Groups C and D are recorded for completeness; neither is recommended
   as the next switch without further discussion (env-var semantics for
   C, no-alternative-value for D).

Per rung 2's own words, "further switches wait for the operator to pick
them" — this document does not recommend which of the above becomes
tranche 2 beyond the one already named (`engaged_criticism_policy`'s
authority, item 1).
