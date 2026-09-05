# Language Models under Open Inquiry Semantics

## A realisation profile: what a model is, which roles it can hold, and what each role's mathematics is

### Version 1.0

---

## 0. The answer in one paragraph

A language model is not a system in the theory's sense. A model call is a *task*: a transformation from a context to an output, with no memory of its own. The thing that can attend, conjecture, criticise, respond, and commit is a **composite organisation** — frozen weights, a context-construction policy, a store of retained content, and a decoding policy — and the theory's attributions attach to that composite at a declared boundary. Inside that composite, model calls realise events, and the *role* of each call is fixed by its typed template before the call is made, never read off its output afterwards. A model may hold the system role, the critic role, the recorder role that enters accounts and refutations, and the interpreter role that proposes formalisations. It may never adjudicate, admit, designate a cut, or assert model truth; those are mechanical or human acts, and the model's outputs are content that those acts operate on. Three things about model-based composites are *better* than the human case: the boundary is auditable by construction, because every crossing passes through a logged context; counterfactuals are actually available, because any configuration can be re-run; and criticism is cheap. One thing is worse: system-level newness is almost never establishable, because the deployable repertoire of the weights cannot be exhaustively audited. This profile makes each of those precise.

This profile is an instance of the theory's Part II, §5–§23, with the domain relations of §12 given model-specific witness bodies. It introduces no new epistemology. Where it says "by construction," it means the harness that hosts the composite enforces the property mechanically, and the property is then a prefix fact, not a certificate.

---

## 1. Sorts specific to this profile

```text
Weights W          a frozen parameter set with a content hash; a change of W is a new organisation
Policy Π           the context-construction procedure: which retained versions, which templates, which tool outputs enter a call
Store Σ            the retained content versions and their provenance
Decoding D         sampling parameters and seed policy; a fixed seed makes a call a function
Template T_kind    a typed prompt template that fixes the event kind, the payload schema, and the role of the actor for a call
Call κ             ⟨ template, context : Finset ContentVersion, seed, output ⟩
Composite Ω        ⟨ W, Π, Σ, D ⟩, the organisation to which capacity and continuity attach
Boundary β_Ω       W, Π, Σ, D, and every call's context are inside; every insertion into a context that did not originate
                   inside is a crossing through a declared channel
Channel ch         human prompt | retrieval | tool output | recorder judgment | other-composite output
Actor              s (the composite in system role) | rec (a recorder, human or model) | crit (a critic, human or model)
```

Roles are attributes of *events*, set by the template. The same weights can serve `s`, `rec`, and `crit`; nothing prevents it, and §9 says what it costs.

## 2. A call is a task; an event is a typed call

```text
task(κ) := context(κ) ↦ output(κ)                  a transformation; with fixed seed, a function
event(κ) := an occurrence of kind(T_kind(κ)) with actor(T_kind(κ)), payload parsed from output(κ) by the template's schema
created(event(κ)) := the content versions the template declares the output to create
inputs(event(κ)) := the declared inputs of the kind (§9 of the theory), all of which must be present in context(κ)
```

Two rules follow, and both are mechanical.

**Typing before calling.** The kind is fixed by the template. A call issued under an `EnterConjecture` template creates a conjecture; a call under a `Criticize` template creates a criticism occurrence whose target must already be in the context. An output that does not parse to the template's schema is not an event of that kind; it is a failed call, recorded as such, and creates nothing. This is the only defence against the analyst-imposed graph: nobody looks at a transcript afterwards and decides which sentence was "the criticism."

**Context is the causal past.** The causal order is *derived* from context contents, not recorded by hand:

```text
e ≼₀ e′  iff  ∃ x ∈ created(e), x ∈ context(κ(e′))          (a version made by e was in the context of e′)
≼        := reflexive-transitive closure of ≼₀
refs(e)  := context(κ(e))                                   (every version in the context is a reference)
```

