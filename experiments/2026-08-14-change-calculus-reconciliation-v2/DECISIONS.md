# DECISIONS — the batched sheet

Deliverable 3 / REQUEST.md R15, R24. Seven items. Everything the v2 design
needed beyond the operator's three pre-decided headline items is here, and
nothing here was decided unilaterally.

Each item: the decision in one sentence, why it cannot be settled from the
record, the options priced as roads (what you get, when, at what cost), and one
recommendation with its reason. **Every item can be answered with a word.**

## Which decisions block which rungs

| Decision | Blocks | Can wait until |
|---|---|---|
| ~~D-2 siren~~ **ANSWERED** — Road B, 2026-08-14 | — | closed |
| ~~D-7 signal park~~ **ANSWERED** — option (iii), 2026-08-14; placed at Rungs 1 + 1b | — | closed |
| **D-8** premise refutation by argument | nothing, on the recommended answer (D) — Rung 2 ships for category errors and formal falsity either way | before Rung 2 **only if** the answer is A |
| D-3 derived vs stored premises | **Rung 2** — the largest rung | before Rung 2 starts |
| D-1 crisis problem | Rung 3, then Rung 7 | before Rung 3 |
| D-5 scope predicate language | **Rung 4** | before Rung 4 |
| D-6 succession instrument | Rung 5 (criterion 5), Rung 7 | before Rung 5 |
| D-4 `knowledge` view | Rung 5 | before Rung 5 |

**Status, 2026-08-15: ALL SEVEN ARE ANSWERED AND CLOSED.** The operator
answered D-1, D-3, D-4, D-5 and D-6 as **A** (every recommendation), D-2 as
Road B, and D-7 as option (iii). Only **D-8** — added by Amendment 1, and not
yet put to the operator — remains open, and it blocks nothing: its recommended
answer is "defer, decide on evidence".

| # | Answer | Where it lands |
|---|---|---|
| D-1 | **A** — crisis is a render state only; no standing-layer spawn trigger | Rung 7 |
| D-2 | **Road B** — the operator's own siren case, in hand | Rung 2 |
| D-3 | **A** — premises are derived, not stored | Rung 2 |
| D-4 | **A** — ship `knowledge(a)`, always with its definition inline | Rung 5 |
| D-5 | **A** — a fixed finite DSL for σ, reusing `declarative_numeric_v1`'s shape | Rung 4 |
| D-6 | **A** — program-first `accounts-for`; judges optional, via the trial guard. **REFINED 2026-08-15 (R46): the program-checkable forms are §3.5's three `Superseded` criteria — recovery, rigidity, non-immunization — and `Refuted` / `Superseded` stay DISTINCT derived relations** (unilateral defeat vs comparative theory choice) | Rungs 5, 7 |
| D-7 | **(iii)** — the signal-contract design; 1b-i delivered, 1b-ii parked | Rungs 1, 1b |
| D-8 | open — recommended: defer, then revive `single_family_trial` on evidence | Rung 2's boundary |
| **ND-2** *(added by Amendment 4)* | open — recommended: **derived-view deactivation, exit episode retained** | Rung 2's cascade, enforced from Rung 4 |

**Rungs 1, 1b-i and 2 are delivered.** Two decisions are open — **D-8** and
**ND-2** — and neither blocks the next rung.

**A note on the numbering.** The operator's rider names this item **ND-2**. This
ledger contains no ND-1, and none has been supplied. The operator's numbering is
kept rather than compacted: inventing an ND-1 to close the gap would be
fabricating a decision nobody made, and renumbering would break the reference in
their own words.

---

## ND-2 — When a fallen premise is REINSTATED, what happens to the orphan mark?

**Why it needs a word.** The Formalization's §1 table records this as an
explicit gap: "the source leaves the restored-premise case underspecified; the
core formalization records the gap explicitly". Rung 2 shipped the cascade with
the mark DERIVED (`premise_orphaned` is a pure function of replayed state), so
today reinstating the premise silently un-marks the problem — the exit ever
having happened leaves no trace on the problem. That is a defensible answer and
it is also an unrecorded one, which is the part worth a decision.

