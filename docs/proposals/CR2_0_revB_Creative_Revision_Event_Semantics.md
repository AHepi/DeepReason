# CR-2.0 proposal — Creative Revision Event Semantics

## Revision B — transition-kernel shape

## Status

This document revises the CR-2.0 proposal so that its kernel has the shape of a non-terminating process rather than a function that returns a verdict. It is a **proposed** revision, not an adopted one. Every change is listed in the change register at the end with its reason and the observation that would revert it. No change is adopted until a human act adopts it.

Unchanged from the original proposal: CR-1.0 remains the source-grounded authority for what it says. CR-EIB remains the fidelity and proof-assurance layer. CR-2.0 is a criticisable modelling conjecture whose purpose is to make the central semantics mathematically explicit enough to construct, refute, and revise.

Every declaration carries two independent fields:

```text
origin: source | user_adopted | model_conjecture
inferential_status: DEF | IMP | DER
```

A source citation does not make a proposition derivable. A formal proof does not make a translation faithful.

## What changed in this revision

The original proposal closed each episode with a decision event and gave correction certificates an endpoint. Both import a terminus that the explanatory framework denies. Theories do not close. Attention lapses.

This revision therefore:

- removes decision events from the kernel;
- makes every stop a **cut** in the observation rather than an event in the process;
- requires the kernel's extension structure to be **total**, so that no state is terminal;
- evaluates every claim **at a cut** with a four-valued evidence status;
- separates **prefix facts**, which are monotone under extension, from **statuses**, which are revisable;
- replaces the certificate endpoint with a **cut version**;
- records the cause of a stop as an optional provenance fact in the application dossier, never as a reason the kernel requires.

The stop is now a fact about the observer's record and the system's resource allocation. It never bears on what a content version is.

## Executive judgment

The previous mapping did not stall because the language model lacked reasoning effort. It stalled because CR-1.0 deliberately stops at a typed semantic schema while the requested destination is a substantive mathematical theory.

CR-1.0 leaves `Explains`, `Authors`, `K_E`, `UsesReason`, `SameJob`, `Var_V`, `StableOrg`, physical possibility, and the realization map as substantive interpretations. CR-EIB correctly turned those unresolved meanings into typed opaque ports. That makes a safe executable shell possible, but it cannot make the ports true, decide their extensions, or explain why they have the intended meanings.

The primary sources leave the decisive gap open. Deutsch distinguishes explanation from prediction while acknowledging that a precise definition of explanation is difficult. He says that the physical distinction between creative and non-creative processes was not yet expressible, and that AI remains blocked because creativity itself is not understood. Marletto gives a physical definition of knowledge and a counterfactual task vocabulary, but describes the laws of knowledge creation as still to be discovered.

A stronger proof assistant, a larger prompt, or deeper reasoning cannot derive missing nonlogical content from syntax. It can only hide the missing content, expose it as an import, or propose a new theory. The next useful step remains to **fork the project explicitly**.

| Product | Legitimate objective | What it cannot do |
|---|---|---|
| CR-1.0 conformance | Preserve and type the existing report exactly | Complete meanings that the report leaves primitive |
| CR-EIB assurance | Anchor translations, check types, replay proofs and countermodels | Decide source fidelity or semantic truth automatically |
| CR-2.0 theory | Introduce new substantive semantics and expose their falsification points | Claim that Deutsch or Marletto already supplied the theory |
| Application classifier | Test a particular system under declared evidence and boundaries | Infer open-ended creativity from outputs alone |

CR-1.0 and CR-EIB should be frozen, tagged, and retained. CR-2.0 should begin on a separate versioned branch.

## Design objective

CR-2.0 should not try to eliminate every semantic primitive. That is impossible without replacing meaning by a proxy. Its objective is narrower:

> Replace unstructured Boolean primitives with explicit mathematical objects and inspectable witness types, so that every unresolved semantic judgment has a location, a contrast class, a positive certificate, a refutation certificate, and a declared boundary of applicability.

This revision adds a second objective of equal weight:

> The kernel is a process, not a function. Steps terminate; the process does not. Every attribution is made from a finite prefix at a declared cut, and "not yet in the prefix" is a legitimate status.

The core should be closed structurally and open semantically. Structural claims should be machine-checkable. Domain meanings should enter through small typed interfaces. Missing evidence should remain open rather than becoming false. Contradictory evidence should remain contested rather than causing explosion. No state of the kernel should be one from which nothing further can happen.

## Architecture

CR-2.0 has four mechanically separate layers.

| Layer | Contents | Status |
|---|---|---|
| Creative Revision Kernel | Event space, causal order, conflict, configurations, runs, cuts, content versions, overlapping spans, provenance links, evidence ledger | Closed structural calculus |
| Domain Profile | What counts as an explanatory job, defect, repair, preservation, adequate rival, and scope in one domain | Explicit semantic import |
| Application Dossier | Boundary, traces, interventions, evidence records, resources, repertoire, provenance facts, record-completeness declarations, lapse causes | Empirical import |
| Physical Realization | Physical states, information variables, task networks, tolerances, resources, retained capacity, and commuting realization maps | Constructor-theoretic and physical import |

The kernel must never import a science, art, AGI, or constructor-theory judgment merely because one application needs it. It must also never import a reason for stopping. Why a system reallocated its resources is a dossier fact, recorded when known, absent when not.

## 1. Domain profile

Let a domain profile be

\[
\mathcal D =
\langle
C,P,B,K,L,\equiv,
\mathsf{Job},
\mathsf{Defect},
\mathsf{Addresses},
\mathsf{Preserves},
\mathsf{Adeq}^{+},
\mathsf{Adeq}^{-}
\rangle .
\]

| Symbol | Role |
|---|---|
| \(C\) | Content versions |
| \(P\) | Represented problems |
| \(B\) | Backgrounds or contexts |
| \(K\) | Criticisable standards |
| \(L\) | Content-equivalence levels |
| \(\equiv_\ell\) | Equivalence at declared level \(\ell\) |
| \(\mathsf{Job}(x,p,b)\) | Content \(x\) purports to address problem \(p\) against background \(b\) |
| \(\mathsf{Defect}(c,x,p,b,k,\delta)\) | Criticism \(c\) alleges defect \(\delta\) in \(x\) under standard \(k\) |
| \(\mathsf{Addresses}(x,\delta)\) | Typed positive evidence that \(x\) addresses defect \(\delta\) |
| \(\mathsf{Preserves}(x_1,x_0,m)\) | Evidence that merit or commitment \(m\) was preserved, or that its loss was disclosed |
| \(\mathsf{Adeq}^{+}(x,p,b)\) | Positive adequacy-certificate type |
| \(\mathsf{Adeq}^{-}(x,p,b)\) | Refutation-certificate type |

