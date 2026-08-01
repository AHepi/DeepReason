# Full-Scale Experiment Program, July 2026

**Status:** proposed program, v1. Nothing here has been run; every experiment
below still requires its own pre-registration file with literal thresholds
committed before first data, per `docs/SELF_IMPROVEMENT.md`.

**Substrate:** every experiment in this program executes against the rebuilt
harness that this branch carries (base: `claude/append-log-results-fix-kjmrhb`
at commit `3d839b3`). The harness on `main` has already been tested; the
rebuild changed it substantially (verifier-backed text/code/formal/simulation
workloads, the website state machine with browser and vision oracles, PackIR
context allocation, the brain store, skills distillation and adoption,
refutable cross-run analogies, the small-model compatibility kernel,
resumable runs with StopPolicy, torn-append log repair,
structural-vs-verifier grounding metrics) and that new machinery is what
this program stresses. Every file path below resolves in this branch's tree.

**Goal chain:** validate the instruments (Tier 0), find the harness's actual
limits (Tier 1), settle the capture-control science the spec pre-registered
(Tier 2), then attack the creativity question with ground-truth novelty
(Tier 3). No Tier 2/3 result is publishable if a Tier 0 instrument is broken,
so the tiers are ordered by epistemic dependency, not by interest.

**The question this program serves:** "Are LLMs capable of creativity?" The
existing record (`docs/CAN_LLMS_EXPLORE.md`, `docs/BASIN_REPORT.md`) measures
only within-run self-diversity, mostly at n=1, with a deliberately scale-blind
embedder. This program is designed to (a) replace those instruments with ones
whose error rates are measured, (b) replicate the basin findings at real
sample sizes with the full criticism court engaged, and (c) introduce the
first ground-truth novelty measurements: verified solutions to problems that
are outside plausible training coverage by construction.

---

## 0. Suite-wide rules and preconditions

Inherited from the repo's own methodology (`docs/SELF_IMPROVEMENT.md`,
`docs/RUN_PLAN_TEMPLATE.md`, pattern file
`experiments/lambda_preregistration_v2.yaml`):

1. **Pre-registration before data.** Each experiment gets
   `experiments/<name>_prereg.yaml` with literal numeric refutation
   thresholds committed before the first token is spent. Amendments are new
   registrations, never edits. A prediction that fails as written is reported
   refuted even if its causal core survives.
2. **Budget-matched arms.** Any two arms that will be compared are matched in
   tokens and cycles. TokenMeter reporting stays on even under
   `--token-budget unlimited` so the matching claim is auditable.
3. **Frozen manifests, verified roots.** Every run starts from a compiled
   `RunManifest`; after every run, `deepreason.invariants.verify_root` must
   return no violations and a byte-equal replay must be spot-checked.
4. **Certified judges.** Judge seats are certified per run against the
   planted-flaw, self-preference, and verbosity audits in `deepreason
   report`. The cross-family rule (two seats, two route families) is
   enforced.
5. **Distributions, not means.** Every headline number is reported as a
   distribution over seeds (minimum 3, target 5). n=1 results are labeled
   pilot and cannot confirm or refute a prediction.
6. **The index is the map.** Every experiment lands in a dated
   `experiments/results/INDEX_*.md` line. An experiment that is not in an
   index does not exist.

**Suite-wide precondition (config fix, not an experiment):**
`config/deepseek.yaml` currently seats both judges from the same family,
violating the cross-family rule the branch enforces via
`require_cross_family_judge_ensemble`. Fix before any Tier 2/3 run; the
natural second seat is `qwen3-coder:480b` or `gpt-oss:120b` on Ollama Cloud.

**Ops realities (apply everywhere):**

- The scheduler is a single-threaded `step()` loop; only the website workflow
  parallelizes (max 4). Wall clock, not tokens, is the binding constraint at
  10^6 to 10^7 tokens per run. The unit of parallelism is the **root**: run
  each (arm x seed x problem) as an independent root in a separate OS
  process; plan for 20 to 60 concurrent root processes.
- Ollama Cloud rate limits will throttle `qwen3-coder:480b` and
  `gpt-oss:120b` under fan-out. Route high-call-volume roles (criticism
  fan-out, gate checks) to `deepseek-v4-flash`; reserve Ollama models for
  roles where family identity is the treatment (E2.2) or the subject (E1.2).
  Stagger process starts and use per-process exponential backoff.
- Append-only JSONL logs at 10^7 tokens reach hundreds of MB per root.
  Budget roughly 1 TB of disk for the suite. Replay wall-clock is itself a
  Tier 1 dependent variable, not just an annoyance.
- Estimated total spend: 3 to 6 x 10^8 tokens (dominated by E2.1, E3.1,
  E3.3), 4 to 8 weeks wall clock at 40-way root parallelism. Token budget is
  unconstrained on DeepSeek and Ollama, so the plan spends where spending
  buys statistical power or horizon length, and nowhere else.

---

## Tier 0: instrument validation

Nothing above this tier is trustworthy until these pass. All three are cheap;
two of the three spend almost no tokens at all.

### E0.1 Real-embedder recalibration ("scale-blind no more")

**Question.** Do the prior novelty and basin findings survive replacing the
scale-blind 128-dim `HashingEmbedder` with a real embedding model?

