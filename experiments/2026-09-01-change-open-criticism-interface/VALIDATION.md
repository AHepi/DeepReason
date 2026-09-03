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

## Verdict (2026-09-01, SUPERSEDED): FAIL

Retained verbatim as history; superseded by the 2026-09-03 revalidation below.

> The targeted contract, mutation, defended-ring, wheel, owner-map, budget, and
> blast checks pass. Delivery is nevertheless blocked because the unfiltered
> test gate and authoritative documentation gate are not zero-failure. Base
> attribution explains those rows but cannot convert them into PASS, and R12 is
> limited to continuing past unavailable real `bc` during validation.
>
> Unblocking requires a capable environment in which both authoritative gates
> reach zero, or a new operator amendment that explicitly disposes these exact
> remaining rows. No such amendment is inferred from "Keep going."

Both of the stated unblocking conditions have since been met, independently of
each other: the operator issued amendment R13, AND the tranche was re-measured
in a capable environment where the full gate does reach zero.

# Revalidation, 2026-09-03 — rebased tree, capable container, amendment R13

Branch: `claude/open-criticism-contracts-delivery-rt5nde`
Tranche base (new): `762178b63`
Merge: `ee61ba4147`, `--no-ff`, from `codex/open-criticism-contracts-20260901`
Full transcript: `proof/revalidation-2026-09-03.txt`

## Rebase — no conflict, no behaviour change

The merge onto `main` at `762178b63` produced NO conflict in
`src/deepreason/criticism_source.py`, in
`tests/test_criticism_source_contract.py`, in `docs/map/CON-criticism-source.md`,
`docs/map/CON-conjecture-kinds.md`, `docs/map/CON-authority.md`, or in
`scripts/wheel_smoke.py`. The socket's contract is byte-identical to the codex
branch's. Nothing was resolved by changing the socket's contract, because
nothing had to be resolved at all.

## Authority for this revalidation

`REQUEST.md` R13 (operator, 2026-09-03), recorded verbatim before it was acted
on:

> Operator amendment R13: every full-gate and docs_verify RED row that
> reproduces on the untouched tranche base under the same container is
> an environment-only known-not-yours baseline. Record each such row
> with its base-reproduction evidence, dispose them as baseline, and
> proceed to delivery. This authorizes no row that does not reproduce on
> the base.

R13 is applied here to THREE `docs_verify` rows and to NO full-gate row.

## Full gate — the S5-class blocker is gone, not disposed

| tree | command | result |
|---|---|---|
| base `762178b63`, untouched | `python -m pytest tests/ -q -n 4` | **4712 passed, 6 skipped, 0 failed** (1720.60s) |
| head, rebased | `python -m pytest tests/ -q -n 4` | **4725 passed, 6 skipped, 0 failed** (1974.36s) |

PASS. The delta is `+13 passed, +0 failed` — exactly the thirteen tests in
`tests/test_criticism_source_contract.py`. The twelve failing nodeids recorded
in `proof/full-gate.txt` were properties of the codex container (no `python -I`
package visibility, no AF_UNIX permission, no unshared network namespace, a
different absolute Python toolchain path in the qualification subject digest,
nested containment restrictions). None of them exists here. This row is closed
GREEN on its own done-criterion; R13 is not invoked for it.

## docs_verify — three rows, all base-reproducing, all disposed under R13

| tree | checks | failed |
|---|---|---|
| base `762178b63`, shallow clone | 1328 | 7 |
| base `762178b63`, after `git fetch --unshallow` + judge-canary branch ref | 1328 | 3 |
| head, rebased | **1331** | **3** |

The four rows that disappeared between the first and second base runs
(`CON-run-identity.md:211/213/215`, `INV-frozen-surfaces.md:669`) are named by
`docs/AUDIT_BASELINES.md` as ENVIRONMENT PRECONDITIONS rather than findings.
They were SATISFIED, not disposed.

`+3` checks is exactly this tranche's three new owner-map checks, and the
failure LIST is IDENTICAL row for row between base and head. No changed owner
map appears in it.

| row | reproduces on untouched base, same container | disposition |
|---|---|---|
| `SEAM-llm-x-rules.md:54` — unparseable check, lost closing backtick | yes | R13 baseline; also a recorded baseline in `docs/AUDIT_BASELINES.md`, parked P3 of `experiments/2026-08-29-fix-docs-verify-multiline-checks/` |
| `INV-frozen-surfaces.md:181` — rotted `transport_failure` census | yes | R13 baseline; also a recorded baseline in `docs/AUDIT_BASELINES.md`, parked P-D3 of `experiments/2026-08-30-fix-rotted-map-checks/` |
| `CON-run-identity.md:298` — `TIMEOUT after 300s` | yes | R13 baseline. Disposed by its own one-command rule: run ALONE and serially it PASSES, `9 passed in 345.31s`. The claim holds; the check costs more than `docs_verify`'s own 300 s per-check ceiling, so it can never pass inside the verifier on this box. Instrument cost, not a code defect. Newly parked as **P6**. |

