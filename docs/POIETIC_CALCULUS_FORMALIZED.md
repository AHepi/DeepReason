# The Poietic Calculus, Formalized

## A two-axis, event-log calculus of conjecture, criticism, background, and attention

### Status of this document

This is a mathematical reconstruction and conservative extension of *The Poietic Calculus (𝔓), v0.1*, informed by *A Computable Calculus of Conjecture, Criticism, and Background*. It is not presented as a proof that the epistemology is true. It identifies exactly which claims follow as theorems, which require new definitions, which are controller policies, and which are only computable surrogates for non-effective notions in the original calculus.

The main result is that all thirteen requested phenomena can be represented in one coherent formal system. Seven become theorem-level consequences once the required invariants are stated. Six are not derivable from the original calculus alone and must enter as explicit representational clauses, policies, or estimators.

## 1. Integration boundary

The two source documents are close in intent but not formally identical. A rigorous reconstruction must expose their differences rather than blur them.

| Issue | Poietic v0.1 | Computable background calculus | Resolution adopted here |
|---|---|---|---|
| Refutation | A lone failed test makes a content problematic; comparative succession is required for tentative refutation | A surviving warranted violation can refute unilaterally; rational displacement remains comparative | Reserve **refuted** for attack-graph status and use **superseded** for comparative replacement |
| Support | Status is read from a Dung grounded extension | Grounded attack labels are followed by a dependency-support pass | Treat the support pass as a conservative extension; with an empty dependency graph it reduces to the original statics |
| Hardness to vary | An order on functional slack structures; generally non-effective | A finite sampled score under a variation kernel | Preserve the abstract order and define the score only as an operational estimator |
| Knowledge | Constructor-theoretic resilient information, with a conjectured resilience identity | A computable view combining survival, demarcation, and reach | Distinguish physical knowledge from an attention heuristic that is evidence about knowledge, never a verification predicate |
| Background exit | Not represented as a separate axis | Claimed to have exactly two exits: fall and revocation | This is true only under a frame-decisiveness condition; otherwise ordinary Dung suspension is a third possible exit |
| Wound persistence | Not represented | Claimed to follow from the frame assertion merely mentioning its subject | Mention alone is insufficient in a globally connected Dung graph; a graph-separation invariant is required |
| Orphans after reinstatement | Not represented | Orphan marks persist until adjudicated resolution, while all statuses remain reinstatable | The source leaves the restored-premise case underspecified; the core formalization records the gap explicitly |

The refutation split is the most important repair. Let

\[
\operatorname{Refuted}_L(a)
\]

mean that the current grounded attack semantics defeats artifact \(a\). Let

