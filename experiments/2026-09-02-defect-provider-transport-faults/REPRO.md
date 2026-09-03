<!-- tranche: 2026-09-02-defect-provider-transport-faults -->

# Reproduction

Two halves. **Half A (offline, complete)** reproduces the mechanism and is the
regression artifact. **Half B (the live Phase 0 probe)** measures the wall
itself and is pending the operator's API key; its design is frozen in
`PREREG.md` and nothing below may be edited once it starts.

---

## Half A — offline

**Form:** unit-test (form 2), against a real socket. No live provider call.
**Artifact:** `tests/test_provider_transport_faults.py`
**RED transcript:** `proof/repro_red.txt` (committed)

### The stub

`WallServer` accepts the connection, reads the complete request, holds for
`wall_s`, then closes having written **no body**. `urllib` surfaces that as
`http.client.RemoteDisconnected`, which is the exact string all 39 P-A1
diagnostics carry. It records every attempt's verbatim request body, which is
what makes "the retry is byte-identical" a measurement rather than a reading.

One fidelity detail worth stating, because getting it wrong silently voided the
first version of the timing assertion: the retry backoff is neutralised the way
`tests/test_llm.py::_patched_endpoint` does it, by monkeypatching `sleep` on the
`time` MODULE object — which is the same object the stub's own thread would
call. The stub therefore holds its wall with `threading.Event.wait`, so the
2/4/8 s ladder is skipped and the wall is real.

### Current output

```
9 failed, 1 passed
```

The one that passes is the constant pin (`_BACKOFFS == (2, 4, 8)`), which exists
so `DIAGNOSIS.md` E1's arithmetic stays re-derivable. The nine failures:

```
AssertionError: the retry resent byte-identical bytes into the same wall:
  4 attempts, 1 distinct request bodies
assert b'{"model": "m", "messages": [...], "max_tokens": 49152}'
    != b'{"model": "m", "messages": [...], "max_tokens": 49152}'

AssertionError: a zero-byte wall got 4 identical attempts;
  the read-timeout branch already stops at 2

deepreason.llm.endpoints.EndpointError: transport failed after retries:
  Remote end closed connection without response
    (the stub would have answered a request whose cap had come down; none did)

AttributeError: 'OpenAICompatEndpoint' object has no attribute
  'last_zero_byte_returns'

AssertionError: 'provider_health' not in ProgressEvent.model_fields   (x3)
AssertionError: no absence code can say 'this root recorded no provider
  attempts'
AssertionError: '## Provider health' not in <rendered results>
```

Direct measurement of the mechanism, outside pytest:

```
attempts=4  distinct_bodies=1  elapsed=1.21s against a 0.30s wall (4.0x)
with the real 2/4/8s backoff this would be 15.2s
last_transport_attempts: 4
last_transport_diagnostics: ['RemoteDisconnected:Remote end closed connection
  without response'] x4
```

### Confirms diagnosis: yes

The offline stub reproduces the live arithmetic to the ratio. P-A1's ten faults
are `1 214 899 ms` against a `300.3 s` wall = **4.05x** (four attempts plus the
14 s ladder); the stub gives `1.21 s` against a `0.30 s` wall = **4.0x** (four
attempts, ladder patched out). Same four attempts, same single distinct request
body, same `RemoteDisconnected` diagnostic repeated four times, same
`transport_attempts: 4`. The mechanism is not a property of glm-5.3, of Ollama,
or of the network — it is `request_with_retries`' generic arm, and a stub that
closes a socket is enough to produce it.

The surfacing half reproduces just as cleanly and needs no stub at all: the
field a monitor would read is absent from the model, and the absence code that
would let `deepreason results` say "this root recorded no provider attempts"
does not exist in `ABSENCE_REASONS`' 17.

### Post-fix expectation

All ten pass, with `## Provider health` in the rendered results, `<= 3`
attempts on a zero-byte wall, `elapsed < 3 * wall`, at least two distinct
request bodies, and a stub that answers a shrunk request answering it.

### Two success-criterion clauses NOT yet reproduced, and why

- **Clause 5 (a streaming stub past the wall completes).** Not written. Whether
  streaming is built at all is decided by `PREREG.md` P2; writing the test first
  would be building the answer into the instrument.
