# Diagnosis: the probe and the harness send different fields — the harness has never sent a bare `reasoning` string, and its own field carried 99 successful calls the day before the probe

## Stop report, section 4 (pasted verbatim, before anything of mine)

Source: `experiments/2026-09-03-change-provenance-history-channel/runs/home-m3/runs/run-5565bd1ef7011e3d25fef3197bdf1cdb`
(root) — the newest committed launch config, the one PARKED P2 names.

```
## 4. THE STOP, CLASSIFIED

Stop message: `(none recorded)`

Boxes ranked by evidence:

### 1. CONFIGURATION — RULED OUT

- evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.

### 2. ENVIRONMENT — RULED OUT

- evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.

### 3. MODEL — RULED OUT

- evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.

### 4. HARNESS — RULED OUT

- evidence RULING IT OUT: the run reached a clean terminal (state='completed', stop_reason='budget_exhausted'); there is no failure to attribute. Section 5 reports whether it can be continued.
```

All four boxes are RULED OUT because this launch config has no failure to
attribute: with `reasoning: "none"` bound on all eleven seats it ran to a
clean terminal. Section 1 of the same report confirms what was bound —
every seat row reads `reasoning | none`, and the `split` column reads
`not observed in this run`, so each call was a single leg carrying the
seat's own reasoning value rather than a two-leg split that could have
substituted a different one.

Primary cause: **PARKED P2 conflates the configuration VALUE `"none"`
with the wire FIELD `reasoning`.** They are the same word in two
different places. The committed launch config does bind the value
`"none"` (section 1's seat rows), but `llm/providers.py::_ollama_reasoning`
realises that value as `reasoning_effort`, never as `reasoning` — so the
body the harness puts on the wire has no `reasoning` key at all, and the
Go decoder error P2 records (`ChatCompletionRequest.reasoning of type
openai.Reasoning`) names a field the harness has never sent. What
remains genuinely open is narrower than P2 states and is not decidable
from the record: whether the provider ALSO stopped accepting
`reasoning_effort` as a string in the same change. Section 3 of the same
report gives the last measurement — 99 attempts, zero faults — from
2026-09-03, one day before the probe.

Evidence:

- `experiments/.../run-5565bd1ef7011e3d25fef3197bdf1cdb/run-manifest.json`
  → all eleven roles carry `reasoning: 'none'`; the critic seat's route is
  `provider: 'ollama'`, `base_url: 'https://ollama.com/v1'`,
  `model_id: 'qwen3.5:397b'`. This is P2's premise, and it is correct as
  far as the VALUE goes.
- The same root's `objects/workflow-provider-attempt-v1/*.json`, all 99 of
  them → `outcome: "provider_result"` on every one, 99 193 completion
  tokens in total, zero attempts with any other outcome. Stop report
  section 3 reports the same census per seat with `faults | none`. This is
  the harness's own wire shape succeeding live.
- `git log -1 --date=iso` on that root's `run-status.json` →
  `2026-09-03 04:54:24 +0000`. The probe recording the refusal is dated
  2026-09-04 (`experiments/2026-09-04-experiment-blind-critic/SPEC.md`
  M5). The two measurements are one day apart, so the successful census
  above bounds when the provider's behaviour could have changed but does
  not extend past it.
- `OpenAICompatEndpoint.build_body` driven with that route's exact fields,
  this session:

      BODY: {"max_tokens": 8192, "messages": "<elided>", "model": "qwen3.5:397b",
             "reasoning_effort": "none", "response_format": {"type": "json_object"}}

  and the adapter table for the neutral value `"none"`:

      ollama    {"reasoning_effort": "none"}
      openai    {"reasoning_effort": "minimal"}
      deepseek  {"thinking": {"type": "disabled"}}
      generic   {}

  No provider adapter emits a key named `reasoning`.
- `docs/map/SUB-llm.md` `Traps` → three recorded traps, none about the
  reasoning field's wire shape. This is a new failure mode, not a
  recurrence.
- Census of every committed `provider.yaml` and every committed
  `run-manifest.json` → exactly two provider/base_url pairs appear,
  `ollama https://ollama.com/v1` and `generic http://127.0.0.1:48789/v1`
  (a local stub). The catalog the goal must cover is one live provider.

Implicated code:

- `src/deepreason/llm/providers.py:66-79` — `_ollama_reasoning`, the
  function that decides the field name and nesting.
- `src/deepreason/llm/endpoints.py:460` — `build_body`, which merges that
  dict into the request body.
- `src/deepreason/llm/providers.py:99-104` — `REASONING_ADAPTERS`, the
  per-provider table.

Falsifiable prediction: what `dr-reproduce` must show.

1. Offline, decidable now: for the committed critic route,
   `build_body(...)` contains the key `reasoning_effort` and does NOT
   contain the key `reasoning`; and every entry in `REASONING_ADAPTERS`
   emits either no key or a provider-specific one, never a bare
   `reasoning` string.
2. Live, needs the key, and DECIDES whether any code changes:
   one authenticated POST to `https://ollama.com/v1/chat/completions`
   carrying the harness's own body above.
   - HTTP 200 with non-empty content → Reading B holds: the committed
     launch configs were never affected, P2's premise is the defect, and
     the deliverable is the recorded contract plus a regression pinning
     the shape.
   - HTTP 400 with the unmarshal error → Reading A holds: the provider
     rejects the harness's field too, and `_ollama_reasoning` must send
     whatever shape it now expects.

Ruled out: **"the run succeeded because the reasoning field was dropped
before the wire."** Two independent things would have to be true for
that, and neither is. `llm/split.py` can override the emission leg's
reasoning value from a model-profile document, but stop report section 1
records `split | not observed in this run` for all eleven seats, so no
split leg ran. And `llm/firewall.py::EndpointLease.verify` compares
`endpoint.reasoning` against `route.reasoning` on every dispatch and
raises `ROUTE_LEASE_MISMATCH` if they differ, so an endpoint that had
silently dropped the value could not have dispatched at all — let alone
99 times.

## Note for the fix phase, recorded here so it is not re-derived

`route_fingerprint` (`llm/firewall.py:115-123`) hashes
`Route.model_dump()`. `Route.reasoning` carries the NEUTRAL value
(`'none'`), which is configuration and not wire shape; the wire shape is
produced downstream in `reasoning_body` and never enters a Route. The
forecast is therefore that a change confined to `_ollama_reasoning`
leaves every committed `route_sha256` unmoved. That is a forecast, and
the fix phase must confirm it with `tools/blast_radius.py` rather than
with this paragraph.
