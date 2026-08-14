# A Computable Calculus of Conjecture, Criticism, and Background

**Provenance:** operator-supplied PDF (docs/COMPUTABLE_CALCULUS.pdf,
committed 2026-08-13, the authoritative original); this file is a
verbatim mechanical text extraction for grep/search. On any doubt the
PDF governs. Theory authority for the v2 reconciliation program; see
the reconciliation tranche's REQUEST.md for the operator's three
pre-decided headline items.

---

A Computable Calculus of Conjecture,

Criticism, and Background

Abstract. We present a calculus in which every epistemic

judgment is computable: statuses are labels of a Dung grounded

extension extended by a support pass, all evaluation is resource-

bounded and deterministic, and the entire state is a replayable fold

over an append-only event log. The calculus is critical-rationalist

throughout: demarcation is explanatory, not merely predictive;

there is no induction, no conﬁrmation relation, and no probability

over the truth of any claim; there is no authority and no ﬁnal state.

Its central contribution is a two-axis epistemic state. Alongside

status (truth-standing under criticism) it computes standing (role

in the economy of generation: whether an artifact is framed, or

does the framing). The second axis realizes the doctrine of

background knowledge — methodologically privileged for the

occasion, epistemically privileged never — and makes

representable the ordinary condition of mature science: a

framework that is refuted and still framing. The same axis is what

the logic of experimental tests requires, since refutation is

unilateral but rational theory-choice is intrinsically comparative.

Promotion into background is earned by measured reach and

adjudicated like any conjecture; background is refuted by

expectation-violation through the ordinary warrant machinery; its

fall is a distinct, adjudicated event whose consequence is a

mechanical criticism-cascade through every problem posed in its

terms. Knowledge itself receives a computable characterization —

unrefuted, hard to vary, reaching — as a derived view that can steer

attention and never adjudicate. Every mechanism reduces to

untyped artifacts, attack and dependence edges, problem criteria,

and deterministic render policy; the calculus formalizes in full the

selective half of an evolutionary process whose generative half it

deliberately leaves open, while aﬃrming the computability of the

whole.

1. Epistemological invariants

The calculus is the enforcement of eleven commitments.

Everything after this section is machinery discharging them; each

is cited where discharged.

P1 (Fallibilism). No element — content, tests, evidence, rules,

measures, the calculus's own procedures — is certain, justiﬁed, or

ﬁnal. Consequence: every status admits an exit; nothing is ever

veriﬁed; the machine never certiﬁes a terminal state.

P2 (No induction). Theories are not derived from observations.

Generation is conjecture, unconstrained by the calculus;

observation enters solely as criticism. Consequence: the calculus

contains no conﬁrmation relation. There is no edge by which

evidence supports a claim; evidence can only ground attacks.

Acceptance into the record is survival, not support.

P3 (Criticism is the sole selector). Epistemic state changes only

through registered criticism and its defeat. A judgment that is not

an attack, or the defeat of an attack, moves nothing.

P4 (Explanatory demarcation). Knowledge-apt content is an

explanation that forbids something: an account of a mechanism

whose assertions rule out states of affairs. Both halves are

necessary. Content that forbids nothing has no attack surface and

is outside the game; content that forbids without explaining —

prophecy, oracle, bare correlation — dies for its explanatory

emptiness before and without testing, since most bad ideas are

rightly rejected unexperimented. Empirical falsiﬁability is the

special case in which a forbidden thing is an observation.

P5 (Theory-ladenness of observation). Observations are

themselves conjectures. Acceptance of a basic statement is a

revisable decision; an observation refutes only while it itself

survives criticism. Science rests on piles driven into a swamp, and

the piles are inspectable.

P6 (No authority). No source enjoys status privilege — not the

user, not the rules, not the calculus. Rule-objects are artifacts

inside the game and attackable there. Authority may exist only as

attention — what is rendered, in what order — never as status.

P7 (Problems ﬁrst). Inquiry runs P₁ → tentative theory → error
elimination → P₂. There is no conjecture without a problem, and
the growth of knowledge is the succession of problems, not the

accumulation of answers.

P8 (Error preservation). Refuted knowledge is retained as refuted.

Error correction requires the error's record; deletion is forgery of

the growth sequence.

P9 (Hard to vary). An explanation whose components can be

freely substituted while its performance is preserved is bad even if

unrefuted. Variability is itself criticizable.

P10 (Unbounded conjecture). The space of proposable

conjectures is open: every unrefuted artifact has proposable

successors with strictly extended attack surfaces. The game

cannot halt by exhaustion — though a conditioned generator's

effective reach can collapse while in-principle reach stays

unbounded, and the calculus must police the gap.

P11 (Background). Every test and every problem is posed against

background knowledge held unproblematic for the occasion. This

privilege is methodological and revocable: background directs the

