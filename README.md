# DeepReason

**A harness that makes an LLM argue with itself — on the record.**

You give it a hard, open "why" question. It has the model *conjecture* a
spread of bold explanations, then *criticize* them: each candidate must
state what evidence would refute it, weak ones get argued down, survivors
compete head-to-head, and the whole exchange is written to an append-only,
byte-for-byte replayable log. The model proposes; a deterministic harness
does all the bookkeeping and decides nothing on vibes. The output isn't one
confident paragraph — it's a *map* of which explanations survived scrutiny,
which died and exactly why, and where the evidence genuinely can't decide.

There are two ways to run it: the **full harness** (all the machinery) and
**MiniReason** (the measured reduced engine profile). Which to use is the
most important decision, so it has its own section below.

---

## Quickstart

### Reason over a text question

```bash
pip install .

deepreason setup
deepreason --config config/my-provider.yaml config compile \
  --schema-version 2 --workload-profile text --profile compact \
  --single-model gemma4:31b --rubric-policy forbid --out run-manifest.json
deepreason --root runs/my-question reason --text "why does X happen?" \
  --run-manifest run-manifest.json
```

The text-first path generates rival explanatory claims, compiles their
counterconditions into current-run commitments, criticizes the candidates,
and retains the surviving argument graph in a replayable run root. `setup`
stores provider credentials privately in
`~/.deepreason/credentials` (owner-only file; the key never appears in any
config, prompt, or log).

Long runs expose append-only, workload-neutral progress and can be watched or
resumed without replacing their bound manifest:

```bash
deepreason --root runs/my-question watch
deepreason --root runs/my-question continue --budget cycles=4 --token-budget 50000
```

### Advisory scratchpad and grounded answers

For an exploratory text run, enable `scratchpad.enabled: true` and
`bridge.mode: grounded_two_stage` in the typed source profile and compile a
RunManifest v3. The manifest freezes the bounded attention, coverage, role,
review, repair, and output policies before any model call:

```bash
deepreason setup
deepreason --config config/my-provider.yaml config compile \
  --schema-version 3 --workload-profile text --profile compact \
  --rubric-policy forbid --out run-manifest-v3.json
deepreason --root runs/my-question reason --text "Why might X happen?" \
  --run-manifest run-manifest-v3.json

# Loose notes need only content. Optional prompts stay optional.
deepreason --root runs/my-question scratch add \
  --content "A provisional mechanism worth revisiting."
deepreason --root runs/my-question scratch search "mechanism" --limit 10
deepreason --root runs/my-question scratch map --limit 10

# Stage A validates a claim ledger; Stage B composes only from that ledger.
deepreason --root runs/my-question bridge build <problem-prefix> --target answer
deepreason --root runs/my-question bridge claims --limit 25
deepreason --root runs/my-question bridge result
```

Scratch objects are immutable, advisory, and separate from the formal graph.
A scratch reference records intellectual provenance, never evidence. Links,
clusters, guides, attention, coverage, and embedding similarity can improve
navigation but cannot change a verdict, merge notes, or promote anything into
the ontology. The bridge visibly separates grounded facts, recorded
observations, supported inferences, surviving conjectures, explicit
assumptions, unknowns, and conflicting evidence. Novel conjectures are allowed;
category laundering is not. An unresolved or partial answer is a valid
successful result.

See the [ordinary-user guide](docs/SCRATCHPAD_GROUNDED_BRIDGE.md) and the
[v1.4 normative amendment](docs/harness-spec-v1.4-amendment.md). The guide also
shows the explicit, non-mutating `--derived-output` flow for v1/v2 run fences.

Pinned code, simulation, and Lean operations are available through
`deepreason code`, `deepreason simulate`, `deepreason prove`, and
`deepreason check-proof`. They evaluate only workload-declared commands,
finite inputs, and exact toolchains. A Lean pass means kernel acceptance under
the declared assumptions; it is not a proof that an informal or empirical
claim is true.

### Explicit skills and local memory

Cross-run skills and the optional brain are advisory inputs only. They never
transfer an old verdict, status, warrant, or evidence credit. Skill capsules
must come from a verified accepted source fence, and adopted tests are rerun
in the current run.

```bash
deepreason distill --source runs/source --seq 42 --artifact <id> \
  --draft capsule-draft.yaml --out capsule.json
deepreason --root runs/current skills --capsule capsule.json \
  --query "bounded partition" --school alpha --school blind

deepreason brain init ./my-brain
deepreason brain ingest ./my-brain notes.txt proof.lean
deepreason brain query ./my-brain "bounded partition" --day 2026-01-01
```

The brain path and every ingested file are explicit. Retrieval is bounded and
receipt-pinned; run-local snapshots can replay selected cards and bodies after
the external brain is removed. `brain inspect`, `reinforce`, `pin`, `unpin`,
`distill-run`, and `reindex` provide the remaining explicit maintenance
operations.

