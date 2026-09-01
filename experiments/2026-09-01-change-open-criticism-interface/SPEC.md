# Spec for: contribution-only criticism-source socket

Traces: every item cites `REQUEST.md` requirements or constraints.
Untraceable items are bugs.

Tranche base: `2ec5512499a06b528664538c828d9d33e73a594b`.

This is the first implementable tranche authorized by “Perfect! Can you get
started?”. It establishes a representation-neutral boundary through which an
optional source may propose criticism. It neither connects the source to the
shipped graph nor claims that older DeepReason mechanisms already satisfy the
new anti-inductivist law.

## Items

S1 (R1, R2, R4, R5, R6, R8, R9):
`src/deepreason/criticism_source.py` adds frozen, closed
`CriticismSourceManifestV1`, `CriticismTargetV1`,
`CriticismContributionV1`, and `CriticismInvocationResultV1` contracts.

Before: there is no representation-neutral extension boundary for an optional
criticism source. Reusing an evaluator or `ArgumentativeCriticOutput` would
import verdict and counterexample vocabulary with authority consequences.

After: the host binds an immutable target containing opaque text and a codec.
A returned contribution contains opaque text and a codec, but no target
selector. No contract can express representation kind, formalism, verdict,
status, warrant, run authority, score, rank, weight, confidence, severity,
threshold, priority, admission, or candidate visibility. The source manifest's
fixed, non-configurable `authority_ceiling="contribution_only"` and the
host-written `authority_explanation` are capability-boundary metadata: neither
can select, grant, or downgrade run authority.
Operational completion, decline, unavailability, and error are host-written
invocation outcomes, not epistemic assessments.

Accept:
`python -m pytest tests/test_criticism_source_contract.py -q -k 'closed_contract or arbitrary_content or host_bound or operational_result'`
passes.

S2 (R2, R6, R7, R8):
The same module adds a `CriticismSource` protocol, explicit
`CriticismSourceRegistry`, and `invoke_criticism_source`.

Before: no safe registry exists.

After: sources enter only by constructor injection, and a caller names exactly
one source for each invocation. The source receives only a
`CriticismTargetV1`, never `Harness`, Config, run authority, graph state, or a
mutation capability. The host revalidates returned values through the closed
contribution contract. An unknown source, a decline, or an exception produces
a local typed operational result. There is no global default, winner,
priority, fallback, aggregator, threshold, learned order, performance
feedback, automatic invocation, or scheduler attachment. Two disagreeing
sources can be invoked independently, and neither result selects or suppresses
the other.

This is an ordinary in-process Python API, not a hostile-code security
boundary. The enforceable claim is that the host exposes no mutation
capability through this interface and accepts only contribution-shaped output.
Sandboxing remains a later tranche.

Accept:
`python -m pytest tests/test_criticism_source_contract.py -q -k 'registry or invocation or decline or unavailable or failure or independent'`
passes.

S3 (R3, R9, C1, C2):
The module adds frozen, closed `CriticismSourceDescriptionV1` and deterministic
`describe_criticism_sources` output containing source id, version, summary,
manifest digest, and this host-owned explanation:

> This source can add criticism. It cannot change status, rank, admission, or
> candidate visibility, and it cannot remove candidates. The run selects
> observation or defended trial separately.

The source cannot supply or soften that explanation. The
`contribution_only` ceiling describes what this interface may return; it does
not select `observe_only`. Explicit run authority remains separate and
unchanged, so the interface neither rejects nor downgrades defended trial.

Before: a human has no stable explanation of an optional source's identity or
power ceiling.

After: a registry can be inspected without invoking a source and without
implying the source was selected for a run.

Accept:
`python -m pytest tests/test_criticism_source_contract.py -q -k human_description`
passes with the exact host-owned text and stable digest.

S4 (R1-R9, C1, C2):
`tests/test_criticism_source_contract.py` supplies the law-line and architecture
proofs. The new module may import only neutral standard-library utilities and
Pydantic. It may not import adjudication, authority, trial, warrants,
scheduler, `capture.pareto`, admission, measures, Config, run-manifest,
qualification, verification, or Harness. Plain prose, mathematical notation,
JSON-looking text, and code-looking text cross the same opaque field
byte-for-byte without parsing or classification. Invocation alone has no graph
effect because this tranche contains no graph consumer. The phase-one
architecture test walks every other shipped Python module and refuses any
import of this socket, so “deliberately unwired” is a pinned boundary rather
than a current observation.

The regression ring also runs the unchanged defended-trial manifest and stub
canary tests. Their continued success proves this isolated socket has not made
source success, decline, absence, or failure a new prerequisite for defended
trial. It does not claim the new source is integrated into that path.

