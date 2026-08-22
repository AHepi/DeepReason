# Fix: on a qualified route the leased `max_tokens` binds as a CEILING, and the controller never calibrates past that ceiling

Guarantee restored: **no lawful move by the allocation controller can be
refused by the route firewall** — the controller may settle a seat's completion
cap down inside its qualified allowance and may never raise it above the
allowance, and the firewall admits exactly that and nothing more.

## Direction chosen, and why

`dr-propose-fix`'s brief offered two roads. The record chooses (b), corrected
from "stop checking `max_tokens`" to "bind it as a ceiling", and pairs it with
the substance of (a) on the controller side. Four reasons, in descending
weight:

1. **The frozen replay validator already licences controller-tuned
   `max_tokens`, and it is not mine to change.** `invariants.py:3986-4004`
   admits an attempt whose `max_tokens` differs from `route.max_tokens`
   whenever "a prior logged controller policy authorized that exact process
   setting", re-deriving the barrier through `controller.cap_envelope`. That is
   frozen surface 3. The firewall's equality check contradicts it directly:
   one instrument of this system says the tune is legitimate evidence, the
   other kills the run for it. The half that can move is the firewall.
2. **`INV-signal-contract.md` makes the licence a FROZEN operator law.**
   "Allocation touches EFFICIENCY, NEVER EVIDENCE" is the strictest row of the
   signal contract. Settling a wasteful cap after three spotless windows is
   the efficiency function itself; forbidding it on qualified routes would
   disable allocation for the only route shape live runs use, which is not a
   fix but an amputation.
3. **The strict branch is stricter than its own purpose.** Its comment says
   "qualified capacity binds the completion side of the envelope", and the
   gate test that pins it is named
   `test_runtime_endpoint_cannot_widen_frozen_capacity` and moves `32 -> 64`.
   Its purpose is to stop a runtime endpoint ESCAPING the qualified allowance.
   An equality is a strictly stronger rule than that purpose requires, and the
   surplus strictness — refusing values *below* the allowance — is the entire
   defect. A ceiling serves the purpose exactly and refuses the escape still.
4. **Direction (a) read literally cannot be implemented.** The firewall line as
   written is an equality: "clamp within the leased value" does not survive it,
   because only the leased value itself passes. (a) therefore reduces to
   "the controller may not tune `max_tokens` on a qualified route at all",
   which contradicts (2) and the function's own comment.

REPRO.md case B forces the second half. Under a ceiling alone, a qualified
route whose leased cap sits below the static envelope maximum (e.g. 3000) still
lets the controller widen to `round(3000 * 1.6) = 4800`, above the lease, and
the next dispatch still dies. GOAL.md's binding constraint — a configuration
that compiles and qualifies must not be terminable mid-run by its own
components' lawful behavior — is met only when the tuner is also bounded.
`cap_envelope`'s own docstring already promises this ("the controller
calibrates inside the operator's own setting and can never move a cap past
it"); the promise is simply false whenever the configured cap is below the
static ceiling. So the controller half is a defect against its own stated
contract, not a new restriction invented here.

## SCOPE REQUEST — stated explicitly before any implementation

This fix **changes the semantics of `EndpointLease.verify`**, which is
route-admission code and frozen-adjacent. Requesting it plainly, per the
tranche brief:

- **What is requested:** for one field (`max_tokens`) on one branch (routes
  declaring `context_window_tokens`), the comparison changes from `!=` to `>`.
  Nothing else about lease verification moves — every other field stays an
  equality, and the unqualified branch is untouched.
- **`route_fingerprint`: zero contact, as the brief requires.** No field of
  `Route` changes, no serialization changes, and `route_fingerprint` is not
  read, written or reordered. Verifiable: the fix touches no line inside that
  function and adds no field to the model it hashes.
- **Frozen surfaces: none touched.** `capabilities/state.py`, `harness.py`,
  replay-validation record formats, manifest schemas and validators, and
  qualification subject digests are all untouched. In particular
  `controller.cap_envelope` — which `invariants.py:3632` re-derives to decide
  what a logged policy authorized — is left **byte-identical**, deliberately:
  narrowing that function would narrow what replay validation authorizes and
  could move a stored verdict. The new ceiling therefore lives beside it, in
  the controller's own apply path, never inside the shared derivation.