| Road | What you get | Cost | Risk |
|---|---|---|---|
| **A. Derived-view deactivation, exit episode RETAINED** *(recommended)* | The mark deactivates the moment the premise stands again — nothing to adjudicate, nothing to clean up — while the EXIT EPISODE stays in the log as a first-class record: this problem was orphaned, by this attribution, from this seq to that one | ~40–70 lines: the episode is already implicit in the event log; what is added is a derived reader that surfaces it | A reader who asks `premise_orphaned` and sees nothing may conclude nothing ever happened. Mitigated by making the episode reader part of the same module, not an optional view |
| **B. A fourth resolution, `revalidate`** | An explicit adjudicated act closes the orphan when its premise returns, symmetric with retire / translate / independence | ~120–200 lines, and every reinstatement now REQUIRES an act before the problem is workable again | Contradicts D-3's answer (premises are derived, not stored) and C4 (statuses are computed, never stored). It also re-introduces an acceptance-shaped event on a layer whose whole design is that nothing is accepted — v0.1 §6, "no acceptance event" |

**Recommendation: A.** It is the only road consistent with two answers already
given: **D-3** (premises are derived) and **C4** (statuses are computed from the
log, never stored). B would make the orphan mark the one stored, act-requiring
status in a calculus that has none, and it would do so to record something the
append-only log already contains. Retaining the exit episode answers the real
worry behind B — that a reinstated problem should not look as though it was
never in trouble — without buying a fourth resolution to get it.

**Reversible if wrong:** yes, cheaply. If live evidence shows reinstated
problems being re-worked as though nothing happened, B can be added later as a
resolution over the retained episodes; nothing in A forecloses it.

---

---

## D-1 — Under H1, is the crisis problem a render state only, or does it get its own trigger?

