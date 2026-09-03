<!-- tranche: 2026-09-02-defect-provider-transport-faults -->

# PREREG — Phase 0 transport-wall probe

**Frozen before the first live call.** Nothing below may be edited after the
probe starts; a change of mind becomes a dated Amendment appended at the end,
stating what changed and why. Raw output is preserved verbatim under
`probe/raw/`, whatever it says. A negative or inconclusive result is recorded as
one.

Written: 2026-09-02, before any call. Authority for the design: the executor
instruction's Phase 0; authority for the numbers it must beat:
`DIAGNOSIS.md` E1-E3.

---

## 1. What is already measured, and what is not

MEASURED (two committed roots, `DIAGNOSIS.md` E1):

- P-A1 `4565139800f5ca02`: eight of ten transport faults at **300.2-300.4 s**
  per attempt, `timeout_s: 1800`, four byte-identical attempts each.
- `retired-transport-timeout180-run-42ad288038dd606c` (2026-08-26): **300.5 s**
  per disconnect, `timeout_s: 180`, different model and cap.

NOT MEASURED, anywhere in this repository:

- whether the close is a function of elapsed time, of byte silence, or of
  queue admission;
- whether it is the container's local relay, the egress proxy, or Ollama's
  edge (the container README states these are indistinguishable at the client
  — `recentRelayFailures` is the only discriminator);
- whether `"stream": true` is accepted at all on
  `https://ollama.com/v1/chat/completions`, and whether it survives past the
  wall;
- whether the wall is per-model.

The single most awkward datum, which any accepted hypothesis must explain: in
the same P-A1 run, one **non-streaming** glm-5.3 call ran **839 028 ms and
returned 43 281 tokens**. A flat cut at 300 s on total request duration is
therefore already refuted.

## 2. Hypotheses, pre-registered

- **P1 (primary).** A non-streaming call to `https://ollama.com/v1/chat/completions`
  whose generation exceeds ~300 s is closed by the remote end with no body,
  regardless of model.
- **P2 (the one that decides the fix).** The same call with `"stream": true`
  survives past 300 s and completes.
- **P3.** The wall is the same second for `glm-5.3` and for
  `deepseek-v4-pro:0813` when both are forced past it — i.e. it is the path,
  not the model.

Three competing mechanisms, stated now so the probe can separate them:

| id | mechanism | P1 | P2 | what discriminates it |
|---|---|---|---|---|
| **M-idle** | an idle-gap timer: no bytes on the socket for ~300 s | TRUE | TRUE | streaming emits bytes continuously and survives |
| **M-ttfb** | a time-to-first-byte deadline at the gateway | TRUE | TRUE | same prediction as M-idle for P1/P2; separated only by whether a *stream* that is slow to its FIRST token also dies at 300 s |
| **M-queue** | an admission/queue deadline: the request is dropped if a model slot is not granted in ~300 s | TRUE | **FALSE** | streaming dies too, and failures correlate with concurrency, not with generation length |

M-queue is the hypothesis that makes P2 false, and P2 false is the tranche's
stated STOP. It is on this table so that outcome is a pre-registered result
rather than a surprise.

The 839 s success is compatible with M-idle and M-ttfb only if the gateway
writes response headers (or any byte) before generation finishes. **Arm C below
tests exactly that**, because if nothing is written early then M-idle and M-ttfb
both predict that 839 s call should have died, and all three mechanisms are in
trouble.

## 3. Design

**Wire shape — identical to the harness's**, so a result transfers. Source:
`llm/endpoints.py:420-427` (headers, URL) and `build_body`
(`endpoints.py:324-389`).

- `POST https://ollama.com/v1/chat/completions`
- headers: `Content-Type: application/json`, `Authorization: Bearer <key>` —
  and nothing else the harness does not send
