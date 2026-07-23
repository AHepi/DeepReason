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

`deepreason qualify` is a separate, explicit action. Before any qualification
dispatch it identifies the configured provider and model and announces the
maximum expected provider-call count. Interactive use asks for confirmation.
For noninteractive use, `deepreason qualify --yes` is the supported explicit
confirmation form; `--json` may be added for machine-readable output. A
completed qualification for the same qualification subject is reused, so
ordinary questions do not repeat it.

`deepreason status` reports provider and V6 qualification readiness as text.
`deepreason status --json` reports the same readiness through the stable
machine-readable boundary. Both expose credential presence only as a boolean
and return one next action.

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

The installed MCP server exposes exactly eighteen tools. All input schemas are
closed and bounded.

| Tool | Public authority |
|---|---|
| `get_readiness` | Read secret-free provider and qualification readiness. |
| `start_run` | Prepare and start one normal question with an optional bounded budget. |
| `run_status` | Read current lifecycle and append-only progress for an opaque managed run ID. |
| `run_result` | Read the fixed terminal result for an opaque managed run ID. |
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
anything. `start_run` accepts only a nonblank question and an optional budget
whose cycles and token budget remain within the public ceilings. It returns an
opaque `run_id`; lifecycle, scratch, and bridge operations resolve that ID
inside host-managed storage.

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

Historical RunManifest versions 1 through 5 are unsupported by installed
public operation. Direct caller-owned run roots and manifest paths are not
public start authority. Source files for legacy workflows may remain in the
repository for preservation or internal migration work, but their physical
presence does not make them supported.

MiniReason is not included in the supported wheel and is not a public starting
workflow. Website construction and chunked website workflows are retired from
the public surface, and website MCP tools are not exposed.

The removed `make`, `prove`, `check-proof`, `code`, `simulate`, `focus`,
`expand`, `attack`, and `step` commands are not supported public operations.
Examples or reports in historical repository material must not be interpreted
as installed-wheel instructions.

## Developer-only source work

The repository checkout remains useful for implementation and offline tests.
The following is explicitly a developer workflow, not installed-wheel public
operation:

```bash
python -m pip install -e ".[dev]"
pytest
```

Production code lives under `src/deepreason/`. Public behavior must be derived
from the installed entry points, closed MCP schemas, application services,
and V6 tests rather than from retired examples elsewhere in repository
history.
