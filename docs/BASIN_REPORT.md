# When Conjecture Circles: Repertoire Exhaustion and Refuted-Attractor
# Orbiting in a Deterministic Criticism Harness

*Technical report — DeepReason project, 2026-07-06.*
*Status: single-run-per-condition, pre-registered, self-contained.*
*Data: `experiments/basin_study_prereg.yaml`,*
*`experiments/results/basin_offline_report.json`,*
*`experiments/results/basin_live_report.json`, run roots `runs/basin/*`.*

## Abstract

Multi-agent LLM systems that maintain persistent "schools" of conjecture
are expected to diversify exploration; in practice their output can
collapse into a basin — low variation, repeated near-equivalent
proposals. We studied when this happens and why in DeepReason, a
deterministic conjecture–criticism harness whose append-only event log
lets every measurement be replayed. An offline pass over ~1.5M tokens of
committed run logs, followed by seven pre-registered live manipulation
arms (~426k tokens), yields four findings. (1) The *soft* basin —
gradual novelty decline on a fixed problem — is **model-internal
repertoire exhaustion**, not prompt conditioning: generation with the
exemplar section of the prompt removed entirely declines at the same
rate as fully-conditioned generation (late/early novelty 0.888 vs
0.846). (2) Strong models echo their own displayed exemplars *below*
chance (0.22–0.87× across every measured run, offline and live): the
"return diverse candidates" directive is honored, and self-conditioning
is anti-basin for them. (3) *Hard* circling has a different mechanism
entirely: **refuted-attractor orbiting**. After a single mechanical
refutation, a generator whose school identity never fades re-proposed
near-equivalents of the refuted answer 54 times (each refused by the
anti-relapse gate) at 4.3× the token cost per registered conjecture; a
weak model at high temperature showed the same signature. Arms with
zero refutations showed zero gate activity. (4) The system's embedding-
threshold convergence detector is structurally blind (within-problem
and cross-problem distances overlap almost entirely on the hashing
embedder), while **gate-block rate** — already in the log, free, and
scale-independent — separates healthy from orbiting runs perfectly
(0 everywhere healthy; 54 and 36 in the two orbiting arms). Two
pre-registered predictions were refuted, one inverted; we report those
with the same prominence as the confirmations.

## 1. System and question