These are not all Boolean predicates. The final four positions are **types of evidence records**. An inhabitant must identify the reason, scope, evidence, provenance, reviewer or instrument, and dependencies. Absence of an inhabitant is not negation.

A science profile can interpret the contents as explanatory theories. A mathematics profile can interpret them as conjectures, definitions, proofs, and proof obligations. An art profile can supply aesthetic problems and standards without pretending that every artwork is a scientific explanation. The creative kernel remains unchanged.

## 2. Content versions

A content version is

\[
x=\langle id,\;surface,\;normal,\;roles,\;parents,\;anchors\rangle .
\]

`surface` retains the full prose, diagram, formula, artefact, or inexplicit-state locator. `normal` is an optional formal interpretation. `roles` may include problem, conjecture, criticism, standard, explanation, observation interpretation, or response. Roles may overlap. `parents` records revision or reconstruction ancestry. `anchors` bind the version to its source or trace.

The formal normal form never overwrites the surface content. A valid prose distinction is not defeated merely because the current formal vocabulary cannot yet express it.

No content version is final. "Current" is always relative to a cut (§5). A version acquires successors through events; it never acquires a status by the absence of events.

## 3. Creative event structure

### 3.1 The event space

A domain's creative histories are configurations of a labelled event structure

\[
\mathcal E_{\mathcal D}
=
\langle
E,\preceq,\#,\lambda,\mathsf{in},\mathsf{out},\Pi
\rangle ,
\]

