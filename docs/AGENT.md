# Installing DeepReason as a Deterministic Tool

DeepReason separates the model-facing role from the process-facing driver:

- **Engine role** (the γ operator): any OpenAI-compatible provider —
  OpenAI, DeepSeek, ollama, llama.cpp server, most gateways — configured
  per role in the §15 role table. No code changes to switch models.
- **Driver role:** the deterministic CLI or narrow MCP operations compile an
  immutable `RunManifest`, bind exact endpoint leases, and invoke the harness.
  A general LLM is not a supported repository-level operator. Do not ask one
  to browse YAML, assign roles, choose/fallback models, spawn peers, repair
  policy, or decide workflow transitions.

## Install

```bash
pip install .            # from the repo root; installs `deepreason` + `deepreason-mcp`
```

### As MCP tools (any MCP client)

```bash
# Claude Code
claude mcp add deepreason -- deepreason-mcp

# Generic MCP client config (stdio transport)
{ "mcpServers": { "deepreason": { "command": "deepreason-mcp" } } }
```

The server speaks newline-delimited JSON-RPC 2.0 over stdio (MCP stdio
transport) with zero dependencies beyond the package.

### As a CLI (any agent that can run commands)

```bash
deepreason --root .deepreason --config config/my-provider.yaml \
    run --budget cycles=6 --token-budget 100000 --problem problem.yaml
deepreason --root .deepreason report
deepreason --root .deepreason theory <id-prefix>
```

## Compile the engine LLM route(s)

Copy `config/deepseek.yaml` and edit the role table. It is a partial profile:
omitted knobs inherit the one typed default schema, and unknown knobs fail
validation instead of being silently ignored. Run `deepreason config` to see
all built-in values, or `deepreason --config your.yaml config` to see the
fully resolved profile. Endpoint, model, provider, reasoning, and caps are all
config (`llm/providers.py` maps the neutral `reasoning` knob to each provider's
wire format):

```yaml
roles:
  conjecturer: { endpoint: "https://api.openai.com/v1", model: gpt-5.2, temperature: 1.0,
                 api_key_env: OPENAI_API_KEY, reasoning: none, max_tokens: 4000, json_mode: true }
  judge:
    - { endpoint: "https://api.openai.com/v1",  model: gpt-5.2,          temperature: 0.0, api_key_env: OPENAI_API_KEY,   max_tokens: 1200, json_mode: true }
    - { endpoint: "https://api.deepseek.com",   model: deepseek-v4-pro,  temperature: 0.0, api_key_env: DEEPSEEK_API_KEY, max_tokens: 1200, json_mode: true }
```

API keys are read from named environment variables and never written into a
manifest, prompt, or log. YAML and `model: auto` / `auto-alt` are source
configuration only: `deepreason config compile` resolves them before the
first role-model call and production manifests reject unresolved sentinels.
Runtime adapters consume only the frozen route matrix. Two judge seats from
different model families satisfy the §9 cross-family rule properly.

```bash
deepreason doctor --endpoint conjecturer --model gemma4:31b
deepreason --config config/my-provider.yaml config compile \
  --single-model gemma4:31b --profile compact --rubric-policy forbid \
  --out run-manifest.json
deepreason config inspect --run-manifest run-manifest.json
deepreason --root runs/example run --budget cycles=6 \
  --problem problem.yaml --run-manifest run-manifest.json
```

`--single-model` copies one explicitly configured concrete route to every
active legal role. It never searches a second provider. Rubric input requires
a frozen second judge family; otherwise compilation fails with
`SECOND_JUDGE_FAMILY_REQUIRED`. `--rubric-policy forbid` is valid only for
program/predicate workloads and rejects rubric-bearing input at preflight.

## MCP tool surface

The default production surface is deliberately limited to three
harness-owned website operations:

| Tool | What it does |
|---|---|
| `start_make` | Start one website workflow from a typed problem and precompiled manifest reference |
| `make_status` | Read operational progress without changing harness state |
| `make_result` | Read terminal result metadata and output paths |

The historical spec §13 research/operator surface is quarantined. It is
available only when a human explicitly starts the server with
`DEEPREASON_ENABLE_LEGACY_MCP=1`; endpoint models must never receive it:

| Legacy tool | What it does |
|---|---|
| `seed_problem` | Register a problem + commitments (+ optional rubric standard) |
| `run_cycles` | Fund N scheduler cycles under an optional hard token budget |
| `frontier` | Problems and their surviving artifacts |
| `theory` / `why` | Render an artifact's theory view / justification chain |
| `eval_report` | P6 metrics: per-role LLM stats, trial-guard blocks, capture dashboard |
| `docket` | Disagreement-ranked cases awaiting an appellate ruling (§10.6) |
| `appellate_rule` | Enter a ruling (a one-line holding calibrating a standard) |
| `research_docket` | Open evidence requests awaiting retrieval (§12) |
| `submit_evidence` | Register CANDIDATE evidence you retrieved for a request |
| `report_research_failure` | Record a failed retrieval attempt (operational, not evidence) |

## Legacy research loop (§12)

With `RESEARCH_BACKEND: "agent"` (the default), the harness does no web
fetching of its own — YOU are the retrieval arm, through an explicit,
logged channel:

