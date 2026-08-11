# Ollama Cloud: Concurrency & Error Handling

**Audience:** orchestrator agent running DeepReason experimental arms against Ollama Cloud.
**Retrieved:** 2026-08-12 from `ollama.com/pricing`, `docs.ollama.com/cloud`, `docs.ollama.com/api/errors`, `ollama.com/terms`.
**Provenance:** supplied verbatim by the operator, 2026-08-12; committed unedited by the monitor session. The epistemic tags below are the document's own.
**Epistemic status:** every claim below is tagged `[DOCUMENTED]`, `[INFERRED]`, or `[UNKNOWN]`. Do not promote an `[INFERRED]` or `[UNKNOWN]` claim to a hard assumption in code without an empirical check. Where behaviour is unknown, fail closed.

---

## 1. The limit

`[DOCUMENTED]` Concurrency is plan-gated per **account**, not per API key, per process, or per client:

| Plan | Limit |
|------|-------|
| Free | 1 |
| Pro  | 3 |
| Max  | 10 |

`[DOCUMENTED]` Overflow behaviour: requests beyond the limit are queued and served when a slot opens. The queue has a fixed depth; once full, further requests are rejected until a slot frees.

`[UNKNOWN]` The queue depth is not published anywhere. Do not assume it is large. Do not rely on the queue as a scheduling mechanism.

`[UNKNOWN]` **What the limit actually counts.** Ollama's own documentation uses two incompatible vocabularies. The plan card says "Run 3 cloud models at a time" and the FAQ table is headed "Concurrent models", but the mechanism described immediately below it concerns requests, slots, and queueing. These imply different behaviour:

- **Interpretation A — in-flight requests.** A slot is held from request acceptance to final token. Serial execution never exceeds 1 regardless of how many distinct models are used.
- **Interpretation B — resident models.** Models stay warm after completion (local Ollama defaults to a 5-minute `keep_alive`). Calling a 4th distinct model within the window would contend even under strict serialization.

`[INFERRED]` A is more likely: hosted inference runs on shared fleets with continuous batching, so per-user model residency is not a natural unit. But this is inference, not documentation. **Resolve empirically before designing the scheduler** (§5).

`[INFERRED]` Under B, local Ollama evicts LRU rather than refusing, so the worst case is a cold-start latency penalty, not an error.

## 2. Error surface

`[DOCUMENTED]` Status codes: `200` success, `400` bad request, `404` model not found, `429` rate limit exceeded, `500` internal error, `502` cloud model unreachable. Errors return JSON with the message in an `error` property.

`[DOCUMENTED]` **Mid-stream failures do not change the status code.** If a stream has already begun, the error arrives as an NDJSON object carrying an `error` property, and the response remains `200`.

> **Consequence:** status-code-only error handling is unsound here. A trial can return `200`, emit partial tokens, and then fail. Every streamed response must be parsed to completion and checked for a terminal `error` object before the trial is marked successful. A truncated-but-clean-looking completion is a silent data-quality failure in the results ledger.

`[UNKNOWN]` No concurrency-specific status code or error string is documented. `[INFERRED]` A queue-full rejection most likely surfaces as `429`, indistinguishable from quota exhaustion.

## 3. Concurrency vs. quota — two independent limits

`[DOCUMENTED]` Quota is separate from concurrency. Usage is billed on model-weighted token processing, with session limits resetting every 5 hours and weekly limits every 7 days. Models carry usage levels 1 (light) to 4 (extra heavy).

`[INFERRED]` Both limits plausibly report as `429`, but they demand **opposite responses**:

| Cause | Correct response |
|-------|------------------|
| Queue full (concurrency) | Retry with backoff — a slot frees in seconds |
| Session/weekly quota exhausted | **Abort the run.** Retrying for hours is futile and burns wall clock |

`[INFERRED]` Disambiguation heuristics, in order: inspect the `error` message body for quota-related wording; check whether *any* request succeeds at concurrency 1; consult account usage state out-of-band. Until distinguished, treat repeated `429`s as quota exhaustion after a bounded number of attempts rather than retrying indefinitely.

