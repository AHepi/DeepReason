# Reproduction

Form: in-memory (form 3), paired with the record replay already in DIAGNOSIS.md

Artifact: `experiments/2026-09-09-neural-embedder-fallback/repro_embedder_drop.py`
Command: `python -u experiments/2026-09-09-neural-embedder-fallback/repro_embedder_drop.py`
Convention: exit 0 = the defect is PRESENT (today), exit 1 = it is gone.
Full output preserved at `REPRO_OUTPUT.txt`.

No provider, no live call, no weights, no run root. The script calls the one
builder the managed `deepreason reason` path uses,
`preparation.build_preparation_manifest`, and then the run-time builder,
`ops.make_embedder`, on the configuration that builder compiled.

## Current output (trimmed; the full run is in REPRO_OUTPUT.txt)

    1. AN OPERATOR CONFIGURATION THAT NAMES THE NEURAL EMBEDDER
    Config() default EMBEDDER_MODEL          : 'nomic-ai/nomic-embed-text-v1.5'
    operator's explicit EMBEDDER_MODEL       : 'nomic-ai/nomic-embed-text-v1.5'
    manifest scratch_policy.embedder_model   : None
    manifest scratch_policy.embedder_backend : 'deterministic_hashing'
    runtime Config.EMBEDDER_MODEL            : None
    compile notices, all codes               : []
    compile notices mentioning the embedder  : []
      >> DEFECT: the value was dropped and NOTHING in the record says so.

    2. WHAT THE RUN-TIME BUILDER DOES WITH THE COMPILED CONFIGURATION
    make_embedder returned                   : None
    Measure records written                  : []
      >> DEFECT: the geometry instrument changed and the log is silent.

    3. THE WEIGHTS ARE IRRELEVANT — NO BACKEND IS EVER BUILT
    warmed cache location                    : /tmp/fastembed_cache
      exists on disk                         : True
    manifest byte-identical either way       : True
      >> The cache hypothesis is REFUTED.

    VERDICT: defect PRESENT

Confirms diagnosis: yes — all three halves of DIAGNOSIS.md's falsifiable
prediction came out as predicted. An operator configuration that explicitly
names the neural embedder compiles to `null` with ZERO compile notices of any
code; `make_embedder` on that compiled configuration returns the hashing
default having written nothing; and the compiled manifest is byte-identical
whether `FASTEMBED_CACHE_PATH` points at the warmed cache (which exists on this
container — the session's own `embedder-warmup` filled it, fingerprint
`d6e3599ce0377000`) or at an empty directory the run cannot use. The third
observation is what refutes the cache hypothesis the tranche brief named as
likely: nothing about the weights can change a decision taken before any
backend is asked for.

One point the reproduction sharpens beyond the diagnosis. The gap is not only
that a host override is undisclosed; it is that the EXISTING disjunction test
cannot see this class of drop at all.
`tests/test_managed_path_config_read.py::test_managed_manifest_carries_or_discloses_every_operator_setting`
compares the operator's configuration against `Config()` and checks only the
fields that DIFFER from the default. `EMBEDDER_MODEL`'s default IS the neural
model, so a configuration that asks for it — or that asks for nothing and
relies on the armed default, which is what all five arms did — never enters
that test's `configured` set. The field is dropped from the default, and the
test that exists to catch exactly this is looking only at deviations from it.
That is why the 2026-08-29 managed-path fix and the 2026-08-16 embedder fix
both shipped green over a live defect.

Post-fix expectation: the same command exits 1 with

    compile notices mentioning the embedder  : [{'code': <the disclosure code>,
                                                 'pointer': '/engine_config/EMBEDDER_MODEL'}]
      >> the value was dropped, and a notice names it. Defect absent.

    Measure records written                  : [['embedder-fallback',
                                                 'nomic-ai/nomic-embed-text-v1.5',
                                                 '<the cause>']]
      >> a typed record names the cause. Defect absent.

    VERDICT: defect ABSENT

Section 3 must keep printing `manifest byte-identical either way : True` after
the fix. If a fix makes the compiled manifest depend on the cache location it
has made run identity depend on the container, and that is a worse defect than
the one being repaired.

Production code untouched by this phase.
