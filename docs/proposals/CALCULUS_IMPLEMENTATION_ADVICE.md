# DeepReason Implementation Advice

## What I could verify

The Claude artifact itself would not load from this environment, so I cannot honestly claim to have read its hidden text verbatim. I reconstructed the intended work from the linked branch, especially the State of the Program, the formalized calculus, the ontology, adjudicator, spawn logic, synthesizer, and evidence contracts.

There is also a handover defect in the repository. The state brief says the reconciliation tranche delivered a seven-rung ladder at `experiments/2026-08-14-change-calculus-reconciliation-v2/LADDER.md`, but a direct lookup of that path on the supplied branch returns 404. The state brief is therefore the only committed description of the ladder I could resolve. I would treat the missing ladder as an unsealed handover and reconstruct it in a docs-only commit before claiming any rung has begun.

## My implementation judgment

The right solution is **not** to add separate built-in mechanisms for premises, frames, proof debt, localization, succession, orphanhood, and standing.

Build one small **typed claim layer over ordinary artifacts**, then derive the new views from the existing attack and dependence graph.

That fits the repository’s deepest design constraint: artifacts deliberately have no `kind`, provenance is inert, and meaning comes from content plus interface structure. The existing interface already distinguishes `MENTION`, `DEPENDENCE`, and `EVIDENCE`, which is almost exactly the vocabulary the new calculus needs.

The architecture should be:

```text
ordinary artifacts
      │
      ├── typed, canonical claim bodies
      ├── controller-compiled Interface refs
      ├── ordinary commitments
      └── ordinary warrants where graph-changing force is intended
                 │
                 ▼
       existing att / dep adjudication
                 │
                 ▼
        pure derived calculus views
        standing, premises, orphanhood,
        supersession, frame exits
```

Do not initially add fields to `EpistemicState`, `StateDiff`, `Problem`, or `Event`. Current status applies only to artifacts, while problems are separate frontier records. That is a gap, but it is better bridged with a companion artifact than by making a large frozen-schema mutation.

## Make problems first-class through companion artifacts

Every newly registered problem should acquire one deterministic companion artifact, something like:

```json
{
  "schema": "poietic.problem-subject.v1",
  "problem_id": "pi:...",
  "description": "...",
  "criteria": ["..."],
  "trigger": "seed",
  "sources": ["..."]
}
```

This body is a decoding schema, not an ontology `kind`. The artifact is only recognised as a problem subject when all of these agree:

```text
canonical body parses
problem_id resolves to the immutable Problem record
copied description, criteria, trigger and sources match that record
the required problem-subject structural commitment is present
the artifact addresses that problem
the Interface contains only the permitted refs
```

Critics then attack the companion artifact exactly as they attack any other artifact. A derived `problem_status(problem_id)` reads the companion’s ordinary artifact status. The original `Problem` remains the immutable scheduling and provenance record.

I would not put `subject_artifact_id` into `Problem` yet. That would alter persisted problem records and pull the change into the harness/object-store/frozen-surface zone. Instead, compute the expected companion deterministically from the existing `Problem` record and find it through `addr`.

Registration can be two-step and idempotent:

```python
problem = harness.register_problem(problem)
subject = ensure_problem_subject(harness, problem)
```

A crash between those writes produces a typed `problem-subject-missing` diagnostic and an idempotent repair on resume. That is preferable to changing event atomicity merely to remove a very small recoverable gap.

The scheduler integration should come later. Once enabled for new runs, it should schedule accepted, unresolved problem subjects; it should not silently delete refuted or orphaned problems from history.

## H1 must land before problem subjects

The current `scan_spawns` explicitly creates a `SUCCESSOR` problem whenever an addressed artifact becomes `REFUTED`.

That must be removed before introducing refutable problem-subject artifacts. Otherwise refuting a malformed question would itself automatically spawn a successor question, recreating the exact doctrine defect the change is intended to eliminate.

The first code tranche should therefore do only this:

```text
remove the refuted-artifact successor loop from scan_spawns
keep SpawnTrigger.SUCCESSOR as a legacy parser value for now
do not rewrite old problem records
prove refutation alone cannot grow the problem frontier
prove all other structural spawn triggers still work
```

I would leave the enum value in place initially. Stopping production of successor problems satisfies H1; deleting the enum immediately risks making already-recorded `ProblemProvenance` records unparsable for little functional benefit.

The decisive regression should be:

```python
before = set(h.state.problems)
refute(candidate)
scan_spawns(h, config)
assert set(h.state.problems) == before
```

A mutation test that restores the old loop should fail this test.

## Use a closed typed-claim protocol

Create a new package along these lines:

```text
src/deepreason/calculus/
    claims.py
    compiler.py
    operations.py
    views.py
    history.py
    scope.py
    programs.py
```

