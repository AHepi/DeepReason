# Temperature vs verbalized sampling for conjecture diversity — external research note

Operator-supplied 2026-08-28 (plugin literature review, alphaXiv-sourced,
retrieved 28 Aug 2026), committed verbatim below the rule. The claims,
numbers, and citations are EXTERNAL and unverified by this repository's
own instruments; nothing here is evidence in the record's sense. Same
standing as docs/RESEARCH_CONVERGENCE_LOOPS_2026-08-22.md.

Consumption points:

- **The conjecture-diversity experiment (planned, unregistered):** the
  source's §5 decision table and §6 "the experiment nobody has run" are
  the design inputs for a matched-budget live A/B on conjecture
  generation (arms: direct / direction-stratification / verbalized
  sampling / combined). Its own grade for VS rows is C (authors-only,
  no independent replication) — the experiment exists to replace C
  with our own measurement, not to confirm it.
- **Any VS-mode seat design:** the source's §6 closing warning is
  BINDING on design: the verbalized probability numbers are a framing
  device, fabricated by construction; nothing downstream may read them
  as estimates (companion to the seats-never-decide-evidence law).
- **Temperature configuration anywhere:** rows 1-3 (grade A): safe band
  0.7-1.0, never past ~1.2; temperature is not a diversity lever.

---

# Temperature vs. Verbalized Sampling for Idea-Level Diversity

**Scope:** aligned/instruction-tuned LLMs, including reasoning-tuned models. Target use case: generating maximally *semantically distinct* scientific-style conjectures over an API, with a separate downstream criticism stage.

**Headline:** The evidence that raising temperature does *not* buy idea-level diversity is strong and comes from several independent groups. The evidence that verbalized sampling specifically is the better alternative is much weaker — it rests almost entirely on the authors' own appendix. What *is* independently supported is the broader family: prompt-level distribution elicitation beats decoding knobs. Two papers argue the inference-time premise is wrong altogether.

---

## 1. Mechanism

### 1.1 What temperature actually moves

The cleanest result is Karouzos, Tan & Aletras (arXiv:2604.16027), who traced three parallel Olmo-3 post-training lineages across 15 tasks and four diversity metrics. Their finding is a *dissociation*:

> Per-input SBERT semantic diversity drops from 0.32 (base) to 0.11–0.12 (post-trained); Vendi drops from ~3.4 effective modes to ~1.8, with near-total collapse on math (GSM8K: 1.3 modes). Meanwhile **EAD (expectation-adjusted n-gram diversity) remains stable or increases**. On WritingPrompts, Think's EAD rose 0.23 → 0.80 while SBERT fell 0.54 → 0.20.

Their gloss: aligned models use varied vocabulary and phrasing to express semantically identical content. That is exactly the failure mode you care about.

Their Appendix H gives the magnitude comparison that matters most for your decision:

| Change | Mean SBERT effect |
|---|---|
| Base model at T=1.0 vs T=0.6 | **−11.2%** |
| Base → Think-SFT (training) | **−62%** |

Temperature moves semantic diversity roughly **5× less** than the training step that destroyed it. That is the single most useful number in this literature.

Independent corroboration:

- **Zeng et al. (arXiv:2604.24927, ESamp):** "stochastic perturbations at the token level tend to induce surface-level lexical variation without substantially altering the underlying reasoning strategy." Vanilla T=1.0 gives Vendi 1.62 on creative writing vs 1.67 for their representation-space method; on AIME25, vanilla Vendi 0.32 vs 0.46. They explicitly contrast vocabulary-space methods (which "fail to capture semantically equivalent sequences expressed with different surface forms") against representation-space ones.
- **Kong, Lai, Piao & Evans (arXiv:2605.17193):** in closed-loop multi-LLM simulations (200–1000 rounds, 7 model families, 45 conditions), raising temperature *increased lexical diversity while decreasing semantic diversity*. Regression coefficients for T=2.0 on within-run semantic diversity: GPT-4o-mini −0.246 (p=4×10⁻⁵), Phi-4 −0.340 (p=2.5×10⁻⁵), DeepSeek-V3 −0.080 (p=0.025). Across 62 baseline comparisons, **no intervention** — four temperature levels, six prompt formulations including an explicit diversity instruction, RAG memory, mixed models, uncensored variants, sycophancy steering, GRPO-for-diversity — produced a positive significant effect after Bonferroni correction.