PASS under R13. This is a statement about ATTRIBUTION: the three checks did not
pass, and nothing was weakened, skipped, xfailed, shimmed, or edited to make
them appear to.

## Every other acceptance check, re-run on the rebased tree

| item | command | result |
|---|---|---|
| S1 | contract ring `-k 'closed_contract or arbitrary_content or host_bound or operational_result'` | 8 passed, 5 deselected — PASS |
| S2 | `-k 'registry or invocation or decline or unavailable or failure or independent'` | 4 passed, 9 deselected — PASS |
| S3 | `-k human_description` | 1 passed, 12 deselected — PASS |
| S4 | contract + `test_judge_canary_dispatch` + `test_v6_manifest_defended_trial` | 16 passed — PASS |
| S4 | five mutation pairs, all RED then GREEN, tree restored, `git status --porcelain` empty | PASS |
| S5 | `CON-criticism-source` exact check | 6 passed, 7 deselected — PASS |
| S5 | `CON-conjecture-kinds` exact check | 4 passed — PASS |
| S5 | `CON-authority` exact check | 3 passed — PASS |
| S5 | `python tools/docs_verify.py` | 3 failed, all R13 baseline — PASS under R13 |
| S6 | four alphaXiv sources disposed in `SPEC.md`, none adopted as authority | PASS (unchanged) |
| — | `python scripts/wheel_smoke.py` | passed, exit 0 — PASS |
| — | frozen-surface `git diff --name-only` over all seven declared paths | empty — PASS |
| — | `python tools/blast_radius.py` | `CLEAR`, frozen contacts `[]`, frozen-adjacent contacts `[]` — PASS |
| — | `python tools/diff_budget.py 762178b63 --ceiling 280` | `280/280 WITHIN` — PASS |
| — | `docs_verify --links` | 0 dangling, 75 documents — PASS |
| — | `docs_verify --audit` | 1 finding, the recorded baseline — baseline |
| — | `docs_verify --coverage` | 2 findings, both on UNCHANGED seams — parked |

The five mutation pairs are: forbidden `score` on `CriticismContributionV1`;
forbidden `priority` on `CriticismSourceManifestV1`; absolute reverse import
`from deepreason import criticism_source`; relative reverse import `from .
import criticism_source`; outbound relative dependency `from . import config`.
Each mutant exited 1 and each restore exited 0.

## Scope — nothing was widened

The socket remains deliberately unwired (P2), formalism does not outrank prose
(R4), and nothing added a score, rank, or heuristic (R6, R8). Blast radius
reports `describe_criticism_sources` and `invoke_criticism_source` as
`UNREACHABLE`, which is the DECLARED phase-one boundary pinned by
`test_registry_is_deliberately_unwired_from_shipped_graph`, not hidden dead
wiring. The complete branch `name-status` against `762178b63` is three modified
owner maps, one modified `scripts/wheel_smoke.py`, two added files, and tranche
artifacts. Nothing else. No committed run root was opened, edited, or replayed.

## What changed in the tranche's own artifacts

`REQUEST.md` gained R13 verbatim. `CHECKLIST.md` closed steps 11, 16, 17, 18 on
their own done-criteria. `PARKED.md` gained P6 and records P5's partial
discharge — the capable-environment rerun P5 asked for was performed, so what
remains under P5 is map debt alone. `proof/revalidation-2026-09-03.txt` is new.
No earlier artifact text was rewritten; the 2026-09-01 FAIL verdict stands
above as history.

## Residue — what this does NOT establish

The socket has no graph consumer and was not exercised against a provider or a
committed run root; "it works" is not claimed, only that the boundary holds.
The mutation evidence establishes five enumerated constraints on this tree, not
suite-wide certification, and no aggregate kill score is claimed. C1 is not
closed globally: the shipped `formally_backed` prose refusal remains parked as
P1. The three `docs_verify` rows remain RED and disposed, not passing.

## Verdict: PASS

Every acceptance check in `SPEC.md` is green on the rebased tree. The full gate
is zero-failure and no full-gate row needed R13. The only remaining RED rows
are three `docs_verify` rows that reproduce identically on the untouched base
in this same container and are therefore disposed as environment-only baselines
under R13. No red row appeared that did not exist on the base.