- **Direction of the divergence, stated so it is not a hidden risk.** After the
  fix the controller's effective ceiling on a qualified seat is a SUBSET of the
  envelope replay validation re-derives. Every value the controller can emit
  remains inside the validator's authorized set, so no steered run can fail to
  verify. The divergence is one-way and safe by construction; the code says so
  at the site.

## Change sites (exhaustive)

  - `src/deepreason/llm/firewall.py:251-256` — the comment. Rewritten to state
    the rule the code will actually enforce: `timeout_s` is freely
    controller-tunable; `max_tokens` is controller-tunable DOWNWARD, and a
    route declaring `context_window_tokens` binds the leased value as its
    ceiling. This is the "other half's text" the brief requires corrected in
    the same commit.
  - `src/deepreason/llm/firewall.py:270-273` — the conditional. `max_tokens`
    leaves the equality-checked `optional` map and becomes a separate ceiling
    comparison after the equality loop: refuse only when
    `endpoint.max_tokens > route.max_tokens`. The raised message becomes
    `field=max_tokens expected<=<lease> actual=<endpoint>`, which states the
    bound that was actually violated.
  - `src/deepreason/controller.py` — new private `_lease_ceiling(instance)`:
    the largest cap the firewall will admit for that seat, read from
    `adapter.leases`, or `None` on an unqualified route (no
    `context_window_tokens`) or an unleased seat.
  - `src/deepreason/controller.py:429-433` (`_propose`, widen branch) — the
    proposed value is capped at `_lease_ceiling`. Clamped HERE so the emitted
    policy artifact states the value actually applied; clamping only at apply
    time would make the record disagree with the endpoint.
  - `src/deepreason/controller.py:545-552` (`_apply_cap`) — the same ceiling,
    applied at the single chokepoint every application passes through. This is
    what makes the guarantee true in EVERY path rather than the default one:
    `_revert_to_last_accepted` and the rehydration of a policy logged by older
    code both reach the endpoint through here.

## Regression artifact

`tests/test_route_lease_maxtokens_tuning.py`, new, mutation-proven — each
assertion must be shown RED on the unfixed tree before the fix lands:

  1. **The recorded death, offline.** REPRO.md case A, inverted: a qualified
     route (`max_tokens=32768`, `context_window_tokens=131072`), the
     controller's own efficiency step to `20480`, and the next
     `lease.verify(endpoint)` ADMITTED. Docstring names run
     `40e713b30a147dfc1a0f73feb91fa67a493454f6103a452888b8e08713368c4c`.
  2. **The escape still refused.** Same qualified route, `max_tokens` raised
     above the lease by something other than the controller → still
     `ROUTE_LEASE_MISMATCH`, `field=max_tokens`.
  3. **REPRO case B closed at the source.** Qualified route leased at 3000,
     six truncated calls, controller steps → the applied cap is `<= 3000` and
     the next verify is admitted. Proves the tuner, not just the checker.
  4. **The emitted policy tells the truth.** In (3) the logged policy
     artifact's `knobs` value equals the endpoint's `max_tokens` — the record
     and the world agree.
  5. **The unqualified route is untouched.** REPRO case C plus the legacy
     widening (`800 -> 1280`): no ceiling, behavior byte-identical.
  6. **Every other lease field is still an equality.** A qualified route whose
     endpoint mutates `context_window_tokens`, `temperature` or `model` is
     still refused — the ceiling relaxes one field, not the check.

`experiments/2026-08-22-fix-route-lease-maxtokens/repro.py` is re-run after the
fix and its output committed as `repro_after.json`: all three cases
`next_dispatch_refused: false`.

## Existing tests at risk