### 1.2 Why temperature *structurally cannot* fix it

Banayeeanzade et al. (arXiv:2605.11128, USC) give the strongest theoretical account, and it does not depend on the typicality-bias story at all. They decompose the bottleneck into:

- **Order miscalibration** — valid tokens are not reliably ranked above invalid ones, so any rank-based cutoff must trade recall of valid continuations against admission of invalid ones. Theorem 4.2 shows these local errors compound multiplicatively: sequence recall ≤ (1−δ)⁻ᶜ·e⁻ᶜᵐ.
- **Shape miscalibration** — next-token distributions are sharp-headed and heavy-tailed (geometric decay in head, Zipf-like tail). Raising temperature moves mass off the head, but most of it flows into the *invalid* tail rather than to rare valid alternatives.

Theorem 5.2: any temperature-scaled distribution with validity ≥ 1−ε has diversity ≤ e^(−m·c(ε)), with c(ε) → ln 2 as ε → 0. Their summary: **"Temperature can flatten the distribution, but it cannot selectively recover valid diversity."**

Their oracle experiment quantifies the loss (best diversity at validity ≥ 0.8, 14 models):

| Strategy | Embedding diversity ↑ | Self-BLEU ↓ |
|---|---|---|
| oracle (knows valid set) | 0.40 | 0.69 |
| top-k | 0.33 | 0.71 |
| min-p | 0.29 | 0.80 |
| top-p | 0.25 | 0.86 |
| no filtering | 0.25 | 0.86 |

⚠️ **Caveat they raise themselves:** the controlled tasks (random-number generation, "name a US state") are diagnostics with exactly-known valid sets, not open-ended generation. They say explicitly that in creative writing and scientific ideation, validity is semantic and graded, and their results should be read as mechanism diagnostics, not a complete account.

### 1.3 The typicality-bias account — and three competitors

Zhang, Yu, Chong et al. (arXiv:2510.01171, the VS paper) argue mode collapse originates in **preference data**: annotators prefer more typical text independent of task quality. Fitting a Bradley-Terry model on 6,874 correctness-matched HelpSteer pairs:

| Reference model | Controls | α̂ | SE | p |
|---|---|---|---|---|
| Llama-3.1-405B | logprob only | 0.569 | 0.073 | 5.5×10⁻¹⁵ |
| Llama-3.1-405B | + surface controls | 0.260 | 0.060 | 1.4×10⁻⁶ |
| GLM-4.5 | logprob only | 0.649 | 0.072 | 1.5×10⁻¹⁹ |
| GLM-4.5 | + surface controls | 0.326 | 0.060 | 5.6×10⁻⁸ |

Surface controls (token count, Flesch–Kincaid, type–token ratio, sentence length) roughly halve the coefficient but don't eliminate it. Plugging α > 0 into the RLHF optimum gives π\* ∝ π_ref^γ with γ = 1 + α/β > 1 — a power transform.

**Note the awkward implication the paper states outright: this sharpening "behaves like temperature scaling."** If alignment is a power transform of the reference distribution, one might expect temperature to undo it. It does not, and the reason is that γ-sharpening applies to the *sequence*-level distribution over a set of complete responses, whereas temperature acts per-token. Undoing sequence-level sharpening with token-level flattening also inflates the invalid tail at every step — which is precisely the compounding failure Banayeeanzade et al. formalise. This asymmetry is the actual mechanistic case for prompt-level intervention, and neither paper states it cleanly.

Three competing accounts locate the collapse elsewhere:

| Account | Source | Locus | Key supporting evidence |
|---|---|---|---|
| Typicality bias in preference data | Zhang et al. 2510.01171 | RLHF/DPO reward | α̂ significant across 4 preference datasets, 6 base models |
| Low-entropy **SFT data** fit | Springer et al. 2605.09995 (CMU/Apple) | SFT likelihood | Lower post-training loss → less diversity; **more** SFT examples → **less** diversity (a confirmed novel prediction); inverse scaling with model size |
| Training **data composition**, not method | Karouzos et al. 2604.16027 | SFT or DPO depending on data | Think loses 62% at SFT; Instruct loses 38% at SFT + 23% at DPO; RL-Zero (bypasses both) retains 93% |
| Intrinsic to autoregressive self-conditioning | Kong et al. 2605.17193 | Decoding dynamics | Alignment removal (uncensored variants) and sycophancy steering (58% bias reduction) both fail to attenuate collapse |

