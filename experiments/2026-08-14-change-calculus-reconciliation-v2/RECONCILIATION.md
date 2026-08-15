# RECONCILIATION — the Computable Calculus vs. the shipped harness

Deliverable 1 of the v2 reconciliation tranche (REQUEST.md R13–R15, R20–R22).
Design only; no code was changed and no frozen surface was touched (R2).

**What this document is.** A row for every place the three authorities say
different things, or where one is silent and another is not. The three
authorities:

| Column | Authority | File |
|---|---|---|
| **CALCULUS** | operator-supplied theory | `docs/COMPUTABLE_CALCULUS.pdf` (governs) / `.md` (searchable extraction) |
| **SPEC** | the normative build spec series | `docs/harness-spec-v1.3.md` + amendments v1.4, v1.5, v1.6, v1.7 |
| **CODE** | the tree at `50e2397a9` | `src/deepreason/` |

**Disposition vocabulary** (R13):

- **adopt** — build the calculus's mechanism as written.
- **adapt** — build the calculus's mechanism with a stated modification, because
  a shipped invariant, a frozen surface, or an operator law requires it. The
  modification is named in the row.
- **defer** — correct, buildable, not in the v2 program; the row says what would
  bring it in.
- **already-decided** — the operator pre-decided it (H1/H2/H3). Designed here,
  not re-litigated (R5, R7, R12).
- **conflict-needs-word** — the three authorities cannot be reconciled without
  an operator decision. Every one of these is batched into `DECISIONS.md` (R15);
  none is decided here.

**Row ids** are stable and are what `LADDER.md` cites.

---

## 0. The one architectural finding, stated first

Everything in §9 of the calculus — background, standing, wounds, falls, the
premise cascade — and everything in the operator's doctrine about problems being
criticizable, can be built **without adding a single node to `att` or `dep`**.

Problems are not in the attack graph today (`Warrant.target` is documented in
`src/deepreason/ontology/warrant.py` as "artifact id under attack", and
`build_att` in `src/deepreason/adjudication/edges.py` takes `artifacts` +
`warrants` and returns edges between artifact ids). The calculus never puts them
there either: it criticizes a problem **through an artifact** — the premise —
and the problem's consequence is a *mark*, not a *label*.

That is why the whole v2 program can be additive:

- the two-pass label computation (§6) is untouched;
- `verify_root`'s replay-validation formats are untouched;
- every committed root replays byte-unchanged at every rung.

**RE-EXAMINED 2026-08-15 under the operator's law of 2026-08-14** ("Old runs owe
the future nothing"). The original argument for this finding rested partly on a
cost that no longer exists: making Π a node set in `att` would have invalidated
every committed root, and that is no longer a prohibition. The finding survives
re-examination anyway, on two grounds that were always the stronger ones:

1. **The calculus does not ask for it.** §9.8 criticises a problem THROUGH its
   premise and marks the problem; nowhere does it make problems attack targets.
   Building what the theory does not ask for is not a clean shape, it is a
   bigger one.
2. **Within-version coherence still binds.** A v2 run's record must be
   replayable by the code that wrote it; rewriting event application and
   verification formats mid-program breaks the runs of the version making the
   change, which the law explicitly does not license.

What HAS changed: the additive-only constraint is gone, so a rung may give
`verify_root` and the record the shape the calculus wants rather than the shape
that would also have parsed a 2026-07 root. **This is still the single most
important thing the implementing tranches must not forget — now for the reason
the calculus gives, not the reason the old compatibility law gave.**

---

## 1. The three already-decided headline rows (R14)

These carry full designs because the operator asked for the design, not the
decision (R6, R8–R11).

---

### H1 — "failed verdict ⇒ successor problem" is DELETED