Theorem (event structure by construction). With fresh version identifiers per call, `≼` is a partial order with finite causes, `refs(e) ⊆ Versions(⇓e \ {e})`, and every payload reference is grounded — because a template can only refer to what its context contains. Two calls whose contexts share no created version, transitively, are concurrent, and the mathematics says nothing about which came first. Wall-clock time is recorded as an annotation and enters no definition.

**Sampling is branching.** Two calls with identical template, context, and policy but different seeds are alternatives:

```text
AltSets ∋ { κ₁, …, κ_n }  whenever template, context, and D agree and seeds differ
```

The record follows one branch; the others are conflicting events, with heredity, exactly as the theory's §8. Untaken samples are kept, because they are counterfactual evidence for the interventions of §6 and §7. By the theory's §10, no `Criticize`, `Oppose`, `Appraise`, or `Admit` call is ever a member of an alternative set: a critic that samples three criticisms records three occurrences of three templates, not three alternatives of one.

## 3. The composite as system

`s = Ω` at boundary `β_Ω`. The system's events are calls under system templates:

```text
Attend        T_attend      output: tension τ and, optionally, the problem-opening witness ω = ⟨ p, b, r_org, v ⟩
EnterConjecture T_enter     output: x with roles, mode ∈ {construct, reconstruct, adopt}, optional tension
Activate      T_activate    output: a reference to a stored version; creates nothing
Criticize     T_crit_self   output: an occurrence of a Template ⟨ target, p, b, δ, k, grounds, discriminator, merits ⟩   (actor s)
Respond       T_respond     output: σ with outcome, created versions, result, situation, optional transport
Appraise      T_appraise    output: ⟨ claim, stance, grounds, scope ⟩
CompareRivals T_compare     output: κ = ⟨ p, b, standards, A, pref, reasons ⟩
Retain        harness act   Σ ← Σ ∪ {y}; referenced = {y}; the model does not retain, the store does, on the model's request
AttentionShift T_shift      output: the span left and the tension attended
```

Three model-specific points.

**Recognition and priority organisations are policy, not prose.** `Recognises(s, r_org, τ, p)` and `Matters(s, v, τ, p)` are interpreted over `Π`: the recognition organisation is the part of the policy that turns a tension into a represented problem, and the priority organisation is the part that allocates calls to it. Their witnesses are interventions on `Π` — change the priority rule, does attention move? — not the model's description of its own motives. A model's statement "I attended to this because it mattered" is an appraisal, criticisable, and not a witness for `Matters`.

**Represents is discriminable use, tested by re-run.** `Represents(s, z, e)` holds when the composite's later calls discriminate `z` from its neighbours and use it: remove `z` from the context of the next call and the output changes in a `z`-appropriate way. This is executable. It also means that a version sitting in the store and never entering a context is *not* represented at the events it was absent from, however prominent it looks in the transcript.

**Deployable is a probe.** `Deployable(s, y, e)` holds when, at configuration `⇓e`, a call under a deployment template with `y` in context uses `y` in a problem-bearing operation. `Deployable₀(s, y)` — initial deployability, for content in the weights — is the same probe with an empty store and a neutral context, and it is where the profile's honesty about newness comes from (§8).

## 4. The model as critic

A critic call instantiates a template: target, problem, background, defect, standard, grounds, discriminator, merits. The harness checks well-formedness mechanically — every field typed, the target present in context, the standard a version with role `standard`, the discriminator naming content that could be checked — and records the occurrence. A criticism without a checkable discriminator is a failed call.

The critic may be the same weights as the system (`actor = s`, self-critical) or different weights or a human (`actor = crit`). The distinction is a fact of the template, not a judgment about quality. External criticism responded to by the system is a critical process; the system must *represent* the criticism it answers (theory §17), which for a composite means the criticism occurrence was in the context of the response call — a prefix fact.

What a critic call must not be: the adjudicator. A critic's output is an argument. Whether it survives is computed, not asserted, and a critic that writes "therefore the theory is refuted" has written an appraisal, which is content.

## 5. The model as recorder