**These are not all compatible.** Springer et al. locate the collapse at SFT, *before any preference data exists*, and confirm a prediction the typicality account does not make. Karouzos et al. show the same DPO recipe produces a −4% or a −23% drop depending purely on upstream SFT data. The typicality-bias story is the only one unique to the VS authors, and it is the one motivating VS.

### 1.4 Independent evidence for prompt-level elicitation

Nothing I found independently replicates VS. The closest independent tests of the *family*:

- **Ibrahim, Azad & Baten (arXiv:2605.30150)** — GPT-5.4, Claude Sonnet 4.6, Gemini 2.5 Pro on AUT, slogans, stories, with full-pipeline token accounting. Two anchorless prompt-level controls beat temperature-style baselines and rival seed-and-regenerate pipelines at a fraction of the cost (details in §3).
- **Wong et al., SimpleStrat (NeurIPS 2025)**, cited by both — LLMs can partition a response space without seeing sample answers, then use those partitions to improve coverage.
- **Springer et al.**, "brainstorm" (plan-then-condition) and "multiple(n)" (n responses in shared context with a diversity instruction, n up to 32) — both raise semantic entropy over direct prompting.

⚠️ **Springer et al. is a partial disconfirmation.** Multiple(n) "raises semantic entropy, [but] it does not close the gap between base and post-trained models, nor does it remove the residual inverse scaling with respect to model size." The VS paper's own Tulu-3 ablation agrees in magnitude: VS recovers **66.8%** of base diversity, vs 23.8% for direct prompting. Prompt elicitation is a large partial fix, not a full one.

---

## 2. Quality cost curves

### 2.1 Where coherence breaks

The most carefully judged temperature study is Parupudi et al. (arXiv:2606.01451): Llama-3.1-8B-Instruct, 500 open-ended creative prompts (WritingPrompts, AUT, HellaSwag), T ∈ {0.3, 0.8, 1.5}, ranked by two LLM judges *and* three blind human raters under a coherence-first rubric.

| T | Judge/human verdict |
|---|---|
| 0.3 | Ranked 1st on 217/500 (gpt-4o), 248/500 (gemini-2.5-pro) |
| 0.8 | Ranked 1st on 293/500, 321/500 |
| 1.5 | Ranked **last on 499/500 and 500/500**; last by all three humans |

Two things matter here:

1. **The cliff is between 0.8 and 1.5**, and it is sharp, not gradual. Post-temperature mass remaining on the pre-temperature top-90% plausible set: 1.000 at T=0.3, 0.982 at T=0.8, **0.868 at T=1.5** — a 13-point leak onto tokens the model itself did not consider plausible. The 95% cumulative-mass width inflates from ~1 to ~131 tokens. At T=1.5, 88.4% of sampled tokens fell outside the captured top-200.
2. **T=0.3 and T=0.8 were statistically indistinguishable in judged creativity** — within 0.05 rank units for every human rater. The extra sampling entropy across that whole range bought nothing detectable.

Inter-rater ceiling was ρ=0.771; the averaged LLM judge hit ρ=0.832 against the human majority, so this is not judge noise.

### 2.2 Where truncation methods break

Ding et al. (arXiv:2604.11012) sweep T from 1.0 to 10.0 across four reasoning benchmarks. Probability-space truncation collapses; logit-space truncation does not:

| Method | LLaMA-3-70B AQuA @ T=1.0 | @ T=5.0 | @ T=10.0 |
|---|---|---|---|
| top-p (0.9) | 74.02 | 4.33 | 0.00 |
| min-p (0.1) | 74.41 | 16.54 | 0.79 |
| top-k (20) | 73.23 | 15.75 | 3.54 |
| top-nσ (1.0) | 74.80 | 72.83 | 72.83 |
| min-k | 73.23 | 72.05 | 73.62 |

They report near-total semantic collapse (>90% noise rate) above T=2.0 for probability-based methods. Their framing is directly useful: **existing truncation methods conflate two distinct effects of temperature — diversifying among plausible candidates, and admitting noise from the tail.** Logit-space methods (top-nσ, min-k) are temperature-invariant by construction, which decouples them.

### 2.3 Curves by model class

