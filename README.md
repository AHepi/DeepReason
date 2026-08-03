# DeepReason

**A deterministic reasoning harness that makes an LLM argue with itself on
the record.**

DeepReason takes a difficult explanatory question, generates rival
conjectures, criticizes them, and preserves the resulting reasoning in an
append-only, replayable record. The model proposes content; the harness owns
policy, authority, accounting, and durable state.

The installed public product is V6-only and question-first. Callers provide a
question and, optionally, a finite budget. DeepReason owns input freezing,
manifest construction, policy, routing, qualification projection, credentials,
managed storage, and run identity.

## Install and operate the wheel

Install the built wheel rather than treating a source checkout as the public
product:

```bash
python -m pip install /path/to/deepreason-0.1.0-py3-none-any.whl
```

The supported CLI workflow is:

```bash
deepreason setup
deepreason qualify --yes
deepreason status
deepreason status --json
deepreason reason "Why can independent checks improve reliability?"
```

`deepreason setup` creates one strict provider profile. The profile contains
provider and model identity, finite capacities, and the name of a credential
environment variable; it contains no credential value. If that referenced
credential is already available in the environment or the separate
setup-managed credential store, setup reuses it. Credentials must never be
placed in manifests, MCP payloads, logs, or documentation examples.

`deepreason qualify` is a separate, explicit action. Qualification cases
dispatch concurrently (default 4 workers; `--concurrency` or
`DEEPREASON_QUALIFY_CONCURRENCY` adjusts it, and 1 restores strictly
sequential dispatch for rate-limited providers) — the persisted report is
byte-identical at any worker count because assembly is canonical
(pair, case) order. Before any qualification
dispatch it identifies the configured provider and model and announces the
maximum expected provider-call counts for both batteries. Interactive use asks
for confirmation. For noninteractive use, `deepreason qualify --yes` is the
supported explicit confirmation form; `--json` may be added for
machine-readable output (the payload names the concluded `tier`). A completed
qualification for the same qualification subject is reused, so ordinary
questions do not repeat it.

### The qualification tier ladder

The whole point of qualification is to return the largest package the
configured model can actually serve. `deepreason qualify` therefore always
concludes with one durable tier for the exact behavior subject:

1. **`full`** — every frozen V6 route/contract pair passed the production
   battery (announced ceiling: at most 840 provider calls under the current
   engaged preset). Full `deepreason reason` is available.
2. **`shallow`** — the model failed the full battery but passed a small
   shallow-fitness battery: 6 live cases against the MiniReason compact wire
   contract with mini's own bounded repair protocol (announced ceiling: at
   most 18 further provider calls; at least 5 of 6 cases must produce
   schema-valid output). The reduced engine is available:
   `deepreason reason --shallow "YOUR QUESTION"`.
3. **`unqualified`** — the model failed both batteries. The next action stays
   `deepreason qualify` (an explicit rerun retries the ladder from the top).

Tier conclusions are durable and reusable exactly like full evidence: they
are keyed by the same qualification-subject digest, so any change to the
provider profile, preset, or contract surface invalidates them and requires
requalification. Full `deepreason reason` on a shallow-tier subject is
refused with a typed error (`QUALIFICATION_TIER_SHALLOW`) that names the
recorded tier and the shallow command — it never silently degrades. A
transport outage during the shallow battery records nothing
(`QUALIFICATION_SHALLOW_EXECUTION_FAILED`): an outage is not evidence.

`deepreason status` reports provider and V6 qualification readiness as text.
`deepreason status --json` reports the same readiness through the stable
machine-readable boundary. Both expose credential presence only as a boolean
and return one next action. A shallow-tier subject reports
`qualification_state: ready_shallow` with the shallow command as its next
action; `ready` (and MCP `start_run`) remains reserved for the full tier.

`deepreason reason "question"` prepares and runs one managed V6 text inquiry.
The optional `--cycles` and `--token-budget` arguments narrow or select a
finite public budget. The implemented defaults are 6 cycles and 100,000
tokens; the fixed public ceilings are 12 cycles and 200,000 tokens.

```bash
deepreason reason "Why does this failure recur?" --cycles 4 --token-budget 60000
```

The public `reason` command accepts no caller-owned run root or manifest path.
It freezes the question, constructs and binds the V6 manifest, projects the
reusable qualification, allocates managed storage, launches through the
application service, and returns a terminal JSON result with an opaque
`run_id`.

### Reasoning over documents

```bash
deepreason reason "What does this study conclude?" --attach study.pdf
```

`--attach` (repeatable; files or directories) admits documents as frozen
evidence for exactly this question and binds them into the run identity in
one step, printing the minted evidence dossier digest so the run stays
reproducible. Plain text, markdown, and CSV/TSV are parsed natively; PDF and
EPUB go through the built-in sandboxed adapters. A document that cannot be
admitted is refused with a typed reason, never silently skipped. The
two-step form remains available for parse-once/reason-many workflows:
`deepreason admit FILES --problem "question"` followed by
`deepreason reason "question" --dossier DIGEST`.

### Changing the question, or adding evidence, after a run has stopped