### Website compatibility workflow

```bash
pip install ".[browser]"
deepreason make "a pomodoro timer website"
```

`make` proposes designs, builds their components as
separately criticized problems, assembles them deterministically, loads the
result in headless Chromium, and exports surviving `.html` files you can
double-click
— with a README explaining why each survived. If nothing survives, it says so
and suggests more rounds: refutation is the tool working, not failing. The
two commands run the very same machinery as everything below and leave the
same replayable record in `runs/`.

For reproducible or small-model runs, compile routing before the first model
call and pass only the resulting immutable manifest to the workflow:

```bash
deepreason doctor --endpoint conjecturer --model gemma4:31b
deepreason --config config/my-provider.yaml config compile \
  --single-model gemma4:31b --profile compact --rubric-policy forbid \
  --out run-manifest.json
deepreason --root runs/dna make "the wonders of DNA" \
  --run-manifest run-manifest.json
```

Source YAML is read only while compiling. The run binds exact routes,
families, output mechanisms, profile, and concurrency in
`run-manifest.json`; endpoint models receive only one rendered role pack and
one output schema. They never receive configuration, model catalogs,
credentials, repository access, peer-model access, or workflow authority.
Implementation and evidence status are recorded in
[`docs/SMALL_MODEL_COMPATIBILITY.md`](docs/SMALL_MODEL_COMPATIBILITY.md).

### Full harness

```bash
pip install .
export DEEPSEEK_API_KEY=...            # any OpenAI-compatible provider works

# Run a typed problem payload to a token budget; the log lands in runs/<name>
deepreason --config config/my-provider.yaml config compile \
  --rubric-policy forbid --out run-manifest.json
deepreason --root runs/my-run run --budget cycles=12 \
  --problem problem.yaml --token-budget 200000 \
  --run-manifest run-manifest.json

# Turn a finished run into a committed, cited thesis (read-only over the run)
python scripts/thesis.py --root runs/my-run --problem pi-1
```

An MCP-capable client can invoke the same deterministic driver over stdio:

```bash
claude mcp add deepreason -- deepreason-mcp
```

Use the narrow `start_make` operation with a precompiled manifest, then read
progress through `make_status` and `make_result`. Do not appoint a general LLM
to inspect this repository, interpret provider YAML, select models, or operate
the workflow. Engine models are per-role source config, no code changes — see
[`docs/AGENT.md`](docs/AGENT.md).
Configuration has one typed source of defaults; YAML files are partial
profiles, and `deepreason config` prints the complete effective result.
Accepted website manifests can also request isolated, exact, run-local browser
libraries without changing this repository; see
[`docs/RUNTIME_IMPORTS.md`](docs/RUNTIME_IMPORTS.md).

### MiniReason

```python
from minireason.call import HttpEndpoint
from minireason.loop import run

run([("pi-1", "why did X happen?")],
    HttpEndpoint("https://api.deepseek.com", "deepseek-v4-flash", api_key=KEY),
    budget=30_000, root="runs/my-run")
```

The reduced control loop lives in [`mini/`](mini/); it reuses the full
package's canonical Harness, ontology, grounded/support adjudication,
anti-relapse guard, warrant plumbing, storage, route firewall, model profiles,
wire contracts, and bounded repair kernel so it cannot drift into a second
protocol. A v3 Mini run also uses `minireason.advisory.MiniAdvisorySession` to
reuse the exact parent scratch, attention, and two-stage bridge implementation;
it does not define a reduced advisory ontology. See
[`mini/README.md`](mini/README.md).

---

## What it's best at (and why)

The harness pays off on **hard, open, explanatory questions where you want
the whole space of rival answers mapped and stress-tested**, not a single
guess. It shines when:

- **You don't trust a one-shot answer.** A direct prompt gives you the
  model's most typical answer and hides the alternatives. This forces a
  *distribution* of candidates and then makes each one defend itself.
- **The question has falsifiable structure.** Each candidate must name what
  would refute it. That single discipline is what lets the harness reject
  hand-waving mechanically and argue substantively about the rest.
- **You want the disagreement made honest.** When two explanations both
  survive, it says so and names the evidence that would decide between
  them, rather than papering over it.

Concretely, good fits:

| Use case | Why the harness helps |
|---|---|
| Mapping rival explanations for an open research question | Generates the distribution, kills the unfalsifiable, keeps survivors with their attack surface |
| Design-space exploration against hard criteria | Forbidden-cases become the acceptance tests; survivors come with the criteria they met |
| Adversarial review of a claim ("steelman, then break it") | The critic/defender/trial loop argues both sides on the record |
| Producing a *defensible* conclusion, not just an answer | The thesis view commits to the best-supported survivor and cites the log |

