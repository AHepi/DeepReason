# Validation for: maximum-modularity criticism-source socket

Branch: `codex/open-criticism-contracts-20260901`

Tranche base: `2ec5512499a06b528664538c828d9d33e73a594b`

## Acceptance checks

S1 — closed, representation-neutral contracts:

```text
python -m pytest tests/test_criticism_source_contract.py -q -k 'closed_contract or arbitrary_content or host_bound or operational_result'
........                                                                 [100%]
8 passed, 5 deselected in 0.05s
```

PASS. The host binds the target. Contribution, target, and result contracts
have no dedicated, machine-interpreted epistemic or run-control field.
Arbitrary `content` and its `codec` remain transport data and cannot bind graph
effects, even when the prose itself discusses status or authority.

S2 — explicit registry and invocation:

```text
python -m pytest tests/test_criticism_source_contract.py -q -k 'registry or invocation or decline or unavailable or failure or independent'
....                                                                     [100%]
4 passed, 9 deselected in 1.53s
```

PASS. Constructor injection and a caller-named source are the only roads in;
unknown, declined, and error outcomes remain local and do not select a
replacement.

S3 — deterministic human description:

```text
python -m pytest tests/test_criticism_source_contract.py -q -k human_description
.                                                                        [100%]
1 passed, 12 deselected in 0.05s
```

PASS. The host-owned explanation says the source can add criticism but cannot
change status, rank, admission, or visibility, and that observation versus
defended trial is selected separately.

S4 — architecture, arbitrary vocabulary, defended-trial independence, and
mutation evidence:

```text
python -m pytest tests/test_criticism_source_contract.py tests/test_judge_canary_dispatch.py tests/test_v6_manifest_defended_trial.py -q
................                                                         [100%]
16 passed in 3.71s
```

```text
score mutant exit: 1
score restore exit: 0
priority mutant exit: 1
priority restore exit: 0
reverse-import mutant exit: 1
reverse-import restore exit: 0
relative reverse-import mutant exit: 1
relative reverse-import restore exit: 0
outbound relative dependency mutant exit: 1
outbound relative dependency restore exit: 0
```

PASS. Plain prose, notation, JSON-looking text, and code-looking text cross
unchanged. The two architecture tests reject non-whitelisted or relative
outbound dependencies and resolve relative reverse imports. Both relative
directions were mutation-proven RED then GREEN. This demonstrates the
enumerated boundary on this tree; it is not suite-wide certification. The
unchanged defender/judge controls remain green.

S5 — owner maps and authoritative documentation verifier:

```text
CON-criticism-source exact check: 6 passed, 7 deselected
CON-conjecture-kinds exact check: 4 passed
CON-authority exact check: 3 passed
blast radius: CLEAR; frozen contacts []; frozen-adjacent contacts []
diff budget: 280/280 WITHIN
```

```text
python tools/docs_verify.py
docs_verify [full]: 71 documents, 1297 checks, 9 workers
docs_verify: 6 failed
```

FAIL. The authoritative documentation gate is not zero-failure. None of the
rows names a changed owner map, and the baseline/environment attribution is
recorded, but attribution does not satisfy S5 or the repository gate. R12
authorizes continuation past unavailable real `bc` only; it does not authorize
delivery through this or any other RED row. The preserved verifier transcript
is in `proof/docs-verify.txt`.

S6 — alphaXiv-before-options rule:

```text
four Source: https://www.alphaxiv.org/abs/... entries
"none is adopted as authority"
```

PASS. Conceptual Multiverse, FlexMind, user-authored sensing, and MyAG are each
adopted, rejected, or bounded in SPEC.md. Their evidence informed explicit
invocation and separation but supplied no score, vocabulary, default, or
authority.

## Full gate

```text
python -m pytest tests/ -q -n 4
12 failed, 4577 passed, 26 skipped in 708.99s (0:11:48)
```

FAIL. The repository gate is RED and R12 does not apply to these rows. The new
contract contributes thirteen passes; the twelve failing nodeids are either
the operator-recorded qualification condition or reproduce at the untouched
tranche base under the same runtime. `proof/full-gate.txt` records the exact
nodeid census, executed base-control commands, and failure snippets. No failing
test was edited, skipped, xfailed, or routed around.

## Record-behavior preservation

Not applicable. The socket has no shipped graph consumer and imports no record
reader or validator. The new reverse-import architecture test enforces that
phase-one boundary. No committed run root was opened for mutation or replay.

## Frozen-surface diff

```text
git diff --name-only 2ec5512499a06b528664538c828d9d33e73a594b -- src/deepreason/capabilities/state.py src/deepreason/harness.py src/deepreason/invariants.py src/deepreason/verification src/deepreason/run_manifest.py src/deepreason/qualification.py src/deepreason/llm/firewall.py
(empty output)
blast radius: CLEAR; frozen contacts []; frozen-adjacent contacts []
```

PASS. The declared frozen/frozen-adjacent census, complete branch name-status
review, and blast instrument all show no contact.

## Packaging surface

The new public module changes wheel layout, so the basic smoke is owed and the
pin moved in the same corrective commit:

```text
python scripts/wheel_smoke.py
wheel smoke passed: isolated V6-only contents, clean imports, exact entry points, module parity, MCP registration, and exact MCP schemas
```

PASS. `deepreason/criticism_source.py` is both a required wheel member and a
clean-environment import. No provider-facing operational surface moved, so the
operational smoke is not owed.

## Map

```text
python tools/docs_verify.py --audit
docs_verify --audit: 1 finding(s)

python tools/docs_verify.py --links
docs_verify --links: 0 dangling reference(s), 71 document(s)

python tools/docs_verify.py --coverage
docs_verify --coverage: 7 seam(s) swept, 19 without a Sweep: header, 2 finding(s)

python tools/docs_verify.py --stale
docs_verify --stale: 46 document(s) worth re-reading
```

