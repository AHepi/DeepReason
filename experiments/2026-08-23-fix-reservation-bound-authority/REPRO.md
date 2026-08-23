# REPRO — the two bounds diverging, offline, with no provider

Two instruments, both committed under `repro/`. Neither contacts a provider;
`MockEndpoint.last_transport_attempts == 0` is asserted, so the refusal
demonstrably happens before the wire.

## 1. `repro/attempt3_census.py <root>` — the record, re-derived

Reads only typed records from the committed
`failed-attempt3-run-bb0455384ea09b5b…` root:

    reservations 50  authorizations 50  provider attempts 49
    authorized-never-dispatched 1

    refused dispatch: role=conjecturer seat=0 contract=conjecturer.turn.v6
      prompt digest matches its reservation: True
      booked  prompt_bound=8333 completion_bound=32768 reserved=41101

    controller policy artifacts: 1
      cycle=2 knobs={'cap:argumentative_critic': 20480, 'cap:conjecturer': 20480}

      reservation.amount (booked, recorded)       = 8333 + 32768 = 41101
      reservation_bound  (dispatch, NOT recorded) = 8333 + 20480 = 28813
      disagreement = 12288 = route ceiling 32768 - settled cap 20480

## 2. `repro/test_repro_bound_divergence.py` — the live seam, offline

Drives the real `preview_request` → `service.issue` → `adapter.call` path
against `MockEndpoint`, in the attempt-3 seat shape: a route declaring
qualified capacity, then the endpoint cap settled below its ceiling exactly as
`Controller._apply_cap` does it.

    python -m pytest experiments/2026-08-23-fix-reservation-bound-authority/repro/ -q
    2 passed

`test_settled_cap_below_the_route_ceiling_kills_the_next_dispatch` prints the
two sides:

      route ceiling                 64
      controller-settled cap        32
      conservative_prompt_bound     7796  (identical on both sides)
      booked   reservation.amount = 7796 + 64 = 7860
      dispatch reservation_bound  = 7796 + 32 = 7828
      disagreement                  32 = 64 - 32

`test_attempt3_exact_numbers_reproduce_the_12288_disagreement` repeats it with
that run's own numbers — ceiling 32768, context window 131072, settled cap
20480 — and asserts the disagreement is **12288**, the value the census derives
from the committed root.

Both raise `WorkflowAuthorizationError("transactional reservation bound differs
from rendered request")`, attempt 3's verbatim message.

## What the reproduction settles

- The divergence needs **no provider, no network, and no live run**. It is
  arithmetic between two expressions.
- It needs **no prompt difference**. `conservative_prompt_bound` is printed and
  asserted identical on both sides; the pack is a faithful stand-in for attempt
  3's rendering (operator-authored `predicate:` criteria, attached-evidence
  manifest, supplements) and its *bytes are immaterial* — which is the finding,
  not a shortcut. Only the pack's length enters the bound, and it enters both
  sides equally.
- It needs only a route declaring `context_window_tokens` and a controller
  doing the one thing `ERRATA` E43 exists to permit.

## Why no existing test caught it

`DR-SEAM-llm-x-workflow` already says so in its own words: *"**NO TEST
constructs an `AuthorizedDispatch` whose reservation amount disagrees with the
rendered request**, so the bound-equality refusal itself is held only by the
source-shape check below plus the proof that both sides compute the bound from
the same `conservative_prompt_bound`."*

The proof it rests on is true of the prompt term and false of the cap term. And
every v6 fixture builds its `MockEndpoint` with `max_tokens=route.max_tokens`,
so the two expressions coincide in every test in the suite.
