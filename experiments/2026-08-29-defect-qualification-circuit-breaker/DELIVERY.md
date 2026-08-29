# DELIVERY.md — qualification circuit breaker (P7-A)

Closed against `GOAL.md`'s six criteria. Verdict in `VERIFY.md`:
**PASS-offline**; live NOT ATTEMPTED, because no provider credential exists in
this container.

## The headline

An account-level provider refusal no longer costs a full battery, and the
record can finally tell one refusal from another.

| | HTTP calls | mandated wait | record |
|---|---|---|---|
| **before**, 401 | 360 | 0 s | `{'ENDPOINT_ERROR': 360}` |
| **before**, 429 | 1440 | **5040 s (84 min)** | `{'ENDPOINT_ERROR': 360}` — *identical in all 83 035 bytes* |
| **after**, 401 | 20 | 0 s | `ENDPOINT_HTTP_401` + `CIRCUIT_OPEN_…401` |
| **after**, 429 | 80 | 280 s | `ENDPOINT_HTTP_429` + `CIRCUIT_OPEN_…429` |

Two conditions 84 minutes apart in cost — one that clears itself, one that
never will — used to leave byte-identical records.

## Criterion by criterion

| # | criterion | verdict |
|---|---|---|
| 1 | bounded, and PER ROUTE | **MET.** dead route 20 of 80 cases; four healthy routes fully measured; 8 of 10 pairs still qualified |
| 2 | a transient that clears does NOT trip it | **MET.** 19 failures + 1 success dispatches all 80 and opens nothing |
| 3 | the record distinguishes the two | **MET.** distinct typed codes both for the observed failure and for the short-circuited cases |
| 4 | switchable OFF, with a TYPED WARNING | **MET**, and on BOTH roads to off — `enabled=False` and an empty prefix set each emit their own notice |
| 5 | changing behaviour never needs a code edit | **MET.** 9 architecture tests, including a 500-status sweep and a retarget-by-environment pair |
| 6 | no knob moves a qualification subject digest | **MET by construction** — there is no new `Config` field; `source_config_hash` is byte-unchanged |

## The correction this tranche owes its own dispatch

**The symptom P7-A was dispatched to fix has no surviving committed
instance.** The evidence file the brief named records an HTTP **401** from an
empty API key — not retryable, so the backoff ladder never slept once. The
"18 minutes" figure four committed documents carry is unsupported by anything
in the repository; the only provenance any of them offers is a wall-clock
interval appearing nowhere but its own sentence.

The defect is not thereby dissolved. Re-measured, it is **worse** than the
audit had it: 84 minutes, not 18. Ledgered as **E62**; `BATCH.md` §5's own
stale table corrected in place as **E63**.

## What was found wrong in this tranche's own work

**The first implementation passed its own criteria, its own review, and a full
gate at 4475 passed / 0 failed — and was wrong in six places.** An independent
skeptic re-ran the claims rather than reading them:

| # | defect | fix |
|---|---|---|
| 1 | **two regression tests were VACUOUS** — green on a tree with no breaker in it | strengthened; both now fail pre-fix with `AssertionError` |
| 2 | "never trips ⇒ byte-identical" was **over-broad** | corrected; the all-admitted case is proven, the general case is false, and the reach is the bundle digest not the subject digest |
| 3 | the resolver **crashed the battery** on `'²'` | guarded by the parse itself |
| 4 | a reconfigured gate that never fired left **zero trace** | the record is emitted for any departure from the shipped policy |
| 5 | `code_prefixes=()` **silently disabled** the gate | typed `..._INERT` notice; both roads to off warn |
| 6 | the explicit road **refused** what the environment clamped | clamped in the model |

Two of the tranche's own claims were also overstated and are corrected on the
record: "that battery took about a minute" was an inference stated as a
measurement, and C1's target list is four documents, not two.

## Budget

Re-declared twice by the operator at the measured figures, both times with the
cone unchanged and the compression option measured and rejected. Recorded in
`FIX.md` §2.

## Parked

**C1** (now ledgered as E62) · **C3** · **C4** (needs frozen surface 5) ·
**C5** (made strictly less reachable) · **C6**. Residue in full in
`VERIFY.md` — most importantly that the bound is guaranteed only for a
uniformly-arming block, and that the breaker has never fired against a real
provider.
