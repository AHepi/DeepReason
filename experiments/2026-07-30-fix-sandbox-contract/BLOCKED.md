# D2 — blocked at the orchestrator's frozen-surface stop condition

Not a goal yet. This records why the tranche cannot open without an
operator decision, so the decision is made once and with the cost known.

## The defect (unchanged, from the 2026-07-30 diagnosis)

`validate_sandboxed_python_source` (`src/deepreason/simulation/compiler.py:212`)
requires the module body to be exactly one `def simulate(inputs, rng)`.
In `run-27b80f26bd398c718360e97e2a403593` the model submitted an
11-statement script and was denied `invalid_model_program`. The words
`simulate`, `inputs`, and `rng` appear nowhere in the 23,570-byte context
pack, which describes `model_source` only as
`{"maxLength": 262144, "minLength": 1, "type": "string"}`. Latent second
failure: `requested_observables` must be keys of the mapping `simulate`
returns (`verification/contained.py:202`), so the proposal's `["stdout"]`
would have failed one stage later.

## Both available fixes touch a frozen surface

**D2b — tell the model the contract.** Any route puts new bytes in the
conjecturer's context pack: the wire model's docstring, a
`Field(description=...)` on `model_source`, or capability prose. The pack's
bytes sit inside two committed provenance digests, proven this session by
the D1 tranche's retracted amendment:

    test_semantic_freedom_constitution — tokens_per_admitted_useful_candidate
      moved 784.5 -> 842.0 for a docstring edit of comparable size
    test_incident_wave_a_v2_fixtures — generated_root_sha256 moved
      d887b4494a5d... -> a8ea8a62891a...

Fixing D2b means editing `PROVENANCE.json`'s `generated_root_sha256` and
the semantic-freedom baseline — rewriting committed provenance records.

**D2a — say WHY the program was invalid.** `CapabilityTransitionV1` has
no detail field at all; its fields are exactly
`budget_delta, capability_policy_digest, formal_fence_seq, id, lifecycle,
manifest_digest, next_process_digest, originating_work_order_ref,
phase_record_ref, previous_process_digest, previous_transition_ref,
problem_ref, reason_code, request_digest, request_ref, run_input_digest,
schema_, scratch_fence_seq, trigger_ref`. Carrying the validator's
message ("sandboxed Python must define exactly one simulate function")
into the record means adding a field to a capability-state record, and
`capabilities/state.py` digests and event application are named frozen in
CLAUDE.md.

## Why this is a stop and not a judgement call

The orchestrator stops rather than improvises when a fix requires
touching frozen-record semantics, and CLAUDE.md requires explicit
operator approval for these surfaces. Proceeding either way without that
approval is wrong: regenerating committed provenance silently is the
failure the freeze exists to prevent, and doing nothing leaves an
operator-ordered defect unfixed.

## What is NOT at stake, so the decision is not over-weighted

Neither surface invalidates a committed run root. The two digests are
test-fixture baselines — a generated fixture root and a measured metric —
not roots under `experiments/`. `verify_root` over all sixteen committed
roots does not read either. The D1 tranche's sweep is the evidence that
run-root validity and these fixtures are independent.

## Options put to the operator

1. Approve regenerating the two fixture baselines. D2b lands; the model
   is told the contract; D1a (the wire contract still saying "exactly")
   is fixed in the same change, paying the cost once.
2. Approve extending `CapabilityTransitionV1` with a denial detail.
   D2a lands; the record explains its own refusals. Heavier: a
   capability-state digest change.
3. Both.
4. Neither — leave D2 parked and the sandbox channel unusable in
   practice, since a model cannot satisfy a contract it is never shown.