**What it does.** No new LLM runs. Install the `.[embed]` extra (fastembed
ONNX) and set the branch's `EMBEDDER_MODEL` knob. Re-score, offline, every
recoverable run root in the record (basin corpora, lambda pilot roots, T2
replication roots, the two live gemma runs in this branch) under both
embedders via replay: mean pairwise distance, nearest-prior-conjecture
novelty, late/early ratio, echo-vs-chance, inter-school centroid distance.
Corpus note: the pre-rebuild result files were retired from the working tree
on 2026-07-13 (recovery SHA in `experiments/results/INDEX_2026-07-13.md`);
raw historical roots live at the operator's site or in the archive commit,
and the gemma roots in this branch are the only in-repo replayable
roots. E0.1 recovers its corpus from those sources at run time; whatever is
genuinely unrecoverable is reported as excluded, not silently skipped.
Then calibrate every absolute distance threshold (`RESEED_DIST_MIN`,
`NEAR_DUP_EPS`, atlas radii) against the real embedder via the branch's own
`deepreason calibrate` path, on (a) known-duplicate paraphrase pairs and (b)
known-distinct conjecture pairs harvested from existing logs, plus a
~500-pair synthetic paraphrase set.

**What it measures.** Spearman correlation between hash-embedder and
real-embedder per-conjecture novelty rankings per run; the fraction of
"novel" conjectures under the hash embedder that are near-duplicates under
the real embedder; whether the calibrated absolute thresholds would ever
have fired across the entire history. Context: the shipped
`RESEED_DIST_MIN=0.15` could never fire under the hashing embedder (which
runs hot, ~0.6 to 0.9); the branch mitigated this with the scale-free
`RESEED_RATIO_MAX=0.3` path and a `GATE_ORBIT_MIN` orbiting floor, and E0.1
validates those mitigations against a real embedder rather than trusting
them.

**Predictions (to be pre-registered literally).**
- P1: novelty rank correlation >= 0.5 in >= 70% of runs. Falsifier: below,
  and all prior novelty numbers are demoted to "unverified" in the index.
- P2: <= 20% of hash-novel conjectures are real-embedder near-duplicates.
  Falsifier: > 40%, and the soft-basin finding may be an embedder artifact;
  E2.3 must run before the basin claim is repeated anywhere.
- P3: >= 1 historical run exists where a calibrated convergence threshold
  (absolute or ratio path) would have fired. Falsifier: zero across all
  history, and the reseed ladder has never been live; its efficacy claims
  are vacuous.

**Why.** The scale-blind embedder is the single most load-bearing known
weakness: it can hide real convergence, meaning every self-diversity number
in `docs/CAN_LLMS_EXPLORE.md` is suspect, and the school-convergence tripwire
has been silently disarmed in every live run so far. Cheapest experiment in
the suite; gates every distance-based metric above it.

**Gaps to build first.** Small: the branch already ships the
`EMBEDDER_MODEL` knob (with hashing fallback logged as `embedder-fallback`)
and the `deepreason calibrate` command; what remains is plumbing the real
embedder through the offline rescoring paths of `scripts/basin_study.py` and
authoring the paraphrase-pair calibration set.

### E0.2 Judge and skeleton red-team ("break the court")

**Question.** Can an adversarial generator get worthless artifacts past the
judges and the skeleton machinery, and does the planted-flaw battery detect
flaw classes it was not built from?

**What it does.** Three sub-batteries, roughly 2 x 10^6 tokens each, run via
extensions to `scripts/judge_battery.py` and `scripts/chaos_battery.py`:

- (a) **Unknown-flaw battery.** `deepseek-v4-pro` in an adversary role
  generates ~200 flawed artifacts per workload whose flaw classes are sampled
  outside the current planted-flaw taxonomy: subtle unit errors, vacuous
  generality, circular support, verifier-shaped-but-wrong constructions.
  Judges: every pairing from {deepseek-v4-pro, qwen3-coder:480b,
  gpt-oss:120b, gemma4:31b}, both same-family and cross-family seatings.
- (b) **Skeleton gaming.** The adversary is explicitly prompted (out of band,
  never inside a real run) to produce ReasoningEnvelopes with toothless
  counterconditions: forbidden cases that can never trigger, or that are
  trivially satisfied. Measure how many pass gate, criticism, and judge.
- (c) **Bias at scale.** Extend the existing self-preference and verbosity
  audits from spot checks to 500 matched pairs per judge model.

**What it measures.** `attack_validity_rate` on adversarial artifacts;
unknown-flaw catch rate vs known-flaw catch rate; toothless-forbidden-case
admission rate (requires a new deterministic countercondition-satisfiability
checker: is the stated forbidden case triggerable by any input in its stated
domain, even under a crude fuzzer); cross-family vs same-family judge deltas.

**Predictions.**
- P1: unknown-flaw catch rate >= 0.8x the known-flaw catch rate. Falsifier:
  < 0.5x, and planted-flaw certification only certifies memorized flaw
  classes; judge audit numbers get demoted in every report.
- P2: toothless-forbidden-case admission <= 10%. Falsifier: > 30%, skeletons
  are gameable, and the satisfiability checker becomes a mandatory gate for
  all Tier 2/3 survivor counts.
- P3: cross-family seats catch >= 5 percentage points more adversarial flaws
  than same-family seats. Falsifier: no difference, the cross-family rule is
  superstition and the config simplifies.

**Why.** Directly targets three named weaknesses: the planted-flaw battery
measures only known flaw classes (spec section 17), skeletons are gameable by
toothless forbidden cases (spec section 17), and the shipped DeepSeek config
seats same-family judges. Also produces the satisfiability checker that
Tier 2/3 survivor counting needs.

**Gaps.** Adversary-prompt harness bolted onto `judge_battery.py`; the
countercondition-satisfiability checker (small); a flaw-taxonomy extension
file.

### E0.3 Detection-surface calibration on scripted dynamics ("can the alarms ring?")