**Base vs RLHF vs RLVR** (Karouzos et al., stage-wise % of base SBERT lost, 15-task average):

| Lineage | SFT | DPO | RL | Retained |
|---|---|---|---|---|
| Think (CoT distillation, 2 teachers) | −62 | −4 | +4 | 38% |
| Instruct (broad multi-source) | −38 | −23 | −5 | 34% |
| RL-Zero (RL direct from base) | — | — | — | **93%** |

Both supervised lineages converge to 1.3–1.6 Vendi modes among correct answers. Data composition sets *when* you fall off the cliff, not *where the floor is*. RL-Zero keeps the diversity but pays heavily in quality (49.8–61.0% on GSM8K vs 93% for Think).

**Reasoning-tuned models specifically** — three findings, all relevant to you:

1. **Suppressing CoT does not recover diversity.** Think-not-thinking matches Think on SBERT at every stage and every task category, while accuracy drops sharply (GSM8K −18%, MATH-Algebra −28%, HumanEval −32%, MATH-Geometry −32%). Conclusion: *"Practitioners cannot recover diversity by switching Think models to direct-answer mode; the cost is paid at training time."* Your disabled hidden CoT is not costing you diversity — it's only costing you accuracy.
2. **Think models retain more correct-answer diversity than Instruct** despite collapsing more in aggregate — their NLI diversity stays above the contradiction threshold on value-pluralism and creative tasks where Instruct's falls below.
3. **Reward specificity predicts diversity loss**: format rewards (99% retained) > math rewards > code pass/fail rewards (88–90%). Verifiable rewards that admit one dominant strategy compress hardest.

**Inverse scaling** (Springer et al., replicating NoveltyBench): base-model semantic diversity *increases* with size across Qwen 0.5B→72B and Llama 1B→70B, while post-trained diversity *decreases*. The gap widens with scale, and holds under direct, brainstorm, and multiple(2/8/32) prompting. Larger frontier models are more collapsed, not less.

### 2.4 Non-monotonicity on ideation

Chen et al. (arXiv:2604.18005), 6,000 research proposals across 20 topics, DeepSeek-V3, 2×3 factorial:

| Structure | T=0.3 | T=0.7 | T=1.0 |
|---|---|---|---|
| Naive | 3.387 | 3.092 | 3.445 |
| Leader-Led | 2.787 | 2.285 | 2.788 |

Vendi is **higher at both T=0.3 and T=1.0 than at T=0.7** for both structures — temperature is not monotonic in idea diversity on this task. Two-way ANOVA: structure η²=0.420, temperature η²=0.135, interaction η²=0.007 (n.s.). **Prompt/interaction structure explains ~3× more variance than temperature.** They also ran a 2×2 on prompt identity × tone: identity η²=0.058, tone η²=0.023 — so *generic* prompt framing does little, while *structural* changes do a lot. That distinction matters when evaluating whether VS-style prompting is "just prompting."

---

## 3. Head-to-head comparisons

### 3.1 VS vs temperature — one source only

Everything here is **Zhang et al. Appendix F.3, the VS authors' own ablation**. Poem generation, GPT-4.1 and Gemini-2.5-Flash, T ∈ {0.4, 0.6, 0.8, 1.0, 1.2, 1.4}.

Finding: VS-Standard's diversity–quality Pareto front sits above Direct and Sequence *at every temperature*, on both models. Within methods, "higher temperatures generally increase diversity at the cost of reduced quality." Notably, Gemini-2.5-Flash's entire quality range across the full temperature sweep spans 63.2–64.2 — temperature bought almost nothing in either direction on that model.

Main-body semantic diversity (mean across models, % = 1 − mean pairwise cosine similarity):

| Method | Poem | Story | Joke |
|---|---|---|---|
| Direct | 11.4 | 22.2 | 30.0 |
| CoT | 12.2 | 23.2 | 39.9 |
| Sequence (list of k) | 18.3 | 29.6 | 58.8 |
| Multi-turn | 14.9 | 26.0 | 57.6 |
| **VS-Standard** | 21.9 | 34.7 | 62.5 |
| **VS-CoT** | **25.8** | **38.2** | 62.9 |
| **VS-Multi** | 23.2 | 36.0 | 62.8 |

Equal-token-budget comparison (their Table 30): VS-Standard costs 1.12× Direct and delivers 2.11× the diversity gain at comparable quality; Sequence costs 0.94× for 1.74×.

