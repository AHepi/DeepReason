# Fix: state the program contract in the schema the conjecturer reads

Guarantee restored: the shape a `sandboxed_python_v1` program must have,
and the rule that binds `requested_observables` to what that program
returns, appear in the bytes the model is shown — the same two rules the
sandbox validator and the contained runner enforce.

## Route chosen, and why

`Field(description=...)` on `SimulationProposalWireV1.model_source` and
`.requested_observables`, with the text held in two module constants.

Rejected: injecting the text conditionally in
`ConjecturerTurnWireContractV6.model_json_schema()`, mirroring
`V6_SCRATCH_WORKSHOP_SCHEMA_DESCRIPTION`. That precedent exists and was
weighed. It would confine the text to simulation-enabled packs — but it
reaches only v6, since `ConjecturerTurnWireContractV5` has no
`model_json_schema` override to hook, so v5 would need one written for
it. Two injection sites and ~15 lines of schema surgery buy a token
saving on packs where `SimulationProposalWireV1` is *already* present:
`$defs` keeps the definition even when `_omit_property` removes the
`simulation_proposals` property (measured — v6 with simulation disabled
still carries the full definition). The dead-weight objection is real
but it predates this tranche and is not what the operator approved
fixing; recorded in PARKED.md as D2e.

Rejected: changing `validate_sandboxed_python_source`. DIAGNOSIS.md's
ruled-out section: the rule is containment design, not documentation
debt, and loosening it widens what model-authored Python may do inside
the sandbox.

## Change sites (exhaustive)

  - `src/deepreason/llm/wire.py`, above `SimulationParameterSetWireV1` —
    two new module constants, `SIMULATION_MODEL_SOURCE_CONTRACT` and
    `SIMULATION_REQUESTED_OBSERVABLES_CONTRACT`, holding the disclosure
    text. Constants rather than inline strings so the regression test can
    assert the same object the schema carries.
  - `src/deepreason/llm/wire.py:839-840` — `model_source` and
    `requested_observables` each gain `description=`, plus a comment
    stating the constraint the code cannot show: these strings are the
    only place the harness tells the program's author what the program
    must look like, so they must track
    `validate_sandboxed_python_source` and the runner's observable check.
  - `tests/test_simulation_compiler.py` — one new regression test naming
    `run-27b80f26bd398c718360e97e2a403593`.
  - `tests/fixtures/incidents/DR-2026-07-16-AUTONOMOUS-INQUIRY-WAVE-A/PROVENANCE.json`
    — `generated_root_sha256.A3` regenerated (see below).

What the text says, in substance: for `sandboxed_python_v1` the whole
source is exactly one `def simulate(inputs, rng)` and nothing else — no
imports, no module-level statements, no decorators, no return
annotation, no default/keyword-only/variadic arguments; it is called
once per (input, seed) pair with `inputs` carrying `parameter_set`,
`parameters`, `sealed_inputs` and `rng` a seeded `random.Random`; it
returns a JSON-safe mapping of observable name to finite value, which is
the only output recorded, so printing reports nothing; `math` is
available and nothing else may be imported; for `declarative_numeric_v1`
the field is a JSON document instead. And: every `requested_observables`
name must be a key of what the program produces — the mapping `simulate`
returns, or the declarative document's `observables` — the sets matching
exactly, since a name that is not such a key ends the run with
`declared observable missing`, so stream names like `stdout` are never
observables.

Each clause is checked against the enforcing code rather than written
from memory: the argument rules against `compiler.py:211-225`, the
`inputs` keys against `capabilities/simulation.py:172-184`, `rng` and
`math` against `contained.py:125-165`, the observable rule against
`contained.py:202` and `compiler.py:160`, and "printing reports nothing"
against the runner's result channel, which is `result.json` and not
stdout (`contained.py:639-641`).

## The two baselines, predicted before the change lands

The operator pre-authorised regenerating two committed baselines.
Predicting them is the condition on that authority, so the predictions
below were MEASURED on a scratch prototype of exactly this text, which
was then reverted (`git checkout src/deepreason/llm/wire.py`) before
this document was written. They are reproducible, not estimated.

**1. `tests/fixtures/incidents/DR-2026-07-16-AUTONOMOUS-INQUIRY-WAVE-A/PROVENANCE.json`
— MOVES, one of three entries.**

    generated_root_sha256.A1  dd0f5df44d86...b15d6d2b661dd6   UNCHANGED
    generated_root_sha256.A2  b6c8de91f91a...0044adfbe23833   UNCHANGED
    generated_root_sha256.A3  d887b4494a5d7843c526cbc299dfe3151a36a67cc69ae89782aceb5972f7c642
                           -> 11b5aa701464ca5ad366374a3cad2f96cc6b65532f19ea8b2916092547384dbc

Only A3 is a fixture whose derived root carries a capability proposal,
so only A3's root embeds a pack containing `SimulationProposalWireV1`.
`descriptor_sha256` does NOT move: the A1/A2/A3 descriptors are inputs
and are not touched. This is a derived witness of determinism —
PROVENANCE.json records `original_root_bytes_included: false` — so
regenerating it re-states "the same descriptor, built by today's
harness, twice, identically". No original incident bytes exist to
falsify.

