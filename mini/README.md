# MiniReason

The measured reduced engine profile of DeepReason. Its scheduler keeps the
small generate/check/rotate loop, while normative state and compatibility
plumbing come from the full package rather than a fork. The construction plan
with per-inclusion citations is [`../docs/MINI_PLAN.md`](../docs/MINI_PLAN.md);
the evidence lives in
`../experiments/results/INDEX_2026-07-05.md` and `../docs/BASIN_REPORT.md`.

## What it keeps (and why)

| module | keeps | measurement |
|---|---|---|
| `log.py` | dictionary-shaped compatibility view over the parent's Harness, state, events, and stores | the accounting layer caught 3 real spend bugs in the parent |
| `call.py` | shared bounded repair kernel, per-attempt replay trace, spend on EVERY exit path, hard meter | retry-exhausted spend was 8.4% of a live run; mid-retry death leaked 833 tokens |
| `gate.py` | process-only gate-rate/orbit analytics; admission uses the shared `deepreason.rules.guards.anti_relapse` guard | perfect healthy/orbiting separation on all 15 parent roots; orbiting burned 4.3x tokens |
| `checks.py` | program checks compiled from each candidate's own forbidden cases | the only criticism that measured cost-positive at low base error (zero judge tokens) |
| `rotate.py` | stance rotation (decay 5) + problem turnover (K=8) | fast rotation best on novelty 0.973 AND separation 0.690; turnover was the only novelty-RAISING force (1.12) |
| `judge.py` | criterion-level forced choice, both orders, verbosity penalty, degraded-control gate | control gates +0.478/+0.909/+0.841; naive pairwise judging discarded 8/9 votes to position bias |
| `loop.py` | propose -> gate -> check -> log -> rotate | never loops a dry problem (the 4.3x burn) |

What its reduced scheduler deliberately drops (all A/B-refuted or placebo at
strong-generator regimes): the 2-judge trial protocol, paraphrase screens,
appellate machinery, embedding-based convergence detection, and the complement
directive. It does not fork what remains: canonical artifacts, commitments,
fail warrants, attack/support construction, grounded adjudication (including
reinstatement), events, stores, and replay all execute in the parent Harness.

## Run

```python
from minireason.call import HttpEndpoint
from minireason.loop import run

summary = run(
    [("pi-1", "why did X happen?")],
    HttpEndpoint("https://api.deepseek.com", "deepseek-v4-flash", api_key=KEY),
    budget=30_000,
    root="runs/my-run",
)
```

`run()` is explicitly `engine_profile=mini`, `model_profile=compact` by
default. Before its first model call it persists the same immutable,
secret-free `run-manifest.json` used by full DeepReason, freezes the
conjecturer endpoint lease, and uses the parent's compact wire contract and
bounded repair protocol. MiniReason still owns only the reduced control loop;
use full DeepReason with `model_profile=compact` for websites, research,
informal trials, capture-control runs, or long-horizon scheduling.
Its manifest fixes `rubric_policy=forbid`; rubric-bearing candidates are
process-logged and dropped before any commitment or artifact registration.
Model-authored forbidden cases may name known `program:` checks; inline
`predicate:` expressions fail the shared skeleton contract. Trusted workload
predicates remain a full-engine input and use the parent's predicate guard.

The run summary is a convenience; the log at `root` is the real output.
`minireason.log.replay(root)` rebuilds state from it — twice, byte-equal.

Evaluation is offline, never in the loop: `judge.score_run` scores committed
pairs behind the degraded-control validity gate, and `judge.certify_seat`
re-runs the planted-flaw battery — re-certify seats on every new provider
before trusting a score.

Live smoke (M2, ~30k tokens): `DEEPSEEK_API_KEY=... python mini/scripts/smoke.py`.

## Shared advisory features

Scratch and grounded final output are not reduced-engine protocols.
`minireason.advisory.MiniAdvisorySession` opens an already-bound
`engine_profile=mini` RunManifest v3 and delegates to the parent Harness,
ScratchService, AttentionPlanner, object/blob stores, append-only log, route
leases, bounded repair, and two-stage bridge. It creates no Mini-specific
scratch schema, ledger, validator, or store.

Legacy Mini runs continue to use their existing manifest and open unchanged.
They are not mutated into v3. To opt in, compile and bind a v3 text manifest
with scratch and `grounded_two_stage` policy, then open the session. Adapters
passed to `build_bridge` must carry the exact manifest leases, model profile,
repair ceiling, and run blob store; the facade never resolves a provider or
makes an implicit call.

Scratch references remain intellectual provenance rather than evidence.
Similarity and attention remain retrieval-only, and an unknown or partial
bridge resolution is a valid success. See
[`../docs/SCRATCHPAD_GROUNDED_BRIDGE.md`](../docs/SCRATCHPAD_GROUNDED_BRIDGE.md).

## RunManifest v4 status

RunManifest v4 separates semantic model output from process authority in the
full harness. It defines `legacy`, `shadow`, and `active_conjecture` profiles,
explicit `conditioning_only` or `route_bound` school execution, bounded model
context requests, work-order-bound local repair, foreign-school criticism
routing, bridge workflow retry, and typed terminal stop evidence.

That control-plane breadth is not silently added to MiniReason. The default
Mini manifest and all existing Mini roots retain their historical behavior and
canonical data. Opening a Mini root never synthesizes v4 fields or control
events. With an explicit v4 `shadow` manifest, the reduced loop reuses the
parent conjecture application boundary and exact `WorkOrderEnvelopeV1`,
`ProposalReceiptV1`, route lease, guard, and transition records for the
overlapping generate boundary. It does not create smaller duplicate records.

Mini still owns generate/check/rotate and does not claim
`conjecture.active.v1` turn/context-expansion coverage. Canonical-envelope
reuse does not import full-engine trials, research, website stages, or the full
scheduler.

For the exact implemented boundary and known gaps, see the
[`v1.5 normative amendment`](../docs/harness-spec-v1.5-amendment.md) and
[`v4 migration guide`](../docs/JOLT_CONTROL_PLANE_MIGRATION.md). Offline
control/replay tests are not evidence that active v4 improves novelty, answer
quality, or cost on live providers.

## Graduation (mini -> full)

The log is the contract: a MiniReason root is a valid DeepReason root.

```python
from deepreason.harness import Harness
h = Harness("runs/my-run")          # no data conversion
from deepreason.invariants import verify_root
verify_root("runs/my-run")           # ["violations"] == []
```

`mini/tests/test_graduation.py` holds this: Mini and full DeepReason read the
same canonical grounded/support status map, including attacks on validity
nodes and reinstatement; Mini survivors are exactly canonically accepted
addressed artifacts. The parent's capture detection also reads Mini's
`gate:` measures.

Graduate when base error is measurably high (then trial filtering has
something to filter), or when policy demands multi-family judge ensembles.

## Verification

`python -m pytest mini/tests` — no network, no keys. The M3 fixture rescores
the parent's committed instrument reports byte-for-byte; M0/M4 fixtures
generate canonical roots in-test and reopen them through the full Harness.
Source-line counts are not a compatibility or quality claim; the maintained
boundary is the reduced engine feature surface plus one shared normative
kernel.