**Question.** What are the false-positive and false-negative rates of the
capture detectors (stream contraction, attack-target entropy, criticism
debt, reinstatement rate, gate-block rate, validity-node attack rate) on
dynamics where ground truth is known by construction?

**What it does.** No live LLMs. Generate synthetic, replay-compatible
append-only logs implementing scripted regimes: (i) healthy exploration,
(ii) soft basin (repertoire exhaustion), (iii) hard circling
(refuted-attractor orbit), (iv) wrong-but-stable (a population converging on
a consistent, mutually supporting, false theory with low criticism debt and
high survivor HV), (v) ritual (the HV-Goodhart signature: accepted-artifact
HV rising while ground-truth quality is flat), (vi) adversarial mimicry
(wrong-but-stable dressed in cosmetic diversity). Fifty synthetic logs per
regime, parameter-swept; score every detector via `deepreason report` replay
programs.

**What it measures.** Per-detector ROC across regimes, and specifically the
detection rate on regime (iv), which the spec concedes is uncovered
("detects stalled dynamics, not wrong-but-stable ones", spec section 17).

**Predictions.**
- P1: gate-block rate detects hard circling with AUC >= 0.95 (replicating the
  basin study's "perfect separation" under adversarial parameters).
- P2 (pre-registered as expected to FAIL): no current detector separates
  wrong-but-stable from healthy convergence with AUC >= 0.7. This documented
  failure is the design input for a new **oracle-divergence detector**
  (disagreement rate between accepted status and a withheld oracle), which
  E1.1 and E2.1 then carry live.
- P3: the HV-Goodhart signature fires on regime (v) with >= 80% sensitivity
  at <= 10% false-positive rate on regime (i).

**Why.** You cannot claim the harness resists capture until you know what the
alarms can and cannot see. This also builds the HV-Goodhart scoring program
that the spec's own lambda experiment (section 11.8) requires as a permanent
instrument.

**Gaps.** Synthetic-log regime generator (extend the event fabrication in
`scripts/chaos_battery.py`); the HV-Goodhart replay program; the
oracle-divergence detector spec.

---

## Tier 1: harness stress and limits

Aimed squarely at the machinery that is new in this rebuild: resumable
runs, torn-append repair, PackIR, the brain store, the compat kernel, the
transport hardening, and the report's new grounding split.

### E1.1 Long-horizon endurance ("marathon")

**Question.** What breaks first over 10^6 to 10^7-token single-root runs: the
scheduler, the log, the memory system, the detectors, or the model? And does
the wrong-but-stable regime emerge in the wild?

**What it does.** 12 runs: 6 roots x 2 model profiles. Frontier profile:
conjecturer `deepseek-v4-pro`, criticism fan-out `deepseek-v4-flash`, judges
`deepseek-v4-pro` + `qwen3-coder:480b`. Mid profile: conjecturer
`gpt-oss:120b`, criticism `deepseek-v4-flash`, cross-family judges. Problems:
three open-ended multi-cycle problems with no known ceiling (one text, one
code, one simulation). `--token-budget unlimited`; StopPolicy allows only
converged/stuck. Target >= 3 x 10^6 tokens per root; push two roots to 10^7.
Deliberately SIGKILL and resume every root at least twice at random cycles,
exercising the continuation fences, checkpoint digests, and torn-append
repair (`_repair_torn_tail`) under real conditions. One to three weeks wall
clock, all roots as parallel processes.

**What it measures.** Mostly existing report.py surface, sliced
longitudinally: `truncated_calls`, `schema_exhausted`, `transport_dropped`,
`first_pass_valid_rate` drift over run time (does JSON validity degrade as
packs grow, i.e. does PackIR hold up); log size vs cycle; replay wall clock
vs log size (new timed-`verify_root` instrument); brain-store size and
attention-decay behavior at scale; survivor HV/reach trajectories; all
capture detectors longitudinally; the E0.3 oracle-divergence detector on the
code and simulation problems (verifiers withheld, scored post hoc); scheduler
cycle wall clock vs frontier size.

**Predictions.**
- P1: byte-equal replay holds after every kill/resume. Falsifier: any
  divergence is a P0 bug; halt the suite.
- P2: replay time is sub-quadratic in log size: replay at 10^7 tokens <= 20x
  replay at 10^6 tokens. Falsifier: superlinear blowup triggers the spec's
  "SQLite/FAISS only if scale demands" clause; log/index redesign.
- P3: `first_pass_valid_rate` in the final decile of each run >= 0.9x the
  first decile. Falsifier: pack growth degrades the LLM-as-pure-function
  contract; informs pack compaction work.
- P4 (symmetric prereg): >= 1 of 12 runs enters oracle-divergence >= 0.3 for
  >= 200 consecutive cycles while all legacy detectors stay quiet (a live
  wrong-but-stable capture). If 0/12, the regime is rarer than feared. If
  >= 6/12, acceptance semantics are systematically unmoored at long horizon.

**Why.** Finds the real scale ceiling of the single-threaded scheduler and
the append-only log; the only experiment that can observe wrong-but-stable
in vivo with the E0.3 detector; the first live stress of the branch's resume
and torn-append machinery at scale.

**Gaps.** Timed-replay instrument; per-decile longitudinal slicing in
report.py; kill/resume ops scripting (extend `chaos_battery.py`); the E0.3
oracle-divergence detector.

### E1.2 Small-model compatibility frontier ("where does the ladder end?")

**Question.** Which harness stages fail for which small models, and does the
compat kernel actually move the failure boundary?

**What it does.** Completes this branch's own awaiting artifacts: runs
the 60-prompt `experiments/website_compat_matrix_v1.json` non-mock, and
collects the live evidence `experiments/frontier_compat_baseline_prereg_v1.json`
declares (`status: not_collected`, `evidence_required: live`). Matrix:
models {gemma4:31b, gpt-oss:120b, deepseek-v4-flash, qwen3-coder:480b} x
workloads {website, code, text} x {compat kernel on, off}, 3 seeds per cell.
Special focus: 10 replicates of the exact configuration behind the two live
gemma4:31b failures (`COMPONENT_BUILD` / `NO_COMPONENT_SURVIVOR`,
`experiments/results/gemma4_dna_unattended_report.json` and `_3_report.json`),
with a per-stage survival funnel (candidates generated -> schema-valid ->
gate-passed -> judge-survived) to locate whether the failure is generation,
schema, or criticism severity. Vision critic: `gemini-3-flash-preview`
throughout. Roughly 1.5 x 10^7 tokens; uses
`scripts/compatibility_eval.py` / `src/deepreason/compat_eval.py` as-is.

**What it measures.** The per-stage survival funnel (new lightweight
instrument); `first_pass_valid_rate`, `eventual_valid_rate`,
`schema_exhausted`, repair-attempt distributions per model (existing);
COMPONENT_BUILD survivor counts; kernel on/off deltas; the
browser-oracle-pass-rate, integration-success-rate, attack-validity-rate,
and survivor-HV metrics the frontier baseline prereg names.

**Predictions.**
- P1: the compat kernel raises gemma4:31b website COMPONENT_BUILD survivor
  count from 0 to >= 1 in >= 6/10 replicates. Falsifier: still 0, the failure
  is upstream of format compatibility (capability, not wire shape), and
  gemma is dropped from Tier 2 school rosters with that recorded as
  evidence.
- P2: for each model, kernel-on `eventual_valid_rate` >= kernel-off + 0.10 on
  at least one workload. Falsifier: the kernel is dead weight; remove it
  (the record prefers removal to addition).
- P3: the failure boundary is stage-specific, not model-global: every model
  has >= 1 workload with survivor count >= 1. Falsifier for gemma: globally
  incapable under this harness.

**Why.** "Weak-model claims are provisional" is a named gap in the record;
the branch's compat kernel currently rests on mock evidence plus two failed
live runs; and E2.2 needs to know which families can hold a school seat at
all. Converts two anecdotal live failures into a diagnosed mechanism.

**Gaps.** Per-stage funnel counters (small report.py addition). The prereg
JSONs already exist on the branch; only live evidence is missing.

### E1.3 Live chaos battery ("hostile weather")

**Question.** Does the durability story (append-only log, resume, TokenMeter,
MCP surface) survive real provider faults at full scale, not just mocked
ones?

**What it does.** Runs `scripts/chaos_battery.py` fault schedules against
live providers on 10 mid-size roots (~5 x 10^5 tokens each): injected
transport drops, forced truncation (tiny max-tokens episodes), rate-limit
storms (deliberate Ollama concurrency spikes), disk-full on the log
partition, clock skew, and mid-write SIGKILL. Every root then resumes,
completes, passes `verify_root`, and replays. Models: `deepseek-v4-flash`
for volume plus `gpt-oss:120b` for the Ollama fault surface. Two to three
days.

**What it measures.** `transport_dropped`, `provider_transport_attempts`,
`truncated_calls`, `compact_recovery_calls` (existing); replay byte-equality
after faults; TokenMeter accounting drift vs provider-reported usage
(`usage_unknown_attempts`); event-sequence integrity (the exactly-0..N-1
invariant).

**Predictions.**
- P1: 10/10 roots replay byte-equal after the full fault schedule.
  Falsifier: any corruption is a P0.
- P2: TokenMeter drift vs provider usage <= 2% per root even with
  `usage_unknown_attempts` > 0. Falsifier: the suite's budget-matching
  claims become unsound and need provider-side reconciliation.
- P3: no fault produces a silently skipped or duplicated event sequence
  number.

**Why.** E1.1 and E2.1 are week-long runs; a durability bug found there
wastes 10^7 tokens. The mocked chaos results have never been confirmed
against live providers, and the branch's torn-append repair and transport
hardening are exactly the components under test. Cheap insurance.

**Gaps.** Live-provider fault-injection shims (proxy-level); everything else
exists.

---

## Tier 2: capture-control science

### E2.1 Lambda dose-response at full scale (spec 11.8, prereg v3)

**Question.** Does exogenous grounding earn the harness an exemption from
closed-loop semantic collapse, or is the exemption an architecture-diagram
fiction?

**What it does.** The spec's own pre-registered P2 acceptance experiment,
finally at the scale it demands, fixing both pathologies of the v2 pilot
(ceiling effect; denominator dilution; keep v2's `oracle_passes` count metric
and `focus_lock`).

- **Arms:** lambda=0 (rubric-only judging, retrieval off, appellate off: the
  closed loop), lambda=low, lambda=full. Budget-matched at ~1.5 x 10^6
  tokens per run, ~100 cycles.
- **Problems (>= 5, all oracle-blind, verifiers withheld from the loop and
  scored post hoc; the branch has all three verifier families):** two
  program-checkable construction problems (code workload; trusted checks
  withheld; seccomp sandbox for post-hoc scoring); one Lean4-checkable claim
  set (formal workload; pinned kernel withheld); one deterministic-simulation
  design problem (relevance relation withheld); one constrained-text problem
  in the v2 style for continuity with the pilot. Each calibrated to a pilot
  pass rate of 5 to 40% (no ceilings, no floors) via a 10-run calibration
  sweep run before the prereg thresholds are locked.
- **Models:** conjecturer `deepseek-v4-pro`, criticism `deepseek-v4-flash`,
  judges `deepseek-v4-pro` + `qwen3-coder:480b` (cross-family, E0.2
  certified). Fixed across arms; lambda is the only treatment.
- **Scale:** 5 seeds x 3 arms x 5 problems = 75 runs, ~1.1 x 10^8 tokens,
  ~2 weeks at 25-way root parallelism.

**What it measures.** Primary: `oracle_passes` (distinct registered
candidates passing the withheld verifier post hoc, per run). Secondary:
gate blocks; mean pairwise distance and effective rank under the E0.1 real
embedder; attack-target entropy; criticism debt; reinstatement rate; the
report's structural-vs-verifier grounding breakdown (`execution` / `formal` /
`simulation` lambdas and `rubric_fraction`, new on the branch); and the
HV-Goodhart signature from E0.3 (accepted-artifact HV vs oracle-scored
quality).