The one audit finding is the baseline malformed check at
`SEAM-llm-x-rules.md:54`. The two coverage findings name unchanged
`SEAM-periphery-x-verification.md` and `SEAM-schools-x-scratch.md`; all
nineteen missing Sweep headers predate this tranche. They are parked as map
maintenance, not repaired in a behavior tranche.

The stale view is advisory. The three changed owners
`CON-criticism-source.md`, `CON-conjecture-kinds.md`, and `CON-authority.md`
are dismissed because their exact checks were rerun at current HEAD after the
same-commit map move; their `Verified-at` anchors necessarily precede the
commit that contains each document. The other 43 entries are unchanged,
pre-existing map debt outside this tranche and are parked together rather than
silently edited during validation.

New map checks added by this change: three, one in each changed owner map.

Record observables added versus sweep probes: none. The new models are an
unwired in-process API contract, not an append-only record type. A sweep probe
would assert bytes no shipped path can emit. Graph recording is explicitly a
later tranche.

## Independent audit disposition

The audit confirmed explicit invocation, opaque content, no default source,
no ranking or heuristic machinery, no graph consumer, and no prohibited
surface contact. Its wording finding was resolved by distinguishing the fixed
`contribution_only` capability ceiling from selectable run authority. Its
future-regression finding was closed with relative-aware dependency tests and
two-direction RED/GREEN mutation proofs. Its gate finding remains open and
therefore controls the overall FAIL verdict.

## Operator-supplied review disposition

`candidate-set-reduction-under-an-unreliable-eliminator.md`: the negative
boundary against deriving selection from indiscriminate criticism was adopted.
Elimination, ranking, suppression, visibility reduction, voting, thresholds,
learned reranking, and coverage optimisation were rejected from this socket;
any later reducer is bounded to an independently named, explicitly selected
downstream module.

`artifact-requirement-gaming.md`: honest local decline, unavailable, and error
outcomes were adopted, together with the distinction between envelope validity
and epistemic merit. Artifact quotas, proxy scores, self-attestation, and
schema-compliance-as-truth were rejected. Artifact-specific receipts or
verifiers remain bounded optional downstream modules and never outrank prose.

`asymmetry-in-test-suite-certification(1).md`: narrow RED/GREEN evidence for
named constraints was adopted. Suite-wide certification, predictive
test-density heuristics, and epistemic promotion from mutation or coverage
were rejected. Static and provenance screens remain bounded opt-in audits.

`self-confirming-checks.md`: mutation-proven law lines, positive liveness, both
dependency directions, and host-written operational outcomes were adopted.
Aggregate kill-score targets, mandatory reference models, and formal checks as
truth gates were rejected; larger batteries remain optional verification
modules.

## Requirement sweep

| Requirement | Demonstration or disposition |
|---|---|
| R1 | S1-S4 implement the first bounded improvement, and the four supplied reviews are each explicitly adopted, rejected, and bounded above. |
| R2 | S2 proves constructor injection, named invocation, no global default, fallback, winner, aggregator, or scheduler attachment. |
| R3 | S3 proves deterministic source identity, digest, summary, and a host-owned plain-language power explanation. |
| R4 | S1/S4 prove there is no dedicated, machine-interpreted epistemic or representation-control field; content and codec remain byte-preserving transport data. |
| R5 | S1/S4 prove prose is neither parsed nor required to be mechanically valid. |
| R6 | S1/S2 prove there is no score, rank, weight, confidence, threshold, feedback, or optimization target. |
| R7 | S2/S4 prove explicit opt-in use and independent disagreeing sources without automatic selection. |
| R8 | S1/S2 prove no heuristic priority, learned order, candidate reduction, or presumed problem-space vocabulary. |
| R9 | S3 and the authority map prove a source may contribute criticism but cannot decide DeepReason status or run authority. |
| R10 | The implemented and pushed phase-one module, tests, maps, and evidence satisfy “get started.” |
| R11 | S6 records four alphaXiv option sources and the advisory evidence limit before selection. |
| R12 | Validation resumed after the unavailable real-`bc` prerequisite while preserving that row as RED; it authorizes no other RED row and no delivery through a failed gate. |

This isolated socket adds no rejection or downgrade, keeps observation versus
defended trial separate, and leaves the sixteen-test defended ring green. That
does not establish C1 globally: the shipped `formally_backed` prose refusal
remains parked as P1. C2 is preserved because no source outcome selects
`observe_only`. C3 is demonstrated by the absence of compatibility code,
historical-root edits, or digest-preservation work.

## Assumptions carried

A1: The smallest authorized first increment is an unwired contribution-only
source contract; candidate reducers, evaluator fabrics, projections, and
ranking remain excluded.

A2: “Get started” authorizes implementation of that first tranche, not only a
design document.

A3: Phase-one human usability is deterministic registry description; a CLI
configuration explainer is a separate candidate tranche.

A4: The blast-radius result is authoritative for the no-frozen-contact
decision; final result remains `CLEAR`.

A5: Representation neutrality means there is no dedicated,
machine-interpreted epistemic or representation-control field. Content and
codec are transport data; the boundary neither derives a category nor decides
validity.

## Verdict: FAIL

The targeted contract, mutation, defended-ring, wheel, owner-map, budget, and
blast checks pass. Delivery is nevertheless blocked because the unfiltered
test gate and authoritative documentation gate are not zero-failure. Base
attribution explains those rows but cannot convert them into PASS, and R12 is
limited to continuing past unavailable real `bc` during validation.

Unblocking requires a capable environment in which both authoritative gates
reach zero, or a new operator amendment that explicitly disposes these exact
remaining rows. No such amendment is inferred from “Keep going.”
