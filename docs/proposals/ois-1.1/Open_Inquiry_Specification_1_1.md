# Open Inquiry Semantics

## Staged specification — Version 1.1

### Purpose and authority

This specification develops a recordable, inspectable account of inquiry toward implementation. Its semantic authority is **PopperSemantics, Version 1.1**, supplied as `PopperSemanticsV1_1.md`. The authority’s explanatory kernel is recursive; the executable component specified here is a finite bookkeeping and checking component. They are not the same object.

The semantic target remains explanatory universality. No finite profile, evidence format, event vocabulary, argument-labeling policy, or collection of successful runs defines that capacity. No requirement to compute every semantic relation is imposed. A working implementation may rely on fallible explanatory judgments by people or other systems; it must represent that reliance rather than disguise those judgments as computed facts.

A release binds to the exact authority bytes, specification bytes, profile, interpretation, checker, and policy versions through a manifest. An implementation that changes the semantic authority must declare a different authority binding. A passing test does not authorize a silent change of meanings.

This document contains normative contracts, mathematical constructions, worked cases, and development gates. A contract is not a report that its implementation exists. Implemented and tested subsets are identified by the accompanying verification report. Unimplemented semantic adapters and universal-capacity attribution remain explicit obligations, not functions secretly supplied by an oracle.

# Part I. Semantic commitments and refinement

## 1. The commitments being preserved

The following table locates the authority; it does not establish a competing abbreviated theory.

| Commitment | Meaning carried into this specification | Prohibited substitution |
|---|---|---|
| K-REAL | Reality, situated judgment, and attribution evidence differ. | A record label becomes truth. |
| K-PROBLEM | Recognition and values direct attention to an interpreted difficulty. | A task ID proves problem recognition. |
| K-CONJECTURE | Criticism depends on a target content available for that criticism. | Every creative contribution must predate every criticism in its episode. |
| K-CRITICISM | An objection alleges a problem-relevant defect; uptake concerns its reasons. | Changed output or a well-formed objection proves reason use. |
| K-RECURSION | Targets include methods, interpretations, standards, and appraisals; results can affect their operative use. | An attackable archive proves that the target can revise its methods. |
| K-ORIGIN | Construction and reconstruction require contribution-specific causal attribution. | Equivalent incoming content automatically defeats reconstructive authorship. |
| K-PROGRESS | Actual explanatory improvement is distinct from change, retention, and verdict. | A preferred candidate, valid form, or disclosed loss proves progress. |
| K-UNIVERSALITY | Continuing explanatory organization has independently scoped understanding and creative capacities. | Finite coverage, permission, or a lucky continuation proves universality. |
| K-PHYSICALITY | Attributed roles and capacities require compatible realization where a physical claim is made. | A constructor description proves explanatory understanding. |

The independent-commitment arguments and source qualifications are those in the authority’s Part I-B. This specification does not add a claim that these commitments have been proved logically independent in every possible formal language.

## 2. Four levels and a partial interpretation

A **semantic claim** concerns what holds in an interpreted model. An **appraisal** concerns what an identified inquirer or reviewer judges. A **record fact** concerns what a dossier contains. A **machine-check fact** concerns a declared procedure’s result on identified bytes. A certificate may exist, have a correctly formed body, be provisionally used, and still be wrong about the world.

Write `Interpretation(D, M, v)` for the proposed relation between dossier `D`, semantic model `M`, and interpretation version `v`. This is a substantive, criticizable interpretation, not an automatically generated equality. For a claim `phi`, an evidence report means “these cases about phi occur and receive these recorded appraisals.” It does not mean `M ⊨ phi`.

An explicit bridge may support a conditional inference from a checked object to a semantic claim. Its premises include the adequacy of the interpretation and any domain assumptions needed by that inference. A checker may establish the consequence of those premises without establishing their truth. The bridge, premises, and applications remain available for criticism.

`Licensed_j(u)` retains the authority’s meaning: a fallible appraisal of the inferential application. It is not a permission to think or act. A software field named `applicable` may represent part of that appraisal; it may not silently remove the relation or turn it into an infallible authorization.

## 3. Claim identity, time, and scope

A claim has a typed predicate and typed arguments, together with the interpretation needed to read those arguments. A reporting context contains the following indices.

```text
Context = (authority_version, interpretation_version, history_id,
           attributed_system, boundary_id, continuity_id, grain_id,
           situation_before, situation_after?, contribution_id?, respect, scope)
ClaimKey = (predicate_id, typed_arguments, Context)
```

An irrelevant index may have the explicit value `not_applicable` under the predicate’s declared signature. It is never dropped because a favorable witness used a different value. Predicate signatures state which fields are mandatory. Authorship and OCA require the contribution index; newness requires the earlier-repertoire boundary; progress requires the compared situations and attributed contribution; capacity requires organization, challenge domain, achievement respect, and enabling discipline.

A scope is a content-bearing specification of the respects and conditions in which a claim is made, with a versioned representation. String equality is a useful identity check, not proof of semantic equivalence. Semantic equivalence at grain `ell` is a separate, criticizable claim. It must preserve the explanatory role relevant to the comparison; a tolerance relation is not automatically an equivalence relation.

The date on which a record was entered, the time of the event it describes, and the situation about which it makes a claim are different. Later evidence can change a present appraisal of a past improvement; it does not make a fixed historical proposition change truth value. An expanded problem is represented by another situation index.

## 4. What counts as refinement

Each adapter declares the semantic roles it represents, its unsupported cases, the conditions under which its output can be projected, and the claims that remain substantive. An adapter must preserve both positive and negative distinctions: a copied string must not become authored understanding, and genuinely reconstructed understanding must not be excluded merely because the string arrived from elsewhere.

A restriction can be legitimate for a profile without being a semantic necessity. A profile may inspect a finite explicit graph or insist on a particular intervention packet. It then reports the coverage of that route. Failure of the packet is not automatically a refutation of reason use, authorship, or explanation; an alternative explanatory account may be adequate.

The obligatory preservation cases include an inherited target with an original criticism, a communicated explanation creatively reconstructed, a tacit contribution without an explicit graph, an independently originated replacement, a standard changed through inquiry, a reasoned limitation, rejection of a mistaken criticism, community retention, and provisional episode closure. Each requires an interpretation of the contribution, not merely the presence of the named event kind.

Conformance is not established by calling the implementation an “admissible interpretation.” It is supported by mapping arguments, discriminating cases, relevant proofs about the chosen representation, and successful criticism of that mapping. Findings against the mapping may require changing the implementation rather than narrowing the authority.

# Part II. The record and appraisal kernel

## 5. Scope of the executable component

The finite kernel stores records, checks declared reference and schema conditions, exposes dependencies, computes one explicitly chosen provisional appraisal policy, and produces reproducible reports. It does not invent explanatory meanings for opaque fields. It does not decide the truth of `Account`, `Bearing`, `Authors`, `UsesReason`, `Progress`, `Can`, `UU`, `UC`, or `UED`.

The minimum implementation has no requirement that every admissible state has a successor. Resource exhaustion, user decisions, interruptions, and terminal target histories are representable. A stopped target is not deemed incapable of a past originative act. A stopped recorder is not deemed to have made its recorded claims infallible.

The kernel is modular. Content adapters, history interpreters, reason-use studies, provenance studies, appraisers, capacity arguments, and physical-realization modules have separate interfaces. An interchange contract may constrain their outputs without requiring identical internal mechanisms. Replacing a module creates an identifiable new configuration and a new appraisal context.

## 6. Sorts and declaration discipline

| Sort | Definition or responsibility |
|---|---|
| `ActorId` | Identity of a person, system, organization, or composite. Recorder and target are roles, not mutually exclusive kinds of being. |
| `Role` | Extensible content-role identifier with a declared interpretation. Unknown roles remain storable. |
| `EntryId`, `ArtifactId` | Distinct identifiers for record events and recorded artifacts. |
| `HistoryId`, `OccurrenceId` | Identities within an account of the target’s actual or counterfactual history. They are not automatically record-event IDs. |
| `SituationId`, `ContributionId` | References to indexed problem situations and delimited explanatory contributions. |
| `VersionId`, `Digest` | Version identity and digest of a declared canonical representation. A digest identifies bytes, not truth. |
| `SystemId`, `BoundaryId`, `ContinuityId`, `GrainId`, `ScopeId` | References to the corresponding criticizable descriptions. |
| `PredicateId`, `Formula`, `Term`, `Polarity` | Typed claim vocabulary; polarity is `positive` or `negative`. |
| `Entry`, `Artifact`, `Snapshot` | Finite record structures in §§7–9. |
| `ApplicationId`, `Application` | One use of content or one inferential application in an identified appraisal, §11. |
| `CheckResult` | `PASS`, `FAIL`, or `UNKNOWN`, with check ID, inputs, result, and reasons. This is never a truth value. |
| `EvidenceCase`, `AppraisalRecord`, `Report` | Separate case, situated-appraisal, and recorder-report structures, §§10–12. |
| `Profile`, `InterpretationVersion`, `PolicyVersion`, `CheckerVersion` | Declared dependencies of the evaluation and projection. |
| `Domain`, `Challenge`, `EnablingConditions`, `Organization` | Semantically interpreted descriptions used by capacity arguments; not necessarily enumerable. |