searchlight — it shapes what is conjectured and which problems

are posable — while remaining, in principle, the most exposed

knowledge in the system, since its commitments stand open

indeﬁnitely. Two consequences frame the second half of this

paper: background must be renderable as the standing frame of

generation without ever being insulated from criticism; and when

background falls, the problems posed in its terms — not merely

the answers — come up for review.

P11 is where this calculus parts company with its neighbours.

Lakatos protected the hard core and directed criticism at a belt;

here the core pays for its position with more exposure, not less.

Kuhn observed that paradigms persist through anomaly and

concluded the persistence was extra-rational; here persistence-

through-refutation is a computed, criticizable state with its

wounds rendered in public.

2. Computability discipline

C1 (Determinism and replay). The append-only event log is the

sole ground truth. Every verdict, label, measure, and rendered

prompt is a pure function of the log; replaying the log reproduces

the state byte-for-byte. Wall-clock time never enters a verdict.

C2 (Budgeted decidability). Every evaluation runs under a

declared, ﬁnite, deterministic budget (step counts, item counts).
Verdicts are total over {pass, fail, overrun};  overrun  means
"unobtainable within the declared budget," never "the machine was

slow." Budgeting is what keeps Rice's theorem at bay: the calculus

never asks an undecidable question.

C3 (Untypedness). Artifacts carry no kind ﬁeld. All dispatch is on

interface structure — what an artifact commits to, attacks, and

depends on. A type would be an unattackable classiﬁcation:

status privilege by construction, violating P6, and a stored

judgment, violating P1. Roles that look like types (standard,

evidence, precedent, frame) are patterns of structure and render

policy, recoverable by query.

C4 (Computed, never stored). Status and standing are

materialized views over the log, recomputable at any historical

sequence number. Nothing is deleted (P8); a historical view is

physically read-only.

C5 (Measures never adjudicate). Numeric signals — hardness-to-

vary, reach, isolation, diversity — inﬂuence the graph through

exactly three channels: (a) spawning problems, (b) being

packaged as budgeted commitments whose fail verdicts generate

warranted attacks, (c) steering attention (scheduling, rendering,

budgets). They never enter label computation. A metric is not a

criticism (P3).

C6 (No credence). No probability ever attaches to the truth of an

artifact. Probabilistic support is not inductive support: every

evidential rise in a hypothesis's probability decomposes into a

deductively entailed component and a countersupported

remainder (the Popper–Miller decomposition), so a probability

calculus can carry no epistemic weight that the attack graph does

not already carry. Corroboration is a record of criticism survived,

never a magnitude of conﬁdence; statistics of the generator's

output distribution are properties of the generator, never of any

conjecture's truth; and no prediction whose outcome depends on

the future growth of knowledge is assigned a probability, since the

growth of knowledge is precisely what no distribution ranges over.

Where probability appears inside content — a stochastic model

and its forecasts — it is content, adjudicated like any other.

3. Ontology

Deﬁnition 3.1 (Content). Content is opaque bytes plus a codec

(utf8, json, csv, numeric, code). Meaning is imposed by conjecture

and checked by program.

Deﬁnition 3.2 (Artifact). An artifact is

a = ⟨ id, content_ref, codec, interface, provenance ⟩

interface = ⟨ commitments : [κ-id],  refs : [⟨target, 

role⟩] ⟩,

role ∈ { dependence, mention, evidence }

id = hash(canonical(content_ref, codec, interface))

Warrant carriage is an explicit append-only relation  carry ⊆ A ×
W ; a later event may add a pair without changing the artifact's
identity.  dependence  refs contribute support edges to  dep  (kept
acyclic);  mention  refs are non-load-bearing;  evidence  refs are
permitted on warrant validity nodes and declare load-bearing

evidence (Closure 3, below). Provenance records the generating

role and event, and is epistemically inert: it may steer attention,

never labels.

Deﬁnition 3.3 (Commitment). A commitment κ = ⟨eval, budget,

observation_valued⟩ where eval is a program, a decidable

predicate, or a rubric reference (§11). Its verdict on content c is

V(κ, c) = U^{≤β}(τ_κ, c) ∈ { pass, fail, overrun }

— extensional, budgeted, decidable (C2). An observation-valued

commitment with no covering evidence artifact spawns a research

problem; evidence sealed under holdout (§11) does not count as

covering before its reveal.

Remark (commitments are counterfactuals). A commitment

asserts that a transformation of the world — its forbidden case

obtaining while its carrier stands unrefuted — is impossible. The

interface is therefore the artifact's content in counterfactual form:

a speciﬁcation of which tasks are possible and which impossible,

and the calculus adjudicates nothing else. What an artifact is,

epistemically, is what it rules out.

Deﬁnition 3.4 (Warrant). A warrant is a contentful attack:

demonstrative (a commitment, its fail verdict, and the trace) or

argumentative (a case). Every warrant carries a validity node ν —

an artifact asserting the test was sound and relevant. A bare

verdict is never an edge.

Closure rules (enforced during  att  construction):

1. Validity closure. Any attacker of ν attacks the warrant, hence

the carrier's attack edge.

2. Case-law closure. The ν of any rubric-derived warrant refs the

standard it applied; every registered attacker of that standard
attacks ν. Refute a standard ⇒ every verdict under it falls ⇒
every target reinstates, computed in one pass.

3. Evidence closure. A ν grounded in recorded evidence refs it;

attackers of the evidence or of anything in its transitive

dependence lineage attack ν. Invalidating a source reinstates
the target with no rule outside  att / dep . This is P5 made
mechanical: the faulty instrument is an attack on the

observation, and its success is an ordinary reinstatement.

Deﬁnition 3.5 (Problem). π = ⟨description, criteria, provenance⟩.

Criteria are commitment schemas instantiated per candidate; the

root battery is pinned into every problem: internal-consistency

checks and the two halves of explanatory demarcation (P4) — the

attack surface is nonempty, and, for empirical scopes, a

mechanism is present and load-bearing, in that role-level

substitution or deletion of it ﬂips verdicts. A mechanism that can

be swapped freely is decoration, and its carrier is refuted by

program without an experiment being run. Provenance records the

spawn trigger and, when the problem is posed under active

background, the ﬁeld

provenance.frame : [ frame-assertion ids ]        

(§9.8)

written deterministically at registration, editable by the registrant

at pose, immutable thereafter (C4). Like all provenance it is

epistemically inert.

Deﬁnition 3.6 (State). S = (A, Π, carry, att, dep, addr, status,

standing, measures) — a materialized view, recomputable at any

log position.

4. Well-formedness

A state is well-formed iff every carried warrant names registered

objects; every attack edge derives from a carried warrant; every

criterion is a commitment schema; the three closures hold;  dep  is
acyclic; and every rubric-derived warrant's trace contains a

conforming trial transcript (§11). All transition rules preserve well-

formedness.

5. Dynamics

Transition rules.

Rule

Conj

Crit

Enabling

condition

Π ≠ ∅; a
problem π

selected

Effect

register a = γ(π, S) with interface

attached; addr += (a, π). No

problem, no conjecture (P7).

target a; a valid

register the critic if new; carry += (k,

warrant w

w); derive att += (k, a)

Rule

Adj

Spawn

Enabling

condition

after any

registration

Effect

recompute the two-pass labels (§6)

any trigger

register a new problem with

below

provenance

Reﬂ

always

the calculus's own rules, standards,

render policies, and guard

procedures are registered artifacts

— attackable (P6)

Spawn triggers (exhaustive): failed verdict ⇒ successor problem;
≥2 surviving rivals for one π ⇒ discrimination problem; unrefuted
artifact with low hardness-to-vary ⇒ remove-arbitrariness
problem; reach event ⇒ explanation-debt problem; reach events
for one artifact spanning ≥ K_frame distinct lineages over a
coherent scope ⇒ promotion problem (§9.4); a frame assertion
leaving unrefuted standing ⇒ premise-orphan problems, lazily
materialized (§9.8); uncovered observation-valued commitment ⇒
research problem; critic-gaming signal ⇒ audit-the-critic problem;
isolation above ﬂoor ⇒ connection problem; unrefuted artifacts on
overlapping problems with no declared relation ⇒ integration
problem.

Registration guards are warrant-validity conditions, not

censorship: they suppress noise, never criticism (P3). Anti-relapse:

a candidate hash-identical to a refuted artifact, or whose verdict-

vector over the active battery matches a refuted prior's, is blocked

unless it carries a warrant against that prior's refuter; near-

duplicates of unrefuted artifacts are never blocked (blocking them

would be a diversity gate adjudicating, violating C5). Trial guard: a

rubric verdict registers as a warrant only downstream of an

adversarial transcript (critic's case, defender's answer, ruling citing

a  decisive_point  that resolves to a real element of the
exchange), order-swap consistency for comparative modes, and

paraphrase spot-checks. Blocked rulings are logged; a streak of

blocks is itself a spawn signal.

6. Adjudication

Labels are computed in two passes; inputs are  att  and  dep only
(C5, C6).

# Pass 1 — attack (Dung grounded extension: unique, 

skeptical, polynomial)

F(X) = { a ∈ A : ∀(b,a) ∈ att, ∃c ∈ X with (c,b) ∈ 

att }

G    = least fixed point of F from ∅
label₀(a) = unrefuted  if a ∈ G
            refuted    if ∃b ∈ G with (b,a) ∈ att

            suspended  otherwise

# Pass 2 — support (over the dep DAG in topological 

order)

