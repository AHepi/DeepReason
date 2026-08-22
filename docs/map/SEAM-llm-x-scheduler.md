<!-- DR-SEAM-llm-x-scheduler -->
Verified-at: 5e0d5bab
Verify: python tools/docs_verify.py
Owns: src/deepreason/controller.py, src/deepreason/llm/firewall.py
Sides: DR-SUB-llm, DR-SUB-scheduler
Sweep: max_tokens && EndpointLease|adapter\.leases|_lease_ceiling

# llm x scheduler — the allocation controller and the route lease

**Scope, stated up front.** This document covers ONE agreement between the two
sides: the allocation controller's authority to retune a seat's completion cap
mid-run, against the route firewall's authority to refuse a mutated lease. The
rest of the llm x scheduler traffic — dispatch, packs, budgets — is not written
up here. `DR-SEAM-scheduler-x-workflow` covers the transaction bracket around a
provider call; `DR-CON-packs-and-token-economy` covers prompt construction.

It exists because the pair terminated a live run. Before
`experiments/2026-08-22-fix-route-lease-maxtokens/`, nothing anywhere said how
these two components agree, and each was independently correct while their
conjunction killed run
`40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c` at cycle 2
of 24. Per `SCHEMA.md`'s rule 6 the seam is written for RISK rather than for
measured coupling: the pair sits at zero on the import metric and still cost a
run.

## The agreement

The controller owns EFFICIENCY and the firewall owns IDENTITY, and the one
field they both touch is `max_tokens`.

The controller promises never to propose or apply a completion cap the firewall
would refuse. Concretely: where a seat's route declares `context_window_tokens`
— a QUALIFIED route, one whose capacity the qualification battery certified —
the leased `max_tokens` is the controller's ceiling, and it calibrates at or
below it. Where a route declares no capacity, no ceiling applies and the
controller keeps the static envelope's latitude, which is what lets a too-small
legacy cap widen under a truncation signal.

The firewall promises in return to admit exactly that. On a qualified route
`EndpointLease.verify` binds `max_tokens` as a CEILING, not an identity: a cap
at or below the leased allowance is inside what qualification certified and is
admitted whoever set it; a cap above it escapes the allowance and is refused.
Every OTHER leased field — model, base_url, provider, family, reasoning,
temperature, output mode and mechanism, logprobs, and `context_window_tokens`
itself — remains an exact equality. `timeout_s` is checked at all only through
the same process-health licence.

**The dependency arrow is absent in both directions, and that is the
agreement's shape rather than an oversight.** `controller.py` imports nothing
from `deepreason.llm`; it reaches the leases duck-typed, through
`self.adapter.leases`, and reads only `route.context_window_tokens` and
`route.max_tokens` off what it finds. `llm/` imports nothing from the
scheduler package at all. So no import graph and no coupling metric can see
this pair — which is precisely why it needed a written seam before anything
else told a reader it existed.
`check: grep -q "getattr(self.adapter, \"leases\"" src/deepreason/controller.py && ! grep -q "deepreason\.llm" src/deepreason/controller.py && grep -q "class EndpointLease" src/deepreason/llm/firewall.py && ! grep -rq "deepreason\.scheduler" --include=*.py src/deepreason/llm/`

## Where it is expressed

| Site | File | Symbol | What it enforces |
|---|---|---|---|
| The contract | `llm/firewall.py` | `EndpointLease.verify`, the `context_window_tokens is not None` branch after the equality loop | a qualified route's `max_tokens` binds as a ceiling; above it is `ROUTE_LEASE_MISMATCH`, at or below it is admitted |
| The identity set | `llm/firewall.py` | `EndpointLease.verify`, the `optional` mapping | every other leased field stays an exact equality; relaxing one field relaxed one field |
| Re-check point | `llm/adapter.py` | `lease.verify(endpoint)` immediately before each provider request, repairs included | a mid-call mutation is caught at the next dispatch, not at the next run |
| The licence, proposed | `controller.py` | `Controller._propose`, the widen branch | the emitted policy artifact states the cap the seat actually got, so the record does not misdescribe its own effect |
| The licence, applied | `controller.py` | `Controller._apply_cap` | the single chokepoint every application passes through — `step`, the fail-static revert, and rehydration of a policy an older version logged |
| The ceiling itself | `controller.py` | `Controller._lease_ceiling` | reads the seat's own lease; returns `None` for an unqualified route, which is what keeps legacy widening lawful |
| The barrier, unchanged | `controller.py` | `cap_envelope` | deliberately NOT the ceiling's home: `invariants.py` re-derives this function to decide what a logged policy authorized, and that is a frozen surface |