Every one of these must keep passing **unmodified**; none has a
defect-dependent fixture, and none will be touched:

  - `tests/test_v6_request_envelope.py::test_runtime_endpoint_cannot_widen_frozen_capacity`
    — qualified route, `32 -> 64`. A widening: still above the lease, still
    refused. This is the assertion the ceiling formulation exists to preserve.
  - `tests/test_model_firewall.py::test_endpoint_lease_allows_logged_process_tuning_only`
    — unqualified route, `800 -> 1280`. No ceiling applies; unchanged.
  - `tests/test_controller.py::test_forbidden3_widen_is_clamped_to_envelope_max`
    — `_CapEndpoint` exposes no `context_window_tokens`, so the seat is
    unqualified and the controller must still widen past 800. Unchanged.
  - `tests/test_controller.py::test_controller_does_not_normalize_an_explicit_cap_outside_its_envelope`
    — unqualified, holds an explicit 7000. Unchanged.
  - `tests/test_v6_controller3_replay_verification.py` — qualified route
    (`max_tokens=512`, `context_window_tokens=262144`) but `CONTROLLER=False`
    and the endpoint's cap is never mutated. Unchanged.
  - `tests/test_route_firewall_scheduler.py` — asserts the drop path
    (`RouteFirewallError` → `dropped-call`), which the fix preserves exactly:
    a genuine escape still terminates the run the same typed way.
  - `tests/test_controller_steering_parity.py`,
    `tests/test_allocation_signal_consumption.py` — neither declares
    `context_window_tokens`; both unqualified, unchanged.

## Map documents moving in the same commit

  - `docs/map/SUB-llm.md` — `Traps` entry naming run `40e713b3…`.
  - `docs/map/INV-signal-contract.md` — `Traps` entry for the tuner half, with
    the lease-ceiling rule and a `check:`.
  - `docs/map/CON-seats.md` — the lease's two-tier rule (equality for identity
    fields, ceiling for the qualified completion allowance).
  - `docs/map/SEAM-allocation-x-llm.md` — **new**. GOAL.md recorded the gap:
    the controller that tunes a seat's cap and the firewall that verifies it
    meet with nothing written down, which is a plausible contributing
    condition. Filed with `INDEX.md`'s seam matrix updated.

## Explicitly not changed

  - **`controller.cap_envelope` and `invariants.py`.** The tempting move is to
    pin the envelope ceiling to the configured cap in the one shared
    derivation. Refused: `invariants.py:3632` re-derives that function to
    decide what a logged policy authorized, so narrowing it narrows replay
    validation's authorized set and can move a stored verdict on a frozen
    surface. The ceiling goes in the controller's apply path instead.
  - **The schema-repair machinery** (`llm/repair.py`,
    `workflow/repair_transaction.py`). That is P7-reach, worked by a parallel
    window. Untouched here.
  - **`run-config.yaml`.** Dropping `context_window_tokens` would dodge the
    branch, change the qualification subject digest and the run identity, and
    hide the disagreement. PARKED.md P9-reach forbids it by name.
  - **The `dropped-call` tag on a firewall refusal.** DIAGNOSIS.md notes that
    a lease violation is recorded under `controller.TRANSPORT_DROP_TAG`, the
    signal that makes the controller lengthen a timeout. After this fix no
    lawful tune produces such a refusal, so the mis-tagging has no live path
    left. Parked rather than fixed: it is a second mechanism, and this tranche
    has one goal.

## Estimated diff

  - production: ~42 lines across 2 files (`llm/firewall.py` ~14,
    `controller.py` ~28) — well inside the 150-line budget.
  - mandated companions: ~115 lines of new regression test, ~75 lines of map
    (three `Traps` entries plus one new seam document).

Stated plainly rather than buried: the **total** diff lands near 230 lines,
above GOAL.md's 150. The budget exists to catch a change growing beyond its
goal, and the change itself has not — it is two files and one semantic
comparison. The overage is entirely the regression suite and the map, both
mandatory and both required by the brief. Proceeding; if the operator reads
the budget as a hard cap on the total, the split above is where to cut.

## Approval gate

Class `defect` (GOAL.md). No frozen surface touched. Production diff 42 lines.
The one scope request — lease-verification semantics — is stated above in full
before any code moves, as the brief requires. Proceeding to
`dr-implement-fix`.