- body: `{"model": M, "messages": [{"role": "user", "content": PROMPT}],
  "max_tokens": K}` plus `"stream": true` on streaming arms only. **No
  `system` message, no `top_p`, no `temperature`, no `reasoning_effort`** —
  omitting the reasoning knob is what the P-A1 seats did, and it is what puts
  glm-5.3 at its documented default `max` effort.
- client: `urllib.request.urlopen`, the harness's own client — NOT `requests`
  or `httpx`, whose keep-alive and gzip defaults are a wire difference.
- **client timeout: 1800 s on every arm.** The harness's own
  `DEFAULT_TIMEOUT_S` is 300, the same number as the suspected wall; a 300 s
  client timeout would confound the two. This is the exact confusion that
  mis-diagnosed the 2026-08-26 tranche for a week.

**The fixed prompt**, one string, identical on every call:

> Write a complete, self-contained technical monograph on the history and
> mechanics of error-correcting codes, from Hamming through Reed-Solomon to
> modern LDPC and polar codes. Include worked numerical examples, full
> derivations, and a chapter on decoding complexity. Do not summarise; write
> the full text.

**Arms.** 20 calls, capped at **3 in flight** (Ollama Pro per-account
concurrency is 3 — `docs/OLLAMA_CLOUD_OPERATIONS.md` §1; exceeding it
contaminates latency with queue wait).

| arm | model | max_tokens | stream | n | tests |
|---|---|---|---|---|---|
| A1-A4 | glm-5.3 | 16384, 24576, 32768, 49152 | no | 4 | P1, and whether the wall scales with the cap |
| B1-B4 | glm-5.3 | 16384, 24576, 32768, 49152 | **yes** | 4 | P2 |
| C1-C2 | deepseek-v4-pro:0813 | 49152 | no, yes | 2 | P3 |
| D1-D2 | glm-5.3 | 49152 | no, yes | 2 | replication of A4/B4 |
| E1-E2 | deepseek-v4-pro:0813 | 49152 | no, yes | 2 | replication of C1/C2 |
| F1-F2 | glm-5.3 | 2048 | no, yes | 2 | negative control: a short call must succeed on both, or the rig is broken |
| G1-G2 | glm-5.3 | 49152 | no, yes | 2 | spare / re-runs of any ambiguous cell |

**Recorded per call** (`probe/raw/<arm>.json`, one file per call, written before
the next call starts so a container rollback loses at most one):

`arm, model, max_tokens, stream, t_submit, t_first_byte, t_last_byte,
elapsed_s, http_status, response_headers, bytes_received, completion_tokens,
finish_reason, exception_type, exception_str, proxy_recent_relay_failures_after`

`t_first_byte` is taken from the first byte off the socket, not from
`urlopen` returning — that is Arm C's whole point, and stdlib `urlopen` returns
once response HEADERS are available, which is itself the datum.

**`recentRelayFailures` is sampled immediately after every failure**, by
`curl -sS "$HTTPS_PROXY/__agentproxy/status"`. This is the only thing that
separates a container-proxy abort from an Ollama-edge close; the container's
own README says so.

## 4. Decision rules, fixed in advance

- **P1 accepted** if >= 3 of the 6 non-streaming long-cap calls (A2-A4, C1, D1,
  E1) die with a zero-body close whose elapsed time is in **[280, 320] s**, and
  `recentRelayFailures` is empty at each. If they die but `recentRelayFailures`
  names the host, the wall is this container's proxy and the finding does not
  transfer to the operator's own machine — **that is a STOP and a report**, not
  a fix.
- **P1 rejected** if the non-streaming long-cap calls complete, or die at times
  that do not cluster. Then `DIAGNOSIS.md`'s wall half is wrong and the tranche
  returns to `dr-diagnose` with the table.
- **P2 accepted** if >= 3 of the 6 streaming long-cap calls (B2-B4, C2, E2, G2)
  deliver a terminal chunk past 320 s.
- **P2 rejected** if streaming dies at the same wall, or if `"stream": true` is
  refused outright by the endpoint. **Then clause 5 of GOAL.md's success
  criterion is struck, no streaming is built, and the tranche STOPS and reports
  with the measurement** — per the executor instruction, which fixed this
  outcome in advance.