supported(a) = ∀(a,b) ∈ dep : final(b) = unrefuted

final(a) = unrefuted               if 
label₀(a)=unrefuted ∧ supported(a)
           suspended_unsupported   if 
label₀(a)=unrefuted ∧ ¬supported(a)
           refuted                 if 
label₀(a)=refuted
           suspended               otherwise

The label is named unrefuted, not "accepted," deliberately:

membership in the grounded extension means every attack on the

node is currently defeated — survival under the criticism so far

supplied, nothing stronger (P1, P2). The calculus has no stronger

word to offer and refuses to imply one.

Orphaned ≠ false. Refuting a premise renders dependents
suspended_unsupported , never  refuted : losing one's ground is
not being wrong. The distinction is load-bearing throughout §9.

Lemma 6.1 (Reinstatement). If k attacks a, j attacks k, and j is
unattacked, then {j, a} ⊆ G. Reinstatement is derived, never ruled.

7. Machine invariants

N1 (No absorbing status). Every label admits an exit:
unrefuted→refuted by new warranted attack; refuted→unrefuted
by reinstatement; demonstrative refutations reopen via attack on

their ν; rubric verdicts additionally via attack on their standard

(Closure 2); support-lost artifacts recover when their premises do.

No artifact — rules, standards, rulings, frame assertions included

— is ever ﬁnal (P1).

N2 (Perpetual proposability). γ's support is unbounded, and for

every unrefuted a there exist proposable successors with strictly

extended batteries (P10). §10 is N2's enforcement arm against

effective collapse.

N3 (No insolubility). No rule, label, or scheduler state asserts that

a problem cannot be solved. A problem leaves the frontier only by

adjudicated retirement, translation into a successor, or resolution

of its premises (§9.8); starvation of attention is a visible condition

of the schedule, never a verdict on the problem. That problems are

soluble is not a theorem the calculus proves; it is a state the

calculus refuses to be able to deny.

8. Measures

Demarcation. crit(a) ⇔ interface.commitments ≠ ∅; mod(a) ⇔ the
variation kernel µ(·|a) yields inequivalent variants with positive
probability; active(a) ⇔ crit ∧ mod. An artifact that forbids nothing
has an empty attack surface and fails the root battery by program;

an artifact whose mechanism is not load-bearing fails it equally

(P4). Both die before testing, which is where most bad ideas

should die.

Hardness to vary. Sample k bounded edits a′ ~ µ(·|a); s(a) = the

fraction that pass a's battery while being battery-inequivalent to a;

HV(a) = 1 − s(a). Where content parses structurally, µ must

substitute at role level — swap the mechanism, the scope, the

causal link — not merely reword (P9: a rename is the same

explanation). The estimating battery excludes HV-type

commitments (stratiﬁcation: HV over a battery containing itself

does not terminate). HV enters the graph only as a criterion inside

problems or as a spawn signal — never as a gate on registration

(C5).

Reach. Periodic budgeted cross-evaluation of unrefuted artifacts

against other problems' criteria. A hit — the artifact accounts for

material it was not built for, timestamped by the log to predate the

encounter, on held-out material where available — is the strongest

currency the calculus mints, and the promotion signal of §9.

Deﬁnition 8.1 (Knowledge, as a view).

knowledge(a)  ⇔  unrefuted(a) ∧ active(a) ∧ reach(a) 

> 0

— information that has survived the criticism actually supplied,

resists variation, and does work it was not built for. This is resilient

information: the mark of knowledge as that which, once

instantiated, tends to remain so and to propagate into problems it

was not made for — here realized as survival-plus-hardness-plus-

reach in the record. It is a view (C4) and an attention signal (C5),

never a status: promoting it to a label would reintroduce

veriﬁcation through the back door. And it is indexed: unrefuted

means unrefuted by the attack supply so far, while the

counterfactual ideal — resilience under all possible criticism — is

approximated, never attained, through hardness-to-vary and the

perpetual extension of batteries (N2).

9. Background: the standing layer

9.1 Two axes

Deﬁne status as above: truth-standing under criticism. Deﬁne

standing as an artifact's role in the economy of generation:

whether it is framed — one node among the packs' retrieved

neighbours and precedents — or does the framing: rendered

always, as the coordinate system every conjecture in a scope is

written in or declared against.

A single-axis calculus cannot host P11.

Proposition 9.1 (Rigidity dilemma). Suppose frame role is a

function of status, so that an accepted violation of a framework's

commitments removes its frame role. Then either (i) framing

toggles with the adjudication of each contested observation — and

since observation-acceptance is revisable (P5, Closure 3), framing

over the scope oscillates with every attack and reinstatement of

the evidence, re-orienting every open problem in scope at each

toggle; or (ii) the system prevents the toggle by delaying,

