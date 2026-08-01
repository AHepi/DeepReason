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

## Q1 — an unquoted citation is recorded as "byte-verified"

Checked during diagnosis and found to be INTENDED, so it is not part of
this tranche's cause. `EvidenceRefClaimV1.quote` is
`str | None = Field(default=None, ...)` and its docstring says a quote
"when present, must reproduce a contiguous byte span" — optional by
design (`src/deepreason/llm/contracts.py:32`). A bare block reference
asserts only that the block exists, which the checker does establish, and
`EvidenceCitationCheckV1.quoted` records which kind it was.

What is NOT clean, and is left parked: the ledger event carries only the
code, not the `quoted` flag (`src/deepreason/rules/conj.py:2314`), so
`findings.py` counts both kinds together and `FINDINGS.md` for this run
reports "Byte-verified citations of admitted evidence: 4" when all four
carried no quote and no bytes were compared. That line overstates what
the record holds. Narrow, cosmetic in effect, and a separate change to
the signal shape — out of scope here.

## D1a — the wire contract still describes the old, stricter quote rule

Split out of this tranche after the gate refused it. `EvidenceRefClaimV1`'s
docstring (`src/deepreason/llm/contracts.py:20-27`) tells the model a
quote "must reproduce a contiguous byte span of the block's canonical
text exactly — the citation checker byte-verifies it". After this
tranche the checker folds whitespace, so the text is stricter than the
rule.

Harmless in effect: a model that obeys the stricter text verifies under
the looser check. It is a documentation debt.

Not free to fix. Pydantic promotes the class docstring into the JSON
schema `description`, which is serialised into the conjecturer's context
pack, and the pack's bytes sit inside committed provenance digests:
`test_semantic_freedom_constitution`'s
`tokens_per_admitted_useful_candidate` baseline and
`test_incident_wave_a_v2_fixtures`'s `generated_root_sha256`. Changing
the docstring turns the gate red on both (proven by isolation, see
FIX.md's retraction). Regenerating those digests is frozen-record
semantics and needs operator approval.

Belongs to the D2 tranche, which is about what the pack tells the model
and will have to pay this cost once for both changes rather than twice.
