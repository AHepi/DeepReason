# External research program — open questions, by the decision each feeds

Authored by the monitor session 2026-08-22, at the operator's request.
These are questions for the operator's external research tool, ordered
by how directly the answer changes a pending design decision. Each
entry names the question as a paste-ready query, the DeepReason
decision it feeds, and what changes under each answer. Answers come
back as research notes (docs/RESEARCH_*.md pattern: verbatim,
provenance-tagged, claims external and unverified).

Standing rule inherited from the first two notes: external findings
are design intelligence, never evidence. Anything load-bearing gets
re-proven by this repo's own instruments or live runs before a gate
depends on it.

---

## Tier 1 — feeds a rung that has not been specced yet

**Q1. Position and ordering effects inside long prompts: where in a
long context do models actually act on critical/corrective content
(start, middle, end), and what is known about "lost in the middle"
for instruction-bearing rather than fact-bearing content?**
Feeds: Rung 6's deterministic pack allocation — WHERE the frame
slice, standing attackers, and active criticism render, not just
whether. If middle-position content is systematically under-weighted,
the allocation puts load-bearing sections at the edges and the map
document records why.

**Q2. Pairwise-comparison bias in LLM judging: position/order bias
magnitude, and the effectiveness of swap-and-aggregate (judge both
orders) versus rubric anchoring versus reference-free scoring.**
Feeds: Rung 7's succession trial, which renders BOTH articulation
digests with the incumbent's frame suppressed. If order bias is large
and swap-aggregation reliably cancels it, the succession pack spec
gains a both-orders requirement; if rubrics dominate, D-6's
"program-first, rubric through the trial guard" posture gets external
support.

**Q3. Sensitivity of grounded/Dung semantics to noisy attack edges:
is there work on how label stability degrades when the attack
relation itself has an error rate (wrong edges added, real edges
missed), and on which graph structures amplify or damp single-edge
errors?**
Feeds: the adjudication robustness picture behind Rungs 7-8. The
harness computes exact labels over an attack graph whose edges
originate from model output; one wrong edge flipping a large
extension is the failure shape. If amplifying structures are
characterizable, the §14 diagnostics (Rung 8) know what to watch.

## Tier 2 — feeds a standing suspicion with money on it

**Q4. When do multi-agent/debate configurations actually beat one
model self-revising at matched token budgets, and when do they merely
redistribute the same errors? Meta-analyses or negative results
preferred.**
Feeds: the solo-run law's empirical side. The operator's ruling is
that solo must never be structurally locked out; this asks whether
ensembles even pay for themselves. A strong "rarely at matched
budget" answer moves ensemble features further down every priority
list.

**Q5. What makes machine-generated criticism load-bearing: is there
evidence on properties of critiques (specificity, actionability,
grounding in the artifact vs generic form) that predict whether the
revised output actually improves?**
Feeds: critic seat prompts and the three-arm ablation protocol
already recorded (RESEARCH_CONVERGENCE_LOOPS note). If measurable
critique properties predict improvement, the criticism policy can
demand them typed, and the vacuous-argument confound gets a
detection handle.

**Q6. Best-answer selection without labels: methods for picking the
best output from a run's history (self-consistency, verifier-free
reranking, embedding-cluster centroids) and how much of the
oracle-vs-online gap they recover.**
Feeds: the results surface. The record keeps every candidate (P8), so
post-hoc selection over the whole run is possible where iterative
loops lose it; the "which round was best" gap from the convergence
note is the sizing. A cheap method that recovers half the gap is a
results-surface feature; nothing here touches evidence.

**Q7. Reasoning-model completion-budget pathologies: documented
behavior of reasoning models burning the entire completion cap on
hidden reasoning (empty visible output), and provider-side or
prompt-side mitigations that actually work.**
Feeds: provider profiles and the ladder's known-facts list. The
glm-5.2 empty-completion seat failure is already typed and ledgered;
this asks whether anyone has a mitigation better than raising
--maximum-completion-tokens.

## Tier 3 — cheap probes, park until a slot is idle

**Q8. Reliability of embedding-distance thresholds for novelty and
near-duplicate detection of ARGUMENTS (not documents): how stable are
cosine thresholds across domains, and is per-corpus calibration
mandatory?**
Feeds: the now-armed neural embedder's dormant thresholds
(NEAR_DUP_EPS etc., all None today). Before any tranche arms them,
this answers whether one calibration generalizes or `deepreason
calibrate` must run per home.

**Q9. Diversity-eliciting generation (verbalized sampling, blind
independent drafting): does asking for a distribution of candidates
raise SEMANTIC diversity or just lexical rephrasing, measured by
metrics like Vendi score?**
Feeds: conjecturer seat prompting, and the diversity signals that
could join the registry by declaration. Complements the
diversity-collapse findings already noted.

**Q10. Empirical work on LLMs extracting argument attack relations:
accuracy of models at deciding "does X attack Y" against
expert-annotated argumentation corpora, and failure taxonomies.**
Feeds: the same robustness picture as Q3 from the other side — the
edge-producing step's error rate, which the harness's criticism
machinery currently takes as given.

---

## How answers land

One research note per answer (docs/RESEARCH_<topic>_<date>.md),
verbatim under a provenance header, with consumption points naming
the rung, law, or parked experiment it feeds — the pattern
established by RESEARCH_JUDGE_BLINDING and RESEARCH_CONVERGENCE_LOOPS.
A finding only becomes load-bearing through this repo's own
instruments: a live run, a committed census, or a gate test minted in
a tranche that cites the note.