| | |
|---|---|
| **CALCULUS says** | §5 lists it first in an EXHAUSTIVE spawn-trigger list: "failed verdict ⇒ successor problem". §9.6 repeats it: "The failed verdict spawns a successor problem as always; under a consulted fa that successor is the crisis problem." |
| **SPEC says** | v1.3 §3: "failed verdict ⇒ successor problem (P2)". v1.3 §7 leans on it: "No bespoke sharpen-or-drop: the failed verdict already Spawns a successor problem (P2) — sharpening is the successor's job." |
| **CODE does** | `SpawnTrigger.SUCCESSOR` (`src/deepreason/ontology/problem.py`) fires in `scan_spawns` (`src/deepreason/rules/spawn.py`) for every artifact at `Status.REFUTED`, once per addressed problem, passing `criteria=parent.criteria` verbatim and carrying the ROOT description forward (two live-observed workarounds are commented in place: nesting to 7 levels, and criteria-only successors starving the generator of the problem's format contract). Measured on root `8e22d0431fd2b98d`: SUCCESSOR spawned 16 problems of 2 894. |
| **DISPOSITION** | **already-decided — DELETE.** A failed conjecture records its failed commitments and mints nothing. |

**Designed consequence (R6): what covers legitimate sharpening.** Three roads,
all on the problem layer, all already in the calculus:

1. **Discrimination.** "≥2 surviving rivals for one π ⇒ discrimination problem"
   is untouched. It fires on SURVIVORS, not on failures, which is exactly where
   the calculus puts theory-choice: §9.1 — "Refutation may be unilateral… Theory
   choice may not: a crucial test is intrinsically comparative." Sharpening
   between live alternatives is comparative work and keeps its trigger.
2. **Premise-criticism (H2's channel).** When repeated failure on π traces to
   something π falsely presupposes, the legal move is to attack the
   PRESUPPOSITION. π is then premise-orphaned, and one of its three resolutions
   is **translate** — which mints a successor PROBLEM in the succeeding
   vocabulary, with an adjudicated premise behind it. This is the operator's
   sentence, mechanized: *"The successor functioning should replace conjecture
   spawned sub problems."* Succession survives; it just stops being a byproduct
   of one candidate dying and becomes an adjudicated problem-layer event.
3. **Criteria already tighten by conjunction, with nothing minted.** SPEC §3's
   battery rule `B₀(a) = I(a).commitments ∪ instantiated criteria of addressed
   problems` is implemented literally in
   `workloads/models.py::compile_interface_draft`. The next candidate on the SAME
   π already faces every criterion the problem carries plus the anti-relapse
   gate's battery-equivalence check. No new problem is needed for the next
   attempt to be harder to get away with — which is the direct answer to the
   parked P5 question (see §5).

**Designed consequence: the crisis problem (§9.6).** H1 removes the clause that
minted it. v2 re-founds it without minting anything: **crisis is a render
state** — which is what §9.5 already says in its own words ("Crisis is a render
state, not a mode switch") — and the incumbent's PROMOTION problem stays on the
frontier, ranked up by wound count (attention only, C5). A rival frame assertion
addressing that same promotion problem triggers the ordinary ≥2-survivors
discrimination spawn (§9.4 criterion 4, §9.7). Nothing new is minted; the demand
stays addressable. The alternative — a standing-layer spawn trigger keyed on
"consulted fa whose subject carries an unrefuted standing attacker" — is priced
in `DECISIONS.md` D-1, because it is a real fork and it is *adjacent* to the
edge H1 deletes.

**What H1 does NOT touch.** P7 ("There is no conjecture without a problem") is
untouched: the deleted edge runs problem-FROM-failure, not conjecture-from-
problem. P8 (error preservation) is untouched: the refuted candidate, its
warrant, its failed commitment, its verdict and its trace all remain
(`Warrant.commitment` / `.verdict` / `.trace_ref`). N3 is untouched: the parent
problem stays on the frontier and stays addressable — note that the deleted
successor problem was a COPY of the parent's criteria under a new id, so nothing
addressable is lost. The one genuinely lost affordance is the fresh problem id;
`LADDER.md` Rung 2's gate proves that loss is inert by replaying the successor
census of root `8e22d0431fd2b98d`.

---

### H2 — the premise channel, generalized

| | |
|---|---|
| **CALCULUS says** | Def 3.5: a problem's provenance carries `provenance.frame : [frame-assertion ids]`, "written deterministically at registration, editable by the registrant at pose, immutable thereafter (C4)", and §9.8 fires the orphan cascade off exactly that field. Presupposition is therefore frame-shaped and pose-time-only. |
| **SPEC says** | Nothing. `ProblemProvenance` in v1.3 §1 is `{trigger, from}`; no amendment adds a premise concept. |
| **CODE does** | `ProblemProvenance` = `trigger: SpawnTrigger` + `from_: list[str]`. No premise, no frame, no cascade. A problem, once posed, has no channel by which anything about it can be criticized. |
| **DISPOSITION** | **already-decided — GENERALIZE.** `provenance.frame` becomes the special case of recorded problem premises. |

**The mechanism, in the calculus's own idiom (R8).** Three ordinary artifacts
and one derived predicate. Nothing is a new node type (C3 holds).

- **X — the presupposition.** An ordinary artifact whose content states what π
  takes for granted. It has commitments like anything else, so it is attackable
  by the ordinary machinery, and observation-valued commitments on it plug
  straight into the research/holdout path.
- **ρ — the attribution.** An ordinary artifact whose content is the claim
  "π presupposes X". Its interface:
  - a **`mention`** ref to X — **never a `dependence` ref.** This is Law 9.4
    (the mention law) generalized, and for exactly the reason the calculus gives
    for frame assertions: if ρ *depended* on X, then refuting X would drag ρ to
    `suspended_unsupported` and the cascade would disarm itself at precisely the
    moment it is needed. Call it **Law 9.4′**; it is the load-bearing edge-role
    choice of the whole design.
  - **`dependence`** refs to ρ's own case — the argument or evidence that π
    really does presuppose X. Attacking the case cuts ρ's support, ρ becomes
    `suspended_unsupported`, and the attribution stops being consulted. That is
    revocation, and it lands exactly where §9.4's revocation lands: *unearned,
    not wrong*.
- **`presupposition-wf` — the recognition commitment.** C3 forbids a `kind`
  field, so an artifact is an attribution **iff it carries a program commitment
  that says so**: `program:presupposition-wf` parses ρ's content into
  ⟨problem-id, premise-artifact-id⟩ and passes iff both resolve and the parsed
  premise is the artifact ρ mentions. Dispatch is on what the artifact commits
  to — the same move `skeleton-wf` already makes for informal content (SPEC
  §10.1), and the same move §9.2 makes for frame assertions. The commitment is
  an ordinary registered artifact, so the channel itself is attackable (P6,
  Refl) — **nothing is hardcoded (R11).**

**The firing rule (R9), derived and never stored (C4):**

```
premise_orphaned(π) ⇔ ∃ρ : passes(ρ, presupposition-wf)
                          ∧ names(ρ) = π ∧ mentions(ρ) = X
                          ∧ final(ρ) = unrefuted
                          ∧ final(X) ∈ { refuted, suspended_unsupported }

grade(π) = premise refuted       if final(X) = refuted          (fall-grade)
           premise unaccredited  if final(X) = suspended_unsupported (revocation-grade)
```

Both grades and both consequences are §9.8's, unchanged. Marks are lazily
materialized (the orphan problem instantiates when π is next focused); pending
marks deprioritize π in scheduling — attention only, C5. The three resolutions
are §9.8's three, unchanged: **retire / translate / independence.**

**Prop 9.7 (cascade totality) survives verbatim.** Its proof is "marking is a
total computable function of the log; resolutions exist only as registered
problem-closures." Replacing a provenance-field lookup with a query over
attributions changes the function, not its totality or its computability.

**`provenance.frame` as the special case (R7).** When a problem is posed under a
consulted frame assertion `fa`, the harness deterministically registers an
attribution ρ_fa = "π presupposes fa" at pose time. `provenance.frame` is then a
**view** — the set of attributions naming π whose mentioned artifact is a
consulted `fa` — rather than a stored field. Three consequences, and the second
is the reason the generalization is not merely cheaper but *necessary*:

1. **Zero stored-record change.** No new field on `ProblemProvenance`, so no
   widening of any stored record, so nothing for a reader of a committed root to
   mis-handle. (The alternative — the calculus's literal stored field — is
   priced in `DECISIONS.md` D-3, because deviating from the calculus's text
   deserves the operator's word.)
2. **A critic can register a HIDDEN presupposition LATER.** The calculus's field
   is "immutable thereafter", which means a presupposition nobody noticed at pose
   time can never be recorded. H2's whole point is that a critic may register a
   problem's *hidden* presupposition — so the pose-time-immutable field cannot
   express the thing the operator asked for. The derived view can: registering
   another attribution is an ordinary registration at any later time.
3. **C4 is honored more strictly than the calculus honors it.** The calculus
   stores presupposition in provenance and then reminds the reader it is
   "epistemically inert". Deriving it removes the need for the reminder.

**The siren case — a complete legal move sequence (R10, R25–R28).**

The operator's own example, supplied 2026-08-14 (REQUEST.md Amendment 1):

> "What is the colour of a siren. It's a question that could be interpreted as a
> problem, but it's fundamentally flawed before even receiving an answer… In
> this case, the problem itself is the subject of criticism, which is summarily
> refuted. Not a conjecture, a problem."

Seed problem **π₁**: *"What is the colour of a siren?"*
Presupposition **X**: *"a siren is the kind of thing that has a colour."*
A category error — **no instrument or measurement anywhere** (R26), so the
sequence may not route through an observation, an evidence artifact, or the
faulty-instrument reinstatement, and X must fall **by argument alone** (R27).

| # | Rule | Move |
|---|---|---|
| 1 | `Spawn(seed)` | π₁ registered. **No conjecture is ever proposed on it** — the flaw is prior to any answer (R28). |
| 2 | `Register` | a critic registers **X** = "a siren is the kind of thing that has a colour" as an ordinary artifact, carrying the **premise rent battery** (below): a premise is a claim like any other and pays demarcation rent. |
| 3 | `Register` | **ρ** = "π₁ presupposes X": `mention` → X (Law 9.4′), `dependence` → its case (that π₁'s question form is unanswerable without X). ρ passes `presupposition-wf` ⇒ consulted. |
| 4 | `Crit` — **the whole weight of the example rests here** | X is refuted for **explanatory emptiness**, by program, with no observation and no judge. The rent battery's demarcation criterion asks whether X carries a SUBSTANTIVE commitment — anything X forbids. A category error forbids nothing: there is no state of affairs whose obtaining would count against it, which is precisely the operator's "no instrument or measurement anywhere". The criterion FAILS ⇒ ordinary demonstrative warrant (commitment, verdict, trace), carried by a critic artifact with validity node ν. **The critic's category-error argument is the content of ν** — it asserts the test was sound and relevant, i.e. that colour-attribution to a sound event is the kind of thing that forbids nothing. The argument therefore does real work and is fully attackable, without ever being a self-certifying prose warrant. |
| 5 | `Adj` | Pass 1: X is **refuted**. Pass 2: ρ is untouched — it only mentions X (Law 9.4′). So `premise_orphaned(π₁)` = true, grade **premise refuted**. The mark is lazy; π₁ is deprioritized in scheduling (C5). |
| 6a | orphan resolution — **retire** | holding: "a siren is not a colour-bearer; there is nothing here to answer." π₁ leaves the frontier, logged, never deleted (P8). **This is the operator's "summarily refuted": the problem died before any conjecture on it was ever proposed.** |
| 6b | orphan resolution — **translate** | successor problem **π₂**: e.g. *"What colour is the housing of a siren unit?"* or *"What is the conventional colour coding of emergency sirens?"* — a different question, posed in a vocabulary where the property has a bearer, provenance recording the lineage from π₁ and ρ. **This is the only way a successor problem is minted in v2** (H1). |
| 6c | orphan resolution — **independence** | holding: π₁ never needed X — it was always about the housing, and the colour question was well-posed all along. The orphan closes; the scheduler thereafter treats π₁ as unorphaned, computed from the resolution. π₁'s own record is never mutated. |
| 7 | `Crit` on **ν** — the argument-only counterpart of the faulty instrument | there is no recording to impeach, so reinstatement runs through N1's other exits: attack ν directly ("a siren is individuated by its housing, which does bear a colour; the category error is the critic's, not the question's"). Accepted ⇒ ν falls ⇒ the warrant falls ⇒ **X reinstates** (Lemma 6.1) ⇒ `premise_orphaned(π₁)` becomes false by the same computed predicate. If the warrant had been rubric-derived, Closure 2 gives a second exit: refute the standard and every verdict under it falls. |
| 8 | `Crit` on the **retirement** | if π₁ was already retired, the retirement closure is itself an ordinary artifact and is attacked on the ground that its premise reinstated; π₁ returns to the frontier. **No absorbing state anywhere in the sequence** (N1, N3). |

**The premise rent battery (design consequence of R27).** For move 4 to be a
program verdict rather than a prose verdict, a premise artifact must carry a
demarcation criterion at registration — the same rent §9.3 charges a candidate
background ("a candidate background must be `active(b)`"), applied to premises.
Two implementation constraints, both from existing code:

- **Substantive, not merely non-empty.** `crit(a) ⇔ commitments ≠ ∅` is
  satisfiable by attaching a structural check, which is the exact
  self-immunisation trap `rules/warrants.py::formally_backed` already guards
  ("`program:json-wf` … passes for anything well-formed, and immunise itself
  against criticism. Structural well-formedness proves nothing about the
  subject, so it protects nothing about the subject"). The premise criterion
  must reuse the existing `_substantive` notion
  (`measures/reach.py`, which excludes `json-wf`, `skeleton_wf`, `lineage_ref`,
  `checker_wf`), not re-derive it.
- **`active(a)` does not exist yet** — see the corrected row M-1 below.

**Why this sequence is stronger than the harness's general position on
argument.** It needs no observation, no evidence, no judge seat, and no model
family beyond the one already running: the refutation is a program verdict, and
**demonstrative outcomes are status-changing under every authority mode**
(`src/deepreason/rules/crit.py`). So the operator's own example runs on a solo
configuration under the shipped default posture — but only because a category
error is the case where "refuted by argument" and "refuted by demarcation"
coincide. The general case does not, and that gap is the new row W-1 and the
new decision **D-8**.

**Where the operator's sentence lands.** *"The problem itself is the subject of
criticism, which is summarily refuted. Not a conjecture, a problem."* is moves
1 → 4 → 6a with **step 2 of the old reading deleted**: no conjecture is
proposed, none fails, and π₁ still dies — directly, by an attack on what it
presupposed. And it happens without putting problems into `att` (§0).

**N3 keeps its force (R11).** No step above asserts π₁ is insoluble. Retirement
is a finding about the PREMISE, not about solubility; it is an ordinary
registered artifact, hence attackable and reversible (move 8); and N1 applies to
every object in the chain. Starvation of attention (the deprioritized mark) is a
visible condition of the schedule, never a verdict — exactly N3's own wording.

---

### H3 — status vocabulary at the view layer only

| | |
|---|---|
| **CALCULUS says** | §6: labels are `unrefuted / refuted / suspended / suspended_unsupported`, and names the choice deliberate: "The label is named unrefuted, not 'accepted,' deliberately… survival under the criticism so far supplied, nothing stronger (P1, P2). The calculus has no stronger word to offer and refuses to imply one." |
| **SPEC says** | v1.3 §4 pseudocode emits `accepted`. v1.7 §E records the cost of that word: the `adjudication-blindness` epistemic check exists because "a reader of `positions.accepted` MUST consult this finding before treating acceptance as adjudicated." |
| **CODE does** | `Status` (`src/deepreason/ontology/state.py`) = `ACCEPTED="accepted" / REFUTED / SUSPENDED / SUSPENDED_UNSUPPORTED`. Those strings are written into `objects/`, event payloads, and run-status files across every committed root. |
| **DISPOSITION** | **already-decided — adopt at VIEW and presentation layers only.** |

**The mapping** (rendering only):

| stored label (never changes) | rendered label | gloss the renderer adds |
|---|---|---|
| `accepted` | `unrefuted` | "every attack so far is defeated — survival, not endorsement" |
| `refuted` | `refuted` | — |
| `suspended` | `suspended` | "under unresolved attack" |
| `suspended_unsupported` | `suspended_unsupported` | "orphaned, not false — it lost its ground, it was not shown wrong" |

**The line that decides every case:** a string **written into a root** stays
`accepted`; a string **rendered to a reader** may say `unrefuted`.

> **Note added 2026-08-15.** H3's stated rationale had two halves: "stored record
> labels never change" AND "readers stay byte-compatible with every committed
> root". The 2026-08-14 law retires the second half — nothing now forbids
> renaming the stored label to `unrefuted` for v2. The first half is an
> independent operator instruction and remains binding, so Rung 1 implemented it
> as written and the stored labels did not move. Flagged, not acted on: if the
> operator now wants the stored vocabulary to match the calculus outright, that
> option has been reopened by the law and costs one small rung. It needs their
> word, not an inference from the law. Machine JSON
keeps the stored label (v1.5 §I: "machine JSON retains stable full IDs and typed
results") and MAY carry an additional display field; it never substitutes.

**Why this is not cosmetic.** v1.7 §E is the recorded evidence that the word
"accepted" has already caused readers to treat acceptance as adjudicated — the
harness had to grow a typed check to warn them. H3 removes the invitation at the
surface where it is read, at zero cost to the record.

---

## 2. The drift table

### 2A. Epistemological invariants (calculus §1)

| id | CALCULUS | SPEC | CODE | Disposition |
|---|---|---|---|---|
| P-1 | P1 fallibilism: every status admits an exit; nothing is ever verified | v1.3 §5 N1, verbatim in substance | two-pass labels recompute after every registration; no terminal certification | **adopt** — already true; no work |
| P-2 | P2 no induction: no confirmation relation; evidence grounds only attacks | v1.3 §0 + §12; evidence enters as an artifact, warrants declare `evidence` refs | `RefRole.EVIDENCE` is permitted only on validity nodes and only lifts ATTACKERS | **adopt** — already true |
| P-3 | P3 criticism is the sole selector | v1.3 §0/§4: inputs to adjudication are `att`/`dep` ONLY | `build_att` + two-pass; measures never enter | **adopt** — already true |
| P-4 | P4 explanatory demarcation, BOTH halves: forbids something AND explains; a non-load-bearing mechanism is refuted by program, untested | v1.3 §6 `crit ∧ mod`; §10.1 `skeleton-wf` requires `forbidden ≠ ∅` | `skeleton_wf` only, and only for skeleton-codec candidates (see the corrected M-1: `demarcation.py` is an unimported stub). **The mechanism-load-bearing half — "role-level substitution or deletion of it flips verdicts" as a ROOT-BATTERY criterion — is not pinned into every problem**; it exists only as `hv-floor` on connection problems (v1.3 §7 Brake 1) | **adapt** — Rung 5 pins a mechanism-load-bearing criterion into the root battery for empirical scopes, reusing `µ_struct`, which already does role-level substitution. Guardrail: it is a CRITERION, never a gate (C5). The siren sequence's move 4 depends on the *first* half being available to premises (§1 H2, premise rent battery) |
| P-5 | P5 theory-ladenness: observations are conjectures; an observation refutes only while it survives criticism | v1.3 §1 evidence closure | Closure 3 implemented in `adjudication/edges.py` | **adopt** — already true; it is the faulty-instrument move of the siren sequence |
| P-6 | P6 no authority: rule-objects are artifacts, attackable; authority may exist only as attention | v1.3 §3 `Refl`; §10.6 "authority is pack ordering, never status privilege" | `rules/refl.py` exists; the audit's dead-symbol census flags `refl` as unreferenced (`experiments/2026-08-13-audit/PARKED.md` P2) | **adapt** — Rung 1 must establish that every NEW rule-object the v2 program introduces (`presupposition-wf`, promotion criteria, scope predicates, render policy) is a registered artifact. The pre-existing `refl` question is P6-adjacent and is NOT absorbed here — it stays parked |
| P-7 | P7 problems first: P₁ → TT → EE → P₂; growth is the succession of PROBLEMS | v1.3 §3: "Conj is gated on `Π ≠ ∅` — D1 made structural" | enforced | **adopt** — and H1 sharpens it: succession of problems now happens on the problem layer, which is where P7 always said it happens |
| P-8 | P8 error preservation: deletion is forgery of the growth sequence | v1.3 §0 "Nothing is deleted (D8)" | append-only log; nothing deleted | **adopt** — binding on retire/translate: a retired problem is logged, never deleted |
| P-9 | P9 hard to vary | v1.3 §6, §7 Brake 1 | `measures/hv.py`, `hv-floor` | **adopt** — already true |
| P-10 | P10 unbounded conjecture, AND "the calculus must police the gap" between in-principle and effective reach | v1.3 §5 N2 + §11 as N2's enforcement arm | `capture/` (detection, ladder, pareto, schools, atlas) | **adopt** — and Rung 7 adds the calculus's specific new instrument: promotion events logged with before/after conditioning diagnostics |
| P-11 | **P11 background: every test and every problem is posed against background held unproblematic for the occasion; methodologically privileged, epistemically never; when background falls, the PROBLEMS come up for review** | **silent — the entire doctrine is absent from v1.3 and all four amendments** | absent | **adopt** — this is the whole v2 program. The operator's own words name the gap: "a first class epistemological object that shaped a person's world view… nothing in the spec that makes the above epistemological distinction" |

### 2B. Computability discipline (calculus §2)

| id | CALCULUS | SPEC | CODE | Disposition |
|---|---|---|---|---|
| C-1 | C1 determinism and replay; wall-clock never enters a verdict | v1.3 §0, §1 "budget honesty is deterministic" | enforced; `verify_root` replays twice and compares | **adopt** — binding on every v2 mechanism: scope predicates, orphan marks and promotion criteria must be pure functions of the log |
| C-2 | C2 budgeted decidability; verdicts total over {pass, fail, overrun} | v1.3 §1 identical | implemented | **adopt** |
| C-3 | C3 untypedness: no `kind` field; dispatch on interface structure | v1.3 §0 identical, with a per-section "untypedness audit" note | artifacts untyped; `informal/`, `capture/` dispatch on criteria and content conventions | **adopt** — and it is the binding constraint on H2: `presupposition-wf` is a commitment, not a type. **Noted honestly:** the harness DOES have typed PROCESS records (work orders, capability transitions, seat bindings). Those are authority/process objects, never members of `A`, so C3 is not violated — but a v2 tranche must not smuggle an epistemic type in behind a process record |
| C-4 | C4 computed, never stored; historical views physically read-only | v1.3 §1 identical, including the read-only clause | enforced (`Harness(root, read_only=True)`) | **adopt** — binding: standing, orphan marks and `provenance.frame` are all DERIVED in the v2 design (§1 H2) |
| C-5 | C5 measures never adjudicate: exactly three channels — spawn, budgeted commitments, attention | v1.3 §0 identical | enforced | **adopt** — binding: nomination (§9.4) is channel (a); orphan-mark deprioritization is channel (c) |
| C-6 | C6 no credence; Popper–Miller decomposition named as the guard | v1.3 §11.6 typicality "prices attention and never weighs truth" | VS typicality is attention-only | **adopt** — already true |

### 2C. Ontology (calculus §3)

| id | CALCULUS | SPEC | CODE | Disposition |
|---|---|---|---|---|
| O-1 | Def 3.2 artifact = ⟨id, content_ref, codec, interface, provenance⟩; id = hash(canonical(content_ref, codec, interface)) | v1.3 §1 identical | identical | **adopt** — note for every rung: provenance is NOT in the id, so provenance work never moves an artifact id |
| O-2 | `carry ⊆ A × W` explicit, not part of artifact identity | v1.3 §1 identical | `carries` in `EpistemicState`, unioned with the legacy `artifact.warrants` encoding so old roots replay | **adopt** |
| O-3 | ref roles: dependence / mention / evidence | v1.3 §1 identical | `RefRole` identical | **adopt** — H2 needs no new role: `mention` + `dependence` carry Law 9.4′ |
| O-4 | Def 3.3 commitment ⟨eval, budget, observation_valued⟩ | v1.3 §1 identical | identical | **adopt** |
| O-5 | Def 3.4 warrant + validity node + **three** closures (validity, case-law, evidence) | v1.3 §1: all three | all three in `adjudication/edges.py`, computed as a fixpoint | **adopt** — but see W-1 for the argumentative half of Def 3.4 |
| **W-1** *(added by Amendment 1)* | **Def 3.4: a warrant is "demonstrative … **or argumentative (a case)**", and both make attack edges.** The calculus grants an argued case full status authority, subject only to its ν being attackable | v1.3 §1 same on paper; but v1.3 §3's rubric-verdict guard, §10's whole design, and v1.7 §E's `adjudication-blindness` check all treat prose verdicts as suspect, and v1.7 §E names `observe_only` "v1.3's default posture: critics file scrutiny, prose changes no status" | **An argued case changes no status in the shipped default configuration**, and cannot be made to in any solo one: `ADJUDICATION_STATUS_AUTHORITY_ENABLED` defaults **False** (`config.py`) and `ARGUMENTATIVE_AUTHORITY` defaults **`observe_only`** (`config.py`; consumed at `rules/crit.py::_authority`). `trial_required` routes the case through the **defended cross-family trial** — two families, so not solo. The third value, `single_family_trial`, **cannot complete a trial**: the `Config` direct-helper path passes no `critic_school_id`, and the v4 envelope demands a manifest-bound authority value — "parked as dead weight, not removed" (`docs/map/CON-schools.md` Traps; `experiments/2026-08-04-change-rung7-authority-as-declared-policy/PARKED.md` P5). Separately, `rules/warrants.py::formally_backed` makes any target carrying a passing substantive commitment prose-immune | **conflict-needs-word → `DECISIONS.md` D-8.** The operator's siren case escapes it — a category error is refuted by DEMARCATION, which is demonstrative and status-changing under every mode (§1 H2, move 4) — but a premise that is contentful and merely wrong-by-argument does not. Note the collision is with the operator's own values, not merely with the code: prose-immunity is the formalism-optional law's protection half, and cross-family trials are the judge machinery the solo law is wary of |
| O-6 | **Def 3.5 problem provenance carries `frame`** | silent | `ProblemProvenance = {trigger, from}` | **already-decided (H2)** — generalized to derived premise attributions |
| O-7 | Def 3.5 root battery pinned into EVERY problem: internal consistency + both halves of P4 | v1.3 §1 "Popper battery auto-pinned" | `harness.register_problem` appends `POPPER_BATTERY` unconditionally | **adapt** — see P-4: the mechanism-load-bearing half is not in the root battery today |
| O-8 | Remark: "commitments are counterfactuals… what an artifact is, epistemically, is what it rules out" | implicit | implicit | **adopt** — no work; it is the reading that makes the interface the artifact's content |
| O-9 | Def 3.6 state S = (A, Π, carry, att, dep, addr, status, **standing**, measures) | v1.3 §1 S = (A, Π, carry, att, dep, addr, status, hv, reach, conn) — **no standing** | `EpistemicState` matches v1.3 | **adapt** — standing is added as a DERIVED view (C4), not as a stored member of the materialized state. Rung 3 |
| O-10 | Def 9.2 frame assertion: an ordinary artifact with content ⟨subject, scope σ, validity, departure protocol⟩ | silent | absent | **adopt** — Rung 3 |

### 2D. Dynamics: rules, spawn triggers, guards (calculus §5)

| id | CALCULUS | SPEC | CODE | Disposition |
|---|---|---|---|---|
| D-1 | Rules Conj / Crit / Adj / Spawn / Refl | v1.3 §3 identical | `Rule` enum has these five plus process rules (Register, Merge, Measure, Reveal, Reseed, Scratch, Bridge, ConjectureTurn, Control, Capability) | **adopt** — the extra rules are process/authority, not epistemic moves; no drift |
| D-2 | **spawn: failed verdict ⇒ successor** | v1.3 §3 same | `SpawnTrigger.SUCCESSOR` | **already-decided (H1) — delete** |
| D-3 | spawn: ≥2 surviving rivals ⇒ discrimination | same | `DISCRIMINATION` | **adopt** — and it carries part of H1's replacement load |
| D-4 | spawn: unrefuted artifact with low HV ⇒ remove-arbitrariness | same | `REMOVE_ARBITRARINESS` | **adopt** |
| D-5 | spawn: reach event ⇒ explanation-debt | same | `EXPLANATION_DEBT` (measured: never fired on root `8e22d0431fd2b98d`) | **adopt** — the never-fired observation is a live-evidence question for Rung 4's gate, not a design change |
| D-6 | **spawn: reach events spanning ≥ K_frame distinct lineages over a coherent scope ⇒ PROMOTION problem (§9.4)** | silent | absent | **adopt** — Rung 4 |
| D-7 | **spawn: a frame assertion leaving unrefuted standing ⇒ PREMISE-ORPHAN problems, lazily materialized (§9.8)** | silent | absent | **adopt**, generalized per H2 — Rung 6 |
| D-8 | spawn: uncovered observation-valued commitment ⇒ research | v1.3 §12 same | `RESEARCH` | **adopt** |
| D-9 | spawn: critic-gaming signal ⇒ audit-the-critic | same | `AUDIT_CRITIC` | **adopt** |
| D-10 | spawn: isolation above floor ⇒ connection | same | `CONNECTION` | **adopt** |
| D-11 | spawn: unrefuted artifacts on overlapping problems, no declared relation ⇒ integration | same | `INTEGRATION` (2 814 of 2 894 problems on the measured root) | **adopt** — no change, but the census is the reason Rung 2's gate measures frontier volume |
| D-12 | Registration guards are warrant-validity conditions, never censorship; anti-relapse blocks only refuted-equivalents; near-duplicates of unrefuted artifacts are NEVER blocked | v1.3 §3, §11.5 identical | `rules/guards/anti_relapse.py`; measured DEGRADED for a whole run (parked P6) | **adopt** — P6's defect is absorbed by Rung 2 (see §5) |
| D-13 | Trial guard: adversarial transcript, decisive point, order-swap, paraphrase spot-checks; blocked rulings logged; a streak of blocks is a spawn signal | v1.3 §3 identical | `informal/trial.py` | **adopt** |
| D-14 | Refl: the calculus's own rules, standards, render policies and guard procedures are registered artifacts | v1.3 §3 identical | `rules/refl.py` present; flagged unreferenced by the 2026-08-13 dead-code census | **adapt** — see P-6 |

### 2E. Adjudication and machine invariants (calculus §6, §7)

| id | CALCULUS | SPEC | CODE | Disposition |
|---|---|---|---|---|
| A-1 | Two-pass: Dung grounded extension, then support over the `dep` DAG | v1.3 §4 identical | identical | **adopt** — **frozen in practice**: this is what every committed root's labels were computed by |
| A-2 | label names `unrefuted` etc. | `accepted` | `accepted` | **already-decided (H3)** — view layer only |
| A-3 | "Orphaned ≠ false": refuting a premise gives `suspended_unsupported`, never `refuted` | v1.3 §4 identical | identical | **adopt** — and §9.8 lifts the same principle to the problem layer, which is the whole point of the cascade |
| A-4 | Lemma 6.1 reinstatement is derived, never ruled | v1.3 §3 identical | falls out of Pass 1 | **adopt** |
| A-5 | N1 no absorbing status | v1.3 §5 identical | enforced | **adopt** — binding on retirement: a retired problem must be un-retirable by attacking the retirement |
| A-6 | N2 perpetual proposability | v1.3 §5 identical | `capture/` is its enforcement arm | **adopt** |
| A-7 | **N3 no insolubility: a problem leaves the frontier ONLY by adjudicated retirement, translation, or resolution of its premises; starvation is a visible schedule condition, never a verdict** | **silent — the spec has no notion of a problem leaving the frontier at all** | problems are never retired; `Π` only grows (2 894 problems on one root) | **adopt** — Rung 6. Note the direction of the gap: the code cannot violate N3 today because it cannot remove a problem at all; adding retirement is what makes N3 need enforcing |

### 2F. Measures and the knowledge view (calculus §8)

| id | CALCULUS | SPEC | CODE | Disposition |
|---|---|---|---|---|
| M-1 **(corrected 2026-08-14)** | demarcation `crit ∧ mod`, `active = crit ∧ mod` | v1.3 §6 identical | **`crit` and `mod` in `src/deepreason/measures/demarcation.py` are stubs that `raise NotImplementedError`, and nothing imports the module.** What ships is `skeleton_wf` (`programs.py` → `informal/skeleton.py`), which enforces `forbidden ≠ ∅` for skeleton-codec candidates and is registered as a **structural** program — so passing it grants no prose-immunity and grounds no reach | **adapt.** An earlier version of this row said "adopt — already true" and cited `demarcation.py`; that was wrong, and it matters: §9.3's rent law is written in terms of `active(b)`, so Rung 5 has nothing to lean on and must BUILD `crit`/`mod`/`active`, or define rent without `mod`. Rung 2's premise rent battery has the same dependency |
| M-2 | hardness-to-vary with role-level `µ` where content parses; estimating battery excludes HV-type commitments | v1.3 §6/§7 identical, incl. stratification | `measures/hv.py` | **adopt** |
| M-3 | reach: budgeted cross-evaluation; a hit is "the strongest currency the calculus mints"; held-out material where available | v1.3 §6/§10.5 same | `measures/reach.py` — cross-problem SURVIVAL with qualifying/coverage discipline from the Bronze Age postmortem | **adopt** — the code is STRICTER than both documents; the strictness stays |
| M-4 | **reach as the promotion signal: hits spanning ≥ K_frame distinct problem LINEAGES over a coherent scope** | silent | reach counts hits; no lineage-spanning aggregate, no scope coherence | **adopt** — Rung 4; it is a measure-rule over the log, channel (a) of C5 |
| M-5 | **Def 8.1 `knowledge(a) ⇔ unrefuted ∧ active ∧ reach > 0` — a VIEW that steers attention and never adjudicates** | silent | absent | **conflict-needs-word → `DECISIONS.md` D-4** (build in Rung 4, or defer). It is cheap and it is a view, but it is also a new user-facing epistemic word, and the operator's judgment on whether the harness should say "knowledge" at all is worth one line |

### 2G. The standing layer (calculus §9) — absent from SPEC and CODE in its entirety

Every row here is **silent** in the spec series and **absent** from the tree; the
columns are collapsed for readability. This is the bulk of the v2 build.

| id | CALCULUS | Disposition |
|---|---|---|
| S-1 | §9.1 two axes: status (truth-standing) and standing (role in the economy of generation) | **adopt** — Rung 3 |
| S-2 | Prop 9.1 rigidity dilemma: a single-axis calculus cannot host P11 (framing would oscillate with every reinstated observation, or be immunized) | **adopt** as the RATIONALE recorded in the new map concept document; nothing to build |
| S-3 | §9.2 Def 9.2 frame assertion (subject, scope σ, validity, departure protocol); consulted iff addressed to a promotion problem AND unrefuted | **adopt** — Rung 3 |
| S-4 | §9.2 σ is a total computable predicate over problem records; "embeddings may inform nomination, never membership" | **adopt**, with the predicate LANGUAGE to be fixed — `DECISIONS.md` D-5 prices a fixed finite DSL against an arbitrary program artifact |
| S-5 | Def 9.3 standing is derived, never stored; instrument standing is not a third value but a `bounded` validity | **adopt** — Rung 3; C4 makes this mandatory anyway |
| S-6 | **Law 9.4 mention law: a frame assertion MUST NOT carry a dependence ref on its subject** — "this single interface constraint is the whole separation of the axes" | **adopt** — Rung 3, enforced by a program well-formedness commitment. Generalized to Law 9.4′ for premise attributions (H2) |
| S-7 | §9.3 rent: promotion is purchase of exposure; a candidate background must be `active(b)` with observation-valued commitments where empirical; promotion is an ARTICULATION event (vocabulary + enumerated assumptions + commitments) | **adopt** — Rung 7 |
| S-8 | §9.4 nomination is a measure-rule (detects, never decides); promotion is an ordinary Conj→Crit→Adj pass with five pinned criteria (subject-demarcation, reach-integrity, scope-determinism, compatibility, accounts-for) | **adopt** — Rung 4 (criteria as programs), Rung 7 (nomination constants) |
| S-9 | Remark 9.5 default-consult closure: criteria are instantiated at registration and generate demonstrative program warrants before the renderer's next consultation; the renderer consults only assertions addressed to promotion problems | **adopt** — Rung 4; this is the guard that stops an unattacked frame assertion from silently framing its scope |
| S-10 | §9.4 revocation requires no rule of its own: attack the reach case, `final(fa) = suspended_unsupported`, the renderer stops consulting. "Revocation says unearned, not wrong" | **adopt** — falls out of Pass 2; no new machinery |
| S-11 | §9.5 frame render semantics: the frame slice carries the subject's articulation digest AND **the subject's standing attackers — wounds render in-frame, in every pack in scope**. "The frame ships its own crisis" | **adopt** — Rung 5. This is a pack section under `DR-CON-packs-and-token-economy`'s deterministic allocation |
| S-12 | §9.5 departures: permitted, MUST be declared as a list of broken assumption/commitment ids; declaration removes the hidden-premise criticism's target; the declaration is itself attackable; **nothing scores departures**; scope predicates never read departure declarations | **adopt** — Rung 5. The no-scoring clause is the same shape as the operator's formalism-optional law (L-4) |
| S-13 | §9.6 wounds: a fail verdict on the subject's observation-valued commitment ⇒ demonstrative warrant ⇒ refuted status, standing untouched (Prop 9.6). Newton 1859–1915 is the intended model | **adopt** — Rung 6 |
| S-14 | §9.6 "the failed verdict spawns a successor problem as always; under a consulted fa that successor is the crisis problem" | **already-decided (H1) — the minting clause is deleted.** Crisis is re-founded as a render state + a prioritized promotion problem (§1 H1). Alternative priced at `DECISIONS.md` D-1 |
| S-15 | §9.7 falls: two grades — fall (support lost or direct attack ⇒ refuted ⇒ cascade grade *premise-refuted*) and revocation (`suspended_unsupported` ⇒ *premise-unaccredited*) | **adopt** — Rung 6 |
| S-16 | §9.7 succession is discrimination, resolved comparatively (pairwise ruling, cited decisive point, mandatory order-swap); the succession pack SUPPRESSES the incumbent's frame slice — the trial of a frame is framed by neither party (incumbent-judge bias) | **adopt with a solo-compatible road** — `DECISIONS.md` D-6, because the comparative instrument leans toward judge seats and the operator's standing law is that judges are suspect-by-default and solo must never be locked out |
| S-17 | §9.7 anomaly conservation: the successor must claim the incumbent's wounds as its own commitments; its scope statement fixes the incumbent's residual validity domain; the predecessor's domain is authored by its successor and that authorship is attackable | **adopt** — Rung 7 |
| S-18 | §9.8 presupposition and the cascade; lazy materialization; batch translation offers; pending marks deprioritize (attention only) | **already-decided (H2)** for the mechanism; **adopt** for the cascade — Rung 6 |
| S-19 | §9.8 three resolutions: retire / translate / independence; the independence rate is the over-binding diagnostic on pose-time recording | **adopt** — Rung 6 |
| S-20 | Prop 9.7 cascade totality | **adopt** — Rung 6's gate proves it |
| S-21 | §9.9 authority audit: standing is render authority and nothing else — derived, content not type, never in label computation, every realizing object attackable | **adopt** — Rung 7, as a replay program over the log (an audit that can FAIL, not a prose assurance) |

### 2H. Generation and effective openness (calculus §10)

| id | CALCULUS | SPEC | CODE | Disposition |
|---|---|---|---|---|
| G-1 | γ is a bounded pure function from packs to schema-valid candidates; holds no state, adjudicates nothing, controls no flow | v1.3 §0 identical | enforced (the LLM is `pack -> schema-validated JSON`) | **adopt** |
| G-2 | each call returns a DISTRIBUTION with stated typicality; typicality prices attention only | v1.3 §11.6 Verbalized Sampling | `VS_K` | **adopt** |
| G-3 | every conjecture is born connected | v1.3 §7 L1 | implemented | **adopt** |
| G-4 | "a frame slice is deliberate, scope-wide conditioning, the strongest the calculus ever applies" — countermeasures are attention-side: population structure + panmictic criticism, capture detection as replay programs, responses reweight rendering with hysteresis | v1.3 §11 (schools, detection, ladder) | `capture/` | **adapt** — Rung 7 must extend the existing capture instruments to the new conditioning surface. A frame slice that nobody measures is precisely the capture the calculus warns about |
| G-5 | **promotion events logged with before/after conditioning diagnostics: "the capture cost of elevation is measured, not vibed"** | silent | absent | **adopt** — Rung 7 |
| G-6 | exogenous grounding ratio with a floor; "a background that is confidently, quietly wrong generates no wounds; only the anchors outside the loop bear on it" | v1.3 §11.3 λ + `LAMBDA_FLOOR` | implemented | **adopt** |

### 2I. Informal content (calculus §11)

| id | CALCULUS | SPEC | CODE | Disposition |
|---|---|---|---|---|
| I-1 | skeletons: claim / mechanism / scope / forbidden cases, each forbidden case compiled at registration into a commitment | v1.3 §10.1 identical | implemented | **adopt** |
| I-2 | the mechanism slot is load-bearing by the root battery; a skeleton whose mechanism swaps freely is refuted by program, untested | v1.3 §10.1 + §7 Brake 1 | `hv-floor` is pinned on CONNECTION problems, not the root battery | **adapt** — same row as P-4/O-7; Rung 4 |
| I-3 | standards as ordinary artifacts wired into Closure 2 | v1.3 §10.3 identical | implemented | **adopt** |
| I-4 | comparative rulings replace absolute scoring; judge behavior program-audited; audit hits enter as ordinary demonstrative warrants | v1.3 §10.2/§10.4 identical | implemented | **adopt** |
| I-5 | human rulings enter as precedent artifacts ranked first in render, attackable | v1.3 §10.6 identical | implemented | **adopt** |
| I-6 | sealed evidence with scheduled reveals; a pass on revealed material is a reach hit with the strongest provenance the informal side can produce | v1.3 §10.5 identical | `Rule.REVEAL` exists | **adopt** — Rung 4 depends on it for reach-integrity criterion 2 ("timestamps prove held-out standing where claimed") |

### 2J. Properties and limits (calculus §12, §13)

| id | CALCULUS | Disposition |
|---|---|---|
| T-1 | Prop 12.1 total computability | **adopt** — every v2 mechanism must be a pure fold over the log; this is the acceptance condition each rung's gate re-proves |
| T-2 | Prop 12.2 no confirmation, no credence | **adopt** — already true |
| T-3 | Thm 12.3 no absorbing status, frame assertions inherit all exits | **adopt** — Rung 3's gate |
| T-4 | Prop 12.4 axis independence | **adopt** — Rung 3's gate proves both directions |
| T-5 | Prop 12.5 standing never adjudicates | **adopt** — Rung 3's gate proves label computation still reads `att`/`dep` only; this is the row `DR-SEAM-adjudication-x-authority` exists to protect |
| T-6 | Prop 12.6 knowledge is a view | **tied to D-4** (M-5) |
| T-7 | §13 limits, stated: nomination thresholds, scope predicates, slice budgets and orphan scheduling are EMPIRICAL CONSTANTS, "none is defended here" | **adopt as an honesty obligation** — every constant the v2 program introduces ships as a config knob with a recorded default and a measurement plan, never as a defended value. `DECISIONS.md` D-5/D-7 |
| T-8 | §13: "a wounded background with no arriving rival frames forever — refuted, indicted in every pack, unreplaced, and never declared irreplaceable" | **adopt** — it is the honest residue and belongs verbatim in the RESULTS.md of whichever rung ships wounds |

### 2K. The operator's standing laws (R21)

| id | Law (CLAUDE.md, operator's words) | Does the v2 design honor it? |
|---|---|---|
| L-1 | **All configurations should be allowed** — compile never refuses an otherwise-parseable configuration; impossibility surfaces typed at the point of use | **Honored, with a named obligation.** Every v2 knob (frame assertions enabled, `K_frame`, orphan scheduling, promotion) must compile in any combination, including nonsensical ones, and fail typed at use. The trap to avoid: a validator that rejects a manifest naming a scope predicate the run has no problems for. Each rung's exit criteria carry this check |
| L-2 | **Operations are available to every configuration** — one run path; amend / continue / cancel / result / finalize reach every run | **Honored.** Nothing in the v2 program adds a launch path or a terminal. Obligation: a run that acquires a frame assertion mid-flight must still amend and continue; Rung 3's gate includes an amend-then-continue over a root carrying standing |
| L-3 | **A solo run with everything on must be an option**; judges are suspect-by-default | **Tension, named, not hidden.** §9.7 makes succession *comparative* — "pairwise ruling, cited decisive point, mandatory order-swap" — which is judge-shaped. The calculus itself offers the solo-compatible road in §9.4 criterion 5: `accounts-for` is "program-checked against the wound list with anchored-rubric backup". v2's recommendation is program-first, rubric optional. Priced at `DECISIONS.md` **D-6** |
| L-4 | **Formalism is an option, never an obligation**; nothing may weight outcomes on conjecture KIND | **Honored, and reinforced.** §9.5's departure clause is the same law in the calculus's own voice: "Nothing scores departures, because no penalty channel exists to score them with — the freedom is by construction, not by rule." Obligation on every rung: no premise attribution, frame slice or promotion criterion may become a rank, admission or acceptance penalty for an informal or uncited conjecture (`DR-CON-conjecture-kinds` R-g) |
| L-5 | **Seats change how content is GENERATED, never what counts as EVIDENCE** | **Honored.** The frame slice (§9.5) is the strongest conditioning the calculus applies and it is *render only*: it changes what γ is shown, never what may refute. Obligation: Rung 5's gate proves a frame slice cannot alter any label |
| L-6 | **Tokens are cheap; the agent is not** — prefer live-run evidence over hand-built machinery | **Honored by the ladder's shape.** Rungs 2, 4 and 6 each carry a live-run gate over the existing ladders rather than a synthetic fixture, and the census work reuses the committed root `8e22d0431fd2b98d` instead of minting new evidence |

### 2L. The signal contract (operator-parked design, supplied 2026-08-14)

REQUEST.md Amendment 2, R29–R36. This is not a calculus row-set — the calculus
is silent on allocation, because allocation is efficiency and the calculus
adjudicates evidence. It is reconciled here because it governs the channel
through which **every signal the v2 program emits** must be declared, and
because three of its six clauses restate C-invariants and operator laws in the
allocation controller's own terms.

| id | Clause | SPEC | CODE | Disposition |
|---|---|---|---|---|
| SC-1 | **(1)** the registry is a CONTRACT — name, unit, producer-agnostic semantics, staleness bound; new setups add signals by declaration, never by teaching a consumer about a subsystem | silent | `src/deepreason/signals.py` is a registry of **89** measure tags as prose docstrings, AST-enforced by `tests/test_signals.py` so an unregistered tag fails the gate. Enforcement exists; the CONTRACT does not — no unit, no declared semantics, no staleness bound, and nothing typed | **adopt.** The 89 existing entries migrate to the typed record; the AST test keeps its job. Bulk of the rung's size |
| SC-2 | **(2)** keyed by SEAT INSTANCE, not role | silent | role-keyed throughout: `controller.py::_clean_streak(role)`, `_propose` over role caps. E28's own evidence is role-shaped — "`judge` pinned at 16 384 for 342 calls whose largest completion was 141 tokens" — and could not have distinguished two judge seats behaving differently | **adopt.** Seat identity already exists and is already in the record: `seat-bindings.v1` (v1.7 §A) carries resolved `group → provider/model/profile-digest` into the log, and `tools/root_sweep.py` already reads it. Keying signals by seat instance consumes identity that is already there — **it adds no role**, so qualification subject digests do not move |
| SC-3 | **(3)** the controller consumes ONLY the signal interface, pinned by an architecture test that fails on imports of schools / rules / criticism internals | silent | **the boundary already holds**: `controller.py`'s only `deepreason` import is `deepreason.ontology` (`Provenance, Rule, Status`). The test would pass on the tree as it stands | **adopt — cheap and high value.** It pins an existing boundary rather than forcing a refactor. One migration item is real though: the controller reads graph state directly (`harness.state.status.get(...)` at three sites) rather than through a signal. Under R29's "interface-only consumption" those reads become declared signals |
| SC-4 | **(4)** compiled matrix test over configuration classes | silent | no such matrix exists | **adopt.** This is the operator's all-configurations law (L-1) made executable for the allocation controller — the same law, with a test behind it |
| SC-5 | **(5)** a topology that cannot produce a signal compiles, with a typed `allocation open-loop for signal X` notice | silent | E28's fix already established the shape: "a controller that cannot steer something says so in a typed `controller-authority` record instead of returning `None`" | **adopt.** Consistent with L-1 verbatim ("a typed disclosure recorded alongside the compiled result … never a stop") and with the precedent the controller already sets. Low cost, because the record type it extends exists |
| SC-6 | **(6)** FROZEN change protocol / VERSIONED registry + policy algorithm / FREE parameters, ledgered as a CLAUDE.md law + INV doc + two REC recipes; no workflow until two recorded recipe failures | silent | **two of the three layers are already implemented in substance**: `cap_envelope`/`clamp` are the FREE layer's envelope bounds, and `_policy_payload` reads the policy from a registered ARTIFACT — which is already "policy-as-recorded-artifact". `config_referee` (v1.7 §F) is the referee the VERSIONED layer names, already opt-in and contract-bound. What is missing is the LAYERING as a stated, checkable protocol | **adopt.** Note the connection to P-6: "policy-as-recorded-artifact, referee-reviewed" is exactly the `Refl` door — a rule-object that is a registered artifact and therefore attackable — which the drift table flagged as adapt because `refl` itself is inert. This clause gives that door a live user |

**Where it lands (R36), argued from the table.** Its own rung, **Rung 1b**,
immediately after Rung 1 — with the *ledger* half of clause (6) folded into
Rung 1. Three reasons, in order of weight:

1. **SC-1 must precede every rung that emits a signal.** The v2 program emits
   new signals from Rung 2 onward — orphan marks, standing consultations, and
   in Rung 8 the promotion event's before/after conditioning diagnostics that
   G-5 requires. If the registry becomes a contract *after* those exist, every
   one of them is a retrofit. The operator's own clause says new setups add
   signals "by declaration through this typed channel" — that only holds if the
   channel is there first.
2. **Its blast radius is disjoint from the standing layer's.** Folding it into
   Rung 4 (frame assertions) would put two unrelated frozen-surface forecasts
   and two unrelated gates in one tranche — the same objection that earned the
   spawn-trigger deletion its own rung. Rung 4's gate proves axis independence;
   an import-boundary test and a configuration matrix have nothing to do with
   it and would dilute it.
3. **The operator's "fold into 1+4" is half right, and it is the ledger half.**
   Clause (6)'s CLAUDE.md design law is documentation of a stated operator law
   and belongs with Rung 1's map work. But the INV- document's **checks** cannot
   be written before the mechanism exists — `python tools/docs_verify.py
   --audit` "refuses checks that cannot fail", so an INV document about an
   unbuilt mechanism would ship vacuous checks. So: **law text in Rung 1; INV
   document, both REC recipes, and the mechanism in Rung 1b.**

**Vocabulary hazard, recorded for Rung 1 (H3).** `controller.py` already has
`_under_standing_attack`, where "standing" means *currently under an unresolved
attack*. The calculus's `standing` (§9.1) means *frame role in the economy of
generation* — a different thing entirely. Two meanings of one word in one
codebase is exactly the drift H3 exists to prevent, and the collision predates
the calculus. Rung 1 renames the controller's predicate (a private method with
no stored string behind it, so nothing in any root moves).

### 2M. The three authorities, their precedence, and every departure from v0.1

REQUEST.md Amendments 4 and 5 (R43–R53). Three documents now govern the v2
design, and they are not one voice.

**Precedence, for DESIGN only (R49):**

    Formalization (repairs)  >  Computable Calculus (design)  >  v0.1 (epistemology)

This orders which document decides a DESIGN question when they conflict. It is
emphatically NOT a claim that a later document is truer: v0.1 is the
foundational epistemology and the other two are read against it, which is why
every departure from v0.1 is rowed below with its reason.

**The charter sentence (R51), v0.1 §7, verbatim:**

> "An engine that implements the bookkeeping faithfully and leaves genesis open
> is not an incomplete implementation of 𝔓; it *is* an implementation of 𝔓."

No rung may treat the open genesis layer as an incompleteness to be closed. The
clean cut is the program's licence to exist: the bookkeeping layer — ledger,
grounded-extension computation, supersession checks against registered
explicanda, status derivation, problem objects with source-types — is what this
harness builds, and the generators are entered as methodic contents,
appraisal-inert in origin, criticized like everything else.

#### The Formalization's §1 integration-boundary table, VERIFIED against v0.1 (R53)

Previously this table had to be taken on its word about what v0.1 says. It no
longer does. All seven rows check out; the verification is recorded because a
row that had been wrong would have propagated into every rung that trusts it.

| §1 row | What §1 attributes to v0.1 | v0.1 says | Verdict |
|---|---|---|---|
| Refutation | lone failed test ⇒ problematic; comparative succession required for tentative refutation | Def 3.5, verbatim: "a lone failed test yields *problematic*, never *refuted*" | **accurate** |
| Support | status read from a Dung grounded extension | §3.3: standing "is read off the argumentation framework (𝔈, ⇀) by its grounded extension G(Σ)"; no dependency pass exists in v0.1 | **accurate** |
| Hardness to vary | an order on functional slack structures, generally non-effective | Def 3.7 (embedding of slack structures) + §7 ("slack-comparison … undecidable") | **accurate** |
| Knowledge | constructor-theoretic resilient information + a conjectured resilience identity | §2 Stratum Φ (the exact constructor-theoretic definition) + Principle 2.4, explicitly labelled *conjecture* | **accurate** |
| Background exit | not represented as a separate axis in v0.1 | v0.1 has no frame-assertion / background-standing axis; "background" appears only as unformalized context in §3.5 and §5 | **accurate** |
| Wound persistence | not represented in v0.1 | no wounds, no frame assertions | **accurate** |
| Orphans after reinstatement | not represented in v0.1 | no presupposition cascade | **accurate** |

#### Departures from v0.1, each with its one line (R50)

| id | Departure | Why |
|---|---|---|
| V-1 | **The dependency-support pass** (`SUSPENDED_UNSUPPORTED`) has no counterpart in v0.1's pure grounded semantics | Licensed as a CONSERVATIVE extension (Formalization §1 + Theorem 5.2): with an empty dependency graph it reduces to v0.1's statics exactly, so nothing v0.1 decides is re-decided |
| V-2 | **The harness refutes unilaterally** on an undefeated warranted violation; v0.1 Def 3.5 reserves *refuted* for the two-place relation requiring a surviving rival | Repaired rather than adopted: §1's split keeps BOTH as distinct derived relations — `Refuted` = unilateral defeat under registered criticism, `Superseded` = comparative theory choice (R46). v0.1's constraint survives intact under the second name, which is what makes "refuted but still framing" coherent |
| V-3 | **`Status.ACCEPTED` exists as a stored label**; v0.1 §6 admits "no acceptance event" | Vocabulary only, and already rowed as H3: the stored label is a computed fold output, not an act, and the view layer is where the word is corrected. No rung may make it an event |
| V-4 | **Attention reads provenance** — the seed question wins rank ties, import-role records never count as survivors | v0.1 Axiom 4.1 quantifies over APPRAISAL predicates ("problematic, good, superseded, harder-to-vary"), and ranking is none of them. Rowed anyway because it LOOKS like a violation, and the next reader should find the answer here rather than re-derive it |
| V-5 | **The premise rent battery and prose-immunity key on commitment KIND** (substantive vs structural) | Also not appraisal-by-provenance: the discriminator is what an artifact DECLARES it forbids, which is available to any content whatever its origin. Axiom 4.1 is untouched; the formalism-optional law (L-4) is the constraint that actually binds here |
| V-6 | **`problem.thrash.v1` and `criticism.attack-target-entropy.v1` as shipped at Rung 2 are NOT §14's formulas.** ATH as shipped reads the whole standing attack relation; §14.2 reads newly carried attacks in a fixed sequence-number window with a declared rounding rule | Shipped before the Formalization arrived. Rung 8 adopts §14's definitions (R48) and must either re-found these two signals or declare them a distinct family — an unreconciled name collision is worse than either |

#### What joins the axiom basis

v0.1 **Axiom 4.1 (Genesis Inertness)** — all appraisal predicates are invariant
under permutation of provenance records; origin confers neither warrant nor
stigma — joins A1–A10 in the `INV-` document (R52). It is the one axiom that
comes from the foundational source rather than the reconstruction, and it
excludes inductivism, authority, and genetic dismissal of any generator in a
single line.

### 2N. The supersession clause, worked through (R54)

REQUEST.md Amendment 6: *"Everything in these documents supercede my previous
decisions."* A clause like this is only worth anything if someone actually walks
the previous decisions against the documents, so here is that walk. Every
previously-answered item, and what the documents do to it.

| Previous decision | Do the documents speak? | Outcome |
|---|---|---|
| **H1** — a failed conjecture mints nothing | Yes, compatibly. v0.1 Axiom 4.3: P2 arises from the CONTENT of a solution, not from a failure; problems enter by GEN like everything else. Formalization A8 lets REACH spawn promotion problems, which is a different trigger | **stands** |
| **H2** — the premise channel | Yes, compatibly. Formalization §9 is the cascade in full | **stands** |
| **H3** — status vocabulary at the view layer only | Yes. v0.1 §6 "no acceptance event" is the sharper statement of the same thing | **stands**, rowed as V-3 |
| **D-1** — crisis is a render state only | Yes, compatibly. §18: a wounded background may remain "refuted and still framing indefinitely, with its crisis RENDERED and its succession problem open" | **stands** |
| **D-3** — premises are derived, not stored | Yes, compatibly for the MARK (§9.2 derived, §9.3 lazy). **But A7 requires problems to immutably RECORD their pose-time frame assertions** — storage, at the frame layer | **stands, with a refinement Rung 4 must honour**: derived marks, recorded pose-time frames. They are different objects and only one is derived |
| **D-4** — ship `knowledge(a)` as a view | Yes, and it strengthens the obligation: §13 + Theorem 13.1 (attention-only) + §18 ("at most a fallible indicator") | **stands, strengthened** |
| **D-5** — a fixed finite DSL for σ | Only indirectly: A2 requires finite-budget deterministic verdicts, which a DSL gives and an arbitrary program does not | **stands** |
| **D-6** — program-first `accounts-for` | Yes: §3.5's three criteria become the checkable forms (R46) | **stands, refined** |
| **D-8** — what refutes a contentful-but-wrong premise | **Partly answered.** §1's split makes refutation UNILATERAL: one undefeated warranted attack suffices, no surviving rival required. What remains open is not the mechanism but the AUTHORITY — who may issue that warrant in a solo configuration | **narrowed**; the open half is authority, not epistemology |
| **ND-2** — restored-premise resolution | The Formalization explicitly records it as a GAP ("the core formalization records the gap explicitly") | **stays the operator's**; the documents decline to decide it |

**Nothing above flips.** What flips is one thing the operator asked for
directly, in Rider 1, and it lands on code already delivered:

| id | What was shipped | What the documents say | Resolution |
|---|---|---|---|
| **S-1** | `crit(a)` requires a SUBSTANTIVE commitment; structural checks must not satisfy it (Rider 1, verbatim) | §12.2: `crit(a) = 1[K_a ≠ ∅]` — the weak declaration test — and the substantive work lives in `load_k`, mechanism load-bearingness | **FLIPPED and re-founded in this tranche.** §12.2 closes the self-immunisation hole better than the shipped design did: an artifact attaching `json-wf` has a nonempty `K` and still fails, because its role variants pass the same check and the verdict vectors agree. Substantiveness became something the battery EXHIBITS rather than something the interface asserts |
| **S-2** | `active(a) = crit(a) ∧ mod(a)`, the Computable Calculus §6 names | §12.2's `demarcated_k(a) = crit(a) ∧ load_k(a)` | **renamed to the governing document's vocabulary.** Same shape; `mod`/`active` are gone rather than aliased, because two names for one predicate is how a codebase acquires two meanings |
| **S-3** | an LLM variator sampled per premise, variants recorded only in the fall trace | §12.1: the kernel must be replay-deterministic — EITHER a seeded total function OR explicitly logged variants | **met by the second road.** Every sample logs its variants, including the empty one, so a replay never needs to reproduce a provider call to know what the reading saw |
| **S-4** | equivalence via `hv._equivalent`, which falls back to embedding distance when the verdict vectors cannot decide | §12.2 defines a load-bearing variant by VERDICT-VECTOR difference and nothing else | **fixed.** An embedding distance is not a verdict; admitting it let a distant paraphrase count as a different claim |
| **S-5** | nothing | §12.2's closing line: "For empirical scopes, at least one commitment must be observation-valued" | **OWED, not implemented.** A premise has no scope object until frame assertions exist, so there is nothing yet to test "empirical" against. Rung 4 introduces σ; Rung 4 or 5 owes this clause |
| **S-6** | `hv._survival` scores an edit as surviving when it passes B0 and is inequivalent | §12.3's `I_i` requires RoleVariant ∧ BatteryInequivalent ∧ `Passes_{B^-HV}` — `B^-HV`, not B0, and no embedder in the equivalence test | **rowed, not changed here.** The HV estimator is not this tranche's surface and changing it would move a measure that live roots already carry. Whichever rung owns HV re-founds it on §12.3 |

**What this cost, stated plainly:** the demarcation criterion was designed three
times in one tranche — substantive-`crit`, then `crit ∧ mod`, then §12.2's
`crit ∧ load`. Only the third is governed by a document. The first two are in
the branch history and in this table, which is the honest place for them: a
reader who finds `active()` in an old commit should be able to learn here why it
is not in the tree.

### 2O. Deferred-essential (R55–R57)

REQUEST.md Amendment 7, sourced from `docs/STATE_OF_THE_PROGRAM_2026-08-14.md`
§6. The operator's own framing — *"not priority, but they seem essential"* — is
the disposition, and it is a real category rather than a polite deferral: these
are not nice-to-haves that fell off a list, they are commitments the program
has now written down so that shipping without them is a KNOWN absence instead
of an oversight.

| id | Row | Why it is essential | Disposition |
|---|---|---|---|
| **E-1** | **Proof debt.** Every derived judgment carries an itemized, attackable manifest of what it rests on: kernel-checked steps, open certificates (attackable conjectures such as slack embeddings), named axioms. Attacking a manifest item invalidates dependents ON RECOMPUTATION, not retroactively. Receipt format `KERNEL_CHECK / OPEN_CERTIFICATES / AXIOM_DEBT` | A result's authority is exactly the authority of its premises and apparatus, and the bill of materials has to stay stapled to the package. The harness already does this for ONE class of judgment — warrants carry validity nodes — and proof debt is that same discipline generalised to every derived judgment | **deferred-essential**; its own future rung, scheduled by the operator. Not in the current seven |
| **E-2** | **Duhem localization.** A problem whose target is a BUNDLE — theory + apparatus + interpretation — does not project blame onto any member without a STANDING LOCALIZATION CRITICISM. Blame assignment is adjudicated work | This is the H2 premise channel's cousin and it slots into the same machinery: an attribution says "π presupposes X"; a localization says "the fault in this bundle lies with member m". Both are ordinary attackable artifacts, and both exist to stop an automatic projection that would otherwise happen silently | **deferred-essential**; the same future rung |
| **E-3** | **Succession implements the STRONG relation.** "A good rival covering the same explicanda" is NOT a strict successor. Rigidity, non-immunization, and a STRICTNESS WITNESS are additionally required | The prose word "rival" invites the weak reading, and a succession program built on it admits non-successors — which then propagate into every place succession decides something. Cheaper to build strong than to re-found | **BINDS Rung 5 NOW.** Not deferred |

**On E-3's placement, checked rather than taken on the operator's word** (they
invited the check: *"unless the drift table finds Rung 5 needs (3) immediately —
it does"*). It does. `DECISIONS.md` records D-6 as blocking "Rung 5 (criterion
5), Rung 7", and Rung 5's work list builds five pinned criteria as programs, of
which `accounts-for` IS the succession relation. There is no version of Rung 5
that does not implement succession, so there is no version that can defer E-3.

**E-3 converges with R46 rather than stacking on it.** Rider 2 already routed
the Formalization §3.5's three criteria into D-6; §3.5's strict clause — "at
least one of recovery, criticism survival, or rigidity is strict" — is the
strictness witness E-3 names. Two authorities arriving at one requirement from
different directions is corroboration, not two requirements, and it is recorded
once so no rung implements it twice.

**What E-1 and E-2 change about the current seven: nothing, and that is the
point of writing them down.** Neither is smuggled into a rung it does not
belong to. What they do change is what a green gate MEANS at the end of Rung 8:
the program will have a working standing layer whose derived judgments do not
yet carry manifests, and a criticism layer that cannot localize blame within a
bundle. Both absences are now nameable, which is the difference between a
limitation and a defect.

### 2P. The external implementation advice, reconciled (R58–R65)

REQUEST.md Amendment 8. **Advisory, not binding** — the operator's own framing —
and the test they set is "adopt unless a delivered rung already contradicts it
with reasons". So each item is checked against what was actually delivered, and
where the advice and this program disagree the disagreement is recorded with the
reason rather than resolved by seniority.

#### The one item that is a check on delivered work — and it comes back ABSENT

**R63 / item (6).** Checked against the tree, not against memory:

    grep -q "SpawnTrigger.SUCCESSOR" src/deepreason/rules/spawn.py   # PASS, 2026-08-15

(Run by hand. `docs_verify` scans `docs/map/` only, so a `check:` line in this
document would be decorative — it is written as a command with its result and
its date instead, which is honest about what authenticates it.)

The refuted⇒successor loop is **still in `scan_spawns`**, gated on
`status.get(aid) != Status.REFUTED`, and no frontier-unchanged-under-refutation
regression exists. Rung 2 did not remove it and never claimed to: the ladder
assigns H1's deletion to **Rung 3**, and Rung 2 shipped the replacement channel
first precisely because *translate* had to exist before the successor trigger
could go. So the advice's finding is correct about the tree and correct about
what must happen next, and the operator's own disposition applies: **Rung 3a is
the next step, alone** — and "alone" forced a split, because Rider 2 had placed
the frame-separation invariant in the same rung. H1's deletion is now **3a**,
frame-separation is **3b**, and neither requirement moved or was dropped.

**One thing the advice's ordering worry does NOT apply to, checked rather than
assumed.** The advice warns that with the loop live, "refuting a malformed
question would itself automatically spawn a successor question". That pathology
is not live for what Rung 2 shipped, because the loop fires on artifacts that
ADDRESS a problem, and a filed premise is registered with no `problem_id` — it
never enters `addr`, so refuting it spawns nothing.

Both halves of that claim are now pinned WHERE THEY ARE RE-RUN — as two
`check:` lines in `DR-CON-problem-layer-lifecycle`, whose Traps section carries
the invariant and the reason it exists. Ran green on addition, 2026-08-15.

That is a reprieve, not a licence: the advice's concern binds fully the moment
problem-SUBJECT artifacts exist (R59), which is exactly why it sequences H1
before them, and why R63 stands.

#### Item by item

| # | Advice | Verdict | Where |
|---|---|---|---|
| R58 | manifest → validity node as EVIDENCE, so manifest attacks disable the attack pre-grounded | **adopt.** Nothing delivered contradicts it. Rung 2's rent warrant already carries its sample in the trace blob and declares it in ν, which is the same instinct one step short of the mechanism: a blob is readable, an evidence ref is ATTACKABLE | Rung D (E-1) |
| R59 | companion problem-subject artifacts; no fields added to `Problem`/`EpistemicState`/`Event` | **adopt**, and it is already this program's instinct — Rung 2 added no field to any of the three. The advice's "no new relation table in `EpistemicState`" rejection agrees with the same reasoning | claim substrate, after Rung 3 |
| R60 | closed discriminated claim union; the CONTROLLER compiles interfaces; models never choose ref roles | **adopt, and it retro-justifies a delivered choice.** Rung 2's critic contract carries a `premise` STRING and `rules/crit.py` builds the `mention` ref itself — the model never named a role. The advice would have this generalised into a typed union rather than one bespoke field | claim substrate |
| R61 | programs consume frozen fence-stamped inputs, never live graph state | **adopt, with one delivered tension named.** Rung 2's `premise_rent_sweep` and `demarcation.load` read LIVE state (the current battery, the current registry). They are not `program:` commitments — the rent battery is deliberately not evaluable — so the letter does not bind them, but the spirit does, and Rung 8's re-founding of the diagnostics is where this gets settled for the whole surface | Rungs 5, 7, 8 |
| R62 | P4's three-layer acceptance; **no live pilot before P4** | **adopt — and it DEFERS the pending live run.** See below | P4 tranche |
| R63 | confirm the successor loop is gone | **ABSENT — next step, alone** | Rung 3 |
| R64 | frame-separation violation ⇒ UNCONSULTABLE + typed diagnostic, never a manufactured refutation | **adopt**, refining R43. The distinction is the whole point: an unmet invariant is a reason to STOP TRUSTING a frame, never a reason to invent a defeat for it. Manufacturing a refutation would put an epistemic verdict on the graph to record an engineering fault | **Rung 3b** — split out of Rung 3 so H1 ships alone |
| R65 | embedder: install-time dependency, doctor warmup, typed capability disclosure; nothing installs inside a reasoning transaction | **adopt, binding on that tranche.** It is the all-configurations law in a new place: an absent capability is a typed disclosure, not a stop and not a silent self-repair | the embedder tranche |

#### R62 defers the pending live run, and that changes what the operator is owed

Rung 2's A19 — one guarded live run asking whether a real critic ever files an
attribution — is exactly "a live pilot judging premise extraction". Under R62 it
**must not run until P4 lands**. It was already blocked on a missing credential;
it is now ALSO deferred by policy, and the policy is the better reason: without
P4's citable-evidence flow, a live miss would be uninterpretable — nobody could
tell a critic that declined the invitation from a critic that never had the
evidence to take it up. Recorded so the operator is not asked for a key to run
something this program has just agreed not to run yet.

#### Where the advice and this program DISAGREE, with the reason

| Point | Advice | This program | Resolution |
|---|---|---|---|
| The `SUCCESSOR` enum member | KEEP as a legacy parser value; deleting "risks making already-recorded `ProblemProvenance` records unparsable for little functional benefit" | Rung 3 DELETES the member | **This program's answer stands, on the operator's own law.** The 2026-08-14 law retired exactly the compatibility obligation the advice is protecting: old roots are artifacts of their own version and are owed neither validity nor readability. The advice's cost — old records stop parsing — is real and is precisely what the law accepted. An advisory review cannot outrank a standing design law, and the reason is recorded here rather than left as a silent divergence |
| Tranche ordering | premise channel comes AFTER claim substrate, P4, and proof debt | premise channel was Rung 2, already delivered | **Not reopened.** The advice's ordering is better on one axis (evidence flow before live evaluation) and this program's is better on another (translate must exist before H1 deletes the successor trigger). The disagreement is resolved by R62 rather than by re-ordering: the channel ships, and the LIVE JUDGEMENT of it waits for P4 |

---

## 3. Errata entry candidates (R22)

Entries are **minted by the implementing tranches, not by this one**. The
ledger tail at `50e2397a9` ends at **E28**, so the next free number is **E29**;
numbers move fast, so each implementing tranche re-checks the tail before
minting rather than trusting the number below.

| Candidate | Document contradicted | What becomes false, and when |
|---|---|---|
| EC-1 (→ next free, ~E29) | `docs/harness-spec-v1.3.md` §3 spawn-trigger list ("failed verdict ⇒ successor problem (P2)") **and** §7's dependent sentence: "No bespoke sharpen-or-drop: the failed verdict already Spawns a successor problem (P2) — sharpening is the successor's job." | Both become false the moment Rung 2 lands. §7's sentence is the load-bearing one: it JUSTIFIES the absence of a sharpen-or-drop rule by pointing at the trigger H1 deletes. The entry must re-found that justification on the premise channel + discrimination (§1 H1), not merely note the deletion |
| EC-2 | `docs/COMPUTABLE_CALCULUS.md` §5 (the trigger list, stated as "exhaustive") and §9.6 ("The failed verdict spawns a successor problem as always") | Not contradicted by another document but by the OPERATOR's H1. Since the calculus is committed theory authority, a reader must be told that two of its sentences are deliberately not implemented, and why. Minted by Rung 2 |
| EC-3 | `docs/map/SUB-rules.md` (the successor-inheritance row, the `rsplit("Original problem: ")` note) and `docs/map/SEAM-ontology-x-rules.md` (its `test_successor_descriptions_do_not_nest` check) | **Not an errata candidate** — map documents move in the SAME COMMIT as the code (SCHEMA.md), so Rung 2 updates them rather than correcting them afterward. Recorded here so no one files it as errata |
| EC-4 | `docs/harness-spec-v1.3.md` §4 pseudocode label `accepted` | **Not an errata candidate** — H3 leaves every stored label unchanged, so §4 stays true. Recorded so the H3 rung does not "fix" a document that is not wrong |
| EC-5 | Any future document claiming the harness has no way to criticize a problem | Not yet written; recorded as a watch item for the audit family |

---

## 4. What is deferred, and what would bring it in

| Deferred | Why | What brings it in |
|---|---|---|
| Making Π a node set in `att` (problems as literal attack targets) | **Re-examined 2026-08-15**: no longer barred by record compatibility (that law is retired), and still rejected — the calculus does not ask for it, and within-version coherence makes a mid-program rewrite of event application costly for v2's own runs (§0) | Evidence from a live v2 run that the premise channel cannot express a criticism the operator wants made |
| A learned response controller for capture | v1.3 §11.4 defers it for the meta-attractor risk; the calculus's §10 does not reopen it | Out of the v2 program by both authorities |
| `refl`'s unreferenced status (2026-08-13 dead-code census) | P6-adjacent but pre-existing and independently parked | Stays in `experiments/2026-08-13-audit/PARKED.md` P2 |

---

## 5. PARKED items the v2 program absorbs (R19)

| Park | Where it lives | What it asked | Absorbing rung | How the v2 design answers it |
|---|---|---|---|---|
| **P4 — evidence citability** | `experiments/2026-08-13-change-lifecycle-operation-parity/PARKED.md` P4 | Citable evidence blocks reach SEED conjectures only (0 of 36 sub-problem prompts), and the quote is requested as optional (101 verified citations, 0 quotes) | **Rung 5** (render semantics) | The frame slice forces the general question P4 raises — what a pack deterministically carries for a problem that INHERITED its context. Rung 5's deterministic section allocation covers inherited citable sets in the same pass as the frame slice, because both are "what does a derived problem see". **Only the render half is absorbed**; the quote-wording half (P4b) is a separate prompt change and stays parked |
| **P5 — conviction criteria** | same file, P5 | Should a refutation tighten what the next conjecture must satisfy? Four options priced (A–D); the operator's framing: knowledge growth should shrink the space of REACHABLE conjectures | **Rung 2** (spawn-trigger deletion + premise channel) — **answered, with option C** | v2 answers P5 directly: criteria do NOT accrete from convictions (that would mint obligations from failures, which is what H1 deletes). Reachability narrows on the problem layer instead — through premise-criticism (a refuted premise removes whole families of posable problems) and through the anti-relapse gate's negative case law (P5's own option C, "already specified, needs no new semantics"). Rung 2's SPEC must record this as P5's answer, with A/B/D rejected and the reason stated |
| **P6 — anti-relapse degradation** | same file, P6 | The relapse gate ran degraded for a whole run (250 candidates, embedder fallback, zero blocks), and nothing in the typed result said so | **Rung 2** | Rung 2 leans on the negative-case-law gate as half of P5's answer, so it cannot ship on a gate that can be silently inert. Rung 2's gate includes a typed operational finding when the relapse gate is unarmed. The policy question P6 raised — whether to REFUSE to start — stays with P6's own tranche |
| **the signal-contract park** | **not in the tree** — supplied by the operator 2026-08-14 (REQUEST.md Amendment 2), "ledgered with the monitor, 2026-08-13" | The six-clause signal-contract design: registry-as-contract, seat-instance keying, interface-only controller consumption, a compiled topology matrix, open-loop disclosure, and the FROZEN/VERSIONED/FREE change protocol | **Rung 1** (the CLAUDE.md design law) + **Rung 1b** (everything else) | Fully absorbed; the six clauses are drift rows SC-1 … SC-6 in §2L, and the placement argument is there. The earlier "NOT FOUND" entry was correct on its facts — the design was never committed to this repository — and the searches it recorded are what established that, rather than a guess. Candidate (i), the existing 89-tag registry, is **included** by the operator's own clause (1) rather than superseded |

---

## 6. Batched decision sheet

Delivered as the final artifact: **`DECISIONS.md`**, seven items (D-1 … D-7),
each with priced options and one recommendation. Titles only, here:

| # | One-line decision |
|---|---|
| D-1 | Under H1, is the §9.6 crisis a render state only, or does it get its own standing-layer spawn trigger? |
| D-2 | ~~Confirm the reconstructed siren case, or supply the original.~~ **ANSWERED 2026-08-14 — Road B; the original is in REQUEST.md Amendment 1 and the sequence is rewritten.** |
| D-3 | Is `provenance.frame` derived (v2's recommendation) or stored as the calculus literally writes it? |
| D-4 | Does the harness ship `knowledge(a)` (Def 8.1) as a user-facing view? |
| D-5 | What language expresses a scope predicate σ — a fixed finite DSL or an arbitrary program artifact? |
| D-6 | Succession is comparative; the operator distrusts judges. Program-first `accounts-for`, or a judge ensemble? |
| D-7 | ~~Which park was "the signal-contract park"?~~ **ANSWERED 2026-08-14 — option (iii); the design is in REQUEST.md Amendment 2, reconciled as §2L, placed at Rungs 1 + 1b.** |
| **D-8** *(added by Amendment 1)* | **When a premise is contentful but wrong-by-argument — not a category error — what refutes it, given that prose changes no status by default and the one trial mode that would is cross-family?** (drift row W-1) |
| **ND-2** *(added by Amendment 4)* | **When a fallen premise is REINSTATED, what happens to the orphan mark — derived-view deactivation with the exit episode retained, or a fourth `revalidate` resolution?** (Formalization §1's explicitly recorded gap) |