A typed identifier references a description rather than supplying its truth. Every executable predicate has a signature, input representation, defined result type, failure behavior, and declaration of the checks it actually performs. Every substantive predicate has an interpretation obligation and can lack an executable decider. A build must reject an undeclared callable; it must not invent a Boolean implementation for a substantive predicate.

`Problem`, `Background`, `Standard`, `Reason`, and `Explanation` are semantic roles of contents, not disjoint artifact types. `SituationId` resolves to the authority’s situation structure, including material standards and values, even when an adapter displays a shorter projection.

## 7. Artifacts, versions, and contribution provenance

```text
Artifact = (id, surface_or_reference, roles, interpretation_claims,
            parent_artifact_ids, associated_history_occurrences, metadata)
Entry = (id, actor, kind, causes, created_artifacts,
         external_artifact_refs, local_artifact_refs, payload)
```

An artifact ID is globally unique within the release’s record namespace. Exactly one entry creates each noninitial artifact. Initial artifacts are explicitly identified; they have no fictitious creator event. Byte identity, content equivalence, interpretation, and explanatory ancestry are separate relations.

An ancestry edge records a claimed source-to-descendant relation, such as a revision or reconstruction. Its parents are existing artifacts, and the claim’s grounds are inspectable. Merely naming a source as a parent does not establish that the source supplied the explanatory organization. An unrelated rival adopted from an existing store need not become the descendant of the theory it replaces.

`AncestorOrSelf` denotes the reflexive-transitive closure of declared ancestry. It is not semantic equivalence and is not named `DescEq`. External parent edges follow record creation order in this encoding. This gives an acyclic record-ancestry relation, including edges from initial artifacts. It is a fact about the representation, not an assertion that semantic opposition or reciprocal explanatory constraint is acyclic.

A batch may create a result and a transport referring to that result atomically. Such local references name artifacts created by that same entry and are distinguished from historical references. The batch does not thereby establish that one newly created semantic content was available earlier for criticism. Where that matters, an internal occurrence-order account is required. The minimal reference checker does not infer that account.

## 8. Record order, target history, alternatives, and snapshots

An entry’s `causes` are earlier record entries required for its admission. Their transitive closure is a strict partial order. For a snapshot, every cause of an included entry is included; every external artifact reference is initial or created in a causal predecessor; every local artifact reference belongs to that entry’s creation set. All artifact fields that contain references participate in this check. An omitted payload reference is a schema error, not permission to bypass grounding.

A **snapshot** is a finite, downward-closed set of entries, with its initial artifacts and explicit constraints. Alternative *record transactions* may be declared incompatible; the checker forbids a snapshot containing both or their conflicting causal descendants. A transaction is not allowed to conflict with itself. The supplied implementation checks finite snapshots by reachability and declared alternatives; it does not materialize an infinite event space.

A **history account** separately identifies occurrences, their actors, their causal order, and any incompatible actual or counterfactual continuations. Recording descriptions of two incompatible possible occurrences is not performing both occurrences. Similarly, recording rival conjectures is normally compatible: believing or considering `p` and `not p` does not make the two recording events physically alternative.

A later comparison may refer only to alternatives available in that comparison’s declared history. It cannot obtain an actual rival occurrence by pointing into an unrealized branch. It may instead compare a conjectured description of that rival, already available in the actual history, with that status explicit.

Where a fixture synchronizes record order with the described inquiry, it declares that simplification. Otherwise a historian may record an earlier target occurrence later. Prior possession for newness is determined by the interpreted target history, not by the record’s causal ancestors alone.

A reporting cut is the choice of a snapshot, not a new event. Designating the same snapshot again changes neither its artifacts nor its target history. Writing a new report about it is a recorder action and is identified as such.

## 9. Event vocabulary, episodes, and results

The core vocabulary is extensible; these kinds prescribe record payloads, not a universal cognitive sequence.

| Kind | Required semantic information or recording role |
|---|---|
| `Attend` | Difficulty, recognition account, values or priority account where claimed, and situation. Missing accounts remain missing, not false. |
| `EnterConjecture` | Attempted content, problem, contribution occurrence, and source mode: construction, reconstruction, or reception. |
| `Activate` | An existing artifact or previously available disposition; it creates no new occurrence of understanding by fiat. |
| `Criticize` | Target, alleged defect, problem context, grounds, and alleged bearing. |
| `Respond` | Objection addressed, affected contents or uses, response disposition, before/after situations, and grounds where represented. |
| `Transport` | An account of continuity between changed situations, §18; it may be created atomically with a response. |
| `Compare` | Alternatives, question and criteria of comparison, reasons, and preference relation or unresolved result. No winner is mandatory. |
| `Appraise` | Actor’s stance on an exact claim key, grounds, scope, and any explicit supersession. |
| `SubmitCase`, `AssessApplication` | A case and a fallible judgment about a particular use of it. |
| `Retain`, `Transmit`, `Reconstruct` | Availability, transmission, and understanding-related occurrences kept distinct. |
| `LinkEpisode`, `Absorb` | Explanatory connection or import of already located contributions. |
| `EngagementChange` | Active, suspended, interrupted, or closed-for-now engagement; reason optional unless a reason-sensitive attribution is claimed. |
| `ProposeMethodChange`, `EnactMethodChange` | Criticism-linked proposal and actual enactment, including affected judgments or practices. |
| `RecordExtension` | A typed extension payload under a named schema, retaining uninterpreted content when necessary. |

A response has an **objection target** and **affected uses or contents**. These may differ. Criticizing an instrument standard can cause a theory to be qualified or a question to be reframed. Such an indirect effect requires an explicit application or explanatory connection; it must not be fabricated by identifying the standard with the theory.

Response dispositions include revision, rejection, reasoned retention, rejection of criticism, evidence request, reframing, restandardization, suspension, setting aside, and rival adoption. They do not exhaust possible semantic responses. A content-insensitive refusal is recordable without a fictional reason. A reason-sensitive setting aside requires the relevant account of its reasons. Neither a disposition name nor the creation of a reason token establishes reason use.

The result of an engagement is a **situation**, possibly accompanied by several artifacts and dispositions. A replacement theory is optional. A rejected criticism, improved uncertainty, changed standard, clarified question, or principled limitation can be a result. Progress remains a separate claim about that situation.

An episode is represented by linked occurrences and an account of their causal-explanatory connection to a difficulty. Shared topic, a shared ancestor in the record graph, or a common episode label is insufficient. Roots are descriptions of attention, not necessarily a separately logged mental instant. Missing an `Attend` token does not disprove an actual originative act.

Concurrent maximal appraisals and engagement reports are retained as a set. A display must report disagreement or incompleteness rather than arbitrarily choose a maximum. Closing an episode does not erase its conclusions or forbid a later reopening. A recorder’s loss of contact yields unknown target engagement unless there is evidence for a stronger description.

Absorption references a selected earlier contribution or snapshot of an episode, together with a connection account. Imported events retain their original identity and location. A merge does not require imported events to occur after the merge. It also does not import unrecorded future events unless a later, separately recorded subscription or import operation does so.

## 10. Submission, checks, and fallibility

A **receipt** records material supplied to the system, including material that cannot be parsed by its current schema. An **evidence case** is the parsed, indexed claim and account. An **application assessment** says whether and how a case is provisionally used. These objects have different identities.

```text
EvidenceCase = (id, claim_key, polarity, body, declared_schema,
                scope, source_provenance, essential_uses, annotations)
Assessment = (application_id, assessor, claim_or_use, interpretation_version,
              scope, activation_stance, checks, reasons, supersedes?)
```

`PASS` means that a declared, executable check passed. `FAIL` means that it failed. `UNKNOWN` means that the check is unavailable or its input is insufficient for that check. A schema can be well formed even when its recorded experiment failed. The failure must then remain a failure; admission alone cannot turn that body into successful evidence through that schema.