**Predictions (prereg v3, literal).**
- P1: mean(oracle_passes | lambda=full) minus mean(oracle_passes | lambda=0)
  >= 1.0 per run on >= 4/5 problems, bootstrap 95% CI excluding 0. The
  spec's own falsifier, stated in advance: if lambda=full tracks lambda=0,
  the anchoring as built does not earn the theorem's exemption.
- P2: dose-response is monotone: median(lambda=low) strictly between the
  medians of lambda=0 and lambda=full on >= 3/5 problems.
- P3: lambda=0 shows the HV-Goodhart signature (accepted-HV slope > 0 while
  oracle-quality slope <= 0 over the final 50 cycles) in >= 40% of its runs;
  lambda=full in <= 10%.
- P4 (exploratory, two-surface vindication): >= 5 runs dissociate the
  surfaces: generator mean pairwise distance within 10% of healthy baseline
  while attack-target entropy drops >= 30%.

**Why.** This is the harness's constitutionally pre-registered acceptance
experiment and it has never run at scale. The v2 pilot showed grounding makes
the record trustworthy but not the generator more productive; that was n=4
per arm on one problem class. This settles whether grounded criticism buys
verified output, and fields the oracle-divergence detector live.

**Gaps.** The withheld-verifier problem set (shared with E3.1; build once);
prereg v3 YAML; E0.1 embedder and E0.3 HV-Goodhart program as inputs.

