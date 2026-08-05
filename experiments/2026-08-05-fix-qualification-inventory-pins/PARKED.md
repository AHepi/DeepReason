# Parked — noticed during the T1 tranche, not done

## V1 — `continue_run` over MCP no longer returns an ERROR for a completed non-resumable run (BLOCKS the end state; a different defect)

With the inventory pins derived, the tool order corrected and typed
failures now reporting, the smoke advances to `STAGE_CONTINUATION_REJECTION`
and fails there. The traceback — visible only because of this session's
reporting work — names the exact line:

    --- typed failure (continuation_rejection/assertion_failed) ---
      File "<redacted>/scripts/wheel_operational_smoke.py", line 3393, in main
        rejected_continuation = first_client.tool_error(
      File "<redacted>/scripts/wheel_operational_smoke.py", line 1894, in tool_error
        raise OperationalSmokeFailure(

`MCPClient.tool_error` requires the response to BE an MCP error:

    is_error, text = self._response_text(response, stage=stage)
    if not is_error:
        raise OperationalSmokeFailure(stage=stage, failure_kind=FAILURE_ASSERTION)

The smoke calls `continue_run` on a run it has just driven to a
completed, non-resumable terminal state and expects the facade to refuse
with `CONTINUE_TYPED_STOP_REQUIRED` (see `_assert_non_resumable_rejection`,
which accepts exactly `"CONTINUE_TYPED_STOP_REQUIRED"` or
`"ValueError: CONTINUE_TYPED_STOP_REQUIRED"`). The call returned a
NON-error response instead, so the refusal never reached the assertion
that inspects its text.

**Why this is not T1's defect.** T1's goal named one question — what
changed in the contract-pair inventory, and is it correct — and answered
it: 14 -> 15 pairs plus a re-exercise allowance, both deliberate, no
`src/` change owed. This failure is at a different stage, has a
different cause, and lives on the `continue_run` MCP surface. Chasing it
here would be diagnosing a second cause inside a one-goal tranche, which
is the thing the workflow exists to prevent, and I said in the preceding
report that the next surfaced failure would be reported rather than
chained.

**What the next tranche must decide first**, because the two readings
need different fixes:

1. **Product regression** — `continue_run` should still refuse a
   completed non-resumable run and no longer does, or no longer does so
   as an ERROR. Fix `src/`; frozen surfaces are in play (the refusal is
   part of the typed continuation contract, `DR-CON-run-identity`).
2. **Surface shape change** — the refusal is still made but now returns
   as a structured non-error RESULT rather than an MCP error, in which
   case the smoke's `tool_error` expectation is the stale reader and the
   fix is in `scripts/`.

Neither is established. Distinguishing them takes one measurement: call
`continue_run` over MCP against a completed root and read the response's
`isError` flag and body. The smoke is payload-free by design so it
cannot show the body; a small manual MCP client against a retained
`--keep` run will.

**Standing caution for that tranche**: the operational smoke has never
run end to end in this container, so every stage beyond
`continuation_rejection` is still unexercised and may hold its own
staleness. Reaching `exit 0` may take more than one more fix, and each
should be diagnosed on its own evidence rather than assumed to share a
cause with this one.

## V2 — the same-commit pin rule now has a demonstrated failure mode

`EXPECTED_MCP_TOOLS` is a `set` in `wheel_smoke.py` and an ordered
`tuple` in `wheel_operational_smoke.py`. Updating "the pin" in both
files by appending was correct for one and wrong for the other, and the
set-based instrument structurally could not detect the error. Two
instruments pinning the same surface with different comparison semantics
is a trap: the weaker one gives false assurance that the pin was updated
correctly.

Recorded, not fixed — S2 (duplicate MCP pins across both smokes) already
proposes de-duplicating them into one shared definition, which would
dissolve this too.

## V3 — carried, still parked

U1 (the second parallel-load flake — the operator kept it parked
explicitly), U3 (my own gate-measurement discipline), T3 (dead
`_provider_server`/`ProviderState`), T4 (`_unused_loopback_port`'s
bind-then-release race), S2, S3, P1a, P1b, P1e, P7.