suppressing, or immunizing — violating P3, P5, or P1 respectively.
Proof: the alternatives are exhaustive. ∎

The two-axis state is also what the logic of experimental tests

demands. Refutation may be unilateral: one accepted violation

ends a universal claim, and no rival need exist for it to do so.

Theory-choice may not: a crucial test is intrinsically comparative,

requiring rival explanations of the total record — the apparatus's

own account included — and a framework is rationally displaced

only by a better explanation of everything it explained, its wounds

now among the explananda. The status axis carries the ﬁrst; the

standing axis carries the second; a single axis must garble one

into the other. The result is the ordinary condition of mature

knowledge — refuted and still framing — which is precisely

background held unproblematic for the occasion while remaining

under open indictment.

9.2 Frame assertions; standing as a view

Deﬁnition 9.2 (Frame assertion). A frame assertion is an ordinary

artifact fa whose content is a frame claim

⟨ subject b,  scope σ,  validity v,  departure 

protocol ⟩

σ : a total computable predicate over problem records   

(C1: deterministic;

     embeddings may inform nomination, never 

membership)

v ∈ { universal,  bounded(domain, tolerance) }

with interface refs: mention → b; dependence → each reach
record cited as its case; mention → the wounds of any incumbent
it succeeds. fa is consulted iff it is addressed to a promotion

problem (§9.4) and ﬁnal(fa) = unrefuted.

Deﬁnition 9.3 (Standing — derived, never stored).

standing(b) ⊒ background over σ  ⇔  ∃ consulted fa :

      subject(fa) = b  ∧  scope(fa) = σ  ∧  final(fa) 

= unrefuted

Instrument standing is not a third value: it is a consulted fa whose
validity is  bounded  — the subject frames its granted domain as a

declared approximation, with the tolerance authored by its

successor and attackable like anything (C3: the distinction is

content, not type).

Law 9.4 (Mention law). A frame assertion MUST NOT carry a

dependence ref on its subject. This single interface constraint is

the whole separation of the axes: because fa merely mentions b,

Pass 2 does not drag fa down when b is refuted — the wound does

not touch the frame role. Because fa depends on its reach case,

refuting that case cuts fa's support. Truth-standing and frame-

standing are thereby decoupled at the level of edge roles, and both
remain fully inside  att / dep .

Whether a refuted subject ought to keep framing is itself a

conjecture: attack fa directly. That argument is the succession or

revocation case — adjudicated, never hardcoded.

9.3 Rent

Promotion is purchase of exposure. The subject's expectation set

is its commitment set, and demarcation (§8) is the rent law: a

candidate background must be active(b), with observation-valued

commitments wherever its scope is empirical. Its commitments

are held open indeﬁnitely and checked against every relevant

episode; the background tier is therefore the most falsiﬁable-in-

practice position in the calculus, not a shelter (P11). A framework

that cannot state what it forbids, or whose mechanism carries no

weight, cannot frame — it fails the root battery before the question

of standing arises. And promotion is an articulation event: a tacit

framework becomes promotable only when factored into

vocabulary, enumerated assumptions, and commitments —

because the assumption ids are what departures declare against,

and the commitments are what wounds violate. Articulation is not

overhead; it is the manufacture of the attack surface.

9.4 Nomination and promotion

Nomination is a measure-rule over the log (channel (a) of C5):

reach events for b spanning at least K_frame distinct problem
lineages that jointly match a coherent candidate scope ⇒ Spawn
a promotion problem. The measure detects; it never decides.

Promotion is an ordinary Conj → Crit → Adj pass: a frame
assertion is proposed addressing the promotion problem, whose

criteria pin — beside the root battery —

1. subject-demarcation (program): active(b), observation-valued

where empirical (§9.3);

2. reach-integrity (program over the log): the cited reach records

exist; timestamps prove held-out standing where claimed;

3. scope-determinism (program): σ evaluates on problem

metadata alone;

4. compatibility: an unrefuted consulted frame assertion

overlapping σ routes this problem to discrimination against it

(§9.7) — rivals never co-frame;

5. accounts-for (succession only): the candidate's subject covers

the incumbent's standing fail verdicts, program-checked

against the wound list with anchored-rubric backup.

Remark 9.5 (Default-consult closure). Grounded semantics labels

the unattacked unrefuted, so an unchallenged frame assertion

would otherwise frame its scope the moment it registered. Two

native facts close the hole: the criteria above are instantiated at

registration and generate demonstrative program warrants before

the renderer's next consultation (Adj follows every registration);

and the renderer consults only assertions addressed to promotion

problems, which exist only by Spawn. A frame assertion born

anywhere else is an ordinary artifact the renderer ignores.

Revocation requires no rule of its own: attack the reach records

("contaminated", "shallow", "not held-out") and fa loses support —

ﬁnal(fa) = suspended_unsupported (§6), and the renderer stops