Human study, 90 annotators, 4-point diversity Likert: VS-Standard beat Direct and Sequence on all three tasks (poem 2.39 vs 1.90/2.07; story 3.06 vs 2.74/2.76; joke 3.01 vs 1.83/2.93), inter-annotator agreement 0.49–0.87.

⚠️ **Limits of this evidence.** One task family (poem) for the temperature sweep, two models, embedding-cosine diversity, a single LLM judge (Claude-3.7-Sonnet) for quality. I found **no independent replication** of the VS-vs-temperature comparison.

### 3.2 On hypothesis generation specifically — nothing direct

No paper I found evaluates VS on scientific conjecture or hypothesis generation. The nearest proxy is the VS paper's own synthetic math-problem generation (§7): 1,000 competition problems generated at k=5, used to SFT three models, evaluated on MATH500/OlympiadBench/Minerva:

| Gen method | Avg. downstream accuracy |
|---|---|
| No SFT baseline | 32.8 |
| Direct | 30.6 |
| CoT | 33.7 |
| Sequence | 34.3 |
| VS-Standard | 36.1 |
| VS-CoT | 36.9 |
| **VS-Multi** | **37.5** |

That's a genuine "distinct instances downstream" result — direct prompting made things *worse than no SFT at all*, which is a striking demonstration of the collapse — but it is not conjecture generation.

### 3.3 The best independent head-to-head on ideation

Ibrahim, Azad & Baten (arXiv:2605.30150) is the most relevant independent study, though it tests VS-adjacent methods rather than VS. Three task families (alternative uses, slogans, stories), three frontier models, 150 outputs per cell, six generation methods × two instruction strategies, with **full-pipeline token accounting**.

Two anchorless prompt-level controls:

- **`diverge`** — a population-referential instruction: *"try to make it stand out from other responses that might be generated for this same task."* Note this is counterfactual and population-level, not "be creative." Δ D_pair ranges +0.0299 [0.0299, 0.0486] (GPT-5.4) to +0.0622 [0.0534, 0.0722] (Claude Sonnet 4.6), at ~1.1× token cost, **while preserving or improving quality proxies**.
- **`strat`** — semantic direction stratification: one planning call asks the model to propose broad semantic directions, then generation budget is allocated evenly across them, in parallel, with no seed examples.

Diversity gain over the neutral independent baseline:

| Model | strat–diverge | best peer-anchored |
|---|---|---|
| GPT-5.4 | +0.1717 [0.1624, 0.1810] | +0.1706 (peer2) |
| Claude Sonnet 4.6 | **+0.2526** [0.2443, 0.2610] | +0.2081 |
| Gemini 2.5 Pro | **+0.1335** [0.1231, 0.1443] | +0.1278 |

`strat–diverge` matches or beats seed-and-regenerate pipelines while staying single-stage and anchorless, and wins clearly on diversity gain per 100k pipeline tokens. It also led on region entropy (+0.220) and medoid distance (+0.173) — i.e. it genuinely covers more semantic regions, not just spreads points apart.

**For conjecture generation this is probably the most actionable independent result in the whole literature**, because hypothesis space does have articulable axes (mechanism / level of description / measurement modality / scope / formal apparatus) that a planning call can enumerate.

---

## 4. Composition

### 4.1 Does VS stack with decoding knobs?

Again, Appendix F.3 only.

| Knob | Range tested | Interaction with VS |
|---|---|---|
| Temperature | 0.4–1.4 | **Orthogonal.** VS front sits above baselines at every T; standard diversity↑/quality↓ trend within each method. |
| Top-p | 0.7–1.0 | **Synergistic.** Under VS, *both* quality and diversity rise from p=0.7 to ~0.95, then quality slightly declines. Optimum ≈ 0.95. |
| Min-p | 0.0–0.1 (Qwen3-235B, Llama-3.1-70B-Instruct) | **Strongest separation of any pairing.** VS "maintains exceptionally high quality even at diversity levels that cause a significant quality collapse in Direct and Sequence." |
| k (candidates) | 1–20 | Higher k → more diversity, small quality cost. VS dominates the Pareto front at every k. |

### 4.2 The probability threshold — where it saturates and breaks

Prompting *"sample from the tail distribution, where each response should be < p%"*, sweeping p ∈ {1.0, 0.9, 0.5, 0.2, 0.05, 0.005, 0.001}:

- **Creative writing:** diversity rises monotonically as p falls, all the way to 0.001, for both GPT-4.1 and Gemini-2.5-Flash. Baselines cannot be tuned this way at all.
- **Open-ended QA (constrained answer space):** Coverage-N peaks near **p=0.1** and *drops* at p=0.01. Precision peaks at p=0.9 then falls monotonically. GPT-4.1's KL spikes at p=0.01, which the authors call instability. **Below p=0.01 the model often returns empty outputs**, and they excluded those thresholds.

Conjecture generation sits between these poles — more constrained than poetry, less than enumerative QA — so I'd expect the QA saturation behaviour to be the better guide.

### 4.3 Cross-family composition (independent)

- Zeng et al. combined ESamp (decoding-level) with FIRE (temperature-schedule-level) on Qwen3-8B/AIME24 and got Pass@64 beyond either alone — evidence that interventions at different levels of the stack do stack.
- Ibrahim et al.: `diverge` composes positively with `indep`, `self`, `peer1`, `peer2`, and `strat` on all three models (inconclusive only for `repr`).
- Ding et al.: logit-space truncation *removes* temperature from the noise-admission path entirely, which is the cleanest way to make temperature and other knobs independent.

⚠️ **Methodological warning from Banayeeanzade et al.:** different truncation methods hit their best validity–diversity trade-off at *different* temperatures, so comparing methods at one fixed temperature is misleading. Every head-to-head above except theirs and Ibrahim et al.'s does exactly that.

### 4.4 Is there a known Pareto frontier?

**No.** The VS paper claims VS-CoT and VS-Multi "approach the Pareto front" on poem generation, but no one has characterised the frontier for hypothesis generation, or for any task with reasoning models, or with all knobs swept jointly. Ibrahim et al. give the only three-way diversity–quality–**compute** frontier, and VS is not on it.

---

## 5. Decision table

Evidence strength: **A** = multiple independent groups, converging; **B** = one strong independent study, or several with caveats; **C** = single source or authors' own results only; **D** = inferred from adjacent findings.

