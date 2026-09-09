# Diagnosis: the managed preparation path overrides EMBEDDER_MODEL to None, and the override is exempt from the compiler's own disclosure channel

## Stop report, section 4 (pasted verbatim, before anything of mine)

Source: `experiments/2026-09-04-experiment-brief-variation-step1/roots/A0-run-fe00609058e10605590206d51ab2b7a0`
(the same section is byte-identical for A1, A1P, A2 and A3 — all five reached
`completed / budget_exhausted`).

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
    

The report rules out all four boxes because the run did not fail. That is the
correct verdict for the STOP and it is why the embedder problem is invisible to
it: nothing about the geometry instrument is a stop. The one line in the report
that carries the fact is in section 1, not section 4:

    - embedder as compiled: **hashing**

"as compiled" is the whole diagnosis in three words: the decision was made
before the run opened its log, so no run-time fallback could be recorded.

Primary cause: on the managed `deepreason reason` path the run configuration is
built by `preparation._config_for_profile`, whose `owned` dictionary sets
`EMBEDDER_MODEL=None` unconditionally — one of seven values the host takes
whatever the operator's configuration says (`preparation.py:376-394`). The
compiler discloses every other engine-config field it does not carry as a typed
`ENGINE_CONFIG_FIELD_NOT_CARRIED` compile notice, and `preparation.py:505-508`
states the exemption in prose: "except the seven the host owns". So the neural
default that `pip install -e .` arms (`config.py:713`,
`EMBEDDER_MODEL = "nomic-ai/nomic-embed-text-v1.5"`) is discarded with no
notice, the manifest compiles `scratch_policy.embedder_model = null` and
`embedder_backend = "deterministic_hashing"`, and at run time
`ops.make_embedder` takes its first branch — `if not config.EMBEDDER_MODEL:
return None` (`ops.py:159-160`) — which returns before the `embedder-fallback`
Measure on the exception path below it can ever be reached. The scheduler then
stamps the hashing geometry (`scheduler.py:2305`) and `embedder_summary` reads a
`fallback: False` record (`application/results.py:393-413`), so
`deepreason results` prints `embedder: hashing (hashing-128)` with nothing to
attribute it to. The warmed weights were never consulted because no code path
ever asked for them. This is not a defect of the model, a seat, or the provider:
the stop report rules all four boxes out (section 4, all four "RULED OUT"), and
the mechanism is entirely in configuration carriage.

Evidence:

  - `roots/*/run-manifest.json` (all five arms) -> `scratch_policy.embedder_model
    = null`, `scratch_policy.embedder_backend = "deterministic_hashing"`,
    `embedder_failure_policy = "fallback"`, and `compile_notices` is EMPTY (0
    notices of any code, embedder or otherwise). The configuration that ran
    never named a neural model, and nothing in the record says a value was
    dropped.
  - `roots/A0-.../log.jsonl` seq 8 -> `Measure inputs
    ["embedder","hashing-128","1","4226e035204776db"]`, the once-per-run
    geometry stamp. The identical stamp, byte for byte, appears in all five
    arms; `grep -c embedder-fallback` returns 0 in all five. So the record
    carries WHICH instrument was used and never WHY.
  - Stop report section 1 -> `embedder as compiled: **hashing**`. The word is
    "compiled": stage 2 of `DR-CON-configuration-stages`, decided before the
    run root existed, so no property of the launching process — its working
    directory, its `FASTEMBED_CACHE_PATH`, its detachment under `setsid nohup`
    — could have changed it.
  - `experiments/2026-09-04-experiment-brief-variation-step1/arm.sh:98` ->
    `deepreason reason --cycles 4 --token-budget 600000 "$Q"`. No `--config`
    was passed by any arm, so `base is None` and `_config_for_profile` returned
    `Config(**owned)` — the code default for `EMBEDDER_MODEL` never entered the
    compiled configuration at all.
  - `docs/map/SUB-llm.md:493-511` (Traps) -> this is the SAME trap recurring in
    a new form. Its 2026-08-16 entry records runs that configured neural
    geometry and measured with `hashing-128` for 24 cycles, and its stated fix
    was to arm the default by install and surface the fallback in `deepreason
    results`. Both halves shipped and neither reaches the managed path, because
    the managed path throws the armed default away one stage earlier than the
    fallback machinery watches. The trap's own general lesson — "a default
    naming an OPTIONAL backend is a default that silently isn't" — recurs here
    as: a default the host silently overrides is a default that silently isn't.

Implicated code:

  - `src/deepreason/preparation.py:388` — `EMBEDDER_MODEL=None` in `owned`, the
    override itself, exempt from the disclosure channel by
    `preparation.py:505-508`.
  - `src/deepreason/ops.py:159-160` — `if not config.EMBEDDER_MODEL: return
    None`, the early return that makes the run-time fallback record
    unreachable on this path.
  - `src/deepreason/application/results.py:393-413` — the reader, which is
    already correct: it renders `fallback` and `fallback_reason` faithfully and
    has nothing to render.

Falsifiable prediction: `dr-reproduce` must show, offline against the
deterministic stub with no provider and no live call, that a run prepared
through `preparation.prepare_managed_run` (or the same `_config_for_profile`
call) with an operator configuration that explicitly sets
`EMBEDDER_MODEL="nomic-ai/nomic-embed-text-v1.5"` still compiles
`scratch_policy.embedder_model = null` with zero compile notices, while the
same configuration compiled WITHOUT the host override carries the model. And
it must show that the emptiness is independent of the weights: with
`FASTEMBED_CACHE_PATH` pointed at the warmed cache AND at an unreadable
directory, the compiled manifest and the log's embedder stamp are byte-identical
in both, because no build is attempted either way. If either half fails, this
diagnosis is wrong.

Ruled out: **the detached process could not see the warmed cache** (the
hypothesis the tranche brief named as likely — that `setsid nohup` gave the arm
a different `FASTEMBED_CACHE_PATH` or temp directory than the warmup filled).
The record refutes it in one step. If a neural backend had been ASKED for and
failed to build, `ops.make_embedder` would have caught `EmbedderUnavailable` and
recorded `embedder-fallback` with the cause under the `fallback` policy that the
manifest shows was in force (`ops.py:166-175`), or raised under the `error`
policy. Neither happened: zero `embedder-fallback` events in all five logs, and
the runs completed. A cache the process cannot read produces a LOUD record here;
what the arms carry is the signature of a request that was never made. The cache
was never reached because `scratch_policy.embedder_model` was already `null`
when the manifest was written, seconds before the run root opened.

Parked (second, independent finding — not fixed here): the same exemption
covers the other six host-owned values (`engine_profile`, `model_profile`,
`scratchpad`, `bridge`, `CHANNELS_DISABLED`, `roles`). Whether any of those
also drops an operator value silently is a separate question with its own
evidence; see PARKED.md.
