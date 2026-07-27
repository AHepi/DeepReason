# Conjecture–Criticism Harness — Formal Build Spec

**Status:** build spec, **v1.3**. Source: *The Necessity of Creativity* (creativity-calculus).
**Audience:** implementing LLM / engineer. Rationale lives in the companion human-readable plan; this file is normative and terse.

**Implementation clarifications:** warrant carriage is an explicit append-only
`carry ⊆ A × W` relation and is not part of artifact identity; validity nodes
grounded in recorded evidence use an `evidence` ref whose dependency lineage
participates in attack closure. Both keep status computation inside `att`/`dep`.

**Changes from v1.2** (capture control; all via attention/provenance/gates — no new acceptance semantics, no types):

1. **New §11 (Capture control).** Two capture surfaces named: generator (variation collapse) and adjudicator (criticism ritualizing). Schools — islands in conjecture, panmixia in criticism — with lineage-based constitution and provenance-ownership allocation (no per-problem curation). Graph-native ritual detection + generator-side embedding detection, all as replay programs over the event log. Exogenous grounding ratio λ with floor + reactive brake. Response ladder as logged scheduler rules with hysteresis. Old §§11–16 renumbered §§12–17.
2. **Anti-relapse upgraded** with a semantic-neighbor trigger stage (§11.5): embedding proximity to a refuted artifact triggers the existing battery-equivalence check; near-duplicates of *accepted* artifacts are never blocked (attention-deduped only — blocking them would be a diversity gate adjudicating).
3. **Atlas split** (§11.5): positive case law stays pack-side (precedent slices, §10); negative case law (refuted-region index) lives at the registration gate and is never rendered into packs.
4. **Conjecturer contract → Verbalized Sampling** (§11.6, §9): γ-calls return a candidate distribution with typicality estimates, not a point.
5. **Pareto retention** (§11.7): scheduler focus and reports keep the frontier over (HV, reach, coverage) instead of argmax-HV. Attention and reporting only.
6. **§1:** `provenance.school` added (epistemically inert by D2 — provenance is never a warrant, so schools cannot enter adjudication by construction). Event rule enum gains `Reseed`; embedder outputs logged as raws.
7. **§9/§10.4:** `embedder` role; cross-family judge/critic assignment (foreign-reviewer rule); planted self-preference/verbosity probes added to judge audits.
8. **§16 (Phases):** P2 scope gains capture-control machinery; P2 acceptance gains the pre-registered λ dose-response collapse experiment (§11.8) and a school-divergence/reseed replay test. **§17 (Residue)** extended.

**Changes from v1.1 → v1.2:** §10 informal-domain protocol (skeletons + forbidden cases, trial guard, standards-as-case-law with closure extension, judge audits, holdout/`Reveal`, user appellate, µ_struct); rubric warrants valid only with trial transcript.
**Changes from v1 → v1.1:** `HV_MIN` acceptance gate and "easy-to-vary ⇒ suspended" removed — floor relocated into connection-problem criteria as `hv-floor`; fail ⇒ demonstrative warrant ⇒ refuted, reinstateable via ν. Measures-never-adjudicate invariant added. "Coupling = reach" corrected to "reach tracks coupling."

---

## 0. Core invariant (do not violate)

- The **harness is deterministic and carries all epistemology**. The LLM is a bounded pure function: `pack -> schema-validated JSON`. The LLM MUST NOT hold graph state, adjudicate, or control flow. It is the conjecture operator γ (Def 4.1), nothing more. Justified by D2 (generator-agnostic).
- **Artifacts are untyped** (Def 3.2). There is NO `kind` field. Dispatch is on interface structure only: an attack edge exists where an artifact carries a warrant against a target; a support edge exists where an artifact's interface declares a `dependence` ref on a target. Informal-domain discipline (§10) and capture control (§11) enter exclusively through problem criteria, content conventions, standard artifacts, provenance, and scheduler policy — never through types.
- **Content is Σ\*** (Def 3.1, Thm 2.1): opaque bytes + codec. Text, numeric, CSV, code all in scope. Meaning is imposed by conjecture and checked by program.
- **Nothing is deleted** (D8). Status is computed, never stored as ground truth. The event log is the source of truth; graph state is a materialized view.
- **Measures never adjudicate; search control steers attention, never status.** HV, reach, conn/iso, novelty/diversity/school signals, Pareto rank, and capture diagnostics influence the graph only by (a) Spawning problems, (b) being packaged as budgeted commitments whose `fail` verdicts generate warranted attacks (§7), or (c) steering scheduler attention, pack rendering, and budgets (§11). They MUST NOT appear as inputs to label computation (§4).

## 1. Ontology (one schema)

**Artifact**

```json
{
  "id": "sha256(canonical(content_ref, codec, interface))",
  "content_ref": "<blob-hash> | <inline-string>",
  "codec": "utf8 | json | csv | f64le | i64le | code:<lang> | raw",
  "interface": {
    "commitments": ["<commitment-id>", "..."],
    "refs": [{ "target": "<artifact-id>", "role": "dependence | mention | evidence" }]
  },
  "warrants": ["<warrant-id>", "..."],
  "provenance": { "role": "conjecturer|critic|variator|synthesizer|seed|import|user", "school": "<school-id>|null", "event_seq": 0 }
}
```

- `refs[].role == "dependence"` ⇒ contributes a support edge (this → target) to `dep`.
- Warrant carriage is logically an explicit append-only relation
  `carry ⊆ A × W`. `artifact.warrants` is its legacy/on-record shorthand, not
  part of artifact identity. A later event MAY add `(artifact, warrant)` to
  `carry` without changing the artifact id. Each pair contributes an attack
  edge `(artifact → warrant.target)` to `att`.
- `refs[].role == "evidence"` is permitted on a warrant validity node and
  declares load-bearing evidence. Attackers of that evidence, or of anything
  in its transitive `dependence` lineage, attack the validity node during
  `att` construction. Plain `mention` refs remain non-load-bearing.
- `dep` MUST remain a DAG. Reject any dependence ref that would create a cycle.
- `provenance.school` records which conditioning regime (§11.1) generated the artifact. Provenance is never a warrant (D2), so school membership is epistemically inert **by construction**: it can shape packs and scheduling, never adjudication.

**Commitment** (Def 3.1)

```json
{
  "id": "...",
  "eval": "program:<ref> | rubric:<spec-id> | predicate:<expr>",
  "budget": { "steps": 100000, "time_ms": 2000 },
  "observation_valued": false
}
```

- `budget` is a structured object interpreted by the test program τκ. Canonical keys: `steps`, `time_ms`; program evals may declare extended structured budgets (e.g. `k`, `per_edit_steps` for `hv-floor`, §7). Total resource is always finite and declared.
- Verdict `V(κ, c) = U^{≤β}(τκ, c) ∈ {pass, fail, overrun}`. Extensional, budgeted, decidable (budgeting keeps Rice at bay).
- **Budget honesty is deterministic (§0).** A verdict is a pure function of content: wall-clock time never drives it, and no wall-clock value enters the content-addressed trace — otherwise two harnesses replaying identical inputs under different machine load would fork their logs. Budget enforcement, where a program enforces one, must be a deterministic bound (step count, item count); `time_ms` is a declared intent, not a verdict input. `overrun` therefore means "the verdict is unobtainable within the declared deterministic budget" (e.g. no variator kernel available, §7) — never "the machine was slow".
- **Oracle isolation is not adjudication.** Untrusted candidate, checker,
  generator, and gate modules execute in a fresh subprocess, with the
  deterministic step tracer installed before module top-level code runs. OS
  memory/CPU ceilings and a parent watchdog are emergency containment only. A
  containment kill produces no epistemic verdict and MUST NOT mint a warrant,
  confer execution supremacy, enter a verdict cache, or mark a fuzz target
  clean. The implementation exposes this no-result condition through the
  existing `overrun` API envelope plus `sandbox_abort`; it is outside `V` and
  must not be written as evidence.