consulting it. Orphaned ≠ false does exactly the right work:

revocation says unearned, not wrong.

9.5 Frame render semantics

The pack — the deterministic render each γ-call receives —

comprises the problem and criteria, the target and its top

attackers and defenders, the retrieved neighbourhood, the

precedent slice, and, for every consulted fa whose σ matches the

problem, the frame slice:

the subject's articulation digest (compressed; expandable by

view), and

the subject's standing attackers. Wounds render in-frame, in

every pack in scope.

The frame ships its own crisis. This is P11's searchlight with its

hand shown: background conditions generation and displays its

open indictments at the site of conditioning. Crisis is a render

state, not a mode switch — the pressure toward rivals is applied at

the only surface the calculus controls, namely what the generator

is shown.

Departures. The frame slice carries a standing directive:

departures are permitted and must be declared, as a list of the

subject's assumption or commitment ids the candidate breaks

with. Declaration removes the hidden-premise criticism's target

(an undeclared conﬂict with the frame is criticizable as a silent

assumption); the declaration is itself attackable (defend the

assumption); and a departer that later reaches is routed by

nomination to discrimination against the incumbent. Nothing

scores departures, because no penalty channel exists to score

them with — the freedom is by construction, not by rule. Scope

predicates never read departure declarations: a departing

conjecture cannot be exiled from the frame it is criticizing.

9.6 Wounds

A wound is nothing new: a fail verdict on one of the subject's
observation-valued commitments ⇒ demonstrative warrant ⇒
attack edge ⇒ Pass 1 computes refuted. The observation is itself
on trial throughout (P5): its warrant's ν carries an evidence ref, and

an accepted attack anywhere in the evidence's dependence

lineage collapses the warrant and reinstates the subject (Closure

3) — the faulty instrument, computed.

Proposition 9.6 (Wound persistence). A wound changes status(b)

and does not change standing(b). Proof: the attack targets b; fa

carries no dependence on b (Law 9.4), so Pass 2 leaves fa's label
untouched; the renderer keys on ﬁnal(fa). ∎

The failed verdict spawns a successor problem as always; under a

consulted fa that successor is the crisis problem — a standing,

addressable demand for an account of the wound — while the

wound renders in-frame across the scope (§9.5). Newton between

1859 and 1915 is the intended model of this state: status-refuted,

standing-background, perihelion on display in every pack,

succession wanted.

9.7 Falls and succession

Standing ends in exactly two ways, and the two-pass labels

distinguish them without new machinery:

Event

Mechanism

ﬁnal(fa)

Fall

succession

refuted

lost, or a

direct

warranted

attack on

Cascade

grade

premise-

refuted

Event

Mechanism

ﬁnal(fa)

Cascade

grade

fa

sustained

reach case
refuted ⇒
support cut

Revocation

suspended_unsupported

premise-

unaccredited

Both end consultation; the labels differ, and §9.8 inherits the

difference.

Succession is discrimination. Rival frame assertions over

overlapping scope trigger the ordinary ≥2-survivors discrimination

spawn, resolved comparatively — as the comparative logic of §9.1

requires: pairwise ruling, cited decisive point, mandatory order-

swap — the calculus's native symmetry instrument. One render

exception is proper to succession: the succession pack

suppresses the incumbent's frame slice and renders both

articulation digests, so the trial of a frame is framed by neither

party. The failure this mitigates deserves its name — incumbent-

judge bias: a succession posed inside the incumbent's vocabulary

is adjudicated by the defendant. The mitigation is symmetric

exposure; a view from nowhere is not on offer.

Anomaly conservation. Nothing is deleted (P8), and the accounts-

for criterion makes the successor claim the incumbent's wounds

as its own commitments — attackably: the new frame must predict

what broke the old one. Its scope statement must also ﬁx the

incumbent's residual validity domain; succession may therefore

leave a residual bounded-validity frame assertion for the fallen

subject, which thereby keeps framing its granted domain as a

declared approximation — instrument standing (Def 9.3). The

predecessor's domain of validity is authored by its successor, and

that authorship is one more attackable claim.

9.8 Presupposition and the cascade

Problems posed under active background record the fact (Def 3.5:
provenance.frame , deterministic at registration, registrant-
editable at pose, immutable after). Presupposition is provenance:

epistemically inert, steering spawn and attention, never labels —

the frame can orient the searchlight without ever voting in court.

When a consulted fa leaves unrefuted standing (either grade), a

replay program enumerates every problem carrying it and marks

each premise-orphaned. Marks are lazily materialized: the orphan

problem instantiates when its problem is next focused, and batch

translation offers may materialize groups — the fall is one event;

its thousandfold consequence is paid as the frontier is touched,

not all at once. Pending marks deprioritize their problems in

scheduling (attention only, C5).

