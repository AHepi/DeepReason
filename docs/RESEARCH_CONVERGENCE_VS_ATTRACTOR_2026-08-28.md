# Distinguishing convergence from attractor basins — external research note

Operator-supplied 2026-08-28 (plugin literature review, alphaXiv-sourced,
retrieved 28 Aug 2026), committed verbatim below the rule. The claims,
numbers, and citations are EXTERNAL and unverified by this repository's
own instruments; nothing here is evidence in the record's sense.
Companion to docs/RESEARCH_CONVERGENCE_LOOPS_2026-08-22.md (earlier,
narrower note on the same territory).

Consumption points:

- **Any future basin/convergence audit of a recorded run:** the
  source's §5 battery (T0 transcript diagnostics → T1 cheap re-runs →
  T2 counterfactual ablation → T3 anchor recovery / out-of-band check)
  is the design input, with its own combining rule and its warning
  that "undetermined" is a legitimate and frequent verdict. Its
  headline constraints are BINDING on any such design: no
  transcript-only classifier is validated, and nothing is
  interpretable without the no-criticism control arm (T7) and the
  stochastic floor (T6).
- **Record-format change (parked prompt candidate):** §7's "cheapest
  high-value change" — log per elimination the specific criticism, its
  named ground, and a hash of the evidence read-set — makes the T0/T4
  diagnostics free forever after. Overlaps the M2 critic-citation
  question in the run-problems audit; sequence AFTER that audit's Q1
  answer.
- **Interpretation discipline for narrowing claims:** presume observed
  narrowing generator-intrinsic until control arms say otherwise; a
  settled endpoint is not evidence criticism worked.

---

# Genuine Convergence vs. Attractor Basin in Iterative LLM Reasoning

*Literature review and operational test battery. Sources: alphaXiv, retrieved 28 Aug 2026.*

---

## Headline

Two findings dominate everything below.

**First: the single most important control is the no-criticism arm.** Almost every naive measure of "narrowing across rounds" conflates three separable causes — generator instability, the mere presence of extra text in context, and actual criticism. Three independent groups built this control and all three found the naive measure badly inflated. Without it, no claim that criticism eliminated a conjecture is interpretable.

**Second: there is no validated transcript-only classifier.** Every method that discriminates reliably requires re-running. The strongest transcript-only signals are *dissociation signatures* (two metrics moving in opposite directions), and these are correlates validated against ground truth in benchmark settings — none has been validated as a decision rule applied to a single held-out run.

---

## 1. Documented attractor phenomena

| Phenomenon | Measurement | Magnitude | Onset | Source |
|---|---|---|---|---|
| Spontaneous instability | Self-reflection flip rate with zero peer input | 37–39% (GPT-4o); range 11.9% (DeepSeek-V4-Flash) to 74% (Qwen-Plus) | Round 1 | 2606.00820 |
| Stance-induced conformity | Flip to a peer answer, conditioned on self-reflection stability | 29–34% across MMLU-Pro, GPQA-D, BBEH, AGIEval; 57–77% correct→wrong | Round 1 | 2606.00820 |
| Form-over-content persuasion | Error adoption among agents resistant to both self-reflection and bare stance, given *logically vacuous* reasoning | 20–39% | Round 1 | 2606.00820 |
| Detect-without-correct | P(miscorrect \| revision fired) | 53–94% across 14 cohorts, 4 model families, 4 benchmarks | Every round | 2605.27559 |
| Semantic collapse | Embedding cosine of late windows to first window | 0.753 (SD 0.038) vs. human Reddit baseline 0.288 (SD 0.129); Vendi effective support declining β = −0.027/100 windows | Early; plateau reached well before round 200 | 2605.17193 |
| Model-specific endpoint basins | Basin separation score S_basin (nearest rival set distance ÷ within-model spread) | > 1 for all 8 models tested; survives role and seed ablation | By turn 20 | 2606.30571 |
| Consistency illusion | Contradiction rate and reasoning similarity both falling | d = −0.08 to −1.32 depending on answer-space width | One debate round | 2606.08457 |
| Consensus destabilisation | Fraction of questions with no majority | 0.4% → 15.2% after one debate round (38×) | Round 1 | 2606.08457 |
| Reasoning collapse | Agents emitting zero extractable reasoning steps post-debate | 5.0% vs. 0.3% under grounded protocol | Round 1 | 2606.08457 |
| Progress mirage | Cycles self-reported as improvements with oracle delta ≤ 0 | 54/54 claimed improvement; 56% had delta ≤ 0 | Cycle 1 onward, compounding | 2607.25152 |
| Saturation | Per-round transition magnitude Δ_t | Exponential-plus-floor, R² = 0.999 | Within ~5 rounds | 2607.14185 |
| Structural coupling | Semantic diversity vs. interaction density | Dense topologies and authority hierarchies accelerate premature convergence | Turns 1–3 | 2604.18005 |