We tested this end-to-end on "why does time have an arrow?" (see
`experiments/results/mini_arrow_comparison.md`, retired to git history; recovery
instructions in
[`experiments/results/INDEX_2026-07-13.md`](experiments/results/INDEX_2026-07-13.md)).
The full harness spun one question into a 224-problem graph, produced 20
argued survivors spanning every major position in the literature, and then
wrote a committed thesis citing its own record. MiniReason reconstructed the
same solution space for roughly **8% of the cost**.

**Research using the harness:**
[Can an LLM explore past its own repertoire?](docs/CAN_LLMS_EXPLORE.md) — a
write-up (with a call for replication and critique) on measuring when an
LLM's idea-generation stalls and what pushes it back out.

## When *not* to use it

Reach for a plain LLM call (or a search tool) instead when:

- **You want a fact or a lookup.** "What's the capital of X", "summarize
  this doc" — there's nothing to conjecture or refute.
- **There's one deterministic right answer.** Arithmetic, code that either
  compiles or doesn't, closed questions. The machinery adds cost, not value.
- **The question has no falsifiable structure.** If nothing could count as
  evidence against a candidate, the harness can't criticize it — it'll
  either reject everything or rubber-stamp it.
- **You're latency- or budget-sensitive.** This is deliberately
  token-heavy and slow next to a single prompt. It buys rigor, and rigor
  isn't free.

## Full vs Mini — pick one

The headline finding from our own testing: **generating good candidate ideas
is nearly free; the expensive machinery earns its keep only when the problem
is hard enough that criticism has something real to argue about.**

| | MiniReason (`mini/`) | Full harness (`src/`) |
|---|---|---|
| Scope / cost | reduced scheduler; measured cheap path | full system; ~10x+ the tokens in the referenced comparison |
| Criticism | mechanical only (a candidate's own falsifier checks) | + LLM critic, defender, cross-family judge trial |
| Problem graph | one problem, generate-and-filter | spawns a *graph* of follow-up problems |
| Ranking | offline calibrated judge (control-gated) | live pairwise discrimination + adjudication |
| Concludes | survivor list | committed, cited **thesis** view |

Rule of thumb: **start with MiniReason** to map the space cheaply. Graduate
to the full harness when you need substantive (not just mechanical)
refutation, follow-up problems, or a defended conclusion — and the answer is
worth paying for. A MiniReason run's log is forward-compatible: the full
harness can open it and keep going.

## What you can trust, and what you can't

**Trust:** every run is deterministic and byte-for-byte replayable from its
log; ontology records are immutable, event sequence numbers are continuous,
and historical views cannot write to the run they inspect. Object ids resolve
to one schema and one canonical record, so a conflicting registration or
merge fails loudly instead of changing history. Token accounting is checked
(`deepreason.invariants.verify_root` — it caught a real 1% leak in a
million-token run this project ran). Nothing is deleted; state is a pure
function of the append-only log.

**Read with care** (documented honestly in
[`docs/MINI_STRESS_REPORT.md`](docs/MINI_STRESS_REPORT.md) and the arrow
comparison):

- MiniReason's free criticism rejects candidates on **falsifier
  well-formedness**, not on whether the idea is *true* — it kills malformed
  tests, not wrong theories.
- The offline judge scores **how well a candidate is argued against a
  rubric**, which is a different axis from "which answer is deepest." Read
  its #1 as "best-argued in the bracket," not "correct."
- A thesis argues from **the run's own record**, not outside knowledge — it
  commits to what *this run* adjudicated, and will say so.

Security: model-authored forbidden cases cannot carry inline `predicate:`
expressions; the shared skeleton contract accepts known `program:` checks (and,
in full-engine rubric workflows, guarded rubric references). Predicate
commitments supplied by a trusted workload use the parent's AST guard against
the `eval` escape family. Execution-oracle candidates, checkers, generators,
and admission gates additionally run in fresh subprocesses with deterministic
line budgets and emergency OS resource containment; module top-level code
never runs in the harness process. See [`tests/test_security.py`](tests/test_security.py)
and [`tests/test_oracle.py`](tests/test_oracle.py).

## Development

```bash
pip install -e ".[dev]"
pytest                      # full suite (parent + mini)
```

Source is `src/deepreason/` (the full harness) and `mini/minireason/` (the
compact build). The normative baseline is
[`docs/harness-spec-v1.3.md`](docs/harness-spec-v1.3.md), amended explicitly by
[`docs/harness-spec-v1.4-amendment.md`](docs/harness-spec-v1.4-amendment.md).
The module-by-module map and operator contract live there and in
[`docs/AGENT.md`](docs/AGENT.md).

The installed-wheel portability gate is also runnable locally and makes no
provider calls:

```bash
python scripts/wheel_smoke.py
```
