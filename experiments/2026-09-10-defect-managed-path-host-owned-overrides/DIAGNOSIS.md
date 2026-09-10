# Diagnosis: the managed path replaces seven configuration values BEFORE the compiler sees them, so the compiler's own disclosure channel has nothing left to disclose

## Stop report, section 4 (pasted verbatim, before anything of mine)

Source: `experiments/2026-09-04-experiment-brief-variation-step1/roots/A0-run-fe00609058e10605590206d51ab2b7a0`
(full report at `probe/stop_report_A0.txt`; the same section is byte-identical
for A1, A1P, A2 and A3 — all five reached `completed / budget_exhausted`).

    ## 4. THE STOP, CLASSIFIED

    Stop message: `(none recorded)`

    Boxes ranked by evidence:

    ### 1. CONFIGURATION — RULED OUT

    - evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.

    ### 2. ENVIRONMENT — RULED OUT

    - evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.

    ### 3. MODEL — RULED OUT

    - evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.

    ### 4. HARNESS — RULED OUT

    - evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.

All four boxes are ruled out because nothing failed, which is the correct
verdict for the stop and the reason this defect is invisible to it. The line
that carries the fact is in section 1, not section 4:

    - embedder as compiled: **hashing**

"as compiled" names the stage. `DR-CON-configuration-stages` splits a setting
into four: the operator's file (stage 1, the one stage that is NOT record and
therefore never evidence about a run), the compiled manifest (stage 2),
run-time restoration from notices (stage 3), and the seat (stage 4). This
defect lives entirely between stages 1 and 2, and the report's section 3
(provider health: 110 attempts, zero faults) rules the provider out
independently of the clean terminal.

Primary cause: `preparation._config_for_profile` builds a dictionary named
`owned` holding seven values and applies it over the operator's loaded
configuration — `data.update(owned)` when a configuration was given,
`Config(**owned)` when none was (`preparation.py:374-399`). The compiler is
then handed the ALREADY-OVERRIDDEN configuration, so
`_emit_uncarried_config_notices` compares that configuration against the echo
it produced (`run_manifest.py:2630-2685`) and finds nothing missing: the
operator's value is not "dropped by the compiler", it is gone before the
compiler is called. The prose guarantee at `preparation.py:505-508` — "every
field it sets is either carried into the compiled manifest or disclosed by the
compiler as a typed `ENGINE_CONFIG_FIELD_NOT_CARRIED` notice, except the seven
the host owns" — therefore states an exemption that no code enforces and no
record discloses; the seven simply vanish. For the embedder specifically the
consequence is a measurement scale: `EMBEDDER_MODEL=None` reaches
`compile_run_manifest`, whose `semantic_active and configured_embedder` branch
is not taken (`run_manifest.py:2962-2996`), so `scratch_policy` compiles
`embedder_backend="deterministic_hashing"`, `embedder_model=None`, and at run
time `ops.make_embedder`'s first branch returns the hashing default
(`ops.py:178-200`). Since 2026-09-09 that branch also writes an
`embedder-unconfigured` Measure, which says the compiled configuration named
no model — true, and silent about the fact that a configuration DID name one
one stage earlier. Nothing here is a defect of a model, a seat or the provider:
section 4 rules all four boxes out and section 3 shows 110 clean attempts.