**Onset is the practically important number: most of the effect lands in the first one to three rounds.** Deep loops are not where the attractor forms; they are where it is confirmed.

Two results deserve emphasis because they cut against the intuition that narrowing implies criticism worked.

*Semantic collapse occurs with no criticism at all.* 2605.17193 ran seven model families for 200–1000 rounds across 45 conditions and found lexical diversity growing monotonically while the semantic distribution contracted. Twelve interventions — temperature (0.5 to 2.0), output budget, six prompt formulations, retrieval-augmented memory with a diversity-oriented packing controller, mixed-model composition, uncensored variants lacking safety alignment, sycophancy-targeted activation steering (58% reduction in compliance bias), and GRPO diversity-targeted RL — produced no positive significant effect on semantic diversity after Bonferroni correction, across 62 baseline comparisons. Sycophancy and alignment were ruled out as mechanisms. The mechanism identified was tail-token erosion plus induction-head recruitment: circuits that replace derivation with constant-time retrieval of historically dominant sequences.

*Narrowing is not universal.* 2606.30571's contraction ratios (final-turn topic spread ÷ turn-1 spread) span 0.60 (Gemini Flash) and 0.63 (GPT-4o mini) through 1.49 (Claude Haiku) to 2.59 (Claude Opus). Some models expand. So "did the surviving set narrow?" is partly a question about the generator, not about the criticism.

---

## 2. Dynamical-systems transfer: what actually worked

### Operationalisations that carried empirical weight

**Basin as endpoint equivalence class with a separation score.** S_basin(A) = min over rivals of set-to-set squared distance ÷ within-cluster spread. Values > 1 mean the nearest rival endpoint set is farther than the model's own spread. Held for all 8 models, in both 384-d and 2-d projections, under role and seed ablation (2606.30571).

**Stochastic floor.** The rate at which two *unperturbed* paired runs already land in different terminal clusters. Measured at ~35% in a 30-step append-mode loop (2605.02236). Raw perturbation effects are uninterpretable without it.

**Dose-response and ED50.** ED50_raw ≈ 40 tokens of in-distribution adversarial text (36, 41, 52 under 4PL, GLMM, and family-cluster bootstrap respectively). Raw switching plateaus near 67%, so the maximum *net* effect above the floor is +32pp at dose 400 (2605.02236).

**Persistent escape, split into two endpoints.** Source-basin escape (kicked and outside the original cluster at terminal step) vs. destination-coherent persistence (kicked and still in the specific post-injection cluster). Under a 12k-char tail clip these plateau at ~36% and ~16% respectively and neither crosses 50% at any tested dose. Under full history, source-basin escape crosses 50% near 400 tokens and saturates at 75–80% by 1500 (2605.02236).

**Hidden-anchor recovery with held-out cross-run validation.** The closest thing in the literature to a formal test for "the system settled here because of its own prior." Model deliberation as x_i(k+1) = x_i(k) − α·Σ(x_i − x_j) − β_i·(x_i − b_i), where b_i is a latent per-agent anchor. Fit by least squares; validate by leave-one-seed-out. The procedure nests DeGroot (β=0) and Friedkin–Johnsen (b_i = x_i(0)) and *selects among them*. On Llama-3.1-70B it certified a transferable anchor (held-out R² = 0.44 vs. ≈0.05 for baselines, selected in 8/10 groups); on gpt-oss-20b it correctly rejected the anchor model (held-out R² = −0.94, selected in 2/10) (2606.19494).

