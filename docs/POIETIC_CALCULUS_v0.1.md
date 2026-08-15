# The Poietic Calculus (𝔓), v0.1

**A calculus of knowledge-creation via creativity, on Deutschian epistemology and constructor-theoretic foundations.**

Status: conjecture. Not computable as stated; deliberately so at one locus (§7). Grounded in the source map *Deutsch's Epistemology & Marletto's Constructor Theory* and in Deutsch's published account of creativity.

---

## 0. The definitional base

Deutsch's canonical definition (*The Beginning of Infinity*, terminology): **creativity is the capacity to create new explanations.** Three refinements from his other writings fix what a formalization must and must not do:

1. Conjectures are not derived from evidence; evidence only tests them ("Creative Blocks," Aeon 2012; *Possible Minds* essay). So the calculus may contain **no operator from data to content**.
2. All progress in narrow AI has been achieved by *narrowing* the range of candidate thoughts toward a predefined criterion (*Possible Minds*, chess-engine passage). Creativity is the contrary operation: open-ended widening under selection. So the calculus may contain **no fixed goal-functional whose optimization is the dynamics** — "if we want it to be creative, then it can't be obedient" (Deutsch–Pinker dialogue).
3. Creativity evolved for the faithful replication of memes (*BoI* ch. 16): acquiring an existing idea already requires conjecturing its meaning. So the calculus must make **interpretation, learning, and discovery the same transition type**, not three mechanisms.

One terminological widening, licensed by Deutsch's own practice: *BoI* applies explanatory knowledge to aesthetics (ch. 14, objective beauty), morality, mathematics, and philosophy, not only to empirical science. 𝔓 therefore takes **content** as the neutral sort and treats "explanatory" as a *role relative to a problem*, so that a proof, a design, a sonata, a moral principle, and a physical theory are all candidate solutions in the same calculus.

## 1. The science-shape failure, mechanically

The brief warns that a formalization of knowledge-creation tends to collapse into a formalization of science. The collapse is not a matter of vocabulary; it happens through two specific formal commitments, jointly or singly:

**(F1) Antecedent closure of the content-space.** The formalism fixes, before the dynamics run, the class of things that can ever be entertained — a σ-algebra of hypotheses, an enumeration of computable predictors, a fixed language under contraction/expansion. Genuine novelty (conceiving what was previously inconceivable — Deutsch: people in 1900 did not consider the internet unlikely; they did not conceive of it at all) is then representable only as *selection*, never as *genesis*.

**(F2) A justificatory or predictive success-functional.** The formalism carries a state variable that accumulates positive standing — credence, confirmation, expected predictive accuracy, converging estimate — and the dynamics are its ascent. This imports justificationism structurally, regardless of the author's Popperian sympathies, and it privileges the one species of reason (empirical prediction) for which such a functional is even superficially plausible.

