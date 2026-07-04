# Installing DeepReason as an Agent Tool

DeepReason is usable by any LLM on **both sides** of the loop:

- **As the engine** (the γ operator): any OpenAI-compatible provider —
  OpenAI, DeepSeek, ollama, llama.cpp server, most gateways — configured
  per role in the §15 role table. No code changes to switch models.
- **As the operator** (the agent driving the harness): any MCP-capable
  harness — Claude Code, Claude Desktop, Cursor, or a custom agent loop —
  installs the harness as a set of MCP tools. Non-MCP agents can shell
  out to the `deepreason` CLI, which exposes the same verbs.

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
deepreason --root .deepreason run --budget cycles=6 --token-budget 100000 \
    --problem problem.yaml --config config/my-provider.yaml
deepreason --root .deepreason report
deepreason --root .deepreason theory <id-prefix>
```

## Configure the engine LLM(s)

Copy `config/deepseek.yaml` and edit the role table — endpoint, model,
provider, reasoning, caps are all config (`llm/providers.py` maps the
neutral `reasoning` knob to each provider's wire format):

```yaml
roles:
  conjecturer: { endpoint: "https://api.openai.com/v1", model: gpt-5.2, temperature: 1.0,
                 api_key_env: OPENAI_API_KEY, reasoning: none, max_tokens: 4000, json_mode: true }
  judge:
    - { endpoint: "https://api.openai.com/v1",  model: gpt-5.2,          temperature: 0.0, api_key_env: OPENAI_API_KEY,   max_tokens: 1200, json_mode: true }
    - { endpoint: "https://api.deepseek.com",   model: deepseek-v4-pro,  temperature: 0.0, api_key_env: DEEPSEEK_API_KEY, max_tokens: 1200, json_mode: true }
```

API keys are read from the named environment variables — never from
files. Name a real model id in the table (`auto` resolution is a
convenience of `scripts/live_run.py` only). Two judge seats from
different model families satisfy the §9 cross-family rule properly.

## MCP tool surface (spec §13 verbs)

| Tool | What it does |
|---|---|
| `seed_problem` | Register a problem + commitments (+ optional rubric standard) |
| `run_cycles` | Fund N scheduler cycles under an optional hard token budget |
| `frontier` | Problems and their surviving artifacts |
| `theory` / `why` | Render an artifact's theory view / justification chain |
| `eval_report` | P6 metrics: per-role LLM stats, trial-guard blocks, capture dashboard |
| `docket` | Disagreement-ranked cases awaiting an appellate ruling (§10.6) |
| `appellate_rule` | Enter a ruling (a one-line holding calibrating a standard) |

## Rules of engagement for the operating agent

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
