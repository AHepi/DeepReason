# RESULTS.md — qualification circuit breaker (defect P7-A)

Honest ledger. Dated segments; what the record shows, and the residue.

## 2026-08-29 — the tranche was re-run from scratch, because the first one was lost

This tranche existed once already. It was completed, green, and WITHHELD on an
operator stop over its diff budget — and it was never pushed. The container was
reclaimed, taking the branch, the tranche directory, the `STOP.md` brief and
`proof/implementation.patch` with it. `experiments/2026-08-29-ultracode-batch-1/LOSS.md`
records the evidence that it was gone rather than merely misplaced.

Everything here was re-derived from what survived on `main`: the dispatch
(`P7-A` and audit `F-H`), the batch manifest's stop brief, and the code itself.
Nothing was inherited as a number; every measurement was re-taken.

The lesson, recorded where it will be read again: **a STOP is a phase
boundary.** Work parked awaiting a verdict is finished work, not work in
progress, and must be pushed at the moment it is parked.

## What the record showed

The battery bounded each provider CALL at 2s/4s/8s
(`llm/endpoints.py:51-70`) and bounded nothing above it. An account-level
condition — one refusal that applies to every case equally — was therefore
re-tested by all 360 cases of the default subject.

Re-measured offline, real doctor and real ladder, only the socket and clock
faked:

| condition | HTTP calls | mandated wait | record written |
|---|---|---|---|
| 429 (clears on its own) | 1440 | **5040 s (84.0 min)** | `{'ENDPOINT_ERROR': 360}` |
| 401 (never will) | 360 | **0 s** | `{'ENDPOINT_ERROR': 360}` |

Identical in all 83 035 bytes. That is the defect stated at full strength: the
record could not tell an operator whether to wait or to fix their key.

## What was fixed

A cross-case breaker keyed per `(endpoint_id, route_sha256)`, evaluated at
block boundaries, that RETURNS a complete typed report and never raises — and
the legibility half without which the breaker has nothing to key on
(`EndpointError` carries `http_status`/`condition`; `_failure_code` turns them
into `ENDPOINT_HTTP_401` and friends).

Cost after: 20 calls for a 401, 80 calls and 280 s for a 429. Records
distinguishable. One dead route still leaves 8 of 10 pairs measured and
qualified — the contingency that would have made it global was re-measured and
leaves 0 of 10.

## What the tranche got wrong, and how it was caught

**The main result, and it is not the fix.** The first implementation satisfied
all six of its own criteria, its own review, and a full gate at 4475 passed / 0
failed — and was wrong in six places. An independent skeptic re-ran its claims
instead of reading them and found: two regression tests that were VACUOUS
(green on a tree containing no breaker at all); a resolver that CRASHED the
battery on a character `str.isdigit()` accepts and `int()` refuses; a
reconfigured gate that left ZERO trace in the record it claimed to be recorded
in; a second road to OFF that warned on neither; and a programmatic road that
refused what the environment road clamped.

Two of the tranche's own claims were also overstated: "a battery that never
trips writes the bytes it wrote before" (true only for an all-admitted
battery) and "that battery took about a minute" (an inference stated as a
measurement, for an invocation that has no committed timing at all).

All six are fixed with regression tests; both claims are corrected in place.
The budget consequence was put to the operator as a STOP and re-declared at
the measured 356.

## The correction the tranche owes the record

The symptom P7-A was dispatched to fix **has no surviving committed instance**,
and the "18 minutes" figure four committed documents carry is unsupported by
anything in the repository — the cited evidence file records an HTTP 401 from
an empty API key, and a 401 is not retryable, so the ladder never slept. The
only provenance any carrier offers is a wall-clock interval appearing nowhere
but its own sentence. Ledgered as **E62**.

The defect was not thereby dissolved. It is real, and the re-measurement makes
it worse than the audit had it: 84 minutes, not 18.

## Residue

Full list in `VERIFY.md`. The two that matter most:

- **No live run, and none possible here.** The breaker has never fired against
  a real provider.
- **The bound is guaranteed only for a uniformly-arming block.** One
  non-arming failure in a block prevents that block from opening the circuit.

Accepted does not mean true.
