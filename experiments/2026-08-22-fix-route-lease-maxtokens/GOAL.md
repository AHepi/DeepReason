# Goal: a route declaring `context_window_tokens` must survive its own controller's lawful `max_tokens` tuning
Class: defect

Observed: the epoch-2 live run of `experiments/2026-08-22-live-reach-rich-run`
(run id `40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c`)
terminated at cycle 2 of 24 with `state=failed`,
`stop_reason=operational_failure`, `error_type=RouteFirewallError`, message
`ROUTE_LEASE_MISMATCH role='conjecturer' seat=0 field=max_tokens
expected=32768 actual=20480`
(`run/run-status.json`, `run/run-result.json`,
`run/objects/workflow-run-terminal-result-draft-v1/6a26a525…`,
`run/log.jsonl` seq 577 `Measure ["dropped-call", "ROUTE_LEASE_MISMATCH …"]`
followed by seq 578 `Measure ["run-stop", …]`). Parked as P9-reach in that
tranche's `PARKED.md`.

Success criterion (machine-decidable):

    python -m pytest tests/test_route_lease_maxtokens_tuning.py -q
    # a new regression file that constructs the recorded mismatch offline
    # (qualified route: context_window_tokens set, max_tokens 32768; the
    # controller's own lawful narrowing to 20480) and asserts the run is not
    # terminable by it; RED on the unfixed tree, GREEN after the fix.

    python -m pytest tests/ -q -n 4
    # 0 failed (baseline at 32492cdb8: 3820 passed, 0 failed)

    python tools/docs_verify.py
    # no new failures beyond the 3 pre-existing shallow-clone failures

In scope:
  - `src/deepreason/llm/firewall.py` (`EndpointLease.verify` — the contract)
  - `src/deepreason/controller.py` (`cap_envelope` / `_propose` — the licence)
  - `docs/map/CON-seats.md`, `docs/map/INV-signal-contract.md`,
    `docs/map/SUB-llm.md` (Traps + the seam text; the map moves in the same
    commit)

NOT in scope: the schema-repair machinery (`llm/repair.py`,
`workflow/repair_transaction.py`) — that is P7-reach, worked by a parallel
window. Also not in scope: `run-config.yaml`'s `context_window_tokens: 131072`
(dropping it would dodge the strict branch, change the qualification subject
digest and the run identity, and hide the disagreement — PARKED.md P9-reach
forbids it explicitly).

Budget: <=150 changed lines, 1 commit (plus phase-boundary artifact commits),
~3 hours
Stop conditions inherited from orchestrator: yes

## Map preflight (resolved ids, recorded here so every later phase starts here)

| id | document | why it is in the work |
|---|---|---|
| `DR-SUB-llm` | `docs/map/SUB-llm.md` | owns `llm/firewall.py`, the route firewall and `EndpointLease` |
| `DR-CON-seats` | `docs/map/CON-seats.md` | owns how a role becomes a provider request: `select_lease`, `EndpointLease` |
| `DR-INV-signal-contract` | `docs/map/INV-signal-contract.md` | owns the allocation controller, its envelopes, and the FROZEN row "allocation touches EFFICIENCY, NEVER EVIDENCE" |
| `DR-INV-frozen-surfaces` | `docs/map/INV-frozen-surfaces.md` | read before designing; see the ruling below |

**Seam gap, recorded as a finding not a blocker.** There is no
`SEAM-allocation-x-llm.md` (nor any allocation subsystem document); `INDEX.md`'s
matrix lists neither pair. The two sides of this defect — the allocation
controller that tunes `endpoint.max_tokens` and the route firewall that verifies
it — therefore meet with nothing written down about how they meet. That absence
is a plausible contributing condition and closing it is part of this tranche.

**Frozen-surface ruling, from `INV-frozen-surfaces.md` read before design.**
Surface 3 (replay-validation record formats) and the frozen-adjacent
`route_fingerprint` serialization are the two that sit near this work.
`route_fingerprint` is untouched: this tranche changes no field of `Route` and
no serialization, only what `EndpointLease.verify` compares. Replay-validation
output is untouched: `invariants.py` already licenses a controller-authorized
`max_tokens` that differs from the route's, and no violation record changes
shape. If the design turns out to need either, it stops at FIX.md and asks.

**Scope request already anticipated.** `EndpointLease.verify` is route-admission
code — frozen-adjacent, per the operator's framing in the tranche brief. FIX.md
must request the scope for touching lease-verification semantics explicitly
before anything is implemented.