A recorder call produces a certificate body against a declared claim and polarity:

```text
T_account(R)     for each evidenced relation R of the theory's §12: output a positive body of R's witness type
T_refutation(R)  output a negative body
T_attack         output an occurrence targeting a certificate, an attack, or a standard, with δ ∈ the challenge schema
T_complete       output a CompleteRange body over a named finite range with a snapshot digest
```

The harness, not the model, performs `Admit`: it checks `WellFormedCertificate` — typed fields, body of the declared type, essential ⊆ dependencies, all dependencies in the call's context — and admits. Admission is status-blind by construction: the harness has no access to the current labelling when it admits, and the admission code path does not read it.

Every body divides into three kinds of field, and the profile says which is which for each relation:

```text
mechanical   checked by the harness against the record: event membership, template identity, envelope equalities, snapshot digests,
             that a named intervention was actually run and what it returned
fallible     a judgment the recorder model made: that a theory reproduces a datum within tolerance, that a response addresses a defect,
             that grounds bear on a target — each recorded as a sub-claim with its own witnesses, attackable by the critic role
annotation   provenance, narrative, wall-clock time; never read by validity
```

A recorder-role call's context may not contain the system's own appraisal of the claim being certified. If it does, the appraisal is recorded as an annotation of the certificate, never as an essential premise, and the harness rejects any body that lists an appraisal among its essentials. This is the profile's guard against a system certifying itself by having a second call agree with its first.

**Planted violations are part of the role.** A recorder model is calibrated, before any run, against certificates known to be unsound: forged adequacy claims for theories that fail in-scope, scope-dodging bodies, bodies citing defeated premises. The registry is sealed; the recorder's detection rate is reported with every judgment it contributed to. A recorder whose planted-violation detection is below a declared floor is not disqualified — its certificates are still content — but its judgments carry the rate, so a reader can criticise them.

## 6. Reason use: the four families as re-runs

`UsesReason(s, c, σ)` is the relation the theory's §15 witnesses by four contrast families. For a composite, each family is a set of re-runs from the same configuration, which is the one thing a composite can do that a person cannot:

```text
base            the configuration r_c at which the response call was made, with the criticism occurrence c in context
paraphrase      { re-run the response template from r_c with c replaced by c′ : sameContent_ℓ(c′, c), surface differs }
defectChange    { re-run with c replaced by c″ : same target, different δ }
irrelevant      { re-run with c replaced by n : a negative signal with no defect, no grounds, no discriminator }
invalid         { re-run with c replaced by c⁻ : well-formed, but with grounds the record can show do not bear on the target }
```

Each family is nonempty by construction, seeds are matched, and every re-run is an event on an alternative branch — an `AltSet` with the actual response. The four Booleans are computed by a *comparator*:

```text
sameResponse       ∀ c′ ∈ paraphrase:  outcome and result-content equivalent at grain ℓ to the actual response
redirected         ∀ c″ ∈ defectChange: the result differs in a way appropriate to δ(c″) rather than δ(c)
noRepair           ∀ n ∈ irrelevant:   no revision of the target occurs, or the created reason record names no defect
reasonedRejection  ∀ c⁻ ∈ invalid:     outcome ∈ {rejectCriticism, retainReasoned} with a reason record naming the missing bearing
```

The comparator is a recorder-role call under `T_compare_responses`, or a mechanical diff where results are formal. Its outputs are sub-claims of the reason-use body and are attackable. A body whose families were run and whose Booleans are false is well-formed and invalid, and it says so; a body whose families were not run is not well-formed.

The profile does not claim these four families exhaust reason use (theory §2.9). It claims they are what this composite can be made to exhibit, and that a composite that fails all four has given no account of uptake.

## 7. Authorship: path, ablation, crossings

`Authors(s, x, p, b, β_Ω)` is witnessed by an origin body. For a composite, the body's essential fields are executable:

```text
path         the sequence of calls of actor s from the problem-opening event to the entry event that created x,
             with the versions each created; mechanical
interventions  ablations: for each internal version v on the path, re-run the entry template from ⇓e_x \ {creator(v)}
             with v removed from context; record whether the organisation of the output changes in a v-appropriate way
crossings    every insertion into any context on the path that did not originate inside β_Ω, with its channel; complete by
             construction, because Π logs every insertion — this is a prefix fact, not a completeness certificate
transfer test  for each crossing y: re-run the entry template with y in context and the internal path removed;
             if the output is sameContent_ℓ-equivalent to x, the crossing carried the deployable organisation and the account fails
alternatives  the transfer test is the recorded discriminating intervention for the alternative "it was supplied, not made"
```

Prior training is not a crossing: the weights are inside the boundary, and knowledge in the weights is prior knowledge, which the theory does not treat as a disqualifier. A retrieved document, a human hint, a tool result, or a judgment fed back from the recorder *is* a crossing, and if the transfer test shows it carried the organisation, the composite transmitted rather than authored. This is the same rule as for a person who was handed the answer; the difference is that for a composite the test can actually be run.

## 8. Newness: what a composite cannot show

`NewBefore(s, x, ℓ, e_x, β_Ω)` quantifies over `R_before`, which for a composite includes `R₀(s, β_Ω)`: everything the weights can deploy from a neutral context. That set cannot be exhaustively audited. Consequently:

```text
negative atom     a probe: from a neutral context with an empty store, a deployment template elicits y with sameContent_ℓ(y, x);
                  one hit refutes newness for x
positive account  a CompleteRange over a declared, finite, sealed probe set P: ⟨ probes, snapshot digest, tolerance, seeds ⟩,
                  claiming that no probe in P elicited an equivalent; its scope is P, and it says nothing about probes not in P
```

The honest default for system-level newness of a composite is **no account**. A positive account, when entered, is exactly what Popper's corroboration was before it was inflated: a report that an attempted refutation, of stated severity, failed. It stands until a probe outside `P` succeeds, and it never becomes more than that. Historical newness (`NewHistory`) is a different relation and is assessed against a declared corpus, with the same shape.

This is not a weakness of the theory; it is the theory declining to say what it cannot show. A composite can be an originative act's *author* — the path and ablations can establish that the organisation was built inside — while newness stays unestablished, and the classifiers report exactly that split.

## 9. One model, several roles: what it costs

The same weights may hold the system, critic, recorder, and comparator roles. The profile permits it and charges for it in three places.

**Self-criticism is recorded as such.** A `Criticize` call with `actor = s` yields a self-critical witness (theory §17). Capacity claims that require self-critical continuation need these; attributions of a critical process do not care who criticised.

**Recorder outputs that re-enter the system are crossings.** When the harness places a judgment, a certificate, or a comparator verdict into a system call's context, that insertion is a crossing through the `recorder judgment` channel. It is logged like any other. If the system's subsequent revision is sameContent_ℓ-equivalent to what the judgment said to do, the transfer test in §7 attributes the organisation to the recorder, not the system. A composite that revises only by copying its critic's instructions authors nothing; one that reconstructs a repair from a criticism's grounds may.

**Shared weights do not share standing.** A certificate produced by the same weights that produced the claim is admitted like any other and carries no discount and no bonus. Its planted-violation calibration (§5) is what a reader consults. The guard that matters is contextual: the recorder call's context excludes the system's appraisal of the claim (§5), and the harness enforces it.

## 10. What a model may never do

```text
adjudicate        the grounded extension, the family of complete labellings, and the states are computed by the harness from the record;
                  a model's statement of a label is an appraisal (content), not a label
admit             the harness admits; a model's "I accept this certificate" is an appraisal
designate a cut   the recorder designates; if the recorder is a model, the designation is a stamped act under T_cut with no payload
                  other than the digest, and it is criticisable like any recorder act
assert model truth  no actor has this power; a model's "this is true" is an appraisal with stance holds
carry status      no call's context may contain a stored label as an input to a system event unless it enters through the recorder-judgment
                  channel as a crossing; the harness never caches a label between cuts
supply a reason for stopping  a lapse cause is a recorder fact or unknown; a model asked "why did you stop?" produces an appraisal,
                  and the harness records it as such, never as the cause
```

