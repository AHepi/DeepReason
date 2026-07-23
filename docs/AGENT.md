# Installing DeepReason V6 as a Deterministic Tool

DeepReason separates the model-facing role from the process-facing driver:

- **Engine role:** one operator-configured OpenAI-compatible provider.
- **Driver role:** DeepReason owns routing, policy, V6 input freezing,
  qualification projection, manifests, managed paths, and execution.

The public installed product is V6-only. A human performs provider setup and
explicit qualification once; a person or LLM then supplies only a question
and an optional bounded budget.

## Install

```bash
python -m pip install .
deepreason setup
deepreason qualify --yes
deepreason status --json
deepreason reason "Why can independent checks improve reliability?"
```

### As MCP tools (any MCP client)

```bash
deepreason mcp-registration
```

The command prints generic JSON containing the absolute installed
`deepreason-mcp` path. Copy it into the MCP client's configuration; DeepReason
does not modify client settings. The server speaks newline-delimited JSON-RPC
2.0 over stdio. Call `get_readiness`, then `start_run` with a question and
optional budget. Use the returned opaque `run_id` for `run_status` and
`run_result`. MCP accepts no provider, route, policy, credential, manifest, or
filesystem-path authority and cannot initiate qualification.

`deepreason status --json` is the stable machine-readable readiness boundary.
Bare `deepreason` prints the same readiness as human-readable text and exactly
one next action. Credential presence is reported only as a boolean.

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

Scratchpad and grounded-output operation is opt-in. It was introduced by
`--schema-version 3` and is also available to a compatible v4 policy. Source
configuration still passes through the same typed, unknown-key-rejecting
boundary. V3 freezes the eleven attention channels,
coverage cadence, embedding/fallback identity, bounded pack sizes, bridge
roles, ledger-amendment bound, schema/grounding repair limits, and output
policy. Versions 1 and 2 retain their original bytes and hashes and are never
migrated on open. See
[`SCRATCHPAD_GROUNDED_BRIDGE.md`](SCRATCHPAD_GROUNDED_BRIDGE.md).

## Opt-in RunManifest v4 authority

V4 adds a complete, strict `ControlPlanePolicyV1`. Compile it explicitly; the
runtime never upgrades a v1–v3 root or guesses a missing control policy:

```bash
deepreason --config config/my-provider.yaml config compile \
  --schema-version 4 --workload-profile text --profile compact \
  --rubric-policy forbid \
  --control-plane-policy control-plane-policy.json \
  --out run-manifest-v4.json
deepreason config inspect --run-manifest run-manifest-v4.json
```

The policy selects one complete repository-owned profile:

- `legacy` preserves historical scheduler and wire behavior;
- `shadow` records and compares conjecture control decisions while legacy
  actuation remains authoritative; and
- `active_conjecture` requires a durable work order before conjecturer
  dispatch and records provider, guard, context, repair, and terminal work
  transitions before their semantic effects.

Schools are conditioning lineages, not model identities. In
`conditioning_only`, several schools may intentionally share the conjecturer
route. In `route_bound`, each school has an exact role seat and endpoint
binding. Only the bound manifest plus the call's lease and route receipt prove
which model route ran; school count alone proves nothing about route diversity.

The active v4 turn may return candidates, a bounded semantic context request,
or an abstention. A request cannot contain paths, commands, tools, routes,
budgets, phases, or status changes. The harness grants or denies it under the
frozen policy and creates a fresh work order for a granted follow-up. Scratch
remains advisory, and an abstention creates no formal artifact.

Local schema repair stays within the rejected object or authorized subtree and
the original route, contract, and state fence. A whole-bridge workflow retry is
a separate manifest authority: it starts a fresh workflow under the same
sealed catalog, prompt policy, contract, and route. Typed failed calls remain
valid process traces when their route, attempts, usage knowledge, and spend are
honestly recorded; they are not successful semantic results.

