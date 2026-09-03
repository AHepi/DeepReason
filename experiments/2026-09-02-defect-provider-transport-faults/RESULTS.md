<!-- tranche: 2026-09-02-defect-provider-transport-faults -->

# Results — provider transport faults

Dated, honest-ledger segments. What the record shows, and the residue.

---

## 2026-09-03 — what was observed

Two runs, both already committed, both dead against a provider and neither
saying so.

- **P-A1, run `4565139800f5ca02`.** Ten of glm-5.3's 25 calls returned zero
  tokens after ~1215 s each — `transport_attempts: 4`, the same
  `RemoteDisconnected` diagnostic four times, `raw_ref: ""`. 3.27 h of a 4.94 h
  run. The window's own `monitor.sh` was written for exactly this signature and
  raised 0 alerts on 40 faults, because it tested keys (`error` / `failure` /
  `status`) the attempt trace does not carry.
- **P-S1, run `9e48a36b1dec91ee`.** 54 typed `transport_failure` attempt objects
  on one seat; 15 of 24 cycles ran with that seat dead. Not one of the tranche's
  13 summary documents contains `transport`, `RemoteDisconnected`,
  `ConnectionError` or `provider health`. The dead cycles were reported as a
  milestone **MET**.

## What the record showed, re-derived rather than quoted

Subtracting the retry ladder's own 14 s from each fault's recorded `ms` and
dividing by `transport_attempts` = 4 puts **eight of P-A1's ten faults in a
0.2-second band around 300.3 s**, with the harness's own `timeout_s` at 1800 on
every one — so the cutter was never the harness. A root committed six days
earlier gives **300.5 s** from a different model, a different cap and a
different client timeout.

Two things this ruled out, both of which had been believed: that glm-5.3 was
merely slow (every one of the ten has `tokens: 0` and `usage_unknown: true` —
nothing generated), and that the harness's read timeout fired (a read timeout
raises `TimeoutError`, which routes to a two-attempt escalating ladder; the
record shows four attempts and `RemoteDisconnected`, the other branch).

## What the probe measured — the first deliberate measurement of this wall

17 calls, hypotheses and decision rules frozen in `PREREG.md` before the first.

| | non-streaming | streaming |
|---|---|---|
| glm-5.3, cap 16384 | 176.7 s OK | 174.9 s OK |
| glm-5.3, cap 24576 | 268.8 s OK | 313.9 s OK |
| **glm-5.3, cap 32768** | **300.51 s DIED** | **369.6 s OK** |
| **glm-5.3, cap 49152** | **300.27 / 300.21 s DIED** | **756.5 / 516.1 s OK** |
| **deepseek, cap 49152** | 229.1 s OK / **300.29 s DIED** | 116.1 / 264.4 s OK |

Four failures: **mean 300.319 s, range 0.300 s, stdev 0.114 s**, every one with
zero bytes received and no response header ever seen, across **two model
families**. The container's own relay reported no abort on any of them, so by
`PREREG.md` §4's stated discriminator the close comes from beyond this machine.

The decisive result is a matched pair, not an average: **A3 and B3 are the same
model, the same cap and the same prompt, and differ only in `"stream": true`.
A3 died at 300.51 s having received nothing; B3 finished at 369.64 s.**

`t_headers` explains why. Non-streaming, A2's headers arrive at 268.791 s
against an elapsed of 268.813 s — nothing comes back until the answer is
finished, so a request that needs longer than the wall sends no byte before it
is cut. Streaming, B3's headers arrive at 0.629 s and bytes flow for 369 s.

## What was fixed

1. **Visible.** `runtime/provider_health.py` is ONE derivation feeding both
   `progress.jsonl` and `deepreason results`, so the two cannot disagree. On
   P-A1's own record it now prints `10 of 71 calls, 10 returning nothing, 196.2
   minutes spent on them`, per seat, with the kind of fault named. On P-S1's:
   `54 of 280 calls, 54 returning nothing`.
2. **Retried on a typed policy.** A `zero_byte_close` bounds at two attempts
   and the retry is the SAME request streamed. Every other fault kind keeps
   today's ladder — deliberately: P-S1's 54 were connection refusals costing
   milliseconds, P-A1's were hang-ups costing 300 s each, and the classifier
   that tells them apart is shared by the endpoint and the record reader.
3. **Survivable.** Streaming reassembles into the exact dict a non-streaming
   call returns, so the same model output writes the same record.

## The residue — what remains unproven

- **P-A1's one 839 s non-streaming success (43 281 tokens) is not explained.**
  Every non-streaming arm here either finished under the wall or died at it;
  none survived past it. That call remains an anomaly against a mechanism
  otherwise measured to 0.3 s, and this probe did not reproduce it.
- **The mechanism is narrowed, not identified.** An idle-gap timer and a
  first-byte deadline both predict every row in the table; no streaming arm was
  slow enough to its first byte to separate them. A queue-admission deadline is
  ruled out, and a cap on total duration is ruled out by the 756 s arm.
- **The failing component is not named.** Client-side, an Ollama-edge close and
  an egress-proxy close are the same bytes.
- **One afternoon, one key, one container.** Nothing here shows the wall is
  stable over time, across accounts, or across regions.
- **Survival is not safety.** A stream can return 200, emit partial tokens and
  then fail; the shipped reader refuses a body without its terminal chunk, and
  that guard is tested, but the failure mode is the provider's and remains real.
- **A dead seat still kills a run.** This tranche discloses; it does not stand a
  seat down. `PARKED.md` P1.

Accepted does not mean true. What is measured is the wall and the streaming
survival; what is fixed is the blind retry and the blind surfaces; what is not
fixed is everything in `PARKED.md`.
