# Goal: the conjecturer is told the sandboxed_python_v1 program contract

Class: defect

Observed: in `run-27b80f26bd398c718360e97e2a403593` (committed under
`experiments/live_research_2026-07-29/openchallenge/runs/`) the model
submitted a `sandboxed_python_v1` proposal whose `model_source` is an
11-statement module, and the harness denied it `invalid_model_program`.
`validate_sandboxed_python_source`
(`src/deepreason/simulation/compiler.py:211`) admits only a module whose
body is exactly one `def simulate(inputs, rng)`. The strings `simulate`,
`inputs`, and `rng` appear nowhere in that run's 23,570-byte conjecturer
context pack, which describes `model_source` only as
`{"maxLength": 262144, "minLength": 1, "type": "string"}`. A second,
latent denial sits behind it: `requested_observables` must be keys of
the mapping `simulate` returns
(`src/deepreason/verification/contained.py:202`), and the pack does not
say so either, so the proposal's `["stdout"]` would have failed one
stage later.

Why `defect` and not `capability-gap`: the capability channel's stated
purpose is that a model may propose a simulation and have it executed
under containment. A contract that is enforced but never disclosed makes
that channel unusable in practice — the model cannot satisfy a rule it
is never shown — so the recorded `invalid_model_program` denials measure
the pack's silence, not the model's competence. The operator has in any
case explicitly ordered this fixed, so the class does not gate
implementation.

## Operator approval (verbatim) — the tranche ledger

BLOCKED.md put four options to the operator and stopped. The reply, in
full and unedited:

> Operator decision on D2: approved for D2b only — disclose the
> simulate(inputs, rng) contract and the requested_observables rule in
> the conjecturer's context pack. The two test baselines BLOCKED.md
> names (semantic-freedom token metric, incident-wave
> generated_root_sha256) may be regenerated in the same commit; FIX.md
> must predict both moves and the full gate must end 0 failed. Park D2a.
> Never touch run-root records or replay validation.

This is the sole authority for regenerating two committed provenance
digests, which the orchestrator would otherwise stop on. Its four
operative clauses bind this tranche:

1. **Scope**: the `simulate(inputs, rng)` contract and the
   `requested_observables` rule, disclosed in the conjecturer's context
   pack. Nothing else in the pack.
2. **Cost, pre-authorised**: the semantic-freedom token metric and the
   incident-wave `generated_root_sha256` may be regenerated, in this
   same commit, and `FIX.md` must PREDICT both moves before they happen
   — a baseline that moves unpredicted is a stop, not a regeneration.
3. **Gate**: the full gate must end 0 failed. No weakened assertion, no
   xfail, no skip.
4. **Excluded**: D2a (a denial-detail field on `CapabilityTransitionV1`)
   is parked. Run-root records and replay validation are untouchable.

Success criterion (machine-decidable):

    pytest tests/test_simulation_capability.py tests/test_llm_packs.py -q
        passes, including a new regression test naming
        run-27b80f26bd398c718360e97e2a403593 in its docstring, asserting
        that the conjecturer context pack a v5/v6 simulation-enabled run
        renders contains, as literal text:
        (a) the `simulate(inputs, rng)` signature;
        (b) the rule that `requested_observables` must be keys of the
            mapping `simulate` returns.

    pytest tests/ -q -n 4
        0 failed.

    verify_root over every committed run root in experiments/
        verdicts byte-identical to those captured at 616b58fe.

Exactly two committed fixture baselines may move, and only these:

    tests/fixtures/semantic_freedom_baseline_v1.json
        metrics.tokens_per_admitted_useful_candidate  (784.5 -> new)
    tests/fixtures/incidents/<incident>/PROVENANCE.json
        generated_root_sha256  (A1/A2/A3 -> new)

Any THIRD baseline that moves is an unpredicted consequence and a stop.

In scope:
  - `src/deepreason/llm/wire.py` (`SimulationProposalWireV1` — the field
    descriptions/docstring that become the pack's JSON schema text)
  - `tests/` (new regression test; the two approved baseline files)
  - `src/deepreason/llm/packs.py` (only if the schema route proves not to
    reach the conjecturer pack and prose is the only route)

NOT in scope: `src/deepreason/simulation/compiler.py`. The validator's
rule is not what is broken — the rule is deliberate containment design,
and loosening it to accept an 11-statement module would widen what
model-authored Python may do inside the contained subprocess. This
tranche moves the disclosure, not the contract.

Also NOT in scope, by explicit operator instruction:
  - D2a — a denial-detail field on `CapabilityTransitionV1`. Parked.
  - Run-root records, `REPLAY_VALIDATION.json`, replay-validation record
    formats, `invariants.py` verify_root semantics. Untouchable.
  - D1a — `EvidenceRefClaimV1`'s quote docstring. See PARKED.md; the
    approval enumerates two disclosures and D1a is not among them.
  - P4 — TOKEN_ACCOUNTING.json miscounting research as simulation.

Budget: <=150 changed lines, 1 commit, ~3 hours
Stop conditions inherited from orchestrator: yes

## What this goal deliberately leaves open

The criterion commits to the OUTCOME (the contract's words are in the
pack the conjecturer reads) and not to the ROUTE. `dr-propose-fix` must
choose among: `Field(description=...)` on the two fields; a class
docstring on `SimulationProposalWireV1` promoted to the schema's
`description`; or capability prose rendered by `packs.py`. The route
matters because `minimal_skeleton` and `_strict_schema` may strip
description text on some paths — which route actually reaches the pack
is a diagnosis question, not an assumption.

## The one thing this goal does NOT claim

Fixing the disclosure does not prove a model will then author a valid
program. Capability-channel use is stochastic (CLAUDE.md), so a live run
is not the criterion here. What is decidable offline is whether the
contract the harness enforces is present in the bytes the model is
shown.
