# Parked — found while specifying the two-call seat protocol, not fixed here

P1 — the extraction leg cannot ride a REPAIR authorization bundle.
WHAT: `V6PatchRepairSession` issues one authorization per repair attempt; the
split protocol deliberately refuses to run on those bundles (SPEC.md QO2
option (a)'s guard), so a repair turn that burns its cap on hidden reasoning
still dies the old way. Not requested by this tranche's R1-R11.
READY-TO-SEND PROMPT:

    Route: dr-change-orchestrator.
    Goal (one): extend the two-call seat protocol to v6 repair attempts, so a
    repair turn that burns its completion cap on hidden reasoning yields a
    patch instead of a typed failure.
    Evidence pointers: experiments/2026-08-22-change-two-call-seat-protocol/
    SPEC.md QO2 and A3; src/deepreason/llm/adapter.py's transactional repair
    guard ("transactional repair requires a new authorization bundle");
    src/deepreason/workflow/repair_transaction.py.
    End state: a repair attempt splits under the same ceiling law as attempt 0,
    with the same typed notices; offline regression mutation-proven; full gate
    0 failed.

P2 — the provider's reasoning payload is discarded on every NON-split call.
WHAT: `OpenAICompatEndpoint` reads `message.content` only. When a reasoning
model burns its cap and emits nothing, the hidden trace it did produce is
thrown away before any diagnostic sees it. This tranche captures it
(`last_reasoning_trace`, SPEC.md S2) but only the split path consumes it; an
ordinary failing call still stores no trace in its diagnostic blob.
READY-TO-SEND PROMPT:

    Route: deepreason-orchestrator (defect-shaped: evidence is being dropped
    from the typed record).
    Goal (one): a completion that dies with null or truncated content records
    the provider's reasoning payload in its diagnostic blob, so the blob-first
    diagnosis rule has something to read.
    Evidence pointers: src/deepreason/llm/endpoints.py:400-403 (the null-content
    EndpointError); experiments/2026-08-22-change-two-call-seat-protocol/SPEC.md
    M10; CLAUDE.md's "READ THE DIAGNOSTIC BLOB before theorising" invariant.
    End state: the diagnostic blob for a null/truncated completion carries the
    reasoning payload when the provider returned one; regression pinned; full
    gate 0 failed.
