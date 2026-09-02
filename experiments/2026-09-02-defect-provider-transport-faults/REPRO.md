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

## Half B — the live probe (PENDING)

Design frozen in `PREREG.md`. Blocked on one thing only: the `OLLAMA_API_KEY`,
which the executor instruction directs be requested at this step and not before.
The probe script and the gitignored credential path are ready; `git check-ignore`
confirms `experiments/2026-09-02-defect-provider-transport-faults/env` is covered
by `.gitignore:47`.

Results table, decision against P1/P2/P3, and the `recentRelayFailures` reading
that separates a container-proxy abort from an Ollama-edge close are appended
here when the probe runs.
