# GOAL.md — qualification circuit breaker (defect P7-A)

Tranche re-run 2026-08-29 after the original lane's work was lost with its
container (`experiments/2026-08-29-ultracode-batch-1/LOSS.md`). The dispatch,
the evidence and the monitor's ruling all survived on `main`; only the
implementation did not.

## Map preflight

Recorded in `FIX.md` §0 before any design, per CLAUDE.md.

## The goal, one sentence

Make the production-contract qualification battery stop when the provider has
refused at the ACCOUNT level, and make the record say which condition it was,
so that a refusal that will never clear is no longer indistinguishable — in
cost or in the record — from a transient one that will.

## Falsifiable success criterion

1. A battery whose every case fails with an account-level provider condition
   stops after a bounded number of cases instead of exercising all of them,
   and does so PER ENDPOINT/ROUTE, so one dead route cannot stop the battery
   measuring every other.
2. A transient condition that clears does NOT trip the breaker: the battery
   completes and qualifies exactly as it does today.
3. The record distinguishes the two. Today an HTTP 401 and a persistent HTTP
   429 both write `{'ENDPOINT_ERROR': 260}` — byte-identical — while costing
   0 s and 3640 s of mandated wait respectively. After the fix, the two
   records differ.
4. The breaker is switchable OFF by configuration, restoring the exhaustive
   behaviour, and switching it off emits a TYPED WARNING — never a refusal,
   never silence (operator law, 2026-08-28).
5. Changing the breaker's behaviour never requires a code edit; two
   architecture tests go red if it ever does (operator law, 2026-08-26).
6. No new configuration knob moves a qualification subject digest.

## What is NOT in scope

Parked, and to stay parked:

- **C1** — the ERRATA correction two committed audit documents owe for the
  "18 minutes" figure. This tranche states the correction in its own
  `RESULTS.md`; writing it into `docs/ERRATA.md` belongs to a tranche whose
  cone includes that file.
- **C3** — the falsified census at `INV-frozen-surfaces.md:181`.
- **C4** — putting the provider status on the `deepreason qualify` console
  line. That means editing `qualification.py`, frozen surface 5, and needs
  its own operator grant.
- **C5** — `_failure_code` returning a schema-invalid code for an error
  carrying a NUMERIC `.code`. Real but unreachable today, and this fix makes
  it strictly less reachable.
- **C6** — duplicate of P19.

## The correction this tranche owes its own dispatch

The symptom P7-A was dispatched to fix **has no surviving committed
instance**. The evidence file the brief named,
`experiments/2026-08-25-change-constructive-frontier/qualify-attempt2-VOID-agent-error.json`,
records an HTTP **401** — a credential refusal, which is not on the retryable
list — so the backoff ladder never slept once and that battery took about a
minute, not eighteen. P7's original file had already been overwritten by a
later successful battery.

The defect is not thereby dissolved. It is re-evidenced, offline, in
`proof/` — see `RESULTS.md`. The number was wrong; the defect is real.

## Offline

No provider credential exists in this container. Every claim is a
compile-time or read-time property of committed code, fixtures, or generated
offline evidence. No live run is attempted, and none is claimed.
