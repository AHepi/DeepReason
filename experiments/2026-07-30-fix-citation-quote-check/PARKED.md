# Parked — out of this tranche's goal

## D2 — the sandboxed_python_v1 program contract never reaches the model

NOT abandoned. Operator-ordered ("the first two need fixing
immediately"); it is the NEXT tranche, split from this one only because
CLAUDE.md requires one defect per commit and the two fixes together
exceed this tranche's 150-line budget.

`validate_sandboxed_python_source` (`src/deepreason/simulation/compiler.py:212`)
requires the module body to be exactly one `def simulate(inputs, rng)`.
In `run-27b80f26bd398c718360e97e2a403593` the model submitted an
11-statement script and was denied `invalid_model_program` with an empty
detail. The words `simulate`, `inputs`, and `rng` appear nowhere in the
23,570-byte context pack (blob `9705881e`), which describes
`model_source` only as `{"maxLength": 262144, "minLength": 1, "type":
"string"}`. Latent second failure behind it: `requested_observables` must
be keys of the mapping `simulate` returns
(`src/deepreason/verification/contained.py:202`), so the proposal's
`["stdout"]` would have failed one stage later as a missing declared
observable.

Open question that tranche must settle before touching anything: whether
adding the contract to the pack or role text moves the qualification
subject digest, which CLAUDE.md declares frozen.

## P4 — TOKEN_ACCOUNTING.json counts research records as simulation records

Operator instruction: investigate further, do not fix. Full entry in
`experiments/2026-07-30-change-amendment-epochs/PARKED.md`.