- **Clause 6 (N consecutive zero-byte attempts on one seat emit a typed
  notice).** Not written. N, and whether the notice is only a notice, is
  `FIX.md`'s to specify — including the dead-provider-streak stop question the
  executor instruction reserves for the operator.

---

## Half B — the live probe (COMPLETE)

Design frozen in `PREREG.md` before the first call; Amendment 1 added arm `H1`
after the control arms and before it ran. 17 calls of a 20-call budget. Raw rows
under `probe/raw/<arm>.json`, one file per call, written before the next started;
`probe/raw/H1.sse` is the verbatim SSE body. Nothing below is edited from what
those files say.

### The table

| arm | model | cap | stream | elapsed s | t_headers s | tokens | finish | outcome |
|---|---|---|---|---|---|---|---|---|
| A1 | glm-5.3 | 16384 | no | 176.717 | 176.715 | 16384 | length | OK |
| A2 | glm-5.3 | 24576 | no | 268.813 | 268.791 | 24576 | length | OK |
| **A3** | **glm-5.3** | **32768** | **no** | **300.510** | — | — | — | **RemoteDisconnected** |
| **A4** | **glm-5.3** | **49152** | **no** | **300.268** | — | — | — | **RemoteDisconnected** |
| B1 | glm-5.3 | 16384 | yes | 174.898 | 0.796 | — | length | OK |
| B2 | glm-5.3 | 24576 | yes | 313.916 | 56.994 | — | length | OK |
| **B3** | **glm-5.3** | **32768** | **yes** | **369.639** | 0.629 | — | length | **OK** |
| **B4** | **glm-5.3** | **49152** | **yes** | **756.511** | 137.886 | — | length | **OK** |
| C1 | deepseek-v4-pro:0813 | 49152 | no | 229.056 | 229.048 | 27096 | stop | OK |
| C2 | deepseek-v4-pro:0813 | 49152 | yes | 116.114 | 0.655 | — | stop | OK |
| **D1** | **glm-5.3** | **49152** | **no** | **300.210** | — | — | — | **RemoteDisconnected** |
| D2 | glm-5.3 | 49152 | yes | 516.091 | 3.476 | — | length | OK |
| **E1** | **deepseek-v4-pro:0813** | **49152** | **no** | **300.289** | — | — | — | **RemoteDisconnected** |
| E2 | deepseek-v4-pro:0813 | 49152 | yes | 264.429 | 178.799 | — | stop | OK |
| F1 | glm-5.3 | 2048 | no | 29.306 | 29.304 | 2048 | length | OK (control) |
| F2 | glm-5.3 | 2048 | yes | 11.133 | 0.906 | — | length | OK (control) |
| H1 | glm-5.3 | 2048 | yes + usage | 28.132 | — | **2048** | length | OK (Amendment 1) |

`G1`/`G2` unused. Controls `F1`/`F2` both succeeded, so every other cell is
admissible under PREREG §4's rig-sanity rule.

### The four failures, together

```
n=4   elapsed = [300.510, 300.268, 300.210, 300.289]
mean = 300.319   range = 0.300   stdev = 0.114
all bytes_received == 0 : True
all t_headers is None   : True
exception types         : ['RemoteDisconnected']
models                  : ['deepseek-v4-pro:0813', 'glm-5.3']
proxy recentRelayFailures after each : [[], [], [], []]
```

**A 0.3-second range across two model families is a timer.** Every failure
received zero bytes and never saw a response header, and the container's own
relay reported no abort in any of the four — so by PREREG §4's stated
discriminator the close came from beyond this container, and the finding
transfers to the operator's machine.

### Verdicts against the pre-registered hypotheses

- **P1 — ACCEPTED.** Four of six non-streaming long-cap calls died in
  [280, 320] s; the rule required three. Measured wall **300.32 s**, against
  300.3 s and 300.5 s derived from two committed roots that were never
  measured on purpose (`DIAGNOSIS.md` E1). Three independent equipments, one
  number.
- **P2 — ACCEPTED.** Three streaming calls completed past 320 s: B3 at 369.6 s,
  D2 at 516.1 s, B4 at **756.5 s — two and a half times the wall**. The rule
  required three. The decisive comparison is a matched pair: **A3 and B3 are the
  same model, the same cap and the same prompt, and differ only in
  `"stream": true`. A3 died at 300.51 s having received nothing; B3 finished at
  369.64 s.**