1. Read `research_docket` — each entry is an observation-valued commitment
   with no covering evidence. Under a `research-agent-requested` signal
   (the grounding-decay brake), treat the named entries as the
   highest-priority grounding task.
2. Search and fetch with your OWN tools (web search, browsing — your
   credentials, never the harness's).
3. On success, `submit_evidence` with the source and the retrieved text.
4. On failure (blocked site, nothing found, timeout),
   `report_research_failure` with the reason — a failed fetch is an
   operational event on the record, never evidence and never a verdict.
5. Let the harness do the rest: your submission enters as an ordinary
   attackable import artifact depending on an attackable
   source-reliability claim, gets checked against the problem's
   relevance/scope commitments, and covers the request only while it
   remains accepted and supported.

What submission does NOT do: it does not certify the source (the
reliability claim stays attackable), does not adjudicate the underlying
claim, does not mark the research problem solved, does not edit λ, and
does not touch any status. You return candidate evidence; the court does
the rest. Your claimed retrieval time is stored as claim metadata — event
time and ordering are harness-controlled.

`start_make`, `make_status`, and `make_result` are the supported production
path. The server intentionally exposes no generic model invoke,
shell, arbitrary-file, route-edit, guard-bypass, event-write, or status-set
operation. Endpoint models receive rendered packs only and have no tools.

## Rules for the explicitly enabled legacy client

The tool surface enforces these, but state them in your agent's prompt
so it doesn't fight the harness:

1. **You cannot set a status.** Acceptance and refutation are computed
   by deterministic adjudication over warrants. There is no tool that
   overrides them — do not look for one.
2. **Your judgement enters ONLY through the docket.** `appellate_rule`
   on a docketed case is the sanctioned, budgeted channel
   (`USER_RULINGS_BUDGET`). Rulings calibrate standards; they do not
   flip individual verdicts.
3. **Nothing is deleted.** Re-seeding an existing id is an error; a bad
   artifact is answered by criticism, not removal.
4. **Metrics steer attention, never status.** Use `eval_report` and
   `frontier` to decide where to fund cycles next, not as verdicts.
5. **Budget every run.** Pass `token_budget` to `run_cycles`; the meter
   stops the run gracefully and the state stays consistent — you can
   always fund more cycles later; the log is the source of truth.

A typical operating loop: `seed_problem` → `run_cycles` (small budget) →
`eval_report` + `frontier` → read `theory`/`why` on survivors → clear the
`docket` with rulings where standards disagree → fund more cycles.

These rules govern driving the harness *on a problem*. When the task is
improving the harness *itself* from its experiment record, follow
[`docs/SELF_IMPROVEMENT.md`](SELF_IMPROVEMENT.md) instead — start from the
latest `experiments/results/INDEX_*.md`, pre-register before running, and
never change code without a report to cite.

## The positive playbook (what TO do)

The rules above are prohibitions; these are the moves. (Live operator
probes showed models follow the written rules but miss every mechanic
that was unwritten — see docs/OPERATOR_DIAGNOSIS.md.)

**If a verdict looks wrong to you — a critic you believe is mistaken has
refuted good work — you criticize the critic.** Every warrant carries an
attackable validity node ν ("this verdict is sound"); when criticism
lands on ν or on the critic artifact and survives adjudication, the
original target is REINSTATED automatically. Reinstatement is computed,
never granted. Concretely: read `why(<refuted-id>)` to find the attacker,
then fund more cycles — the argumentative critic attacks accepted
artifacts including critics — or, in hostile cases, seed a problem whose
criteria target the critic's weakness. You never need (and never have) a
tool that flips the verdict directly.

**What `appellate_rule` actually does — and does not.** A ruling enters
case law for a STANDARD: it is rendered into FUTURE trial packs for that
standard (a precedent slice), shifting how the judge reads borderline
cases from now on. It does NOT re-adjudicate any existing verdict, does
not touch the artifact you were looking at, and takes the standard's
spec id (e.g. `std-hist`) — not a severity label — as its `standard`
argument. Worked example: the docket shows case `c-42` where two judges
split over whether "the model is memorizing" names a mechanism. Ruling:
`appellate_rule(case_id="c-42", holding="Naming a training-data pathway
(memorization of benchmark X) IS a mechanism for this standard",
standard="std-explain")`. Effect: future trials under `std-explain` see
that holding; the artifact in `c-42` is unchanged until criticism or a
new trial moves it.

**Reading results without fooling yourself.** An empty frontier on a
hostile problem is success (nothing uncriticizable was admitted); a
budget stop is graceful (fund more cycles on the SAME root); refutations
are progress, not damage. The truth of a run is in its log, not its exit:
`narrate` renders the log as readable reasoning, and `run_cycles` returns
an accounting reconciliation (metered vs logged tokens) — if those
diverge, stop and investigate before trusting any metric.

**Engine calls need pinned reasoning and generous caps.** Reasoning-mode
models silently burn the whole completion budget on thinking and return
EMPTY output with no error (observed live on the strongest models). Every
role in your config should set `reasoning` explicitly and a `max_tokens`
with headroom; when an engine returns empty or truncated output, suspect
the cap before the model.