**Convex-hull escape as a falsifiable prediction.** All classical linear consensus rules forbid any coordinate leaving conv{x_j(0)}. Observing escape refutes pure consensus dynamics and licenses the anchor model. Escape margin > 0.10 in 77% of Llama runs vs. ~25% for Qwen and gpt-oss (2606.19494).

**Lyapunov drift as a saturation diagnostic.** E[V(x_{t+1}) | x_t] ≤ ρV(x_t) + σ gives E[V(x_t)] ≤ ρ^t V(x_0) + σ/(1−ρ) — an exponential-plus-floor signature confirmed across LLM self-refinement, RL value iteration, and Bayesian optimisation (2607.14185).

**First-divergence time.** Number of generated tokens until two perturbed trajectories first select a different token. Proposed as a robust substitute for the Lyapunov exponent in discrete-output systems (2607.27805).

### Operationalisations that failed or remain metaphor

**Maximal Lyapunov exponent — does not work on symbolic output.** 2607.27805: hidden-state distances saturate almost immediately due to normalisation and dimensionality; observed divergence is jump-like rather than smooth exponential (~90% of trajectory pairs show a latent phase then a discrete jump), so exponential fits attain low R². The authors state plainly that the discreteness of token space prevents a robust global estimate.

**Correlation dimension.** Explicitly interpreted as "an indicator of deterministic structure and effective dimensionality," not as a fractal-dimension estimate.

**Anchor drift within a run.** Refitting on early and late windows to distinguish compliance (stable anchor) from internalisation (moving anchor) *did not generalise* — too few transitions per window, dominated by fit noise. No conclusions drawn (2606.19494 Experiment D).

**Conditional mutual information cannot certify escape.** It measures variation among intervention-conditioned updates, not departure from the no-intervention law. The correct quantity is baseline-relative KL: increasing one-step escape probability by η requires KL(P_z ‖ P_0) ≥ 2η² (2607.14185).

**Hysteresis: nothing found.** No paper operationalises path-dependence in the loading/unloading sense for LLM loops. The nearest results are order-effect sensitivity checks (below), which are not hysteresis.

**Basin size / volume: nothing validated.** ED50 is a barrier-height proxy in injected tokens, and it is explicitly *memory-policy-conditioned* — the same generator gives a different number under a 12k tail clip than under full history.

---

## 3. Perturbation diagnostics: effectiveness, cost, failure modes

### (a) Seed and order perturbation

Effectiveness: establishes the floor, which is a precondition for everything else. Endpoint dispersion across seeds was *small* relative to model identity in 2606.30571 (three seeds returned comparable endpoint basins). Order shuffling in 2606.00820 moved conformity from 29.15% to 27.22% (< 2pp), indicating minimal positional bias in that protocol.

Cost: one extra run per seed unit, plus a second unperturbed control per unit to estimate the floor.

Failure modes: with few seeds the floor estimate is noisy and Wilson intervals are wide. The floor is protocol-specific — 35% for one append loop is not transferable. Temperature raises spontaneous instability (self-flip 39% → 47% from T=0 to T=1.0) without proportionally raising conformity (26–29%), so seed dispersion and influence-susceptibility dissociate and must be measured separately.

### (b) Counterfactual evidence injection

This is the strongest family, but it requires a decomposition that is easy to skip.

**Displacement is not evidence-sensitivity.** 2607.14185 measured escape magnitude E_shift = d(x_condition, x_baseline_continuation) against *useful* escape E_useful = E_shift · max(ΔQ, 0). Targeted feedback: E_shift ≈ 0.54, useful ≈ 0.09. Generic: 0.26, useful ≈ 0. **Mismatched (irrelevant) feedback: E_shift ≈ 0.43 — nearly as large as targeted — with useful escape near zero.** An endpoint that moves under evidence perturbation has not thereby been shown to be evidence-driven.

In the Bayesian-optimisation instantiation, active global-basin escape rates: targeted feedback 0.93–1.00 at one injected observation on 2-D landscapes; generic 0.30 at m=1 rising to 0.70–1.00 at m=16; mismatched ≈ 0–0.33. Alignment shifts the information–escape frontier rather than being strictly necessary.