A substantive case can remain discussable when a particular instrument-based route fails. The failure is not silently changed to success; the alternative causal explanation is another case, under its own declared interpretation and application assessment. For example, a recorded reason-use experiment can fail while a different, better explanation of the episode supports genuine but mistaken reasoning.

Schema formation is assessed before an admission event is assigned. It cannot depend on the as-yet nonexistent creator of the proposed case. References and scope are checked against the requested snapshot, and the admitted occurrence records the actual creation event.

Submission is status-blind in the following scoped sense: for the same material, schema, resource policy, and available references, a favorable or unfavorable current verdict about its claim does not determine whether it can be submitted. Parsing failures, resource limits, transport failures, and unsupported encodings are reported separately from semantic rejection. They are not evidence that the claim is false. A receipt and an alternative interpretation route permit criticism of the current schema without requiring the schema to parse every possible future language today.

Criticism templates are descriptions, not preexisting occurrences. A template is instantiable at a snapshot only when **all** required references, not merely its target, are available under the selected schema. The availability of an instantiation is not a guarantee that a physical actor will create it. The existence of a challenge schema does not establish that its grounds are true or that a defect actually exists.

An idealized record language can have a free-extension construction that adds any fully grounded finite challenge packet with fresh IDs. This is a representation result, not an axiom that every actual record, target, or physical world continues forever. Actual mutually exclusive criticism acts are allowed. The representation may describe them in separate histories while recording both descriptions in one dossier.

## 11. Applications, dependency, opposition, and provisional appraisal

### 11.1 A use is the unit of dependency

An application identifies a use of a content, a provisional premise, or an inferential step in a particular appraisal. Applications are distinct from artifact roles. An ordinary observation, a background theory, a comparison, a mathematical model, a reason, a certificate, a standard, or a policy application can all be essential premises.

```text
Application = (id, subject_ref, context, role,
               essential_application_ids, alleged_defeat_targets,
               local_readiness, activation_assessment_ref,
               claim_key?, polarity?, evidence_case_ref?)
local_readiness : PASS | FAIL | UNKNOWN
```

An application with no essential predecessors is not automatically an established truth. It may be an explicitly provisional assumption, an observed record fact, or a checked derivation with its background made explicit. The role and explanatory basis are declared. Inquiry does not require a completed proof of every background assumption before it can proceed.

All references resolve within the appraisal slice. A use of a content in one scope does not automatically attack, defend, or withdraw its use in another. An essential premise cannot be reclassified as an annotation merely to keep its dependent standing. Disagreement about essentiality is a further claim, represented by another assessment rather than by erasing the old account.

### 11.2 An objection is not automatically a successful edge

A criticism record alleges a defect and its bearing. An appraisal may provisionally treat that allegation as pertinent to an application; it records the grounds and interpretation for doing so. The corresponding defeat application is itself criticizable and includes essential grounds, standards, interpretation claims, and sources where they do work. Mere entry of a hostile string is not enough to create an operative defeat edge.

`local_readiness` concerns the declared finite check route and the existence of the activation assessment, not the truth of that assessment. A failed body is `FAIL` for that route. A missing assessment or unresolved finite check is `UNKNOWN`. A provisionally admitted semantic interpretation can have `PASS` while being wrong. Nothing derives `Bearing` merely from this value.

Positive and negative cases about one claim may coexist. Opposing conclusions do not automatically show that both arguments are unsound. A declared policy may interpret the conflict as a reason to suspend a premise application; that conflict application and its grounds are explicit. The raw record never resolves the conflict by selecting whichever polarity was entered last.

### 11.3 A finite dependency-aware policy

The default bookkeeping policy is named **DA-1**. It is a modeling choice, not the definition of rational appraisal or a claim about the unique correct treatment of every cycle.

Let `N` be the finite set of applications in the appraisal slice. Let `deps(x)` be the essential application IDs of `x`, and let `attackers(x)` be the applications whose declared defeat targets include `x`. Let `ready(x)` be its local readiness. Start with `I = O = empty` and repeatedly apply, simultaneously:

```text
I_next = I ∪ {x in N : ready(x) = PASS
                      and deps(x) ⊆ I and attackers(x) ⊆ O}
O_next = O ∪ {x in N : ready(x) = FAIL
                      or deps(x) intersects O
                      or attackers(x) intersects I}
```

At the fixed point, label `in` for members of `I`, `out` for members of `O`, and `undecided` for the remaining applications. An `UNKNOWN` check does not become `PASS` because its application is unattacked. An undecided essential premise prevents its dependent from becoming `in`. An out essential premise makes that dependent out. This applies to criticisms and other arguments without exception.

The sets grow monotonically during one evaluation. Previously established conditions persist, and each productive round adds at least one member, so a finite input reaches a fixed point after at most `2|N|` productive rounds. Starting from the empty sets, the rules preserve disjointness: entry into `in` requires every attacker already out and every dependency already in; the conditions that could put the same node out would contradict those established memberships. The same induction covers simultaneous additions. This is a proof about the stated finite policy, not a semantic soundness theorem.

For an argument labeled in, each declared essential application is in. Consequently a dependent cannot remain in when one of those applications is withdrawn as out in a recomputed appraisal. A new independent application supporting the same conclusion need not share the withdrawal. This gives the authority’s dependency diagnostic a faithful *record-level* implementation under the declared interpretation of the slice.

Mutual attack can leave applications undecided. A support cycle with no independently usable entry remains undecided rather than generating its own warrant. An external defeater or independent application may change those labels. The semantic authority does not require that every cyclic debate remain unresolved, nor that DA-1 be used by the thinker.

### 11.4 Other appraisers and recursive effects

Other policies are allowed with declared semantics and counterexamples. Each must expose the difference between evidence availability, application usability, and semantic merit. A policy claiming coherent usability must satisfy the essential-premise condition at the same scope. A mere version label cannot excuse violating that contract.

DA-1 processes a finite interpreted appraisal slice. It is not an unlimited detector of every hidden premise or relevant criticism. Discovering a missing premise or a wrongly activated defeat requires revising the slice and its interpretation; the report records the new version and the reason. That discovery can itself be the result of creative inquiry.

A policy, checker, schema, or activation standard used by the target can be represented as content and criticized. A recursive-capacity claim additionally requires a path from that criticism to possible changes in operative use. An external operator may enact a proposed change; the account must show the target’s or declared composite’s contribution. A recorder re-labeling a frozen history without affecting the target supports an attribution-review claim, not target recursive capacity.

## 12. Reports, finite derivations, completeness, and situated judgment

### 12.1 Reporting cases without reporting truth

For a fully indexed claim, retain the IDs of all parsed submitted positive and negative cases. Its **raw case summary** is one of `NO_CASE`, `POSITIVE_CASE_ONLY`, `NEGATIVE_CASE_ONLY`, or `BOTH_CASES`. These names describe case presence; they do not describe belief, truth, refutation, probability, or comparative explanatory merit.

The **usable-case summary** uses cases whose assessed application is in under the named policy. It is accompanied by failed checks, unknown checks, out applications and reasons, undecided applications, conflicting premises, and the conditional dependencies of any derived case. An undecided case must not disappear into an unexplained `NO_CASE` display.

Adding another positive case does not change a presence bit that is already set. It does change the dossier. A new independently relevant argument, criticism, scope distinction, or experimental result may alter an appraisal even when the raw bits are unchanged. Neither counts nor the absence of new bits licenses ignoring the new content.

```text
Report = (exact_claim_key, snapshot_digest, authority_digest,
          specification_digest, interpretation_version, profile_version,
          checker_version, policy_version, raw_case_ids, usable_case_ids,
          labels, check_results, conditional_premises, limitations,
          semantic_decision = NOT_EVALUATED, supersedes_report_id?)
```

`NOT_EVALUATED` states what this bookkeeping report does not decide. It is not a denial that an investigator may rationally judge the semantic claim. Such a judgment is a separately attributed `AppraisalRecord` with its reasons. A software API must not alias an `in` label or a positive-case summary to a field called `is_creative`, `true`, or `universality_verified`.

### 12.2 Finite derivations

A future derivation adapter may use a typed signed grammar for atomic cases, conjunction, disjunction, negation, and quantifiers over **explicit finite ranges**. It must type-check every rule application, binder, claim key, scope conversion, and leaf; the mere existence of leaf certificates is insufficient. Introduction of a positive conjunction needs cases for both conjuncts; a negative conjunction needs a case against at least one conjunct. A positive disjunction needs a case for a named disjunct; a negative disjunction needs cases against both. A signed case for a negation switches the sign on the same formula, without treating a missing case as a negative one.