| # | Situation | Recommendation | Evidence | Basis |
|---|---|---|---|---|
| 1 | You want more *distinct ideas* and reach for temperature first | **Don't.** Temperature moves semantic diversity ~5× less than the training step that removed it, and mostly buys wording variety | **A** | Karouzos 2604.16027 App.H (−11.2% vs −62%); Zeng 2604.24927; Kong 2605.17193 |
| 2 | Aligned model, single-shot open-ended generation, want a safe default T | **T = 0.7–1.0.** Do not exceed ~1.2 | **A** | Parupudi 2606.01451 (T=1.5 last on 499/500 by judges and 3/3 humans); Zhang 2510.01171 Fig.20 |
| 3 | You believe raising T past 1.2 is fine because you'll filter downstream | **No.** Above ~1.5 the model samples tokens it never considered plausible (13pp mass leak; 88% of sampled tokens outside top-200). You're filtering noise, not ideas | **A** | Parupudi 2606.01451; Ding 2604.11012 (>90% noise rate above T=2.0) |
| 4 | You want the diversity gain of high T without the noise, and can set logit-space params | **top-nσ (n≈1.0) or min-k**, then raise T freely — these are temperature-invariant by construction | **B** | Ding 2604.11012 (min-k 73.6% at T=10 vs top-p 0.00%) |
| 5 | **Primary lever for distinct conjectures** | **Semantic-direction stratification**: one planning call to enumerate 5+ broad directions, then parallel generation with budget split evenly across them | **B** | Ibrahim 2605.30150 (3 frontier models, best diversity–quality–compute frontier, +0.13 to +0.25 D_pair); Wong SimpleStrat NeurIPS'25 |
| 6 | Near-free add-on to any generation call | Append a **population-referential divergence instruction** — "stand out from other responses that might be generated for this same task," not "be creative" | **B** | Ibrahim 2605.30150 (+0.03 to +0.06 D_pair at 1.1× cost, quality preserved or improved) |
| 7 | **Secondary lever**: single-call multi-candidate elicitation | **VS-Standard or VS-CoT, k=10–20**, with verbalized probabilities. Expect ~1.9–2.1× diversity at ~1.1× token cost | **C** | Zhang 2510.01171 §5, App.F.2/F.3 — authors' own; no independent replication found |
| 8 | Tuning the VS probability threshold | Start at **p ≤ 0.1**. Do not go below **0.01** | **C** | Zhang 2510.01171 App.F.6 — coverage peaks at p=0.1, KL spikes and outputs go empty below 0.01 |
| 9 | Choosing a VS variant when hidden CoT is disabled | **VS-CoT is still available** (it's *verbalized* reasoning in the output, not hidden thinking tokens) and was strongest on diversity. Costs output tokens | **C→D** | Zhang 2510.01171 Fig.3a-c; interpretation mine |
| 10 | API exposes min-p | **VS + min-p ∈ [0.02, 0.05]** — the largest Pareto separation in any pairing tested | **C** | Zhang 2510.01171 App.F.3 Fig.22 (open-weight models only) |
| 11 | API exposes only top-p | **top-p = 0.95** with VS. Both quality and diversity rise up to ~0.95 | **C** | Zhang 2510.01171 App.F.3 Fig.21 |
| 12 | Reasoning model, considering disabling thinking to get more diverse answers | **Won't help.** CoT suppression costs 8–32% accuracy and leaves answer-level diversity unchanged | **B** | Karouzos 2604.16027 §4.2 |
| 13 | Tempted to run N independent samples of the same prompt at high T | **Weakest option available.** Repeated sampling from one prompt is exactly the regime that mode collapse defeats | **A** | Zhang 2510.01171 §C; Karouzos 2604.16027 (majority-vote gain +0.4% for Think vs +24% for base) |
| 14 | Tempted to add a multi-agent debate/refinement loop for diversity | **Don't.** 12 intervention families across 45 conditions all failed; structural coupling makes it worse | **B** | Kong 2605.17193; Chen 2604.18005 (Leader-Led −0.6 to −0.8 Vendi at every T) |
| 15 | Choosing model size for maximum idea diversity | Larger aligned models are **more** collapsed, not less — but also benefit more from VS. Net direction unresolved | **C** | Springer 2605.09995 (inverse scaling, 2 families × 4 sizes) vs Zhang 2510.01171 Fig.3e (2 small vs 2 large models) |
| 16 | You need *both* knobs | **VS/stratification sets the operating point; temperature fine-tunes within it.** Structure explains ~3× the variance temperature does | **B** | Chen 2604.18005 (η² 0.420 vs 0.135, interaction n.s.); Zhang 2510.01171 App.F.3 |

### Concrete starting configuration for DeepReason conjecture generation

```
Stage 0 (once per problem):  planning call → 5–8 orthogonal conjecture directions
                             (mechanism / level of description / measurement /
                              scope / formal apparatus / failure mode ...)

Stage 1 (parallel, per direction):
  prompt      = task + direction constraint
                + VS framing: "give k candidates with estimated probabilities"
                + probability threshold: each candidate < 10%
                + population-referential divergence clause
  k           = 10
  temperature = 0.9
  top_p       = 0.95   (or min_p = 0.03 if exposed)
  thinking    = off
```

Rationale: rows 5, 6, 7, 8, 11, 16. Stratification does the heavy lifting; VS-within-direction prevents each direction from collapsing to its own local mode (Theorem D.2 in the VS paper: a plain list prompt collapses to a "bestseller list" of the top-k modes); temperature is set at the top of the safe band rather than pushed.

---

## 6. Where the evidence is thin, contradictory, or single-sourced

**Single-sourced to the VS authors:**
- Every VS-vs-temperature, VS-vs-top-p, VS-vs-min-p comparison (Appendix F.3).
- The k-scaling and probability-threshold curves (F.2, F.5, F.6).
- The equal-token-budget cost ratio (Table 30).
- The "more capable models benefit more from VS" trend — this rests on **two small and two large models from two families**. Treat as a hypothesis, not a finding.

**Genuine gaps:**
- **No VS evaluation on hypothesis or conjecture generation.** Nearest proxy is synthetic math-problem generation.
- **No VS evaluation on reasoning-tuned models with thinking mode as a controlled variable.** Qwen3-235B appears in the min-p ablation with no mode specified.
- **No characterised Pareto frontier** for any task with all knobs swept jointly.
- **No independent replication of VS at all** in this search.

**Direct contradictions:**
- Karouzos et al. conclude the opposite of the VS thesis: *"diversity collapse is determined during training by data composition and cannot be addressed at inference time alone."* They did not test VS, so this is a clash of framings rather than of results — but it is a real clash.
- Springer et al. find multiple-response prompting raises entropy without closing the base↔post-trained gap or removing inverse scaling. The VS paper's own 66.8%-of-base recovery figure is consistent with this: prompt elicitation is a large partial fix.
- Kong et al. found *no* prompt intervention worked, including an explicit diversity instruction. **Scope caveat:** their setting is closed-loop recursive multi-agent interaction over 200–1000 rounds, where the Data Processing Inequality applies to the loop. Single-shot generation from a fixed prompt is not the same system, and their result should not be read as refuting VS. But it does mean: don't put your conjecture generator inside a self-conditioning loop.
- The mechanism is genuinely contested four ways (§1.3), and the SFT-locus account (Springer et al.) makes a confirmed prediction the typicality account does not.

**One thing worth flagging about the probabilities themselves.** VS requires the model to emit numeric probability fields it cannot actually compute. Appendix F.4 tested seven different definitions — implicit, explicit, relative, percentage, confidence, perplexity, NLL — and all performed comparably. The paper's own theoretical story (the representativeness heuristic: the model produces what a *representative sample* would look like) does not require the numbers to be calibrated at all. So the probabilities are best understood as a **framing device that changes what "typical" refers to**, not as a signal. This is worth holding onto given what's known about required closed-vocabulary fields under structured output: if the numbers are fabricated by construction, don't build anything downstream that reads them as estimates. Rank order across candidates within one response might carry weak signal; the values almost certainly do not.

**The experiment nobody has run.** Matched-budget comparison on scientific conjecture generation: temperature sweep vs VS vs stratification, semantic distinctness measured with an embedding metric *and* a domain-expert or criticism-stage pass rate, on a reasoning model with thinking off. Everything in row 5 and row 7 above is transfer from creative writing and alternative-uses tasks. Given the criticism stage already gives you a quality signal, you're unusually well placed to run it.

---

## Sources

| ID | Citation |
|---|---|
| 2510.01171 | Zhang, Yu, Chong, Sicilia, Tomz, Manning, Shi. *Verbalized Sampling: How to Mitigate Mode Collapse and Unlock LLM Diversity.* ICML 2026 (v4, Jul 2026) |
| 2604.16027 | Karouzos, Tan, Aletras. *Where does output diversity collapse in post-training?* Sheffield, Apr 2026 |
| 2605.11128 | Banayeeanzade, Yang, Tarsadiya, Bahrani, Blas, Samuel, Jia, Razaviyayn, Karimireddy. *Sampling More, Getting Less: Calibration is the Diversity Bottleneck in LLMs.* USC, May 2026 |
| 2605.09995 | Springer, Advani, Aichberger, Bradley, Malach, Saremi, Williamson, Nakkiran, Littwin, Raghunathan. *Annotations Mitigate Post-Training Mode Collapse.* CMU/Apple, May 2026 |
| 2605.17193 | Kong, Lai, Piao, Evans. *Multi-LLM Systems Exhibit Robust Semantic Collapse.* Toronto/Chicago/Tsinghua, May 2026 |
| 2605.30150 | Ibrahim, Azad, Baten. *Anchorless Diversification for Parallel LLM Ideation.* USF, May 2026 |
| 2606.01451 | Parupudi, Ponnada, Kaushal, Parupudi, Dasari, Bulusu. *Before and After Temperature: A Distributional View of Creative LLM Generation.* May 2026 |
| 2604.24927 | Zeng, Lu, Li, Zhang, Li, Ren. *Large Language Models Explore by Latent Distilling.* ICML 2026 |
| 2604.11012 | Ding, Li, Garces Arias, Aßenmacher, Heumann, Zhang. *Min-k Sampling: Decoupling Truncation from Temperature Scaling via Relative Logit Dynamics.* Apr 2026 |
| 2604.18005 | Chen, Tong, Yang, He, Zhang, Zou, Wang, He. *Diversity Collapse in Multi-Agent LLM Systems.* NUS/CUHK-SZ, Apr 2026 |
| 2608.07460 | Sahu, Bansal, Stengel-Eskin. *CreativeInstruct: Scalably Teaching LLMs to Balance Quality, Creativity, and Diversity.* Aug 2026 |