- `eval:program|predicate` ⇒ computed by execution (reliable).
- `eval:rubric` ⇒ computed by the judge LLM role under the trial protocol (§3 guard, §10). `<spec-id>` MUST resolve to a registered **standard artifact** (§10); the standard's content specifies the evaluation mode: `absolute | anchored | pairwise`. Noisy; every structural mitigation in §10 applies.
- `observation_valued == true` and no covering evidence artifact ⇒ Spawn a research problem (§12). Evidence registered **sealed** (holdout, §10) does not count as covering before its reveal; the commitment is scheduled-pending, not failed.

**Warrant** (Def 3.4)

```json
{
  "id": "...",
  "target": "<artifact-id>",
  "type": "demonstrative | argumentative",
  "commitment": "<commitment-id>",      // demonstrative: the κ that failed on target
  "verdict": "fail",                     // demonstrative
  "trace_ref": "<blob-hash>",            // demonstrative
  "validity_node": "<artifact-id>"       // ν(κ): asserts the test is sound & relevant
}
```

- **Closure rule:** any attacker of `validity_node` attacks the warrant (hence its carrier's attack edge). Enforce in `att` construction.
- **Closure extension (case law):** the ν of any rubric-derived warrant MUST carry a `mention` ref to the standard artifact it applied. `att` construction adds an edge (x → ν) for every registered attacker x of that standard. Consequence, all in pass 1: refute a standard ⇒ every ν citing it is attacked ⇒ every warrant under it falls ⇒ targets reinstated (Lemma 3.1 mechanics). This is the parallel-fifths reinstatement, computed, not curated.
- **Closure extension (evidence):** a ν grounded in recorded evidence MUST
  carry an `evidence` ref to it. `att` construction adds `(x → ν)` for every
  attacker `x` of the evidence or any artifact in its transitive dependence
  lineage. The ordinary closure rule then attacks every carrier of the
  warrant, so invalidating a source can reinstate the target without any
  status rule outside `att`/`dep`.
- Both warrant types are contentful (packaged in artifacts); **a bare verdict is never an edge**.

**Problem** (Def 3.2)

```json
{
  "id": "...",
  "description": "string",
  "criteria": ["<commitment-schema-id>", "..."],   // instantiated per candidate; Popper battery auto-pinned
  "provenance": {
    "trigger": "seed|successor|discrimination|remove-arbitrariness|explanation-debt|audit-critic|connection|integration",
    "from": ["<id>", "..."]
  }
}
```

**Epistemic state** (materialized view; Def 3.3)

```
S = (A, Π, carry, att, dep, addr, status, hv, reach, conn)
```

Recompute from the event log at any `seq` for time-travel. A historical view
is physically read-only: opening it MUST NOT create directories, repair a
torn log tail, materialize a reveal, or write objects, blobs, or events.

**Event** (source of truth; append-only JSONL)

```json
{
  "seq": 0, "ts": "iso8601",
  "rule": "Conj|Crit|Adj|Spawn|Refl|Register|Merge|Measure|Reveal|Reseed",
  "inputs": ["<id>"], "outputs": ["<id>"],
  "llm": { "role": "...", "model": "...", "endpoint": "...", "prompt_ref": "<blob>", "raw_ref": "<blob>", "tokens": 0, "ms": 0 },
  "state_diff": { "carry+": [], "att+": [], "dep+": [], "A+": [], "Π+": [], "status_changed": [] }
}
```

Embedder calls (§9, §11) are logged exactly like any other role — prompt/input ref + raw output ref — so every diagnostic in §11.3 is replay-deterministic from the log.

## 2. Formation rules (well-formedness; §3.2)

A state is well-formed iff: every `(carrier,warrant)` pair names a registered
artifact and warrant; every attack edge derives from such a pair; every problem
criterion is a commitment schema; every `addr` pair is declared; the
validity-node closure (including case-law and evidence extensions) holds; `dep`
is acyclic; **and every rubric-derived demonstrative warrant's `trace_ref`
contains a conforming trial transcript (§3 rubric-verdict guard)**. All
transition rules preserve well-formedness.

## 3. Transition rules (§3.3)

| Rule  | Enabling condition                          | Effect |
|-------|---------------------------------------------|--------|
| Conj  | `Π ≠ ∅`; a problem π selected               | `a = γ(π, S)` via conjecturer role under the assigned school's render policy (§11.2), born-connected (§7); `A += a`, `addr += (a,π)`, interface attached |
| Crit  | target `a ∈ A`; a valid warrant `w` for `(k,a)` | register `k` if new; `carry += (k,w)`; derive `att += (k,a)` |
| Adj   | after any registration                      | recompute two-pass labels (§4) |
| Spawn | any trigger below                           | register new problem with provenance |
| Refl  | always available                            | rule-artifacts, demarcation criterion, adjudication semantics, standards, guard procedures, and school-policy artifacts are registered artifacts in `A`, attackable |

Conj is gated on `Π ≠ ∅` — D1 made structural. No problem, no conjecture.

**Spawn triggers (all of them):**

- failed verdict ⇒ successor problem (P2)
- ≥2 surviving rivals for one π ⇒ discrimination problem (in informal domains, resolved comparatively; §10)
- accepted `a` with low HV ⇒ remove-arbitrariness problem
- reach event ⇒ explanation-debt problem
- critic-gaming signal ⇒ audit-the-critic problem. Signals include: judge-ensemble disagreement, rubric-guard failure streaks, calibration error rate > `JUDGE_ERR_MAX`, paraphrase-flip audit hits (§10), and adjudication-ritual flags (§11.3)
- `iso(a) > 0` ⇒ connection problem (§7)
- ≥2 accepted artifacts on overlapping problems with no declared relation ⇒ integration problem (§7)

**Reinstatement is derived, not a rule** (Lemma 3.1): if `k` attacks `a`, `j` attacks `k`, `j` unattacked, then `{j,a} ⊆ G`. Falls out of §4 Pass 1.

**Anti-relapse (registration guard, MANDATORY before Conj commit)** — three stages, cheap first (§11.5 details):

1. **Hash:** candidate id matches an existing refuted artifact ⇒ block.
2. **Semantic trigger (new):** embedding nearest-neighbor against the refuted index within `NEAR_DUP_EPS` ⇒ run stage 3 against that prior.
3. **Battery equivalence:** candidate's verdict-vector over the active battery matches a refuted prior's (`≈_B`, Def 3.5) ⇒ block **unless** the candidate carries a warrant against that prior's refuter. Verdicts differ ⇒ admit; log the near-miss (capture diagnostic, §11.3).

Blocking occurs **only** for relapse onto refuted-equivalents. Near-duplicates of *accepted* artifacts are never blocked — they register normally; the scheduler withholds criticism budget from `≈`-redundant twins and the near-duplicate rate feeds §11.3. (Blocking non-refuted content would be a diversity gate adjudicating — forbidden by §0.)

**Rubric-verdict guard (registration guard, MANDATORY before Crit commit of any rubric-derived warrant):**

1. **Trial transcript.** critic role drafts the case for `fail`, citing specific clauses/cases; `defender` role answers; judge rules on the exchange. The ruling MUST populate `decisive_point` — a reference to a specific element of the exchange.
2. **Referential integrity** (program check): `decisive_point` resolves to an actual element of the transcript. Unresolvable ⇒ invalid ruling.
3. **Order-swap consistency** (pairwise/anchored modes only, program-orchestrated): run both presentation orders; same winner required, else no warrant.
4. **Paraphrase spot-check:** re-run the ruling on `TRIAL_PARAPHRASE_N` variator-generated paraphrases of the exchange; any flip ⇒ no warrant.

Only surviving rulings are packaged as warrants; `trace_ref` = full transcript + all check results. Blocked rulings are logged, never registered as attacks; a streak of blocks is a critic-gaming signal (Spawn). Rationale: an unreliable verdict is not a valid warrant — this is a warrant-validity condition (§2), the same species of rule as anti-relapse, and it suppresses noise, not criticism (the critic's *argumentative* case may still register on its own merits as an argumentative warrant).

## 4. Adjudication — two-pass (normative pseudocode)

```python
# Pass 1: attack (Dung grounded extension; unique, skeptical, polynomial)
F(X) = { a ∈ A : for all (b,a) in att, exists c in X with (c,b) in att }
G = least fixed point of F starting from ∅
label0(a) = accepted   if a in G
            refuted    if exists b in G with (b,a) in att
            suspended  otherwise

# Pass 2: support (compiled into Dung; deviation from vanilla, registered via Refl)
# process dep-DAG in topological order (dependencies before dependents)
for a in toposort(dep):                      # a -> b means "a depends on b"
    supported(a) = all(final(b) == accepted for (a,b) in dep)
    if label0(a) == accepted and supported(a): final(a) = accepted
    elif label0(a) == accepted:                final(a) = suspended_unsupported
    elif label0(a) == refuted:                 final(a) = refuted
    else:                                      final(a) = suspended
```

- Refuting a premise ⇒ dependents become `suspended_unsupported`, NOT `refuted` (orphaned ≠ false).
- Attacking a relation artifact directly ⇒ that relation `refuted` while its endpoints may stay `accepted`.
- Recompute after every registration. This realizes D4; N1 (§5) keeps every label revisable.
- **Inputs to adjudication are `att` and `dep` ONLY.** Measures, school membership, novelty/diversity signals, and Pareto rank MUST NOT enter label computation; they act upstream — via Spawn, via commitments whose fail verdicts generate warranted attacks (§0, §7), or via attention (§11).

## 5. Fallibilism axioms (§3.5) — enforce as invariants

**N1 (no absorbing status):** every status admits an exit. `accepted→refuted` by new warranted attack; `refuted→accepted` by reinstatement; demonstrative refutation reopens via attack on its `validity_node`; rubric verdicts additionally reopen via attack on their standard (closure extension, §1). No artifact — rule-artifacts, standards, school policies, user rulings included — is ever marked final. N1 is the premise Theorem 4.1 consumes.

**N2 (perpetual proposability):** γ's support is unbounded; for every `accepted a` there exist proposable successors with strictly extended batteries. §11 is N2's practical enforcement arm: it exists because a conditioned generator's *effective* support can collapse while its in-principle support stays unbounded.

Fallibilism is axiom, not theorem (D7): do not attempt to certify HV=1 or any final state.

## 6. Measures (§3.4)

**Demarcation (replaces falsifiability)**

```
crit(a)   ⇔ interface.commitments ≠ ∅                      # nonempty attack surface
mod(a)    ⇔ Pr_{a'~µ(·|a)} [ a' ≉_B a ] > 0                # nontrivial variation surface
active(a) ⇔ crit(a) ∧ mod(a)
```

Empirical falsifiability = special case of `crit` where a commitment is observation-valued. For informal content, the skeleton discipline (§10) makes `crit` real rather than nominal: each forbidden case compiles to a commitment, so an artifact that forbids nothing has an empty attack surface and fails demarcation — Deutsch's sense, made structural.

**Hard-to-vary (Def 3.6) — lazy, accepted artifacts only**

```
variator emits k bounded edits {a'} via µ(·|a)
s(a)    = Pr[ a' passes B(a) ∧ a' ≉_B a ]                  # inequivalent survivors only
HV_B(a) = 1 - s(a)
```

`k ∈ [5,10]` local. Count only inequivalent survivors (a rename is the same explanation). Estimable to (ε,δ) by Hoeffding. Log the estimate + k; it is a spot-check, re-estimable later.

**Structural kernel `µ_struct` (mandatory where available):** when content parses as a skeleton (§10), µ MUST substitute at role level — swap the mechanism, the motive, the causal link, the scope — not merely reword. This is the Persephone test: if any god and any crime slot in and the account still "passes," survivors abound and HV is low. Rewording-only µ measures phrasing rigidity and is declared insufficient for D5. Applies to both the lazy spot-check here and `hv-floor` (§7).

HV can additionally be packaged as a budgeted commitment (`hv-floor`, §7); the stratification rule there (estimate over B₀, HV-type commitments excluded) prevents self-reference.

**Theory-level HV** (required for real D5): run µ over structure of a bundle — drop a component ref, swap a relation, substitute a mechanism — count inequivalent survivors. Claim-level HV alone measures phrasing rigidity only.

**Reach** (Def 3.7)

Periodic budgeted cross-evaluation of accepted artifacts against other problems' criteria; a hit raises standing and Spawns an explanation-debt problem. Reach tracks coupling (Prop 4.1), asserted as a modelling commitment (attackable), not a proven bound. In informal domains reach is the hardest currency available (§10): the event log timestamps what an artifact was built for, so "accounts for something it wasn't built for" is verifiable in the trace, and reach hits on **held-out** material are the highest-signal event the informal side produces.

## 7. Unification reflex (coupling → reach → unification)

Three layers + guardrails. Correction from v1: Def 4.2 coupling and Prop 4.1 reach are **not** the same parameter — coupling is a property of γ, reach a measured outcome of artifacts; reach *tracks* coupling (Prop 4.1). The reflex is still not a new drive: it strengthens coupling on every conjecture and lets reach be discovered rather than designed.

**L1 — born-connected conjecture (the reflex):** every Conj pack includes the target's neighbourhood; the conjecturer is instructed to carry `dependence`/relation commitments to neighbours where natural. Fires on every thought. Rendered per-school (§11.1): neighbourhood weighting is part of the school's render policy, so coupling is preserved while conditioning diverges.

**L2 — isolation floor (safety net):**

```
conn(a) = #{ accepted dependence edges a participates in }
iso(a)  = max(0, FLOOR - conn(a))
```

`iso(a) > 0` ⇒ Spawn a cheap connection problem against top-`K` neighbours (rank: shared problem > shared refs > lexical/embedding overlap). Runs under `INTEGRATION_BUDGET_SHARE` of cycles.

**Upper brakes (anti-runaway-abstraction):**

**Brake 1 — HV floor as criterion, never as gate.** At Spawn, every connection problem pins into its `criteria` (alongside the auto-pinned Popper battery) the commitment schema:

```json
{
  "id": "hv-floor@<params-hash>",
  "eval": "program:hv_estimator",
  "budget": { "k": "HV_K", "per_edit_steps": 100000, "time_ms": 10000 }
}
```

Instantiation freezes `k`, the threshold `HV_MIN`, and the B₀ snapshot into the commitment content — content-addressed, so verdicts are replay-stable. Retuning `HV_MIN` affects future instantiations only.

`hv_estimator(candidate a)`:

1. Sample `k` edits `a' ~ µ(·|a)` via the variator role — `µ_struct` whenever the candidate parses as a skeleton (§6, §10). Prompts and raws logged; replay consumes logged raws, so the verdict is replay-deterministic (§0, P0 replay test).
2. Base battery `B₀(a)` = `I(a).commitments` ∪ instantiated criteria of addressed problems, **minus all HV-type commitments**. Stratification is mandatory: HV over a battery containing itself does not terminate. `B₀ ⊂ B` is a declared surrogate for Def 3.6, asserted in the validity node, hence attackable.
3. `ŝ` = fraction of edits that pass B₀ and are `≉_{B₀} a` (inequivalent survivors only).
4. Verdict: `pass` iff `1 − ŝ ≥ HV_MIN`; else `fail`; `overrun` when the estimate is unobtainable within the declared budget (no variator role configured, or the variator yields no edits — never a wall-clock condition, §1 budget honesty).

**Fail path.** `V = fail` ⇒ the harness registers (Crit) a critic artifact carrying an ordinary demonstrative warrant: `commitment = hv-floor@…`, `verdict = fail`, `trace_ref = {k edits, per-edit verdict vectors, ŝ, logged raws}`, and a `validity_node ν` asserting (i) kernel fairness — µ emitted genuine bounded edits; (ii) `k` sufficiency at the decision margin; (iii) `≈_{B₀}` adequacy as equivalence surrogate — misclassifying rephrasings as inequivalent inflates ŝ; (iv) B₀-for-B adequacy. (Adj) then runs unchanged: a fresh, unattacked critic is in G ⇒ the relation is **refuted** — never `suspended`; suspension would require the critic itself to be under unresolved attack. Reinstatement = attack ν (canonical attack: "the counted survivors are ≈-equivalent under a fairer surrogate; ŝ is inflated"). `overrun` packages no warrant; only `fail` does.

Consequences, all via existing machinery:

- Shallow links ("both involve energy") admit many inequivalent survivors ⇒ `fail` ⇒ **refuted**, with a full trace.
- No bespoke sharpen-or-drop: the failed verdict already Spawns a successor problem (P2) — sharpening is the successor's job.
- Accepted links whose HV later sags (battery growth, marginal pass, (ε,δ) error) trip the **remove-arbitrariness** Spawn via the lazy spot-check (§6).
- Estimator gaming ⇒ critic-gaming signal ⇒ **audit-the-critic** (§3).

Untypedness preserved: the floor is a property of connection **problems**, not of relation artifacts. Anything addressing a connection problem faces it; any other problem MAY pin the same schema.

**Brake 2 — abstraction pays rent on introduction** (unchanged): a super-principle over 2 nodes is spawned only if it addresses an open problem OR immediately covers a 3rd previously-unconnected node. No rent, no tower. Gates Spawn only — scheduler/budget policy under §14; never touches statuses.

D1 preserved: spontaneity in the noticing, discipline in the adjudication — every connection problem runs the normal Conj→Crit→Adj loop, HV entering only as the `hv-floor` criterion inside it.

Emergent: raw uninterpreted data is maximally isolated ⇒ the isolation signal drives interpretation of numeric/opaque content by the same mechanism as unification.

The Goldilocks band is knobs, not a guarantee. Control surface: `FLOOR, K, INTEGRATION_BUDGET_SHARE, HV_MIN, rent-rule`. Settling is empirical (P6).

## 8. Views (not types)

`theory(id)`: walk `refs ∪ dep` closure from `id`; render narrative + postulates + derivation DAG + per-component verdict history + open attack surface + HV/reach profile. Deterministic function of the graph ⇒ cannot drift. Time-travel via event log.

Any artifact can be viewed as a theory by following its refs. **Prose is a view, not the content:** for skeleton-codec artifacts (§10), `prose(id)` renders the readable narrative from the skeleton via the summarizer role, cached and logged; the skeleton is what gets criticized.

## 9. LLM adapter

**Roles** (each = prompt template + JSON schema + temperature + endpoint):

`conjecturer (Verbalized-Sampling contract, §11.6), argumentative_critic, defender, variator(µ, µ_struct), judge(rubric verdicts under trial protocol), summarizer(content→pack, skeleton→prose), synthesizer(propose relation artifacts), embedder(content→vector; non-generator model; outputs logged as raws)`

Config maps role → endpoint (frontier APIs | ollama | llama.cpp | OpenAI-compatible). Mix freely. **Cross-family assignment (normative):** the judge role MUST run on ≥2 endpoints from different model families for ensemble-disagreement detection; argumentative critics for school-k artifacts are drawn preferentially from a *different* school/family — the **foreign-reviewer rule** (deterministic: farthest school by recent embedding centroid, tiebreak by school id). The conjecturer's family is per-school (§11.1).

**Pack contract** (deterministic render, target ≤ 2–3k tokens): problem; compressed criteria; target artifact; top-N attackers/defenders; pinned root criteria (Popper battery); neighbourhood (for born-connected), weighted per school render policy; **precedent slice** — for any rubric call, the top-`PRECEDENT_K` accepted precedent artifacts citing the applied standard, user rulings ranked first; selection is a deterministic query (nearest-K by shared-problem > refs > lexical/embedding), logged. Blobs rendered as shape/stats/head by summarizer. **Anti-self-conditioning rules:** self-generated prose re-enters packs only re-voiced by the summarizer (different template or family); verbatim recent generator output is rationed — lineage and lessons re-enter, voice does not. **Complement and distribution-eliciting directives** are standard render options (§11.4). Negative case law is NEVER rendered into packs (§11.5).

**Safety property:** any substantive claim about a summarized blob is program-checked against the real bytes; a lossy summary cannot corrupt a verdict.

Schema-invalid output ⇒ feed error back, bounded retries, then drop the cycle (logged).

**Noisy-judge mitigation** (structural): every demonstrative warrant carries an attackable `validity_node`; rubric ν nodes cite their standard and fall with it (§1 closure extension); rubric verdicts exist only downstream of the trial guard (§3); judges are audited by program (§10.4); critic-gaming Spawns audit-the-critic. Noisy rubric verdicts become criticizable artifacts, not silent corruption. Prefer `eval:program|predicate` over `eval:rubric` wherever content is formal/numeric/code.

## 10. Informal domains

Design premise: the rubric judge must never be asked the question LLMs (and humans) are worst at — a holistic pass/fail on free prose. Every mechanism below narrows, anchors, compares, or audits; none introduces a type, a status, or an acceptance rule. The institutional analogues (courts, peer review, case law, editorial calibration) are the design source; each move compiles to existing machinery.

**10.1 Skeleton + forbidden cases (make conjectures pay in checkable coin).**

Problems in informal domains pin (in `criteria`) a `skeleton-wf` commitment (`eval:program`): the candidate's content is `codec:json` conforming to:

```json
{
  "claim": "string",
  "mechanism": "string",
  "scope": { "covers": ["..."], "excludes": ["..."] },
  "forbidden": [ { "case": "string", "eval": "rubric:<spec-id> | program:<ref>", "observation_valued": false }, "..." ],
  "prose_notes": "string (optional; rendered, never adjudicated)"
}
```

`skeleton-wf` passes iff the skeleton parses AND `forbidden ≠ ∅`. At registration (before id computation — deterministic), the harness **compiles each forbidden case into a commitment in `I(a)`**: "if this case obtains, I fail." Observation-valued forbidden cases plug into research/holdout machinery. Consequences: demarcation is real (§6) — forbid nothing, fail `skeleton-wf`, get refuted by a program; and the judge's question shrinks from "is this good?" to "does case X violate clause Y?" — narrow, where rubric judges are serviceable. Prose is a §8 view. D2 intact: this constrains what survives, not what γ may emit.

**10.2 Comparative adjudication (compare, don't score).**

Judges of every substrate are more reliable at "is A better than B for π" than at absolute verdicts. Two mechanisms:

- **Anchored rubric mode.** A standard artifact (10.3) may declare `mode: anchored` with anchor exemplar refs. The judge's question per commitment: "does the candidate beat the known-bad anchor on criterion c?" — pass iff yes. Absolute scoring is thereby eliminated from the hot path; the anchors come from the precedent pack.
- **Pairwise discrimination rulings.** The existing discrimination Spawn (≥2 surviving rivals for π) resolves, in informal domains, by a pairwise judge call: (A, B, π, criteria) → winner + `decisive_point`. The ruling registers as an **argumentative warrant against the loser, indexed to π** (D10: A-beats-B-for-π, never a global ranking). Full rubric-verdict guard applies (§3), including mandatory order-swap. A judge that cannot discriminate registers nothing — the rivalry stands, correctly unresolved.

**10.3 Standards as case law.**

Every `rubric:<spec-id>` resolves to a registered **standard artifact**: the rubric text, its evaluation mode (`absolute|anchored|pairwise`), and refs (`mention`) to exemplar artifacts — known-good and known-bad, with one-line holdings. Standards are ordinary artifacts: attackable, reinstateable, succeedable (a revised standard is a successor artifact addressing the standard's own open problems). Precedents accrete by reference (10.6): no mutation, no successor churn for routine growth. The closure extension (§1) is the enforcement teeth: **the productive attack in informal domains usually lands on the standard, not the work** — and when it lands, every verdict issued under that standard falls with it, and every target reinstates, computed in pass 1. Parallel fifths, as a theorem of the graph.

**10.4 Judge audits (program-checked attacks on rubric infrastructure).**

Informal *truth* cannot be program-checked; judge *behavior* can. Periodic audit programs (every `AUDIT_PERIOD` cycles, budgeted):

- **Paraphrase invariance:** re-run logged rulings on variator paraphrases; flips are hits.
- **Premise-deletion sensitivity:** delete the cited `decisive_point` from the transcript; the verdict SHOULD flip; a verdict that survives the removal of its own stated grounds is easy to vary.
- **Planted-flaw calibration:** maintain a constructed calibration set — artifacts with flaws known by construction (circularity, equivocation, Persephone-style vacuity) and clean controls; run the judge; log the error rate. Ground truth by construction is what makes this a *program* check on an informal judge.
- **Bias probes (new):** planted **self-preference** pairs (judge's own family's output vs. a matched foreign-family output, authorship masked) and **verbosity** pairs (same content, padded vs. terse). Systematic preference for own-family or padded variants is a measured bias, logged against the judge's reliability record.
- **Ensemble disagreement:** cross-family judge endpoints (§9) disagreeing on a ruling is a critic-gaming signal (§3), never averaged away.

Audit outputs enter as ordinary **demonstrative warrants** (`eval:program` — reliable) against the relevant ν nodes or standards: "this judge flips under paraphrase" is a direct, warranted attack on the judge-reliability assertion those ν carry. Calibration error > `JUDGE_ERR_MAX` ⇒ audit-the-critic Spawn. The inversion to preserve: formal machinery criticizing informal machinery, with the full force of the graph.

**10.5 Holdout + novel-case commitments (weight reach; demand novel facts).**

A `HOLDOUT_SHARE` of the evidence corpus is registered **sealed**: content-addressed (hash visible; bytes excluded from all packs by the deterministic renderer), with scheduled `Reveal` events. Informal problems SHOULD pin `novel-case` criteria: the candidate commits, via its skeleton, to expectations over unseen cases. Sealed evidence does not count as covering (§1) — no premature research Spawn; the commitment is scheduled-pending. At `Reveal`: instantiate, evaluate (program where possible, anchored-rubric otherwise). Pass on held-out material = a reach hit with the strongest provenance the informal side can produce (timestamps in the log prove the artifact predates the evidence — Lakatos's novel-fact criterion, mechanized); fail = ordinary failed verdict ⇒ successor Spawn.

**10.6 User as appellate court.**

The `ask-user` backend (§12) is repurposed: a **disagreement-ranked queue** (ensemble splits, guard-block streaks, audit hits, maximum-entropy rivalries), never round-robin, capped at `USER_RULINGS_BUDGET` per session — the user is the scarce calibration resource and MUST be spent where the machine is most confused. Each ruling registers as a **precedent artifact** (`provenance.role: user`): the case, the holding, a `mention` ref to the standard it calibrates. Effects: (a) enters the precedent slice of subsequent judge packs, ranked first; (b) is an ordinary artifact — attackable, reinstateable (N1; authority is pack ordering, never status privilege). Appellate, not oracle.

**10.7 Structural HV for informal content.**

Covered normatively at §6/§7: skeleton-codec candidates get `µ_struct` — role-level substitution over `{mechanism, motive/causal-link, scope}` — in both the lazy spot-check and `hv-floor`. The Persephone configuration (any substitution passes) yields low HV ⇒ `hv-floor` fail on connection problems, remove-arbitrariness Spawn on accepted artifacts. Rewording-only variation is banned as the sole kernel for skeleton content.

**Dispatch note (untypedness audit):** nothing above is a type. 10.1 is problem criteria + a content convention; 10.2/10.3 are standard-artifact content; 10.4 is programs over the log; 10.5 is storage + scheduler policy + criteria; 10.6 is a backend + provenance role; 10.7 is a kernel selection rule keyed on whether content parses. An artifact is "informal" only in the sense that the problems it addresses pin these criteria.

## 11. Capture control (two surfaces)

Design premise. Theorem 4.1 guarantees γ-with-feedback is open *in principle*; a conditioned generator's **effective** reachable set can still collapse into a basin, and a criticism process can ossify into ritual while every status stays formally correct. These are distinct failure surfaces requiring distinct instruments:

- **Generator capture** (variation collapse): the conjecture stream contracts to near-duplicates of one idea. Population structure *prevents* this; embedding diagnostics *detect* residual cases.
- **Adjudicator capture** (selection collapse): criticism ritualizes — the court re-litigates the same nodes, leaves commitments unevaluated, never reinstates, never attacks a test. Grounded semantics is exactly as skeptical as its attack supply (unattacked ⇒ accepted), so population structure cannot fix this: every school shares the same corruptible court. Only graph-native detection catches it.

Everything in this section steers **attention** — pack rendering, scheduling, budgets, registration gates — never status (§0). School membership lives in provenance, and provenance is never a warrant (D2), so schools cannot leak into adjudication by construction.

**11.1 Schools — islands in conjecture, panmixia in criticism.**

A **school** is a persistent conditioning regime for γ-calls: `(endpoint/family, stance_seed, lineage exemplar slice, render weights)`, registered as a school-policy artifact (Refl — attackable like any rule). `N_SCHOOLS` schools; one global graph; one global court.

- **Constitution = lineage inheritance.** School k's packs draw exemplars preferentially from accepted artifacts with `provenance.school == k`. This — not designed differences — is what makes islands diverge: each school conditions on its own descendants. Curation-free by construction.
- **Cold start.** Schools are seeded from the shipped **stance library** (one-time global curation; ~8 generic conditioning priors: mechanist — demand a causal mechanism; skeptic — counterexample first; unifier — seek the covering principle; empiric — anchor in cases; formalist — derivation first; historicist — precedent and succession; adversary — strongest attack on the incumbent; minimalist — parsimony pressure) and endpoint families round-robin over configured providers. **Stance weight decays** on a fixed schedule (`STANCE_DECAY`) as the school's lineage corpus grows: identity migrates from seed to lineage.
- **What schools never touch:** `att`/`dep` construction, adjudication, statuses.
- **Criticism is panmictic.** Attacks cross school lines freely — that is D3 working, not leakage. The foreign-reviewer rule (§9) actively routes criticism *across* schools and families. What must not migrate is voice (anti-self-conditioning, §9).
- **Migration = machinery you already have.** Integration problems + the synthesizer are the crossover operator: controlled reading across schools, adjudicated globally. No new mechanism.

**11.2 Allocation policy (no per-problem curation).**

Deterministic function of (event log, config):

1. **Ownership by provenance.** `successor` and `remove-arbitrariness` problems are worked, by default, by the school of the artifact that spawned them — lineages follow through on their own problem-shifts (research programmes, not hats).
2. **Fan-out classes.** `seed`, `discrimination`, and `integration` problems fan out to **all** schools: these are exactly where rival programmes should compete (discrimination literally adjudicates rivals; integration is migration).
3. **Cross-examination slice.** `XEXAM_SHARE` of cycles per lineage is allocated to the **most foreign** school (farthest recent embedding centroid; tiebreak by school id) — scheduled migration hygiene.
4. **Recruitment on stagnation.** A lineage-stagnation flag (11.3) escalates the lineage to full fan-out (11.4).
5. **User pinning** optional via config/CLI; never required.

Rejected alternatives, for the record: clustering as constitution (clusters follow diversity — clustering a captured graph yields k copies of one school, and there are no clusters at cycle 0; retained diagnostically as inter-school distance); round-robin as default (homogenizes exemplar exposure and multiplies budget; survives as the cross-examination slice); problem *types* (forbidden — but provenance triggers, already in the ontology, legitimately drive the fan-out classes).

**11.3 Detection — Measure-rule replay programs over the event log.**

All metrics are deterministic functions of the log (embedder raws logged, §1). Windows of `CAPTURE_W` cycles; flags are **conjunctions** with hysteresis — similarity alone is ambiguous (healthy convergence looks identical); progress alone is ambiguous (healthy exploration looks flat).

*Generator surface:* mean pairwise embedding distance of the recent conjecture stream + its slope (contraction); near-miss rate at the anti-relapse gate (§3); min pairwise **inter-school centroid distance** (school convergence); optional effective rank of window embedding covariance.

*Adjudicator surface (graph-native — the set no reference system has, because no reference system has the graph):* **attack-target entropy** (are criticisms probing new commitments or re-litigating the same nodes?); **criticism debt** (fraction of accepted artifacts carrying never-evaluated commitments); **G-churn** (status changes per window); **reinstatement rate** (a Popperian system where nothing is ever reinstated is suspicious — band, not floor); **validity-node attack rate** (if no test is ever attacked, D3 has died in practice while remaining true on paper).

*Grounding ratio λ:* windowed fraction of verdicts from `program`/`observation` evals vs. `rubric`; evidence-artifact entry rate; fraction of accepted artifacts whose support chains bottom out in an exogenous anchor (evidence, program check, user ruling) rather than pure conjecture. `LAMBDA_FLOOR` is the closed-loop alarm line.

*Flags:* **lineage stagnation** = conjecture-stream contraction ∧ flat progress (no status changes, no problems retired, no oracle delta where present) sustained `CAPTURE_W`. **School convergence** = min inter-school distance < `RESEED_DIST_MIN` sustained. **Adjudication ritual** = any two of {attack-entropy < floor, criticism debt > ceiling, reinstatement outside band, validity-attack rate ≈ 0} sustained. **Grounding decay** = λ below `LAMBDA_FLOOR` despite the standing exogenous schedule.

Honest limit, stated: these detect **stalled** dynamics, not **wrong-but-stable** ones. A consensus ossified around a shared blind spot is invisible from inside; the exogenous anchors (§10.5, §12, appellate) are the only lever against it, which is why λ has a floor.

**11.4 Response ladder — logged scheduler rules with hysteresis (attention only).**

- **Lineage stagnation** ⇒ recruit fan-out (11.2.4); switch the lineage's γ-calls to VS tail-weighted selection (11.6); add complement directives to the pack ("produce the attempt these summaries make least likely").
- **School convergence** ⇒ `Reseed` the laggard (lowest recent novelty contribution; deterministic tiebreak): rotate stance seed, rotate the lineage exemplar slice toward imports/evidence, optionally rotate endpoint family. Logged as a `Reseed` event; the prior school-policy artifact persists (D8) — reseed is succession, not deletion.
- **Adjudication ritual** ⇒ criticism-debt sweep (schedule evaluation of never-evaluated commitments on accepted artifacts); audit-the-critic Spawn (§3); appellate docket priority raised (§10.6).
- **Grounding decay** ⇒ exogenous brake: research problems to maximum priority, retrieval forced, appellate docket surfaced, cross-family critic quota raised.

Every intervention is logged with before/after diagnostics — escape efficacy is measured, not vibes. Policy is **fixed** in v1 (escalation + hysteresis); a learned controller is out of scope (meta-attractor risk: a controller that always reaches for its favorite move has itself been captured).

**11.5 Negative case law lives at the gate; positive case law lives in packs.**

The refuted-artifact embedding index that powers anti-relapse stage 2 (§3) **is** the negative atlas. Refuted-region records (cluster centroid, exemplar ids, model-version tag, which response worked) are ordinary artifacts feeding the gate and the scheduler — and are **never rendered into packs**: negative conditioning primes the very content it bans, and banned lists grow without bound. Enforce tabu at the door, not in the prompt. Positive case law — precedent slices, user rulings, standards exemplars (§10.3, §10.6) — remains pack-side and retrieval-driven. Negative-atlas entries are model-version-specific: revalidate on endpoint upgrade rather than trust.

**11.6 Conjecturer contract: Verbalized Sampling by default.**

Each γ-call returns `VS_K` candidates, each with a stated probability/typicality estimate (schema-enforced), rather than a single point — distribution elicitation recovers diversity that mode-seeking post-training suppresses. The harness registers candidates per deterministic policy (default: all candidates through the anti-relapse gate; under a stagnation flag, tail-weighted selection — spend budget on the candidates the model itself marks atypical). Registration cost scales with `VS_K`; criticism budget does not have to (scheduler may triage).

**11.7 Pareto retention (attention and reporting only).**

Scheduler focus (which survivors receive successor/variation budget) and run reports keep the **Pareto frontier** over `PARETO_AXES` (default: `HV_B`, reach `R_t`, criteria-coverage) rather than argmax-HV. Greedy single-metric selection collapses the population onto one basin of the measure itself; frontier retention preserves live alternatives without a full QD/MAP-Elites build. Never a status; an artifact off the frontier is merely unfunded, not demoted.

**11.8 The λ dose-response experiment (P2 acceptance; pre-registered).**

Question: does the harness's exogenous anchoring earn exemption from closed-loop semantic collapse, or is the exemption an architecture-diagram fiction?

- **Arms:** λ=0 (rubric-only judging, retrieval off, appellate off — the closed loop), λ=low, λ=full. Fixed seeds, problem set, budget, endpoints; ≥N replicates per arm; report distributions, not means.
- **Oracle-blind, oracle-scored.** Problems where an external verifier *exists but is withheld* from the loop (program-checkable synthesis; prover-checkable claims); the oracle scores outcomes post-hoc only. Even the closed arm gets objective measurement without contamination.
- **Dependent variables, both surfaces:** literature-comparable stream metrics (effective rank, mean pairwise distance); the graph-native ritual metrics (11.3); and the **HV-Goodhart signature** — HV of accepted artifacts rising while oracle-scored quality flatlines, the empirical fingerprint of ritual.
- **Predictions:** λ=0 contracts on both surfaces and plateaus below λ>0 arms; dose-response monotone in λ; some runs dissociate the surfaces (generator diversity holds while attack entropy collapses) — which would empirically vindicate the two-surface framing.
- **Falsifier, stated in advance:** if λ=full tracks λ=0, the anchoring as built does not earn the theorem's exemption. Thresholds pre-registered in config and committed **before** first look.
- **Cost:** ~zero marginal build. The experiment requires long-horizon runs, so it *is* P2; the metrics, built once as replay programs, are simultaneously the experiment instruments and the permanent detection layer.

**Dispatch note (untypedness audit):** a school is provenance metadata + a render policy artifact; the gate blocks only refuted-equivalents; detection is programs over the log; responses are scheduler rules; Pareto rank and VS selection are attention. Nothing here is a type, a status, or an acceptance condition.

## 12. Research

`observation_valued` commitment with no covering evidence artifact ⇒ Spawn research problem. Sealed holdout evidence does not count as covering pre-reveal (§10.5).

Backend pluggable: web-search | local-RAG | ask-user (doubles as the appellate channel, §10.6). Research cadence is part of the standing exogenous schedule that keeps λ above floor (§11.3).

Evidence enters as an artifact depending on a source-reliability assertion;
any warrant grounded in it declares an `evidence` ref from its validity node.
Attacking the evidence or its source therefore propagates through the explicit
evidence closure and can reinstate the warrant's target.

## 13. Interface (CLI first)

`frontier` · `focus <id>` · `expand` · `attack <id>` · `step` · `run --budget <spec>` · `why <id>` (print attack/defence chain justifying status — computable from grounded semantics) · `theory <id>` (render §8 view) · `prose <id>` (skeleton → narrative view) · `docket` (disagreement-ranked user queue, §10.6) · `rule <case-id>` (enter an appellate ruling) · `schools` (rosters, centroid distances, stance weights) · `capture` (both-surface dashboard: contraction, ritual metrics, λ) · `reseed <school-id>` (manual override; logged) · `merge <path>` · `trace <id>` (replay). TUI later.

## 14. Scheduler & stack

Thin custom scheduler over a rule registry — control flow is "apply enabled rules under budget," NOT a fixed node graph. Do not use LangGraph as the spine (may wrap later for tooling).

Frontier of problems + global budgets (κ budgets generalized). School allocation per §11.2; focus selection per Pareto retention (§11.7). Short horizon: one problem, N cycles, return the Pareto frontier of G-members. Long horizon: persistent frontier across sessions. Integration work capped by `INTEGRATION_BUDGET_SHARE`; audits by `AUDIT_PERIOD`; user queue by `USER_RULINGS_BUDGET`; `Reveal` events per holdout policy; capture-response rules per §11.4 with hysteresis.

**Storage:** schema-namespaced content-addressed JSON files
(`objects/<schema>/<sha256(id)>.json`) + an append-only JSONL log, git-native.
Legacy flat object records remain readable. Validated ontology records and
their nested collections are immutable. Because event references contain an
untyped object id, an id is globally unambiguous within a root: every stored
copy of an id MUST have the same schema and canonical bytes. A conflicting
registration or merge is rejected rather than silently choosing a record.
Event sequence numbers MUST be exactly `0..N-1`; duplicates, gaps, and
out-of-order appends are corruption. Sealed holdout blobs live in a `holdout/`
namespace excluded from pack rendering until their `Reveal` event;
refuted-index (embedding NN over refuted artifacts) is rebuilt
deterministically from the log. Save = git commit. Merge = componentwise
set-union + re-adjudicate when common ids are identical; school-policy
artifacts union like any artifact, and the scheduler reconciles active rosters
from config. SQLite/FAISS-style index only if scale demands.

Pydantic models throughout.

## 15. Config knobs (single typed schema, optional profile)

`deepreason.config.Config` is the sole source of defaults and accepted field
names. A YAML config is a partial profile containing only intentional
overrides; omitted values inherit the typed defaults, while unknown top-level
knobs or role-seat fields are errors. Profile-driven CLI, MCP,
setup-generated configs, and general-purpose live scripts MUST load through
`deepreason.config.load` and construct endpoints through
`deepreason.llm.adapter.build_adapter`. Pre-registered experiment arms MAY
instantiate the same schema directly to keep their manipulations explicit.
`deepreason config` renders the complete effective configuration for
inspection.

| Knob | Meaning | Start |
|------|---------|-------|
| `FLOOR` | min accepted dependence edges before isolation fires | 1 |
| `K` | neighbours considered per connection problem | 3–5 |
| `INTEGRATION_BUDGET_SHARE` | cap on cycles spent on connection/integration | ≤0.30 |
| `HV_MIN` | pass threshold of the `hv-floor` criterion (`1 − ŝ ≥ HV_MIN`) | tune |
| `HV_K` | edits sampled per HV estimate (lazy §6 and `hv-floor` §7) | 5–10 |
| `PRECEDENT_K` | precedents in a judge pack's precedent slice | 3–5 |
| `TRIAL_PARAPHRASE_N` | paraphrase spot-checks per rubric ruling | 2–3 |
| `JUDGE_ERR_MAX` | tolerated planted-flaw error rate before audit Spawn | tune |
| `AUDIT_PERIOD` | cycles between judge-audit sweeps | 20–50 |
| `USER_RULINGS_BUDGET` | appellate rulings requested per session | 1–3 |
| `HOLDOUT_SHARE` | fraction of evidence corpus sealed | 0.1–0.3 |
| `N_SCHOOLS` | conjecture schools | 3–5 |
| `STANCE_DECAY` | stance-weight decay vs. lineage-corpus size | schedule; tune |
| `XEXAM_SHARE` | cross-examination slice per lineage | 0.1–0.2 |
| `RESEED_DIST_MIN` | min inter-school centroid distance before reseed | tune |
| `NEAR_DUP_EPS` | embedding radius triggering anti-relapse stage 3 | tune |
| `VS_K` | candidates per γ-call (Verbalized Sampling) | 4–8 |
| `PARETO_AXES` | frontier axes for focus/reporting | HV, reach, coverage |
| `LAMBDA_FLOOR` | min exogenous grounding ratio before brake | tune |
| `CAPTURE_W` | detection window / hysteresis width (cycles) | 10–30 |
| `PACK_TOKEN_BUDGET` | max pack size | 2000–3000 |
| `RETRY_MAX` | schema-repair retries | 2 |
| role→endpoint/model/temp | per-role model routing (cross-family rules, §9) | — |

## 16. Phases & acceptance tests

| Phase | Scope | Acceptance test |
|-------|-------|-----------------|
| **P0** (~1 day) | untyped schema; content=bytes+codec; event log; two-pass adjudicator; `dep`/`att` from interfaces (incl. case-law closure extension); Popper battery; isolation/integration driver stubbed w/ knobs; `why`/inspect CLI. No LLM. | Deterministic core passes unit tests: grounded extension correctness, reinstatement (Lemma 3.1), two-pass support cascade, cycle rejection in `dep`, standard-refutation ⇒ dependent-verdict collapse ⇒ target reinstatement via closure, replay-from-log reproduces state byte-for-byte. |
| **P1** (usable now) | single-problem loop: Conj → Crit(program + argumentative) → Adj; Popper battery; anti-relapse (hash + battery stages); born-connected conjecture; VS conjecturer contract; theory render. | Point at a problem file → returns the Pareto frontier of survivors, a rendered theory document, and a complete trace. Anti-relapse blocks a re-submitted refuted idea. A γ-call yields `VS_K` schema-valid candidates. |
| **P2** | all Spawn triggers; scheduler; budgets → long horizon; lazy HV; reach checks; synthesizer; isolation floor + integration trigger; `hv-floor` on connection problems; **capture control (§11): schools + allocation, semantic gate stage, both detection surfaces, λ, response ladder, Pareto focus**. | Multi-cycle run spawns successor/discrimination/connection problems; HV and reach logged; frontier persists across save/reload. An easy-to-vary relation draws an `hv-floor` warrant, lands `refuted`, reinstates via ν-attack, replays byte-for-byte. **Schools:** two schools measurably diverge (inter-school distance grows from seed); a forced convergence triggers `Reseed`, replayed byte-for-byte; the semantic gate blocks a paraphrase of a refuted artifact and admits a near-neighbor with a differing verdict-vector. **λ experiment (§11.8):** pre-registered thresholds committed; λ=0 vs λ=full arms run oracle-blind on withheld-verifier problems; both-surface metrics reported as distributions; verdict against the falsifier recorded either way. |
| **P3** | merge command; session namespaces. | Two divergent saved graphs merge and re-adjudicate with no manual conflict resolution; identical artifacts dedupe by id; school registries union cleanly. |
| **P4** | research commitments + backends; standing exogenous schedule. | An observation-valued commitment with no evidence spawns a research task; fetched evidence enters as an attackable artifact; λ is computed live and the grounding brake fires on a staged decay. |
| **P5** | informal-domain protocol (§10): skeleton criteria + forbidden-case compilation; trial guard; standard artifacts + precedent packs; anchored + pairwise modes; judge audits incl. bias probes; holdout/`Reveal`; appellate queue; `µ_struct`. | (a) A forbid-nothing conjecture fails `skeleton-wf` ⇒ refuted by program. (b) A Persephone-style skeleton fails `hv-floor` under `µ_struct` with the substitution trace logged. (c) A rubric warrant registers only with a conforming trial transcript; an order-swap inconsistency blocks a pairwise warrant. (d) Planted-flaw battery yields a measured judge error rate; a paraphrase-flip audit registers a program warrant against a ν; a self-preference probe logs a measured bias. (e) Refuting a standard collapses its verdicts and reinstates targets (closure, replayed). (f) A user ruling enters the next judge pack's precedent slice and is itself attacked and reinstated. |
| **P6** | frontier-model hardening: per-role few-shots, pack compression; cross-family eval; knob tuning from P2 experiment data. | Eval reports valid-JSON rate, attack-validity rate, survivor-HV/reach, trial-guard survival, paraphrase-flip, planted-flaw error, per-school novelty contribution, escape efficacy per response rule; Goldilocks + capture knobs tuned from data. |

**MVP slice within P2** (buildable first): lineage-stagnation flag (contraction ∧ flat progress) + semantic gate stage + fan-out recruitment, on one long-horizon problem. This alone converts silent circling into a visible, logged, managed event.

## 17. Non-goals & residue (state honestly; do not paper over)

Guarantees faithful bookkeeping (statuses, reinstatement, no relapse, replayable trace). Does not manufacture good conjectures. Theorem 4.1 openness is in-principle reach; §11 manages the gap between in-principle and effective reach — it forces variation, which is not the same as producing a creative conjecture, and must never be advertised as such.

HV at k≈8 is a spot-check, not a measurement. The `hv-floor` verdict is program-computed but stands on LLM-dependent assumptions (kernel quality of µ/µ_struct, `≈_{B₀}` adequacy) parked in its validity node: visible and attackable, not eliminated.

§10 does not make informal verdicts reliable — it makes them narrow, comparative, precedent-anchored, procedurally screened, and audited. `≈_B` in informal domains is irreducibly judgment-laden; paraphrase-invariance audits bound the damage. Skeletons can be gamed by toothless forbidden cases. Comparative rulings are problem-indexed only. User rulings are the scarce calibration resource; a starved docket degrades calibration silently — the docket makes starvation visible, which is the most the design can do. The planted-flaw battery measures the judge on flaws we know how to construct; unknown flaw classes are unmeasured by construction.

§11 detects **stalled** dynamics, not **wrong-but-stable** ones: a consensus ossified around a shared blind spot is invisible from inside, and only the exogenous anchors bear on it — hence `LAMBDA_FLOOR` is load-bearing, not decorative. The stance library is one act of global curation, declared. School count, all thresholds, windows, and hysteresis widths are empirical per model family and domain; transfer is not assumed. Embedding-space metrics inherit the embedder's biases; the embedder is a configured role, swappable and logged, but not itself adjudicated. Negative-atlas entries and school geometry are model-version-specific: revalidate on upgrade. The fixed response policy caps but does not solve the meta-attractor regress (a learned controller is deferred for exactly this reason). Schools mitigate shared-model gravity best when families genuinely differ; if all configured endpoints converge on the same modal answer, inter-school distance collapses honestly and the reseed rule can only rotate among the same basins — exogenous entropy (§12, appellate) is the remaining lever.

Text-only model + raw perceptual bytes (image/audio/embeddings) is inert without a multimodal interpreter or a program that computes a verdict. Leave a clean interpreter seam; assume text+numeric+code as target.

The unification band is empirically tuned, not analytically guaranteed.
