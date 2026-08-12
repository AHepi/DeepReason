# Operating DeepReason V6

This document is the public operating contract for a person or unfamiliar LLM
using the installed DeepReason wheel. The installed product is V6-only and
question-first.

The caller supplies a normal question and may supply a finite bounded budget.
DeepReason owns input freezing, manifest construction, policy, provider
routing, reusable qualification projection, credential resolution, managed
storage, application dispatch, replay, and terminal authority.

## Installed CLI workflow

Install the current wheel:

```bash
python -m pip install /path/to/deepreason-0.1.0-py3-none-any.whl
```

Then use the public sequence:

```bash
deepreason setup
deepreason qualify --yes
deepreason status
deepreason status --json
deepreason reason "Why can independent checks improve reliability?"
```

`setup` writes a strict provider profile containing provider/model identity,
finite model capacities, and only a credential environment-variable name.
The credential value is resolved separately from the environment or the
setup-managed credential store. Never put credential values in profiles,
manifests, MCP payloads, logs, prompts, or examples.

Qualification is explicit and reusable. `deepreason qualify` announces the
provider, model, and maximum expected provider-call counts before dispatch and
asks for confirmation on an interactive terminal. `deepreason qualify --yes`
is the supported noninteractive confirmation form. Add `--json` when
machine-readable qualification output is required; the payload names the
concluded `tier`. A valid cached qualification for the same subject is reused.

Qualification concludes on a tier ladder, and the conclusion is durable:

- `full` — every frozen V6 route/contract pair passed the production battery
  (announced ceiling: at most 840 provider calls under the current engaged
  preset). `deepreason reason "..."` is available.
- `shallow` — the full battery failed, but a small shallow-fitness battery
  passed: 6 live cases against the MiniReason compact wire contract with
  mini's bounded repair protocol (announced ceiling: at most 18 further
  calls; at least 5 of 6 cases must be schema-valid). Use
  `deepreason reason --shallow "YOUR QUESTION"`.
- `unqualified` — both batteries failed; the next action stays
  `deepreason qualify`, and an explicit rerun retries the ladder.

Tier records are keyed by the same qualification-subject digest as full
evidence, so profile, preset, or contract changes invalidate them identically.
Full `reason` on a shallow-tier subject is refused with the typed
`QUALIFICATION_TIER_SHALLOW` error naming the recorded tier and the shallow
command; nothing silently degrades. A transport outage during the
shallow-fitness battery records no tier at all
(`QUALIFICATION_SHALLOW_EXECUTION_FAILED`).

`deepreason status` is the human-readable readiness boundary;
`deepreason status --json` is its machine-readable form. A ready result means
the profile is valid, the referenced credential is present, and a reusable
full-tier qualification exists for the current subject. A shallow-tier
subject reports `qualification_state: ready_shallow` with the shallow command
as its one next action; MCP `start_run` stays closed until the full tier.

`deepreason reason --shallow "question"` runs the MiniReason reduced engine
(generate/check/rotate) against the configured profile. MiniReason ships in
the wheel with two declared purposes: an explicit low-cost option for any
user, and the supported fallback for small models that cannot complete full
production qualification. Shallow mode requires only a valid profile and a
present credential, never touches the qualification cache, works for both
`shallow`- and `full`-tier subjects, and always labels its result as shallow
(no V6 qualification, transactions, or terminal commitment authority).

`deepreason reason "question"` accepts an optional `--cycles` and
`--token-budget`. The implemented defaults are 6 cycles and 100,000 tokens.
Cycles carry a fixed public ceiling of 12; the token budget has no ceiling
— any positive integer is accepted.

```bash
deepreason reason "What mechanism best explains this observation?" \
  --cycles 4 --token-budget 60000
```

The caller does not choose a root, manifest, route, policy, or qualification
record. DeepReason returns an opaque managed run identity in the terminal JSON
result.

`deepreason amend` appends one typed epoch to a run standing at a terminal
stop, admitting further evidence and/or superseding the central question,
after which `deepreason continue` resumes the same run:

```bash
deepreason --root RUN_ROOT amend --attach further-evidence.pdf \
  --reshape-question "REVISED QUESTION"
deepreason --root RUN_ROOT continue --budget cycles=4
```

The amendment is strictly additive: one new seed problem whose provenance
names the question it supersedes, one new dossier for the admitted files,
and no status change to anything already recorded. The manifest is copied
verbatim across the epoch, so the qualification subject is unchanged and no
requalification occurs. Typed refusals cover a run not at a terminal stop
(`AMEND_NOT_AT_TERMINAL`), an amendment that changes nothing
(`AMEND_EMPTY`, `AMEND_QUESTION_UNCHANGED`, `AMEND_NO_EFFECT`), evidence
already admitted (`AMEND_SOURCE_ALREADY_ADMITTED`), evidence beyond the
frozen attached-evidence budget (`AMEND_EVIDENCE_BUDGET_EXCEEDED`), and an
epoch staged but never committed (`CONTINUE_AMENDMENT_INCOMPLETE` on the
following continuation).

`python -m deepreason` invokes the same installed parser and accepts the same
arguments:

```bash
python -m deepreason status --json
```

`deepreason mcp-registration` prints generic secret-free registration JSON
whose command is the absolute installed `deepreason-mcp` executable. It does
not edit any client's configuration.

## MCP contract

The production MCP facade contains exactly twenty unique tools:

