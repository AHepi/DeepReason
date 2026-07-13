# Small-model compatibility status

The `deepreason-small-model-compat-v1` compatibility kernel is implemented.
DeepReason now compiles source configuration into a canonical immutable
`RunManifest`, binds every call to an `EndpointLease`, isolates model-visible
wire contracts from canonical outputs, logs every bounded repair attempt, and
uses a deterministic website state machine with skeleton-first compact
generation and component-local repair. MiniReason consumes the same route,
profile, wire, repair, event, blob, and object-store modules while retaining
its reduced engine surface.

The default MCP surface is limited to `start_make`, `make_status`, and
`make_result`. Endpoint models receive a rendered role pack and one closed
output schema only. Model-authored route, model, delegation, command, guard,
status, acceptance, and concurrency fields fail validation and have no
operational effect.

## Local conformance

The frozen local record is
[`experiments/results/small_model_compat_local_verification_v1.json`](../experiments/results/small_model_compat_local_verification_v1.json).
It records 751 passing tests, one skipped optional `fastembed` test, real
Chromium execution, clean Ruff, successful bytecode compilation, and a clean
diff check. The suite includes the three Gemma failure reproductions, route
mutation fail-closed behavior, per-attempt replay/accounting, direct-to-compact
later-cycle recovery, malicious control fields, deterministic component
concurrency, localized manifest repair, terminal diagnostics, MiniReason
graduation, and process-metadata isolation.

## Live acceptance protocol

The preregistered 60-prompt matrix is
[`experiments/website_compat_matrix_v1.json`](../experiments/website_compat_matrix_v1.json).
Run it with `scripts/compatibility_eval.py`; checkpoints are resumable, mock
observations are never acceptance-eligible, and reports leave A3-A10 as
`insufficient_evidence` until complete non-mock coverage exists. A9 also
requires the separately preregistered live frontier baseline from the same
matrix digest and at least two non-mock frozen frontier families. The resumable
checkpoint may be populated in separate invocations—for example, compact
Gemma trials first, then frontier trials from an explicitly mixed-family
configuration—without changing keys, seeds, or budgets.

No provider credential was available during local verification, so this
implementation does not claim the Gemma schema-rate, three-round website, or
frontier regression thresholds have been empirically met. That is an explicit
evidence gap, not an inferred failure or a substituted mock result.