**The three-condition counterfactual design.** 2606.00820's is the cleanest available: each agent-question pair is observed in parallel under (i) self-reflection only, (ii) peer stances only, (iii) full peer reasoning. This partitions changes into spontaneous, normative-influence, and informational-influence sources, and the partition is exhaustive and mutually exclusive by construction. Cost: 3× the round-1 inference. Roughly 40% of what looked like peer influence turned out to be spontaneous instability.

Failure modes: a state displacement without a verified change in the transition law is not evidence of structural change (2607.14185 Corollary 2). And because vacuous reasoning moves 20–39% of otherwise-resistant agents, an injection that changes the endpoint may have worked through form rather than content — which is why the placebo arm below is not optional.

### (c) Mid-trajectory perturbation

Effectiveness: gives a graded dose response and a barrier estimate. But the strict endpoint is the one that matters and it is much harder to reach than the raw one.

Cost: a dose ladder × paired controls. 2605.02236 used 1,350 trajectories per regime.

Failure modes, in order of how likely they are to bite:

1. **Memory clipping.** Under bounded memory the injection is usually clipped out before terminal measurement, so larger doses do not produce durable escape. Destination-coherent persistence stayed at ~16% across doses 5–400.
2. **Overwrite artifacts.** Replace-mode loops look fragile mostly because the update rule overwrites state, not because the model flipped. The overwrite-vs-insert probe separates these; if the gap dominates, the "fragility" measurement is a statement about the memory policy.
3. **Endpoint-definition sensitivity.** A high-dose non-monotonicity in destination-coherent persistence turned out to be a finite-horizon artifact: roughly half came from comparing a destination cluster sampled while the perturbation was still raw text against a terminal cluster dominated by model-generated continuation. Extending 30 → 79 steps dropped the dip by 73% and the interval straddled zero.
4. **Clustering granularity.** Persistence at the same dose read 16% (k-means k=12), 10% (k=4), 39.5% (HDBSCAN). Pre-register the equivalence rule.

### (d) Other established diagnostics

**No-interaction ablation plus matched-irrelevant-text control.** 2607.01600's CAF = JSD_conditioned / JSD_baseline. GPT-4o: real peer consensus 0.803 [0.740, 0.873], d = 1.30; no-communication ablation 0.978 (n.s.); *equal-length irrelevant Wikipedia text 1.082*. Homogenisation is specifically social, not a generic prompt-length effect. This is the placebo control transposed directly to criticism.

Also from that paper: coupling was **stateless**. Toggling peer information off restored diversity immediately (sawtooth, no cumulative drift across rounds; round 1 JSD 0.096, round 10 0.131). This contradicts the cumulative updating that DeGroot and Friedkin–Johnsen predict, and it is a warning against importing opinion-dynamics intuitions wholesale.

**Out-of-band verification.** 2607.25152 held the agent and tool surface fixed and varied *only* the evaluator's information channel, with a network- and container-isolated world-state oracle plus a per-run boundary proof. The preregistered adversarial hypothesis — that a sufficiently strong in-band judge closes the gap — was **rejected**. The strongest in-band judge, reading full artifact text, the change diff, and its own verdict history, accepted cycles of which 44% were real-world regressions and rejected 38% of real improvements. On a boundary task whose success criterion *is* verifiable from the artifact, the same judge's error went to zero. The variable is where the success signal lives, not judge quality.

---

## 4. Rate signatures available from the transcript alone

### Dissociation signatures (the strongest family)

| Signature | Reads as | Source |
|---|---|---|
| Contradiction rate ↓ **and** reasoning similarity ↓ | Consistency illusion: contradictions smoothed away without shared reasoning replacing them | 2606.08457 |
| Contradiction rate ↓ **and** reasoning similarity ↑ | Genuine alignment | 2606.08457 |
| Lexical diversity ↑ **and** semantic diversity ↓ | Semantic collapse; surface novelty over a contracting manifold | 2605.17193 |
| Revision rate high **and** accuracy flat or falling | Detect-without-correct regime | 2605.27559 |

CARA computes the first pair post-hoc from stored traces with no additional model calls: NLI contradiction hard-filter (DeBERTa-v3) with embedding cosine on non-contradictory step pairs, best-match aligned and symmetrised across the agreement set.

### Selection-independent structural indicators

