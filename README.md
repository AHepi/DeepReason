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
**MiniReason** (the measured ~20% that carries most of the value, in ~900
lines). Which to use is the most important decision, so it has its own
section below.

---

## Quickstart

### The two-command path (no configuration knowledge needed)

```bash
pip install ".[browser]"

deepreason setup      # one time: pick your AI provider, paste your API key
deepreason make "a pomodoro timer website"
```

`setup` asks two questions and stores your key privately in
`~/.deepreason/credentials` (owner-only file; the key never appears in any
config, prompt, or log). `make` proposes several complete single-file
websites, criticizes them (each candidate is really loaded in headless
Chromium; with a vision-capable provider a vision critic judges the rendered
screenshots), and exports the survivors as `.html` files you can double-click
— with a README explaining why each survived. If nothing survives, it says so
and suggests more rounds: refutation is the tool working, not failing. The
two commands run the very same machinery as everything below and leave the
same replayable record in `runs/`.

### Full harness

```bash
pip install .
export DEEPSEEK_API_KEY=...            # any OpenAI-compatible provider works

# Run a built-in problem suite to a token budget; the log lands in runs/<name>
python scripts/live_run.py --suite arrow --root runs/arrow --token-budget 200000

# Turn a finished run into a committed, cited thesis (read-only over the run)
python scripts/thesis.py --root runs/arrow --problem pi-arrow
```

Or drive it from any MCP-capable agent (it exposes a tool surface over
stdio):

```bash
claude mcp add deepreason -- deepreason-mcp
```

Engine models are per-role config, no code changes — see
[`docs/AGENT.md`](docs/AGENT.md).

### MiniReason

```python
from minireason.call import HttpEndpoint
from minireason.loop import run

run([("pi-1", "why did X happen?")],
    HttpEndpoint("https://api.deepseek.com", "deepseek-v4-flash", api_key=KEY),
    budget=30_000, root="runs/my-run")
```

Self-contained in [`mini/`](mini/) (pydantic only). See
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
[`experiments/results/mini_arrow_comparison.md`](experiments/results/mini_arrow_comparison.md)).
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
| Size / cost | ~900 lines; cheap | full system; ~10x+ the tokens |
| Criticism | mechanical only (a candidate's own falsifier checks) | + LLM critic, defender, 2-seat judge trial |
| Scope | one problem, generate-and-filter | spawns a *graph* of follow-up problems |
| Ranking | offline calibrated judge (control-gated) | live pairwise discrimination + adjudication |
| Concludes | survivor list | committed, cited **thesis** view |

Rule of thumb: **start with MiniReason** to map the space cheaply. Graduate
to the full harness when you need substantive (not just mechanical)
refutation, follow-up problems, or a defended conclusion — and the answer is
worth paying for. A MiniReason run's log is forward-compatible: the full
harness can open it and keep going.

## What you can trust, and what you can't

**Trust:** every run is deterministic and byte-for-byte replayable from its
log; token accounting is checked (`deepreason.invariants.verify_root` — it
caught a real 1% leak in a million-token run this project ran). Nothing is
deleted; state is a pure function of the append-only log.

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

Security: forbidden-case predicates use an AST guard against the `eval` escape
family. Execution-oracle candidates, checkers, generators, and admission gates
additionally run in fresh subprocesses with deterministic line budgets and
emergency OS resource containment; module top-level code never runs in the
harness process. See [`tests/test_security.py`](tests/test_security.py) and
[`tests/test_oracle.py`](tests/test_oracle.py).

## Development

```bash
pip install -e ".[dev]"
pytest                      # full suite (parent + mini)
```

Source is `src/deepreason/` (the full harness) and `mini/minireason/` (the
compact build). The normative design spec is
[`docs/harness-spec-v1.3.md`](docs/harness-spec-v1.3.md); the module-by-module
map and phase status live there and in [`docs/AGENT.md`](docs/AGENT.md).