## 4. Handling rules

1. **Own the concurrency, don't borrow it.** Enforce a client-side semaphore at or just under the plan limit. Do not fire an unbounded batch and let the server queue it — beyond an unknown depth those requests are rejected, and the rejections will be non-uniformly distributed across arms.
2. **Bounded retries with jitter.** Exponential backoff, hard attempt cap, circuit breaker on consecutive failures.
3. **Retries are budget events.** Every retried call consumes quota. If matched-budget accounting ignores retries, the arms are no longer matched. Log attempt counts per trial and include them in budget reconciliation.
4. **Never silently drop a trial.** A rejected or abandoned request must be recorded as an explicit failure with class and timestamp, not omitted. Missing trials bias results in a direction the analysis cannot see.
5. **Separate queue wait from generation latency.** If any budget or performance measure is latency-derived, queue time contaminates it. Record request-submitted, first-token, and last-token timestamps separately.
6. **Assume slot leaks.** A dropped connection or killed client may leave a slot counted until server-side timeout. Unexplained queueing with nothing running is expected behaviour, not a bug. Set explicit client timeouts and close streams cleanly.
7. **Fleet load varies by hour.** Latency and throughput drift with time of day. Do not run one arm at 02:00 and another at 14:00 — use randomised blocks so each arm spans comparable conditions.

## 5. Empirical checks to run before scaling

Nothing below is answered by the documentation. Run these and record the results; they determine the scheduler design.

1. **Interpretation A vs B.** Serially call 4+ distinct models within a 5-minute window. If call 4 is merely slower → A (or B with LRU eviction). If it is refused → B with hard capping.
2. **Same-model vs cross-model concurrency.** 3 parallel calls to one model, then 3 parallel calls to three models. Compare latency and error rates.
3. **Queue depth.** Ramp parallel requests from 4 upward until rejections appear. Record the threshold.
4. **Rejection signature.** Capture the exact status code and `error` body of a queue-full rejection so it can be pattern-matched against a quota `429`.

## 6. Reproducibility hazards

`[DOCUMENTED]` Ollama retires cloud models on a rolling schedule with advance notice by email and website. `deepseek-v3.1:671b` and `deepseek-v3.2` were retired 2026-07-15 with `deepseek-v4-flash` named as successor; further retirements were scheduled for 2026-07-31.

> **Consequence:** a model identifier is not a stable experimental referent. Pin the exact tag, record the retrieval date, and capture any available build or version metadata alongside results. A pre-registered protocol naming only a model family cannot be replicated after a retirement.

`[DOCUMENTED]` Model weights are native as released, but on modern NVIDIA hardware may use accelerated data formats such as NVFP4. `[INFERRED]` Numerical behaviour may therefore differ from a local run of the "same" model, and may change without notice if the fleet's hardware mix changes. Do not treat cloud and local runs of one model as the same experimental condition.

`[DOCUMENTED]` Requests are served primarily from the United States, with routing to Europe and Singapore for additional capacity. `[INFERRED]` Region routing is not user-controllable and adds unmodelled latency variance.

## 7. Terms of service constraints

`[DOCUMENTED]` One account per person — no sharding a workload across multiple accounts to multiply concurrency.

`[DOCUMENTED]` No clause addresses circumventing rate or concurrency limits. The prohibited-use list does include automated access without permission, which sits oddly beside officially published Python and JS clients and issued API keys. `[INFERRED]` Ordinary scripted API use is plainly intended; treat the clause as boilerplate but avoid conduct that looks like limit evasion.

`[DOCUMENTED]` Prompt and response data is not logged or trained on; partner providers are contractually held to no-logging, no-training, zero-retention.

## 8. Facts an agent must not invent

- The queue depth.
- Whether the limit counts requests or resident models.
- The error code or message returned on queue-full rejection.
- Whether a `429` means "wait" or "stop".

If any of these matters to a decision and has not been measured, say so and stop rather than guessing.