- **No-majority / undefined rate** across rounds (0.4% → 15.2% in one debate round).
- **Zero-step revisions** — an agent adopting a position while emitting no extractable reasoning. 5.0% of agreement-set memberships under free-form debate, 0.3% under a protocol requiring each claim to name a ground.
- **Δ_t decay curve**, fitted as A·e^(−kt) + c. The residual floor c, not the decay rate, is the diagnostic quantity: it says the loop has reached its stability region.
- **Round of last substantive change** vs. total rounds.

### Predictive signatures

- **Early-window prediction of the late plateau.** Anchored displacement in the early windows predicted late-stage semantic diversity with MAE 0.053 (2605.17193 SI 5.1). If rounds 1–3 already determine the endpoint, rounds 4–N contributed nothing regardless of what the criticism said.
- **Round-0 risk scoring.** Harmful conformity was predictable from round-0 peer-disagreement structure alone at ROC-AUC 0.79, and risk-targeted intervention cut it by 13.6pp (p < 0.001) (2606.00820).

### Engaged-vs-ignored dissent

Measurable, and the measurement has an effect size. The Grounded Debate Protocol requires each reasoning step to pair a CLAIM with a named GROUND and, in debate rounds, an explicit STANCE (AGREE / DISAGREE / EXTEND) toward a *specific* peer claim, with DISAGREE requiring a counter-GROUND. Decomposition: format effect alone d = +0.62; STANCE-mediated debate interaction d = +1.51 — 2.4× larger. Stripping the literal field markers and recomputing attenuated the effect by only 6–10%, so it is not a template artifact. Severe failure modes (complementary reasoning, sycophantic convergence) went from 34/50 and 33/50 to 0/50 on both datasets (2606.08457).

Note the honest caveat the authors flag: contradictory-premise cases *rose* under the grounded protocol (2 → 12 and 1 → 15). Structure surfaces contradictions that vague free text hides. That is the diagnostic working, not failing.

### Verdict on transcript-only classification

**No validated method exists.** Every signature above is a correlate measured against ground truth across benchmark populations; none has been validated as a decision rule on a single held-out run, and several are explicitly agreement-set-selected or dataset-dependent (the consistency illusion ranges d = −0.08 to −1.32 depending only on how wide the answer space is). The strongest reason for pessimism is 2607.25152's rejected hypothesis: an in-band judge with the complete record still misclassified 44% of accepts and 38% of rejects when the success signal lived outside the transcript. Transcript-only classification has a demonstrated ceiling, and it is not a high one.

---

## 5. The battery

Ordered by cost. "Undetermined" is a legitimate verdict and should be reached often.