An existential positive case identifies a member and its positive instance case. An existential negative case requires an exhaustive declared range and negative cases for every member. A universal positive case requires that range and positive cases for every member; a universal negative case identifies a member and a negative instance case. These are constructions of **cases under premises**, not a theorem that every resulting semantic claim is true. No rule obtains a negative case from failed proof search.

A derivation’s essential uses include its inference interpretation, every semantic premise application it relies on, and each range or transport bridge. A reusable positive witness for `phi` is not an automatic license to assume `phi` unconditionally when a contrary case is also relevant. The appraiser must state its stance on that premise use or report the derivation as conditional on `phi`. Classical explosion is not applied to the coexistence of two records.

### 12.3 Three different completeness claims

`CompleteRecordedRange` asserts that a finite extraction exhausts specified entries in an identified snapshot. It can be checked against the snapshot’s canonical representation. It says nothing, by itself, about everything the target ever understood or every alternative that could exist.

`CoverageBridge` is a substantive claim relating that extraction to an independently identified semantic domain, such as the system’s actual earlier repertoire. It includes the domain, history, boundary, grain, observation or loss model, possible missing channels, and an explanatory account of why missing members have been ruled out in the claimed respect. A complete log is not automatically such a bridge.

`UniversalArgument` is an argument about an unrestricted class, possibly infinite or not enumerable. It is not a finite-range completeness certificate. A finite proof may support it, but the proof’s own premises and interpretation must be stated. The kernel must not instantiate a universal semantic quantifier by iterating only over dossier-named objects.

All three are criticizable contents. Defeating a completeness or coverage application removes the dependent derivation’s usability without making its conclusion false by fiat. No completeness witness about a current variant list proves that no informative, previously unimagined variation exists.

### 12.4 Situated appraisals and supersession

An appraisal records its actor, exact claim key, stance `holds`, `fails`, or `unresolved`, grounds, occurrence, and explicit supersession where applicable. For a declared history and cut, the current display retains the causally maximal relevant appraisals not explicitly superseded. Multiple incompatible maxima are reported as multiple appraisals, not collapsed by upload time or an arbitrary topological ordering.

The actual semantic relation `Judges` can be more extensive than the recorded appraisals, especially for inexplicit thinking. The maximal-record rule is a display convention. Absence of an appraisal record does not prove that the target lacks a judgment. A new interpretation of an earlier utterance creates a new attribution record without changing the historical utterance’s bytes.

## 13. Newness and contribution-specific attribution

The semantic baseline is the authority’s actual previously possessed explanatory repertoire, at a fixed system, boundary, continuity, grain, history, and contribution index. A record extraction is only evidence about that repertoire. Storage of a string does not establish understanding; causal absence from an output’s recorded ancestry does not establish that the understanding was never possessed.

The normative relation is:

\[
\mathrm{New}_{\ell,\beta}(s,x,e,h)
\iff \neg\exists y\in R^{\ell,\beta}_{<e}(s,h)\;(y\equiv_\ell x).
\]

A negative newness case identifies an earlier possessed equivalent and explains its deployment, equivalence, and historical relation to the contribution. A positive newness case explains why the earlier repertoire lacks an equivalent; an exhaustive token scan is sufficient only for a token-scan claim. Projecting it to actual semantic newness requires the coverage bridge in §12.3.

The result of scanning a finite named range is `NoEquivalentFoundInRange`, with the range and equivalence assessments attached. It is not exposed as `New` unless the further attribution is explicitly recorded. Reacquisition after forgetting, first possession by a continuing system, and historical firstness are separately indexed questions.

An OCA report never existentially chooses its boundary, grain, history, or contribution. Candidate witness search may search for evidence matching the requested key; it may not answer the request with a witness for another key. All predicate conjuncts refer to the same contribution. Authorship acquired later cannot validate an earlier unauthored use of the same content.

## 14. Explanatory attempts and optional explanation objects

`Attempt(s,x,p,h,e)` means that the system deploys content `x` as an attempted account of a represented problem in the indexed contribution. The attempt can be false, incomplete, inexplicit, or unsuccessful. Whether it is an attempt is not established solely by assigning the role `explanation` to an artifact.

An optional `ExplanationObject` represents explanatory job, commitments, connections, scope, and auxiliaries. Its graph is an interpretation of those roles. A route through a graph does not by itself supply explanatory relevance; the connection’s content must do the claimed work. The relevant use may be distributed over an episode and several contributors, rather than every link being active in a single instant.

A strict profile may define `ExplicitGraphCandidate` by a well-formed object, a nondegeneracy account, and a causal-use account. Its failure is a failure of that representation route. The authority’s OCA uses `Attempt`, not `ExplicitGraphCandidate`. An artist, learner, or investigator with genuine inexplicit explanatory organization is not excluded merely because a complete graph cannot be supplied.

`Account_M(x,p,b;scope)` remains substantive. A domain adapter describes how it assesses the work done by the explanatory commitments and distinguishes that assessment from predictive fit, correlation, graph reachability, and favorable review. The adapter supplies cases and criticisms, not a universally reliable adequacy function. The legacy name `Adeq` may be retained only as an explicit alias with the same scope and interpretation indices.

## 15. Criticism and reason-sensitive uptake

A criticism occurrence represents an allegation with a target, problem context, defect, grounds, and proposed bearing. Its standards and interpretation assumptions are dependencies where they do work. A critic can be mistaken about those matters while genuinely proposing a criticism. Therefore `IsCriticismOccurrence` does not require that `Bearing_M` actually hold.

A `ReasonUseCase` identifies the response, criticism, represented grounds, scope of uptake, relevant contrast family, held-fixed conditions, and a causal explanation of what the system did with the grounds. A comparison can concern deliberation, a narrowed conclusion, an evidence request, a changed standard, or a response—not only different final words.

The contrast family must be informative for the particular attribution. Content-preserving recodings are considered only where the system understands them. The effect of changing the alleged defect is interpreted relative to the problem and response. Two reasons can rationally lead to the same action; one reason can be misunderstood; an invalid criticism can genuinely influence a mistaken reason-sensitive response. Perfect rejection of every invalid objection is not constitutive of reason use.

Performed interventions, observations of use, and broader causal explanations can contribute. No four-family intervention battery is mandatory for every case. An adapter requiring such a battery names the stronger property, such as `PassesProtocolRU4`, and does not identify it with `UsesReason`. An unperformed or inconclusive comparison yields missing evidence for that route rather than semantic falsity.

Every claimed protocol outcome is checked against the declared comparison. Recording all comparison fields is not enough; a failed comparison cannot count as a pass. The comparison’s interpretation remains criticizable even when the code executes correctly. A mechanically successful manipulation of a superficial token does not establish the intended counterfactual difference in reasons.

A negative reason-use case needs a causal account that the relevant response was content-insensitive or otherwise lacked the claimed use in the specified respect. The system’s unchanged final action, failed verbalization, or response to an invalid objection is not sufficient by itself.

## 16. Authorship and distributed reconstruction

The normative attribution is `Authors_beta,ell(s,x,p,h,e)`, including the contribution index. It concerns construction or reconstruction of the explanatory organization, not exclusive origination of every input. The associated `OriginCase` records the contribution’s organization, acquisition mode, system boundary and continuity, source materials, channels, attributed contributors, integration, temporal locus, and alternative causal accounts relevant to the attribution.

Sources and collaborators are not decorative annotations when they are essential to deciding who created the organization. A field may be an annotation only when the specific argument does not rely on it; another argument about credit may use that very field essentially.

A reconstruction case explains how a recipient developed a new understanding of a communicated explanation. Equivalent incoming content is compatible with that contribution. A transmission-only case explains that the relevant organization was supplied elsewhere and that the target merely forwarded or selected it without the claimed explanatory reconstruction. The same incoming message can figure in either kind of account; message provenance alone does not decide which occurred.

For a group attribution, contributors may be different actors within the declared composite. The account identifies what each contributed and how those contributions were integrated into one explanatory achievement. Requiring every step to carry the same individual actor ID would wrongly exclude distributed inquiry. Expanding the boundary until an unexplained result becomes internal is not a substitute for an integration account.

A complete channel log is evidence about channel traffic, not a complete account of every prior possession or contribution. An unobserved channel may defeat a particular attribution argument; its mere possibility does not logically prove that the organization was externally authored. A causal account may discriminate alternatives without a performed intervention on every conceivable alternative.