- **P2b (Amendment 1) — ACCEPTED.** `H1` sent `stream_options:
  {"include_usage": true}` and the terminal frames carry
  `{"prompt_tokens": 75, "completion_tokens": 2048, "total_tokens": 2123}`. A
  streamed call can still report its own spend, so streaming does not trade a
  visible failure for an invisible one. **The STOP that Amendment 1 armed does
  not fire.**
- **P3 — ACCEPTED.** `E1`, deepseek-v4-pro:0813 non-streaming at 49152, died at
  **300.289 s** — inside the same 0.3-second band as glm-5.3's three. The wall
  is the path, not the model.

  Read `C1` beside it or the finding is over-read: the same model at the same
  cap SUCCEEDED at 229.1 s, because that generation stopped naturally at 27 096
  tokens before reaching the wall. Exposure to the wall is a function of how
  long a call runs, not of who is running it. That is exactly why P-A1 recorded
  39 `RemoteDisconnected` on glm-5.3 and none on deepseek: not a sick endpoint,
  a slower generation.

### The mechanism, and what is still not decided

`t_headers` separates the two framings cleanly. Non-streaming: A2's headers
arrive at 268.791 s against an elapsed of 268.813 s — **nothing comes back until
the whole answer is done**, so a request that needs longer than the wall sends
no byte before it is cut. Streaming: B3's headers arrive at 0.629 s and bytes
flow for the next 369 s.

That rules out **M-queue** (a queue-admission deadline would kill the streams
too) and it rules out a cap on total request duration (B4 ran 756 s). It does
NOT separate **M-idle** (no bytes for ~300 s) from **M-ttfb** (no FIRST byte
within ~300 s): no streaming arm was slow enough to its first byte to test the
difference — the slowest was E2 at 178.8 s. Both readings predict every row in
this table. **Recorded as undecided**, because the fix is the same either way.

### Residue, stated rather than hidden

- P-A1's one **839 s non-streaming success** (43 281 tokens) is still not
  explained by this table. Every non-streaming arm here either finished under
  the wall or died at it; none survived past it. That call remains an anomaly
  against a mechanism otherwise measured to 0.3 s, and this probe did not
  reproduce it. It is not load-bearing for the fix — streaming survives
  regardless — but it is the one datum the model does not cover.
- One afternoon, one API key, one container. Nothing here shows the wall is
  stable over time, across accounts, or across regions.
- The failing component is not named. Client-side an Ollama-edge close and an
  egress-proxy close are the same bytes; `recentRelayFailures` clears only this
  container's own relay. The `server: Google Frontend` response header on every
  successful arm is a hint and is not evidence.
- Survival is not safety. `docs/OLLAMA_CLOUD_OPERATIONS.md` §2 records that a
  stream can return 200, emit partial tokens, then fail with an `error` object
  mid-body. The probe's parser checked for the terminal `data: [DONE]` and every
  streamed arm carried it; a harness implementation must check the same thing on
  every call, and FIX.md carries that obligation.

### Ground truth for the reassembly (`probe/raw/H1.sse`)

1 915 SSE lines, standard OpenAI framing. Delta keys observed: `role` x1,
`content` x1912, `reasoning` x1911. `finish_reason` arrives on its own chunk with
an empty delta; `usage` arrives on a chunk with `choices: []`; the body ends
`data: [DONE]`. Reassembling gives back exactly the dict shape
`OpenAICompatEndpoint.complete` already reads:

```json
{"choices": [{"message": {"content": "...", "reasoning": "..."},
              "finish_reason": "length"}],
 "usage": {"prompt_tokens": 75, "completion_tokens": 2048, "total_tokens": 2123}}
```

**No `logprobs` key appears on any chunk.** That is a measured constraint on the
fix, not a guess: a call that asked for logprobs cannot be answered by this
reassembly, and FIX.md must keep such a call non-streaming.

Incidental, and worth one line because it corroborates a finding another window
owns: `H1` at cap 2048 with the reasoning knob omitted produced **0 content
characters and 6 388 reasoning characters**. The whole cap went to thinking.
