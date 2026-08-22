# Convergence, conformity, and basin escape in LLM loops — external research note

Operator-supplied 2026-08-22, committed verbatim below the rule. The
claims and links are EXTERNAL and unverified by this repository's own
instruments; nothing here is evidence in the record's sense. Same
standing as docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md.

CAUTION on the source's own mapping section: its "What this means for
DeepReason" references experiments that are NOT in this repository's
committed record (a "sham-critic ablation", "flash-vs-pro effect
sizes", a "0.600 truncation artifact") — they are another
conversation's referents. The advice survives re-anchoring; the
referents do not. Do not hunt for those artifacts here.

Consumption points:

- **Rung 6 (frame render semantics), binding requirement when its
  prompt is written:** the pack renderer is this harness's memory
  policy. The perturbation result — interventions persist at ~16%
  regardless of strength when history is tail-clipped, and persist
  with dose under full history — means criticism, steering, and
  standing attackers must keep RENDERING within the horizon to keep
  acting, and persistence is measured at the terminal step, never at
  injection. The record forgetting nothing does not make the pack
  remember.
- **Live-experiment discipline, new standing clause:** every
  pre-registered comparative live experiment includes a
  CONTROL-VS-CONTROL arm (same configuration run twice) to measure
  the stochastic floor before any A/B effect is claimed — two
  unperturbed runs diverged ~35% of the time in the cited work, and
  the repo's own ledgered fact that capability-channel use is
  stochastic across identical runs is the same phenomenon.
- **Cheap parked probe:** before any convergence signal is trusted as
  a stop criterion (including grounded-extension stability), a ~40
  item calibration checks whether the signal separates useful
  convergence from mere settling, per domain (the SPRT/KL probe). A
  negative answer is a result, not a failure.
- **Judge-evidence protocol, if that tranche ever runs again:** the
  three-arm counterfactual (self-revision / stance-only verdicts /
  full reasoning) distinguishes whether criticism CONTENT is
  load-bearing or argument-shaped text alone does the work. The
  cited finding that vacuous reasoning moved 20-39% of resistant
  agents is external support for two standing laws at once: judges
  suspect-by-default, and model prose is never evidence. The same
  paper's deployment sting — intervention without correctness labels
  gained nothing — warns against any conformity-suppressor mechanism
  (A9: diagnostics act only through attention).
- **Diversity metrics (Vendi score, centroid-cosine collapse) join
  through the signal registry, not the calculus:** Rung 8's §14
  formulas are THE diagnostic definitions by rider; external metrics
  enter, if wanted, as new DECLARED signals compared against that
  family — the signal contract exists precisely for this.

---

## Operator-supplied text, verbatim

Six papers carry most of the weight here. Summary first, then the
DeepReason mapping.

### 1. Convergence worth terminating on

**The cheap signal works; the expensive one doesn't.** *Semantic
Early-Stopping for Iterative LLM Agent Loops* (arXiv 2606.27009) runs
a Writer→Critic loop and halts when cosine distance between
consecutive draft embeddings stays below ε for k consecutive rounds.
The judge-free variant cut operational tokens 38% at statistically
indistinguishable quality; the quality-gated variant that called a
judge every round cost **+129%** for no benefit. Note the patience
window is load-bearing: distances decrease on average (Wilcoxon
p=1.3e-3) but only ~5% of trajectories are strictly monotone.

The paper's real finding is the one you'd care about: an oracle that
picks the best round beats every online policy by +0.115 IS (p≈4e-11).
**"When to stop" is solved; "which round was best" is open.**
Termination detection and answer selection are different problems and
conflating them silently costs you the whole gap.

**Calibrate before you trust the stop signal.** *Sequential Consensus
for Multi-Agent LLM Debates* (2605.19193) wraps Wald's SPRT around a
per-round consensus score with Beta likelihoods fit on ~40 calibration
items. On GSM8K: 3.7× call reduction at −2pp. On MMLU: the calibrated
KL between "useful convergence" and "not yet" collapsed to ≈0, the
test correctly refused to stop, and cost rose 2.1×. That negative
result is the contribution — **the calibrated KL is a pre-deployment
false-green probe on your convergence signal itself.** If KL≈0 for a
domain, your convergence detector is measuring nothing about
correctness there, and you learn this for 40 items instead of a full
run.

### 2. Convergence worth intervention

**The detection method is a counterfactual arm, not a threshold.**
*Not All Flips Are Conformity* (2606.00820) shows raw flip rate
conflates three mechanisms and separates them by running Round 1 under
three parallel conditions — self-reflection (no peer info),
stance-only, full reasoning. Results: ~40% of apparent peer influence
is spontaneous instability masquerading as conformity; strict
conformity is 29% and **63.6% correct-to-wrong**; and in the
information-gradient experiment, *vacuous* reasoning still induced
20-39% error adoption among agents that had resisted both
self-reflection and bare stances. Models treat the structural
appearance of argument as evidence.

Harmful conformity is predictable from round-0 features at AUC 0.79 —
and the dominant features are **peer disagreement structure** (largest
wrong-answer coalition, peer support count, answer entropy).
Self-reported confidence ranked dead last.

The sting: targeted intervention cut harmful conformity 13.6pp in the
diagnostic setting, but in deployment without correctness labels it
gave no accuracy gain, because suppressing peer adoption blocks
beneficial corrections at the same rate.

**For the conjecture arm, use dispersion metrics.** *Diversity
Collapse in Multi-Agent LLM Systems* (2604.18005): Vendi Score (87%
agreement with expert judgment), structural disorder 1−φ (mean cosine
to group centroid — low values mean collapse onto one point), pairwise
cosine dispersion, plus IDF-weighted lexical uniqueness as a sanity
check that semantic spread isn't just rephrasing. Mechanism is
*structural coupling*: dense topologies and authority-weighted roles
accelerate premature convergence independent of model capability.
Nominal Group Technique (blind independent generation before
discussion) and subgroup partitioning both raised diversity at modest
quality cost.

### 3. Jumping the basin

*Perturbation Dose Responses in Recursive LLM Loops* (2605.02236) is
the only paper that actually measures this, and it's deflationary.

- **ED50 for raw switching ≈ 40 tokens** in append mode — but two
  *unperturbed* runs already diverge ~35% of the time. Raw switching
  plateaus at 67%, so max net effect is +32pp. Report the stochastic
  floor or you'll report noise as escape.
- **Memory policy dominates the model.** Under a 12k-char tail clip,
  persistent escape plateaus at **16%** regardless of dose 5-400 —
  the perturbation gets clipped out before terminal measurement.
  Under full history: retained source-basin escape crosses 50% near
  400 tokens and saturates 75-80% by 1500; the stricter
  destination-coherent endpoint needs ~1000-2000.
- **Content specificity is real.** In-distribution adversarial
  continuations give a graded dose response; off-topic and lorem stay
  at the noise floor. Counterintuitively, *heterogeneous concatenated*
  perturbations retained escape at 0.74-0.79 vs 0.54-0.58 for
  homogeneous repetition — repeated content gives the model a clean
  signal to recover from.
- **Replace-mode "fragility" is an artifact.** Injected text literally
  becomes the next state, so switching is tautological. An insert-mode
  probe (perturbation visible for one generation, not written to
  state) drops it to 12-32%.

Cheaper structural levers, if a 1500-token kick is too expensive:
Verbalized Sampling (2510.01171) — ask for a distribution of
candidates with probabilities rather than one answer — and the NGT
blind-writing phase from 2604.18005.

### What this means for DeepReason

1. **Your sham-critic ablation should become a three-arm
   counterfactual, not two.** 2606.00820's decomposition is exactly
   your discriminating experiment, done rigorously: a self-revision
   arm with no critic, a stance-only arm (verdicts without reasons),
   and the full arm. Without the middle arm you can't tell whether
   criticism *content* is load-bearing or whether the mere presence of
   argument-shaped text is doing the work. Given that vacuous
   reasoning moved 20-39% of resistant agents, this is not a
   hypothetical confound.

2. **Add a control-vs-control arm to your matched budgets.** A 35%
   stochastic floor would have swallowed your flash-vs-pro effect
   sizes whole. Your 0.600 truncation artifact suggests you already
   know this failure shape.

3. **Grounded-extension stability is a natural stop signal, but
   calibrate its KL first.** Run the 40-item SPRT calibration per
   domain. If extension stability doesn't separate correct from
   incorrect convergence, that's a publishable negative result about
   Dung semantics as a termination criterion — and it costs almost
   nothing to find out.

4. **Argue for intervention on attack-graph structure, not on
   self-reported confidence.** AUC 0.79 from coalition size and
   entropy; confidence ranked last of six features. Your framework
   already computes the structural quantities.

5. **Anti-relapse ledger has a design implication.** If the ledger
   tail-clips, injected criticism gets forgotten before terminal
   measurement and you'll measure 16% persistence regardless of
   intervention strength. Full history within the horizon, measured at
   terminal step, not at injection.