The evidence adapter returns assessments of `OriginCase` applications. The semantic relation is not defined as `no equivalent crossing`, a nonempty trace, a successful set of interventions, or a preferred narrative. Those features must be interpreted relative to the contribution whose origin is at issue.

## 17. Originative acts, critical episodes, and creative critical episodes

The authority’s contribution-indexed definition is retained:

\[
\begin{aligned}
\mathrm{OCA}_{\beta,\ell}(s,x,p,h,e)\iff{}&
\mathrm{Attempt}(s,x,p,h,e)\\
&\land \mathrm{New}_{\ell,\beta}(s,x,e,h)\\
&\land \mathrm{Authors}_{\beta,\ell}(s,x,p,h,e).
\end{aligned}
\]

An `OCARequest` contains that complete key. An `OCACase` links matching cases for the three conjuncts and the problem recognition involved. The finite checker verifies identity and structural connection; the semantic interpretation supplies the substantive claims. Missing evidence is reported without changing the definition of OCA.

A `CriticalEpisodeCase` identifies the represented difficulty, target already available for criticism, criticism occurrence, reason-sensitive response, resulting situation, attributed actor or composite, and their causal-explanatory connection. It requires no authorship of the target. The response may reject the criticism, set a proposal aside, reframe the question, or suspend judgment. It does not have to emit a replacement theory.

A `CreativeCriticalEpisodeCase` adds an OCA contribution connected to that same inquiry. The contribution may precede the criticism, be the explanatory criticism itself, occur in the response, or arise in an associated subproblem. Its connection must explain what work it did. Sharing an episode tag is insufficient, but a chain of content descendants is not necessary.

`LineageCreativeRevision` is an optional narrower profile in which an authored conjecture has a descendant, the descendant is criticized, and a connected response follows. In that profile a provenance path is appropriate, and the original conjecture precedes the descendant’s criticism. That ordering theorem does not apply to every creative critical episode: an original response to an inherited target can be created after criticism has begun.

A creative critical result comprises the resulting situation and identified contributions or resources. A response that remains wrong can still be genuinely critical or creative. Neither `OCA` nor a creative critical episode entails progress, truth, repeatability, universal capacity, or historical firstness.

## 18. Contextual transport and absorption

A `TransportCase` names the before and after situations, the relevant difficulties and commitments, their preservation or change, and the grounds for treating the inquiry as connected. The transport can concern the problem, background, standards, values relevant to attention, or interpretation. A problem–background pair is not a sufficient summary when another component materially changes.

For each named item, the record states whether it is preserved, revised, abandoned, or rendered inapplicable. A revision identifies its successor and explains the connection. An abandonment or inapplicability claim identifies why the old obligation no longer applies or why it remains an acknowledged loss. A preservation claim identifies how the item still does work. Mere entries in four columns do not establish these relations.

A partition of the **declared finite obligation set** can be checked exactly. Exhaustiveness over all semantically relevant obligations is a different claim and requires a coverage argument. The first may pass while the second is unresolved. Tacit, newly discovered, or contested obligations can be represented by additional cases without pretending that an earlier snapshot already listed them all.

A response can atomically create a revised problem and its transport. Alternatively, a later transport entry can describe an earlier response, provided the response does not claim to have referenced a then-nonexistent artifact. Later explanatory recognition is not backward causation.

Absorption uses a separate connection account and preserves historical positions. Neither arbitrary relabeling nor a purely syntactic import discharges an earlier difficulty. Conversely, a genuine explanatory revolution is not rejected because it does not preserve every obsolete demand of the old formulation.

## 19. Explanatory quality, progress, and knowledge creation

### 19.1 A good explanation need not be originated by its current user

A `GoodExplanationCase` concerns explanatory work, scope, relevant criticisms, and comparison with actual alternatives where the comparison matters. It may concern inherited knowledge. An OCA is not a prerequisite for explanatory quality, current usefulness, possession, or reasonable preference.

A comparison can be partial, tied, or unresolved. A reasoned preference can be a substantive contribution; a database field `preferred = x` is not sufficient evidence that x is better. An absence of recorded defeat is not a definition of quality.

Hard-to-vary analysis can contribute to the comparison, with its limitations exposed (§21). It is neither a universal pass/fail certificate for truth nor a requirement that every useful explanation have a completed variation audit.

### 19.2 Progress concerns the whole claimed change of situation

A `ProgressCase` has the following envelope.

```text
ProgressCase = (claim_key, contribution_ids, before_situation, after_situation,
                problem_connection, deficiency_account, explanatory_gain,
                retained_work, superseded_work, material_losses,
                standards_change_account?, scope, grounds, dependencies)
```

The envelope does not require every result to be an adequate candidate explanation of the original problem. A new question is a question, a standard is a standard, and a rejection is a disposition. A limitation can explain why the old numerical question cannot yet be answered; it need not be entered as a rival mass estimate.

Outcome-specific bodies may describe better revision, justified rejection, independent rival adoption, improved reasoned retention, clarification by rejecting a mistaken criticism, an informative evidence request, a better-posed question, improved standards, or a principled limitation. The family is extensible when an additional case respects the authority. No outcome is guaranteed to be progress; no outcome is excluded merely because it lacks a retained replacement theory.

A revision body identifies the criticized target, correction, relevant preserved or superseded explanatory work, and consequences of losses. It does not demand preservation of an old commitment whose defect is part of what has been explained. Disclosure of a loss is not sufficient to make it acceptable. A changed standard requires an account of why the comparison is pertinent and improved, rather than a new criterion selected to guarantee victory.

The body’s content must support a substantive explanation of why the resulting situation is better in the claimed respect. A local gain is labeled local. A comprehensive superiority claim requires correspondingly comprehensive treatment of material losses and displaced tasks. These are explanatory burdens; the checker verifies only the declared formal and record conditions.

### 19.3 Knowledge creation, availability, and historical assessment

The semantic claim of explanatory knowledge creation combines a connected creative critical contribution, actual progress attributable to it, and availability of the resulting knowledge for use or reconstruction by the system **or an explicitly identified community**. A creator can lose access while a collaborating community preserves the result. Availability is not identical to endorsement, permanent storage, or a `Retain` event.

`EKCRequest` therefore specifies the contribution, compared situations, system and boundary, history, scope, and the beneficiary or retaining community. Its cases remain separable. An in application for an improvement case is not a computed fact that actual improvement occurred.

The legacy symbol `K_E` may be used only as a declared alias of this fully indexed progress claim. A token `y` and two problem–background pairs are insufficient when contributions, standards, values, or other material aspects of the situation differ.

Later criticism of a premise can remove current support for an earlier progress claim. The historical claim is then presently disputed; its truth was not changed by the new certificate. New circumstances or a newly posed problem generate another indexed claim, not a retroactive mutation of the old one.

## 20. Capacity and the limits of finite observations

The semantic predicates `Can`, `UU`, `UC`, and `UED` are those of the authority, with explicit domains, achievement respects, enabling conditions, attribution boundaries, and organizational continuity. They are not evaluated by finite fixture enumeration.

An `ObservedCoverageReport` describes witnessed activities in a declared domain and the perturbations actually considered. A `CapacityCase` gives an explanatory argument that a continuing organization has a specified ability under an independently described family of enabling conditions. These are distinct objects. A collection of successful continuations is not substituted for that organizational argument.

A capacity case identifies why the relevant variation in problem or reasons is handled by the organization, which resources and external contributions are allowed, which interruptions or recovery conditions are covered, and which architectural barriers would refute the claim. It must not define the domain as whatever the target succeeds at, or let enabling conditions supply the claimed solution under the label of resources.

Understanding a communicated explanation can be an achievement and can create knowledge for the learner. It does not by itself demonstrate origination of an unsupplied solution in a challenge requiring that achievement. A case must match the challenge’s achievement respect rather than switch it after observing success.

A negative capacity case may explain a genuine organizational barrier or, for an explicitly finite transition model, establish the absence of a required continuation under complete stated assumptions. A failed trajectory is evidence about that attempt, not automatically such a barrier. A negative claim must also distinguish destruction of the capacity from a failure within enabling conditions that are supposed to preserve it.

The default capacity vocabulary does not require a fresh, system-new explanation of the same solved problem after every reachable snapshot. That stronger condition would demand inexhaustible novelty under the chosen scope and may fail even for an organization capable of the relevant inquiry. It can be investigated as a separately named repeatability hypothesis, with resource renewal and achievement conditions explicit; it is not hidden in the definition of general creativity.

