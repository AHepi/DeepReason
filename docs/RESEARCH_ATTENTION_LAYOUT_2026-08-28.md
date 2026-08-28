# Attention geometry and context layout for iterative harnesses — external research note

Operator-supplied 2026-08-28 (plugin literature review, alphaXiv-sourced,
retrieved 28 Aug 2026), committed verbatim below the rule. The claims,
numbers, and citations are EXTERNAL and unverified by this repository's
own instruments; nothing here is evidence in the record's sense.

Consumption points:

- **Any render/pack/scratch redesign:** the source's §(a) placement
  table and its two cross-cutting rules ("selection dominates
  ordering"; "every round needs something the loop did not produce")
  are design inputs. The robust-across-models list is usable directly;
  everything in §(b) is model-specific and needs local re-testing on
  the bench model before being relied on.
- **The evidence-channels doctrine:** the source's strongest negative
  (closed loops contract semantically; twelve in-loop interventions
  failed; only external input changes the trajectory) is external
  corroboration of the standing ruling that research/simulation/
  code-testing channels stay ON. Corroboration, not proof.
- **Carry-forward design in amendment epochs:** verbatim carry of prior
  rounds causes rehashing; distilled carries better; raw text stays
  retrievable by reference (the reference-menu pattern is already the
  repo's shape for this).

---

# Attention Geometry and Context Layout for Multi-Round Reasoning Harnesses

Evidence review, August 2026. Scope: what is known about positional attention behaviour, prompt layout, self-conditioning across rounds, and compression strategies — read specifically for a conjecture-and-criticism harness that re-feeds a growing append-only record through an API each round.

---

## Headline

Five findings change harness design more than anything else in this literature:

1. **The U-shape is architectural, not learned, and it is scale-free.** It re-instantiates inside *every* delimiter-bounded sub-block of the prompt, not just globally.
2. **Prime positions amplify whatever occupies them**, including stale or refuted material. This is why sophisticated reordering fails in realistic mixed-quality contexts.
3. **Carrying prior-round output verbatim causes rehashing.** One-sentence summaries of prior assistant turns beat full text on both quality and topicality across four models.
4. **Closed loops contract semantically, and twelve intervention classes failed to stop it.** Only genuinely external input changes the trajectory.
5. **Self-revision without an external error signal is re-generation, not revision**, and its information gain collapses to ~zero after the first pass.

---

## 1. Positional behaviour

### What is settled

**The U-shape precedes training.** Chowdhury (arXiv 2603.10123) derives a closed form for influence density in a causal decoder with residual connections and shows the U-shape exists at random initialisation. Causal masking forces a logarithmically diverging primacy tail (early tokens sit on combinatorially more paths); residual connections create an isolated O(1) delta spike at the final token. Between them sits an O(1/(H−1)!) dead zone, H being depth. Untrained Qwen2-0.5B and GPT-2 reproduce the predicted shape with Spearman ρ = 0.99, and the shape is *identical* with RoPE removed. Pretraining adds sharp local spikes at content discontinuities but does not lift the middle floor — normalised to the recency anchor, the valley gets *deeper* during the first 100 steps. Peak-to-trough ratio: ~10² at init, ~10³ after pretraining.

**The most operationally important corollary:** the prior is scale-free. Any sub-interval bounded by attention anchors — chunk boundaries, formatting delimiters, segment markers — exhibits its own local U-shape governed by the same kernel. Your per-block rendering creates a dead zone *inside each block*, not only across the prompt.

This reframes the mitigation literature: flattening RoPE (YaRN, LongRoPE, ALiBi) treats a symptom of something the positional encoding did not cause. Attention sinks are likewise forced by geometry before the optimiser exploits them.

### What is not solved, and what turns out not to matter

**Position bias applies to distractors too.** Cuconasu et al. (2505.15561) is the key corrective. Rotating a hard distractor through a context produces the same U-shape as rotating a relevant passage: distractors in slots 1 and 10 do 36–44% damage versus 28–34% in the middle. In realistic retrieval, >60% of queries surface at least one hard distractor in the top 10, and stronger retrievers surface *more* harmful distractors. Consequence: MaxRelevance and MinDistraction reordering strategies are statistically indistinguishable from random shuffle across Llama 3.2/3.1/3.3 and Qwen 2.5, at k=5 and k=10, across four retrieval pipelines. Placing good material in privileged slots also places bad material there.

**Model-specific severity.** Qwen 2.5 7B shows the most pronounced positional bias; the Llama 3 family is markedly flatter, plausibly because mid-context robustness became an explicit training target. Models with high closed-book accuracy lean on parametric knowledge when evidence lands in a non-preferred slot, which suppresses measured position effects for the wrong reason.

### Across architectures

**Hybrids (SWA + full attention, Mamba-2/GDN/Lightning + full attention).** Qiao et al. (2606.15378) settle the division of labour: long-range retrieval is carried almost entirely by full-attention layers. Restricting efficient attention to ~2048 tokens at inference barely moves LongPPL; restricting full attention raises it sharply — even for recurrent mixers with in-principle unbounded receptive fields, which store little long-range information in their recurrent states. Layer-wise probing on needle tasks shows accuracy gains concentrated exclusively at middle full-attention layers. Efficient attention acts as an *optimisation prior*: large SWA windows delay retrieval-head formation ("Large-Window Laziness"), so differently-configured hybrids converge to similar long-context performance given enough training but differ sharply under limited budgets.

For an operator with no access to internals, the practical translation is: **a hybrid model's long-context behaviour should resemble a full-attention model's of the same maturity.** Where it doesn't, suspect training budget rather than architecture.

**MLA.** One small-scale mechanistic study (2607.23054, single 114M model, single seed, no matched baseline — treat as hypothesis-generating) finds the KV bottleneck learns a content-only representation: entity identity preserved at ~98%, position near chance, with position flowing through the separate RoPE path. Induction heads co-located at a single layer rather than distributed. If this holds at scale it would predict MLA models handle content-similarity retrieval and positional retrieval through more separable pathways than MHA/GQA — but nothing at production scale confirms it.

**GQA** shows no positional behaviour distinct from MHA in anything I found. It is a KV-cache optimisation, not a change to the routing topology that produces the U-shape.

### The failure mode that actually appears at length

Two independent results say the degradation is not what benchmarks look for.

Eliav (2607.19257): across 5,760 absent-fact probes spanning Claude Sonnet 5, Claude Haiku 4.5, Gemini Flash, and two Qwen sizes over a 2k–512k ladder, fabrication occurred **zero times** and sycophancy stayed ≤8.3%. What rises near each model's effective ceiling is outright refusal — from 0% to 79–90%. Spread tracks proximity to a model's *own* ceiling, not absolute token count.

Xia et al. (2606.29718): in long-horizon agentic search, the dominant failure is **premature termination** — giving up or submitting a low-confidence wrong answer while most of the window remains. Controlling for query difficulty by rank-matching trajectory lengths, premature-termination rate rises monotonically with context length across GLM-4.7, GLM-5.0, Qwen3.5-397B, and MiniMax-M2.5.

For a criticism harness, the analogue is a round that concludes "no further refutation available" not because none exists but because the context got long.

---

## 2. Layout

### Demonstrations and instructions: early beats late, and the gap is large

Cobbina & Zhou (2507.22887) hold demo content fixed and move the block between four canonical slots: start of system prompt (ssp), end of system prompt (esp), start of user message (sum), end of user message (eum). Across ten models in four families:

- On MMLU averaged over all models: ssp 0.689, esp 0.695, sum 0.687, **eum 0.452**. Pairwise Wilcoxon puts eum significantly below all three (p ≈ 0.02–0.04, FDR-corrected); differences among the other three are trivial (|Δ| < 0.03, p > 0.4).
- eum flips >30% of QA predictions without improving correctness. On generative tasks, prediction-change rates approach 100%.
- Sensitivity shrinks with scale but does not vanish, and the *winner* moves: Qwen 1.5B prefers ssp/esp, Llama-3 70B prefers sum. On GSM8K, Llama-3 70B actually improves at eum (21.5% → 88% improved-prediction rate) — the opposite direction from every small model.

**The robust part is the negative:** put nothing load-bearing after the question. The positive ranking among the three pre-question slots is model-specific.

### Instruction count is a harder constraint than format

Eliav (2607.19257), 960 calls/model:

- Perfect-response rate hits **zero at N=80 for every model, every format, both placements**. Steep decline already by N=40. This is a floor, not an asymptote. Past ~40 simultaneous constraints, reformatting is futile; split across turns, tools, or a validation pass.
- **No format wins.** Markdown-minus-plain deltas are ≤2.1pp and unsigned across N for four of five models; the one clean signal (Qwen 35B) favours *plain text*. At 128k, one model collapsed to 38.3% recall specifically under plain text while the other three formats sat at 82–87%.
- **Placement of an identical instruction block between system prompt and user turn moved adherence by up to 8.7pp — larger than the format effect for four of five models — with model-specific sign.** User-turn helped two, hurt two, no effect on one.

### Ordering effects on reasoning quality specifically

Thinner than the retrieval literature. The strongest direct evidence is 2507.22887's reasoning subset: GSM8K prediction-change rates exceed 90% across nearly all models and positions, with non-monotonic improvement — arithmetic reasoning appears to require inductive biases that don't scale uniformly. That is evidence that *reasoning is at least as position-sensitive as retrieval*, but not evidence about which order is better.

---

## 3. Self-conditioning across rounds

### Re-reading its own text pulls generation toward the model's prior, not toward the target

Tao et al. (2607.28908) is the cleanest result. A two-pass protocol run identically on humans and five LLMs (Llama-3.1-405B, Claude-3.5-Sonnet, Mistral-Large, GPT-4o, DeepSeek-R1; GPT-5 series in appendix):

- Human revision yields positive information gain on both objective and subjective tasks (+17.8%, +6.0%, +4.7%).
- LLM self-revision yields ΔI ≈ 0 on objective tasks — statistically indistinguishable from independent re-sampling — and **significantly negative** ΔI on subjective tasks (−5.1% to −29.2%). Embedding analysis shows second-pass responses drifting *toward the model's own task prior* (mean cosine drift −0.113 to −0.178); human revisions stay localised (+0.086).
- Cross-agent matrices localise the failure to the revision step, not input quality: LLMs degrade high-quality human first passes.
- **Multi-iteration experiments to 5 passes: incremental information gain collapses to near zero after the first revision step** across self-revision, self-ensemble, and cross-model strategies.
- A single bit of oracle feedback ("your answer is wrong") changes behaviour where self-conditioning cannot — but recovery exceeds a random-reshuffle baseline only for the strongest models. Most of the oracle's benefit is *retention* (97–99.9% preservation of correct answers).

Structural statement: without external information, self-conditioning cannot reduce uncertainty about the target.

### Verbatim vs summarised prior output

Huang et al. (2602.24287, COLM 2026) compare full context against four reductions on real WildChat/ShareLM conversations across Qwen3-4B, DeepSeek-R1-Distill-Llama-8B, GPT-OSS-20B, and GPT-5.2:

- **Replacing each prior assistant turn with a one-sentence summary matches or beats full context** on topicality for 4/4 models and on quality for 3/4, at roughly 8× less context, and cuts median response length ~25%.
- Keeping only the last exchange matches full context on topicality for 4/4.
- Dropping assistant turns entirely (user turns only) costs modestly; dropping everything is clearly bad.
- Mechanism named **context pollution**, with a taxonomy: intent override (most common), code carryover, factual hallucination carryover, reasoning-trace carryover, formula carryover. They control for generic length effects by substituting length-matched filler.
- The stated cause of the summary advantage: verbose half-baked prior thoughts cause the model to rehash rather than address the current prompt.

### Diversity collapse in closed loops

Kong et al. (2605.17193), seven model families, runs to 1,000 rounds, 45 conditions:

- **Lexical–semantic dissociation.** Cumulative vocabulary grows monotonically while semantic distribution contracts toward narrow attractors. Late-window similarity to the initial window: 0.753 (SD 0.038). Human Reddit baseline: 0.288.
- **Twelve intervention classes all failed** after Bonferroni correction across 62 baseline comparisons: temperature (0.5–2.0), output budget, diversity-oriented retrieval packing, six prompt formulations, mixed-model composition, uncensored (unaligned) variants, sycophancy activation steering, GRPO trained for diversity, N=10 agents, AutoGen/AgentSociety scaffolds, periodic stochastic perturbation. Raising temperature increased lexical diversity while semantic diversity fell.
- **Mechanism:** recursive self-conditioning progressively suppresses low-probability outputs, with increasing recruitment of induction-like heads that retrieve and promote historically dominant sequences (761 events, mean logit margin 3.92; target is top-1 in 61.1%). The authors frame induction heads as depth-reduction circuits: constant-time retrieval substituting for extended computation.
- Sycophancy and alignment were ruled out as causes.

Ko & Geiping (2606.30571) add a finding that should worry any criticism harness directly. Over 20-turn debates across seven models, tracking discourse traits early vs late: **rationality drops sharply in every model** (Δ −0.44 to −0.77), and so do counter-evidence (−0.10 to −0.19), rebuttal (−0.10 to −0.24), and reframing (−0.05 to −0.16). Meanwhile meta-commentary, phatic bridging, agreement (+0.11 to +0.70), elaboration, and gratitude all rise. Argumentative content decays into social content over turns. Attractors are model-specific and influence between paired models is asymmetric — some models are strongly attracting, others malleable.

Geng et al. (2603.11228) confirm the decoding dependency in memoryless chains: greedy decoding enters fixed points or 2-cycles within a handful of steps; sampling prolongs transients. Alternating prompt templates across iterations increases distinct outputs but does not eliminate exact recurrence. Decoding regime dominated prompt variation.

---

## 4. Compression vs verbatim

| Strategy | Finding | Source |
|---|---|---|
| Full transcript | Baseline; often excessive. Hits context limits, accumulates pollution, raises premature termination | 2602.24287, 2606.29718 |
| One-sentence summaries of own turns | Matches or beats full context at ~8× fewer tokens | 2602.24287 |
| Last exchange only | Matches full context on topicality for 4/4 models | 2602.24287 |
| Fixed-threshold compaction | Works, but is really test-time scaling: lower thresholds → lower premature termination, more tool calls, higher accuracy | 2606.29718 |
| Trimming (discard old tool output) | Cheaper than compaction, worse at reducing premature termination | 2606.29718 |
| Isolation / sub-agents | Best for strong agentic backbones (Qwen3.5-397B: 54.0 vs 35.0 ReAct on BrowseComp); *worse* than compaction for weaker ones (GLM-4.7) | 2606.29718 |
| Lossless offload + query (ACM) | Best overall. Compress to summary but keep raw on disk, retrievable by ID. +27% on BrowseComp-Plus, −20% peak tokens. Gains concentrate in **pass^4 (consistency)** more than pass@4 (capability) | 2607.23809 |
| Structured/graph memory | Leads dialogue QA, Pareto-dominated on agentic tasks, 10–100× latency | 2608.15008 |
| Refinement memory (distilled strategies) | Leads embodied planning, trails on QA, scales gracefully | 2608.15008 |

Huang et al. (2608.15008) ran the only controlled substrate comparison — 11 methods, 7 families, 3 backbones, 26 metrics — and the summary is that **no substrate dominates and the winner reverses between regimes**. An attention probe explains why: as retrieval depth grows, attention shifts away from task context toward the retrieved block. That helps QA, where the answer lives in the block, and hurts sequential decision-making, where the policy must attend to the current state. Their design rule: **trade read breadth for write depth** — retrieve fewer entries, invest more in distilling at write time.

**Is aggressive semantic compression of carried-forward reasoning safe?** The direct evidence says yes for *prior conclusions* and no for *material under active examination*. One-sentence summaries preserving the idea while dropping the concrete implementation freed models to build correctly rather than reuse a stale scaffold. But ACM's advantage over lossy summary agents comes precisely from being able to re-read the raw text on demand — and the trajectory analysis shows the model genuinely does re-read.

---

## (a) Placement and selection decision table

Assumes a chat-formatted API, fixed token budget, prompt read top to bottom.

| Material | Where | Form | Evidence | Cite |
|---|---|---|---|---|
| Task frame, epistemic rules, output contract | System prompt, before everything | Verbatim, **≤40 rules** | Strong — hard floor at 80, steep decline from 40, format-invariant | 2607.19257 |
| System vs user placement of the rule block | **Test both** | — | Strong that it matters (≤8.7pp); sign is model-specific | 2607.19257 |
| Externally-sourced evidence (retrieved, tool, witness) | Early, after instructions | Verbatim excerpts | Strong. Only external input escapes the attractor | 2605.17193, 2607.28908 |
| Prior-round conjectures, superseded | Middle or omit | One-line claim summary, no prose | Strong. Summaries ≥ full text on 3–4/4 models | 2602.24287 |
| Prior-round conjectures, live | Late, before the question | Verbatim, few, explicitly labelled live | Moderate. Late slots amplify — reserve for material that should dominate | 2507.22887, 2505.15561 |
| Binding refutations / ledger constraints | Late, adjacent to the question | Verbatim, compact | Moderate-strong by analogy to oracle signal — a small external error signal changes behaviour where self-conditioning cannot | 2607.28908 |
| Full prior reasoning traces | Off-prompt, retrievable by ID | Offloaded | Strong. Lossless offload beat both full context and lossy summary | 2607.23809 |
| Anything after the question | **Nothing** | — | Strong. eum flips >30% of predictions without improving correctness | 2507.22887 |
| Prior-round *criticism* text | Verbatim if it constrains this round; else drop | — | Weak — inferred, not directly tested | — |
| Number of carried items | Fewer, distilled | — | Moderate. Retrieval breadth reallocates attention away from task context | 2608.15008 |
| Block structure | Few large blocks, not many small ones | — | Moderate. The U-shape re-instantiates inside every delimiter-bounded interval | 2603.10123 |

Two cross-cutting rules:

**Selection dominates ordering.** Reordering by positional preference does not beat random shuffle once the context contains a realistic mixture of good and bad material, because privileged slots amplify distractors equally. Spend the effort on what goes in, not where.

**Every round needs something the loop did not produce.** This is the one lever with strong evidence behind it, and it is the one thing twelve failed interventions had in common: they were all inside the loop.

---

## (b) Architecture-sensitive — needs local re-testing per model

Re-test these when switching models. None transfer.

1. **Which pre-question slot is best (ssp / esp / sum).** Winner moves with scale and task; Llama-3 70B inverts the small-model preference, and on GSM8K it inverts completely.
2. **System-prompt vs user-turn placement of the instruction block.** Sign is model-specific; magnitude rivals format.
3. **Rendering format.** No universal winner; one model lost 44pp of recall to a single format at 128k while others were unaffected. Also check token overhead: markdown +26%, prose +22%, table +37% over plain.
4. **Effective context ceiling.** Degradation tracks proximity to the model's *own* ceiling, not absolute tokens. Advertised windows are not usable windows.
5. **Best context-management strategy.** Isolation/sub-agents beat compaction for strong agentic backbones and lost to it for weaker ones, on the same benchmarks.
6. **Best memory substrate.** Reversed between regimes and between backbones in the only controlled comparison.
7. **Retrieval depth (how many ledger items to show).** More helps retrieval-shaped rounds, hurts decision-shaped rounds, via measurable attention reallocation.
8. **Severity of the U-shape.** Qwen 2.5 7B strongly biased, Llama 3 family much flatter.
9. **Whether the model will self-manage context if given tools.** GPT-5.5 made near-zero context-management calls when offered them; a post-trained 9B made 6.8 per question.

**Robust across models** — safe to fix in the harness:

- Nothing load-bearing after the question.
- Instruction count ceiling around 40; hard floor at 80.
- Verbatim carried-forward reasoning causes rehashing; distilled carries better.
- Self-conditioned revision gains collapse after the first pass.
- Closed loops contract semantically regardless of parametric intervention.
- Long context produces refusal and premature termination, not fabrication.
- Sampling sustains diversity longer than greedy decoding.

---

## (c) Where the literature is thin

**Multi-round self-conditioning with selection as the manipulated variable.** Nobody has run the experiment your harness needs: fix the loop, vary *which* prior-round material is rendered, measure idea quality and diversity over rounds. 2602.24287 varies inclusion in real chat but on response quality, not conjecture novelty. 2605.17193 varies twelve things but not the selection policy. This gap is the centre of your question.

**Ordering effects on idea diversity.** Every placement result measures accuracy, F1, ROUGE, or exact match. None measures whether one arrangement yields *more distinct hypotheses* than another.

**Verbatim-vs-summary as a dose–response over rounds.** 2602.24287 tests one summarisation level (one sentence). No compression ladder, no interaction with round index. Whether compression that is safe at round 3 is safe at round 30 is unmeasured.

**Placement interacting with criticism.** All placement work is single-turn or short multi-turn on cooperative tasks. Whether a refutation placed early binds differently from one placed late is untested.

**Escape mechanisms.** The collapse literature is much stronger on the negative than the positive. It establishes robustly that closed loops contract, and that external input is necessary — but not what kind, how much, or how often. The interventions tested were all parametric or scaffolding-level, not information-injection at controlled rates. Recombination operators over an accumulated record — recombining stored material rather than extending it — were not among the twelve.

**Reasoning-quality position effects.** The GSM8K instability in 2507.22887 is the best direct evidence, and it is a side observation in a study designed around classification.

**Frontier closed models in agentic context studies.** 2606.29718 excluded GPT-5.4 and Claude Opus 4.7 because encrypted reasoning traces made analysis impossible. The premature-termination result is established only on open-weight models.

---

## Sources

| ID | Title |
|---|---|
| 2603.10123 | Lost in the Middle at Birth: An Exact Theory of Transformer Position Bias |
| 2505.15561 | Do RAG Systems Really Suffer From Positional Bias? |
| 2507.22887 | Where to show Demos in Your Prompt: A Positional Bias of In-Context Learning |
| 2607.19257 | Prompt Design at Scale: Format, Instruction Count, and Context Length |
| 2606.15378 | Rethinking the Role of Efficient Attention in Hybrid Architectures |
| 2607.23054 | Through the Bottleneck: How MLA Separates Content from Position |
| 2602.24287 | Do LLMs Benefit From Their Own Words? (COLM 2026) |
| 2607.28908 | Reflection or Re-Generation? Why LLM Revision Fails Where Human Revision Succeeds |
| 2605.17193 | Multi-LLM Systems Exhibit Robust Semantic Collapse |
| 2606.30571 | Attractor States Emerge in Multi-Turn LLM Conversations |
| 2603.11228 | Markovian Generation Chains in Large Language Models |
| 2606.29718 | Diagnosing and Mitigating Context Rot in Long-horizon Search |
| 2607.23809 | ACM: Agentic Context Management for Long Horizon Tasks |
| 2608.15008 | Harness the Memory: A Holistic Evaluation of Memory Substrates |
