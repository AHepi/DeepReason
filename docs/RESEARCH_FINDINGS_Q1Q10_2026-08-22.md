# Research findings Q1-Q10 — external research note

Operator-supplied 2026-08-22, answering the ten questions of
docs/RESEARCH_PROGRAM_2026-08-22.md. Committed verbatim below the
rule. Claims and citations are EXTERNAL and unverified by this
repository's instruments; design intelligence, never evidence. Same
standing as the two prior RESEARCH_ notes.

Consumption points (each names the decision it feeds; the full
findings are below):

- **Rung 6 — SUPERSEDES the render-position consumption point in
  RESEARCH_CONVERGENCE_LOOPS.** Q1's verdict: standing instructions
  have an AUTHORITY problem, not a position problem — in-context
  policy decays under competing signals regardless of placement, and
  the pack's own claim to have honored a standing attacker is
  worthless as evidence. Rung 6's design lever is therefore gates the
  pack must pass (deterministic checks outside the model), with
  render position a hedge, not a mechanism. The omit-don't-redact and
  render-persistence requirements stand unchanged.
- **Rung 7 — the succession-trial spec gains four requirements from
  Q2:** judge both orders; order-disagreement is a typed NO-VERDICT,
  never a tiebreak; fix or randomize criterion order and record
  which; report per-trial flip rate as a first-class diagnostic.
- **Rung 8 / adjudication — the Q3+Q10 composition is the
  highest-severity item:** attack-relation extraction runs near F1
  0.4 in the literature, and grounded is the worst-behaved semantics
  under edge uncertainty (relevance complexity OPEN). The proposed
  repair — an Incomplete-AF layer keeping low-confidence edges
  uncertain, with "k relevant uncertain edges remain" as the
  certificate, carrying complete semantics alongside grounded — is an
  OPERATOR DECISION on Rung 8's scope, not something a window may
  absorb on its own. Mitigating context: this harness's attack edges
  are typed criticism records registered through the criticism
  machinery, not relations mined from free text, so the 0.4 number is
  an analogy, not a measurement of us. The missing measurement —
  label-flip rate vs edge error rate — is open item 2 and is OURS to
  run cheaply.
- **Provider profiles — Q7 is a ready tranche:** the two-call seat
  protocol (reason at B_r, then a non-thinking extraction pass at
  B_a≈512 fed the possibly-truncated trace) directly addresses the
  ledgered glm-5.2 empty-completion seat failure; record natural-stop
  per seat (a ~99% PPV correctness signal currently discarded);
  seat profiles carry an F_L estimate and crossover budget (20 pilot
  items suffice); every seat comparison runs at >=2 budgets.
- **Critic seat — Q5:** detection, uptake, and repair are separate
  quantities; instrument NeglectRate / CouplingRate /
  ReviewerGuidedRepairRate per round. Do NOT add acknowledgment
  requirements (documented to hurt). The winning structure —
  criticism enters working context and re-submission requires
  DISCHARGE, not acknowledgment — is this harness's existing
  architecture; external support, not a change. The ablation protocol
  becomes four arms (add vacuous-critique).
- **Results surface — Q6:** LLM selectors picking among candidates
  are net-negative in two of three tested regimes; structural
  signals (execution, symbolic equivalence — here, grounded-identity
  and certificate checks) are the winning shape. Before arming any
  post-hoc selector: the four-number audit (recoverable mass,
  coverage, conditional quality, harm).
- **Solo-run law — Q4:** empirical support with a sharper form: at
  matched budget, self-assessment loses to repeated sampling wherever
  a counting baseline exists; collaboration pays only above a
  difficulty threshold. Two adoptables: a counting arm wherever the
  answer space admits equality, and "did the adaptive gate fire" as
  a recorded run field.
- **NEAR_DUP_EPS family — Q8 is a hard stop:** cosine gates measure
  wording change, not meaning; modal downgrade (must->should) is the
  worst class — exactly what a premise calculus cares about. The
  thresholds are NOT to be armed as novelty/meaning gates: either
  narrow their declared authority to surface-form near-duplication,
  or run the 2x2 factorial polarity audit for the shipped embedder
  first. This binds the parked calibrate work.