A domain containing one problem can support a domain-restricted capacity claim. Increasing its cardinality to two does not establish universality or cross-domain creativity. Diversity is explanatory, not a counting threshold. The unrestricted authority target remains a substantive capacity claim across independently admitted explanatory subject matters, not a larger finite benchmark.

## 21. Explanatory constraint and reach

A variation case identifies an explanatory detail, the job it is purported to do, the background, and a material alternative. `FreeVariation` concerns whether that detail can be changed without losing its claimed explanatory work and without an independently reasoned compensating explanation. It does not require the variant to be a true explanation. Otherwise every false myth could appear rigid merely because its equally arbitrary variants were also false.

A variation family must be informative: empty sets, mere recodings, and families selected to exclude the relevant objection do not establish nonarbitrariness. Distinct, independently reasoned explanations of the same problem are not automatically arbitrary variants of one another. Scope and respect remain explicit.

A finite adapter can report `FreeVariantCaseFound` or `NoFreeVariantCaseFoundInV`. A positive assertion of `ConstrainedRelativeToV` additionally depends on the substantive assessment of the family’s informativeness and the proposed comparisons. No finite loop promotes it to unrestricted hardness to vary. Tight internal constraint does not imply truth, explanatory reach, or universal capacity.

A `ReachCase` identifies the explanation’s unchanged commitments, the further problem, additional facts or auxiliaries, the role of the explanatory connections, and any newly created bridge. Paths through an explicit graph can help inspect that account, but graph reachability alone does not establish reach. A field called `added` may not conceal the complete answer or an independently created bridge while crediting the original explanation for all of it.

A new bridge can be valuable knowledge. It receives its own contribution attribution. The original explanation’s reach is the work actually done by its commitments, which can exceed anything listed or noticed by its creator. A finite coverage report and a general reach argument remain different claims.

## 22. Contrast classes and discriminating countermodels

A generator, predictor, search procedure, learning procedure, deductor, computer, or selection process can be a component of a creative system. Classification by a broad mechanism name does not decide what explanatory organization that particular system has.

A countermodel against an entailment must satisfy the antecedent under a substantive interpretation and falsify the consequent under that same interpretation. To show that predictive output does not entail OCA, for example, one can specify a relay that selects a supplied answer without a represented explanatory problem or without constructing the organization it outputs. Failure of an optional explicit-graph predicate does not suffice, since OCA does not contain that predicate.

Two finite records can be compatible with different causal explanations of authorship. A demonstration of underdetermination must identify the unobserved difference or the inadequacy of the record, not merely flip an `Authors` Boolean while claiming the entire relevant organization has been held fixed. Likewise, finite behavioral agreement alone does not establish universal capacity; the competing models must explain their different continuations or domain barriers.

A biological adaptation can instantiate physical knowledge without representing an explanatory criticism. That contrast does not deny that blind lower-level variation can participate in a higher-level creative organization. The attributed system, level of organization, and semantic roles must be stated.

## 23. Physical realization module

The physical module is a declared extension, not part of the minimum finite checker. Its realization account identifies physical assumptions, substrates and relevant attributes, represented contents, activities, interventions, system boundaries, resources, tolerances, and error correction where retained capacity is claimed.

It must preserve the distinctions it projects: different reasons correspond to the relevant differences in the organization’s use of them; content occurrence, interpretation, ancestry, transport, and causal attribution are not conflated. One consistent interpretation is used across the contrasts rather than a new convenient mapping for each output.

A one-time originative act does not require perpetual retention or repeatability. A retained capacity does require an account of the conditions that preserve or restore it. Constructor-theoretic possibility and explanatory universality are separate claims. No result about consciousness, personhood, moral standing, or species membership follows from the record predicates alone.

`K_CT` is reserved for a separately specified constructor-theoretic knowledge predicate. This document does not provide a complete mathematical definition of it or a theorem relating it to explanatory progress. A physical-stage release must supply that definition, the necessary physical assumptions, and any claimed bridge or non-equivalence argument before reporting those obligations discharged. The source books motivate the distinction; their citation is not a completed formal module.

# Part III. Consequences, fixtures, and development gates

## 24. Results and their exact strength

| Result | Status and argument | What it does not establish |
|---|---|---|
| External record ancestry is acyclic. | Under §§7–8, each external parent is available from the strict causal past or is initial. A cycle among noninitial creators would contradict the strict order; an initial artifact has no incoming creator edge. | Semantic opposition, shared explanation, or reciprocal constraint need not be acyclic. |
| A cut is inert. | A cut is a selection of already specified entries. Repeating the selection creates no artifact and changes no target occurrence. | Producing a report is not itself a causally inert action by a recorder. |
| A fully grounded packet can be represented by a fresh extension. | In an extensible record language, assign fresh IDs, use the selected cut as finite causes, and introduce no incompatible transaction. This constructs one extended representation. | No actual actor, physical archive, or target is guaranteed to continue. |
| DA-1 terminates on finite input. | The two label sets grow monotonically and are bounded by the finite application set; §11.3 gives the bound and disjointness argument. | The policy does not decide every semantic claim. |
| An in application has in essential applications. | This is a necessary condition for its entry into `I`; fixed-point iteration preserves it. Recomputed loss of a premise removes the dependent’s in status. | The premise is not thereby true; another argument for the same conclusion may remain usable. |
| The raw presence summary is monotone under additional cases for the same exact claim. | Each polarity’s existence bit can change only from absent to present when its indexed cases are retained. | Usable-case status need not be monotone; new case content is not irrelevant. |
| Matching contribution indices prevent cross-event OCA splicing. | A case at another contribution index fails the identity guard before its semantic premises are considered. | Matching indices do not establish any of the three semantic conjuncts. |
| A finite repertoire inventory does not entail an exhaustive semantic inventory. | A model can contain an earlier, unrecorded possession without changing that inventory. The coverage bridge is a distinct premise. | Semantic newness is not declared unknowable; an explanatory account may support it. |
| A terminal creator is representable. | The finite record contains a contribution and no later target activity; no target-extension axiom forbids this. | Whether that contribution is actually originative still requires its semantic account. |
| Historical acyclicity permits semantic opposition cycles. | Later records can represent opposing applications whose targets already exist. Their opposition can be cyclic while record creation remains acyclic. | Cycles alone do not determine explanatory merit or mandate a unique policy. |

The reference implementation checks finite contracts and DA-1. The accompanying tests include an independent enumeration of all two-node dependency graphs, attack graphs, and three-valued readiness assignments: `16 × 16 × 9 = 2,304` cases. That enumeration checks the least-labeling property on those finite cases; the general policy argument remains the mathematical argument above. It is not a machine proof of the entire semantic theory.

## 25. Non-entailments and their witnesses

| Non-entailment | Discriminating interpretation |
|---|---|
| OCA does not entail successful knowledge creation. | A system originates a false attempted explanation and makes no actual explanatory improvement. |
| OCA does not entail continuing or universal capacity. | An originative contribution occurs once; the organization then ceases to function or has an independent domain barrier. |
| A critical episode does not entail authorship of its target. | An investigator reasons about a theory received from a predecessor. |
| A creative critical episode does not entail target-to-result ancestry. | A novel explanation of a defect or an independently originated rival contributes to criticism of the inherited target. |
| Receiving equivalent content does not entail absence of reconstructive authorship. | A learner creates an understanding of a communicated explanation that the learner had not previously possessed. |
| Earlier attempted use plus later authorship does not entail earlier OCA. | The earlier act lacks authored organization; the later act cannot supply its contribution-indexed conjunct. |
| A failed explicit-graph audit does not entail absence of an attempt. | An inexplicit explanatory contribution is not represented by the selected graph profile. |
| An inherited explanation can be good without the current user’s OCA. | Its problem-relevant explanatory work and merits do not depend on that user being its author. |
| Current support does not entail truth or actual progress. | A provisionally used premise, interpretation, or argument is wrong without a recorded successful objection yet. |
| Goodness in a stated respect does not entail complete truth. | An approximate or qualified account does useful explanatory work without being correct in every respect. |
| Constraint does not entail truth. | A tightly constrained attempted explanation is false. |
| Falsehood does not entail constraint. | An arbitrary myth and arbitrary variants are all false while preserving the same purported explanatory work. |
| Record completeness does not entail repertoire completeness. | An earlier understanding was forgotten or not recorded. |
| Graph reachability does not entail explanatory reach. | The added graph edges merely insert the new answer without explaining it from the original commitments. |
| Finite behavioral agreement does not settle universal capacity. | Rival organizational accounts agree on observed cases but differ at an independently characterized, unobserved domain barrier. |
| Reconstruction of a supplied answer does not establish unsupplied origination capacity. | The achievement and the environmental contribution differ even though the final understanding is valuable. |