The familiar calculi each fail through one or both. Bayesian confirmation theory fails through both: a fixed hypothesis space and a credence functional that the Popper–Miller theorem (and Deutsch's 2016 reconstruction) argues cannot coherently reward ampliative content — a lever the source map correctly flags as *contested*, so 𝔓 relies on it only conjecturally (§8). Solomonoff induction fails through both, and additionally makes prediction the telos, rendering non-predictive species (mathematics, art, philosophy) invisible and empirically equivalent rivals indistinguishable. Formal learning theory fails through a teleological variant of F2: convergence-to-a-fixed-target, where Popper's schema P1 → TT → EE → P2 has the target itself transformed by each solution. AGM belief revision fails through F1: revision in a static language with an exogenous entrenchment order — entrenchment *given*, not *earned by criticism*. Reinforcement learning and classical decision theory fail through F2 in its goal form: an obedient optimizer is by construction a narrower. Dung argumentation frameworks, taken alone, avoid F2 but exhibit a static form of F1: the arguments and attacks are given; there is no genesis. 𝔓 accordingly uses argumentation semantics as its *statics of criticism* (§3.3) and supplies what AFs lack: the dynamics of genesis, problem-formation, and supersession.

The two negative commitments of 𝔓, then: **no antecedently closed content-space** (openness), and **no positive-standing functional** (appraisal is comparative and negative: problematicity and supersession only).

## 2. Strata and primitives

𝔓 is stratified. Nothing in the upper strata floats free of physics; nothing in the physics dictates content.

**Stratum Φ (physical / constructor-theoretic).** Primitives are those of constructor theory: substrates, attributes, tasks (attribute-transformations), and the modal classification of tasks as **possible (✓T)** — performable with arbitrarily high accuracy by some constructor, an entity that causes the task and retains the ability to cause it again — or **impossible (✗T)** — forbidden by law. Laws are expressed as ✓/✗ statements; counterfactuals are first-class. Information media are substrates on which the flip and copy tasks are ✓; the interoperability principle gives medium-independence. **Knowledge** takes its exact constructor-theoretic definition: *information that can act as a constructor and cause itself to remain instantiated* — resilient information, knower-free.

**Stratum Ε (content).** Contents are abstract information-objects — Popper's World-3 residents: theories, proofs, designs, works, norms, methods, construals, criticisms. By inheritance from Φ, a content is information only if it *could have been otherwise*: the counterfactual character of information gives, for free, the requirement that contents have alternatives — the raw material of variation. Contents bind to Φ by the instantiation relation inst(e, s).

**Stratum Δ (dialectical).** The machinery of problems, criticism, standing, and supersession, defined over states of an **ecology**: a population of substrates instantiating contents and performing the transitions of §4.

**Definition 2.1 (State).** A poietic state is Σ = ⟨𝔈, ⇀, Λ⟩ where 𝔈 is the corpus of instantiated contents, ⇀ ⊆ 𝔈 × 𝔈 is the registered criticism (attack) relation — criticisms are themselves contents, so higher-order criticism is automatic — and Λ is the **ledger**: an append-only, monotone record of every transition event. Nothing is ever deleted from Λ; retirement, refutation, and reopening are *events*, not erasures. All appraisal statuses of §3 are **computed from Σ, never stored**: there is no acceptance event, and every status is instantly revisable by the next registration.

**Definition 2.2 (Roles).** Contents occupy roles, which may overlap and may change: *explanatory* (offered as resolving a problem), *critical* (attacking), *problematic-construal* (stating a problem — see §3.1), *explicandum* (a record standing in need of explanation: an experimental event, a proof-obligation, a surprising equivalence, an aesthetic datum such as *this cadence grips*, a moral case), and *methodic* (generators of variation, criticism, problems, or explicanda). One sort, many roles: this is what makes reflexivity automatic — methods, appraisals, and problems are all first-class contents, criticizable by the same machinery they serve.

**Definition 2.3 (Repertoire).** ρ(Σ) ⊆ 𝔈 is the set of methodic contents currently in good standing. The repertoire is *in the loop*: it is conjectured, criticized, and superseded like everything else. 𝔓 never identifies creativity with any fixed ρ — doing so would reinstate F1 one level up.

**Principle 2.4 (Resilience Identity — conjecture).** In an ecology whose error-correction includes criticism, *surviving criticism is the mechanism of resilience*: a content's epistemic career (withstanding attack, acquiring reach, being used and re-instantiated) just is the physical process by which its information causes its own perpetuation. Popper's "surviving criticism" and Marletto's "resilient information" name one property at two strata. This identity is the single most load-bearing import from the source map, and it is attackable (§8.1).

## 3. Statics

### 3.1 Problems

**Definition 3.1 (Tension, problem).** A *tension* in Σ is a set τ ⊆ 𝔈 whose joint standing is impugned — paradigmatically, contents that attack one another or that jointly generate an unabsorbed explicandum. A **problem** is a content p = ⟨τ, γ⟩: a *conjectural construal* of a tension, where γ states in what way τ seems inadequate. Problems are first-class and enter by the same genesis rule as everything else; hence problem-identification is itself creative, and a problem can be attacked (as a pseudo-problem, as misconstrued, as three problems wearing a coat). γ carries a **source-type** — too glib, too laboured, too narrow, over-ambitious, glimpsed-but-unachieved unification, cross-field conflict, surprising explicandum — because different sources license different repair moves.

Problems are defined over contents, never over the world. A raw goal or target that references no content is not a problem but a **task**, and belongs to Φ, classified only as ✓ or ✗.

### 3.2 Explicanda and accounting

**Definition 3.2.** X(e) is the set of explicanda that e is registered as accounting for. The accounting relation is itself asserted by contents ("e accounts for x") and is therefore attackable — this is where theory-ladenness lives: what an apparatus-record *is* a record of, what a text *says*, what a chord *does*, are conjectures. Evidence, generalized to all species, enters the calculus **only** as new explicanda: an explicandum can render a content problematic, or enable a supersession, and can do nothing else. There is no operation by which an explicandum raises anything's standing.

### 3.3 Standing

**Definition 3.3 (Impugnment structure).** The current standing of Σ is read off the argumentation framework (𝔈, ⇀) by its **grounded extension** G(Σ): the unique minimal complete extension. Grounded semantics is forced by fallibilism: it is the sceptical, commitment-minimal solution, it exists uniquely (no arbitrary choice among preferred extensions), and membership in it is a computed status rather than an act — matching the requirement that no event of "accepting" a theory ever occurs.

Impugnment is necessary but not sufficient for the epistemically decisive judgments, which are comparative:

### 3.4 Supersession

**Definition 3.4 (Succession).** For contents e, e′ in explanatory roles: e′ ⊒ e (e′ *succeeds* e) iff
(a) **Recovery**: X(e) ⊆ X(e′), *or* e′ accounts for the apparent success of e over X(e) — the misconception/successor move, by which a successor authorizes its predecessor's restricted validity;
(b) **Rigidity**: e′ is no easier to vary than e over the shared explicanda (§3.5);
(c) **Non-immunization**: no proper part of e′ is excisable without loss of some member of X(e′). Ad-hoc riders and protective-belt moves are exactly the excisable-without-loss parts; clause (c) rejects them mechanically.

e′ ▷ e (strict) iff e′ ⊒ e and additionally X(e) ⊊ X(e′), or e′ survives an attack that impugns e, or e′ is strictly harder to vary.

**Definition 3.5 (Status ladder).** *Conjectured*: e ∈ 𝔈. *Problematic*: e ∈ τ of some standing problem. *Tentatively refuted*: e is problematic **and** some rival e′ ∈ G(Σ) with e′ ▷ e exists. There is no higher positive status than *currently unsuperseded and unimpugned*, and that status is expressly indexed to Σ. Refutation is a two-place relation requiring a surviving rival: a lone failed test yields *problematic*, never *refuted* — an engine that closes a problem on a single failure without a rival commits the exact error the 2016 paper isolates. Every transition on the ladder is reopenable, because the ladder is computed and the ledger forgets nothing.

### 3.5 Hard to vary, order-theoretically

No probabilities, no measures. Let the *variants* 𝒱(e | X) of e relative to explicanda X be the contents sharing e's architecture of claims but differing in at least one **explanatory degree of freedom** — a component of e not pinned by X under current background. (Variant-hood is functional, not syntactic: a paraphrase is not a variant; a swapped mechanism is.)

**Definition 3.6 (Slack).** slack_Σ(e | X) is the substructure of 𝒱(e | X) that is **criticism-indistinguishable** from e in Σ: same attack-survival profile, same accounted explicanda.

**Definition 3.7 (Harder to vary).** e is harder to vary than f (relative to shared X, in Σ) iff slack(e | X) embeds into slack(f | X) under variation-structure-respecting maps and not conversely. The Persephone myth has vast slack — swap deities, motives, mechanisms; every variant survives exactly the same criticisms. The axial-tilt explanation has slack ≈ {itself}: vary the geometry and the explicanda themselves (anti-phased seasons across hemispheres) attack the variant.

Slack classes are in general unsurveyable, so hardness-to-vary judgments are **themselves conjectures**, asserted as contents and attackable — which is 𝔓's rendering of Deutsch's reply to Bayesian reduction attempts: hard-to-vary is a property of explanations, which are only approximately modelled as propositions.

**Definition 3.8 (Good explanation).** e is *good* relative to X in Σ iff it accounts for X, it stands in no live conflict with members of G(Σ) that are otherwise good, and its slack is minimal among extant rivals with no excisable idle parts. Good rivals for the same explicanda are scarce — typically one or zero; a **crucial test** (of any species: experiment, counterexample, decisive critical comparison) is definable only when at least two exist.

### 3.6 Reach and universality

**Definition 3.9.** Reach_Σ(e) = {p : e participates in a standing resolution of p in Σ}. Potential reach Reach*(e) = the union of Reach over all ✓-reachable extensions of Σ. By Theorem 4.4 below, Reach* is not determinable within Σ: reach is emergent and unbidden, discovered rather than designed.

**Definition 3.10.** A repertoire ρ is **universal over a domain D** iff Reach*(ρ) covers every ✓-resolvable problem of D. A **jump to universality** is a single genesis step whose addition tips Reach*(ρ) from bounded to unbounded in D — alphabets, positional numerals, Turing machines are the Φ-historical instances.

## 4. Dynamics

Two transition schemata generate everything.

**(GEN)  Σ ⇝ Σ ⊕ e**, permitted whenever the instantiation of e in the ecology is ✓. That is the *only* side-condition, and it lives in Φ. No premises, no derivation requirement, no licensing by data, method, or authority. Provenance is logged in Λ and is appraisal-inert:

**Axiom 4.1 (Genesis Inertness).** All appraisal predicates (problematic, good, superseded, harder-to-vary, …) are invariant under permutation of provenance records in Λ. Origin confers nothing — neither warrant nor stigma. This one axiom simultaneously excludes inductivism (data-derivedness confers nothing), authority (source confers nothing), and genetic dismissals of any generator, mechanical or biological (machine-origin confers nothing).

**(CRIT)  Σ ⇝ Σ with ⇀ ∪ {(c, e)}**, where c ∈ 𝔈 in a critical role. Since c itself enters by GEN, criticism is creative: new *modes* of criticism — proof, the controlled trial, perspective construction, close reading — are inventions, and the growth of the criticism-repertoire is part of the same dynamics it serves.

**Remark 4.2 (Transmission is re-creation).** Receiving a content is a GEN of a conjecture about its meaning, criticized against use and context. Learning, interpretation, and discovery are one transition type; a hermeneutic act and a laboratory conjecture differ in repertoire, not in kind. This is *BoI* ch. 16 rendered structurally, and it is one of the places 𝔓 visibly refuses the science shape.

**Axiom 4.3 (Inevitability).** Every state with a nontrivial corpus and a live repertoire admits ✓(GEN of a problem-content construing some tension). There are no problem-free fixed points except degenerate states: empty corpus, or dead repertoire. Solving transforms the problem-situation; P2 arises from the *content* of the solution to P1, and progress is gauged by the depth-distance between them.

**Axiom 4.4 (Solubility).** For every problem p in Σ: if the tasks required to instantiate some resolving content are not ✗, then ✓(a trajectory from Σ to a state in which p is resolved — some content attains standing and the tension retires). Law-impossibility is the only absolute obstacle; every other obstacle is want of knowledge. This is the momentous dichotomy lifted from Φ into Δ.

**Theorem-schema 4.5 (No prophecy).** There is no task — hence no constructor — that, for arbitrary Σ, yields the content of a future standing-attaining novelty of Σ's trajectory *without that yielding being itself a GEN event*. Sketch: suppose Π computes from Σ a content e — not in 𝔈 and not obtainable from Σ by its extant repertoire — that will attain standing. Running Π instantiates e; the prediction *was* the creation; and by Axiom 4.1, Π's authorship confers nothing — e stands only by surviving criticism. Forecasting the growth of knowledge and performing it are the same task. Corollaries: the corpus's growth is unpredictable-in-content from within, though ✓ throughout — unpredictability without stochasticity; and Reach* is undeterminable in advance (Definition 3.9).

**Definition 4.6 (Expectation, probability-free).** Expect_Σ(x | e) iff the GEN of a record of ¬x would render e problematic. This is the calculus's entire surrogate for prediction, and it is the only forward-looking operator 𝔓 contains.

**Remark 4.7 (Statuses in motion).** Under GEN and CRIT, the derived statuses of §3 shift without any further rule: a new explicandum can make a good explanation problematic; a new rival can convert problematic into tentatively-refuted; a new defence can reopen a refutation. The engine's *only* memory is Λ; its *only* judgments are computed; its *only* growth is GEN.

## 5. Species of reason

Nothing in §§2–4 mentions experiment, observation, prediction, or nature. That is the point. Science enters as one *instance* of a quantified structure:

**Definition 5.1 (Species).** A species of reason 𝔖 is a self-maintaining lineage of methodic contents ⟨problem-construal generators, variation generators, criticism generators, explicandum generators⟩ — a quadruple of repertoire-components, each first-class, each evolvable, whose joint exercise sustains unbounded trajectories in some domain.

**Science** is the species whose explicandum-generators include experiential records and whose criticism-generators include the crucial-experiment schema. The 2016 status ladder, comparative refutation, background knowledge, the Duhem–Quine management, and the treatment of experimental error (a discrepancy is validly error precisely when no rival explanatory content predicts it) are all recovered as the science-instantiation of §§3–4, with nothing added.

**Mathematics**: explicanda are proof-obligations, surprising equivalences, and monsters; criticism is proof-checking and counterexample-construction; Lakatos's proofs-and-refutations is GEN/CRIT run on definitions, with monster-barring as slack-negotiation over Definition 3.6. A constructor-theoretic signature: which criticisms are *performable* — what is provable — depends on the physics of computation (the Church–Turing–Deutsch principle), so even mathematics' criticism-repertoire has nomologically contingent reach.

**Philosophy**: explicanda include the norms of the other species and its own; criticism is argument, retorsion, and conflict-with-otherwise-good-contents — clause (ii) of Definition 3.8 does alone the work that clause (i) plus experiment does in science. Bartley's pancritical rationalism is the normative statement that the repertoire contains no attack-suppressors (below), applied to methodology itself: the calculus's own rules are conjectural conventions, criticizable in-calculus.

**Art**: aesthetic explicanda are objective in exactly Deutsch's ch.-14 sense (signals that had to cross a species gap could not be parochial), and aesthetic problems are tensions among aesthetic contents. Criticism is aesthetic criticism; hard-to-vary applies verbatim — in a masterwork, slack is near-trivial (alter a bar and it worsens), while kitsch is high-slack work whose elements are interchangeable without any criticism noticing. Genres and techniques are repertoire; a work's continuing grip on problems it was never made for is Reach, emergent and unbidden. Nothing here required relabeling; that is the test that 𝔓 is not science-shaped.

**Definition 5.2 (Rational and anti-rational resilience).** A content (or repertoire) is **rationally resilient** iff its resilience mechanism is *surviving registered criticism*; **anti-rationally resilient** iff its mechanism is *preventing registration* — suppressing CRIT, flagging itself unattackable, disabling the critical faculties of its hosts. The distinction is structural, not psychological: a rational meme's resilience requires ⇀ live — it persists *through* criticism — while an anti-rational meme's resilience requires ⇀ suppressed — it persists *by preventing* criticism; each is fragile exactly where the other thrives. **Static ecologies** are states whose repertoires contain ⇀-suppressors and variation-suppressors; **dynamic ecologies** keep both transition schemata unimpaired. Coercion's epistemic signature is ⇀-suppression: it entrenches error by disabling criticism. A species is *rational* iff its repertoire contains no suppressors — rationality as a structural property of repertoires.

**Definition 5.3 (Open clause).** A **new species** is a GEN on methodic contents constituting a novel self-maintaining quadruple. That undiscovered species exist is a ✓-statement; by Theorem 4.5 their content is unspecifiable now. 𝔓 is open at the top by construction: it quantifies over species and forbids itself an enumeration of them.

**Definition 5.4 (Person; creativity).** A **person** is a substrate that is a universal constructor for the poietic dynamics itself: a universal explainer, capable of unbounded GEN/CRIT trajectories across species, including the genesis of new species. **Creativity is not an operator of 𝔓; it is the name of 𝔓's dynamics as realized in such a substrate** — the capacity to create new explanations, exercised as open-ended genesis under self-improving criticism. Because the dynamics contain no goal-functional, a creative substrate is not an optimizer of anything; goals appear only *as contents* — conjectured, conflicting, revisable — which is why a genuinely creative system cannot be obedient.

## 6. Deliberate absences

Each absence is load-bearing; each names what its reintroduction would break.

**No credences over contents.** A probability functional over 𝔈 reinstates F2 and, per the Popper–Miller lever, incoherently rewards ampliative content. (The lever is contested; see §8.5. The absence survives on independent grounds: F2.)

**No confirmation or support operator.** Explicanda create problems and enable supersessions; nothing else. Reintroduction converts corroboration into accumulation and the calculus into inductivism with Popperian paint.

**No truth-predicate in the dynamics.** Two partial orders can diverge — *truer* and *better* — and only *better* (the ⊒/▷ machinery plus hardness-to-vary) is operative. *Truer* survives as a regulative relation asserted in-practice by contents and attackable like any of them; formalized verisimilitude died in 1974 and 𝔓 does not resurrect it.

**No acceptance event, no terminal state.** The intended models of 𝔓 are the unbounded trajectories. A convergence condition or success state would reintroduce teleological closure and falsify Axiom 4.3.

**No antecedent content-language.** The corpus is open; GEN may introduce contents inexpressible in any prior state's vocabulary. Fixing a language reinstates F1 and reduces creativity to search.

**No goal-functional over the dynamics.** Optimization narrows; creativity widens under selection. Goals are contents.

**No probability in Δ at all.** Expectation is Definition 4.6. Where decisions must be taken, small-world decision-theoretic probabilities may be used *by* agents *about* actions — as contents of methodic role — never as appraisal of contents.

## 7. Computability posture

𝔓 is a transition-system schema with deliberately non-effective components: slack-comparison, variant-classification, and ✓-judgment are in general undecidable and are ascertained only conjecturally, in-calculus. This is fidelity, not deficit: an effective recipe for GEN would be a frozen repertoire, and Definition 2.3 forbids freezing the repertoire — while the Church–Turing–Deutsch principle guarantees that any *particular* poietic ecology is physically instantiable and simulable. The engineering consequence is a clean cut: the **bookkeeping layer** — ledger, grounded-extension computation, supersession checks against registered explicanda, status derivation, problem objects with source-types — is exactly implementable today; the **genesis layer** is supplied by whatever fallible generators one has, entered as methodic contents, appraisal-inert in origin, and criticized like everything else. An engine that implements the bookkeeping faithfully and leaves genesis open is not an incomplete implementation of 𝔓; it *is* an implementation of 𝔓.

## 8. How to refute this calculus

𝔓 is a content; this document is a GEN event; Genesis Inertness applies to it. Its most exposed conjectures, in descending order of consequence:

**8.1 The Resilience Identity (2.4)** may conflate memetic fitness with epistemic standing. Definition 5.2 is the built-in defence — resilience-by-suppression is distinguished from resilience-by-survival — but a content could survive *genuine, registered* criticism because the ecology's criticism is miscalibrated, and 𝔓 as stated cannot distinguish a hardy truth from a criticism-shaped parasite except by more criticism. If that regress is vicious rather than virtuous, 2.4 falls.

**8.2 Grounded semantics (3.3)** is minimal-commitment, but working practice treats background knowledge as *held*, not merely unattacked; if rational practice requires commitments beyond the sceptical core — choosing among preferred extensions — the fallibilist argument for groundedness is incomplete.

**8.3 Functional variant-hood (3.5)** defines variants via explanatory degrees of freedom, which presupposes an analysis of explanation-architecture that 𝔓 gestures at but does not supply. If no non-circular analysis exists, hardness-to-vary floats.

**8.4 Non-immunization as excisability (3.4c)** may misclassify idealizations, which are excisable-ish yet not ad hoc; Duhem–Quine pressure concentrates exactly here.

**8.5 The Popper–Miller lever** is disputed (transitivity-paradox readings). 𝔓's no-credence commitment is argued independently via F2, but if a probabilistic epistemology were exhibited that carries no antecedent hypothesis-closure and no positive-standing accumulation, the absence in §6 would need a new defence — or the calculus a revision.

A successor to 𝔓 must recover these explicanda, remain harder to vary, and carry no idle parts. Definition 3.4 applies to this document.