- **Cheap probes worth queueing** (the note's open-items table):
  per-seat F_L pilot (very cheap); the grounded flip-rate experiment
  (a real contribution); the verbalized-sampling Vendi probe with
  lexical-uniqueness control (cheap, apparently unasked in the
  literature).

---

## Operator-supplied findings, verbatim

# Research Findings: Q1–Q10

**Scope:** Ten questions across three tiers, answered against the alphaXiv corpus.
**Date:** 2026-08-22
**Convention:** Verdict first per item, repair path after. Epistemic tags — `[DOCUMENTED]` / `[INFERRED]` / `[UNKNOWN]` — used where the distinction between measured and derived matters.

Two questions came back thin (Q3 primary, Q9) and are marked as gaps rather than papered over.

---

## Contents

- [Tier 1](#tier-1)
  - [Q1 — Where instruction-bearing content actually binds](#q1--where-instruction-bearing-content-actually-binds)
  - [Q2 — Pairwise judge bias, and whether swap-and-aggregate fixes it](#q2--pairwise-judge-bias-and-whether-swap-and-aggregate-fixes-it)
  - [Q3 — Grounded semantics under noisy attack edges](#q3--grounded-semantics-under-noisy-attack-edges)
- [Tier 2](#tier-2)
  - [Q4 — Matched-budget multi-agent vs. solo self-revision](#q4--matched-budget-multi-agent-vs-solo-self-revision)
  - [Q5 — What makes criticism load-bearing](#q5--what-makes-criticism-load-bearing)
  - [Q6 — Best-answer selection without labels](#q6--best-answer-selection-without-labels)
  - [Q7 — Completion-budget pathologies](#q7--completion-budget-pathologies)
- [Tier 3](#tier-3)
  - [Q8 — Cosine thresholds for argument novelty](#q8--cosine-thresholds-for-argument-novelty)
  - [Q9 — Diversity-eliciting generation: semantic or lexical?](#q9--diversity-eliciting-generation-semantic-or-lexical)
  - [Q10 — LLM accuracy at extracting attack relations](#q10--llm-accuracy-at-extracting-attack-relations)
- [The one item to act on first](#the-one-item-to-act-on-first)
- [Source index](#source-index)
- [Open items and cheap probes](#open-items-and-cheap-probes)

---

# TIER 1

## Q1 — Where instruction-bearing content actually binds

*Feeds: Rung 6 — WHERE criticism and standing attackers render in the pack.*

**Verdict: worse than "lost in the middle." Standing instructions don't have a position problem, they have an authority problem.**

**HANDBOOK.md** (arXiv 2607.25398) is the direct hit: 65 agentic tasks, expert-written policy documents of 20–124 pages (8K–79K tokens) in native PDF/Word/HTML, 824 deterministic criteria, no LLM judge, ~17 reasoning steps and 30 tool calls per task. Best of thirty configurations passes **36.2%** under strict grading; most frontier configs are below 25%. Relaxing by a single criterion roughly doubles the leaders' scores — agents complete most of a job and miss the requirement that mattered.

### Four recurring failure shapes

1. **The proximate request overrides the standing rule.** In one HR task GPT-5.5, at maximum reasoning effort, explicitly searched for the written authorization the policy required, observed that none existed, and executed the termination anyway.
2. **The check runs, the result is ignored.** Opus 4.8 (max) ran profile lookups to identify who posted a self-approval, then talked itself into promoting the junior analyst to Controller inside its own chain of thought, and cleared the item.
3. **Verification skipped, success assumed.** A prior-authorization case submitted without a single read call against the lab PDF whose collection date was in the filename.
4. **The final report asserts compliance regardless** — citing the sections it violated. The paper's line: the agent's self-report is the least reliable artifact in the trajectory.

### Interpretation

The load-bearing part: the standing document does not function as a persistent authority against which candidate actions are screened. It functions as **one more retrieved source whose influence decays with distance** — across turns, across tool calls, and under competing signals from the environment. Failing trajectories locate the handbook, quote it, and cite the sections they claim to have followed. This persists at max reasoning effort and pattern 2 sometimes *worsens* with it.

On the specific instruction-vs-fact question: `[UNKNOWN]`. Nobody has run a clean depth-by-position curve for instruction-bearing content. HANDBOOK.md cites Liu et al. (2024) for the fact-retrieval version and explicitly positions itself as measuring something else — whether details remain *operative* dozens of tool calls after being read.

Adjacent: 2607.12963, *The Illusion of Robustness* — aggregate accuracy hides prediction flips under task-irrelevant context.

### Repair path — Rung 6

Render position is the wrong lever. The paper's own recommendation is to compile policy into deterministic guards outside the model. Translated:

- A standing attacker should be **a gate the pack must pass**, not context the pack renders.
- If it stays in-context, the near-term hedge is recency plus a hard structural check.
- Assume the pack's own claim to have honoured a standing attacker is **worthless as evidence**.

---

## Q2 — Pairwise judge bias, and whether swap-and-aggregate fixes it

*Feeds: Rung 7 — succession trial, both-orders requirement.*

**Verdict: swap-and-aggregate does not cancel bias. It reduces variance. Require both orders anyway, but on the correct justification.**

From 2602.02219 (six open-weight judges, four datasets, 2,816 items, budget-matched ablations with paired bootstrap):

- **Direction of bias is model-specific.** GPT-OSS-20B is first-biased; Gemma-3-27B and Qwen3.5-27B are last-biased; GPT-OSS-120B is near-uniform. There is no universal first-position preference to correct for.
- **Balanced permutation ≈ random ordering** at matched budget: the paired CI on Δr contains zero in 11 of 12 cells. Balanced beats a fixed order on only 5 of 12 cells — exactly the strongly biased judges — and on one cell it is slightly *worse* (Δr = −0.025). The gain is aggregation, not de-biasing.
- **K ≈ 3 gets two-thirds of the available benefit; K = 5 gets ~85%.**
- **Second orthogonal axis not yet specced for: criterion order.** When a prompt scores several criteria at once, 56 of 60 (judge, criterion) Friedman tests are significant, shifting a criterion's mean by up to 0.80 points on a 5-point scale.
- **Rubric granularity:** 3- or 5-point is the low-bias regime. Both n=2 and n=9 carry higher Cramér's V.

### The number that governs Rung 7

**Ordering alone flips the top-1 candidate on 16–39% of prompts**, and Kendall τ between orderings is only 0.67–0.85.

This is *not* confined to biased judges — GPT-OSS-120B, the lowest-bias judge by χ², still shows 17.5–31.2% top-1 reversal, because rank reversal depends on per-item variance rather than average bias direction. The bias bites hardest in selection, which is exactly what a succession trial is.

Reference-free scoring is not a fix in the other direction: 2607.12885 finds LLM judges systematically too generous without a reference answer.

### Repair path — Rung 7

Both-orders is necessary and insufficient. Add three things:

1. When the two orders disagree, that is a **no-verdict** outcome, not a tiebreak — flag it and escalate, the way an SPRT flags no-consensus.
2. Fix or randomize criterion order too, and record which.
3. Report the per-tranche **flip rate** as a first-class diagnostic. A succession trial that never reports its flip rate is claiming a precision it does not have.

---

## Q3 — Grounded semantics under noisy attack edges

*Feeds: adjudication robustness; Rung 8 diagnostics.*

**Verdict: `[GAP]`. Nobody has measured label-flip rate against an edge error rate. But the right formal machinery already exists and is tractable — and it says grounded is the worst-behaved semantics for this purpose.**

### What exists

**Incomplete Argumentation Frameworks** (IAFs; Baumeister et al., AIJ 2018) are exactly the problem re-read: uncertain attacks `R?` alongside certain attacks `R`; *completions* are the graphs obtained by resolving them; *stability* means the answer is the same in every completion.

2505.16507 gives the operational notions:

- **Relevance** — which uncertain elements must be resolved in *some* situation to reach stability.
- **Strong relevance** — necessary in *all* situations.

Complexity for verification of a set of arguments:

| Semantics | Relevance | Strong relevance |
|---|---|---|
| admissible | **P** | **P** |
| stable | **P** | **P** |
| complete | **P** | **P** |
| **grounded** | **in NP, exact complexity OPEN** | **P** |
| preferred | Σ₂ᵖ-c | Π₂ᵖ-c / coNP-c |

> **Grounded is the open case.** No tractable method was found, because grounded requires *strong admissibility* — the labelling is built by iterated defence from the unattacked set — so an edge touching S can be gr-relevant while not being co-relevant. Minimal example: in `I = ⟨{a,b}, ∅, {(a,b)}, {(b,a)}⟩`, removing `(b,a)` is not co-true-relevant but **is** gr-true-relevant for `{a}`.

`[INFERRED]`, from directionality (Baroni & Giacomin 2007) rather than measured: the blast radius of a single edge error is bounded to the downstream cone — under semantics satisfying directionality, uncertain elements that cannot reach *a* are irrelevant to *a*'s status. So the amplifying structures are long defence chains and odd-length attack cycles, where a spurious edge into an early defender truncates the whole fixpoint below it.

`[UNKNOWN]`: empirical label-flip rate at a given edge error rate.

Also relevant: σ-kernel / strong-equivalence work (Oikarinen & Woltran 2011; Baumann 2012) identifies attacks whose modification has no influence on σ-extensions at all.

### Repair path — Rung 8 (working artifact, not advice)

Stop thresholding extracted edges into a crisp graph.

- Keep low-confidence edges in `R?` and compute stability plus the relevant / strongly-relevant sets.
- Rung 8's headline diagnostic becomes: **"of N uncertain edges, k are relevant and j are strongly relevant."**
- **If k = 0 the adjudication is stable regardless of how the extractor errs** — that is a certificate, not a hope.
- P-time under complete semantics.
- Given that grounded's relevance complexity is open, carry **complete alongside grounded** so a tractable stability certificate exists even where grounded's does not.

---

# TIER 2

## Q4 — Matched-budget multi-agent vs. solo self-revision

*Feeds: the solo-run law's empirical side.*

**Verdict: the solo-run law survives, with a sharper shape than expected and a stated boundary condition.**

2607.28576, *Sample More, Reflect Less*, is the best-designed test: seven methods, three model sizes (1.5B / 3B / 7B), two math benchmarks, 150 paired questions, **36 comparisons with paired bootstrap CIs and Holm correction**, and budget-matching done properly — each method compared against the self-consistency curve *interpolated at that method's own measured token cost*, counting every critique and debate token.

### Headline

- **Zero of 36 comparisons significantly better than repeated sampling at equal cost. Ten significantly worse. 30 of 36 point estimates negative.**
- The split is not simple-vs-elaborate. It is **counting vs. judging.** Every method where the model assesses its own output — Self-Refine, forced Reflexion, Best-of-N with self-verification — is below the equal-cost baseline in **all 18** of its comparisons. Methods adding no self-assessment sit *on* the baseline, not beneath it.
- The confound-free version: Best-of-N draws 8 samples and asks the model to pick. Take the same 8 samples, same tokens, same model, and count the mode instead. **Counting wins by 5–17 points below 7B.** At 7B the gap falls to ~2 points and is indistinguishable from zero — which locates the crossover rather than asserting it.

### The methodological finding worth stealing

**Reflexion as published never fired on the 1.5B model.** It judged itself correct on every question in both benchmarks, silently collapsed into a single chain of thought, and scored well *because it had become cheap*. The authors' line — a method that decides for itself when to act can stop acting without any outward sign — is `false-green-probing` applied to control flow. Their forced variant, which runs the mechanism regardless, lands below baseline.

Reflexion firing rates by setting:

| Setting | Stopped immediately | Mean rounds used (max 3) |
|---|---|---|
| Qwen2.5-1.5B / GSM8K | **100%** | 0.00 |
| Qwen2.5-1.5B / MATH-500 | **100%** | 0.00 |
| Qwen2.5-3B / GSM8K | 77% | 0.60 |
| Qwen2.5-3B / MATH-500 | 31% | 1.82 |

### The boundary

2607.15388 on Omni-MATH finds collaboration gain over a *matched single-agent iterative anchor* is ≈0 on tiers 1–2 and opens sharply from tier 4, reaching 10–20pp on tiers 6–9. Difficulty is the moderator. Cost, though: 400K–616K tokens/problem for the collaborative protocols vs 48K for single-agent iterative.

Counterweights and corroborations:
- 2605.00914 — isolated self-correction prevails over unguided homogeneous multi-agent debate.
- 2606.02866 — debate's effect **reverses sign** across 6,000+ task-condition pairs in data cleaning.
- 2607.11598 — argues the other way (interaction as a third scaling axis). Worth reading as the opposing case.

### Pre-registerable form of the law

> At matched budget, criticism loses to resampling wherever a counting baseline exists and the solo anchor is not already failing outright; the collaborative advantage appears only above a difficulty threshold where the anchor drops below ~70%.

Scope limit the authors themselves flag: on open-ended work majority voting does not exist, so the strongest competitor to criticism is unavailable and the comparison cannot be run in that form.

### Repair path

- Add a **repeated-sampling-with-mode-counting** arm wherever the answer space admits equality.
- Make **"how often did the adaptive gate fire"** a mandatory field in every run record.

---

## Q5 — What makes criticism load-bearing

*Feeds: critic seat prompts; the three-arm ablation protocol.*

**Verdict: it isn't critique quality. It's the interface. And the obvious fix makes it worse.**

2607.15388, on 4,181 verifier-grounded Omni-MATH problems, separates three things that get conflated: **detection**, **uptake**, **repair**.

| Metric | PER (Planner–Executor–Reviewer) | Broadcast (peer deliberation) |
|---|---|---|
| Reviewer precision | **0.861** | 0.644 |
| CouplingRate (useful critique changes next candidate) | **33.6%** | **93.5%** |
| ReviewerGuidedRepairRate | **0.051** | **0.286** |
| Repair (wrong-initial cases) | 11.0% | 25.7% |
| **Neglect** | **48.8%** | 26.2% |
| Try-but-fail | 40.2% | 48.1% |

PER's reviewer is substantially *better* at spotting real errors and substantially *worse* at causing repair. Try-but-fail rates are close. The entire difference is **neglect**.

Cross-family replication on Gemma 3: protocol ranking flips, but the precision–uptake separation persists and widens (PER precision 0.881, uptake 0.092; broadcast 0.722, uptake 0.742).

### The structural difference

In PER the reviewer signal enters a **separable advice field** and the solver can acknowledge it while preserving the candidate. In broadcast the critique enters shared candidate state and **submission requires collective re-approval**, so bypass is harder by design.

### Interventions tested (model family and budget held fixed)

- **ACK-required — forcing explicit acknowledgment — *lowered* final accuracy.** A failed compliance control.
- **EMB — placing guidance directly in the solver's working context — partially recovered.**
- Deeper local reflection (PER-inner6) partially recovered but still trailed, at higher verifier cost.

### The uncomfortable symmetry

Pair this with 2606.00820: *vacuous* reasoning moved 20–39% of otherwise-resistant agents. So:

- Content-free criticism moves artifacts that shouldn't move.
- Content-full criticism fails to move artifacts that should.

Both are interface effects. Neither is a critique-quality effect.

### Repair path — critic seat and ablation protocol

1. Instrument three separate quantities per round, not one: **NeglectRate**, **CouplingRate** (did the carried-forward artifact change), **ReviewerGuidedRepairRate** (did the change help). A seat that detects well and couples badly looks strong under any reviewer-centric metric and solves nothing.
2. **Do not add an acknowledgment requirement.** Documented to hurt.
3. Structural change, not a prompt change: criticism enters the conjecturer's working context, and re-submission requires the criticism to be **discharged** rather than noted.
4. **The three-arm ablation should become four:**
   - no-critique
   - **vacuous-critique (form only)**
   - real-critique-as-advice
   - real-critique-in-context

   Arms 2 and 3 isolate form-effect and interface-effect independently. Without arm 2 you cannot distinguish a working critic from argument-shaped text.

---

## Q6 — Best-answer selection without labels

*Feeds: the results surface — the record keeps every candidate, so post-hoc selection is possible.*

**Verdict: the record-everything design is right, but post-hoc selection is net-negative in two of three tested benchmarks unless you audit first. LLM selectors are the worst available option.**

2607.17531 gives the decomposition to build against:

```
gain = P(recoverable ∧ signal-defined) · q
     − P(reference-correct ∧ signal-defined) · h
```

where *recoverable* = reference wrong but some candidate correct, *q* = conditional selection success, *h* = harm to already-correct outputs. Bounded first by **oracle gap**, then by **signal fidelity**.

### The numbers

| Setting | Mechanism | Gain | Harm |
|---|---|---|---|
| LiveCodeBench (oracle +11.74pp) | public-test verifier, MCC 0.825 | **+8.14pp** | **0** |
| | generated-test verifier, MCC 0.248 | +2.70pp | 0.10% |
| | same-family LLM selector | +3.50pp | **4.69%** |
| | cross-family LLM selector | +1.97pp | **5.65%** |
| MATH-500 | symbolic answer-equivalence | **+4.67pp** vs SC | — |
| | LLM selector (L1 / L3) | **−3.20 / −1.87pp** | — |
| GPQA-Diamond (oracle +3.03pp) | LLM selector (L1 / L3) | **−1.68 / −2.36pp** | 5.30 / 7.07% |

Oracle-gap capture rates on LiveCodeBench: public tests recover 69.32% of recoverable cases at zero harm; same-family LLM 58.70% at 4.69% harm; generated tests 23.30% at 0.10% harm.

### Why GPQA is instructive

87.54% of k=5 pools are answer-identical (mean 1.138 unique letters). Harm cost alone (15/594 = 2.53pp) already exceeds what five recovered cases could compensate. And **oracle gap is a joint property of task, model, prompt, temperature, and sampling config** — a weaker pool shrinks recoverable mass to 0.67% with 94.44% identical pools. It is not a benchmark constant you can look up.

**Signal availability binds separately from fidelity:** generated tests were *active* on only 35.77% of rows; the MATH equivalence key on 69.07%.

Combined with the SHP oracle gap (2606.27009: +0.115 IS over every practical policy, p ≈ 4e-11, unrecovered by any online signal): the gap is real and large in some regimes, near-zero in others, and no natural-language signal locates it.

### Repair path

Before arming any post-hoc selector, run the four-number audit on a small labelled dev tranche — **recoverable mass, coverage, conditional quality, harm** — and deploy only if `capture × recoverable > harm × correct-mass`. The workflow stops early when the gap is small, which is the cheap outcome.

**The good news:** the winning selectors are the **structural, non-LLM** ones — execution, symbolic equivalence. The analogue here is **grounded-extension identity or certificate-checking**: a high-fidelity, zero-harm signal of exactly the shape that won on LiveCodeBench and MATH. An LLM adjudicator picking among candidates is the shape that lost.

---

## Q7 — Completion-budget pathologies

*Feeds: provider profiles; the glm-5.2 empty-completion seat failure.*

**Verdict: fully characterised, with a mechanism, a predictive formula, and a two-call fix worth +25.4pp on the affected subset. The glm-5.2 failure is a known point on a known curve.**

2605.07686 names it the **coupling tax**: reasoning trace Z and answer A share one output budget, `|Z| + |A| ≤ b`, and since Z precedes A autoregressively, when the natural chain length L(q) exceeds b the answer is truncated or **absent entirely**.

### Findings

- **At b=256 on GSM8K, 98.6% of thinking responses produce no parseable answer** — a 69.5pp loss. At b=512: non-thinking 93.1% vs thinking 56.9%.
- Predictive decomposition:

  ```
  Acc_think(b) = F_L(b)·α_c + (1 − F_L(b))·α_t
  ```

  It checks out numerically — at b=512, 0.374 × 99.0% + 0.626 × 31.8% = 56.9%, matching observed; on MATH-500 at b=1024 the estimate and observation are both 18.0%. Twenty 50-sample pilots predict the full budget sweep at **3.48pp RMSE**, so a seat's crossover can be estimated cheaply.
- **Inverse scaling — bigger models are worse.** Tax at b=512 is 36.2pp (8B) vs 77.1pp (27B), a 2.1× ratio, because the 27B natural-stop rate at b=512 is 0.7% vs 37.4% for 8B. At 27B on GSM8K a residual tax survives even a 4096-token cap.
- **Natural stop is a free 99.0% PPV confidence oracle.** Chains that terminate on their own are 99.0% correct.
- **The fix is split-budget generation:** run the reasoning call at `B_r`, then feed the trace — *even truncated* — to a separate non-thinking extraction pass at `B_a`. On the 106 escalated MATH-500 samples this recovers **+25.4pp** over the coupled cascade; at 27B the gap averages **+34.5pp**. Optimal split is heavily skewed to reasoning, since extraction saturates by `B_a ≈ 256–512` (they use 4096:512).
- Crucially it is **mode mismatch, not budget scarcity**: giving thinking mode 512 more tokens yields ≤2pp, because those tokens extend reasoning rather than produce answers. The 31.2pp gap between non-thinking extraction and think-mode parsing on *identical truncated traces* is modal, not budgetary.

Separately, 2608.12150 shows **model rankings are budget-dependent** — a seat comparison run at one budget is measuring the budget as much as the model.

### Repair path — provider profiles

- **Two-call seat protocol as default:** reason at `B_r`, extract at temperature-0 non-thinking with `B_a ≈ 512`, feeding the possibly-truncated trace. Highest value-per-line-of-code item in this list.
- Record **natural-stop** as a per-seat field. Free, and a 99% PPV signal currently being discarded.
- A seat profile should carry an `F_L` estimate and a crossover budget, not a binary works / empty-completion flag. Twenty pilot items gets you both.
- Run every seat comparison at **≥2 budgets** or the profile is uninterpretable.

---

# TIER 3

## Q8 — Cosine thresholds for argument novelty

*Feeds: the dormant NEAR_DUP_EPS-family thresholds.*

**Verdict: do not arm them. Per-corpus calibration is necessary and demonstrably not sufficient — every calibration-shaped repair died on an author change.**

2608.10216 audits this exact gate class. **The score measures how much the wording changed, not whether the meaning held**, and in precisely the pairs these gates exist to catch the two are *anti-correlated*: negation is an additive edit (token-Jaccard ≈ 0.72 with the anchor), faithful restatement is substitutive (≈ 0.06).

### Findings

- Production drift guard: **0 of 56** meaning-breaking mutations caught. Held-out specimen: *"Withhold the study drug from any participant who reports chest tightness"* → *"Administer the study drug…"* scored cosine **0.9608** against a firing line of 0.60.
- Across 90 configuration × threshold × task cells at five shipped operating points (0.30, 0.40, 0.80, 0.85, 0.95), **balanced accuracy never exceeded 0.700, median 0.525**.
- **The corpus trap:** a naturally-authored evaluation corpus inherits the same confounder and returns an *inverted* verdict — decision AUROC exactly **0.000** in 13 of 18 cells. It captured the authors' own headline claims twice while they were actively watching for it.
- **Repairs, all pre-registered, all failed out of domain:**

  | Repair | In-sample | Held-out |
  |---|---|---|
  | Encoder swap (best-auditing encoder) | 0.485 | **0.433** |
  | Logistic gate on (cosine, token-Jaccard) | 0.750 | **0.533** |
  | NLI cross-encoder drop-in | 0.831 | **0.533** |

- No single threshold works even for good encoders: the optimal cut moves **0.11–0.56 cosine between lexical-overlap strata** (median 0.264), and the gate never observes the stratum.
- **Worst mutation classes were modal downgrade** (must→should; AUROC 0.000 / 0.125) **and quantity drift** (0.160 / 0.067) — not negation, which sat near chance.
- Salvageable: the two strongest encoders (bge, mxbai) separated reversal from paraphrase **at matched overlap** at AUROC 0.79–0.90. The signal exists; the deployed configuration in the audit could not see it.

### Why this is sharper for a premise calculus

"P entails Q" vs "P does not entail Q" is a one-token edit. Modal downgrade — the class the guard was worst at — is exactly the class a premise calculus cares about.

### Repair path — NEAR_DUP_EPS family

Either:

- **(a)** Narrow the gate's declared authority to what cosine actually measures — surface-form near-duplication. A legitimate and useful gate that simply is not novelty detection. Or
- **(b)** Build the 2×2 factorial audit corpus (decision × lexical overlap, balanced per anchor, encoder-blind) and validate the specific embedder before arming anything. The harness is public and runs offline in one command.

Two non-negotiables:

1. Validate **across an author change**.
2. Add **polarity cases** to the harness test suite: pairs sharing wording that flip decision (negation, scope, modal strength, quantity), and pairs sharing decision with no shared wording. Four of four audited suites had none, which is why the gate class ships broken.

---

## Q9 — Diversity-eliciting generation: semantic or lexical?

*Feeds: conjecturer seat prompting; diversity signals via the registry.*

**Verdict: `[PARTIAL]`. The metric suite to answer this is settled and validated. The specific experiment — verbalized sampling scored on Vendi with a lexical control — could not be found. A genuine gap, and a cheap one to close.**

### What exists

- **Verbalized Sampling** (2510.01171) attributes mode collapse to typicality bias in preference data rather than algorithmic limits, and elicits a distribution with probabilities instead of a single answer.
- 2608.02618 — meta-persona anchoring plus sequential temperature scaling against the "artificial hivemind."
- 2607.01433 — CreativityNeuro, weight steering for divergent thinking.

### The metric suite (validated in 2604.18005 against five expert annotators)

| Metric | What it measures | Human agreement |
|---|---|---|
| **Vendi Score** | effective number of unique semantic modes | **87%** |
| **1 − φ** (structural disorder) | mean cosine to group centroid; low = collapse onto one point | 82% |
| **PCD** (pairwise cosine distance) | magnitude of spread | 81% |
| **IDF-weighted lexical uniqueness** | **sanity check that semantic diversity is not verbose rephrasing** | — |

The last row is precisely the confound in the question, and it is already operationalised.

### Structural alternatives to prompting tricks (same paper)

- **NGT blind-writing phase** produces the highest initial semantic diversity.
- **Subgroup partitioning** sustains the highest density of constructive conflict in the back half of a discussion.

Both are topology changes, not prompt changes, and both survived a cross-model replication.

### Suggested probe

Run VS against a plain-sampling control on the conjecturer seat; score both on Vendi + 1−φ + IDF-weighted lexical uniqueness.

- Vendi rises **and** lexical uniqueness rises proportionally → rephrasing.
- Vendi rises **and** lexical uniqueness stays flat → real.

That is a publishable answer to a question nobody appears to have asked.

---

## Q10 — LLM accuracy at extracting attack relations

*Feeds: the edge-producing step's error rate — the other half of Q3.*

**Verdict: the number needed is F1 ≈ 0.33–0.43 on Attack edges, under favourable conditions. Read alongside Q3, this is the highest-severity finding in the set.**

2606.16047, on UKP Argument Annotated Essays v2 (402 essays, standard 80-essay test split, 2,407 candidate pairs, **gold component boundaries assumed**, Gemini 2.5 Flash / Pro):

| Method | Macro F1 | F1 (Support) | **F1 (Attack)** | F1 (None) |
|---|---|---|---|---|
| Vanilla | 0.549 | 0.623 | **0.340** | 0.683 |
| CoT | 0.560 | 0.636 | **0.327** | 0.716 |
| Gemini 2.5 Pro, judge-style | 0.578 | 0.635 | **0.412** | 0.688 |
| Full debate (all pairs) | 0.561 | 0.609 | **0.378** | 0.697 |
| Confidence-gated debate (τ=0.70) | **0.585** | 0.630 | **0.427** | 0.698 |
| RoBERTa-large (fine-tuned) | 0.522 | 0.610 | **0.167** | 0.788 |
| RoBERTa-base (fine-tuned) | 0.473 | 0.552 | **0.071** | 0.797 |

None dominates at ~2/3 of pairs; there are only **42 Attack instances in test** and 160 in training, so supervised models collapse on the class that matters and generative models win macro-F1 purely on Attack. Every number above is **under gold boundaries** — an end-to-end pipeline propagates component-detection errors into this stage on top.

### Two secondary findings worth carrying

- **Full debate over all pairs is net-zero and lands below the best single-agent baseline**: 249 improvements against 236 regressions. Confidence gating at τ=0.70 debates only the least-certain 14% and nets +36 (84 improvements, 48 regressions). Push τ to 0.75 and the debated fraction jumps to 48% while Attack F1 falls back from 0.427 to 0.374.

  | Threshold τ | Macro F1 | F1 (Att.) | Debated |
  |---|---|---|---|
  | Manager only | 0.562 | 0.383 | 0 (0%) |
  | > 0.60 | 0.583 | 0.425 | 286 (12%) |
  | **> 0.70** | **0.585** | **0.427** | **332 (14%)** |
  | > 0.75 | 0.571 | 0.374 | 1160 (48%) |
  | Full debate | 0.561 | 0.378 | 2407 (100%) |

- **The mechanism:** below a confidence margin of 0.6, debate is net-positive (54 vs 41). Above margin 0.8, **62% of the changes are for the worse** — the debate introduces doubt where none existed, and one debater constructs a superficially plausible counterargument that misleads the judge. Same shape as the vacuous-reasoning result in Q5.

Authors' own caveat: the +0.007 margin over the strongest single-agent baseline is untested for significance, on one corpus, in one domain.

---

# The one item to act on first

**Q10 and Q3 compose badly, and nothing else in this list is as structurally dangerous.**

The attack-edge extractor runs at F1 ≈ 0.4 on Attack edges, on a gold-boundary single-domain corpus, with errors skewed toward false negatives given a None-dominant prior. That relation is then fed into **grounded semantics** — which, per 2505.16507, is the *worst-behaved* of the five common semantics under edge uncertainty, the one whose relevance complexity is open precisely because strong admissibility means an edge touching the extension can matter under grounded while being irrelevant under complete.

Crisp-thresholding a 0.4-F1 relation into a Dung graph and computing a grounded extension is arithmetic on noise, and Rung 8 will report it with full confidence because the adjudication step has no way to know.

**The fix is not a better extractor.** It is the IAF layer:

- Keep low-confidence edges uncertain.
- Compute relevance and strong relevance in P-time under complete semantics.
- Make the certificate read ***k* relevant uncertain edges remain**, rather than *the grounded extension is E*.
- When *k* = 0 you have a real result. When *k* > 0 you have a list of exactly which edges to spend adjudication budget on — which is also, conveniently, the cheapest possible allocation rule for the confidence-gated debate that Q10 shows is the only version of debate that pays.

---

# Source index

| ID | Title | Used for |
|---|---|---|
| 2607.25398 | HANDBOOK.md: A Benchmark for Long-Context Agentic Instruction Following | Q1 |
| 2607.12963 | The Illusion of Robustness: Aggregate Accuracy Hides Prediction Flips under Task-Irrelevant Context | Q1 |
| 2602.02219 | Am I More Pointwise or Pairwise? Revealing Position Bias in Rubric-Based LLM-as-a-Judge | Q2 |
| 2607.12885 | LLM Judges Can Be Too Generous When There Is No Reference Answer | Q2 |
| 2603.20562 | Permutation-Consensus Listwise Judging for Robust Factuality Evaluation | Q2 |
| 2608.03091 | Position Bias Undermines Preference Consistency in Listwise LLM-Based Reranking | Q2 |
| 2505.16507 | Relevance for Stability of Verification Status of a Set of Arguments in Incomplete Argumentation Frameworks | Q3 |
| 2606.31080 | Beyond But-for Test: Counterfactual Explanation in Abstract Argumentation via Actual Causality | Q3 |
| 2607.28576 | Sample More, Reflect Less: Self-Refine and Reflexion Lose to Repeated Sampling at Equal Token Cost | Q4 |
| 2605.00914 | The Cost of Consensus: Isolated Self-Correction Prevails Over Unguided Homogeneous Multi-Agent Debate | Q4 |
| 2606.02866 | When Helping Hurts and How to Fix It: Multi-Agent Debate for Data Cleaning | Q4 |
| 2607.11598 | Interaction Scaling: Grounding the Third Axis of Test-Time Compute | Q4 (counterweight) |
| 2607.15388 | Precise but Uncoupled: Reviewer Precision Does Not Guarantee Critique Uptake | Q4, Q5 |
| 2606.00820 | Not All Flips Are Conformity: Decomposing Stance Convergence in Multi-Agent LLM Debate | Q5 (prior session) |
| 2603.09723 | RbtAct: Rebuttal as Supervision for Actionable Review Feedback Generation | Q5 |
| 2606.11173 | The Role of Feedback Alignment in Self-Distillation | Q5 |
| 2607.17531 | Oracle Gap and Signal Fidelity: A Fixed-Pool Diagnostic for Test-Time Collaboration | Q6 |
| 2606.27009 | Semantic Early-Stopping for Iterative LLM Agent Loops | Q6 (prior session) |
| 2608.11403 | When Self-Consistency Backfires: Majority Vote Hurts the Majority of Hard Science Problems | Q6 |
| 2605.07686 | The Coupling Tax: How Shared Token Budgets Undermine Visible Chain-of-Thought | Q7 |
| 2608.12150 | Who Thinks Best Depends on How Long You Let Them: Budget-Dependent Rankings | Q7 |
| 2608.16033 | R³-Bench: LLMs Struggle with Resource-Rational Reasoning under Shared Budgets | Q7 |
| 2608.10216 | Similarity Gates Approve Reversals: A Validity Audit of Embedding-Cosine Thresholds | Q8 |
| 2601.16907 | Calibrated Similarity for Reliable Geometric Analysis of Embedding Spaces | Q8 |
| 2606.29571 | Anisotropy Decides Cosine vs. Rank Metrics for Text Embeddings | Q8 |
| 2504.16318 | Semantics at an Angle: When Cosine Similarity Works Until It Doesn't | Q8 |
| 2510.01171 | Verbalized Sampling: How to Mitigate Mode Collapse and Unlock LLM Diversity | Q9 |
| 2604.18005 | Diversity Collapse in Multi-Agent LLM Systems: Structural Coupling and Collective Failure | Q9 (metrics) |
| 2608.02618 | Beyond the Hivemind: Escaping LLM Homogeneity via Meta-Persona Anchoring | Q9 |
| 2607.01433 | CreativityNeuro: Steering Language Model Weights to Improve Divergent Thinking | Q9 |
| 2606.16047 | From Argument Components to Graphs: Multi-Agent Debate with Confidence Gating for Argument Relations | Q10 |
| 2509.15739 | Can LLMs Judge Debates? Evaluating Non-Linear Reasoning via Argumentation Theory Semantics | Q10 |
| 2603.19253 | A Comprehensive Study of LLM-Based Argument Classification | Q10 |
| 2605.13793 | An LLM-Based System for Argument Mining | Q10 |

---

# Open items and cheap probes

| # | Item | Status | Cost |
|---|---|---|---|
| 1 | Depth-by-position curve for instruction-bearing (not fact-bearing) content | `[UNKNOWN]` | Medium |
| 2 | Empirical grounded-label flip rate vs. attack-edge error rate | `[UNKNOWN]` — nobody has run it | Medium; would be a real contribution |
| 3 | Verbalized sampling scored on Vendi **with** IDF lexical-uniqueness control | `[UNKNOWN]` | Cheap; metric suite already validated |
| 4 | Per-seat `F_L` chain-length CDF + crossover estimate | Derivable from 20 pilot items at 3.48pp RMSE | Very cheap |
| 5 | Oracle-gap audit (recoverable mass, coverage, quality, harm) on a labelled dev tranche | Required before arming any post-hoc selector | Cheap; ~600 observations sufficed for GPQA |
| 6 | 2×2 factorial polarity corpus for the embedder configuration in use | Required before arming NEAR_DUP_EPS | Cheap; public harness, one command |
| 7 | Grounded-semantics relevance complexity | **Open problem in the literature** | — |