When the result shows you the question you should have asked, or the
evidence you should have had, `deepreason amend` adds to a stopped run
instead of replacing it:

```bash
# add evidence, reshape the question, or both
deepreason --root RUN_ROOT amend \
  --attach new-paper.pdf \
  --reshape-question "Under what conditions does the effect reverse?"

# then carry on in the same run
deepreason --root RUN_ROOT continue --budget cycles=4
```

The reshaped question enters as a new problem and gets first claim on the
next continuation's budget. Everything the run already established stays:
the old question keeps its record, its rival positions, its accepted
answers, and their status. Nothing is deleted, edited, or re-scored — the
record can still show you exactly what you used to be asking and what
survived it.

New documents are admitted the same way `--attach` admits them at the start:
same parser, same typed refusals, their own evidence dossier with its own
digest. Evidence is cumulative, so later cycles reason against the old and
new material together, and a quotation that was byte-verified against the
original evidence verifies identically afterwards. A file already admitted
to the run is refused up front — an amendment adds evidence, it does not
re-add it.

`amend` refuses, with a typed reason, unless the run is standing at a real
terminal stop, and refuses an amendment that would change nothing. Each
amendment is one epoch, chained to the last behind a declared position in
the run's history, so replay validates each side of that boundary against
the evidence and question in force there. If the process dies mid-amendment
the run says so and will not continue until the amendment is completed or
replaced — it never half-applies.

What an amendment cannot do is change the run's routing, budgets, policy, or
provider profile. Those stay frozen for the life of a run, which is what
lets an amended run keep its existing qualification instead of requalifying.
If you need different machinery, you need a different run.

### The local web page

```bash
deepreason web
```

`deepreason web` opens a local browser page for people who never use a
terminal beyond this one command: type a question, optionally attach
documents, watch progress, and read the result with its uncertainty intact.
The page is served on loopback only, requires a per-process API token, and
is a thin shim over the same closed MCP tool surface — it can do nothing
the validated facade cannot.

### Shallow (reduced-engine) mode

```bash
deepreason reason --shallow "Why does this failure recur?"
```

`--shallow` runs the MiniReason reduced engine (generate/check/rotate) against
the configured provider profile. MiniReason ships inside the wheel and has two
declared purposes: an explicit low-cost option for any user, and the supported
fallback for small models that cannot complete full production qualification
(the `shallow` tier above). Shallow mode needs only a valid profile and a
present credential — it never consults or writes the qualification cache, and
works for both `shallow`- and `full`-tier subjects. Its result is always
labeled shallow: no V6 qualification, transactions, or terminal commitment
authority.

### The engaged public preset

Public preparation compiles one repository-owned policy preset
(`deepreason.v6.engaged.v1`). Its capabilities, all finite and modest:

- **Advisory scratch** — bounded scratch authoring and bounded
  model-requestable scratch context, with the deterministic hashing embedder.
- **Foreign-school criticism** — every seeded public school bound to the
  single provider critic seat, observe-only, minimum one foreign school per
  accepted school artifact.
- **Grounded two-stage bridge** — review-free single-route shape: a frozen
  summarizer builds the claim ledger, a frozen thesis route composes at most
  four grounded output sections.
- **Local simulation** — declarative-numeric proposals only, at most one
  proposal per turn and two executions per run, executed on one frozen local
  no-network toolchain pinned to the preparing interpreter at manifest
  compile time (never a hardcoded path). Model-authored Python never reaches
  the local runner; an operational failure is recorded, not treated as
  refutation. Research capability remains OFF (on hold).

The installed module entry point uses the same parser:

```bash
python -m deepreason status --json
python -m deepreason reason "Why can independent checks improve reliability?"
```

To obtain generic, secret-free MCP stdio registration JSON for the installed
server, run:

```bash
deepreason mcp-registration
```

The result names the absolute installed `deepreason-mcp` executable and has no
environment block. DeepReason prints the registration; it does not alter an
MCP client's configuration.

## MCP public facade

The installed MCP server exposes exactly twenty tools. All input schemas are
closed and bounded.

| Tool | Public authority |
|---|---|
| `get_readiness` | Read secret-free provider and qualification readiness. |
| `start_run` | Prepare and start one normal question with an optional bounded budget and optional local document attachments admitted as frozen evidence. |
| `run_status` | Read current lifecycle and append-only progress for an opaque managed run ID. |
| `run_result` | Read the fixed terminal result for an opaque managed run ID. |
| `run_findings` | Read a replay-derived findings summary: rivalry sets, refutations with their attackers, suspended positions, spawned side branches with worked/starved status, and the criticism and capability ledgers. |
| `amend_run` | Admit further evidence and/or reshape the central question of a stopped managed run, as an appended epoch that supersedes neither its record nor its earlier evidence. |
| `continue_run` | Request bounded continuation of the same managed run when durable lifecycle authority permits it. |
| `cancel_run` | Request cancellation at the next safe completed-cycle boundary. |
| `scratch_map` | Read a bounded cluster map from immutable advisory scratch history. |
| `scratch_search` | Run bounded deterministic literal search over advisory scratch blocks. |
| `scratch_open` | Preview one immutable scratch block and bounded relationships without recording attention. |
| `scratch_related` | Read bounded explicit, cluster, and retrieval-only similarity neighbours. |
| `scratch_attention` | Preview a deterministic bounded attention plan without committing a receipt or visibility. |
| `start_bridge` | Start the harness-owned grounded bridge for an existing managed, bound, qualified V6 run. |
| `bridge_status` | Read bridge operational status with terminal replay validation. |
| `bridge_result` | Read a bounded replay-validated grounded result. |
| `bridge_claims` | Read a bounded replay-validated claim ledger. |
| `get_capabilities` | Read a bounded summary of the public MCP surface. |
| `get_help_topic` | Read one bounded help topic. |
| `get_request_requirements` | Read the information required by a supported operation. |