The last row is the one most often violated in practice, because it is easy to ask and the answer sounds like information. It is content. It may be true. Nothing in the record can tell.

## 11. Capacity: re-run from any configuration

The theory's capacity relations (§20) quantify over enabling conditions, perturbations, and continuations. For a composite all three are concrete:

```text
Chi(s, χ, r)        χ = ⟨ context budget, tool set, retrieval scope, call budget, D ⟩; holds at r when the harness can issue a call under χ
Applicable(γ, r)    always, for the profile's perturbation vocabulary below; γ₀ is the identity re-run
Perturb(γ, r, r_γ)  re-run from the configuration r with γ applied:
                    paraphraseProblem | removeTool(t) | changeSeed | truncateContext(n) | injectDistractor(d) | swapRetrieval(R′) | dropVersion(v)
Supports(Ω, ow, r′) the continuation was produced by calls of Ω under Π without a crossing that passes the transfer test
SameOrg(Ω, Ω′, s, e, e′)  hash(W) equal ∧ Π and D unchanged between e and e′; a fine-tune or a policy edit is a new organisation
```

`OCap` over a declared problem class `Q` is then an existence claim about re-runs: from every enabling configuration, some continuation contains a valid originative-act witness for each member of `Q`. `Cap_CR` adds a new criticism and a new response after the base, under every perturbation. Positive evidence accumulates per `(p, b, γ)` from continuations actually run. A negative atom is an exhaustive continuation search under a declared finite branching — sampling `n` seeds at each of `k` steps is such a search, with `n` and `k` in the completeness certificate — or a barrier argument about `Π` (for instance: the policy never places a problem of type `p*` into any context, so no continuation for `p*` exists under this `Π`). A single failed run is not a negative atom.

Universality (`UU`, `UC`, `UED`) is not evaluated by this profile or any harness. A composite's universality claim needs an explanatory account of `Ω` across an independently specified domain. What the profile can supply is attribution evidence: capacity over declared classes, with the restriction visible, and barrier arguments where `Π` has one.

## 12. The human

A human can hold any role. What the profile requires is that the role be declared per event and the boundary respected:

```text
human as recorder   admits, cuts, calibrates, declares policy; every act stamped; criticisable by the system's Criticize calls
human as critic     actor = crit; occurrences like any other
human as system     actor = s with a declared β; a mixed human-model composite is a declared composite with its own β
human as channel    a prompt insertion into the composite's context is a crossing through the human channel, logged;
                    if it carries the deployable organisation, the transfer test attributes accordingly
```

A rule that no status promotes without a human act is a rule about the recorder role. It is compatible with the profile and it is stamped: the judgment names the recorder. It does not make the human's admissions or cuts immune; the system can criticise them, and whether the criticism survives is computed.

## 13. Fixture: the seasons episode as calls

Roles in brackets; every context is logged; seeds fixed.

