# Diagnosis: the enforced program contract exists only in the validator, never in the bytes the model is shown

Primary cause: the shape a `sandboxed_python_v1` program must have is
expressed in exactly one place — `validate_sandboxed_python_source`, which
rejects any module whose body is not a single `def simulate(inputs, rng)`
— and in no place the model can read. What the model reads is the wire
contract's JSON schema, serialised whole into the conjecturer prompt
(`adapter.py:764`, `json.dumps(schema_value, sort_keys=True)`), and
`SimulationProposalWireV1.model_source` carries no `description`, so the
schema states only `{"maxLength": 262144, "minLength": 1, "type":
"string"}`. A free-form string field is an accurate description of what
the wire accepts and a false one of what the harness admits. The same
silence covers `requested_observables`, whose enforced meaning — the
names must be keys of the mapping `simulate` returns — lives in
`contained.py:202` and is stated nowhere the model sees. So one cause
produces two denials, one recorded and one latent behind it.

Evidence:

  - `run-27b80f26bd398c718360e97e2a403593` capability state (read via
    `Harness(read_only=True).capability_state`): 11 transitions, of which
    the last is `CapabilityLifecycle.DENIED` /
    `reason_code=invalid_model_program`, on problem
    `question-71b4c653b03a234c64e9e018293e8927`. The transition
    immediately before it is `VALIDATED` /
    `typed_semantic_schema_valid` — the proposal passed the WIRE
    contract and then failed the PROGRAM contract. That pair is the
    defect in one line of record: schema-valid, harness-invalid.
  - The denied proposal
    (`sha256:480ef6d2abfa46076131681d0f9a444fd553832d479c4a840901192c52402f83`,
    `request_identifier=sim_2x2_diagonal_W_refutation`,
    `simulation_mode=sandboxed_python_v1`): its `model_source` parses to
    11 top-level statements —
    `['FunctionDef', 'Assign', 'Assign', 'Assign', 'Assert', 'Expr',
    'Assign', 'Assert', 'Expr', 'Assign', 'Expr']`. The one FunctionDef
    is `def verify_decomposition(U, V, W, n=2, r=7)`. The model wrote a
    script — a calibration against Strassen's rank-7 decomposition, a
    corrupted-W negative control, then the discriminating check — which
    is a competent piece of work under the contract it was given, and
    inadmissible under the contract that was enforced.
  - The same proposal's `requested_observables` is `('stdout',)`, and its
    program's outputs are `print()` calls. Under
    `capabilities/simulation.py:659` these names are handed to the
    contained runner, where `contained.py:202-212` computes
    `missing = [name for name in observables if name not in output]`
    against the mapping returned by `simulate` and fails
    `declared observable missing`. `stdout` could not have been a key of
    a mapping the model was never told to return. This is the second
    denial, latent behind the first.
  - The context pack blobs in that root's own blob store, scanned for the
    contract's words:

        blob      bytes   'simulate'  'inputs'  'rng'  'model_source'
        9705881e  23598       0          0       0          2
        29dcd187  23410       0          0       0          2
        881b47d3  23406       0          0       0          2

    Three conjecturer packs, ~23.5 KB each, every one containing the
    `SimulationProposalWireV1` schema and none containing the words the
    validator requires. The literal pack text is
    `"model_source": {"maxLength": 262144, "minLength": 1, "title":
    "Model Source", "type": "string"}`.

Implicated code:
  - `src/deepreason/llm/wire.py:839-841` — `model_source` and
    `requested_observables` fields with no `description`.
  - `src/deepreason/llm/adapter.py:764` — the whole schema, sorted, is
    the prompt's contract section; whatever `description` exists reaches
    the model, and whatever does not exist cannot.
  - `src/deepreason/simulation/compiler.py:211-225` — the enforced rule.
    Named as the site of the requirement, NOT as a site to change.

Falsifiable prediction (what `dr-reproduce` must show):

    Rendering a conjecturer context pack today, on a v5/v6
    simulation-enabled run, yields text containing "model_source" and
    "requested_observables" and containing no occurrence of "simulate",
    "inputs", or "rng" in the SimulationProposalWireV1 schema; and
    feeding the field run's own recorded `model_source` to
    `validate_sandboxed_python_source` raises
    ValueError("sandboxed Python must define exactly one simulate
    function"); and a program that satisfies that validator but returns
    a mapping without the requested observable name still fails
    `declared observable missing` in the contained runner. The route
    check: setting `description=` on those two fields changes the
    rendered pack text and nothing else in the proposal's validation.

Ruled out: **that the validator is what is broken.** The alternative
diagnosis is that `validate_sandboxed_python_source` is gratuitously
strict and should accept a module with statements beside the function.
Rejected on the record and on design. The single-function rule is what
makes the contained runner's contract decidable — the runner imports the
program, calls `simulate(inputs, rng)` once per input/seed pair, and
reads observables out of its return value (`contained.py:180-212`);
module-level statements would run at import, outside the per-call step
and memory metering, and their side effects (the field program's two
`assert`s and three `print`s) have no place to be recorded. Loosening it
widens what model-authored Python may do inside containment, which is a
capability question and not a documentation one. GOAL.md's Observed line
stands: the rule is right and unspoken.

Ruled out, second: **that a `description` cannot reach the pack.**
`_strict_schema` (`wire.py:179-195`) deep-copies the schema and only
sets `additionalProperties: false`; it strips nothing. `minimal_example`
(`wire.py:1844-1854`) does return a stripped skeleton, but for
`conjecturer.turn.v5` and `conjecturer.turn.v6` it short-circuits to the
literal `'{"abstention":{"search_signal":"stuck"}}'` before any skeleton
is built, so the skeleton path never touches these fields. The pack
blobs above corroborate it from the other end: they carry the full
schema with `title`, `maxLength`, and `minLength` intact.

## Second cause found and NOT parked

`requested_observables` is a second undisclosed rule with a second
enforcement site, so it could be read as a separate defect. It is kept
in this tranche rather than parked because the operator's approval names
it explicitly ("disclose the simulate(inputs, rng) contract **and the
requested_observables rule**"), and because the two share one cause, one
change site, and one payment of the frozen-baseline cost. Splitting them
would regenerate the two committed baselines twice for one disclosure.