Mutation proof: after GREEN, add a forbidden `score` field to
`CriticismContributionV1` and show the exact-field contract RED; restore and
show GREEN. Then add a forbidden `priority` field to
`CriticismSourceManifestV1` and show the manifest-field contract RED; restore
and show GREEN. Record both RED/GREEN transcripts in this tranche. The import
error against the pre-feature tree is recorded as base RED but is not accepted
as either mutation proof.

Accept:
`python -m pytest tests/test_criticism_source_contract.py tests/test_judge_canary_dispatch.py tests/test_v6_manifest_defended_trial.py -q`
passes, and both deliberate-mutant transcripts contain a nonzero RED run
followed by a zero-exit GREEN run.

S5 (R1-R10, R12, C1-C3):
`docs/map/CON-criticism-source.md` owns the new module and contribution-only
contract; `docs/map/CON-conjecture-kinds.md` gains its representation-neutral
law line; `docs/map/CON-authority.md` records that the source ceiling cannot
choose run authority. All three move in the same commit as code and each new
load-bearing claim has a rerunnable single-line `check:` already run before it
is written.

No compatibility layer, digest preservation, historical-root rewrite, source
default, Config default, or run-authority change is added for C1-C3.

Accept:
`python tools/docs_verify.py` completes in authoritative no-cache mode, no
failure names any changed owner map, and every non-owner failure is either in
`docs/AUDIT_BASELINES.md`, the operator-recorded qualification-path condition,
the operator-disposed missing-`bc` environment condition, or passes its
required isolated re-run. Any other isolated failure is a finding and stops
delivery. The missing-`bc` disposition permits only transparent recording: no
shim, map-check edit, skipped check, or inferred pass.

Validation finding: the scheduler candidate's isolated rerun does not pass.
It records a typed `DENIED` transition with reason `runner_unavailable` because
this container's real network-namespace probe returns unavailable. An
independent detached-worktree control reproduces the same empty result-package
failure at tranche base `2ec5512499a06b528664538c828d9d33e73a594b`. Under R12
this pre-existing non-owner environment row is carried explicitly as RED; it
is not counted as a pass and authorizes no scheduler, runner, containment, or
test change.

Execution correction: the repository's verifier defines plain invocation as
“authoritative: every check, no cache” and has no `--full` parser option. The
earlier flag spelling exited before verification and did not test this item.
The first authoritative run completed 1,297 checks across 71 documents; its
load-sensitive and missing-utility rows are disposed individually before this
item can pass, following `AUDIT_BASELINES.md`'s explicit rule.

S6 (R11, C4):
Every option-discovery pass uses alphaXiv before selection and records which
retrieved mechanisms were adopted, rejected, or bounded. Literature evidence
may inform an interface choice but cannot add a scorer, category, default, or
authority that the operator did not request.

Accept: this SPEC's Research disposition contains an alphaXiv source for every
adopted or rejected external mechanism and states the evidence limit that keeps
it advisory.

## Research disposition

The operator requires alphaXiv use while exploring options. Four retrieved
design lines informed this tranche, but none is adopted as authority.

The Conceptual Multiverse makes alternative conceptual commitments visible and
intervenable, and its three-domain study found that people could revise their
framing after navigating alternatives. Its expert-calibrated verification is
not imported here: a fixed domain calibration would be an epistemic authority
and could close the vocabulary DeepReason is meant to keep open.
Source: https://www.alphaxiv.org/abs/2604.17815 (pp. 1-7).

FlexMind exposes opt-in aids that users may invoke in a nonlinear order. Its
initial comparison involved only three users, so it supports the opt-in
interaction principle but does not establish a general optimization rule.
This tranche therefore has explicit invocation and no automatic source.
Source: https://www.alphaxiv.org/abs/2509.12408 (pp. 1-5).

The user-authored sensing study let eight participants create, edit, and delete
their own categories throughout a week. It also found that a progress wheel and
low-level display pushed some participants toward fixed boundaries. This
supports revisability and warns against progress/completion signals. This
tranche therefore adds neither categories nor progress metrics; opaque content
crosses unchanged.
Source: https://www.alphaxiv.org/abs/2608.24058 (pp. 1-7, 13, 17).

MyAG separates component composition, workflow, and runtime search, but its
experiments compare scored search strategies and efficiency tradeoffs. This
tranche adopts only separation of component declaration from invocation; it
rejects scorer and search-policy machinery for this boundary.
Source: https://www.alphaxiv.org/abs/2607.13474 (pp. 1-5).

## Assumptions (operator may override)

A1 (Q1): assumed, operator may override — the smallest concrete first
increment is a contribution-only source contract with no graph consumer.
Candidate reducers, evaluator fabrics, projections, and ranking are excluded
because they would recreate mechanisms the operator rejected.

A2 (Q2): decided without asking — the recorded “get started” authorizes this
first implementation tranche, not merely a design artifact.

A3 (Q3): assumed, operator may override — phase-one human usability is a
deterministic registry description. A CLI configuration explainer is a later
independent tranche because phase one has no per-run selection to explain.