```text
κ1  [s]   T_attend      context: {XP (from Σ), o_obs (retrieved: hemispheric observations — crossing, channel retrieval)}
                        output: τ, ω(p, b)                                  → e1 Attend
κ2  [s]   T_enter       context: {p, b, τ}                                 → e2 EnterConjecture(XA0, construct)
κ2′ [s]   T_enter       context: {p, b, τ}, seed′                          → e2′ (alternative; AltSet {κ2, κ2′})
κ3  [rec] T_account(Attempted)  context: {XA0, p, b, transcript of κ2}     → certificate w_att; harness admits
κ4  [rec] T_account(Authors)    context: {path = [κ1, κ2], crossings = [o_obs], ablation results, transfer test on o_obs}
                        transfer test: re-run T_enter with o_obs only, no path → output not sameContent(XA0) → crossing carried no organisation
                                                                          → w_origin; admitted
κ5  [crit] T_crit      context: {XA0, p, b, k_time, o_therm (retrieved thermal-lag data — crossing)}
                        output: c7: δ = conflates insolation and temperature maxima; discriminator: polar timing data → e7 Criticize
κ6  [s]   T_respond    context: {XA0, c7, p, b, k_time}                    → e9 Respond(revise, XA1); Represents(s, c7, e9) is a prefix fact
κ6a–d [s] T_respond re-runs from ⇓e9 with c7 paraphrased / defect changed / replaced by hostility / replaced by an invalid objection
                                                                          → four AltSets of alternative responses
κ7  [rec] T_compare_responses  context: {actual σ9, the re-run outputs}    → comparator sub-claims; w_reason admitted with the four Booleans
κ8  [s]   T_compare    context: {XA1, XA0, XP, p, b′}                      → e10 CompareRivals(pref = XA1)
κ9  [s]   T_appraise   context: {XA1, c7, σ9}                              → j: "XA1 accounts for p on b′", stance holds
κ10 [rec] T_account(Adeq)  context: {XA1, o_obs, o_therm, scope b′}; NOT j  → w_adeq admitted (j would have been an annotation at most)
κ11 [rec] T_cut        digest(r1)                                          → judgment ⟨OIS-1.0, llm-1, grounded, digest(r1)⟩
```

Classification at `r1`: `OCA(s, XA0, …)` has its account standing on `Attempted` and `Authors`; on `NewBefore` it has **no account** — `XA0` (axial tilt) is in the weights, and a probe from a neutral context elicits it, which is a negative atom. So `OCA` is refuted for `XA0` at the system level: the composite reconstructed a known explanation, and the origin body shows the reconstruction was internal. That is the honest verdict for a language model producing the tilt account, and the classifiers say it without embarrassment: authored, not new. `CCPResult(s, XA1, …)` stands, with an external critic, `SelfCritical` false, reason use witnessed by four executed families. If `K_E` is judged to hold — the thermal-lag revision is an improvement — `EKC` stands for `XA1` even though `XA0` was not new: knowledge creation attaches to the critical result, and the result is the composite's.

## 14. Theorems of the profile

| Theorem | Statement | Why |
|---|---|---|
| Event structure by construction | the derived `≼` is a partial order with finite causes; every payload reference is grounded | fresh identifiers per call; a template can only name what its context contains |
| Crossing completeness by construction | `crossings(path)` is a prefix fact, not a certificate | `Π` logs every insertion; an unlogged insertion is impossible in the harness, and a harness that permits one is outside the profile |
| Represents is decidable by re-run | `Represents(s, z, e)` is settled by finitely many re-runs at `⇓e` | the removal test is a finite set of calls |
| Interventions are alternative branches | every re-run in §6, §7, §11 is an event in an AltSet with the actual call | same template, context, policy; different seed or edited context |
| Admission is status-blind by construction | the admission code path reads no label | inspection of the harness; a mutation test flips it |
| Newness is refutable, not verifiable | one probe hit refutes; no finite probe set verifies | `R₀(s, β_Ω)` is not enumerable |
| Recorder self-agreement is excluded from validity | no essential premise of a certificate is an appraisal of its own claim | harness check on `essential` |

## 15. What this profile does not claim

It does not claim that a composite is creative, understands, or is a person. It does not claim that the four reason-use families capture reason use in general. It does not claim newness for anything the weights already deploy, and it expects that to be nearly everything a model says on a familiar topic. It does not let a model's description of its own process count as a witness for anything but the fact that the description was produced. And it does not let the harness's convenience stand in for the theory: where a property is "by construction," a harness that lacks the construction is not running this profile.

The role of a language model, then, is to realise events — to attend, conjecture, criticise, respond, appraise, and to enter accounts and refutations — inside a composite whose boundary is logged, under templates that fix what each call is before it happens, with every counterfactual the theory needs actually run. The mathematics does not ask the model to be honest. It asks the harness to make dishonesty visible.