DeepReason is a deterministic epistemology harness: LLM calls are
bounded pure functions (prompt pack → schema-validated JSON), all state
derives from an append-only event log, and adjudication over an
argumentation graph decides artifact status. Conjecture is organized
into *schools* — persistent conditioning regimes seeded with stances
("demand a causal mechanism", "counterexample first", ...) whose weight
fades as the school's lineage grows (`stance_weight = 1 −
lineage/STANCE_DECAY`, default decay 20). Conjecturer prompts display
up to 8 accepted prior artifacts (the *neighbourhood*), preferring the
school's own lineage. An anti-relapse gate refuses candidates
battery-equivalent to already-refuted artifacts.

The question: **when does conjecture start circling a basin — little
variation, repeated near-equivalents — and which mechanism causes it?**
Candidate mechanisms, each with advocates in the design history:

- **H-echo**: the neighbourhood conditions the generator on its own
  past output; the basin is an echo chamber.
- **H-exhaustion**: the model has finitely many distinct answers to a
  fixed question; the basin is repertoire depletion.
- **H-decay**: when stance weight hits zero, schools lose their only
  differentiator and converge on the model's modal answer.
- **H-filter**: adjudication keeps a narrow subset of a wide pool.
- **H-scale**: no basin at all — the convergence detector's embedding
  scale is miscalibrated, so "convergence" reports are artifacts.

## 2. Instrument

All metrics are deterministic functions of (log, embedder) implemented
in `src/deepreason/views/basin.py`; the embedder is the same
HashingEmbedder(128) the production detector uses, so its scale
problems are the detector's scale problems (this is deliberate).

- **novelty_global**: cosine distance of each new conjecture to the
  nearest prior conjecture in the run. The basin's primary curve.
- **echo vs chance**: was the *single nearest* prior artifact one the
  prompt actually displayed? The logged prompt blobs name their
  exemplars, so this is measurable exactly. Chance baseline = fraction
  of priors displayed at that moment. >1× = echoing the prompt;
  <1× = actively avoiding it.
- **late/early**: mean novelty of the last half of draws over the
  first half. 1.0 = no basin pull; lower = deeper pull.
- **problem age**: prior conjectures on the same problem (the candidate
  clock, vs raw run length).
- **survivorship narrowing**: pairwise diversity of accepted subset ÷
  diversity of everything generated.
- **gate/no-register counts**: literal circling — candidates refused as
  battery-equivalent to refuted artifacts, and cycles registering
  nothing new.
- **scale calibration**: distributions of within-problem vs
  cross-problem pair distances — can this embedder even see topical
  convergence?

## 3. Offline phase (8 committed roots, zero tokens)

| finding | evidence |
|---|---|
| Novelty declines with **problem age**, not run length | needham r = −0.68; the one run with heavy successor-problem turnover (700k criticism run) *recovered*: late/early 1.12 |
| The soft basin is shallow for strong models | late/early 0.85–0.94 across pro-model roots |
| Strong models echo **below chance** | echo/chance 0.22–0.46 across all pro roots — the nearest prior is *rarely* something the prompt displayed |
| A weak model at temp 0.2 parrots | echo/chance 1.12 (raw rate 0.78) on the all-weak chaos root |
| Adjudication is not the funnel | accepted/all diversity 0.82–0.99 — **H-filter ruled out** |
| The embedding detector is blind | within-problem vs cross-problem medians 0.645 vs 0.671 (criticism root) — nearly total overlap; the production `school_convergence` threshold (0.15) can never be reached by real content — **H-scale confirmed** for the detector |

Correlations cannot separate H-echo from H-exhaustion (both predict
declining novelty on a fixed problem), so a manipulation battery was
pre-registered (`experiments/basin_study_prereg.yaml`, committed before
any live token) with numeric pass/fail thresholds per prediction.

## 4. Live battery (7 arms, one variable each)

All arms: conjecture-only (licensed by the survivorship result), fixed
problem (`pi-bronze`), 2 schools, ~60k tokens each, fresh roots,
invariants verified clean after every arm.

| arm | manipulation | conjectures | late/early | echo/chance | gate blocks |
|---|---|---|---|---|---|
| A-control | none (v4-pro, t=1.0) | 60 | 0.846 | 0.73 | 0 |
| B-blind | neighbourhood removed | 96 | 0.888 | n/a | 0 |
| C-decay-off | stance never fades | 14 | n/a (too few) | 0.76 (raw 0.70) | **54** |
| D-decay-fast | stance gone at lineage 5 | 58 | **0.973** | 0.68 | 0 |
| E-complement | "avoid the modal continuation" every cycle | 64 | 0.865 | **0.49** | 0 |
| F-weak-cold | laguna-m.1, t=0.2 | 46 | 1.037 | 0.87 | 0 |
| G-weak-hot | laguna-m.1, t=1.0 | 8 | n/a (too few) | 0.0 | **36** |

### P1 — exhaustion vs conditioning (primary): causal core confirmed

The blind arm, which never sees prior output, declines the same as the
conditioned control (0.888 vs 0.846, within the pre-registered 0.15
band, over *more* draws). **The soft basin is inside the model, not the
prompt.** The prediction's second clause failed as committed: blind
generation was predicted to produce ≥2× duplicate refusals (it cannot
see what it already said) and produced zero in 96 draws — exhaustion
manifests as semantic clustering, never literal repetition; the
repertoire is too large for exact collisions. Formally the conjunction
is REFUTED; the causal claim it was built to test survived, and the
surface-signature sub-claim did not.

### P3 — stance decay: refuted and inverted

Predicted: permanent stances keep schools apart. Measured: fast decay
won on *both* metrics — best inter-school separation (0.690 vs 0.545)
and the flattest novelty of any pro arm (0.973 vs control 0.846).
Meanwhile the permanent-stance arm produced the study's most important
unpredicted finding (§5).

### P4 — complement directive: placebo, with a dissociation

E-complement showed the lowest echo of any arm (0.49× chance — the
directive genuinely pushes output away from the displayed exemplars)
and no novelty gain (0.865 vs 0.846, threshold +0.1). The directive
moves the model *relative to its prompt*, not *out of its own
repertoire*. A remedy aimed at the wrong mechanism does measurable
work and buys nothing.

### P2 — weak-model echo: undecided, and weakened

G-weak-hot registered too few conjectures to score (it was busy
orbiting, §5). F-weak-cold alone failed to replicate the offline
parroting (0.87× chance, late/early 1.04) — the offline S3 signature
came from a different problem with critics present. H-echo-weak is
real somewhere but not robust across problems.

## 5. The unpredicted finding: refuted-attractor orbiting

Hard circling — the behavior the study was commissioned to explain —
appeared in exactly two arms, with one shared signature:

1. An artifact fails (here: mechanical skeleton well-formedness — no
   judges were even present) and is refuted.
2. Successor/discrimination problems spawn around the refutation
   (C: 16 problems; G: 18).
3. The generator, its identity pinned to the refuted answer (permanent
   stance) or too weak/hot to move off it, re-proposes battery-
   equivalent candidates indefinitely. The anti-relapse gate refuses
   each one: C-decay-off drew **54 gate blocks + 27 empty cycles from a
   single refutation**, spending 4.3× the tokens per registered
   conjecture; G-weak-hot: 2 refutations → 36 blocks → 8 registered.
4. Every arm with zero refutations had zero gate activity.

Circling is therefore a *conjunction*: *(a refuted attractor exists)*
AND *(the generator cannot rotate away from it)*. Neither alone
produces it — default-decay strong arms refuted nothing and orbited
nothing; the blind arm couldn't even see its history and still didn't
collide. This reframes stance decay: it is not identity erosion to be
minimized but the system's built-in escape velocity from dead
attractors. It also explains the observed 4.3× cost amplification:
orbiting is invisible in output quality metrics (nothing registers)
but very visible in spend.

## 6. Engineering consequences

1. **Detector**: replace/augment the embedding-threshold
   `school_convergence` flag with **gate-block rate per window**. It is
   already logged, deterministic, free, scale-independent, and
   separated healthy from orbiting arms perfectly in this study. The
   embedding threshold cannot work on the current embedder (§3, F4).
2. **`STANCE_DECAY` should default lower** (faster rotation), not
   higher. Fast rotation cost nothing measurable and prevented the
   orbit; permanence caused it.
3. **Problem turnover is the strongest anti-basin force observed**
   (offline: the only run whose novelty *rose*). Liveness scheduling
   that rotates attention across problems is doing epistemic work,
   not just fairness.
4. **The complement directive should not be relied on** as a
   stagnation remedy at strong-model level; it treats the wrong cause.
5. Weak models at high temperature combine the worst of both failure
   modes (invalid output + orbiting) — temperature is not a diversity
   knob for them.

## 7. Threats to validity

- **One run per condition.** Every live number above is n=1 per arm;
  variance across seeds is unmeasured (the harness is deterministic
  given provider output, but providers are not).
- **Instrument**: HashingEmbedder is nearly scale-blind (that blindness
  is itself finding F4); real effects are likely *understated*, which
  makes confirmations conservative but weakens refutations of small
  predicted effects (stated in the prereg before running).
- **Arms differ in draw count** (blind packs are cheaper → 96 draws vs
  60), partially confounding late/early comparisons; the direction of
  this bias runs *against* the exhaustion confirmation (more draws ⇒
  more decline), so P1's core survives it.
- **Two model families, one problem** for the live phase; the
  weak-model results already failed to replicate across problems
  offline→live, so treat every weak-model claim as provisional.
- Conjecture-only arms exclude critic/judge feedback loops; licensed by
  the survivorship null, but criticism-coupled circling dynamics (e.g.
  attack-target re-litigation) are untested here.

## 8. What a publishable version would need

A real embedding model (and showing the conclusions are
embedder-invariant), ≥3 model families, ≥5 problems, ≥5 seeds per
condition with confidence intervals, and a comparison against published
mode-collapse / self-consumption results (the exhaustion finding is a
single-generation, prompt-level cousin of iterative-retraining
collapse — the relationship is worth making precise). The
refuted-attractor orbiting mechanism and the gate-rate detector are,
to our knowledge, the novel claims worth defending.

## Appendix: companion results from the same session

- The judge-side measurement problem and its fix (criterion-level
  forced choice + degraded-control validity gate):
  `experiments/informal_ab_prereg.yaml`, instrument reports.
- Rank-concentration hypothesis ("criticism improves the max, not the
  mean") pre-registered and REFUTED on two fresh problems:
  `experiments/rank_concentration_prereg.yaml`.
- All raw curves: `runs/basin/*` (replayable); analysis code:
  `src/deepreason/views/basin.py`, `scripts/basin_study.py`,
  `scripts/basin_live.py`.