`claims.py` should define a closed discriminated union of versioned content bodies. Do not introduce an open `RelationClaim(predicate: str)` object. That would let arbitrary prose predicates become quasi-ontology.

The initial closed set should cover:

```text
poietic.problem-subject.v1
poietic.premise-attribution.v1
poietic.derivation-manifest.v1
poietic.reach-certificate.v1
poietic.frame-assertion.v1
poietic.problem-retirement.v1
poietic.problem-translation.v1
poietic.localization.v1
poietic.succession.v1
```

`compiler.py` should be the only place that translates typed claim content into an `Interface`. Models may propose bodies and endpoint IDs, but they must never choose whether an endpoint is a mention, dependence, or evidential premise. The controller owns that semantic compilation.

This matters because the existing synthesizer does the wrong thing for the new calculus: every connected endpoint is currently compiled as a `DEPENDENCE` ref.

Do not generalise that synthesizer and hope the model chooses correctly. Add dedicated claim-authoring operations.

## Premise attributions must mention the premise, not depend on it

A premise attribution should have this shape:

```python
PremiseAttributionV1(
    problem_subject_ref=problem_subject_id,
    premise_ref=premise_id,
    derivation_manifest_ref=manifest_id,
)
```

Its compiled interface should be:

```python
Interface(
    commitments=[premise_attribution_wf],
    refs=[
        Ref(target=problem_subject_id, role="mention"),
        Ref(target=premise_id, role="mention"),
        Ref(target=manifest_id, role="dependence"),
    ],
)
```

The attribution must **not depend on the premise**.

That distinction is load-bearing. When the premise falls, the attribution must remain standing so the system can still derive:

```text
this problem presupposes X
X is now refuted
therefore the problem is orphaned under a refuted premise
```

If the attribution depended on the premise, pass two would suspend the attribution at the moment the premise failed, erasing the very relation needed to identify the orphan.

An independence resolution should not be a magic override flag. It should be ordinary criticism of the attribution artifact. Once the attribution no longer stands, orphanhood disappears by recomputation.

A translation should create a new Problem plus companion subject and a `problem-translation.v1` claim mentioning the old and new subjects. A retirement should be an accepted retirement claim addressed to the old problem. Neither operation deletes or mutates the earlier record.

## Standing must remain a derived view

A frame assertion should be another ordinary artifact:

```json
{
  "schema": "poietic.frame-assertion.v1",
  "subject_ref": "...",
  "promotion_problem_ref": "...",
  "scope": { "... fixed DSL ..." },
  "departure_protocol": { "..." },
  "reach_certificate_refs": ["..."],
  "derivation_manifest_ref": "..."
}
```

Its interface should mention the framed subject, while depending on the reach and derivation records:

```text
MENTION       subject
MENTION       promotion problem subject
DEPENDENCE    reach certificates
DEPENDENCE    derivation manifest
```

It must not depend on the framed subject. That is what allows the subject to become refuted while the frame continues to organise generation.

The standing query should be approximately:

```python
def is_standing(frame, problem, view) -> bool:
    return (
        view.status(frame.id) == Status.ACCEPTED
        and frame_addresses_promotion_problem(frame)
        and scope_matches(frame.scope, scope_environment(problem, view))
        and frame_separated(frame.subject_ref, frame.id, view.att, view.dep)
        and compatible_with_other_standing_frames(frame, problem, view)
    )
```

Frame separation should examine connectivity through `att ∪ dep`, treating edges as undirected for component membership and excluding `MENTION`. A violation should make the frame unconsultable and emit a typed diagnostic. It should not manufacture a refutation.

The frame exit vocabulary falls naturally out of existing statuses:

```text
REFUTED                 fall
SUSPENDED_UNSUPPORTED   revocation
SUSPENDED               contestation
ACCEPTED                 standing, subject status irrelevant
```

This gives the required “refuted but still framing” state without adding another status enum. The formalisation and state brief explicitly require frame separation, a third contested exit, and restored-premise handling as derived behaviour rather than stored verdict vocabulary.

## Orphanhood should be derived from the log, not appended as truth

`views.py` should derive current orphanhood from accepted attributions and current premise statuses:

```python
ORPHAN_GRADES = {
    Status.REFUTED: "premise-refuted",
    Status.SUSPENDED_UNSUPPORTED: "premise-unaccredited",
    Status.SUSPENDED: "premise-contested",
}
```

A problem is currently orphaned when an accepted premise attribution exists, the attributed premise is not accepted, and no accepted retirement or translation resolution governs the current episode.

`history.py` can retain exit episodes without new events. The existing event record already carries `status_changed`, and the adjudicator is the only producer of status. A deterministic scan can reconstruct transitions out of and back into `ACCEPTED`.

That solves the restored-premise gap cleanly:

```text
premise falls       current orphan episode opens
premise reinstated  current orphanhood deactivates
history             episode remains visible forever
premise falls again a new episode opens
```

Do not append thousands of derived orphan events. They would duplicate information already recoverable from the log and create synchronization problems.

## The critical proof-debt distinction

I’ll need to push back on one tempting implementation: **“make every derived judgment depend on its proof manifest.”**

That is correct only for judgments whose effect is read through a derived view.

DeepReason adjudicates in two stages. Pass one computes attacks and the grounded extension. Pass two then demotes artifacts whose dependencies are unsupported.

Suppose a derived judgment carries a warrant attacking another artifact. If its proof manifest is connected only by `DEPENDENCE`, the judgment can lose support in pass two **after its attack has already operated in pass one**. The target may remain falsely refuted.

The implementation rule must therefore be:

```text
View-only judgment:
    judgment DEPENDENCE -> derivation manifest

Attack-producing judgment:
    judgment DEPENDENCE -> derivation manifest
    warrant validity node EVIDENCE -> derivation manifest
```

The manifest itself depends on each item in:

```json
{
  "schema": "poietic.derivation-manifest.v1",
  "kernel_checks": ["..."],
  "open_certificates": ["..."],
  "axiom_debt": ["..."]
}
```

Existing evidence closure already follows the transitive dependence lineage and lifts attacks onto a warrant’s validity node. That is exactly the mechanism needed to disable an attack before the grounded-extension pass. The ontology explicitly describes `EVIDENCE` as keeping invalidation inside the attack calculus rather than relying on a view-level check.

The essential proof-debt regression is:

```text
derived critic attacks target
target becomes refuted
one manifest item is attacked
derived critic loses validity before pass one settles
target is reinstated
replay reproduces the same statuses
```

No new closure rule is needed if validity nodes are wired correctly.

## Programs must consume frozen input artifacts

The program registry is deliberately pure: program verdicts are functions of text, budget, and the artifact, not live harness state.

Therefore reach promotion, succession, capture metrics, and frame-scope checks must not query a mutable live graph from inside a checker.

First materialise a deterministic input artifact at a declared event fence:

```text
ReachCertificateV1
IncumbentWoundLedgerV1
ScopeEnvironmentV1
CaptureWindowV1
```

Each should include its `fence_seq`, source IDs, canonical state digest or receipt references, and its proof-debt manifest. Programs then operate over those frozen bytes.

This prevents the same succession claim from passing today and failing tomorrow merely because unrelated later events changed the graph.

## Duhem localization can reuse warrants directly

A bundle should be an ordinary claim artifact that mentions its theory, apparatus, and interpretation members. Criticism of the bundle targets the bundle only.

Nothing should project that criticism onto a member automatically.

A localization claim can itself carry a warrant targeting the selected member. Its validity node must evidence-reference both the localization manifest and the standing bundle criticism. The result is:

```text
bundle criticism without localization
    bundle affected
    members unchanged

accepted localization to member M
    ordinary warrant attacks M

localization or its evidence defeated
    member M reinstated automatically
```

This needs no new “blame edge” and no special adjudicator branch. It is merely disciplined warrant minting.

## Succession must be a strong comparative claim

Do not equate “accepted rival covering the same problem” with succession.

Create a frozen `IncumbentWoundLedgerV1` from the incumbent’s machine-derivable commitments, accepted criticisms, explicanda, and relevant scope. A `SuccessionClaimV1` then references:

```text
the incumbent and rival
an explicanda-recovery certificate
a wound-coverage mapping
a rigidity certificate
a non-immunisation certificate
a strictness witness
a derivation manifest
the comparison fence
```

The program verifies structural coverage and strictness over those frozen records. Judges may author attackable certificates behind the existing trial guard, but a judge verdict must never directly set `Superseded`.

`Superseded` remains a comparative derived view. It is not an alias for `REFUTED`. The incumbent may be unrefuted but superseded, refuted but not superseded, both, or neither.

Where succession is intended to make an old frame fall, the succession artifact should carry a normal warrant targeting that frame assertion, with its validity node evidencing the complete succession manifest.

## P4 must precede any meaningful live evaluation

The branch’s measured evidence defect is structural. On the examined run, subproblems accounted for 36 of 49 conjecturer calls, but subproblem prompts received aliases rather than citable block IDs. Quotes were optional, producing 101 verified block references but zero byte-checked quotations. The current `EvidenceRefClaimV1` likewise makes `quote` optional.

A stronger prompt is not enough.

The context packer must put full citable block IDs and the relevant bytes into every subproblem context. For the new calculus contracts, use a quoted-evidence subtype or semantic rule requiring `quote` to be non-null. Do not mutate the old V1 contract globally merely to serve the new claim types.

The acceptance condition should bind all three layers:

```text
block bytes appear in the recorded context-exposure receipt
model returns block ID plus exact quote
semantic admission byte-checks quote against those same recorded bytes
claim interface depends on the admitted evidence record
```

Schema and offline view work can proceed before P4, but premise extraction, localization, and succession should not be judged by a live pilot until this channel is fixed.

## Concrete file boundary

The first several calculus tranches should avoid touching:

```text
src/deepreason/harness.py
src/deepreason/ontology/event.py
src/deepreason/ontology/state.py
src/deepreason/invariants.py
src/deepreason/run_manifest.py
```

Those are unnecessary for the proposed design and carry the largest replay blast radius.

The likely changes are:

```text
src/deepreason/rules/spawn.py          H1 producer removal
src/deepreason/programs.py             closed structural programs
src/deepreason/calculus/*.py           new claim and view layer
src/deepreason/llm/contracts.py         dedicated typed proposal contracts
src/deepreason/rules/premise.py         premise + attribution authoring
src/deepreason/rules/frame.py           reach/frame authoring
src/deepreason/rules/localize.py        localization warrant authoring
src/deepreason/rules/succession.py      strong comparison authoring
src/deepreason/llm/packs.py             later rendering and P4 context
src/deepreason/scheduler/scheduler.py   later active-problem/standing view
```

Do not retrofit the generic synthesizer. Its present “everything connected is a dependence” semantics are useful for its original integration relations and wrong for these new claims.

## Recommended tranche order

**Authority recovery.** Commit the missing ladder or an explicit replacement reconstructed from the state brief and formalisation. Record that the originally referenced path was absent. No source changes.

**H1.** Remove automatic successor production, preserve the legacy enum, and mutation-prove that refutation alone cannot grow the frontier.

**Claim substrate.** Add canonical claim decoding, controller-owned interface compilation, structural programs, companion problem subjects, and pure views. No scheduler integration yet.

**P4.** Flow complete citable evidence into subproblem contexts and require quotes for the new claim contracts. Do this before live testing of the calculus.

**Proof debt.** Add derivation manifests and the split between ordinary dependency and validity-node evidence.

**Premise channel.** Add premise attribution, derived problem premises, direct problem criticism, and the siren/category-error fixture.

**Frames and promotion.** Add frozen reach certificates, promotion problems, frame assertions, scope DSL, frame separation, and standing views.

**Cascade and resolution.** Add exit-history derivation, the three orphan grades, retirement, translation, independence-through-criticism, and reinstatement deactivation.

**Duhem localization.** Add bundle and localization claims, using ordinary warrants and validity nodes.

**Strong succession.** Add wound ledgers, recovery, rigidity, non-immunisation, strictness, and the separate supersession view.

**Rendering and diagnostics.** Only after the semantics are stable, wire standing frames, departure protocols, capture diagnostics, and the knowledge/attention view into packs and results.

## Minimum acceptance contract

I would pin the programme with these invariants:

```text
refuting an answer never creates a problem

every new problem has one canonical attackable subject artifact

refuting a problem subject does not automatically refute its answers

premise attribution mentions its premise and never depends on it

accepted attribution + refuted premise
    => premise-refuted orphan

accepted attribution + suspended_unsupported premise
    => premise-unaccredited orphan

accepted attribution + suspended premise
    => premise-contested orphan

defeating the attribution
    => no orphan

reinstating the premise
    => no current orphan, historical episode retained

refuting the framed subject
    => frame may remain standing

refuting the frame assertion
    => fall

support loss of the frame assertion
    => revocation

undecided frame assertion
    => contestation

attacking a proof-manifest item
    => every view-level dependent loses standing
    => every warrant-level dependent loses force before grounded adjudication

refuting a bundle
    => no member attack without accepted localization

weak rival with equal coverage
    => never Superseded

strong succession at a fixed fence
    => Superseded view, not REFUTED alias

replay
    => byte-identical formal state and identical derived calculus views
```

## Two changes I would explicitly reject

I’ll also push back on runtime embedder auto-install. A reasoning run should not silently invoke a package manager and mutate its environment. That introduces network state, package-index state, and dependency resolution as hidden inputs. Put the neural embedder in a declared production extra or container image, qualify it during setup or doctor, and emit a typed capability disclosure when absent. “Zero-touch installation” belongs in build and deployment, not inside the reasoning transaction.

I would likewise reject a generic new relation table in `EpistemicState`. It would produce a second graph whose interactions with `att`, `dep`, replay, and status would have to be re-proven. Ordinary attackable relation artifacts plus derived views are both smaller and closer to the theory.

The immediate executable move is therefore: **recover the missing ladder, then land H1 alone.** After that, the companion problem-subject and typed-claim substrate can be introduced without triggering the old recursive successor pathology.