| # | Test | Cost | Attractor verdict | Convergence verdict | Evidence strength | Source |
|---|---|---|---|---|---|---|
| **T0 — free, from the stored record** |
| 1 | Round of last substantive change ÷ total rounds; fit Δ_t = A·e^(−kt) + c | Zero | Endpoint fixed in rounds 1–3 and c reached early; later rounds are restatement | Substantive movement continues past the round where a specific refutation lands | Strong (R² 0.999 across three system classes); untested as a per-run rule | 2607.14185, 2605.17193 |
| 2 | Dissociation audit: contradiction rate vs. reasoning similarity across rounds | Zero (NLI + embeddings, no LLM calls) | Both fall together | Contradictions fall, similarity rises | Strong population-level (N≈1000 ×2 backbones); not validated per-run | 2606.08457 |
| 3 | Lexical vs. semantic diversity of surviving conjectures across rounds | Zero | Lexical flat or rising while semantic contracts | Both contract, or semantic contracts to a floor above the generator's own | Strong (7 families, 45 conditions, 1000 rounds) | 2605.17193 |
| 4 | Dissent-engagement audit: does each elimination name the specific claim and supply a counter-ground, or restate? | Zero if grounds logged; else one parse pass | Eliminations are restatement, or zero-content revisions appear | Named claim + counter-ground, traceable to a specific criticism | Strong construct validity (d=+1.51 vs. format d=+0.62; 6–10% attenuation when markers stripped) | 2606.08457 |
| 5 | Structural indicators: zero-content revisions, no-majority rate, revision rate vs. quality delta | Zero | Revision rate high with flat quality; zero-content revisions present | Revision rate tracks quality gain | Strong (14 cohorts; P(miscorrect\|revise) 53–94%) | 2605.27559, 2606.08457 |
| **T1 — cheap re-runs** |
| 6 | **Stochastic floor.** Two paired unperturbed re-runs per seed unit; measure terminal-cluster disagreement | 2× base, no new prompts | — (precondition) | — (precondition) | Strong; ~35% floor measured in a 30-step append loop | 2605.02236 |
| 7 | **No-criticism control arm.** Re-run each round with the agent seeing only its own prior conjecture set | 1× base | Same conjectures survive as with criticism | Surviving set differs materially from the control arm | Strong (37–39% flip under self-reflection alone; ~40% of apparent influence reattributed) | 2606.00820, 2607.01600 |
| 8 | **Placebo criticism arm.** Well-formed, matched-length, logically vacuous criticism | 1× base + authoring | Placebo narrows the set as much as real criticism | Real criticism narrows measurably beyond placebo | Strong; two independent instantiations (20–39% adoption of vacuous reasoning; CAF 1.082 for irrelevant text vs. 0.803 real) | 2606.00820, 2607.01600 |
| 9 | **Seed and order shuffle.** Vary seed and the presentation order of evidence and conjectures | k× base | Endpoint dispersion at or below the stochastic floor across all variants — the endpoint is over-determined | Dispersion above floor, and it collapses once the load-bearing evidence is present | Moderate (seed ablation n=3; order effect < 2pp in one protocol) | 2606.30571, 2606.00820 |
| **T2 — moderate** |
| 10 | **Counterfactual evidence ablation.** Remove, weaken, and invert the evidence the ledger records as load-bearing. Score both displacement and quality-aligned displacement | 3–4× base per evidence item | Endpoint invariant to removal *or* inversion; or it moves but with near-zero quality-aligned component (mismatched-feedback signature) | Endpoint moves *and* quality-aligned displacement concentrates in the targeted condition | Strong for the displacement/useful split (E_shift 0.43 mismatched vs. 0.54 targeted; useful ≈0 vs 0.09) | 2607.14185 |
| 11 | **Mid-trajectory dissent injection with a dose ladder.** Report raw switching, net switching (raw − floor), source-basin escape, destination-coherent persistence, and ED50 for each | 5–10× base | ED50_raw not reached in range, or reached but persistence stays near the floor: the loop absorbs and returns | Modest doses produce net switching and *persistent* escape | Strong protocol, well-characterised failure modes; ED50 is memory-policy-conditioned | 2605.02236 |
| 12 | **Overwrite-vs-insert probe.** If the ledger or scratchpad compresses or summarises, re-inject the same content as a non-replacing addition | 1× base | Large overwrite/insert gap: apparent sensitivity is the update rule, not the reasoning | Small gap | Strong | 2605.02236 |
| **T3 — expensive** |
| 13 | **Hidden-anchor recovery.** Fit x(k+1) = x(k) − α·Σ(x_i−x_j) − β_i(x_i−b_i); recover b_i; validate leave-one-seed-out against DeGroot and Friedkin–Johnsen restrictions | Needs ≥3 seeds × ≥5 rounds × several cases; analysis only, no new inference | Anchor model wins held-out **and** the recovered anchor sits far from the initial conjecture set — the endpoint is a latent prior, not the initial evidence | Anchor model loses held-out, or the anchor coincides with the initial position | Moderate: positive result rests on one model family; per-agent CIs contain zero in 46–87% of agent-runs; best held-out R² = 0.44 | 2606.19494 |
| 14 | **Independent witness / out-of-band check.** A verifier with access to the ground-truth signal, not the transcript | Highest; requires an external oracle | Discrepancy between the harness's acceptance and the oracle | Agreement | Strongest available; the only intervention that closed the gap | 2607.25152 |

### Combining verdicts

- **Attractor** if T7 (no-criticism control) or T8 (placebo) reproduces the narrowing, *or* T10 shows the endpoint invariant to evidence inversion, *or* T9 shows endpoint dispersion at the stochastic floor across seeds and orders.
- **Evidence-driven** requires all of: narrowing exceeds both control arms; the endpoint moves under evidence inversion *with* a quality-aligned component; and eliminations name specific claims with counter-grounds (T4).
- **Undetermined** otherwise — and specifically whenever T6 was not run, since without the floor the other numbers have no denominator.