**Why it needs a word.** H1 deletes the clause that minted the crisis problem
(§9.6: "The failed verdict spawns a successor problem as always; under a
consulted fa that successor is the crisis problem"). Something has to carry the
"standing, addressable demand for an account of the wound", and the two
candidates sit on opposite sides of the line H1 just drew.

| Road | What you get | Cost | Risk |
|---|---|---|---|
| **A. Render state only** (+ the incumbent's promotion problem stays on the frontier, ranked up by wound count — attention only) | The wound renders in every pack in scope; a rival frame assertion addressing the same promotion problem triggers ordinary discrimination | **zero extra work** — Rung 7 renders wounds anyway | If nobody ever proposes a rival, there is no object anyone is working on. This is precisely §13's own honest residue ("a wounded background with no arriving rival frames forever") |
| **B. A standing-layer spawn trigger** — consulted assertion with ≥1 unrefuted standing attacker ⇒ crisis problem over σ | A real problem on the frontier that the scheduler ranks like any other | ~80–120 lines in Rung 7, plus one more auto-minting trigger on a frontier that already reached 2 894 problems on one root | Re-introduces the shape H1 deleted — a failed verdict minting a problem — one layer up. Defensible (the subject is background, not a candidate), but it is the same shape |

**Recommendation: A.** H1's content is "stop minting problems from failures",
and §9.5 already calls crisis a render state in the calculus's own words. A is
also reversible with evidence: if a live fall shows nobody addresses the
promotion problem, B becomes a small follow-on rung with a measurement behind
it. Choosing B first would be choosing it without one.

---

## D-2 — ANSWERED (2026-08-14): Road B

The original is ledgered in REQUEST.md Amendment 1 (R25–R28). π₁ = *"What is the
colour of a siren?"*, X = *"a siren is the kind of thing that has a colour"* — a
category error, no instrument or measurement anywhere, X refuted by argument
alone, and **no conjecture on π₁ ever proposed**.

The Doppler reconstruction is superseded and has been replaced, not annotated
(`RECONCILIATION.md` §1/H2). Two things changed beyond the example's content:

1. **The sequence lost a move and gained a stronger claim.** It no longer needs
   a candidate to be proposed on π₁ at all — which is what "fundamentally flawed
   before even receiving an answer" requires — and it no longer routes through
   an observation, an evidence artifact, or the faulty-instrument reinstatement.
   Move 4 refutes X for **explanatory emptiness**: a category error forbids
   nothing, so the demarcation criterion fails by program, and the critic's
   category-error argument is carried as the content of the warrant's validity
   node. The argument does real work without ever becoming a self-certifying
   prose warrant.
2. **It surfaced D-8.** Your example runs on a solo configuration under the
   shipped defaults — but only because "refuted by argument" and "refuted by
   demarcation" coincide for a category error. For a premise that is contentful
   and merely wrong, they do not, and the harness has no solo road. That is the
   new item below.

---

## D-3 — Is a problem's premise derived, or stored as the calculus writes it?

**Why it needs a word.** This is the one place where the v2 design deliberately
deviates from the calculus's literal text. Def 3.5 stores `provenance.frame` on
the problem, "written deterministically at registration, editable by the
registrant at pose, immutable thereafter".

| Road | What you get | Cost | Consequence |
|---|---|---|---|
| **A. Derived** — `provenance.frame` becomes a view over premise attributions | A critic can register a **hidden** presupposition at any later time | zero stored-record change; no widening of any committed record | Deviates from Def 3.5's text |
| **B. Stored**, exactly as written | Literal fidelity to the calculus | one additive field on `ProblemProvenance` (old records default; problem ids are not content-addressed, so nothing moves) | **Forbids the thing H2 asks for**: "immutable thereafter" means a presupposition nobody noticed at pose time can never be recorded |
| **C. Both** — store at pose, derive for later additions | Fidelity plus late discovery | the union of A and B | Two sources of truth for one fact; against C4's spirit, and the first thing to drift |

**Recommendation: A.** Not on cost grounds — on grounds that B cannot express
your own requirement. H2's sentence is "a critic **may** register a problem's
hidden presupposition"; a pose-time-immutable field makes that impossible. A is
also strictly better on C4 (computed, never stored), which the calculus itself
has to apologize for in Def 3.5 by reminding the reader the field is inert.

---

## D-4 — Does the harness ship `knowledge(a)` as a user-facing view?

**Why it needs a word.** Def 8.1 defines `knowledge(a) ⇔ unrefuted ∧ active ∧
reach > 0` as a **view** that steers attention and never adjudicates. It is
cheap to build and safe by construction. The question is whether the harness
should say the word "knowledge" to a reader at all.

| Road | What you get | Cost | Risk |
|---|---|---|---|
| **A. Build it in Rung 5**, always rendered with its definition inline | The calculus's own characterization becomes inspectable and can rank attention | ~60–100 lines — it is a query over measures that already exist | Readers over-read it. There is a recorded precedent: v1.7 §E had to add the `adjudication-blindness` check because readers of `positions.accepted` were treating acceptance as adjudicated |
| **B. Defer** | Nothing now; addable at any time, since a pure view has no migration | zero | The characterization stays invisible; attention keeps steering on raw HV/reach |

**Recommendation: A, with the H3 discipline attached** — the view never prints
the bare word; it prints "knowledge (unrefuted ∧ active ∧ reach > 0)". That is
the same fix H3 applies to `accepted`, applied before the misreading happens
rather than after.

---

## D-5 — What language expresses a scope predicate σ?

**Why it needs a word.** §9.2 requires σ to be "a total computable predicate over
problem records", deterministic, with "embeddings may inform nomination, never
membership". It does not say in what language, and the answer sets the size of
Rung 4.

| Road | What you get | Cost | Risk |
|---|---|---|---|
| **A. A fixed finite DSL** — a small JSON expression language over problem metadata, compiled by the harness | Determinism and replay-stability by construction; trivial budgets | ~150–250 lines inside Rung 4 | Expressiveness ceiling; some scopes will be awkward to state |
| **B. An arbitrary program artifact** | Any scope statable at all | Much larger: sandbox, budgets, a determinism story, and the whole risk surface of executing authored code at *membership* time | The tree already refuses model-authored Python without a certified container (v1.6, `sandboxed_python_v1` fails closed). Choosing B imports that refusal into scope membership |

**Recommendation: A**, and reuse the shape this repository has already solved
once: `declarative_numeric_v1` (v1.6) is exactly a finite JSON expression
language compiled into harness-authored Python. Building the second one costs
less than designing the first did, and it inherits a proven determinism story.

---

## D-6 — Succession is comparative; you distrust judges. Which instrument?

**Why it needs a word.** §9.7 resolves succession by discrimination — "pairwise
ruling, cited decisive point, mandatory order-swap" — which is judge-shaped. Your
standing law says a solo run with everything on must be an option, and that
judge seats "prosecute without any discernable discrimination". The calculus
itself offers the escape in §9.4 criterion 5: `accounts-for` is "program-checked
against the wound list with anchored-rubric backup".

| Road | What you get | Cost | Risk |
|---|---|---|---|
| **A. Program-first `accounts-for`; judges optional** — the wound list is machine-derivable (the incumbent subject's failed observation-valued commitments), so coverage is program-checked; a rubric ruling is admitted only through the existing trial guard, and only when a wound has no program-checkable form | Succession works solo, with no judge seat required anywhere | Rung 5 builds the wound-list program (~120 lines) | A wound whose account is genuinely prose-shaped falls back to a rubric, and rubrics are what you distrust — but it falls back *visibly*, through the trial guard |
| **B. Require a cross-family judge ensemble**, order-swapped | Closest to §9.7's letter | Rung 5 and Rung 7 both gain an ensemble requirement | Locks solo out of succession entirely — a direct collision with your standing law |
| **C. Defer succession** until a live fall exists to measure | Nothing decided prematurely | Rung 7 ships falls without succession | A background can fall with no road to being replaced; §13's residue becomes the only outcome |

**Recommendation: A.** It is the only road that satisfies your solo law without
weakening the calculus's comparative requirement — the comparison still happens,
it is just adjudicated by a program wherever a program can adjudicate it, which
is also the harness's own standing preference ("prefer `eval:program|predicate`
over `eval:rubric` wherever content is formal", v1.3 §9).

---

## D-7 — ANSWERED (2026-08-14): option (iii), design supplied

The signal-contract design was never in this repository — which is why the
search below could not find it, and why the honest answer at the time was
"not found" rather than a guess at one of the two near-misses.

The six clauses are ledgered verbatim in REQUEST.md Amendment 2 (R29–R36),
reconciled as drift rows **SC-1 … SC-6** in `RECONCILIATION.md` §2L, and placed
on the ladder.

**Placement, which you delegated to the drift table (R36): its own rung —
Rung 1b — with clause (6)'s CLAUDE.md design law folded into Rung 1.** Your
"fold into 1+4" was half right, and it is the *ledger* half that folds. Three
reasons, argued in full in §2L:

1. The registry must become a contract **before** the rungs that emit new
   signals — Rung 2 onward, and Rung 8's promotion diagnostics. Your own clause
   (1) says new setups add signals by declaration through the channel; that only
   holds if the channel exists first. Placed at Rung 4, every v2 signal would be
   a retrofit.
2. Its blast radius is disjoint from the standing layer's. Folding it into Rung
   4 would put two unrelated gates in one tranche — the same objection that
   earned the spawn-trigger deletion its own rung.
3. The INV document's **checks** cannot precede the mechanism:
   `docs_verify --audit` refuses checks that cannot fail, so an INV document
   about an unbuilt mechanism ships vacuous checks. Law text in Rung 1;
   document, both recipes, and the mechanism in Rung 1b.

**Three things in your design are already substantially built**, which is why
the rung is 450–650 lines rather than a rewrite: `cap_envelope`/`clamp` are the
FREE layer's envelope bounds; `_policy_payload` already reads the policy from a
registered artifact, which *is* policy-as-recorded-artifact; and `config_referee`
(v1.7 §F) is the referee the VERSIONED layer names. Clause (3)'s boundary also
already holds — `controller.py` imports only `deepreason.ontology` — so the
architecture test pins it rather than forcing a refactor.

**One thing your design will collide with, flagged not decided:**
`controller.py` already uses "standing" to mean *under unresolved attack*
(`_under_standing_attack`), while the calculus uses it for *frame role*. Rung 1
renames the controller's private predicate; nothing stored moves.

### The original question, retained for the record

**Why it needs a word.** The brief names four parks the v2 program should
absorb. Three resolve exactly (P4, P5, P6, all in
`experiments/2026-08-13-change-lifecycle-operation-parity/PARKED.md`). The
fourth does not exist under that name. Searched: every `PARKED.md` heading in
`experiments/`; every `.md` in the tree for `signal[- _]contract`,
`signals contract`, `contract of signals`; the model-signal contract of v1.5 §H
(`stuck` / `complete` / `need_context` / `capability_mismatch`); and the signal
REGISTRY.

| Candidate | What absorbing it would mean |
|---|---|
| **(i) the signal registry** — `src/deepreason/signals.py`, "every measure tag the harness emits, documented once", AST-enforced by `tests/test_signals.py` | Every signal the v2 program emits is registered there as it is introduced. **Rung 1 already carries this**, on the assumption that it is the intended one |
| **(ii)** `experiments/2026-08-13-change-results-retrieval-surface/PARKED.md` P2 — the map owns no top-level reader module, and names `signals.py` among them | The v2 program would owe a map document covering the reader modules |
| **(iii) something not in the tree** | Paste it and it gets a rung |

*(Answered above: (iii). Candidate (i), the existing 89-tag registry, turns out
to be **included** by clause (1) rather than superseded, so the provisional
assumption Rung 1 was proceeding on was compatible with the real answer.)*

---

## D-8 — What refutes a premise that is wrong by argument, but is not a category error?

*(Added by Amendment 1. Drift row W-1.)*

**Why it needs a word.** Your siren case is safe: a category error forbids
nothing, so demarcation kills it by program, and **demonstrative outcomes are
status-changing under every authority mode** (`rules/crit.py`). But the premise
channel's general case is a premise that *does* forbid something and is simply
false — and there, the shipped harness has no solo road:

- `ADJUDICATION_STATUS_AUTHORITY_ENABLED` defaults **False**, and
  `ARGUMENTATIVE_AUTHORITY` defaults **`observe_only`** — an argued case records
  scrutiny and creates no attack edge.
- `trial_required` works, but routes through the **defended cross-family
  trial** — two model families, so not a solo run.
- `single_family_trial` exists as a config value and **cannot complete a
  trial**: the direct-helper path supplies no critic school, and the v4 envelope
  demands a manifest-bound authority value. It is parked as dead weight
  (`CON-schools.md` Traps).

So today, on a solo run, a false-but-contentful premise cannot be refuted at
all, and the cascade never fires for it. This is not a code accident: it is the
deliberate suspicion of prose verdicts that runs through §10, the
`adjudication-blindness` check, and your own standing wariness of judges.

| Road | What you get | Cost | Risk |
|---|---|---|---|
| **A. Revive `single_family_trial`** — the defended trial, critic and defender drawn from the same family, order-swap and decisive-point checks intact | Argument-only refutation on a solo run, through the existing trial guard; the cascade works for every premise, not only category errors | The park calls it "a behavior decision, not a refactor": wire `critic_school_id` on the direct-helper path, or admit the mode through the envelope. Estimate ~150–250 lines, its own tranche before Rung 2 | A same-family critic and defender share the model's blind spots — the trial is procedurally real but the adversary is the defendant's twin |
| **B. Leave it demonstrative-only** — premises fall by demarcation, by a failing formal commitment, or not at all | Nothing to build; the strictest possible reading of "no self-certifying prose warrant" | zero | The premise channel works for category errors and formal falsity, and is inert for ordinary substantive error — which is most of it. Your "problems are first-class subjects of criticism" doctrine then holds only for the flawed-before-answering case |
| **C. Require cross-family** (`trial_required`) for premise refutation | The strongest adversary the harness can field | zero to build | Locks solo out of the premise channel — a direct collision with your standing law that a solo run with everything on must be an option |
| **D. Defer** — ship Rung 2 for category errors and formal falsity, measure how often a live run wants to refute a premise by argument, then decide | Rung 2 is unblocked immediately; the decision gets evidence | zero now | The channel ships knowingly partial, and "partial" is easy to forget once it is green |

**Recommendation: D now, A next.** Rung 2 does not need this answered to ship
the operator's own example, and deciding it without evidence would be guessing
at how often premises fail by argument rather than by emptiness — a number a
live run produces cheaply. But A is the road I expect the evidence to point to,
because it is the only one that keeps both of your standing laws intact at once:
a solo run can do everything, and no prose verdict certifies itself. If you
would rather not wait, answer **A** and it becomes a tranche before Rung 2.

---

## What happens after you answer

Rung 1 opens as its own tranche (`dr-change-orchestrator`, one rung per tranche),
carrying your answers into its REQUEST.md. Nothing in this tranche touched code,
and no frozen surface was contacted.