`check: python -m pytest tests/test_route_lease_maxtokens_tuning.py -q`

## Invariants

- `DR-INV-signal-contract` — allocation touches EFFICIENCY, NEVER EVIDENCE.
  The ceiling is an efficiency bound and writes no status, warrant or edge.
- `DR-INV-frozen-surfaces` — surface 3 (replay-validation record formats).
  `cap_envelope` is shared with `invariants.py`, so the ceiling lives beside it
  rather than inside it. The bound the controller applies is a SUBSET of the
  envelope replay validation re-derives, so every value the controller can emit
  stays authorizable and no steered run can fail to verify.
`check: grep -q "def _lease_ceiling" src/deepreason/controller.py && python -c "import inspect; from deepreason.controller import cap_envelope; src = inspect.getsource(cap_envelope); assert 'context_window_tokens' not in src, 'the lease ceiling leaked into the shared derivation'; assert 'lease' not in src, 'the lease leaked into the shared derivation'" && grep -q "from deepreason.controller import cap_envelope" src/deepreason/invariants.py`

## Where to change what

| To do this | Edit | Test |
|---|---|---|
| change which lease fields are frozen for identity | `llm/firewall.py`, the `optional` mapping in `EndpointLease.verify` | `tests/test_model_firewall.py`, `tests/test_route_lease_maxtokens_tuning.py` |
| change what a qualified route bounds | `llm/firewall.py`, the ceiling branch, AND `Controller._lease_ceiling` — both, in one commit, or they disagree again | `tests/test_route_lease_maxtokens_tuning.py`, `tests/test_v6_request_envelope.py` |
| change the controller's envelope shape | `controller.py`, `ENVELOPES` / `cap_envelope` | `tests/test_controller.py`, and `tests/test_v6_controller3_replay_verification.py` because replay validation re-derives it |
| add a knob the controller may move | `DR-REC-revise-allocation-policy` | — |

## Traps

- **Two components can each be lawful and still terminate a run together.**
  In reach-rich epoch 2 (run `40e713b3…`, `log.jsonl` seq 442 then 577) the
  controller settled the conjecturer seat from its leased 32768 to
  `round(32768 / 1.6) = 20480` after three spotless windows — inside its
  envelope, past its dwell, emitted as a replayable policy artifact — and the
  firewall, which then bound `max_tokens` for EQUALITY on any route declaring
  `context_window_tokens`, refused the next dispatch. `state=failed`,
  `stop_reason=operational_failure`, cycle 2 of 24. Six lines above the
  offending conditional, the same function's comment asserted the opposite
  rule, so the contract and the licence had been contradicting each other in
  writing since the branch was added. FIXED 2026-08-22 by
  `experiments/2026-08-22-fix-route-lease-maxtokens/`: the contract became a
  ceiling and the licence gained one, in the same commit, and the comment was
  corrected with them. Epoch 1 emitted the byte-identical policy artifact at
  its own seq 352 and died of an unrelated repair exhaustion first — the tune
  is deterministic, so which of two deaths arrives first is not evidence about
  either.
- **Neither side of this seam is reachable by an import grep.** Looking for
  the controller's dependence on the firewall finds nothing, because there is
  none: the leases arrive duck-typed on the adapter. A change that "cannot
  affect the firewall because nothing imports it" is exactly the reasoning
  that shipped the trap above.
- **The ceiling is qualification-bound, not a blanket freeze on widening.**
  An unqualified route must still let the controller widen a cap past its
  configured value under persistent truncation; making `_lease_ceiling`
  unconditional breaks that and is caught by
  `test_an_unqualified_seat_may_still_widen_past_its_configured_cap`.
- **A firewall refusal is recorded under `controller.TRANSPORT_DROP_TAG`.**
  `Scheduler._drop` tags every dropped call `dropped-call`, which is the same
  signal the controller reads to LENGTHEN the transport timeout. After the fix
  no lawful tune produces such a refusal, so nothing acts on it; if a future
  change reopens a path where a run survives a lease refusal, the controller
  will answer a lease violation by widening a wait. Parked, not fixed
  (`experiments/2026-08-22-fix-route-lease-maxtokens/FIX.md`).
