# DIAGNOSIS — the guard cannot fire on the prompt, only on the cap

Tranche: `experiments/2026-08-23-fix-reservation-bound-authority/` (GOAL.md).
Motivating run: `bb0455384ea09b5b72664a4f6f3f0cb7a5ac227c00a93976e5c8c31873ca84f4`,
retired as `failed-attempt3-run-bb0455384ea09b5b…` under
`experiments/2026-08-22-change-epoch3-second-lineage/`.

    state            failed
    stop_reason      operational_failure
    error_type       WorkflowAuthorizationError
    error            transactional reservation bound differs from rendered request
    cycles completed 2 of 4
    verify_root      0 violations

## The cause, in one sentence

The two sides of the guard differ **only in their completion-cap term**, because
`preview_request` and `call` compute that cap with two structurally different
expressions over the same inputs; the prompt term is provably identical on both
sides, and the dispatch-side cap is the one quantity the record never stores.

## Step 1 — the prompt term cannot differ. This is proven, not assumed.

The guard at `llm/adapter.py:1388-1401` compares

    reservation.amount    = conservative_prompt_bound(<service prompt>) + <booked cap>
    reservation_bound     = conservative_prompt_bound(request)          + <dispatch cap>

`reservation.amount` is built by `TokenMeter.reserve` (`llm/budget.py:130-158`)
from `prompt_text=prompt`, with no tokenizer count supplied by
`transaction_service.reserve_dispatch`, so its prompt term is exactly
`conservative_prompt_bound(prompt)`.

`request` is `turn.request` (`adapter.py:1340`). For `attempt == 0`,
`BoundedRepairSession.turn` returns `self.initial_request` **unchanged**
(`llm/repair.py:1725-1729`), and `initial_request` is the `prompt` that
`_render_request` produced (`adapter.py:1281`). Any `attempt != 0` is refused
earlier under an authorization — "transactional repair requires a new
authorization bundle" (`adapter.py:1392-1396`). So on every path that can reach
the guard, `request is` the adapter's rendered `prompt`.

And the adapter's rendered prompt is already pinned byte-for-byte to the
service's prompt **before** the guard runs. At `adapter.py:1205-1218`, ahead of
the reservation block, `call` computes
`prompt_sha256 = sha256(prompt)` and passes it to
`DispatchAuthorizationBundleV1.verify_dispatch`, which compares the whole
six-field tuple — `prompt_sha256` included — and raises
`ValueError("dispatch differs from its authorization bundle")` on any
difference (`workflow/transaction.py:336-362`).

> Equal digests ⇒ equal bytes ⇒ equal length ⇒ equal `conservative_prompt_bound`.
> The prompt term is identical on both sides of the guard, always.

`DR-SEAM-llm-x-workflow`'s own Traps entry states the same mechanism from the
other direction: "Both `preview_request` and `call` render through the same
`_render_request`, so the bundle's `prompt_sha256` matches whatever that helper
produces."

**Therefore the guard can fire on one term and one term only: the cap.**

## Step 2 — the cap is computed twice, by two different expressions

Re-derivable from the committed source:

`check: python -c "import inspect, re, pathlib; from deepreason.llm.adapter import LLMAdapter; p=re.search(r'maximum = \((.*?)\)\n', inspect.getsource(LLMAdapter.preview_request), re.S).group(1); d=re.search(r'transport_limits = \{\n\s+\"max_tokens\": (.*?),\n\s+\"timeout_s\"', pathlib.Path('src/deepreason/llm/adapter.py').read_text(), re.S).group(1); norm=lambda s: ' '.join(s.split()); assert norm(p) != norm(d), 'caps now share one expression'"`

| site | expression |
|---|---|
| `preview_request` (`adapter.py:766-771`) — **booked** | `lease.route.max_tokens` **if** `lease.route.context_window_tokens is not None` **else** `getattr(endpoint, "max_tokens", lease.route.max_tokens)` |
| `call` (`adapter.py:1375-1381`) — **dispatched** | `getattr(endpoint, "max_tokens", lease.route.max_tokens)` |

They are the same function only when `context_window_tokens is None`. When a
route declares qualified capacity they are different functions: the booked side
reads the route **ceiling**, the dispatch side reads the endpoint's **settled**
cap.

Evaluated over identical inputs (`repro/cap_divergence.py`):