**2. `tests/fixtures/semantic_freedom_baseline_v1.json` — DOES NOT MOVE.**

`tokens_per_admitted_useful_candidate` stays `784.5`. This contradicts
the expectation BLOCKED.md set, so the mechanism is given rather than
asserted: the D1 tranche moved this metric with an `EvidenceRefClaimV1`
docstring, and that model IS in this fixture's conjecturer schema. The
simulation wire model is not. Measured by spying on `MockEndpoint` while
replaying the `offline_semantic_baseline` fixture — its three prompts
are 2685 / 445 / 2846 bytes, all three carry `EvidenceRefClaim`, and
none contains `SimulationProposalWireV1` or the string `simulate`. The
prototype gate confirms it from the other end: that test passed with the
change applied.

**Nothing else moves.** Full gate with the prototype applied and no test
edits at all: `1 failed, 3167 passed, 7 skipped in 813.25s`, the single
failure being the incident-wave frozen-roots test above. No third
baseline moved, which GOAL.md declared would be a stop.

**`verify_root` is untouched.** The sweep over all 23 committed run
roots under `experiments/` was run twice — with the prototype and on the
clean tree — and the full JSON reports are byte-identical, violation
counts and all. The append-only record is not a party to this change.

## Regression artifact

`experiments/2026-07-30-fix-sandbox-contract/repro_sandbox_contract.py`
must invert in part 1 only:

    part 1a/1b  occurrences {'simulate': 0, ...} -> nonzero, both v5 and v6
    part 1c     the field run's three committed packs -> STILL zero
    part 2      ValueError('...exactly one simulate function') -> unchanged
    part 3      'declared observable missing'                  -> unchanged

New permanent test, `tests/test_simulation_compiler.py`, docstring naming
`run-27b80f26bd398c718360e97e2a403593`. It asserts disclosure and
enforcement TOGETHER, so the two cannot drift:

  - the signature named in the disclosure text is the signature
    `validate_sandboxed_python_source` accepts (built into a program and
    validated, not string-compared);
  - the field run's shape — that same function with a script around it —
    still raises `exactly one simulate function`;
  - the failure phrase the observables text names,
    `declared observable missing`, is the runner's own wording, asserted
    against `CONTAINED_WORKER_SOURCE_V1`;
  - the declarative site enforces the same set rule
    (`compile_declarative_numeric` raises `observables differ` for a
    program whose observable is not the requested one);
  - both the v5 and the v6 simulation-enabled contract schemas, rendered
    the way `adapter.py:764` renders them, contain the signature,
    `sealed_inputs`, and the observables text.

## Existing tests at risk

  - `tests/test_incident_wave_a_v2_fixtures.py::test_incident_descriptors_and_generated_roots_are_frozen_and_deterministic`
    — **will fail; predicted above; the fixture is updated**, and only in
    the one approved field, under the operator's explicit authority. The
    test's other assertion (that two independent builds agree) keeps
    passing unchanged, so what the test proves is not weakened: it still
    proves determinism, now against today's bytes.
  - `tests/test_semantic_freedom_constitution.py::test_offline_semantic_freedom_baseline_is_measurable`
    — must keep passing UNCHANGED, and does. If it fails, the prediction
    above was wrong and this is a stop, not a second regeneration.
  - `tests/test_simulation_capability_v5.py`, `tests/test_research_conjecture_wire.py`,
    `tests/test_v6_*` — all build these contracts and all passed with the
    prototype. No expected-schema literals contain the changed fields.

## Explicitly not changed

`src/deepreason/simulation/compiler.py` and
`src/deepreason/verification/contained.py`. This tranche moves what is
disclosed; what is enforced stays exactly as it is. Three of the
reproduction's four parts must not move, and that is the check.

Also unchanged: run-root records, `REPLAY_VALIDATION.json`, replay
validation (operator: "Never touch run-root records or replay
validation"); `CapabilityTransitionV1` (D2a, parked);
`EvidenceRefClaimV1`'s quote docstring (D1a, parked — see PARKED.md for
why the cheap-now argument was refused).

## Estimated diff

    src/deepreason/llm/wire.py                ~32 lines
    tests/test_simulation_compiler.py         ~45 lines
    .../PROVENANCE.json                         1 line
    3 files, ~78 lines — inside the 150-line budget.

## Approval gate

GOAL.md classes this `defect`. The frozen surface it touches is named
and pre-authorised by the operator, quoted verbatim in GOAL.md, and the
authority's condition — that FIX.md predict the baseline moves — is
discharged above with measurements rather than estimates. `verify_root`
over every committed root is proven unmoved. Proceeds to
`dr-implement-fix`.

## Correction to GOAL.md's success criterion

GOAL.md's first criterion named `tests/test_simulation_capability.py`
and `tests/test_llm_packs.py`. Neither file exists — the names were
written before the test tree was searched. The criterion is unchanged in
substance and now reads against the real files:

    pytest tests/test_simulation_compiler.py tests/test_simulation_capability_v5.py -q
        passes, including the new regression test described above.

An amendment recording this is appended to GOAL.md rather than editing
its committed text, so the ledger shows what was claimed and when.