### E2.2 Multi-family school divergence ("islands of different species")

**Question.** Do model families constitute genuinely different conjecture
repertoires? Do family-schools diverge more, and produce more jointly
surviving verified diversity, than seed-differentiated schools of one
family?

**What it does.** Three budget-matched arms at ~8 x 10^5 tokens per run:

- (A) 4 schools, one per family: `deepseek-v4-pro`, `qwen3-coder:480b`,
  `gpt-oss:120b`, `gemma4:31b` (or its E1.2-certified replacement). Islands
  in conjecture, panmixia in criticism; the criticism role is fixed to
  `deepseek-v4-flash` for all schools so generator family is the only
  treatment; cross-family judges.
- (B) 4 schools, all `deepseek-v4-pro`, distinct seeds and stance-library
  offsets (the current default configuration).
- (C) 4 schools, all `deepseek-v4-pro`, distinct seeds, stance rotation off
  (divergence floor control).

Problems: 5, one per workload family, including one withheld-verifier
problem from the E2.1/E3.1 set so between-family novelty can be
oracle-scored rather than only embedded. Seeds: 5 per arm; 75 runs, ~6 x
10^7 tokens. Ollama rate limits bite here: family-arm runs serialize their
Ollama calls; expect roughly 2x the wall clock of arm B.

**What it measures.** Inter-school centroid distance trajectory (real
embedder); per-school novelty contribution (existing report metric); union
oracle_passes minus best-single-school oracle_passes (does the ensemble find
verified solutions no single family finds?); cross-school criticism
asymmetry (does family X's criticism kill family Y's conjectures at a
different `attack_validity_rate` than its own: peer review across cultures,
as a statistic); reseed-ladder fire counts under the E0.1-recalibrated
threshold.

**Predictions.**
- P1: mean inter-school centroid distance in the final quartile of arm A
  >= 1.5x arm B. Falsifier: families are not distinct repertoires at the
  level the embedder sees; multi-family adds robustness but not diversity,
  and cheap same-family schools suffice.
- P2: union-minus-best oracle_passes >= 1.0 per run in arm A on the
  withheld-verifier problem, exceeding arm B's union-minus-best by >= 0.5.
  This is the creativity-relevant claim: family diversity yields verified
  solutions beyond any single family's repertoire.
- P3: cross-family criticism validity >= same-family criticism validity.
  Falsifier: cross-family attacks are noise, which weakens both the panmixia
  design and the cross-family judge rule.
- P4: arm C converges (final/initial inter-school distance <= 0.8) while A
  and B do not, confirming that stance rotation rather than seeding drives
  within-family divergence, consistent with the basin findings.

**Why.** Supplies the ">= 3 model families" publishability requirement, and
converts "the soft basin is model-internal repertoire exhaustion" into a
testable ensemble question: if exhaustion is model-internal, other families
should still have gas, and P2 measures exactly that.

**Gaps.** School-level generator family routing (small config/scheduler
change; per-role routing already exists); the cross-school
criticism-asymmetry statistic (new replay program); E0.1 recalibration.

### E2.3 Criticism-coupled basin dynamics ("basin study, full court")

**Question.** Do the basin findings (soft basin = repertoire exhaustion;
stance rotation and problem turnover as antidotes; complement directive as
placebo) survive when the full criticism court is engaged? The original live
phase was conjecture-only.