where \(E\) is a set of **possible** events, \(\preceq\) is a causal partial order, \(\#\) is an irreflexive symmetric conflict relation inherited along \(\preceq\), \(\lambda\) assigns event kinds, `in` and `out` assign consumed and produced content versions, and \(\Pi\) is a provenance graph over events and versions.

The event space is not a record of what happened. It is the space of what can happen. A record is a configuration of it.

### 3.2 Configurations, runs, and cuts

A **configuration** is a finite subset \(r \subseteq E\) that is conflict-free and downward-closed under \(\preceq\). A **run** is a configuration. Runs are ordered by inclusion; \(r \subseteq r'\) means \(r'\) extends \(r\).

A **cut** is a run designated for observation. Every attribution in CR-2.0 is made at a cut. Nothing in the kernel distinguishes a cut from any other run except that an observer stopped recording there.

### 3.3 Totality

\[
\forall r \text{ a configuration},\;\exists e \notin r:\; r \cup \{e\} \text{ is a configuration.}
\]

Every finite configuration has a proper extension. Equivalently, the event space has no maximal finite configuration. No run is terminal. Runs end only at cuts.

Totality is an axiom of the kernel and a theorem obligation for every implementation: a kernel that admits a configuration with no extension has smuggled in a terminus. The weakest extension always available is an attention event, because a system that can attend to anything can attend again.

### 3.4 Event kinds

```text
Attend
EnterConjecture
Criticize
InterpretEvidence
Respond
Retain
Reframe
Restandardize
RepertoireExpand
Merge
```

`Decide` is removed. It was an episode-level summary of the most recent `Respond` and a stop marker in one; the summary is now derived (§5.3) and the stop is a cut (§5.4). `Reopen` is removed as a kind: reopening is an `Attend` whose provenance links target content from an earlier span (§5.5).

Independent events may be concurrent. Backtracking is represented by later events that depend on earlier content. The same event or content may belong to several spans. A span may influence, merge into, or be absorbed by another.

### 3.5 Conjecture-before-criticism invariant

Every criticism targets a conjecture that already exists in the configuration:

\[
\mathsf{Criticize}(e_c,c,x)\in r
\;\Rightarrow\;
\exists e_x\in r,\; e_x\prec e_c,\;\mathsf{EnterConjecture}(e_x,x).
\]

`EnterConjecture` includes original construction, reconstruction, adoption, or reactivation of standing content. **Side condition on reactivation.** An `EnterConjecture` event whose provenance marks it as reactivation is well-typed only if the content was already in the system's repertoire \(R_s(t')\) or `Retained` at some \(t'\) before the event, with a provenance link to that earlier state. Without this condition the invariant is vacuous, because a reactivation event could be inserted before any criticism at no cost.

## 4. Attention, recognition, and values

A tension or inadequacy in the world does not automatically constitute an active problem for a system.

Let \(\tau\) be a candidate tension, \(r_{\mathrm{org}}\) a recognition organisation, and \(v\) a value or priority organisation. A problem-opening event requires witnesses for all of the following:

\[
\mathsf{OpenProblem}(e,s,p,\tau,r_{\mathrm{org}},v)
\iff
\mathsf{Attend}_s(e,\tau)
\land
\mathsf{Recognises}_s(r_{\mathrm{org}},\tau,p)
\land
\mathsf{Matters}_s(v,\tau,p)
\land
\mathsf{Represents}_s(p).
\]

`Matters` is a relation, not necessarily a scalar threshold. Recognition and values are themselves revisable contents.

The value organisation \(v\) directs resources. It is knowledge in the constructor-theoretic sense — causally active, resilient information — without being explanatory content. The kernel treats it as a **cause** of attention events and of cuts. It never requires that cause to be represented as a reason, to be explanatory, or to lie inside the system boundary. Removing recognition or values makes the theory unable to explain why one anomaly becomes a problem while surrounding noise does not; requiring them to be explanatory would demand that the system fabricate reasons it does not have.

## 5. Spans and cuts

### 5.1 Spans

A **span** (the original proposal's "episode") is a causally connected subgraph of a run rooted in one or more attention events:

\[
q=\langle Root_q,\;Events_q\rangle .
\]

There is no closing event. Span membership is not exclusive. The span's extent at a run \(r\) is \(q \cap r\).

A merge records, by a `Merge` event, that one span's subsequent events are absorbed into another. The absorbed span is not closed; it simply has no events of its own after the merge.

### 5.2 Cut versions

For content \(x\), span \(q\), and run \(r\), the **cut versions** of \(x\) are the \(\preceq\)-maximal members of \(x\)'s lineage within \(q \cap r\):

\[
\mathsf{cut}(x,q,r)
=
\{\,y \in \mathrm{lineage}(x) \cap q \cap r \;:\; \nexists z \in \mathrm{lineage}(x)\cap q\cap r,\; y \prec z\,\}.
\]

This set is usually a singleton. Concurrency can make it larger. Any certificate that refers to "the" cut version names one member. Nothing about a cut version implies completion: it is the version that was current when observation stopped, and a cut can fall anywhere, including in the middle of a response.

### 5.3 Disposition at a cut

The **disposition** of \(x\) in \(q\) at \(r\) is derived: it is the kind of the \(\preceq\)-latest `Respond` event in \(q \cap r\) whose target is in \(x\)'s lineage, or `undecided` if there is none.

The disposition is reported alongside every classification. It is never a precondition for one. `Respond` kinds include *suspend* and *deliberately ignore*; those are stances toward a criticism, recorded as events, and are content-bearing. They are not the stop.

### 5.4 Lapse cause

When a span's activity ceases at a cut, the application dossier may record a **lapse cause**:

```text
chosen        a later Attend in r lies outside q (derivable from the run)
interrupted   the run ended by a cause outside the system
exhausted     a declared resource bound was reached
unknown
```

Only `chosen` is derivable from the kernel. The others are dossier facts. `unknown` is legitimate and expected to be common. A lapse cause may carry provenance. It is never a reason, never required to be explanatory, and never required at all. A session that ends by external wipe has a lapse cause of `interrupted` and involved no decision by anyone.

### 5.5 Reopening

A later `Attend` whose provenance links target content from an earlier span opens a new span linked to the old one. The old span's history is unaltered. A criticism in the new span of a conjecture entered in the old one satisfies the conjecture-before-criticism invariant directly, because the earlier `EnterConjecture` is already in the run.

### 5.6 What the cut does and does not bear on

The cut bears on two things: **availability**, because a version not committed before the cut is not `Retained` at that cut; and **process classification**, because whether a criticism received a reason-specific response within \(q \cap r\) is a fact about \(q \cap r\). It bears on nothing else. In particular it does not alter any content version, does not confer or remove any status on a theory, and does not require the system to know, represent, or explain why it stopped.

## 6. Explanation objects

CR-1.0's bare `Explains(x,p,b)` is replaced by an explicit representation contract.

An explanatory candidate is represented as

\[
X=\langle O_X,C_X,\Lambda_X,S_X,A_X\rangle ,
\]

where \(O_X\) is a set of explanatory obligations, \(C_X\) is a set of commitments, \(\Lambda_X\) is a typed hypergraph of explanatory links, \(S_X\) is declared scope, and \(A_X\) is the set of background assumptions or auxiliaries used.

Possible link roles include causal, constitutive, mechanistic, constraint, reason, realization, derivational, and counterfactual roles. A domain profile need not use every role and may add others.

A mechanically checkable predicate \(\mathsf{WellFormed}_{\mathcal D}(X)\) may require that every obligation is connected to at least one declared explanatory route, that every material commitment participates in a route or is marked auxiliary, and that all links are well typed. This is structural well-formedness only.

\[
\mathsf{ExpCandidate}_{\mathcal D}(X,p,b)
\iff
\mathsf{WellFormed}_{\mathcal D}(X)
\land
\mathsf{Job}_{\mathcal D}(X,p,b).
\]

Actual adequacy is represented by positive and negative certificate types. The formalism therefore distinguishes:

```text
well-formed explanatory proposal
supported adequate explanation
refuted explanation
unresolved explanatory proposal
```

A prediction oracle can have accurate outputs while lacking an explanatory-commitment graph. A myth can be a well-formed explanatory proposal while receiving poor adequacy and hard-to-vary judgments. The distinction is no longer hidden in one uninterpreted Boolean.

## 7. Evidence states and satisfaction at a cut

### 7.1 Ledger

For any claim \(\phi\), the model maintains separate sets of supporting and refuting certificates:

\[
\mathcal J(\phi)=\langle W^+_\phi,W^-_\phi\rangle .
\]

| Positive certificates | Negative certificates | Status |
|---:|---:|---|
| none | none | `OPEN` |
| one or more | none | `SUPPORTED` |
| none | one or more | `REFUTED` |
| one or more | one or more | `CONTESTED` |

These are evidence states, not truth values. A policy may determine which certificates are currently admissible, but the policy and its consequences remain explicit. Contradictory evidence does not license arbitrary conclusions. Missing evidence never becomes Boolean false.

### 7.2 Satisfaction at a cut

A CR-2.0 model over a domain profile is

\[
\mathcal M = \langle \mathcal D,\; \mathcal E_{\mathcal D},\; \mathcal J,\; \mathcal A \rangle ,
\]

where \(\mathcal A\) is the application dossier. The satisfaction relation assigns each claim a status at a run:

\[
\mathrm{status}_{\mathcal M}(\phi, r) \in \{\mathtt{OPEN},\mathtt{SUPPORTED},\mathtt{REFUTED},\mathtt{CONTESTED}\}.
\]

This is the relation that CR-1.0's `M,h,t ⊨ φ` becomes. It is four-valued because attribution is made from a finite prefix, and whether a certificate will ever appear is in general undecidable. "Not yet in the prefix" is the honest verdict and the only one computation licenses.

### 7.3 Two classes of claim

**Prefix facts.** A claim of the form "an event of kind \(k\) with witness \(w\) occurs in \(r\)" is a prefix fact. Prefix facts are **monotone**: if supported at \(r\), supported at every \(r' \supseteq r\). The kernel must prove this for every fact-shaped predicate it defines.

**Statuses.** A claim whose witnesses are certificates — adequacy, origin, reason-use, correction, newness — is a status. Statuses are **not monotone**. A later negative witness can move a claim from `SUPPORTED` to `CONTESTED`. The kernel must not attempt to make them monotone; their revisability is the formal shape of fallibilism.

**Compound claims.** A claim defined as a conjunction of components has a positive witness exactly when every component has one, and a negative witness exactly when any component has one. This is the conjunction of Belnap's four-valued logic, and the kernel should state it as such rather than rediscover it.

### 7.4 Negative witnesses by exhaustive inspection

Absence of a certificate is never a negative witness. Absence of an **event** in a finite run can be, under one condition: the application dossier declares that the record is complete for that event kind over that span. Under a **complete-record declaration**, "no `Criticize` event targets \(x\)'s lineage in \(q \cap r\)" is a negative witness for span-indexed claims that require one, valid relative to \(r\) only. Without the declaration, absence yields `OPEN`.

This is what allows a span-indexed claim to be refuted at a cut while capacity claims (§13.4) cannot be: the span is finite and inspectable; the extension structure is not.

## 8. Criticism and reason-specific response

A criticism is a structured content object

\[
c=\langle target,\delta,k,reason,discriminator\rangle ,
\]

where \(\delta\) is the alleged defect, \(k\) is the criticisable standard, and `discriminator` states what evidence, contrast, argument, or intervention would bear on the allegation. The `reason` here is content: it is the reason *in* the criticism, and it is the only sense of "reason" the kernel requires.

A criticism is itself conjectural content and may be criticized.

A response record is

\[
\sigma=\langle kind,c,target,outputs,reasonUse\rangle .
\]

The response kind may revise or reject the target, retain it for stated reasons, reject the criticism, request evidence, reframe or restandardise, suspend, or deliberately ignore the criticism. Suspend and ignore are stances toward the criticism; they are recorded as `Respond` events and are distinct from a cut.

Reason-specific uptake is supported by a `ReasonUseCertificate`, not by temporal succession or a changed output alone. The default empirical certificate family asks whether content-preserving paraphrases preserve the response, defect-changing interventions redirect the response in defect-appropriate ways, irrelevant negative signals fail to produce the same repair, and invalid criticisms can be reasonedly rejected.

This family is a proposed measurement theory, not a definition of all inexplicit reasoning. Where tacit cognition cannot yet be discriminated under interventions, the correct status is `OPEN`, not `REFUTED`.

## 9. Derived lineage

Critical lineage is not a primitive relation.

Let `parent(x,y)` mean that \(y\) is a declared revision, reconstruction, rejection-result, reframing-result, or retained successor of \(x\). Event edges record which criticism and response produced that relation.

\[
\mathsf{Desc}(x,y)
\iff
\text{there is a role-preserving path from }x\text{ to }y.
\]

A lineage witness contains the actual path, all event identifiers, the criticism and response edges, and any span crossings. Lineages have no last member. The kernel must not define or quantify over "the endpoint of a lineage"; the only bounded notion is the cut version of §5.2.

## 10. Correction certificates

The global primitive `K_E` is replaced, for span-level knowledge creation, by an inspectable correction certificate.

A correction certificate is

\[
\kappa=
\langle
q,r,p,x_0,\delta,c,k,\sigma,x_1,
w_{\mathrm{address}},
w_{\mathrm{preserve}},
\Delta p,\Delta k,U
\rangle .
\]

It is valid relative to domain profile \(\mathcal D\) only when:

| Obligation | Required evidence |
|---|---|
| Starting defect | The starting problem situation represents defect \(\delta\) in \(x_0\) |
| Criticism | \(c\) alleges \(\delta\) under criticisable standard \(k\) |
| Causal response | \(\sigma\) is linked to \(c\) by an accepted reason-use certificate |
| Addressing | \(x_1\) has positive evidence for addressing \(\delta\) |
| Preservation | Named merits or commitments of \(x_0\) are preserved, or losses are disclosed |
| Frame changes | Any change to problem or standard is explicit in \(\Delta p,\Delta k\) |
| Residue | Remaining and newly opened problems are recorded in \(U\) |
| Cut | \(x_1 \in \mathsf{cut}(x_0,q,r)\): the version current at the cut in the same lineage, not an unrelated retained result |

Define local explanatory correction by:

\[
K^{corr}_{\mathcal D}(x,p,q,r)
\iff
\exists \kappa\;
\mathsf{ValidCorrection}_{\mathcal D}(\kappa)
\land x = x_1(\kappa).
\]

Its value is a status, not a Boolean. It is fallible and revisable. It does not entail truth. It improves on a primitive `K_E` because every positive attribution must expose the defect, reason, response, preservation claim, changed standard, and residual problem. Some domain judgments remain imported, but they are now local and inspectable rather than hidden in one atom.

## 11. Newness

Newness is relative to a declared repertoire snapshot and equivalence level:

\[
\mathsf{New}_{s,\ell,R}(x,r)
\iff
\nexists y\in R_s(r)\; y\equiv_\ell x .
\]

The repertoire \(R_s(r)\), system boundary, audit scope, and equivalence level are mandatory, and the snapshot is taken at a run, not at an abstract time. A real application may support or refute newness only to the extent that its repertoire audit warrants. Historical novelty is a separate claim:

\[
\mathsf{NewHistory}_{\ell,H}(x,r).
\]

Creative reconstruction can satisfy system-relative newness and authorship while failing historical novelty.

## 12. Authorship and reconstruction

Authorship becomes a certificate-backed causal attribution rather than an unexplained predicate.

An `OriginCertificate` contains:

```text
predeclared boundary
provenance graph and declared channels
problem-specific organisation extracted from the candidate
internal construction or reconstruction path
matched interventions on that path
external stores, prompts, tools, evaluators and selectors
alternative provenance explanations
scope and equivalence level
positive and negative evidence
```

A positive certificate must support the claim that operations inside the boundary made a problem-specific causal difference to the organisation that lets the system deploy the candidate across declared contrasts. It must also show that a complete deployable organisation was not merely transferred across the boundary and emitted unchanged.

Prior knowledge, training, communication, search, imitation, deduction, and randomness are not automatic disqualifiers. The relevant question is where the problem-specific organisation was constructed or reconstructed. A communicated explanation may underdetermine its usable meaning and be creatively reconstructed. A stored answer that is merely emitted may fail authorship.

The certificate may remain contested. CR-2.0 does not claim a universally decidable quantitative theory of causal credit.

## 13. Creativity classifications

Every classification is indexed by a run \(r\) (the cut) and takes an evidence status as its value, computed by §7.3 from the statuses of its components. Let \(q\) be a span, \(\beta\) its predeclared boundary, and \(\ell\) its content-equivalence level.

### 13.1 Originative creative act

\[
\begin{aligned}
\mathsf{OCA}_{\mathcal D,\beta}(s,x,p,q,r)
\iff\;&
\mathsf{RootAttention}(q,p)\in r\\
&\land \mathsf{EnterConjecture}(x,p,q)\in r\\
&\land \mathsf{New}_{s,\ell,R}(x,r)\\
&\land \exists o\;\mathsf{ValidOrigin}(o,s,x,p,\beta).
\end{aligned}
\]

The first two conjuncts are prefix facts; the last two are statuses. No criticism, success, truth, retention, generality, or historical firstness is included.

### 13.2 Critical creative process

\[
\begin{aligned}
\mathsf{CCP}_{\mathcal D,\beta}(s,q,r)
\iff \exists x_0,x_1,c,\sigma\;&
\mathsf{OCA}(s,x_0,p,q,r)\\
&\land \mathsf{Desc}(x_0,x_1)\\
&\land \mathsf{Criticize}(c,x_1,p,q)\in r\\
&\land \exists u\;\mathsf{ValidReasonUse}(u,\sigma,c),
\end{aligned}
\]

with all named events in \(q \cap r\). There is no closure conjunct. The disposition at the cut (§5.3) is reported with the classification and may be `undecided`. A CCP can end worse than it began, and the cut can fall before any disposition exists.

### 13.3 Explanatory knowledge creation

\[
\mathsf{EKC}_{\mathcal D,\beta}(s,x,q,r)
\iff
\mathsf{CCP}_{\mathcal D,\beta}(s,q,r)
\land
K^{corr}_{\mathcal D}(x,p,q,r)
\land
\mathsf{Retained}(s,x,r),
\]

where \(x\) is the cut version named by the correction certificate. Retention is availability at the cut — a token or reconstructible disposition accessible to a later operation — not endorsement.

### 13.4 Capacity and general disposition

A bounded capacity profile is a property of the event space's **extension structure**, not of any run. Over a declared problem class \(Q\), perturbation family \(\Gamma\), enabling envelope \(\chi\), and stable organisation \(\Omega\):

\[
\mathsf{BCap}(s,Q,\Gamma,\chi,\Omega)
\]

holds only if, from every configuration in the admitted region, for every explicitly admitted problem in \(Q\) and perturbation in \(\Gamma\), there exists an extension containing the required continuation pattern supported by the same organisation \(\Omega\).

Finite runs contribute to its ledger in both directions: an observed continuation under matched conditions is a positive witness for that member of \(Q \times \Gamma\); an observed failure under matched conditions is a negative witness. Neither settles the claim over the whole class. Totality guarantees that some extension always exists; it does not guarantee that the required one does.

A general creative disposition adds problem formation, conjecture, criticism, revision, and problem or standard transformation across a declared nontrivial \(Q\). Finite experiments can support or refute a bounded profile; they do not prove an unrestricted modal claim.

`UED` should not remain in the executable core. It belongs in a separate universality-conjecture module because its no-domain-bar clause cannot be discharged by finite evidence and is partly source-conjectural.

## 14. Hard to vary

"Hard to vary" becomes exact only relative to a declared variation family.

For candidates \(X,X'\):

\[
\begin{aligned}
\mathsf{FreeVariant}^{\mathcal D}_V(X,X')
\iff\;&
\mathsf{MaterialVariant}_V(X,X')\\
&\land \mathsf{SameJob}_{\mathcal D}(X,X')\\
&\land \mathsf{AdeqNow}^{+}_{\mathcal D}(X')\\
&\land \neg\mathsf{AdditionalRepair}(X,X').
\end{aligned}
\]

Then:

\[
\mathsf{HTV}^{\mathcal D}_V(X)
\iff
\forall X'\in V(X),\;
\mathsf{MaterialVariant}_V(X,X')
\Rightarrow
\neg\mathsf{FreeVariant}^{\mathcal D}_V(X,X').
\]

This is a checked result only for the declared family \(V\). It is not a scalar creativity score, a truth certificate, or proof that no unimagined free variant exists. A hard-to-vary candidate is one on which a criticism can bind; add empirical content and it is testable. Neither property replaces the other.

## 15. Reach

A reach witness transports an unchanged explanatory commitment subgraph into a new problem/background pair:

\[
\mathsf{ReachWitness}_{\mathcal D}(X,p',b').
\]

The witness identifies which commitments remain unchanged, which background facts are added, and which new obligations are discharged. If problem-specific commitments must be invented, that is additional explanatory work rather than pure reach.

Reach may be unknown to the author. Wide reach remains relative to a declared coverage condition.

## 16. Physical realization

The physical module uses a family of maps rather than one post-hoc label:

\[
\rho_C:\text{physical attributes}\to C,\qquad
\rho_E:\text{physical events}\to E,\qquad
\rho_I:\text{physical interventions}\to\text{semantic interventions}.
\]

A realization claim requires commuting obligations showing that these maps preserve:

```text
event occurrence and causal order
content distinctions and declared equivalence
span and lineage edges
provenance and boundary crossings
reason-specific intervention effects
memory and reconstructibility
resources, tolerances, noise and repair
extension structure: the retained capacity to continue
the exact predicate being attributed
```

The new obligation is the constructor-theoretic one. A constructor is characterised by retaining the ability to cause a task again; a task has an output, a constructor does not finish. Task is step, constructor is process. A physical system realizes the kernel's totality only if its retained capacity to produce a further event is preserved by \(\rho_E\) across the declared intervention family. A realization map that carries a halting machine onto the kernel fails this obligation.

Constructor theory can supply task possibility, information variables, composition, repeatability, error correction, and physical resources. It does not supply explanatory meaning, problem identity, criticism, authorship, or correction certificates.

The physical module begins only after the abstract event and evidence kernel passes its fixtures.

## 17. Immediate consequences

Each consequence has two forms. A **weak separation** exhibits a run at which the antecedent is `SUPPORTED` and the consequent is `OPEN`. A **strong separation** exhibits a run at which the consequent is `REFUTED`, which requires a negative witness: either a domain refutation certificate or an exhaustive-inspection witness under a complete-record declaration. The table states which form each consequence can reach in the first slice.

| Claim | Witness | Form reachable |
|---|---|---|
| OCA does not entail CCP | A new authored false conjecture; no `Criticize` event in the span under complete record | Strong |
| CCP does not entail EKC | A reason-responsive revision whose correction certificate fails the addressing obligation | Strong (refutation certificate) or weak (no certificate offered) |
| EKC does not entail a general disposition | One corrected retained span; no observed continuation on any other member of \(Q\) | Weak only: capacity claims admit no exhaustive-inspection witness |
| Prediction does not entail explanation | A perfect oracle with no commitment graph: `WellFormed` fails structurally | Strong |
| New output does not entail authorship | A lookup emitter with a transferred-organisation negative origin witness | Strong |
| Revision frequency does not entail uptake | A generic negative-token follower failing the paraphrase and irrelevant-signal contrasts | Strong |
| Retention does not entail correction | A retained error with no correction certificate | Weak; strong if a refutation certificate for addressing exists |
| Finite behaviour does not entail authorship | Trace-equivalent lookup and reconstructive provenance models | Underdetermination: both models agree on every prefix fact; origin status is `SUPPORTED` in one and `REFUTED` in the other, so the trace alone leaves it `OPEN` |
| Finite runs do not entail generality | Trace-equivalent bounded and stable-extension event spaces | Underdetermination, by construction: no run distinguishes them, and no exhaustive-inspection witness exists for the extension structure |
| Natural selection does not entail explanatory creativity | Variation and differential replication without attention, represented problems, conjectures, or reasons | Strong |
| Universal computation does not entail creativity | A universal interpreter executing a constant or lookup program | Strong |
| Correction does not entail final truth | A later criticism defeats an earlier valid correction certificate | Strong: the status moves to `CONTESTED` at the later cut |
| No state is terminal | Totality (§3.3) | Theorem, not separation |
| Prefix facts are monotone | Every fact-shaped predicate is preserved under run extension | Theorem, not separation |
| The cut is inert for content | No content version differs between two runs that differ only in where the cut falls | Theorem, not separation |

Every theorem must cite the exact structural definitions, domain imports, complete-record declarations, and evidence policy it uses. A consequence claimed in strong form without a named negative witness is ill-typed.

## 18. Deletion tests

Each major component is load-bearing.

| Delete | Resulting collapse |
|---|---|
| Attention | Every detectable discrepancy becomes an active problem |
| Recognition | The system need not understand that an inconsistency occurred |
| Values | There is no account of why one anomaly matters and surrounding noise does not |
| Conjecture-before-criticism with the reactivation side condition | Criticism can appear without a target idea, or a target can be inserted for free |
| Partial-order event space | Overlap, opportunistic backtracking, and shared subproblems are forced into a false linear cycle |
| Totality | A configuration with no extension exists; the kernel has a terminus and theories can "complete" |
| Cut as observation index rather than event | Stops become events in the process and can be made to bear on content or status |
| Complete-record declaration | Absence of an event refutes a claim without warrant, or can never refute one |
| Prefix-fact / status distinction | Either every attribution is revisable, so no fact about the past is stable, or no attribution is revisable, so fallibilism is lost |
| Evidence states | Missing information becomes false or contradictory evidence explodes |
| Explanation graph | Prediction, output fit, and explanation can collapse |
| Provenance certificate | Retrieval and designer-supplied adaptation can count as authorship |
| Reason-use certificate | Generic compliance can count as criticism uptake |
| Correction certificate | Retained change can count as knowledge creation |
| Cut obligation on correction certificates | An unrelated retained result can receive the correction |
| Declared variant family | Hard-to-vary becomes an unfalsifiable slogan |
| Declared repertoire and equivalence | Newness becomes boundary-gameable |
| Capacity as a property of the extension structure | Finite performance becomes a proof of generality |
| Realization commuting obligations, including retained capacity | Any physical trace can be re-labelled after the fact, and a halting machine can realize a non-terminating process |

A component that changes no theorem, countermodel, fixture, or admissible model distinction should be removed or moved to an optional application module.

## 19. Worked fixture — explanations of seasons

This fixture should be completed before any AGI or physical-realization claim.

Let \(X_P\) be the Persephone explanation and \(X_A\) the axial-tilt explanation. Both are explanatory proposals because each purports to answer why seasons occur. They differ in structure and criticism.

| Event | Content and role | Causal purpose |
|---|---|---|
| \(e_0\) | Enter standing conjecture \(X_P\) (reactivation, with provenance to a prior repertoire) | Gives later criticism a prior target and satisfies the side condition |
| \(e_1\) | Attend to the conflict between \(X_P\) and out-of-phase hemispheric seasons | Opens problem \(p\) under recognition and values |
| \(e_2\) | Enter conjecture \(X_A\) | Proposes tilt, orbit, sunlight incidence, and rotational orientation |
| \(e_3\) | Criticize \(X_P\) | Alleged defect: its story has no constrained mechanism for opposite hemispheric phases |
| \(e_4\) | Interpret evidence | Connects observations and instruments to the phase discriminator |
| \(e_5\) | Criticize \(X_A\) with independent geometry and heating constraints | Tests whether its links survive rather than merely fitting the data |
| \(e_6\) | Respond: reject \(X_P\), retain \(X_A\), record remaining orbital and climatic problems | Reason-specific response; the disposition at any later cut derives from this event |
| \(e_7\) | Retain \(X_A\) | Makes the corrected organisation available |
| — | **Cut** \(r_1 = \{e_0,\dots,e_7\}\); lapse cause `chosen` if the run continues with an `Attend` elsewhere, otherwise `unknown` | Observation stops. Nothing is completed. |

The commitment graph of \(X_P\) contains Demeter, sadness, a marriage contract, and a magic seed. A declared variant family can substitute other gods, motives, schedules, or magic while preserving the same familiar observations without additional explanatory repair. It therefore contains free variants. The Persephone story is testable — it predicts simultaneous seasons everywhere — and is refuted by the southern hemisphere; what makes it a bad explanation is not that it fails the test but that its believers can vary it to survive one.

The graph of \(X_A\) links axial tilt, orbital position, solar radiation, surface angle, and rotational stability. Replacing the Sun with the Moon, removing the tilt, or holding both hemispheres identically oriented breaks independently constrained links. Repairs require new explanatory work. Relative to that declared family, \(X_A\) is harder to vary, and because it has empirical content it is also testable.

At \(r_1\): a valid correction certificate identifies the phase defect, the criticism \(e_3\), the reason-specific response \(e_6\), the preserved annual regularity, the additional reach to tropics and polar regions, and the residual problems; its cut version is \(X_A\) as retained at \(e_7\). The span can have OCA, CCP, and EKC `SUPPORTED` at \(r_1\) if newness and origin certificates are supplied. It does not establish a general disposition.

Two further cuts test the shape:

- \(r_0 = \{e_0,\dots,e_5\}\), before the response. OCA `SUPPORTED` (given the same newness and origin certificates); CCP `OPEN` (a criticism exists, no reason-use certificate yet); disposition `undecided`; correction certificate cannot be issued because no cut version satisfies the addressing obligation. Nothing is false. Extending to \(r_1\) changes only statuses, never facts.
- \(r_2 \supset r_1\) containing a new span whose criticism \(e_9\) alleges that \(X_A\) mispredicts the timing of extreme temperatures. The \(r_1\) correction certificate remains a positive witness; \(e_9\) supplies a negative one; \(K^{corr}\) for \(X_A\) is `CONTESTED` at \(r_2\). The content of \(X_A\) at \(e_7\) is unchanged.

A second span about planetary geometry may share \(X_A\), \(e_4\), or later consequences. That overlap is represented directly rather than by duplicating the content into disjoint linear episodes.

## 20. Construction process

The formalisation should proceed through small versioned semantic commitments rather than one whole-report translation.

| Branch or tag | Active question | Pass condition |
|---|---|---|
| `authority/cr1-frozen` | Preserve CR-1.0 and accepted EIB artefacts | Hashes and source anchors reproduce |
| `cr2/0.1-transition-kernel` | Can attention, conjecture, criticism, response, overlap, merge, reopening, runs, and cuts be represented over a total event space? | Totality proven; monotonicity of every prefix fact proven; a status non-monotonicity fixture passes; the seasons fixture at \(r_0,r_1,r_2\) classifies as §19; concurrency and ill-typed fixtures pass; no `Decide` kind exists |
| `cr2/0.2-explanation-profile` | Can the seasons rivals be represented without a primitive `Explains` Boolean? | Oracle, myth, and axial-tilt contrasts classify correctly |
| `cr2/0.3-correction` | Can local explanatory improvement be witnessed at a cut without equating it with truth or retention? | Valid, invalid, contested, and later-defeated corrections pass; no reference to a lineage endpoint compiles |
| `cr2/0.4-provenance` | Can lookup, communication, reconstruction, and designer-supplied adaptation be distinguished? | Trace-equivalent provenance countermodels pass |
| `cr2/0.5-capacity` | Can bounded modal profiles be stated over the extension structure without inferring them from finite runs? | Paired-extension countermodels pass; capacity claims never reach `REFUTED` by inspection alone |
| `cr2/0.6-physical` | Can one realization mapping preserve the semantic structure, including retained capacity, across interventions? | Deleting any required commuting obligation blocks attribution; a halting-machine realization is rejected |
| `cr2/0.7-domain-adapters` | Can science, mathematics, art, and institutions share the kernel without sharing success predicates? | Conservative extension and domain-specific fixtures pass |

Every accepted tag becomes a real harness mutation. The harness compares the classifications, proof obligations, and countermodels across actual versions.

### Verification shape

In Lean the kernel needs no native coinduction. Model the event space as a type with the causal and conflict relations, configurations as a predicate on finite sets, and extension as a relation on configurations. Totality is a theorem about that relation. Invariants over reachable configurations are proved by induction on the derivation of reachability, which is finite even though runs are not bounded. Fixtures are safety properties (every reachable configuration satisfies this) and, where wanted, eventuality properties under declared fairness assumptions. No fixture may be phrased as "the run returns \(v\)". A harness's output is a ledger snapshot at a cut with a lapse cause recorded, never a result.

## 21. Model-orchestration protocol

A single long-running language-model context should not both invent a formalisation and certify it. Use four fresh-context roles, even when the same underlying model fills them.

| Role | Output |
|---|---|
| Source extractor | Literal source span, claim status, dependencies, and admitted gap |
| Rival formaliser | At least two materially different formal readings |
| Countermodel builder | Small positive, negative, and underdetermined configurations, each evaluated at a named cut |
| Adjudicator | Chooses, rejects, or suspends based on the fixtures and project authority |

Each iteration handles one semantic question. No reading is accepted merely because it is elegant or implementable. No primitive enters the core without a witness schema. No theorem is attempted before at least one positive and one negative fixture exist. An unresolved choice is recorded and blocks only its dependants. The adjudicator records at a cut; no run is required to finish, and the adjudicator's own stopping is a lapse with a cause, not a verdict on the matter.

Lean should check the closed event, witness, dependency, and theorem structures. SMT or finite model finding should search for typed countermodels. Neither tool should decide prose meaning or source fidelity.

## 22. First implementation slice

The first slice should contain only:

```text
DomainProfile interface
ContentVersion
EvidenceState and the compound-claim rule
Event space with causal order, conflict, configurations, runs, cuts
Totality axiom and its proof obligation
attention/recognition/value records
overlapping Span, cut version, derived disposition
lapse cause as a dossier field
complete-record declaration
ExplanationObject
Criticism and Response
derived lineage
Newness relative to repertoire and equivalence at a run
OriginCertificate interface
ReasonUseCertificate interface
CorrectionCertificate with the cut obligation
OCA, CCP and EKC as status-valued claims at a cut
seasons fixture at three cuts
oracle, lookup, generic-feedback, retained-error, failed-revision and later-defeated-correction countermodels
```

It should exclude:

```text
Decide or any closing event kind
lineage endpoints
GCD and UED proofs
AGI and personhood
artistic universality
natural-selection physical knowledge
constructor-theory realization
real-system classification
global decision procedures for explanation or authorship
```

The slice passes only when every field is used by a fixture or theorem, every missing certificate yields `OPEN`, every contradictory evidence pair yields `CONTESTED`, every prefix fact is proven monotone, totality is proven, and deleting a load-bearing field changes a declared result.

## 23. What can be reused

CR-EIB's strongest work should be retained:

```text
immutable source anchors
separation of source marks from DEF/IMP/DER
typed declaration records
proof and countermodel replay
bounded-search honesty
conservative-extension checks
schema and artefact hashes
semantic mutation testing
```

What should stop driving the theory is the attempt to map all 110 declarations before the central semantic choices have discriminating models. CR-EIB becomes the assurance layer downstream of accepted CR-2.0 versions, not the engine that discovers the missing semantics.

## 24. Falsification points

CR-2.0 should be revised if any of the following is shown.

| Conjecture | Revision trigger |
|---|---|
| Event-space configurations adequately represent creative histories | A clear case requires non-event or non-causal organisation that cannot be conservatively encoded |
| Attention, recognition, and values are jointly required for problem opening | A valid counterexample opens a problem without any corresponding role |
| Conjecture globally precedes criticism, with the reactivation side condition | A genuine criticism has no prior target conjecture even as retained or repertoire content, or the side condition excludes a genuine reactivation |
| Totality: no configuration is terminal | A defensible creative history requires a state from which no admissible event is possible |
| The cut is inert for content | A defensible case in which the stop itself, rather than a response event, alters what a content version is |
| Stops need no reason | A defensible case in which a classification cannot be made correctly without the system's reason for stopping |
| Prefix facts and statuses are the right two classes | A claim that must be both monotone and revisable, or neither |
| Explanation graphs preserve the relevant distinctions | A good explanation cannot be represented without distorting its explanatory role |
| Reason-use interventions distinguish uptake from compliance | A robust class of reason-responsive systems systematically fails every admissible contrast |
| Correction certificates improve on primitive `K_E` | The certificates merely relocate the same circular judgment without adding discriminating constraints |
| Provenance certificates support authorship attribution | Trace and intervention evidence cannot distinguish reconstruction from transferred deployment even in principle |
| UED belongs outside the executable core | A finite, non-question-begging criterion for unrestricted universality is supplied |
| Constructor theory belongs only in realization | A completed constructor-theoretic semantics derives problem, meaning, criticism, and explanatory correction without equivalent semantic imports |

## 25. Source map

The source-facing motivation is concentrated in the following supplied locations.

| Topic | Supplied source location |
|---|---|
| Explanation is not prediction; precise definition remains difficult | *The Fabric of Reality*, supplied PDF pp. 14–25 |
| Problem-led conjecture, criticism, replacement, and new problems | *The Fabric of Reality*, supplied PDF pp. 74–83 |
| Backtracking and simultaneously active subproblems | *The Fabric of Reality*, supplied PDF pp. 79–80 |
| Knowledge cannot appear authorless; physical creative criterion remained open | *The Fabric of Reality*, supplied PDF pp. 327–329 |
| Theories are created as conjectures, not derived from observation | *The Beginning of Infinity*, supplied PDF pp. 15–20 |
| Hard-to-vary explanations, testability as necessary but insufficient, and reach | *The Beginning of Infinity*, supplied PDF pp. 30–40 |
| Behaviour does not settle where adapted knowledge originated | *The Beginning of Infinity*, supplied PDF pp. 166–168 |
| Creativity reconstructs meanings rather than copying behaviour | *The Beginning of Infinity*, supplied PDF pp. 413–423 |
| Creativity is software-level but its mechanism is unknown | *The Beginning of Infinity*, supplied PDF pp. 425–427 |
| Constructor as retained capacity; task as transformation with output | CR-1.0 constructor-theory dossier, PDF pp. 117–141 |
| CR-1.0's typed model and explicit non-derivability boundary | CR-1.0 PDF pp. 215–234 |
| Application gaming and unresolved primitives | CR-1.0 PDF pp. 278–283 |
| Current bridge remains mapping-unreviewed and conformance-blocked | CR-EIB-0.2 |

The source status of the process shape itself is `model_conjecture`. Neither Deutsch nor Marletto states that creative histories are configurations of a total event structure. What the sources supply is the denial of any terminus for explanatory knowledge and the characterisation of a constructor by retained capacity; the event-structure encoding of those two commitments is this document's reconstruction.

## Final criterion

The replacement succeeds when it does not merely translate words into predicates. It must make each disputed attribution answerable by a finite object at a cut: an event path, explanation graph, origin certificate, reason-use certificate, correction certificate, countermodel, or explicit unresolved evidence state.

It fails if `Explains`, `creative`, `understands`, `authored`, `improved`, or `general` reappear as unexplained Boolean labels hidden behind a cleaner type signature. It also fails if any configuration of the kernel has no extension, if any certificate names the endpoint of a lineage, or if any classification requires the system to say why it stopped.

## Change register

Each entry is `origin: model_conjecture`, status **proposed**. Adoption requires a human act per entry. "Reverts if" names the observation that would undo the change.

| # | Change | Reason | Reverts if |
|---|---|---|---|
| 1 | `Decide` removed from event kinds; `Suspend`/`MoveOn` duality removed | It packaged a stop marker and a stance summary into one event, importing a terminus; the stance is already carried by `Respond` | A stance is found that no `Respond` kind can carry and that must be an event |
| 2 | Episodes become spans with no closing event; extent is span ∩ run | Theories do not close; attention lapses; overlap and reopening were already non-exclusive | A case requires an episode to have an intrinsic end independent of observation |
| 3 | Cut introduced as an observation index, not an event | Stops are facts about the record and resource allocation, inert for content | A case in which the stop itself alters content (falsification point above) |
| 4 | Lapse cause as optional dossier field with `unknown` legitimate | Requiring a reason for stopping is an artifact requirement and invites fabrication; causes are often external or unrepresented (values, budget, session wipe) | A classification is shown to depend on the system's reason for stopping |
| 5 | Certificate endpoint replaced by cut version; lineage endpoints forbidden | "Endpoint" presupposes lineages terminate | A theorem is found that needs a global lineage endpoint and cannot be restated at a cut |
| 6 | Totality axiom and deletion test | Formal statement of "no theory has closure"; separates step (terminates) from process (does not) | A defensible history requires a terminal state |
| 7 | Satisfaction relation defined as status at a run; prefix facts vs statuses; Belnap conjunction for compound claims | Resolves the Boolean-over-four-valued mismatch in the original; makes fallibilism the non-monotonicity of statuses | A claim is found that is neither a monotone fact nor a revisable status |
| 8 | Complete-record declaration and exhaustive-inspection negative witnesses | Lets span-indexed claims be refuted at a cut without letting absence of evidence become falsity in general | Complete-record declarations prove unobtainable in every application, leaving only weak separations |
| 9 | Consequences split into weak and strong separations | The original table assumed classical countermodels the evidence semantics cannot deliver | All consequences are shown reachable in strong form without the split |
| 10 | Reactivation side condition on conjecture-before-criticism | Without it the invariant is vacuous | A genuine reactivation is excluded by the condition |
| 11 | Capacity stated over the extension structure, not runs | Modal content lives in what successors exist; finite runs can only witness | A capacity claim is shown decidable from a finite run |
| 12 | Realization must preserve retained capacity to continue | Constructor-theoretic content of totality; excludes halting-machine realizations | A halting realization is shown adequate for a non-terminating kernel |
| 13 | `Reopen` derived from `Attend` with provenance | One fewer primitive; changes no theorem | Reopening is shown to need an event kind distinct from attention |
| 14 | §14 and §19 restate the testability–hard-to-vary relationship | Corrects an earlier misdescription: hard-to-vary is what lets criticism bind; empirical content is what makes it testable; neither displaces the other | Source evidence that Deutsch subordinates hard-to-vary to testability rather than the reverse |