`get_readiness` must report ready before `start_run` may prepare or execute
anything, and its response carries plain-language guidance naming the one
next terminal command so a host model can walk a first-time user through
setup without assuming they know what an endpoint or an API key is.
`start_run` accepts only a nonblank question, an optional budget whose
cycles and token budget remain within the public ceilings, and optional
bounded local document paths admitted as frozen evidence for exactly that
question (the response reports the minted dossier digest and any typed
refusals). It returns an opaque `run_id`; lifecycle, scratch, and bridge
operations resolve that ID inside host-managed storage.

MCP callers cannot supply filesystem roots, manifest paths or references,
provider selection, routes, provider-profile paths, credential references,
qualification authority, policy, or plaintext keys. Qualification is an
operator CLI action and is not an MCP tool.

Continuation is not a generic request to keep going. It appends to the same
run only when replayed durable state grants typed lifecycle authority,
including the required stop, checkpoint, event fence, manifest identity, and
empty outstanding-work conditions. Cancellation is likewise operational: it
is observed at a safe completed-cycle boundary and does not let a caller set
epistemic status.

Amendment is narrower still: `amend_run` carries exactly the CLI `amend`
authority described above — question and evidence only, from a valid
terminal stop, everything earlier byte-identical — and cannot set epistemic
status, retract a refutation, or reach evidence already admitted.

Terminal state alone is not sufficient evidence of valid success. The current
V6 terminal commitment must have a fresh matching replay-validation binding,
and the terminal verification summary must report valid security and
integrity evidence. Invalid security or integrity produces a failing CLI
result even if a stored payload says `completed`.

## Architecture and safety

V6 freezes the input and its complete criteria before execution, then binds
their digest into an immutable manifest. A changed question or criterion is a
new run, not an in-place edit. Manifests contain exact route, contract, policy,
budget, and qualification projection identities, but never credential values.
Endpoint models receive bounded role material and an output contract; they do
not receive configuration, credentials, model catalogues, repository access,
MCP tools, or workflow authority.

Objects are immutable and the event log is append-only. Replay reconstructs
workflow and capability state and verifies canonical identities. Terminal
commitments bind one terminal epoch, stop record, result draft, event horizon,
and replay-validation result. Continued work opens a new typed epoch without
deleting earlier stops.

Scratch content is immutable, advisory material. Scratch links, clusters,
similarity, coverage, and attention can assist exploration but cannot become
evidence, satisfy a criterion, change a verdict, or grant authority. The
grounded bridge keeps facts, observations, supported inferences, conjectures,
assumptions, conflicts, and unknowns distinct. A partial, conflicting, or
underdetermined answer can be a valid successful result.

Deterministic adjudication, not model prose, determines formal status.
Qualification proves the configured provider/model can satisfy the frozen V6
production contracts; it does not prove that any later substantive answer is
true.

## Unsupported and historical boundaries

RunManifest versions 1–5, caller-owned run roots and manifest paths, the
retired website workflows and their MCP tools, and the removed `make`,
`prove`, `check-proof`, `code`, `simulate`, `focus`, `expand`, `attack`, and
`step` commands are all outside installed public operation. MiniReason ships
in the wheel solely as the engine behind `deepreason reason --shallow`.
Historical examples elsewhere in the repository are not installed-wheel
instructions.

## Operating this repository

Everything above is the installed product. Working ON the repository —
running live experiments, modifying source, diagnosing a defect — is a
different activity with its own law and its own manual:

- **`CLAUDE.md`** is the operating law: environment preflight, the gate,
  frozen surfaces, live-run rules, and the two workflow families every
  substantive change must route through.
- **`.claude/skills/dr-drive-harness/SKILL.md`** is the driving manual for
  any agent (or person) new to the repo: how to run the harness properly,
  and where to look before modifying anything or when something breaks.
  `.claude/skills/README.md` indexes the full workflow skill set.
- **`docs/map/INDEX.md`** navigates the 125k-line source tree; read
  `docs/map/INV-frozen-surfaces.md` before designing any change.

Developer install and tests:

```bash
python -m pip install -e ".[dev]"
python -m pytest tests/ -q -n 4     # the gate; 0 failed is the only pass
```

Production code lives under `src/deepreason/`. Public behavior derives from
the installed entry points, closed MCP schemas, application services, and V6
tests — not from retired examples in repository history.