\[
\operatorname{Superseded}_L(a',a)
\]

mean that \(a'\) comparatively recovers the work of \(a\), is at least as rigid, and avoids immunizing additions. A universal claim can therefore be refuted by one undefeated counterexample while remaining unsuperseded because no better framework yet exists. That distinction is exactly what makes “refuted but still framing” coherent.

## 2. Two levels of the calculus

The formalism has an abstract epistemic level and a finite computable realization.

The abstract level, \(\mathfrak P^{\infty}\), preserves the original open-ended semantics of contents, problems, criticism, reach, and functional hardness to vary. Its genesis relation is not reduced to a search procedure.

The computable level, \(\mathfrak P^{c}\), formalizes the selective and bookkeeping side as a deterministic fold over a finite append-only log. It works over opaque finite encodings, budgeted commitments, attack warrants, dependencies, problem records, frame assertions, reach records, and deterministic render policies.

The relation between them is not identity. \(\mathfrak P^{c}\) is an implementation-level model of the currently registered part of \(\mathfrak P^{\infty}\). In particular, sampled hardness is not the abstract hardness order, and a derived knowledge view is not constructor-theoretic knowledge itself.

## 3. Abstract poietic semantics \(\mathfrak P^{\infty}\)

### 3.1 Growing content signatures

Let \(\mathcal L_0,\mathcal L_1,\ldots\) be a chain of finite or recursively presented signatures such that

\[
\mathcal L_n \subseteq \mathcal L_{n+1}.
\]

A state may register a content whose interpretation requires an extension from \(\mathcal L_n\) to \(\mathcal L_{n+1}\). The meta-level carrier may be finite bytes, but no fixed object-language determines in advance which meanings, roles, mechanisms, or criticism procedures can occur. This separates representational encodability from antecedent closure of the hypothesis space.

### 3.2 Abstract state

An abstract poietic state is

\[
\Sigma=\langle E,\rightsquigarrow,\Lambda,\mathsf{Acc},\mathsf{Prob}\rangle,
\]

where \(E\) is the finite corpus of currently instantiated contents, \(\rightsquigarrow\subseteq E\times E\) is the registered attack relation, \(\Lambda\) is an append-only event history, \(\mathsf{Acc}\subseteq E\times X\) is an attackable accounting relation to explicanda, and \(\mathsf{Prob}\subseteq E\) is the set of contents currently playing the problem-construal role.

No appraisal label is primitive. Every label is a view computed from the state.

### 3.3 Problems and explicanda

A problem is a content

\[
p=\langle \tau,\gamma\rangle,
\]

where \(\tau\subseteq E\) is a tension set and \(\gamma\) is a conjectural account of why the joint standing of \(\tau\) is inadequate. Because \(p\in E\), problem construals can themselves be attacked, replaced, split, or retired.

For \(e\in E\), let

\[
X_\Sigma(e)=\{x:(e,x)\in\mathsf{Acc}\}
\]

be the explicanda that \(e\) is currently registered as accounting for. The relation \((e,x)\in\mathsf{Acc}\) is itself represented by attackable content. Evidence therefore creates or sharpens problems; it does not add positive standing.

### 3.4 Grounded criticism

For \(Y\subseteq E\), define the Dung characteristic operator

\[
F_\Sigma(Y)=\{a\in E:\forall b\,(b\rightsquigarrow a\Rightarrow\exists c\in Y\;c\rightsquigarrow b)\}.
\]

The grounded extension is

\[
G(\Sigma)=\operatorname{lfp}(F_\Sigma).
\]

The basic attack status is

\[
\ell_0(a)=
\begin{cases}
\mathsf U,&a\in G(\Sigma),\\
\mathsf R,&\exists b\in G(\Sigma)\;(b\rightsquigarrow a),\\
\mathsf S,&\text{otherwise.}
\end{cases}
\]

Here \(\mathsf U\) means unrefuted, \(\mathsf R\) means refuted, and \(\mathsf S\) means suspended. None means accepted, verified, probable, or true.

### 3.5 Abstract succession

Let \(e,e'\) play explanatory roles. Define

\[
e'\succeq_\Sigma e
\]

when the following all hold.

**Recovery.** Either \(X_\Sigma(e)\subseteq X_\Sigma(e')\), or there exists an unrefuted account explaining why \(e\) worked over its restricted domain.

**Rigidity.** Relative to shared explicanda, the functional slack structure of \(e'\) embeds into that of \(e\), or a registered and currently unrefuted comparative claim asserts the corresponding relation.

**Non-immunization.** No proper functional component of \(e'\) can be removed while preserving all currently registered accounting and criticism outcomes.

Strict succession is

\[
e'\succ_\Sigma e
\]

when \(e'\succeq_\Sigma e\) and at least one of recovery, criticism survival, or rigidity is strict.

Define

\[
\operatorname{Superseded}_\Sigma(e)
\iff
\exists e'\in G(\Sigma)\;e'\succ_\Sigma e.
\]

This is deliberately distinct from \(\ell_0(e)=\mathsf R\). Refutation is unilateral defeat under registered criticism. Supersession is comparative theory choice.

### 3.6 Open genesis and criticism

The abstract transitions are

\[
\frac{\operatorname{PossibleToInstantiate}(e)}{\Sigma\Longrightarrow\Sigma\oplus e}
\quad\mathsf{GEN}
\]

and

\[
\frac{c,e\in E\quad c\text{ plays a critical role}}{\Sigma\Longrightarrow\Sigma[\rightsquigarrow\cup\{(c,e)\}]}
\quad\mathsf{CRIT}.
\]

No premise derives the content of \(e\). Methods, evidence, prompts, and generators may condition which event occurs, but provenance is appraisal-inert.

## 4. The finite computable realization \(\mathfrak P^{c}\)

### 4.1 Carriers and identities

Let

\[
\mathbb B^*=\bigcup_{n\ge 0}\{0,1\}^n
\]

be the set of finite byte strings. A canonical encoding function \(\operatorname{can}\) maps every finite record to a unique byte string. Identifiers are

\[
\operatorname{id}(x)=H(\operatorname{can}(x)),
\]

under the idealized assumption that \(H\) is injective on the records appearing in one execution history. The byte carrier is not a hypothesis space. Meaning, codecs, schemas, evaluators, and interpretation rules can themselves be added as artifacts.

### 4.2 Artifacts

An artifact is

\[
a=\langle id_a,c_a,q_a,I_a,prov_a\rangle,
\]

where \(c_a\in\mathbb B^*\), \(q_a\) is a codec reference, and

\[
I_a=\langle K_a,R_a\rangle.
\]

Here \(K_a\) is a finite set of commitment identifiers and

\[
R_a\subseteq A\times\{\mathsf{dep},\mathsf{mention},\mathsf{evidence}\}.
\]

A dependence reference is load-bearing for the support pass. A mention reference is visible to queries and rendering but invisible to adjudication. An evidence reference records load-bearing evidence for a warrant-validity node. There is no stored kind field. “Frame”, “critic”, “evidence”, “standard”, and similar descriptions are structural views.

### 4.3 Commitments

A commitment is

\[
\kappa=\langle M_\kappa,\beta_\kappa,o_\kappa\rangle,
\]

where \(M_\kappa\) is a program, decidable predicate, or rubric reference, \(\beta_\kappa\in\mathbb N\) is a finite deterministic budget, and \(o_\kappa\in\{0,1\}\) marks observation-valued commitments.

Its verdict is total:

\[
V(\kappa,a)=U^{\le \beta_\kappa}(M_\kappa,c_a)
\in\{\mathsf{pass},\mathsf{fail},\mathsf{overrun}\}.
\]

Overrun is a result, not a timing accident. Wall-clock time does not enter the verdict.

### 4.4 Warrants and attack closure

A warrant is

\[
w=\langle k,t,\nu,\chi,\tau\rangle,
\]

where \(k\) is the critic artifact, \(t\) is the target, \(\nu\) is a validity artifact, \(\chi\in\{\mathsf{demonstrative},\mathsf{argumentative}\}\), and \(\tau\) is a finite trace.

A carried warrant contributes the base attack \((k,t)\). The effective attack relation \(att_L\) is the least relation containing all base attacks and closed under the following finite rules.

\[
(j,\nu_w)\in att_L\Rightarrow(j,k_w)\in att_L.
\]

If \(\nu_w\) applies a standard artifact \(s\), then

\[
(j,s)\in att_L\Rightarrow(j,\nu_w)\in att_L.
\]

If \(\nu_w\) cites evidence \(e\), and \(x\) is in the transitive dependence lineage of \(e\), then

\[
(j,x)\in att_L\Rightarrow(j,\nu_w)\in att_L.
\]

Because the node set is finite, this least closure exists and is computable by fixed-point iteration.

### 4.5 Problems

A problem record is

\[
\pi=\langle id_\pi,d_\pi,C_\pi,m_\pi,F_\pi,prov_\pi\rangle,
\]

where \(d_\pi\) is its description, \(C_\pi\) is a finite family of commitment schemas, \(m_\pi\) is deterministic metadata, and \(F_\pi\) is the finite set of frame-assertion identifiers presupposed when the problem was posed.

The set \(F_\pi\) is selected at registration, may be edited by the registrant before the registration event is sealed, and is immutable afterward. It is provenance. It does not alter any artifact label.

### 4.6 Event log and raw state

Let the event alphabet contain at least

\[
\begin{aligned}
\mathsf{RegA}(a),\quad
\mathsf{RegP}(\pi),\quad
\mathsf{Carry}(w),\quad
\mathsf{Reach}(r),\quad
\mathsf{Resolve}(\pi,z),\quad
\mathsf{Focus}(\pi),\quad
\mathsf{Policy}(q).
\end{aligned}
\]

A log is a finite sequence

\[
L_n=\langle e_1,\ldots,e_n\rangle.
\]

The raw state is a deterministic fold

\[
S_n=\operatorname{Fold}(\delta,S_0,L_n),
\]

where \(\delta\) validates an event against the current prefix and either produces the next state or rejects the event. Valid logs contain only accepted events. The state contains registered artifacts, problems, carried warrants, dependencies, mentions, evidence references, addresses, reach records, resolutions, and policy records. Status, standing, measures, orphan marks, and render packs are not stored.

### 4.7 Online generation without replay nondeterminism

A generator invocation may be represented as

\[
a=\gamma(\operatorname{Pack}_L(\pi),\xi),
\]

where \(\xi\) is either a deterministic seed derived from the log prefix or an explicitly logged seed. The resulting artifact bytes are registered in \(L\). Replay never needs to regenerate the artifact. It only folds the already registered event.

This permits open, fallible generation while preserving deterministic reconstruction of the record.

## 5. Computed status

### 5.1 Grounded attack pass

For the finite artifact set \(A_L\), define

\[
F_L(X)=\{a\in A_L:\forall b\,((b,a)\in att_L\Rightarrow\exists c\in X\;(c,b)\in att_L)\}.
\]

Since \(F_L\) is monotone on the finite lattice \(\mathcal P(A_L)\), its least fixed point is

\[
G_L=\bigcup_{i=0}^{|A_L|}F_L^i(\varnothing).
\]

Define

\[
\ell^0_L(a)=
\begin{cases}
\mathsf U,&a\in G_L,\\
\mathsf R,&\exists b\in G_L\;(b,a)\in att_L,\\
\mathsf S,&\text{otherwise.}
\end{cases}
\]

### 5.2 Dependency-support pass

Let \(dep_L\subseteq A_L\times A_L\), with \((a,b)\in dep_L\) meaning that \(a\) depends on \(b\). Well-formed logs keep \(dep_L\) acyclic.

In a reverse topological order, define

\[
\ell_L(a)=
\begin{cases}
\mathsf R,&\ell^0_L(a)=\mathsf R,\\
\mathsf S,&\ell^0_L(a)=\mathsf S,\\
\mathsf U,&\ell^0_L(a)=\mathsf U\land
\forall b\,((a,b)\in dep_L\Rightarrow\ell_L(b)=\mathsf U),\\
\mathsf{SU},&\ell^0_L(a)=\mathsf U\land
\exists b\,((a,b)\in dep_L\land\ell_L(b)\ne\mathsf U).
\end{cases}
\]

The fourth label means suspended-unsupported. It expresses loss of grounds, not refutation.

### Theorem 5.1. Totality and uniqueness

For every finite well-formed log, \(G_L\), \(\ell^0_L\), and \(\ell_L\) exist uniquely and are computable.

**Proof.** Monotonicity of \(F_L\) on a finite lattice gives a unique least fixed point after at most \(|A_L|\) growth stages. Acyclicity of \(dep_L\) gives a topological order, and each final label is then determined once the labels of its dependencies are known. ∎

### Theorem 5.2. Conservative support extension

If \(dep_L=\varnothing\), then \(\ell_L=\ell^0_L\), with \(\mathsf{SU}\) unreachable.

**Proof.** The universal dependency condition is vacuously true for every attack-unrefuted artifact. ∎

## 6. Frame assertions and background standing

### 6.1 Frame assertions

A frame assertion is an ordinary artifact \(f\) whose decoded body is

\[
\operatorname{body}(f)=\langle b,\sigma,v,D\rangle.
\]

Here \(b\) is the subject artifact, \(\sigma:\Pi_L\to\{0,1\}\) is a total budgeted predicate over problem metadata, \(v\) is either \(\mathsf{universal}\) or \(\mathsf{bounded}(Q,\varepsilon)\), and \(D\) is a departure protocol.

Its interface must satisfy

\[
(f,b)\in mention_L
\quad\text{and}\quad
(f,b)\notin dep_L.
\]

It may depend on reach records supporting its promotion case. It may mention the wounds of an incumbent it claims to succeed. It is eligible for consultation only when it addresses a registered promotion problem.

### 6.2 Consultation and standing

Define

\[
\operatorname{Consult}_L(f,\pi)
\iff
\operatorname{FrameAssertion}(f)
\land
\operatorname{PromotionAddressed}(f)
\land
\ell_L(f)=\mathsf U
\land
\sigma_f(\pi)=1.
\]

Define background standing by

\[
\operatorname{Background}_L(b,\pi)
\iff
\exists f\;(
\operatorname{subject}(f)=b
\land
\operatorname{Consult}_L(f,\pi)).
\]

Thus background is not a truth label. It is a derived role in the economy of generation: the subject is rendered as the coordinate system for problems in the matching scope.

A compatibility criterion is required to ensure that no two unresolved rival frame assertions co-frame the same problem. Formally,

\[
\operatorname{Consult}_L(f,\pi)\land\operatorname{Consult}_L(g,\pi)
\Rightarrow f=g.
\]

The criterion can be enforced by routing overlap to a discrimination problem before the candidate frame assertion becomes consultable.

### Theorem 6.1. Standing never adjudicates

If two log states agree on \(A_L\), \(att_L\), and \(dep_L\), then they have identical status labels even if their standing, schedules, render packs, reach measures, or attention weights differ.

**Proof.** The definition of \(\ell_L\) reads only \(A_L\), \(att_L\), and \(dep_L\). ∎

This gives methodological privilege without epistemic privilege. A background can determine what is shown to a generator without contributing any support edge or positive label.

## 7. Refuted but still framing

The mention law prevents a direct support dependency from a frame assertion to its subject. For a fully rigorous persistence theorem, a stronger graph condition is needed.

### Definition 7.1. Adjudication component

Let \(Q_L\) be the undirected graph obtained from \(att_L\cup dep_L\) by forgetting edge directions. Let \(\operatorname{Comp}_L(x)\) be the connected component of \(x\) in \(Q_L\).

### Definition 7.2. Frame-separation invariant

A consulted frame assertion \(f\) with subject \(b\) is separated when

\[
\operatorname{Comp}_L(f)\cap\operatorname{Comp}_L(b)=\varnothing.
\]

Mention edges are deliberately excluded from \(Q_L\). Reach records supporting \(f\) must mention, rather than depend on, the subject if subject refutation is not intended to revoke the reach case.

### Theorem 7.3. Wound persistence

Suppose \(\operatorname{Consult}_L(f,\pi)\), \(\operatorname{subject}(f)=b\), and the frame-separation invariant holds. Let \(L'\) extend \(L\) only by registering a new critic component whose only connection to the old adjudication graph is an attack on \(b\). Then

\[
\ell_{L'}(f)=\ell_L(f)=\mathsf U.
\]

Consequently,

\[
\ell_{L'}(b)=\mathsf R
\quad\text{is compatible with}\quad
\operatorname{Background}_{L'}(b,\pi).
\]

**Proof.** The extension changes only the adjudication component containing \(b\). Grounded semantics decomposes over disconnected components, and no dependency of \(f\) changes. Therefore the attack and support computation for \(f\) is identical. Since consultation depends on \(f\), not on the status of \(b\), standing persists. ∎

The source document’s mention law is necessary but not sufficient for this theorem. Without the separation invariant, a new attack on \(b\) can propagate through pre-existing attack cycles and alter the status of \(f\) indirectly.

## 8. Wounds, falls, refutation, and revocation

### 8.1 Wounds

A live wound on \(b\) is a carried demonstrative warrant \(w\) such that its trace contains

\[
V(\kappa,b)=\mathsf{fail}
\]

for an observation-valued commitment \(\kappa\in K_b\), its critic is in \(G_L\), and the resulting edge defeats \(b\).

Formally,

\[
\operatorname{Wound}_L(w,b)
\iff
\chi_w=\mathsf{demonstrative}
\land o_{\kappa_w}=1
\land V(\kappa_w,b)=\mathsf{fail}
\land k_w\in G_L
\land(k_w,b)\in att_L.
\]

A wound is an event in the status career of the subject. Under Theorem 7.3, it need not be an event in the standing career of the background frame.

### 8.2 Frame exits

Let \(L_n\) and \(L_{n+1}\) be consecutive valid prefixes. A consulted frame assertion exits standing when

\[
\ell_{L_n}(f)=\mathsf U
\quad\text{and}\quad
\ell_{L_{n+1}}(f)\ne\mathsf U.
\]

Define the exit grade by

\[
\operatorname{grade}(f,n+1)=
\begin{cases}
\mathsf{fall},&\ell_{L_{n+1}}(f)=\mathsf R,\\
\mathsf{revocation},&\ell_{L_{n+1}}(f)=\mathsf{SU},\\
\mathsf{contestation},&\ell_{L_{n+1}}(f)=\mathsf S.
\end{cases}
\]

A fall is refutation of the frame assertion itself, normally by a comparative succession warrant or a direct warranted attack. A revocation is support loss, normally because one or more reach records supporting the promotion case ceased to be unrefuted. Contestation is unresolved attack under grounded semantics.

### Theorem 8.1. Refutation and revocation are disjoint

For every artifact \(f\),

\[
\ell_L(f)=\mathsf R\Rightarrow\ell_L(f)\ne\mathsf{SU}
\]

and

\[
\ell_L(f)=\mathsf{SU}\Rightarrow\ell^0_L(f)=\mathsf U.
\]

Thus fall says that the frame assertion is defeated; revocation says that its accreditation is no longer supported.

**Proof.** Immediate from the mutually exclusive cases in the support-pass definition. ∎

### Theorem 8.2. Wounds and falls occur on different objects

Under frame separation, a wound targets the subject \(b\) and can change \(\ell(b)\) while leaving \(\ell(f)\) unchanged. A fall targets or defeats \(f\) and therefore ends consultation even if \(\ell(b)=\mathsf U\). A revocation can likewise end consultation while leaving \(b\) unrefuted.

**Proof.** Wounds contribute attacks on \(b\). Falls change the attack label of \(f\). Revocations change the support label of \(f\). Consultation is keyed to \(f\) alone. ∎

The claim that standing ends in exactly two ways requires the additional axiom

\[
\operatorname{FrameDecisive}(L):
\quad
\ell_L(f)\ne\mathsf S
\quad\text{for every promotion-addressed frame assertion }f.
\]

Without this axiom, contestation is a third exit permitted by the calculus’s own label set.

## 9. Presupposition cascade and orphaned problems

### 9.1 Exit episodes

An exit episode is

\[
x=\langle f,n,g\rangle
\]

where \(f\) leaves \(\mathsf U\) at sequence number \(n\) with grade \(g\in\{\mathsf{fall},\mathsf{revocation},\mathsf{contestation}\}\).

### 9.2 Derived orphan marks

For a problem \(\pi\), define

\[
\operatorname{OrphanMark}_L(\pi,x)
\iff
f_x\in F_\pi
\land
x\text{ occurs in }L
\land
\neg\operatorname{ResolvedAfter}_L(\pi,x).
\]

The grade carried by the orphan is

\[
\operatorname{orphanGrade}(\pi,x)=
\begin{cases}
\mathsf{premise\mbox{-}refuted},&g_x=\mathsf{fall},\\
\mathsf{premise\mbox{-}unaccredited},&g_x=\mathsf{revocation},\\
\mathsf{premise\mbox{-}contested},&g_x=\mathsf{contestation}.
\end{cases}
\]

The mark is a problem-layer review obligation. It does not refute the problem, its candidate answers, or its explicanda.

### 9.3 Lazy materialization

A mark may remain a derived scheduler fact until a focus event occurs. On \(\mathsf{Focus}(\pi)\), the renderer materializes the corresponding orphan-review problem if it has not already been registered.

This makes the cascade computationally cheap. One frame exit is one log event; its potentially large consequence is enumerated by a pure query and paid for as affected frontier items are revisited.

### 9.4 Resolutions

The source permits three substantive resolutions.

\[
\operatorname{ResolveKind}(z)\in
\{\mathsf{retire},\mathsf{translate}(\pi'),\mathsf{independent}\}.
\]

Retire records that the problem died with its premise. Translate registers a successor problem in a successor frame and records lineage. Independent records a successful argument that the problem never required the frame assertion.

A rigor gap remains when the frame assertion is later reinstated. The source simultaneously requires every status to be reopenable and every orphan mark to close only through adjudicated work, but it provides no restored-premise resolution. A complete implementation must either add

\[
\mathsf{revalidate}
\]

as a fourth adjudicated resolution or define current orphanhood as a state-derived view that deactivates upon reinstatement while retaining the historical exit episode. This document does not pretend that the choice is already settled by the sources.

### Theorem 9.1. Cascade totality

For every exit episode \(x=\langle f,n,g\rangle\) and every registered problem \(\pi\),

\[
f\in F_\pi\land\neg\operatorname{ResolvedAfter}_L(\pi,x)
\Rightarrow
\operatorname{OrphanMark}_L(\pi,x).
\]

No problem that explicitly recorded the frame assertion silently escapes the cascade.

**Proof.** \(F_\pi\) is immutable registration data, and \(\operatorname{OrphanMark}\) is a total finite filter over the log and problem table. ∎

### Theorem 9.2. Orphaned does not imply false

Changing \(\operatorname{OrphanMark}_L\) while leaving \(A_L\), \(att_L\), and \(dep_L\) fixed cannot change \(\ell_L(a)\) for any artifact \(a\).

**Proof.** Orphan marks are consumed only by scheduling, rendering, and problem-resolution transitions. They are absent from the label equations. ∎

## 10. Reach, nomination, and promotion

### 10.1 Reach records

A reach record is

\[
r=\langle a,\pi_s,\pi_t,\lambda,t_a,t_e,h,\tau\rangle,
\]

where \(a\) is the artifact, \(\pi_s\) is the problem it was developed for, \(\pi_t\) is a distinct target problem, \(\lambda\) is a lineage identifier, \(t_a\) is the artifact registration sequence, \(t_e\) is the encounter sequence for the target material, \(h\in\{0,1\}\) marks held-out provenance, and \(\tau\) is an evaluation trace.

A reach record is valid only if

\[
t_a<t_e
\]

and all commitment and provenance checks in its validity artifact are unrefuted and supported.

Let

\[
\operatorname{Reach}_L(a,\sigma)
=
\{r:\operatorname{valid}_L(r)\land\sigma(\pi_t(r))=1\}.
\]

### 10.2 Nomination

Fix a declared threshold \(K_{frame}\) and a total budgeted coherence predicate \(\operatorname{Coherent}_\sigma\) over problem metadata. Define

\[
\operatorname{Nominate}_L(a,\sigma)
\iff
\left|\{\lambda(r):r\in\operatorname{Reach}_L(a,\sigma)\}\right|
\ge K_{frame}
\land
\operatorname{Coherent}_\sigma(\operatorname{Reach}_L(a,\sigma)).
\]

Nomination causes a deterministic spawn of a promotion problem. It does not itself create background standing.

### 10.3 Promotion

A frame assertion addressing the promotion problem is evaluated through ordinary conjecture, criticism, and adjudication. Its criteria include subject demarcation, reach integrity, deterministic scope, compatibility with incumbents, and, in succession cases, recovery of the incumbent’s wound list.

Only an unrefuted and supported frame assertion becomes consultable.

### Theorem 10.1. Reach never adjudicates directly

Appending a reach record can change labels only through ordinary artifacts, warrants, and dependencies introduced by the event. The numeric reach count or nomination predicate is not read by the label equations.

**Proof.** The label equations read only \(att_L\) and \(dep_L\). Nomination merely spawns a problem. Promotion requires a separate frame assertion whose status is adjudicated normally. ∎

Promotion by reach is therefore a controller rule, not a theorem of the original Poietic calculus. What is derivable is the non-authority property: reach can nominate, but it cannot vote.

## 11. Deterministic render semantics

### 11.1 Render policy

A render policy \(q\) specifies finite slice budgets, canonical sort keys, retrieval radii, compression functions, and frame-slice rules. The active policy is selected deterministically from the log by a fixed policy-selection function. Policy artifacts remain attackable; the selection kernel itself is part of the bookkeeping semantics rather than an epistemic judgment.

For problem \(\pi\), define

\[
\operatorname{Pack}_L(\pi)=
\operatorname{can}\langle
\pi,
C_\pi,
T_L(\pi),
A_L^{top}(\pi),
D_L^{top}(\pi),
N_L^k(\pi),
P_L^k(\pi),
F_L^{slice}(\pi)
\rangle.
\]

Here \(T_L\) is the current target slice, \(A_L^{top}\) and \(D_L^{top}\) are bounded attacker and defender slices, \(N_L^k\) is a bounded graph neighborhood, \(P_L^k\) is a precedent slice, and \(F_L^{slice}\) contains one frame slice for each consulted frame matching the problem.

Every set is sorted by a declared lexicographic key such as

\[
(\text{graph distance},-\text{attention priority},\text{registration sequence},\text{id}).
\]

All ties are therefore deterministic.

### 11.2 Frame slice

For a consulted frame assertion \(f\) with subject \(b\), the frame slice contains

\[
\langle
\operatorname{digest}(b),
\operatorname{commitmentIds}(b),
\operatorname{assumptionIds}(b),
\operatorname{StandingAttackers}_L(b),
D_f
\rangle.
\]

The current wounds of the subject are rendered inside every matching scope. Background therefore ships its own crisis rather than hiding it.

### 11.3 Departures

A generated candidate \(a\) may carry

\[
\operatorname{depart}(a,f)\subseteq
\operatorname{commitmentIds}(b)\cup\operatorname{assumptionIds}(b).
\]

An undeclared conflict may ground a hidden-premise warrant. A declared departure is not penalized merely for departing; it is itself attackable and may later acquire reach sufficient to trigger discrimination against the incumbent.

### 11.4 Succession exception

For a succession problem, the renderer suppresses the incumbent’s ordinary frame slice and renders the two competing articulation digests symmetrically. This is a policy against incumbent-judge bias, not a proof of neutrality.

### Theorem 11.1. Render non-adjudication

Changing \(\operatorname{Pack}_L\) while holding \(att_L\) and \(dep_L\) fixed cannot change any current label.

**Proof.** Render packs are inputs to future generation and criticism. They are absent from the current status equations. ∎

Render policy conditions the future search trajectory. It does not confer present epistemic standing.

## 12. Demarcation and hardness to vary

### 12.1 Deterministic variation kernels

A variation kernel is a total function

\[
\mu_q(a,i,L)=a_i
\]

for \(1\le i\le k_q\), where the seed is determined by the artifact identifier, policy identifier, log-prefix identifier, and sample index. Alternatively, the generated variants can be logged explicitly. This is required for replay determinism.

Variants must alter functional roles such as mechanism, scope, causal link, or decomposition. Mere paraphrases are identified as equivalent and excluded.

### 12.2 Demarcation

Define

\[
\operatorname{crit}(a)=
\mathbf 1[K_a\ne\varnothing].
\]

Let \(B^{-HV}_L(a)\) be the current evaluation battery with hardness-to-vary commitments removed to avoid self-reference. Define mechanism load-bearingness by

\[
\operatorname{load}_k(a)=
\mathbf 1\left[
\exists i\le k:
\operatorname{RoleVariant}(a_i,a)
\land
\operatorname{VerdictVector}_{B^{-HV}}(a_i)
e
\operatorname{VerdictVector}_{B^{-HV}}(a)
\right].
\]

A finite demarcation view is

\[
\operatorname{demarcated}_k(a)=
\operatorname{crit}(a)\land\operatorname{load}_k(a).
\]

For empirical scopes, at least one commitment must be observation-valued.

A failed demarcation criterion may generate a demonstrative warrant. The Boolean view itself does not directly change a label.

### 12.3 Hardness-to-vary estimator

Let

\[
I_i(a)=
\mathbf 1[
\operatorname{RoleVariant}(a_i,a)
\land
\operatorname{BatteryInequivalent}(a_i,a)
\land
\operatorname{Passes}_{B^{-HV}}(a_i)
].
\]

Define sampled slack and sampled hardness by

\[
\widehat s_k(a)=\frac{1}{k}\sum_{i=1}^{k}I_i(a),
\qquad
\widehat{HV}_k(a)=1-\widehat s_k(a).
\]

This is a measure of how much sampled functional variation survives the current battery. It may spawn a remove-arbitrariness problem, alter attention, or be packaged as an attackable commitment. It cannot enter grounded label computation as a weight.

### 12.4 Relation to abstract slack

Let \(\operatorname{Slack}_\Sigma(a\mid X)\) be the abstract set or structure of variants that preserve the attack-survival profile and accounted explicanda. If the finite kernel enumerates a representative finite variant family and the battery exactly captures criticism-indistinguishability, then

\[
1-\widehat{HV}_k(a)
\]

is the sampled mass of that slack family.

It is not, in general, equivalent to the original embedding order on slack structures. Two slack structures can have equal sampled cardinality while differing structurally, and an embedding order need not be recoverable from one scalar. The score is therefore an operational surrogate, not a reduction of hard-to-vary to probability.

## 13. Knowledge as a derived attention view

The source paper’s exact computable definition is

\[
\operatorname{Knowledge}^{src}_L(a)
\iff
\ell_L(a)=\mathsf U
\land
\operatorname{active}(a)
\land
\operatorname{reach}_L(a)>0,
\]

where active means criticizable and variationally non-degenerate.

That formula does not itself require a high hardness-to-vary score, despite prose describing knowledge as resistant to variation. A strengthened view that matches the prose is

\[
\operatorname{Knowledge}^{\theta}_L(a)
\iff
\ell_L(a)=\mathsf U
\land
\operatorname{demarcated}_k(a)
\land
\widehat{HV}_k(a)\ge\theta
\land
\operatorname{reach}_L(a)>0.
\]

The threshold \(\theta\), kernel, and battery are policy parameters and must remain attackable.

Neither view is constructor-theoretic knowledge itself. They are finite, history-indexed indicators that the artifact has survived the criticism actually supplied, exposes itself to counterexamples, resists sampled functional variation, and works beyond its original address.

### Theorem 13.1. Knowledge is attention-only

Let \(\alpha_L(a)\) be any scheduler or renderer priority function that consumes either knowledge view. Replacing \(\alpha_L\) by another function while preserving \(att_L\) and \(dep_L\) leaves every status label unchanged.

**Proof.** Measures and attention do not occur in the status equations. ∎

Thus the machine may focus on what looks knowledge-like without certifying knowledge.

## 14. Capture diagnostics

Capture is treated as effective collapse of generation under conditioning, not as proof that the stable consensus is false. Every diagnostic is a deterministic function of a fixed sequence-number window, never wall-clock time.

Let

\[
W_m(n)=\{\max(1,n-m+1),\ldots,n\}
\]

and let \(C_{m,n}\) be conjecture registrations in that window. Let \(\phi_L(a)\) be a deterministic behavioral signature consisting of the artifact’s commitment-verdict vector over a declared battery, its declared relations, and its problem lineage.

### 14.1 Stream contraction

Let \(p_z\) be the empirical fraction of \(C_{m,n}\) with signature \(z\), and define the effective support

\[
N_{eff}=\frac{1}{\sum_z p_z^2}.
\]

For \(N=|C_{m,n}|>1\), define

\[
\operatorname{SC}_{m,n}
=
1-\frac{N_{eff}-1}{N-1}.
\]

A value near one means the conjecture stream has contracted into a small number of repeated behavioral forms.

### 14.2 Attack-target entropy

Let \(q_t\) be the empirical fraction of newly carried attacks targeting artifact \(t\) in the window. Define normalized entropy

\[
\operatorname{ATH}_{m,n}
=
\frac{-\sum_t q_t\log q_t}{\log |\{t:q_t>0\}|},
\]

with value one when targets are spread evenly and zero when all attacks concentrate on one target. A fixed precision and rounding rule is part of the policy.

### 14.3 Criticism debt

Fix an age floor \(h\). Let

\[
U^{old}_{m,n}=
\{a:\ell_L(a)=\mathsf U\land n-\operatorname{seq}(a)\ge h\}.
\]

Define

\[
\operatorname{Debt}_{m,n}
=
\frac{|\{a\in U^{old}_{m,n}:\operatorname{LiveAttackers}_L(a)=\varnothing\}|}
{\max(1,|U^{old}_{m,n}|)}.
\]

This measures the fraction of old unrefuted artifacts that have attracted no live criticism.

### 14.4 Reinstatement rate

Let \(R\!\to\!U\) count artifacts whose label changes from refuted to unrefuted in the window. Let \(N_{crit}\) be the number of criticism registrations. Define

\[
\operatorname{RR}_{m,n}
=
\frac{R\!\to\!U}{\max(1,N_{crit})}.
\]

A persistently zero rate can indicate that criticism only accumulates and is not itself being criticized.

### 14.5 Validity-node attack rate

Let \(N_\nu\) be the number of new attacks on warrant-validity artifacts and \(N_{att}\) the number of new attacks. Define

\[
\operatorname{VAR}_{m,n}
=
\frac{N_\nu}{\max(1,N_{att})}.
\]

This exposes whether the machinery that turns judgments into attacks is itself under criticism.

### 14.6 Exogenous grounding ratio

Call a live warrant externally grounded when every terminal leaf in its validity lineage is a budgeted program check, recorded evidence item, or appellate ruling rather than a closed loop of mutually dependent judgments. Let \(W^{live}_{m,n}\) be live warrants in the window. Define

\[
\operatorname{EGR}_{m,n}
=
\frac{|\{w\in W^{live}_{m,n}:\operatorname{ExternallyGrounded}(w)\}|}
{\max(1,|W^{live}_{m,n}|)}.
\]

This does not establish correctness. It measures contact with anchors outside the current judgment loop.

### 14.7 Attention response with hysteresis

Let

\[
D_{m,n}=
\langle
\operatorname{SC},
\operatorname{ATH},
\operatorname{Debt},
\operatorname{RR},
\operatorname{VAR},
\operatorname{EGR}
\rangle.
\]

A deterministic hysteresis controller may enter a diversify-attention mode when a registered threshold predicate \(T_{enter}(D_{m,n})\) holds and leave only when a stricter recovery predicate \(T_{exit}(D_{m,n})\) holds. The mode may alter lineage quotas, render slices, retrieval balance, critic budgets, and variation budgets.

It may not add or remove attack edges, dependency edges, or labels directly.

### Theorem 14.1. Capture diagnostics are non-adjudicative

Two states with identical \(A_L\), \(att_L\), and \(dep_L\), but different diagnostic values or attention modes, have identical labels.

**Proof.** The diagnostic vector is consumed only by the renderer and scheduler. ∎

These instruments detect stalled dynamics. They cannot detect a confidently stable ecology whose blind spot is shared by its generator, critics, evidence interpretation, and standards.

## 15. Deterministic replay

### 15.1 Replay conditions

Byte-identical replay requires more than an append-only log. The following conditions are necessary.

**Canonical events.** Every event, record, set, map, numeric value, and string normalization has one canonical byte encoding.

**Deterministic fold.** Event validation and state transition are total functions of the current prefix and event.

**Deterministic evaluators.** Every commitment has a finite step budget and a specified overrun result.

**Deterministic graph algorithms.** Fixed-point iteration, topological ordering, closure expansion, and tie-breaking use canonical identifier order.

**Deterministic sampling.** Variation kernels and generator sampling are seeded from logged data, or their outputs are logged.

**No hidden mutable input.** Wall-clock time, remote mutable state, ambient locale, unspecified floating-point behavior, and unordered iteration do not enter verdicts or serialization.

### Theorem 15.1. Replay determinism

Let \(L\) be a valid log. Under the replay conditions,

\[
\operatorname{Fold}(\delta,S_0,L)
\]

is unique. Any two conforming implementations of the same specified functions produce the same canonical state bytes and the same canonical render-pack bytes for every log prefix.

**Proof.** By induction on \(|L|\). The base state has a unique canonical encoding. Assume the canonical state after prefix \(L_n\) is unique. The next event has a unique canonical encoding; validation and \(\delta\) are deterministic; every derived graph, label, measure, and render component uses deterministic algorithms and canonical ordering. Therefore the state after \(L_{n+1}\) is unique. ∎

The cross-implementation byte claim is conditional on identical specified codecs, evaluators, numerical rules, and serialization. Semantic determinism alone does not imply byte identity.

### Corollary 15.2. Historical views

For every \(i\le n\),

\[
S_i=\operatorname{Fold}(\delta,S_0,L_{1:i})
\]

is a read-only historical state. Refutation, retirement, revocation, and reopening are represented by later events rather than deletion of earlier records.

## 16. Derivability ledger

| Requested phenomenon | Formal realization | Classification | What it depends on |
|---|---|---|---|
| Background knowledge as standing | \(\operatorname{Background}_L(b,\pi)\) | Explicit construction | Separate status and standing axes |
| Frame assertions | Ordinary artifacts with subject, scope, validity, departure protocol, mention and reach dependencies | Explicit construction | Promotion-addressing and mention law |
| Refuted but still framing | Theorem 7.3 | Derived theorem | Frame separation plus consultation keyed to the frame assertion |
| Wounds versus falls | Theorem 8.2 | Derived theorem | Distinct subject and frame-assertion objects |
| Revocation versus refutation | Theorem 8.1 | Derived theorem | Two-pass labels \(\mathsf R\) and \(\mathsf{SU}\) |
| Presupposition cascade | Theorem 9.1 | Derived theorem | Immutable problem-frame provenance and frame-exit episodes |
| Orphaned problems | \(\operatorname{OrphanMark}\), Theorem 9.2 | Derived view and theorem | Cascade query plus non-adjudicative scheduling |
| Promotion by reach | Nomination and promotion transitions | Controller construction | Valid reach records, scope coherence, ordinary adjudication |
| Render policy | \(\operatorname{Pack}_L\) | Controller construction | Canonical budgets, ordering, frame slices, succession exception |
| Capture diagnostics | \(D_{m,n}\) | Operational measure family | Fixed windows, behavioral signatures, attention-only response |
| Demarcation and hardness to vary as measures | \(\operatorname{demarcated}_k\), \(\widehat{HV}_k\) | Operational surrogates | Budgeted commitments and deterministic role-level variation |
| Knowledge as a derived attention view | \(\operatorname{Knowledge}^{src}\) or \(\operatorname{Knowledge}^{\theta}\), Theorem 13.1 | Derived view and theorem | Status, demarcation, reach, optional hardness threshold |
| Deterministic replay over an append-only log | Theorem 15.1 | Derived theorem | Canonical serialization, pure fold, deterministic budgets and seeds |

All thirteen are therefore formalizable. The direct theorem-level results are refuted-but-still-framing, wounds-versus-falls, revocation-versus-refutation, cascade totality, orphan non-falsity, knowledge non-adjudication, and deterministic replay. Background standing, frame assertions, promotion, rendering, diagnostics, and computable demarcation or hardness are additional structures rather than consequences of the original three-component state alone.

## 17. Minimal axiom set for the thirteen results

The following compact theory is sufficient.

\[
\mathsf A_1:\quad L\text{ is append-only and state is a pure fold over }L.
\]

\[
\mathsf A_2:\quad \text{All verdicts are finite-budget deterministic results.}
\]

\[
\mathsf A_3:\quad \text{Status is the grounded attack pass followed by the acyclic support pass.}
\]

\[
\mathsf A_4:\quad \text{Standing is a derived consultation relation and never enters status computation.}
\]

\[
\mathsf A_5:\quad \text{A frame assertion mentions but does not depend on its subject.}
\]

\[
\mathsf A_6:\quad \text{Consulted frame assertions satisfy the frame-separation invariant.}
\]

\[
\mathsf A_7:\quad \text{Problems immutably record their pose-time frame assertions.}
\]

\[
\mathsf A_8:\quad \text{Reach can spawn promotion problems but cannot directly alter labels.}
\]

\[
\mathsf A_9:\quad \text{Render, measures, diagnostics, and knowledge views act only through attention.}
\]

\[
\mathsf A_{10}:\quad \text{All set ordering, numerical evaluation, sampling, and serialization are canonical.}
\]

Under \(\mathsf A_1\) through \(\mathsf A_{10}\), the seven theorem-level results follow. The remaining six requested items are the definitions and policies named by \(\mathsf A_4\), \(\mathsf A_5\), \(\mathsf A_8\), \(\mathsf A_9\), and the finite estimators in Sections 12 and 14.

## 18. What has not been derived

This formalism does not derive the content of a future conjecture. It formalizes registration, criticism, defeat, support loss, standing, rendering, and attention after contents exist.

It does not prove the constructor-theoretic resilience identity. The computable knowledge view is at most a fallible indicator.

It does not make abstract hardness to vary decidable. The finite score depends on kernel quality, battery quality, sample budget, and the current repertoire of criticism.

It does not prove that reach thresholds identify genuine background knowledge. Promotion thresholds and scope predicates remain empirical policy constants.

It does not detect a stable ecology whose blind spots are shared by all internal generators, critics, standards, and evidence interpretations.

It does not prove that a successor will arrive. A wounded background may remain refuted and still framing indefinitely, with its crisis rendered and its succession problem open.

## 19. Final result

The Poietic calculus can be made mathematically precise without turning it into a positive-standing optimizer. The key move is to separate four things that ordinary epistemic systems often collapse:

\[
\text{attack status},\qquad
\text{dependency support},\qquad
\text{background standing},\qquad
\text{attention}.
\]

Attack status says what currently survives criticism. Dependency support says whether an artifact still has its declared grounds. Background standing says what frames generation in a scope. Attention says what the system chooses to show, schedule, measure, or revisit.

Once those layers are kept distinct, the requested phenomena stop looking like exceptions. A background can be refuted and still frame because its subject and its frame assertion are different objects. A wound can leave the frame standing, while a fall defeats the frame assertion and a revocation merely removes its accreditation. Problems can inherit pose-time presuppositions and enter a total orphan cascade when a frame exits. Reach can nominate a frame without conferring status. Render policy and capture diagnostics can shape future variation without voting on truth. Knowledge can be exposed as a revisable attention view. The entire selective record can be replayed deterministically from an append-only log.

The price of that clarity is equally precise. Several attractive claims in the source paper require extra invariants that were not stated: graph separation for wound persistence, a decisiveness condition for exactly two frame exits, canonical serialization for byte replay, deterministic seeding for sampled measures, and a resolution rule for orphan episodes after frame reinstatement. Those are not philosophical objections. They are the small pieces that turn a compelling sketch into an executable calculus.