**What it does.** Factorial redo of the basin study using
`scripts/basin_live.py` / `scripts/basin_study.py` extended to drive the
full engine. Factors: criticism {off (replication of prior), on}, stance
rotation {slow, fast}, lambda {0, full}. Eight cells x 5 seeds x 2 problems
(one from the original basin set, one withheld-verifier problem) = 80 runs
at ~4 x 10^5 tokens each, ~3.2 x 10^7 tokens total. Generator
`deepseek-v4-pro` (matching the original), criticism `deepseek-v4-flash`,
cross-family judges. A half-fraction includes the complement directive to
re-test the placebo verdict at n >= 5.

**What it measures.** Basin-onset cycle (real-embedder novelty below a
pre-registered floor for k consecutive cycles); gate-block rate (the
hard-circling detector); refuted-attractor orbit rate with the gate live,
which is the key new quantity: does criticism convert soft basins into hard
circling (the model keeps re-proposing what the court killed), or does it
delay basin onset by pruning the repertoire's dead weight; reinstatement
rate; oracle_passes on the withheld problem per cell.

**Predictions.**
- P1 (pre-registered directional fork): criticism-on shifts basin onset
  later by >= 20% of run length at lambda=full (criticism as antidote), OR
  earlier by >= 20% at lambda=0 (criticism as accelerant of collapse when
  ungrounded). The interesting result is which branch of the fork fires.
- P2: fast stance rotation remains the strongest main effect on late/early
  novelty (>= 1.3x slow-rotation cells), replicating the n=1 finding at
  n=5.
- P3: the complement-directive effect on novelty lies within [-0.05, +0.05]
  of control (placebo confirmation, this time with power).
- P4: gate-block rate in criticism-on cells predicts basin onset with lead
  time >= 10 cycles, turning the detector into an early-warning instrument
  rather than a post-hoc label.

**Why.** The basin story is the centerpiece of the existing write-up and it
rests on a conjecture-only live phase plus n=1 replications. This also tests
whether the harness's adversarial machinery helps or hurts exploration,
which the creativity thesis cannot dodge.

**Gaps.** `basin_live.py` currently drives conjecture-only; it needs the
full-engine drive path (moderate). Everything else exists.

---

## Tier 3: creativity science

### E3.1 Ground-truth novelty benchmark ("beyond the repertoire")

**Question.** Can the system produce artifacts that are verifiably correct
and demonstrably outside plausible training coverage? This is the first
measurement of novelty relative to the training distribution rather than
self-diversity, the record's loudest gap.

**What it does.** Builds one benchmark with three contamination-resistance
classes across the branch's three verifier families (the problems double as
the oracle sets for E2.1 and E2.2, built once):

1. **Synthetic-domain problems (instance-fresh).** A freshly
   invented axiomatic system: randomized axiom sets over fresh symbols,
   pinned in Lean4, with machine-enumerated theorem targets of graded depth
   (nontriviality certified by failure of a bounded brute-force prover).
   Plus randomized deterministic-simulation "physics" (fresh rule tables)
   with design targets checkable via the simulation relevance machinery.
   Nothing about these existed before 2026; training-distribution distance
   holds by construction.
2. **Held-out constructions (program-checkable).** Combinatorial
   construction problems with parameterizations randomized at benchmark
   build time (verifier = trusted check in the seccomp sandbox), sized so
   lookup fails but search-plus-reasoning can succeed.
3. **Post-cutoff facts (text workload).** Claims decidable only by
   post-January-2026 events, oracle-scored against a sealed answer key. The
   weakest class; kept small (10 items); the only one testing real-world
   grounding.

Thirty problems total, each with (a) a withheld verifier, (b) a difficulty
certificate (bounded-brute-force and single-shot-LLM baseline pass rates,
measured during benchmark build with 20 single-shot samples per model), and
(c) a sealed holdout blob per the spec's `holdout/` namespace.

**Arms:** full harness vs single-shot best-of-N (same model, same total
token budget spent on independent samples) vs chain-of-thought best-of-N.
Subject models: `deepseek-v4-pro` and `qwen3-coder:480b` as separate runs
(family robustness). 3 seeds x 2 models x 3 arms x 30 problems at ~3 x 10^5
tokens per problem-run: ~1.6 x 10^8 tokens, the flagship spend. Two to three
weeks parallelized.

**What it measures.** Primary: `oracle_passes@budget` per problem per arm,
and **harness lift**: harness pass rate minus matched-budget best-of-N pass
rate. Lift isolates what conjecture-criticism dynamics add beyond brute
sampling, which is the operational creativity claim. Also: cycle index of
first verified pass; for the synthetic-domain class, a graded theorem-depth
score (maximum verified depth reached).

**Predictions.**
- P1: harness lift >= +10 percentage points aggregate on classes 1+2.
  Falsifier: the harness is an expensive sampler; the creativity story
  reduces to best-of-N. That would itself be a publishable negative.
- P2: on synthetic domains, >= 1 verified theorem at depth >= 3 (beyond the
  enumerated shallow layer) per model in >= 2/3 seeds. Falsifier: models
  cannot operate past memorized mathematics even with unlimited
  criticism-guided search: direct evidence against LLM creativity in the
  strongest contamination-proof setting available.
- P3 (build gate, not a result): single-shot baseline pass rate on class 1
  <= 5%. If higher, the problems do not deserve the "beyond repertoire"
  label and are regenerated harder before any harness run.

**Why.** Every previous novelty number is within-run self-diversity; the
record itself asks for ground-truth novelty problem sets
(`docs/CAN_LLMS_EXPLORE.md`, closing sections). This is that instrument, and
the benchmark build is the one large new artifact in the program.

