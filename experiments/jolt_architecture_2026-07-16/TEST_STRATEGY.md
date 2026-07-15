# Test strategy

The central recommendation is falsified if model prose changes a route, budget, phase, retry bound, stop decision or formal status without a typed logged transition; if replay differs; if scratch becomes authoritative; or if different clients/providers produce different control transitions from the same canonical state and policy.

Required cases include phase-changing prompt injection; output selecting another route; malformed output; local repair and exhaustion; missing/conflicting evidence; interruption and continuation; historical replay; v1-v3 manifest compatibility; scratch attempting formal promotion; bridge composition introducing a fact absent from the ledger; CLI/MCP equivalence; and provider substitution under the same state machine. Assert event sequences, route leases, budget deltas, state hashes, retry counts, formal status and claim references—not merely schema validity.

Add reducer property tests, event-prefix replay at every transition, mutation tests that remove event emissions, capability-denial tests for forbidden controller fields, crash/restart tests between every write, and shadow-run differentials against legacy scheduler traces. The bridge regression suite must include the two observed failures: a contract label used as an event handle and a formal-artifact handle used in `scratch_handles`.

The pinned checkout's targeted existing suite passed: 41 tests in 0.89 seconds.