Each orphan problem admits exactly three resolutions:

1. retire — the problem leaves the frontier, logged, never deleted:

it died with its premise;

2. translate — a successor problem is posed in the succeeding

frame's vocabulary, provenance recording the lineage:

succession lives on the problem layer;

3. independence — a ﬁnding that the problem never needed the

premise; the orphan closes with that holding and the scheduler

thereafter treats the problem as unorphaned (computed from

the resolution; the problem's provenance is never mutated).

The independence-resolution rate doubles as the over-binding

diagnostic on pose-time recording.

Fall-grade orphans carry premise refuted; revocation-grade carry

premise unaccredited; neither auto-kills — orphaned ≠ false

operates at the problem layer exactly as at the artifact layer, and

none of the three resolutions is an insolubility verdict (N3): a

problem dies with its premise, moves to better language, or stands

free of both.

Proposition 9.7 (Cascade totality). Every problem whose

provenance carries fa receives an orphan mark when fa leaves

unrefuted standing; no presupposing problem silently survives,

and no mark resolves except by adjudicated work. Proof: marking

is a total computable function of the log; resolutions exist only as
registered problem-closures. ∎

Here is the asymmetry P11 demands, now mechanical. An

ordinary refuted conjecture retires nothing but itself, because

nothing presupposes it. A fallen background's refutation is a

premise-criticism of everything posed in its terms: one fall retires

a thousand questions, translates a thousand more into a better

vocabulary, and reveals some hundreds that never needed the

premise at all — which is how the succession of frameworks

becomes the succession of problems (P7).

9.9 Authority audit

Standing is render authority and nothing else. It is derived, never

stored (C4); it is content and edge-structure, never a type (C3); it

appears in packs and schedules, never in label computation (C5,

§6); every object realizing it — the frame assertion, its reach case,

its subject's commitments, the succession rulings — is attackable

and reinstateable (N1, P6). Methodological privilege without

epistemic privilege: the background frames every conjecture in its

scope and can be dragged into court by any of them.

10. Generation and effective openness

The generator γ is a bounded pure function from packs to schema-

valid candidates; it holds no state, adjudicates nothing, and

controls no ﬂow (P2: conjecture is unconstrained guessing; P6:

the guesser has no authority). Each call returns a distribution of

candidates with stated typicality rather than a point — eliciting the

tails that mode-seeking suppresses. Typicality is a statistic of the

generator's distribution and nothing more: it prices attention and

never weighs truth (C6). Every conjecture is born connected: packs

carry the target's neighbourhood, and candidates are invited to

declare relations, so uniﬁcation is discovered by reach rather than

designed (C5: coupling is a property of generation; reach is its

measured shadow).

γ is a role, and the calculus is agnostic about its realization up to

the contract. Nothing here presumes the generative side lies

beyond computation: physical processes are computable, minds

are physical, and a system that created explanatory knowledge

would be a program. On the evolutionary account of knowledge

there is no third ingredient — creation is conjecture and criticism —

so this calculus is best read as the error-correcting half of exactly

such a composite: selection formalized in full, generation

constrained only in its direction. Problem-pressure,

neighbourhoods, complements, and elicited tails say where

variation is aimed; they are silent on how novelty arises. Absent a

theory of that remaining half, the calculus licenses no claim in

either direction: forced variation must not be advertised as

creation, and creation must not be declared uncomputable. Both

errors are refusals to say we do not yet know.

P10's honest gap: in-principle openness survives any conditioning,

but a conditioned generator's effective support can collapse into a

basin — and a frame slice is deliberate, scope-wide conditioning,

the strongest the calculus ever applies. The countermeasures are

attention-side by constitution: population structure in conjecture

(persistent conditioning regimes diverging by their own lineages)

with panmixia in criticism (one court; attacks cross lines freely);

capture detection as replay programs over the log — stream

contraction, attack-target entropy, criticism debt, reinstatement

rate, validity-node attack rate; responses that reweight rendering

and budgets with hysteresis, never statuses. Promotion events are

logged with before/after conditioning diagnostics: the capture

cost of elevation is measured, not vibed. And because these

instruments detect stalled dynamics, not wrong-but-stable ones,

the calculus keeps a ﬂoor under its exogenous grounding ratio —

the fraction of verdicts bottoming out in program checks, recorded

evidence, and appellate rulings rather than closed-loop judgment.

A background that is conﬁdently, quietly wrong generates no

wounds; only the anchors outside the loop bear on it.

11. Informal content

Informal domains enter through structure, never through types

(C3). Candidates parse to a skeleton — claim, mechanism, scope,

forbidden cases — and each forbidden case compiles at

registration into a commitment: explanatory demarcation made

real for prose (P4), with the judge's question shrunk from "is this

good?" to "does case X violate clause Y?". The mechanism slot is

load-bearing by the root battery, so a skeleton whose mechanism

swaps freely is refuted by program, untested. Rubric evaluation

resolves against standard artifacts — rubric text, evaluation mode,

exemplars with holdings — which are ordinary artifacts:

attackable, succeedable, and wired into Closure 2, so the

productive attack in informal domains lands on the standard and

its success reinstates every target judged under it, in one

computed pass. Comparative rulings (anchored or pairwise, order-

swapped, decisive-point-cited) replace absolute scoring; judge

behavior is program-audited — paraphrase invariance, premise-

deletion sensitivity, planted-ﬂaw calibration — and audit hits enter

as ordinary demonstrative warrants against the relevant validity

nodes: formal machinery criticizing informal machinery with the

full force of the graph. Human rulings enter as precedent artifacts

ranked ﬁrst in render and attackable like anything: authority is

pack ordering, never status privilege (P6). A share of the evidence

corpus is registered sealed with scheduled reveals; a pass on

revealed material is a reach hit with the strongest provenance the

informal side can produce, the log's timestamps proving the

artifact predates its evidence — the novel-fact criterion,

mechanized.

12. Properties

Proposition 12.1 (Total computability). Every verdict is decidable

within its declared budget (C2); Pass 1 is a least ﬁxed point of a

monotone operator on a ﬁnite lattice, polynomial in |att|; Pass 2 is
a single topological traversal of  dep ; standing is a query over
labels; every view is a pure fold over the log (C1). No judgment in
the calculus invokes an undecidable question. ∎

Proposition 12.2 (No conﬁrmation, no credence). The only

evidence-bearing edges in the calculus ground attacks (Def 3.4,

Closure 3): there is no derivation by which evidence raises any

artifact's label, and no probability over any artifact's truth appears

in label computation, measures, or scheduling weights on truth

(C6) — generation statistics price attention only. What remains of

"support" is exactly membership in the grounded extension with

intact premises — survival (P2, P3), with the Popper–Miller

decomposition standing guard against its probabilistic re-
description. ∎

Theorem 12.3 (No absorbing status). Under N1, every label of

every artifact is revisable by a constructible registration: unrefuted

falls to a fresh warranted attack; refuted reinstates by attacking

the refuter, its validity node, its standard, or its evidence lineage;

suspended_unsupported recovers with its premises. Frame

assertions inherit all exits, and their subjects hold an additional

permanent exposure through open observation-valued

commitments (§9.3). Sketch: each exit names a registrable object

whose adjudication ﬂips the label by §6; none is blocked by any
guard, since guards are warrant-validity conditions only. ∎

Proposition 12.4 (Axis independence). Status(b) can change

without standing(b) changing (Prop 9.6), and standing(b) can

change without status(b) changing (revocation attacks fa's reach

case, not b). The axes are decoupled exactly by edge roles, inside
att / dep . ∎

Proposition 12.5 (Standing never adjudicates). Label computation
reads  att  and  dep  only (§6); standing is consumed by render
and schedule alone. Hence background confers no inferential

weight: P6 and C5 are preserved under the standing layer, and
P11's privilege is methodological in the strict sense. ∎

Proposition 12.6 (Knowledge is a view). knowledge(a) (Def 8.1) is

a total computable function of the log, consumed only by

attention. It can rank, focus, and report; it cannot move a label. The

characterization of knowledge as resilient, reaching information is

thereby available to the machine without ever becoming a
veriﬁcation predicate. ∎

13. Limits, stated

The calculus guarantees faithful bookkeeping — computable

statuses, reinstatement, preserved error, replayable history,

background that frames without ruling — and formalizes the

selective half of the growth of knowledge while leaving the

generative half as a role. That division is a statement of what has

been theorized, not of what is possible: the whole process is

computable in principle, and a generator that created explanations

would complete the composite this calculus is built to correct.

Until such a theory exists, forcing variation is not producing

creativity and is not advertised as such. Hardness-to-vary at small

k is a spot-check standing on kernel-quality assumptions parked,

visibly, in validity nodes. Informal verdicts are made narrow,

comparative, precedent-anchored, and audited — not reliable.

Capture instruments detect stalled dynamics; a consensus

ossiﬁed around a shared blind spot is invisible from inside, and

only the exogenous anchors bear on it, which is why the grounding

ﬂoor is load-bearing rather than decorative. Nomination

thresholds, scope predicates, slice budgets, and orphan

scheduling are empirical constants; both failure directions are

measurable from the log, and none is defended here. Succession

neutrality is symmetric exposure, not neutrality. And a wounded

background with no arriving rival frames forever — refuted,

indicted in every pack, unreplaced, and never declared

irreplaceable (N3). The calculus keeps the crisis visible and the

succession problem open; it cannot force the successor into

existence. That is not a gap in the machinery. It is what the growth

of knowledge is like.