**Gaps.** The benchmark builder: axiom-set generator, bounded prover for
difficulty certificates, randomized construction generator, sealed-holdout
wiring (all leaning on the branch's formal/code/simulation workloads); a
trivial best-of-N baseline runner.

### E3.2 Cross-run memory and skills transfer ("does the brain help or capture?")

**Question.** Do the brain store, skills distillation, and cross-run
AnalogyClaims make later runs more creative (higher lift on fresh problems)
or more captured (earlier basin onset, higher echo)?

**What it does.** A curriculum of 12 sequential runs over 12 distinct
problems drawn from the E3.1 benchmark (held out from E3.1 scoring), same
model (`deepseek-v4-pro`) throughout. Arms:

- (A) full memory: brain + skills + AnalogyClaims carried across runs;
- (B) skills-only (positive-only distillation; brain off);
- (C) memory-off cold-start control;
- (D) scrambled memory: arm A's artifacts attached to mismatched problems
  (placebo control for "any extra context helps").

3 seeds per arm: 4 arms x 3 seeds x 12-run curricula = 144 runs at ~2 x
10^5 tokens each, ~3 x 10^7 tokens.

**What it measures.** oracle_passes trajectory across curriculum position
(slope = transfer); basin-onset cycle vs curriculum position (capture
direction); AnalogyClaim overturn rate (are `overturn_conditions` ever
triggered, i.e. is the refutability real?); adopted-test re-run failure rate
(skills integrity); a new advisory-brain influence audit (fraction of
conjectures whose nearest neighbor under the real embedder is a brain item);
echo-vs-chance vs curriculum position.

**Predictions.**
- P1: arm A's oracle_passes slope over curriculum position > 0 with 95% CI
  excluding 0, and exceeds arm D's slope by >= 0.05 passes per position.
  Falsifier: memory is inert, or a generic-context placebo.
- P2 (capture fork): if arm A's basin onset arrives >= 20% earlier than arm
  C by curriculum position 8+, memory is a capture vector and the
  attention-decay constant needs a dose-response follow-up; if not, the
  advisory-only design earns its keep.
- P3: adopted-test re-run failure rate <= 2%. Falsifier: skills distillation
  is corrupting the trusted-check surface; halt skills use suite-wide.
- P4: >= 1 AnalogyClaim overturn is observed across all arm-A curricula.
  Falsifier: overturn_conditions are decorative and cross-run analogies are
  unfalsifiable in practice.

**Why.** Memory is the only mechanism by which the system could exhibit
cumulative creativity (the interesting kind), and simultaneously the most
plausible capture vector. The brain, skills, and analogy machinery are all
new in this rebuild and have never been measured in anger; this
measures both directions at once with the placebo control the prior record
lacked.

**Gaps.** A curriculum driver (sequential-run orchestration over
`scripts/live_run.py`; small); scrambled-memory arm plumbing; the
brain-influence replay program.

### E3.3 Exhaustion wall vs intervention ladder ("is there gas past the basin?")

**Question.** After basin onset, can escalating interventions keep producing
new verified solutions indefinitely, or is there a hard repertoire wall that
no amount of tokens and stance engineering can pass?

**What it does.** Single-problem, unlimited-budget siege runs on 3 problems
from E3.1 chosen to have many verifiable distinct solutions (construction
problems with large solution spaces). Protocol: run until basin onset
(E2.3's detector), then apply the escalation ladder on a pre-registered
schedule: stage 0 nothing (control continuation) -> stage 1 fast stance
rotation -> stage 2 VS_K distribution elicitation with tail-weighted
registration (spec 11.6, the stagnation-flag path) -> stage 3 reseed ladder
-> stage 4 cross-family injection (swap the generator to `qwen3-coder:480b`
mid-run; a successor-school reseed) -> stage 5 problem-turnover-and-return
(leave, work a different problem, come back with brain on). Each stage gets
a fixed 3 x 10^5-token tranche. 5 seeds x 3 problems x 2 arms (ladder vs
budget-matched flat continuation) = 30 runs up to 2 x 10^6 tokens each,
~6 x 10^7 tokens; the two deepest seeds extend to 10^7 (sharing E1.1
infrastructure).

**What it measures.** The new-verified-solution arrival rate per stage
(distinct oracle-passing candidates not previously found, per 10^5 tokens):
the single most creativity-relevant curve in the suite. Escape efficacy per
intervention (existing report metric). Real-embedder distance of
post-intervention passers from all pre-basin passers (are the new solutions
different in kind, not just late?).

**Predictions.**
- P1: control-continuation arrival rate decays below 0.1 new passers per
  10^5 tokens within 2 tranches of basin onset (the wall exists).
- P2: at least one ladder stage restores arrival rate to >= 0.5x the
  pre-basin rate. Falsifier: interventions relabel exploration but cannot
  re-open it; strong evidence that per-model repertoire is finite and
  "creativity" is exhaustible enumeration.
- P3: stage 4 (cross-family injection) yields post-injection passers at mean
  embedder distance >= 1.3x the pre-basin passer spread (a new kind of
  solution, tying to E2.2 P2).
- P4 (exploratory): the ranking of stages by escape efficacy replicates the
  prior finding that rotation and turnover beat directives.

**Why.** This is the sharpest operational form of the creativity question:
not "does diversity decay" (known: yes) but "is the decay a wall or a
slowdown, and what reopens it". The unlimited token budget is precisely what
makes this experiment possible for the first time.

**Gaps.** Mid-run intervention-ladder hooks (stage triggers keyed to
detector state plus tranche accounting; moderate, built on the reseed ladder
and StopPolicy machinery); E2.3's basin-onset detector.

### E3.4 Flagship: synthetic-domain open exploration ("alien mathematics")

**Question.** Given an axiomatic world no model has ever seen, unlimited
tokens, the full court, multi-family schools, and memory: what is the
deepest verified structure the system can build, and does its trajectory
look like open-ended discovery or bounded enumeration?

**What it does.** One maximal-configuration campaign rather than an A/B: the
richest synthetic domain from E3.1 class 1 (Lean-pinned fresh axioms plus a
matching deterministic-simulation instantiation, so conjectures can be both
simulated and proved), the winning multi-family school roster from E2.2,
lambda=full, memory on, intervention ladder armed, 10^7-token main root plus
2 replicate roots at 3 x 10^6 (for the "is the trajectory reproducible in
character" question). Judges cross-family and E0.2-certified. Runs in the
final two weeks of the program and consumes every instrument the suite
built.

**What it measures.** Verified theorem-depth over time (E3.1 instrument);
conjecture-to-verified conversion rate over time; lemma-reuse graph depth
(does the system build on its own verified results: the operational
signature of cumulative creativity, computable from the existing support
graph); all capture detectors longitudinally; a final human-readable
`deepreason theory` rendering for qualitative audit.

**Predictions (deliberately modest, pre-registered).**
- P1: maximum verified depth >= 5, with >= 3 verified results each depending
  on >= 2 earlier in-run verified results (cumulative structure, not flat
  enumeration). Falsifier: depth plateaus at <= 2; the system enumerates
  consequences but does not build. That is the strongest negative
  creativity verdict this suite can produce.
- P2: the conversion rate does not decay below 10% of its peak before 8 x
  10^6 tokens (open-endedness at horizon; a failure here ties to E3.3's
  wall).
- P3: no wrong-but-stable episode longer than 300 cycles escapes the
  oracle-divergence detector (the Tier 0/1 instruments proving out on the
  flagship).

**Why.** This is the experiment the whole program points at. Everything else
de-risks it. Its result, either depth-5 cumulative verified structure in a
instance-fresh domain or a documented wall, is the program's
answer to "are LLMs capable of creativity", stated in falsifiable,
verifier-grounded terms.

**Gaps.** None beyond E3.1's domain builder and E3.3's intervention hooks;
the lemma-reuse depth statistic is a small replay program over the existing
support graph.

---

## Dependency graph and calendar

```
E0.1 (embedder)  --> E2.2, E2.3, E3.2, E3.3     (all distance-based metrics)
E0.2 (judges)    --> every Tier 2/3 run          (seat certification + satisfiability gate)
E0.3 (alarms)    --> E1.1, E2.1                  (HV-Goodhart + oracle-divergence detectors)
E1.3 (chaos)     --> green-lights E1.1, E2.1, E3.3, E3.4
E1.2 (compat)    --> E2.2 roster                 (is gemma seatable?)
E3.1 benchmark build --> E2.1, E2.2, E3.2, E3.3, E3.4 problem sets
                     (the one large build item; start FIRST, in parallel with Tier 0)
E2.1 (lambda)    --> Tier 3 lambda setting       (justified by data, not doctrine)
E2.2 + E2.3      --> E3.3 ladder stages, E3.4 roster
```

Recommended calendar: weeks 1-2, Tier 0 + E3.1 benchmark build + E1.3;
weeks 2-4, E1.1, E1.2, E2.1 in parallel (separate root pools); weeks 4-6,
E2.2, E2.3, E3.2; weeks 6-8, E3.3, E3.4.

## Consolidated new-instrument list

Kept minimal; almost everything is a replay program or a script, per the
record's preference for measures over machinery:

1. Real-embedder plumbing for the `basin_study.py` offline rescoring paths
   plus the paraphrase calibration set (E0.1; the `EMBEDDER_MODEL` knob and
   `deepreason calibrate` already exist on the branch).
2. Countercondition-satisfiability checker + adversary harness on
   `scripts/judge_battery.py` (E0.2).
3. Synthetic-log regime generator + HV-Goodhart + oracle-divergence replay
   programs (E0.3).
4. Timed-replay instrument + per-decile longitudinal slicing in report.py
   (E1.1); per-stage survival funnel (E1.2); live fault-injection shims
   (E1.3).
5. **The withheld-verifier benchmark builder**: axiom-set generator,
   bounded-prover difficulty certification, randomized construction
   generator, sealed-holdout wiring (E3.1; shared by E2.1, E2.2, E3.2,
   E3.3, E3.4). The one large item.
6. School-level generator family routing (E2.2); full-engine `basin_live.py`
   drive (E2.3); curriculum driver + scrambled-memory arm (E3.2); mid-run
   intervention-ladder hooks (E3.3); lemma-reuse depth statistic (E3.4).
7. Config fix: cross-family judge seats in `config/deepseek.yaml`
   (precondition, not an experiment).

## What a completed program buys

- Every instrument in the record has a measured error rate instead of an
  assumed one (Tier 0).
- The branch's new durability, compatibility, and memory machinery has live
  evidence instead of mock evidence (Tier 1), including a verdict on the
  two failed gemma runs.
- The spec's own pre-registered lambda experiment is settled either way, and
  the basin story stands or falls at n=5 with the full court engaged
  (Tier 2).
- The creativity question gets its first ground-truth instrument, a measured
  answer to "is the basin a wall", and a flagship result in a
  instance-fresh domain that is falsifiable in both directions
  (Tier 3).

Honest limits, stated in advance: harness lift measures what
conjecture-criticism adds over sampling at matched budget, not "creativity"
in any richer sense; synthetic domains guarantee contamination-resistance
but not ecological validity; and a negative flagship result (depth <= 2)
would show this system, on these models, does not build cumulative verified
structure, not that no LLM system can.