Evidence:

  - `probe/seven_values.out` (re-derivable: `python -u probe/seven_values.py`)
    -> an operator configuration stating all seven values away from the host's
    own, compiled through the same `build_preparation_manifest` the managed
    path calls, yields `compile_notices: 0` and `silently replaced: 7 of 7`.
    Every one of the seven is neither carried into the runtime configuration
    nor named by any notice. This is the guarantee at `preparation.py:505-508`
    failing for exactly the fields its own sentence exempts.
  - `probe/census.out` (re-derivable: `python -u probe/census.py`) -> across
    101 committed run manifests, **63 of 63 MANAGED roots compiled
    `deterministic_hashing`; none compiled neural**, and 62 of the 63 carry
    zero compile notices of any code. Six NON-managed manifests compiled
    `neural`. So the neural road exists and works — it is the managed door
    that cannot reach it, which is the record's own statement of the parked
    P3 finding rather than a reading of code.
  - `experiments/2026-09-04-experiment-brief-variation-step1/roots/A0-.../run-manifest.json`
    -> `scratch_policy.embedder_model = null`,
    `scratch_policy.embedder_backend = "deterministic_hashing"`,
    `compile_notices = null`, and `engine_config_json` carries
    `"EMBEDDER_MODEL": null`, `"engine_profile": "full"`,
    `"model_profile": "standard"`, `"roles": {}` while `scratchpad`, `bridge`
    and `CHANNELS_DISABLED` are absent from the echo entirely. Four of the
    seven are in the echo and three are not, which is why one channel cannot
    serve all seven.
  - `experiments/2026-09-04-.../roots/A0-.../log.jsonl` seq 8 -> `Measure
    inputs ["embedder","hashing-128","1","4226e035204776db"]`, byte-identical
    across all five arms; `grep -c embedder-fallback` returns 0 in all five.
    The record says WHICH instrument measured and, before 2026-09-09, nothing
    about why.
  - `tests/test_managed_path_config_read.py:151`
    (`test_managed_manifest_carries_or_discloses_every_operator_setting`) ->
    the guarantee is already a committed test, and it passes today only
    because its `OPERATOR_YAML` fixture (`:53-59`) sets five switches, none of
    them among the seven. The test states the right law over the wrong
    domain.
  - `docs/map/CON-configuration-stages.md:71-90` (stage 3) -> the ONLY
    documented road by which a setting the manifest does not carry still takes
    effect is an `ENGINE_CONFIG_FIELD_NOT_CARRIED` notice, restored at run
    time. A value dropped before the compiler has no stage-3 road at all, so
    "not carried" and "not disclosed" are the same event for the seven.

Implicated code:

  - `src/deepreason/preparation.py:374-399` — the `owned` dictionary and the
    two application sites (`Config(**owned)` and `data.update(owned)`). The
    override itself, and the only place that still knows what the operator
    asked for.
  - `src/deepreason/run_manifest.py:2650-2657` — `_emit_uncarried_config_notices`'s
    loop, which can only disclose a field DROPPED FROM THE ECHO; four of the
    seven are in the echo (holding the host's value, not the operator's) and
    are therefore invisible to it by construction.
  - `src/deepreason/ops.py:178-200` — `make_embedder`'s first branch, correct
    as written: it reports the compiled configuration faithfully and has
    nothing else to report.

Falsifiable prediction: `dr-reproduce` must show, offline against the
deterministic stub with no provider call, (a) that a run prepared through the
managed door from an operator configuration explicitly naming
`EMBEDDER_MODEL` stamps `["embedder","hashing-128",...]` and an
`embedder-unconfigured` Measure, while the SAME configuration compiled without
the host override stamps the neural fingerprint and no `embedder-unconfigured`;
and (b) that all seven values are absent from `compile_notices` in the first
case. If either half fails — if a notice already names one of the seven, or if
the two roads stamp the same geometry — this diagnosis is wrong.

Ruled out: **the compiler's existing disclosure channel is merely mis-scoped
and could be widened to cover the seven.** It cannot, and the reason decides
the fix's shape. `_emit_uncarried_config_notices` iterates
`_unconditionally_dropped_config_fields()` — fields absent from the engine-config
echo — and skips any field still present in it (`run_manifest.py:2654-2656`).
Four of the seven (`engine_profile`, `model_profile`, `EMBEDDER_MODEL`,
`roles`) ARE in the echo, carrying the host's value; the channel would have to
compare against a configuration it never receives. Measured, not argued: the
probe's seven rows include those four, and the compiler emitted zero notices.
Separately, the channel's `value` field is the road BACK — `run_manifest.py:1202-1205`,
"a disclosure is also the road back: `config_from_run_manifest` restores it" —
so a notice under that code carrying an overridden value would re-arm exactly
the value the host means to own, which for `roles` and `model_profile` is the
endpoint-redirection boundary the override exists to hold.

Second, independent finding, parked (PARKED.md P4): `config.apply_overrides`
rebuilds the configuration with `Config.model_validate(data)`, so its result
reports all 106 fields as explicitly set. Any fix using "the operator stated
this" as its test must not read that function's output. It has no caller in
`src/`, which is why this tranche's fix is safe today and why the park exists.