| Tool | Semantics |
|---|---|
| `get_readiness` | Read redacted provider and qualification readiness. |
| `start_run` | Prepare and start a question with an optional bounded budget. |
| `run_status` | Read lifecycle and progress using an opaque managed run ID. |
| `run_result` | Read a fixed terminal result using an opaque managed run ID. |
| `run_findings` | Read a replay-derived findings summary for one managed run. |
| `amend_run` | Append an evidence/question amendment epoch to a stopped run. |
| `continue_run` | Continue the same run only under durable typed lifecycle authority. |
| `cancel_run` | Request cancellation at a safe completed-cycle boundary. |
| `scratch_map` | Read a bounded immutable scratch cluster map. |
| `scratch_search` | Search immutable scratch blocks deterministically. |
| `scratch_open` | Preview one immutable block and bounded relationships. |
| `scratch_related` | Read bounded explicit, cluster, and similarity neighbours. |
| `scratch_attention` | Preview bounded deterministic attention without committing a receipt. |
| `start_bridge` | Start grounded composition for a managed, bound, qualified V6 run. |
| `bridge_status` | Read replay-validated bridge operational status. |
| `bridge_result` | Read a bounded replay-validated grounded result. |
| `bridge_claims` | Read a bounded replay-validated claim ledger. |
| `get_capabilities` | Read a bounded summary of available operations. |
| `get_help_topic` | Read one bounded help topic. |
| `get_request_requirements` | Read the information required for a supported operation. |

Call `get_readiness` first. `start_run` must stop before preparation and
execution unless readiness is successful. Its closed schema requires a
nonblank question and permits an optional finite budget within the public
ceilings.

The returned `run_id` is opaque. Every lifecycle, scratch, and bridge
operation resolves it through host-managed storage. Callers must not derive a
path from it.

The MCP schemas contain no caller authority for roots, manifest paths or
references, providers, routes, provider-profile paths, credential references,
qualification, policy, arbitrary files, event writes, or status setters.
Qualification cannot be initiated through MCP.

`continue_run` does not create a new caller-controlled run. It uses the same
bound manifest and appends only after the application service verifies durable
typed stop authority, checkpoint identity, event fence, prior continuation
history, operator locking, and the absence of outstanding work.

`cancel_run` records an operational request. The scheduler observes it at the
next completed-cycle boundary; the request cannot interrupt a transition or
set a formal verdict.

Scratch tools are read-only previews over immutable advisory history.
`scratch_attention` commits neither visibility nor an attention receipt.
Bridge status is operational rather than epistemic. Partial,
`underdetermined`, `insufficient_evidence`, conflicting, and outside-scope
grounded results can be valid outcomes rather than tool failures.

## The engaged public preset

Public preparation compiles the repository-owned `deepreason.v6.engaged.v1`
preset. Its capabilities are all finite and modest:

- **Advisory scratch**: bounded scratch authoring and bounded
  model-requestable scratch context on the deterministic hashing embedder.
- **Foreign-school criticism**: all four seeded public schools bound to the
  single provider critic seat, observe-only, minimum one foreign school of
  coverage per accepted school artifact.
- **Grounded two-stage bridge**: review-free single-route shape — a frozen
  summarizer route builds the claim ledger and a frozen thesis route composes
  at most four grounded output sections.
- **Local simulation**: declarative-numeric proposals only (at most one per
  turn, two executions per run) on one frozen local no-network toolchain.
  The toolchain pin is derived from the preparing interpreter at manifest
  compile time, so the wheel stays portable across end-user machines; a
  changed interpreter changes the behavior subject and requires
  requalification. Model-authored Python never reaches the local runner.
- **Research**: OFF (on hold). Formalization and attached evidence: OFF.

## Authority and replay invariants

V6 prepares a typed immutable input, evidence dossier, conservative policy,
qualification projection, and exact manifest before application dispatch.
The manifest binds route and contract identities, finite budgets, input
digests, and terminal policy. Credential values never enter it.

Engine models receive only bounded role context and the required output
contract. They cannot choose providers, routes, tools, budgets, phases,
credentials, workflow transitions, continuation, or terminal status.

Formal objects are immutable and the event log is append-only. Replay
reconstructs workflow and capability state from canonical events. A V6
terminal commitment binds the terminal epoch, stop record, result draft,
reasoning event horizon, and commitment ledger. A fresh replay-validation
binding must match that commitment and result projection.

A stored `completed` string is not independently authoritative. Valid terminal
success requires the current committed terminal head, matching fresh replay
validation, and a verification summary with both `integrity_valid` and
`security_valid`. Failure of either channel produces a failing public result.

Deterministic adjudication owns formal acceptance and refutation. Model text,
scratch notes, similarity, attention, bridge prose, progress state, and MCP
responses cannot grant epistemic authority. Qualification demonstrates
contract compatibility for the configured provider/model; it does not certify
the truth of an answer.

## Unsupported public operation

RunManifest versions 1 through 5 are historical and unsupported. Direct
caller-owned roots, manifest paths, source YAML routing, and manual manifest
preparation are not the normal or supported public start workflow.

MiniReason ships inside the wheel only as the engine behind
`deepreason reason --shallow`; it has no separate public entry point.
Website construction and chunked website operation are not exposed. There are
no public website MCP tools.

The retired `make`, `prove`, `check-proof`, `code`, `simulate`, `focus`,
`expand`, `attack`, and `step` commands must not be suggested to a user.
Repository modules, old specifications, tests, or archived examples that
mention those interfaces are non-operational history.

Physical legacy code may remain inside the source repository while migration
or preservation work continues. Presence in a checkout does not create public
authority, wheel inclusion, compatibility, or support.

## Developer boundary

Source-checkout commands are developer operations only. They must not be
presented as installed-wheel usage:

```bash
python -m pip install -e ".[dev]"
pytest
```

Developers may inspect internal manifests, roots, application intents, and
historical migrations when maintaining the product. A public caller or agent
must stay within the question-first CLI and the twenty-tool closed MCP
facade above.