V4 types terminal stop evidence around the existing deterministic
`StopController`. A typed `RESUMED` continuation is available only from a
typed deterministic converged `STOPPED` decision: it rechecks the immutable
manifest and controller, prior process and stop records, exact canonical
checkpoint bytes, event fence, and an empty outstanding-work snapshot before
new work may start. Completed, stuck, exhausted, budget, cancelled, and
untyped historical stops are not resumable through that transition. `PAUSED`
is not implemented. The implementation also does not establish that active
control improves semantic quality or cost. See
[`harness-spec-v1.5-amendment.md`](harness-spec-v1.5-amendment.md) and
[`JOLT_CONTROL_PLANE_MIGRATION.md`](JOLT_CONTROL_PLANE_MIGRATION.md).

## MCP tool surface

The default production surface is the following exact 17-tool,
harness-owned contract. All schemas are closed and bounded.

| Family | Tools | What they do |
|---|---|---|
| reasoning operation | `start_run`, `run_status`, `run_result`, `continue_run`, `cancel_run` | Start, inspect, continue, or safely cancel the manifest-bound harness at completed-cycle boundaries |
| website operation | `start_make`, `make_status`, `make_result` | Start one typed website workflow and read its operational status/result |
| scratch reads | `scratch_map`, `scratch_search`, `scratch_open`, `scratch_related`, `scratch_attention` | Browse immutable scratch history or preview bounded deterministic attention without committing visibility or receipts |
| grounded bridge | `start_bridge`, `bridge_status`, `bridge_result`, `bridge_claims` | Start the two-stage bridge and read replay-validated operational/result/ledger views |

The scratch MCP surface is deliberately read-only. It has no add, revise,
link, retire, cluster, receipt-write, guide-generation, or coverage-advance
tool. `scratch_attention` is a pure preview. Bridge status is operational and
non-epistemic; successful `underdetermined`, `insufficient_evidence`, partial,
conflicting, and outside-scope results are not tool errors.

Every run-starting operation accepts only a bounded root, typed workload, and
precompiled immutable manifest reference. The server does not infer routes or
read source YAML. Its one shared process-lock abstraction works on Windows,
macOS, and Linux; a busy root returns a typed busy result rather than racing a
second writer. Status and result tools never create a missing root.

`cancel_run` writes a run-bound operational request; it does not set status or
interrupt a provider call mid-transition. The scheduler observes it at the
next completed-cycle boundary. `continue_run` requires the same bound manifest
and verifies the prior stop, checkpoint, event fence, and operator lock before
appending. These operations must not be described as model-authored workflow
commands.

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

Only the exact 17 tools above are the supported production path. The server
intentionally exposes no generic prompt or model invoke, shell, arbitrary-file
read, provider credential, route edit, direct event/object write, scratch
mutation, guard bypass, or status setter. Endpoint models receive a compact
rendered pack and one output contract only; they receive no MCP tools.

All scratch text, source excerpts, relation phrases, IDs, handles, and bridge
text are untrusted data. They cannot influence routing. Requests reject path
traversal, unsafe manifest/control-file links, oversized payloads, unknown
fields, and mismatched canonical IDs without echoing rejected secrets.

CLI and MCP text runs translate their inputs into the same strict application
intents and use `TextRunApplicationService` for start, continue,
progress/watch, cancellation, and terminal result handling. Scratch queries
and grounded-bridge operations likewise pass through their shared application
services; direct scratch open is the one explicitly mutating query and owns
its process lock and visibility receipt. The services own dispatch, locking,
and durable lifecycle behavior, so the transport facades do not implement
competing loops. MiniReason's explicit v4 `shadow` path separately reuses the
parent conjecture application boundary and exact work-order, proposal, guard,
and transition records while retaining Mini's reduced generate/check/rotate
semantics. Its default historical path remains unchanged, and this does not
claim `active_conjecture` controller breadth. No client may append raw control
events, choose hidden routes, mutate manifests, set status, bypass a guard, or
implement an alternative scheduler loop.

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
