# FIX — the reservation is the authority; the adapter spends what was booked

Follows `DIAGNOSIS.md` (one cause: the completion cap is computed twice, by two
different expressions) and `REPRO.md` (the divergence, offline, no provider).

## The mechanism, in one sentence

For an authorized dispatch the completion cap of record is
`reservation_record.completion_bound_tokens` — the number the workflow already
booked and already durably recorded — and the adapter **consumes** it instead of
recomputing a second cap from the live endpoint.

## Why this discharges BOTH obligations with one change

The operator's brief says two obligations, one mechanism. This is the mechanism,
and the reason it covers obligation (2) is not a coincidence:

**(1) ONE AUTHORITY.** After the change there is exactly one cap per dispatch. It
is computed once, at `preview_request`, by one named helper; the workflow books
it; the adapter reads it back off the reservation. There is no second
computation left to disagree with the first. This is the E26 shape applied at
the call boundary — parity by construction, not parity by agreement.

**(2) OBSERVABILITY.** The guard's three inputs become, all of them, quantities
that are already durable typed records:

| the guard compares | where the record already carries it |
|---|---|
| `reservation.amount` | `TokenReservationV2.reserved_tokens` |
| `conservative_prompt_bound(request)` | `TokenReservationV2.prompt_bound_tokens`, pinned to the dispatched bytes by `verify_dispatch` |
| the completion cap | `TokenReservationV2.completion_bound_tokens` |

Nothing new has to be stored, because the fix replaces an *unrecorded computed
value* with a *recorded booked value*. A future disagreement is diagnosable from
the root alone — by construction, not by adding a field.

## What changes

Three edits in `src/deepreason/llm/adapter.py`, plus a diagnostic on the
refusal path.

1. **One definition of the cap.** Extract `preview_request`'s expression into a
   private helper:

       def _completion_cap(self, endpoint, lease) -> int:
           """The completion envelope one dispatch may book and spend."""

   `preview_request` returns `self._completion_cap(endpoint, lease)`. The
   expression itself is unchanged — a route declaring qualified capacity binds
   its ceiling, which is the only value stable across the booking window and the
   only one safe against a controller *raising* a cap between issue and
   dispatch. `preview_request` was right; `call` was wrong.

2. **The adapter consumes the booked cap.** In `call`:

       transport_limits = {
           "max_tokens": (
               dispatch_authorization.reservation_record.completion_bound_tokens
               if dispatch_authorization is not None
               else self._completion_cap(endpoint, lease)
           ),
           "timeout_s": ...,
       }

   The unauthorized path books and records through the same helper, so the two
   paths cannot drift either.

3. **The guard stays, and becomes an identity.** Not relaxed — the operator's
   constraint forbids a tolerance window, and nothing here widens it. It now
   compares `reservation.amount` against
   `conservative_prompt_bound(request) + reservation_record.completion_bound_tokens`,
   which `TokenReservationV2`'s own `_bound_is_exact` validator already pins to
   equality. It can therefore fail only if the live `Reservation` and its
   recorded `TokenReservationV2` disagree — genuine corruption, never drift.

4. **If it ever does fire, it says what it saw.** On the refusal path, write a
   diagnostic blob carrying both sides and their inputs — booked
   `prompt_bound`/`completion_bound`/`reserved`, the recomputed bound, the
   rendered request's length and digest, and the live `endpoint.max_tokens` at
   that instant — and attach `_spend(attempt)` to the exception the way every
   other pre-dispatch refusal in this method already does.

## What deliberately does NOT change

- **The wire.** `transport_limits` feeds the attempt trace and the bound check;
  the provider cap comes from `endpoint.complete`'s own `self.max_tokens`
  (`llm/endpoints.py:335`). No dispatch sends a different number after this
  change than before it.
- **Fails closed.** Booking the ceiling is a conservative UPPER bound on what
  the seat can spend under its lease, exactly as `conservative_prompt_bound`
  over-counts on the prompt side. A controller narrowing spends less than
  booked; a controller raising is bounded by `Controller._lease_ceiling` at the
  same ceiling. Neither can spend past the booking.
- **Replay validation.** `invariants.py:3988-4004` admits
  `attempt.max_tokens ∈ {route.max_tokens} ∪ authorized controller caps`. The
  booked cap is `route.max_tokens` for a qualified route and an
  already-authorized policy value otherwise, so it stays inside `allowed_caps`
  and no verdict moves. **No frozen-surface contact, and no operator grant is
  requested by this tranche.**
- **`scripts/`.** Untouched; a parallel window owns the soak instrument there.
- **P5-epoch3** (whether a token-bounded run should reach a resumable terminal)
  stays parked. This tranche does not touch `lifecycle.py`.

## A consequence worth stating plainly

`attempt.max_tokens` currently records the *live* endpoint cap. After this
change it records the *booked envelope*. That is what `LLMAttempt`'s own
committed comment already says it should be — "max_tokens stays the envelope the
route or a logged controller policy AUTHORIZED, because that is the value replay
validation admits and the token reservation booked" (`ontology/event.py:106-110`)
— so the change restores a documented invariant rather than inventing one. On
every run where no controller moves mid-call the recorded value is unchanged.

## Tests, mutation-proven

Each is shown RED on the unfixed tree before it is committed green.

1. `test_settled_cap_below_the_route_ceiling_still_dispatches` — the repro's
   scenario, now expecting a *successful* call rather than
   `WorkflowAuthorizationError`.
2. `test_attempt3_shape_books_and_spends_one_cap` — attempt 3's exact numbers
   (ceiling 32768, window 131072, settled 20480); asserts the booked cap, the
   recorded attempt cap and the guard's own arithmetic are one number.
3. `test_preview_and_dispatch_share_one_cap_definition` — a source-shape check
   that `call` does not recompute a cap from the endpoint under an
   authorization. This is the mutation guard: reintroducing the second
   expression fails it.
4. `test_bound_refusal_records_both_sides` — forces a corrupted bundle and
   asserts the diagnostic blob carries both bounds, so the residual failure is
   diagnosable.

Ring while iterating: `tests/test_adapter_workflow_authorization_c2.py`,
`tests/test_v6_global_dispatch_guard.py`,
`tests/test_v6_contract_schema_repair_runtime.py`,
`tests/test_v6_bridge_transactions.py`. Full gate at the boundary.

## Map moves in the same commits

- `docs/map/SEAM-llm-x-workflow.md`: the "Meter ownership" row ("the adapter
  only checks the arithmetic"); the bound-equality paragraph that admits **no
  test constructs a disagreeing reservation amount** — now one does; the "What
  breaks first" line that glosses this error as *"the prompt changed after
  issue"*, which `DIAGNOSIS.md` Step 1 shows it cannot be; and a new `Traps`
  entry naming run `bb0455384ea09b5b…`.
- `docs/ERRATA.md`: the three committed statements that attribute this failure
  to the prompt, and P6-epoch3's false "not a controller cap re-tune"
  elimination.