These are interpreted counterexample patterns. The test suite includes stipulated finite instances of several patterns. It does not establish that an arbitrary real system instantiates them merely by setting matching Boolean fields. Any future claim that a countermodel has been fully formalized must supply its complete interpretation and check the relevant antecedent rather than just label the conclusion false.

## 26. Regression and mutation discipline

A regression specifies the phenomenon, the authority clause at risk, the exact representation under test, and the expected record-level result. A mutation deliberately removes or alters one mechanism. The test must then detect the change for the reason claimed. The existence of a failing test does not establish that the chosen encoding is semantically necessary; another encoding can preserve the same distinction.

| Mechanism under test | Fault deliberately introduced | Required detection |
|---|---|---|
| All typed references are grounded. | Ignore a nested reference or permit a future transport reference. | The malformed record cannot pass the same grounding check. |
| Branch consistency. | Permit a comparison to depend on incompatible occurrence branches. | The finite history check detects the incompatible causal past. |
| Contribution identity. | Ignore the authorship contribution index. | Later reconstruction cannot be used to validate the earlier act. |
| Fixed attribution boundary. | Match evidence while ignoring its boundary. | A foreign-boundary case cannot answer the query. |
| Body outcome checking. | Treat a failed but admitted body as locally ready. | Its case cannot enter the usable summary through that route. |
| Essential dependency. | Exempt criticisms from dependency withdrawal. | A criticism using the withdrawn standard or observation loses in status. |
| Activation assessment. | Treat a missing activation assessment as present. | The application remains unassessed rather than silently in. |
| Variation-family informativeness. | Let an empty family count as evidence of constraint. | The output identifies the uninformative family. |
| Scope-specific use. | Identify physical applicability with conditional mathematical consequence. | Criticism of physical applicability cannot automatically refute the conditional algebra. |
| Case conflict. | Use a positive premise while concealing the appraised contrary case. | The report exposes the conflict and the affected premise use or conditional dependency. |

The mutation runner distributed with this specification executes a selected subset of these fault injections against the reference checker. Its report states which mutations were actually run and detected. The table itself is a contract for broader testing, not a claim that every row has an executable mutation in the current package.

## 27. Fixture A — two balances, method criticism, and scope

This is a stipulated inquiry, not a report of a physical laboratory. The full grounded record and appraisal slices are in `verification/fixtures.py`, function `balances`. That fixture synchronizes the represented inquiry and recording sequence for the activities it models. The semantic adequacy of its stipulated review judgments is not proved by executing it.

An investigator sees readings 10 and 12 for one object. She proposes that the second balance is correct and the first reads two units low. A rival proposal, that the first is correct and the second reads two units high, is also represented. Both contents are available; their entry events are not declared physically incompatible.

A critic challenges the rule selecting the second balance as the reference. A provisional reviewer treats the circular reference-selection argument as defective. This removes the usability of the original adequacy application that essentially used that rule. It does not make the rival theory true and does not establish that the investigator herself has accepted the criticism.

The investigator reframes the question. The response atomically creates the revised question and its transport, so no response refers to a future transport artifact. She then proposes the additive model:

\[
10=x+b_A,\qquad12=x+b_B.
\]

For any admitted shift `lambda`, replacing `(x,b_A,b_B)` with `(x+lambda,b_A-lambda,b_B-lambda)` leaves both readings unchanged. The equations determine `b_B-b_A=2`, not the absolute mass. The result is a limitation under the model and a more appropriate demand for an independent constraint—not an invented numerical answer.

The fixture’s appraisal slices have these record-level results:

| Slice | Added appraisal material | DA-1 result |
|---|---|---|
| `balances-r1` | Reference-selection criticism and its activation assessment. | The original adequacy application is out because its reference-standard use is out. |
| `balances-r2` | Additive-model account, limitation argument, and local progress case. | The limitation and progress-case applications are in under their stipulated premises. |
| `balances-r3` | A provisionally accepted challenge to the particular inferential rule application used by the limitation criticism. | That criticism, its dependent limitation case, and the dependent progress case become out. |
| `balances-r4` | A countercriticism of that rule challenge. | The rule challenge becomes out and the dependent applications return in. |
| `balances-r5` | A criticism of treating the additive model as an accurate description of the physical apparatus. | Its physical-application use becomes out; the conditional algebraic consequence remains in. |

The rule challenge at `r3` is a deliberately stipulated stress case, not an assertion that the displayed algebra is actually invalid. It tests withdrawal of a criticism’s essential premise. The countercriticism illustrates that the appraiser can itself be wrong and later revised.

`XM-as-formal-premise` and `XM-as-physical-model` are distinct applications of the same content. Their distinction prevents a valid objection about changing offsets from automatically refuting the mathematical statement conditional on constant offsets. A claim applying the limitation to real apparatus would need its physical-application premises as well.

A subsequent engagement entry closes the episode for now. It does not destroy the result or prevent later criticism. Every emitted evidence report retains `semantic_decision = NOT_EVALUATED`. Actual progress and actual reason use remain claims requiring the interpretation of the inquiry.

## 28. Fixture B — inherited target, independent rival, and contrary evidence

This stipulated fixture uses the seasons theme to exercise provenance separation and evidence dependency; it does not compute the truth of a climate model. The grounded record and appraisal slices are in `verification/fixtures.py`, function `seasons`.

An inherited explanation `XP` is available before the episode. The investigator creates a candidate `XA0`, criticizes `XP`, and adopts `XA0`. Adoption is not represented as descent from `XP`. A subsequent criticism distinguishes an account of illumination from an account of temperature timing. The response creates `XA1` with the additional explanatory background and records the change of situation.

An adequacy case for `XA1` is submitted, followed by a local progress case using an explicit adequacy-premise application. The report can inspect the positive case separately from the premise use made of that case. It does not conflate a case’s recorded survival with the unconditional truth of its claim.

A negative adequacy case is then recorded. The reviewer gives a conflict account and suspends the particular positive adequacy-premise use on which the progress case relied. Both raw cases remain available. Later a criticism challenges the negative case’s applicability, and the reviewer’s recomputation can reinstate the premise use.

| Slice | Case and application state | Significance |
|---|---|---|
| `seasons-r1` | Positive adequacy case, its premise use, and the dependent progress case are in. | A provisional evidence configuration, not certified knowledge creation. |
| `seasons-r2` | Positive and negative adequacy cases are both in, while the explicit conflict application makes the adequacy-premise use and dependent progress case out. | The positive certificate cannot silently bypass the appraised contrary case. |
| `seasons-r3` | The negative-case application is out under the scope criticism; its conflict application is out; the positive premise use and progress case are in. | Withdrawal and reinstatement affect applications, not the existence of old records. |

The conflict application is a stipulated reviewer judgment with grounds, not an automatic truth rule triggered by the mere existence of two polarities. Another appraiser can retain a conditional argument, investigate further, or challenge the conflict interpretation; it must expose those decisions and their dependencies.

The fixture illustrates that an inherited target can be part of a creative critical inquiry and that a rival need not share ancestry with that target. The code checks recorded identity, reference grounding, application binding, and the displayed label transitions. The actual authorship and epistemic success of the described contributions are not inferred from that code.

## 29. Stepwise construction and gates

The stages identify releasable increments. A stage can remain useful while later substantive attribution work is unresolved. An implementation report must not mark a stage complete merely because this specification describes its desired behavior.