The ordering is deliberate: T7 and T8 are cheap and they are where most claimed convergences will fail. Running T13 before T7 is wasted effort.

---

## 6. Where no validated method exists

**Hysteresis.** Nothing found. No operationalisation of path-dependence in the loading/unloading sense for symbolic LLM loops. Classification here would rest entirely on analogy to physical systems.

**Basin size or volume.** Nothing found. ED50 is a barrier-height proxy measured in injected tokens, and it changes with the memory policy for a fixed generator — it does not characterise a basin.

**Anchor drift within a single run.** Attempted and abandoned; too few transitions per window, fit noise dominates.

**Transcript-only classification of a single run.** No validated rule. The best in-band judge with the complete record had 44% / 38% error rates.

**Open-ended conjecture spaces.** Nearly every conformity, miscorrection, and consistency number above comes from multiple-choice tasks with ground truth. CARA's own limitations note that its agreement-set definition relies on discrete answer matching and would require adaptation for free-form generation. The multi-agent-debate literature's cleanest results are the least transferable to a conjecture-and-criticism harness over open-ended claims.

**Lyapunov spectra on symbolic output.** Actively fails, for the specific reason that token discreteness turns divergence into jumps.

### What rests on analogy to other fields

*Opinion dynamics* (DeGroot, Friedkin–Johnsen, Hegselmann–Krause) supplies the convex-hull bound, and that bound has genuine falsifying power — but the empirical picture is mixed and partly hostile. 2606.19494 found LLM deliberation escaping the hull, which classical consensus forbids. 2607.01600 found coupling to be *stateless* — no cumulative drift across rounds, diversity restored the moment peer text is removed — directly contradicting the cumulative updating those models assume. Importing opinion-dynamics intuition wholesale is likely to mislead.

*Bayesian agent simulations* enter through the escape-condition machinery in 2607.14185, but that paper states plainly that its experiments measure escape outcomes and feedback budgets and **do not** estimate the structural discrepancy δ or the baseline-relative KL. The saturation–escape phenomenology is supported; the numerical information-divergence threshold is not validated.

*Evolutionary dynamics* — no direct transfer found. The nearest thing is the social psychology of group ideation borrowed by 2604.18005: Nominal Group Technique's blind-writing phase and subgroup partitioning as structural interventions against premature convergence, both of which reproduced in LLM populations.

---

## 7. Implications for the harness

**The typicality-bias worry is empirically well-founded.** 2605.17193 shows narrowing occurring with no criticism at all, from recursive self-conditioning alone, resisting twelve interventions including explicit diversity instructions and diversity-targeted RL, with alignment and sycophancy ruled out as mechanisms. Any observed narrowing across rounds should be presumed generator-intrinsic until the control arms say otherwise.

**"Accepted does not mean true" is well-supported by the measurements.** Answer-level consensus can hide mutually exclusive rationales (2606.08457's worked example: three agents agreeing on atropine via three incompatible pharmacological targets). And revision events are 53–94% miscorrections across every cohort tested.

**The entropy-shell result has a formal counterpart.** 2607.14185 Corollary 2: with the governing parameter fixed, repeated internal iteration can move the state within a basin but cannot relocate the attractor that defines it. Relocation requires a parameter update producing a reproducible kernel discrepancy on pre-specified probes. This is the same claim as the expansion-only-by-construction result, arrived at independently, and it carries the same architectural implication: adding rounds is not the lever.

**A structural prediction worth pre-registering.** 2605.27559: adding agents, rounds, or self-correction passes without changing P(miscorrect | revision fires) cannot improve expected accuracy when detection is non-trivial — each addition recruits items into a regime whose expected outcome is wrong. This is directly testable in a matched-budget arm.

**Cheapest high-value change to the record format.** Log, per elimination, (a) the specific criticism that eliminated the conjecture, (b) the named ground supplied for it, and (c) a hash of the evidence read-set at that moment. Items (a) and (b) make T4 free and T8 possible; (c) makes T10 a lookup rather than a reconstruction.
