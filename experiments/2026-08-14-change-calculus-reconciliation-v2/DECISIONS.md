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
| D-2 siren, D-7 signal park | Rung 1 (documentation only) | Rung 1's REQUEST.md |
| D-3 derived vs stored premises | **Rung 2** — the largest rung | before Rung 2 starts |
| D-1 crisis problem | Rung 3, then Rung 7 | before Rung 3 |
| D-5 scope predicate language | **Rung 4** | before Rung 4 |
| D-6 succession instrument | Rung 5 (criterion 5), Rung 7 | before Rung 5 |
| D-4 `knowledge` view | Rung 5 | before Rung 5 |

Rung 1 can start on D-2 and D-7 alone. Nothing is blocked on all seven.

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

## D-2 — Confirm the reconstructed siren case, or supply the original

**Why it needs a word.** Your doctrine names the siren example; the tranche brief
does not quote it, and it appears nowhere in this repository
(`grep -rni siren --include=*.md .` returns nothing outside this tranche).
`RECONCILIATION.md` §1/H2 reconstructs the canonical Doppler-shaped case —
π₁ = *"Why does the siren's pitch drop as the ambulance passes?"*, presupposing
X = *"the emitted pitch falls"*, X refuted by a source recording, π₁ then
retired / translated / found independent — and marks it a reconstruction.

| Road | Cost |
|---|---|
| **A. Confirm the reconstruction** | zero |
| **B. Supply the original** | one paste; the eight-move sequence is unchanged, only the content of X moves |
| **C. Drop the named example** | zero, and nothing is lost mechanically — the move sequence is example-independent — but the doctrine loses its worked case |

**Recommendation: A or B, whichever is less work for you.** The design does not
depend on it; the documentation does.

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

## D-7 — Which park was "the signal-contract park"?

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

**Recommendation: tell us which, in a word.** Rung 1 proceeds on (i) meanwhile,
because it is the cheap half and it is certainly required either way — a new
signal that is not registered fails the existing test.

---

## What happens after you answer

Rung 1 opens as its own tranche (`dr-change-orchestrator`, one rung per tranche),
carrying your answers into its REQUEST.md. Nothing in this tranche touched code,
and no frozen surface was contacted.
