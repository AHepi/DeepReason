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

## V4 — T2's human diagnostic channel has no destination on a failing run

T2 delivered three concealment fixes by writing evidence to stderr
beside the typed record. Two of them (timeout, assertion) are committed
and green; the third — typed `OperationalSmokeFailure`, added in
`228b2ce6` — is reverted at `31480e5f`, because stderr on a failing run
is not free space.

`tests/test_wheel_operational.py` enforces the reservation in three
tests: `_annotation_record` does
`json.loads(stderr.strip().removeprefix(prefix))`, which only parses if
stderr is EXACTLY the annotation, and each test asserts
`captured.out == ""`. Prepending a diagnostic block produced
`json.decoder.JSONDecodeError` in all three. `FIX.md` did not predict
those tests moving, so the fix was wrong as implemented; weakening the
assertions was not available.

**Why the two surviving diagnostics are green and this one is not.** No
test drives `main()` into the timeout or assertion handler on a run
whose stderr is then parsed, so they sit in the same reserved stream
untested rather than proven safe. That asymmetry is luck, not design.

**A hazard measured, and it did NOT fire.** `_redact` scrubs exactly two
values — the repo path and `TEST_CREDENTIAL` — so a traceback channel
can only be as clean as the source lines it renders, and it cannot scrub
payload it cannot name. Probed on 3.11: `format_exc` emits only the
RAISING line of each frame, so the sentinel literals in the three tests
(which sit on non-raising lines, or on continuation lines of a
multi-line call that renders as its first line only) never appeared.
Recorded as unproven-against-payload, not as a demonstrated leak.

**What the next tranche must decide**: where a human-facing channel
belongs when both public streams are reserved. The candidate that costs
nothing on the contract is a file under `temp_root`, which the `--keep`
fix already retains on failure — the record stays payload-free on the
wire, and the evidence is on disk for whoever reads the run. That is a
proposal, not a decision; it revises T2's delivered design and is the
operator's call.

**Consequence for V1 above**: its traceback evidence was captured while
`228b2ce6` was in the tree and is a real measurement, but the mechanism
that produced it no longer exists. Re-deriving it after the revert needs
either this channel restored somewhere legal, or a direct
`python -c` reproduction against a `--keep` run.

## V3 — carried, still parked

U1 (the second parallel-load flake — the operator kept it parked
explicitly), U3 (my own gate-measurement discipline), T3 (dead
`_provider_server`/`ProviderState`), T4 (`_unused_loopback_port`'s
bind-then-release race), S2, S3, P1a, P1b, P1e, P7.
