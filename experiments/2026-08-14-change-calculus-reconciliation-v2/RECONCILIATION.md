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

The cost of the alternative — making Π a node set in `att` — would be a rewrite
of frozen surfaces 2 and 3 and the invalidation of every committed root. The
calculus's own design avoids it. **This is the single most important thing the
implementing tranches must not forget.**

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

**The siren case — a complete legal move sequence (R10).**

> **Reconstruction notice.** The siren example is named in the operator's
> doctrine but is not quoted in the tranche brief and appears nowhere in this
> repository (`grep -rni siren --include=*.md .` returns nothing outside this
> tranche). What follows is the canonical Doppler-shaped reconstruction, marked
> as a reconstruction. `DECISIONS.md` D-2 asks the operator to confirm it or
> supply the original. The MOVE SEQUENCE is what matters and is
> example-independent; only the content of X would change.

Seed problem **π₁**: *"Why does the siren's pitch drop as the ambulance passes?"*

| # | Rule | Move |
|---|---|---|
| 1 | `Spawn(seed)` | π₁ registered. No attribution yet. |
| 2 | `Conj` | candidates c₁, c₂ on π₁ — accounts of a mechanism by which the emitted pitch falls. Both may stand unrefuted for a long time. |
| 3 | `Conj`/`Register` | a critic registers **X** = "the siren's emitted pitch falls as the ambulance passes", with an observation-valued commitment ("a recording at the source shows a falling emitted frequency"). |
| 4 | `Register` | **ρ** = "π₁ presupposes X": `mention` → X (Law 9.4′), `dependence` → its case (that every candidate on π₁ assumes it, and that π₁'s own criteria quote the falling pitch). ρ passes `presupposition-wf` ⇒ consulted. |
| 5 | `Crit` | a demonstrative warrant against X: the observation-valued commitment FAILS — the source recording shows a constant emitted frequency. Carried by a critic artifact with validity node ν asserting the test was sound and relevant; ν carries an `evidence` ref to the recording (Closure 3). |
| 6 | `Adj` | Pass 1: X is **refuted**. Pass 2: ρ is untouched — it only mentions X (Law 9.4′). So `premise_orphaned(π₁)` = true, grade **premise refuted**. The mark is lazy; π₁ is deprioritized in scheduling (C5). |
| 7a | orphan resolution — **retire** | holding: "there is no fall in *emitted* pitch to explain." π₁ leaves the frontier, logged, never deleted (P8). c₁ and c₂ keep their own labels: **orphaned ≠ false**, at the problem layer exactly as at the artifact layer. |
| 7b | orphan resolution — **translate** | successor problem **π₂**: *"Why does the OBSERVED pitch fall as the ambulance passes?"* — posed in the succeeding vocabulary (source frequency vs. observed frequency), provenance recording the lineage from π₁ and ρ. **This is the only way a successor problem is minted in v2** (H1). |
| 7c | orphan resolution — **independence** | holding: π₁ never needed X — it always meant "why does the SOUND change as it passes". The orphan closes; the scheduler thereafter treats π₁ as unorphaned, computed from the resolution. π₁'s own record is never mutated. |
| 8 | `Crit` — the **faulty instrument**, the operator's other named example | attack the RECORDING, or anything in its transitive `dependence` lineage: "the source microphone clipped." Accepted ⇒ ν falls ⇒ the warrant falls ⇒ **X reinstates** (Lemma 6.1, Closure 3) ⇒ `premise_orphaned(π₁)` becomes false by the same computed predicate. If π₁ had already been retired, the retirement closure is itself an ordinary artifact and is attacked on the ground that its premise reinstated; π₁ returns to the frontier. |

**Where the operator's sentence lands.** *"The problem itself is the subject of
criticism, which is summarily refuted"* is move 7a: the problem died **without
any conjecture on it having to fail** — directly, by an attack on what it
presupposed. That is what "summarily" buys. And it happens without putting
problems into `att` (§0).

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
`accepted`; a string **rendered to a reader** may say `unrefuted`. Machine JSON
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
| P-4 | P4 explanatory demarcation, BOTH halves: forbids something AND explains; a non-load-bearing mechanism is refuted by program, untested | v1.3 §6 `crit ∧ mod`; §10.1 `skeleton-wf` requires `forbidden ≠ ∅` | `measures/demarcation.py`; `skeleton_wf`. **The mechanism-load-bearing half — "role-level substitution or deletion of it flips verdicts" as a ROOT-BATTERY criterion — is not pinned into every problem**; it exists only as `hv-floor` on connection problems (v1.3 §7 Brake 1) | **adapt** — Rung 4 pins a mechanism-load-bearing criterion into the root battery for empirical scopes, reusing `µ_struct`, which already does role-level substitution. Guardrail: it is a CRITERION, never a gate (C5) |
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
| O-5 | Def 3.4 warrant + validity node + **three** closures (validity, case-law, evidence) | v1.3 §1: all three | all three in `adjudication/edges.py`, computed as a fixpoint | **adopt** |
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
| M-1 | demarcation `crit ∧ mod` | v1.3 §6 identical | `measures/demarcation.py` | **adopt** |
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
| Making Π a node set in `att` (problems as literal attack targets) | It would rewrite frozen surfaces 2 and 3 and invalidate every committed root (§0). The calculus does not need it | Nothing short of an explicit operator decision to break record compatibility |
| A learned response controller for capture | v1.3 §11.4 defers it for the meta-attractor risk; the calculus's §10 does not reopen it | Out of the v2 program by both authorities |
| `refl`'s unreferenced status (2026-08-13 dead-code census) | P6-adjacent but pre-existing and independently parked | Stays in `experiments/2026-08-13-audit/PARKED.md` P2 |

---

## 5. PARKED items the v2 program absorbs (R19)

| Park | Where it lives | What it asked | Absorbing rung | How the v2 design answers it |
|---|---|---|---|---|
| **P4 — evidence citability** | `experiments/2026-08-13-change-lifecycle-operation-parity/PARKED.md` P4 | Citable evidence blocks reach SEED conjectures only (0 of 36 sub-problem prompts), and the quote is requested as optional (101 verified citations, 0 quotes) | **Rung 5** (render semantics) | The frame slice forces the general question P4 raises — what a pack deterministically carries for a problem that INHERITED its context. Rung 5's deterministic section allocation covers inherited citable sets in the same pass as the frame slice, because both are "what does a derived problem see". **Only the render half is absorbed**; the quote-wording half (P4b) is a separate prompt change and stays parked |
| **P5 — conviction criteria** | same file, P5 | Should a refutation tighten what the next conjecture must satisfy? Four options priced (A–D); the operator's framing: knowledge growth should shrink the space of REACHABLE conjectures | **Rung 2** (spawn-trigger deletion + premise channel) — **answered, with option C** | v2 answers P5 directly: criteria do NOT accrete from convictions (that would mint obligations from failures, which is what H1 deletes). Reachability narrows on the problem layer instead — through premise-criticism (a refuted premise removes whole families of posable problems) and through the anti-relapse gate's negative case law (P5's own option C, "already specified, needs no new semantics"). Rung 2's SPEC must record this as P5's answer, with A/B/D rejected and the reason stated |
| **P6 — anti-relapse degradation** | same file, P6 | The relapse gate ran degraded for a whole run (250 candidates, embedder fallback, zero blocks), and nothing in the typed result said so | **Rung 2** | Rung 2 leans on the negative-case-law gate as half of P5's answer, so it cannot ship on a gate that can be silently inert. Rung 2's gate includes a typed operational finding when the relapse gate is unarmed. The policy question P6 raised — whether to REFUSE to start — stays with P6's own tranche |
| **the signal-contract park** | **NOT FOUND** | — | — | Named in the brief; no park by that name exists in the tree. Searched: every `experiments/*/PARKED.md` heading; every `.md` for `signal[- _]contract`, `signals contract`, `contract of signals`; the model-signal contract of v1.5 §H (`stuck`/`complete`/`need_context`/`capability_mismatch`); the signal REGISTRY (`src/deepreason/signals.py`, whose docstring is "every measure tag the harness emits, documented once", AST-enforced by `tests/test_signals.py`). Nearest candidates: (i) that registry — every new v2 signal must be registered there, which Rung 1 would own; (ii) `experiments/2026-08-13-change-results-retrieval-surface/PARKED.md` P2, which names `signals.py` among readers the map does not own. **`DECISIONS.md` D-7 asks the operator which was meant.** Until then, Rung 1 carries the registry obligation on the assumption it is (i) — the cheap, certainly-correct half |

---

## 6. Batched decision sheet

Delivered as the final artifact: **`DECISIONS.md`**, seven items (D-1 … D-7),
each with priced options and one recommendation. Titles only, here:

| # | One-line decision |
|---|---|
| D-1 | Under H1, is the §9.6 crisis a render state only, or does it get its own standing-layer spawn trigger? |
| D-2 | Confirm the reconstructed siren case, or supply the original. |
| D-3 | Is `provenance.frame` derived (v2's recommendation) or stored as the calculus literally writes it? |
| D-4 | Does the harness ship `knowledge(a)` (Def 8.1) as a user-facing view? |
| D-5 | What language expresses a scope predicate σ — a fixed finite DSL or an arbitrary program artifact? |
| D-6 | Succession is comparative; the operator distrusts judges. Program-first `accounts-for`, or a judge ensemble? |
| D-7 | Which park was "the signal-contract park"? |
