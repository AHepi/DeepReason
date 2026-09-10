# Reproduction

Form: in-memory + record (a real `Harness` log, read back by the function
`deepreason results` calls). Offline: no provider, no network, no live call.

Artifact: `experiments/2026-09-10-defect-managed-path-host-owned-overrides/repro_managed_override.py`
(`python -u <path>` from the repo root; exit 1 = defect present, exit 0 = gone).
Full output: `REPRO_OUTPUT.txt`.

Every stage is the run's own code, not a restatement of it: the managed door
(`preparation.build_preparation_manifest`), the run-time rebuild
(`config_from_run_manifest`, stage 3 of `DR-CON-configuration-stages`), the
builder (`ops.make_embedder`), the geometry stamp (the real `Scheduler`'s
`_embedder_fingerprint`, recorded with the same `record_measure` call
`Scheduler.step` makes once per run) and the reader
(`application/results.embedder_summary_for_root` and `embedder_line`).

## Current output (trimmed; full text in REPRO_OUTPUT.txt)

    ## 1. THE SEVEN
    compile notices on the manifest: 0
    value                carried   disclosed  the operator stated
    engine_profile       False     False      'mini'
    model_profile        False     False      'frontier'
    scratchpad           False     False      'enabled=True max_blocks_per_pack=24 max_guid'
    bridge               False     False      "mode='grounded_two_stage' allow_partial=True"
    EMBEDDER_MODEL       False     False      'nomic-ai/nomic-embed-text-v1.5'
    CHANNELS_DISABLED    False     False      "('simulation',)"
    roles                False     False      "{'conjecturer': {'provider': 'openai', 'mode"
    neither carried nor disclosed: 7 of 7

    ## 2. THE GEOMETRY
    compiled scratch policy: backend='deterministic_hashing' model=None
    engine_config EMBEDDER_MODEL (what the run rebuilds): None
    Measure kinds on the log: ['embedder-unconfigured', 'embedder']
    deepreason results would print: embedder: hashing (hashing-128) — no
      embedder model in the compiled run configuration, though a default one
      names this model: it was dropped before the manifest

    ## 3. THE CONTROL (the same rebuild, EMBEDDER_MODEL put back)
    deepreason results would print: embedder: neural (nomic-ai/nomic-embed-text-v1.5)

    ## VERDICT
    the run asked the neural backend for it at all: False
    the same rebuild with the field restored measured with
      'nomic-ai/nomic-embed-text-v1.5' (backend 'neural')
    DEFECT PRESENT: 7 of 7 values silently replaced; the configured embedder
    was never requested

## Confirms diagnosis: yes

Both halves of DIAGNOSIS.md's falsifiable prediction hold. (a) The managed
door drops a configuration that explicitly names the neural model and the run
stamps hashing plus `embedder-unconfigured`, while the SAME rebuilt
configuration with that one field restored stamps the neural fingerprint in
the same container, same process, same cache — so nothing environmental
decides it; one value does. (b) `compile_notices` is empty and all seven
values are absent from it, which is the disclosure channel failing for exactly
the fields `preparation.py:505-508` names as its exception.

The control also settles what the 2026-09-09 tranche could only park: the
neural road WORKS from this container. `probe/census.out` said the same thing
from the committed record (six non-managed manifests compiled `neural`, zero
managed ones); observation 3 says it live, offline, in the process that just
failed to reach it.

## Post-fix expectation

Exit 0, with:

  - observation 1: every row `carried=True` or `disclosed=True`;
    `neither carried nor disclosed: 0 of 7`. `EMBEDDER_MODEL` carried;
    the six the host keeps disclosed by a typed notice naming each.
  - observation 2: `compiled scratch policy: backend='neural'
    model='nomic-ai/nomic-embed-text-v1.5'`, `Measure kinds on the log:
    ['embedder']` with NO `embedder-unconfigured`, and `deepreason results
    would print: embedder: neural (nomic-ai/nomic-embed-text-v1.5)`.
  - observation 3 unchanged — it is a control and must keep printing neural;
    if it ever stops, the container lost its weights and observation 2's
    reading is about the cache rather than about the fix.
  - the one legitimate alternative the script accepts: on a container with no
    fastembed weights, observation 2 records `embedder-fallback` instead. The
    run then measured on hashing because the backend could not be BUILT, which
    is a typed record of a real event and the opposite of this defect. A fix
    that made the geometry depend on the cache being warm would have made run
    identity depend on the container, so the script must not demand neural.