| Stage | Deliverable | Exit condition | Dependency |
|---|---|---|---|
| `S0 — Authority and interpretation` | Version binding, claim keys, source/assumption ledger, and semantic mapping. | No operational predicate silently replaces a semantic predicate; preservation cases and unsupported routes are stated. | Authority adopted for that build. |
| `S1 — Record integrity` | Typed artifact references, finite causal snapshots, receipts, content versions, atomic local references, and cut digests. | Grounding, uniqueness, branch, ancestry, late-recording, absorption, and closure cases behave as specified. | S0. |
| `S2 — Appraisal bookkeeping` | Application-use graph, declared checks, essential dependencies, DA-1 or another named policy, and scoped reports. | Failed bodies do not count; missing premises are exposed; criticism dependencies withdraw; cycles and contrary cases remain visible; report identity is complete. | S1. |
| `S3 — Semantic adapter contracts` | Separately reviewable adapters for attempts, reason use, authorship, novelty, and episode connection. | Copiers and reconstructors are distinguished by causal accounts; inherited targets, tacit cases, and independent rivals are not excluded by format; no claim is manufactured from missing evidence. | S0–S2. |
| `S4 — Transport, progress, and retention` | Situation-indexed comparison and knowledge-creation cases with outcome-sensitive bodies. | Limitations, criticism rejection, evidence requests, reframing, standards change, and community availability are supported; destructive local repair is not labeled global progress. | S3. |
| `S5 — Recursive effect` | Method-change proposals, enactments, and effect accounts involving operative rules. | A criticism can lead to a declared change in actual use; an archive-only observer is not misclassified as target recursion; unchanged verdicts remain possible when objections fail. | S2–S4 as used by the chosen organization. |
| `S6 — Domain and capacity arguments` | Distinct observed-coverage and modal-capacity dossiers, including architecture-barrier cases. | No empty-domain, favorable-boundary, answer-supply, failed-run, or perpetual-freshness substitution; universal claims retain their full independent domains. | S3–S5. |
| `S7 — Physical realization` | Explicit realization model, resource conditions, tolerances, and any constructor-theoretic bridges. | The exact attributed predicate and physical assumptions are linked; retained capacity is not imposed on one-time acts; reserved physical claims are actually defined before use. | S0 plus the semantic predicates being realized. |

The included reference is a testable subset of S1–S2 with selected projection safeguards. It is not a complete S1 storage service, a complete history interpreter, a semantic attribution engine, or an implementation of S3–S7. Examples of remaining engineering work include a persistent receipt store, parser adapters that extract all typed payload references, full signature checking, a derivation adapter, and a complete report-binding validator. These engineering tasks are distinct from the explanatory problems of interpreting meaning, origin, and capacity.

The next implementation increment is to connect the finite checker to an actual stored dossier and parser while preserving the exact claim keys and record/semantic separation. Only then should a semantic adapter be added and challenged with the positive as well as negative preservation cases. Wiring an LLM to output favorable Boolean predicates would not complete that adapter.

## 30. Revision triggers and non-regression

The record design requires revision if a genuine late-recorded history cannot be represented without reversing causal order, if incompatible possible events cannot be described together, or if an actual provisional closure has to be suppressed to preserve a fallibility slogan.

The appraisal policy requires revision or a different declared scope if it systematically obstructs a defensible use of mutually constraining explanations, hides a material premise, silently elevates a failed check, or treats the latest objection as correct merely by date. A counterexample to DA-1 need not be a counterexample to the semantic authority.

The origin and uptake adapters require revision if they classify generic compliance as reason use, deny a communicated reconstruction solely because of its source, or exclude a genuine inexplicit contribution because it lacks a prescribed artifact. Those cases require causal explanations, not a rule that every favorable human description must be accepted.

The progress adapter requires revision if it can declare victory by changing standards without explaining the change, by renaming the problem, by concealing relevant losses, or by treating a question as though it were a newly adequate answer. It also requires revision if it excludes an explanatory advance merely because the result is a limitation or a correction to a criticism.

The capacity account requires revision if it depends on favorable choices of domain or boundary, answer-bearing enabling conditions, unacknowledged external authorship, or perpetual production of new answers to already exhausted tasks. A genuine organizational barrier must be addressed rather than removed by redefining the challenge after failure.

# Part IV. Declaration status, sources, and release meaning

## 31. Declaration and migration ledger

| Family or legacy name | Status in this specification | Interpretive boundary |
|---|---|---|
| Authority commitments, `Account`, `Bearing`, `Authors`, `UsesReason`, `Progress`, `Can`, `UU`, `UC`, `UED` | Imported semantic commitments and relations. | No executable truth oracle is supplied. |
| `Entry`, `Artifact`, `Snapshot`, references, digests | Chosen finite recording representation. | Record order is not the target’s entire history. |
| `ActorId` with recorder/target roles | Chosen identity representation. | One actor can occupy both roles. |
| `AncestorOrSelf` | Record-ancestry closure replacing ambiguous `DescEq` terminology. | Not equivalence or general explanatory continuity. |
| `Application`, `Assessment`, DA-1 | Chosen fallible appraisal representation and policy. | Application labels are not explanatory merit or truth. |
| Raw and usable case summaries | Chosen evidence displays. | “Positive case only” does not mean confirmed, proved, or rationally preferred. |
| `CompleteRecordedRange`, `CoverageBridge`, `UniversalArgument` | Separated completeness and quantification claims. | Finite exhaustion is not global semantic coverage. |
| `Attempt`, OCA | Authority predicates with full indices. | Optional graph checks do not replace them. |
| `ExplicitGraphCandidate`, `PassesProtocolRU4` | Optional stronger profile predicates. | Unsupported cases and restricted meaning must be visible. |
| `CriticalEpisodeCase`, `CreativeCriticalEpisodeCase` | Evidence structures for the authority’s episode relations. | Authorship of the initially criticized target is not required. |
| `LineageCreativeRevision` | Optional restricted descendant-revision profile. | Provenance-path necessity is local to that profile. |
| `OriginCase`, `ReasonUseCase`, `TransportCase`, `ProgressCase` | Evidence-account structures. | Well-formedness is not semantic adequacy. |
| `Adeq`, `K_E` | Permitted aliases only with the full authority meanings and indices. | Abbreviations cannot omit material situations or contribution identity. |
| `GoodNow` | An appraisal or quality claim, explicitly labeled as such. | No OCA prerequisite for inherited good explanations. |
| `OCap`, `Cap_CR`, `GCD` | Legacy capacity names require separately declared mappings before reuse. | No implicit perpetual-freshness or finite-cardinality substitute for `Can` or universality. |
| `ObservedCoverageReport`, `CapacityCase` | Distinct observational and modal-argument records. | Finite successes do not decide the modal relation. |
| `FreeVariation`, finite variation summaries, `ReachCase` | Authority relations and restricted evidence reports. | False variants and explanatory work cannot be replaced by truth checks or graph reachability. |
| `K_CT` | Reserved physical-module predicate. | Not defined or proved by the finite kernel. |
| Typed finite derivations | Normative adapter contract, not implemented by the reference subset. | No absence-to-negation rule, no finite-to-unrestricted promotion. |

The required primitive names and indices for an executable release are generated from that release’s typed schemas, not from an informal symbol list alone. A semantic relation may be declared without a decider. An executable function may not remain undeclared, untyped, or silently delegated to an unspecified external service.

## 32. Sources and attribution limits

**Normative semantic source:** `PopperSemanticsV1_1.md`, especially Part I-A, Part II’s sections on occurrences, dependency, newness, authorship, critical processes, transport, progress, and universality, and Part IV’s refinement contract. Its source keys identify the supplied works by David Deutsch and Chiara Marletto and distinguish their claims from this project’s constructions.

**Deutsch, The Fabric of Reality, Chapter 3:** the recursive subsidiary-inquiry account, particularly printed pages 67–68, motivates method and problem revision without a completed hierarchy of judges. It does not prescribe this event schema or DA-1.

**Deutsch, The Beginning of Infinity, Chapters 1 and 16:** the explanation/constraint distinction and creative reconstruction account motivate the treatment of false explanatory attempts, explanatory reach, and learning from communicated ideas. They do not supply a finite certificate definition of understanding.

**Marletto, The Science of Can and Can’t, Chapters 5 and 7:** physical knowledge, retained capacity, and the objective framing of creativity motivate the physical-module distinction. A complete formal bridge remains a separately stated obligation.

Historical comparisons with Popper, Bartley, abstract argumentation, four-valued evidence displays, or event-structure formalisms can be useful research inputs. They are not independent normative premises of this specification. Exact historical claims or formal import theorems require inspection of their primary sources before they are reported as established. The implementation choices stated here are this specification’s proposals, not formulas attributed to those authors.

No unavailable prior project schema is required to interpret the contracts in this document. A module that reuses such a schema must identify its exact version and restate the imported contract in its own release manifest. A source’s name does not complete a missing declaration.

## 33. What a release may claim

A conforming report may state that specified bytes passed specified finite checks, that a case is present, that an application is in under a named policy, that an exact fixture produced the predicted labels, or that a conditional derivation follows from its declared premises. Each statement is scoped to the actual check or argument performed.

It may also record a person’s or system’s reasoned judgment that a contribution was creative, a criticism successful, or an organization universal. That remains an identified, criticizable attribution with substantive explanatory grounds, not a machine certificate of truth.

No finite release may infer semantic failure merely from an unsupported evidence format, or infer semantic success merely from a populated schema. The purpose of implementation is to preserve, expose, and test the relevant distinctions while enabling inquiry—not to replace the explanatory question with a score or a fixed vocabulary of acceptable answers.