| configuration | booked | dispatched | delta |
|---|---|---|---|
| controller settled the seat below its ceiling | 32768 | 20480 | **12288** |
| role spec omits `max_tokens` → endpoint default `None` | 32768 | 0 | **32768** |
| no qualified capacity declared (legacy route) | 20480 | 20480 | 0 |
| caps coincide | 32768 | 32768 | 0 |

## Step 3 — the divergent configuration is LAWFUL, which is why this is a defect and not a misconfiguration

`EndpointLease.verify` binds `max_tokens` as a **ceiling, not an identity**, on
exactly the routes that declare `context_window_tokens`
(`llm/firewall.py:286-293`): `cap <= route.max_tokens` passes. Its own comment
says why — "An equality here would make the controller's own lawful settling of
a wasteful cap terminal mid-run."

That ceiling semantics is recent and deliberate: `docs/ERRATA.md` **E43**
records the 2026-08-22 tranche `experiments/2026-08-22-fix-route-lease-maxtokens`
changing `verify` from equality to ceiling, precisely so a controller narrowing
a seat's cap (32768 → 20480 in reach-rich epoch 2) no longer kills the run.

**E43 made the narrowed cap lawful at the firewall and left the reservation
arithmetic reading the ceiling.** The run that E43 saved from
`ROUTE_LEASE_MISMATCH` is the run this defect now kills with
`WorkflowAuthorizationError`. Same seat, same cap, one layer further in.

Note also `getattr(endpoint, "max_tokens", …)`: `OpenAICompatEndpoint.__init__`
declares `max_tokens: int | None = None` (`llm/endpoints.py:261,275`) and
`_endpoint_from_spec` passes `spec.get("max_tokens")` (`adapter.py:1710`), so the
attribute is **present and `None`** when a role spec omits it. `getattr`'s
default never fires; `int(None or 0)` is `0`. The fallback in that expression is
unreachable for the production endpoint — it is dead in a way that reads as
protective.

## Step 4 — why the record could not settle it, and what exactly is missing

`TokenReservationV2` (`workflow/transaction.py:244-266`) already stores the
**booked** side in full: `prompt_sha256`, `prompt_bound_tokens`,
`completion_bound_tokens`, `reserved_tokens`, with a validator pinning
`reserved = prompt_bound + completion_bound`.

Combined with Step 1 — the prompt bytes being pinned identical — the record
carries *everything the guard compares except one number*: the completion cap
the adapter actually used at dispatch. It is computed inline into a local dict
and never persisted, on the failure path least of all.

So the observability gap is not "the rendered request bytes are unrecoverable"
as P6-epoch3 framed it. The bytes are recoverable in the only sense the guard
needs — their digest is in the bundle and their equality to the service prompt
is already enforced. **The gap is exactly one integer: the dispatch-side cap.**

## What this corrects

Three committed statements attribute this failure to the prompt. Each was
written before Step 1 was established; each earns an `ERRATA` entry rather than
a silent edit:

1. The error message itself — `"transactional reservation bound differs from
   rendered request"` — names the request. It cannot be the request.
2. `DR-SEAM-llm-x-workflow`, "How to change it": `"transactional reservation
   bound differs from rendered request"` (the prompt changed after issue)`.
   The prompt cannot have changed after issue; `verify_dispatch` runs first and
   would have raised a different error.
3. `PARKED.md` P6-epoch3: "the prompt-bound term computed over two different
   strings". The strings are provably one string.

The eliminations P6-epoch3 *did* make hold and are not re-derived here: no
policy artifact carrying a `knobs`/`cap:` entry exists in the log, `max_tokens`
is 32768 across every stored object, and `prompt_sha256` agrees in 50 of 50
reservation/authorization pairs. Step 1 explains why that last one had to agree:
a disagreement there raises a different exception.

Those eliminations also mean the record cannot tell us *which* of the two
divergent configurations attempt 3 was in — a controller-settled cap or an
absent one — because neither leaves a trace. That is the gap, restated as its
own consequence, and it is what obligation (2) closes.

## One cause, named

> `preview_request` and `call` compute the completion cap with two different
> expressions. The bound the workflow books is therefore not the bound the
> adapter checks, on every route that declares `context_window_tokens` and whose
> endpoint cap is not equal to its route ceiling. The prompt term is identical by
> construction and cannot contribute.

The fix is not to reconcile the two expressions — that is parity by agreement,
the E26 shape, and it would leave the same defect one refactor away. One
component computes the cap once; every other party consumes that number.