A4 (Q4): decided by the blast-radius instrument — the planned topology is
`CLEAR`, with empty frozen and frozen-adjacent contact lists. No grant is
required.

A5 (R4, R5): representation neutrality here means the boundary neither asks
for nor derives a representation category. It does not mechanically decide
whether prose, notation, code, or any other text is valid.

## Questions for operator (STOP if non-empty)

None. Each recorded question is answered by repository evidence, dominated by
the operator's recorded values, or bounded as a later independent tranche.

## Out of scope (explicit)

The existing `formally_backed` prose-immunity guard is not changed. Today it
can refuse a prose case before defender and judges; that is a direct conflict
to reconcile in its own authority tranche, not something this source contract
silently fixes.

The mandatory `ConjectureCandidate.typicality` field and its `tail_weighted`
ordering are not changed. They are an existing statistical/heuristic channel
whose removal affects the conjecture wire contract and recovery path.

The Pareto reporting frontier and `_standing_recrit_pool` are not changed.
They are existing attention/reduction mechanisms with their own consumers.

Candidate views are deferred. Even a non-destructive subset changes practical
attention; a later contract must keep the complete canonical population
available and keep view membership out of every deciding package.

Per-run Config/manifest selection, scheduler invocation, entry-point discovery,
sandboxing untrusted Python, graph recording, observation, and routing a source
contribution into defended trial are deferred. Phase one proves the boundary
before connecting it to live or frozen surfaces.

The discharge channel's binding re-ask behavior is unchanged and remains
independently configurable off.

No change is made to defaults, `rules/crit.py`, `rules/warrants.py`,
`informal/trial.py`, `run_manifest.py`, `config.py`, `capabilities/state.py`,
`harness.py`, `invariants.py`, `verification/`, `qualification.py`,
`llm/firewall.py`, scheduler ranking, `capture/pareto.py`, admission, or any
committed run root.

## Frozen-surface contact forecast

The required first invocation against not-yet-created files returned:

```text
evidence unavailable: declared file does not exist: src/deepreason/criticism_source.py
```

To make the forecast decidable without implementing on the tranche branch, a
detached temporary worktree at the tranche base received only topology stubs
for the planned module and test. The instrument command was:

`python tools/blast_radius.py --files src/deepreason/criticism_source.py tests/test_criticism_source_contract.py docs/map/CON-criticism-source.md docs/map/CON-conjecture-kinds.md docs/map/CON-authority.md --symbols describe_criticism_sources invoke_criticism_source`

The computed contact lists and scalar result were:

```json
"frozen_surface_contacts": [],
"frozen_adjacent_contacts": [],
"frozen_surface_verdict": "CLEAR"
```

The planned API functions were intentionally not wired to a known entry point:

```json
"reachability": [
  {"symbol": "describe_criticism_sources", "status_current": "UNREACHABLE", "status_base": null, "direction": null},
  {"symbol": "invoke_criticism_source", "status_current": "UNREACHABLE", "status_base": null, "direction": null}
]
```

This is the declared phase-one boundary, not hidden dead production wiring:
the functions are a library interface exercised directly by their contract
tests, and automatic run integration is out of scope.

## Blast-radius census

The tool-reported consumer fields were:

```json
"tests": [
  {"target": "describe_criticism_sources", "hits": ["tests/test_criticism_source_contract.py:2", "tests/test_criticism_source_contract.py:8"]},
  {"target": "invoke_criticism_source", "hits": ["tests/test_criticism_source_contract.py:3", "tests/test_criticism_source_contract.py:9"]}
],
"map_checks": [],
"qualification_digest": [],
"wheel_smoke_pins": []
```

The new test hits are EXPECTED TO MOVE with the implementation. There are no
pre-existing consumers. Manual `rg` over the base found no exact occurrence of
the planned class or function names; the only partial-name hits were existing
`ForeignCriticismTargetV1` references, which are unrelated and MUST NOT MOVE.

## Budget

Declared diff-budget areas are `src/deepreason/criticism_source.py`,
`tests/test_criticism_source_contract.py`, `docs/map/CON-criticism-source.md`,
`docs/map/CON-conjecture-kinds.md`, and `docs/map/CON-authority.md`.

Itemized insertion ceilings are: contracts, protocol, registry, invocation,
and explanation 140; tests 105; owner-map additions 35.

Arithmetic, pasted:

```text
$ python3 -c "items=[140,105,35]; print(items, sum(items))"
[140, 105, 35] 280
```

Budget: at most 280 inserted lines in the declared areas, with five post-spec
phase commits: plan; tests plus base RED; implementation plus maps plus mutation
proofs; validation; delivery. Tranche artifacts are excluded from the
code-and-map line budget. Frozen surfaces touched: none.

Rubric: 6/6 yes.
