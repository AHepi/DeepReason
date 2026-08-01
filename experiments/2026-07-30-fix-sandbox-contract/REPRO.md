# Reproduction

Form: record-replay (parts 1 and 2) + live contained execution (part 3),
all offline — no provider call.

Artifact: `experiments/2026-07-30-fix-sandbox-contract/repro_sandbox_contract.py`

    $ python3 experiments/2026-07-30-fix-sandbox-contract/repro_sandbox_contract.py

Current output:

    == 1. what the pack says about model_source ==
      conjecturer.turn.v5: 5232 bytes of schema
        model_source          -> {"maxLength": 262144, "minLength": 1, "title": "Model Source", "type": "string"}
        requested_observables -> {"items": {"type": "string"}, "maxItems": 128, "minItems": 1, "title": "Requested Observables", "type": "array"}
        occurrences {'simulate': 0, 'inputs': 0, 'rng': 0}
      conjecturer.turn.v6: 9814 bytes of schema
        model_source          -> {"maxLength": 262144, "minLength": 1, "title": "Model Source", "type": "string"}
        requested_observables -> {"items": {"type": "string"}, "maxItems": 128, "minItems": 1, "title": "Requested Observables", "type": "array"}
        occurrences {'simulate': 0, 'inputs': 0, 'rng': 0}
      the same question asked of the field run's own committed packs:
        blob 29dcd187 (23410 bytes) occurrences {'simulate': 0, 'inputs': 0, 'rng': 0}
        blob 881b47d3 (23406 bytes) occurrences {'simulate': 0, 'inputs': 0, 'rng': 0}
        blob 9705881e (23598 bytes) occurrences {'simulate': 0, 'inputs': 0, 'rng': 0}
    == 2. the field run's recorded model_source, through the validator ==
        request_identifier    = sim_2x2_diagonal_W_refutation
        simulation_mode       = sandboxed_python_v1
        requested_observables = ('stdout',)
        top-level statements  = 11
        validator             -> ValueError('sandboxed Python must define exactly one simulate function')
    == 3. the latent second denial: an undeclarable observable ==
        a single simulate(inputs, rng) module -> accepted by the validator
        requested_observables  ['stdout']  (the field run's)
        contained runner       -> verdict='fail' trace={'error': 'declared observable missing',
                                   'input_index': 0, 'missing': ['stdout'], 'seed': 7}

Confirms diagnosis: yes. The words the validator requires occur zero
times in the schema the adapter serialises into the prompt — in the
contract as it stands today (parts 1a/1b, both v5 and v6) and in the
three packs the field run actually committed (part 1c). The field run's
own recorded program is refused by that unspoken rule (part 2), and a
program that satisfies it is still refused one stage later for the
observable name the model was equally never told how to choose (part 3).

Part 3 is a real contained execution, not a mirrored membership check:
`ContainedSimulationBackend.containment_available()` is True on this host,
so the subprocess ran under the containment envelope and returned the
typed `declared observable missing` trace itself.

Post-fix expectation, exactly:

  - part 1a/1b: `occurrences` becomes nonzero for all three words in both
    the v5 and v6 schemas, and `model_source` /
    `requested_observables` each carry a `description` stating the rule.
    The schema byte counts grow.
  - part 1c: UNCHANGED — `{'simulate': 0, 'inputs': 0, 'rng': 0}` on all
    three committed blobs. Those bytes are immutable record; a fix that
    moved them would be the frozen-record violation this tranche exists
    to avoid.
  - part 2: UNCHANGED — the same `ValueError`. The validator is not what
    is being changed; the field run's 11-statement script is still an
    invalid program, and would still be denied today. What changes is
    that a model reading the pack is told so before it writes one.
  - part 3: UNCHANGED — `declared observable missing`. The runner's rule
    is not being loosened either.

That three of the four parts must NOT move is the point: this tranche
changes what the model is shown, and nothing about what is enforced.