- **P3 accepted** if deepseek's non-streaming long-cap calls die in the same
  [280, 320] s band. **P3 rejected** (deepseek survives) does NOT block the
  fix: it would mean the wall is reached only by models slow enough to hit it,
  which is a statement about generation speed, not about the wall. Recorded
  either way.
- **Rig sanity:** if F1/F2 (the 2048-token control) do not both succeed, no
  other cell is admissible and the probe is re-run after the rig is fixed.

**Budget: 20 calls.** A 21st call is an Amendment with its reason, not a
judgement call.

## 5. What this probe cannot decide (stated now, not later)

- It cannot attribute the wall to a named component. Client-side, an Ollama
  edge close and an egress-proxy close are the same bytes; `recentRelayFailures`
  distinguishes only the container's own local relay.
- It cannot establish that the wall is stable over time or across accounts. One
  afternoon, one key.
- A green streaming result does not prove streaming is safe for the harness —
  `docs/OLLAMA_CLOUD_OPERATIONS.md` §2 records that a stream can return 200,
  emit partial tokens, and then fail with an `error` object mid-body. Any
  streaming implementation must parse to completion and check for that; the
  probe only establishes survival, and FIX.md must carry the rest.
- It measures nothing about how a *fix* behaves. That is the offline stub's job.

## 6. Credential handling

The key is read from `experiments/2026-09-02-defect-provider-transport-faults/env`
(`OLLAMA_API_KEY=...`), which `.gitignore:47` (`experiments/*/env`) already
covers — confirmed with `git check-ignore` before the file is written. It is
never echoed, never printed into `probe/raw/`, and never committed. The probe
script reads it via `os.environ` after sourcing that file and redacts the
`Authorization` header from every recorded response-header dump.

---

## Amendment 1 — 2026-09-03, after the control arms, before the extra call

**What changed:** one arm added, `H1` — glm-5.3, `max_tokens` 2048, `"stream":
true`, plus `"stream_options": {"include_usage": true}`. Call 17 of the 20-call
budget; the two spare arms `G1`/`G2` are unused, so no arm is displaced.

**Why, and why it could not wait for FIX.md.** The frozen §3 body deliberately
sends nothing the harness does not send, and the harness sends no
`stream_options`. Control arm `F2` (glm-5.3, cap 2048, streaming) came back
`status=200`, terminal chunk present, 18 chunks, **`completion_tokens: None`** —
the OpenAI-compatible streaming framing carries no usage block unless it is
asked for. That is not a curiosity: `SUB-llm.md` Traps records that
under-counting provider usage "is not cosmetic: it defeats the hard ceiling",
and `usage_unknown: true` is one of the three fields that make a P-A1 fault
recognisable in the first place. A streaming implementation that silently
stopped reporting usage would fix the wall by breaking the budget.

So P2 as originally worded — "streaming survives past 300 s" — is necessary but
not sufficient for the fix the goal asks for. The sufficient question is P2
AND P2b:

- **P2b.** Ollama's `/v1/chat/completions` honours `stream_options:
  {"include_usage": true}` and returns a usage block in the terminal chunk.

**Decision rule, fixed now:** P2b accepted if `H1` returns a
`completion_tokens` integer. **If P2b is FALSE, streaming is not built even if
P2 is true** — the same STOP, for a different and better reason, and FIX.md
records that the wall stays unfixed rather than trading a visible failure for
an invisible one. The alternative roads (estimate usage from the reassembled
content; ask the operator to accept `usage_unknown` on streamed calls) are
FIX.md's to price, not this document's to choose.

**What is NOT changed:** the arms already running, the fixed prompt, the client
timeout, the concurrency cap, the P1/P2/P3 decision rules, and the budget.
`H1` runs only after the main batch drains, so the 3-in-flight cap holds.
