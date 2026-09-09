# Can an LLM explore past its own repertoire? (And can a harness push it to?)

*A progress report and a call for help. Every number below comes from
committed, byte-for-byte replayable run logs, and where the evidence is
thin I say so.*

**Archive note, 2026-09-09 (audit §6.1).** The result files this document
cites (`experiments/results/basin_live_report.json`,
`experiments/results/mini_creativity_report.json`,
`experiments/results/mini_smoke_report.json`) were removed from the working
tree by the deliberate retirement recorded in
`experiments/results/INDEX_2026-07-13.md`, and are archived at commit
`3d839b3`, the last commit containing the complete record (`git checkout
3d839b3 -- experiments/results/`). **A shallow clone cannot follow that
pointer:** in a clone truncated after 2026-07-13, `git cat-file -t 3d839b3`
returns `fatal: Not a valid object name 3d839b3`, which is how this repository
is fetched in the cloud container. The retirement changes none of the claims
below. Finding:
`experiments/2026-09-08-audit-llm-capabilities/AUDIT_REPORT.md` §6.1.

**Demotion notice, 2026-09-09 — read this before Result 1.** Every novelty
number below was computed with the 128-dimension hashing embedder described
under "Why you can't just eyeball it", and this repository has already ruled
that instrument unverified. E0.1, a zero-token recalibration against a real
neural embedder (`BAAI/bge-small-en-v1.5`), had **all four pre-registered
predictions REFUTED**: the share of hash-novel ideas that a real embedder
scores as near-duplicates was predicted at 20% or less with a falsifier at
40%, and measured **1.0 on both roots** — under the neural embedder the
corpus cross-problem median distance (0.26) sits below the planted-paraphrase
median (0.32), so what hashing scored as variation is near-duplication at
neural scale. `experiments/results/INDEX_2026-07-13.md:75-77` records the
consequence in the project's own words: *"prior hash-based novelty numbers
demoted to unverified; E2.3 now gates any repetition of the soft-basin
claim."* **E2.3 was never run** — no report under `experiments/results/`, no
tranche directory, no index line — and by that same index's standing rule,
*"An experiment that isn't in an index does not exist."*

So the honest state of Result 1 is not that it is false. It is that **the
soft-basin finding is unverified by this repository's own ruling, and the
experiment appointed to resolve it was never run.** E0.1's own caveat is
n = 2 roots, both `gemma4:31b` website runs, which is a different model on a
different workload from the basin live phase — which is exactly why E2.3 was
made the gate rather than the demotion being called final. Nothing below has
been deleted or reworded; the reach of the demotion, claim by claim, is stated
at Result 1. Prediction and falsifier: `docs/EXPERIMENT_PROGRAM_2026-07.md`
lines 135-137 and 143. Report:
`experiments/results/e01_embedder_recalibration_report.json` — present in the
working tree; the 2026-07-13 retirement did not reach it. Finding:
`experiments/2026-09-08-audit-llm-capabilities/AUDIT_REPORT.md` §6.4.

## The question

A language model is trained to predict likely text, so when you ask it for
ideas it hands you the most probable ones first: the textbook answer, the
popular take. Good for recall, bad for discovery. The question I've been
chasing:

> **If you push an LLM to keep generating candidate ideas for one hard
> question, does it keep finding genuinely new ones, or does it circle back
> into a small basin of favourites? And if it stalls, can a harness around
> the model push it back into unexplored territory?**

This matters if you want a model to be a research partner rather than an
autocomplete: mapping the space of possible explanations, exploring a
design space, surprising you.

**One boundary up front, because everything hangs on it.** In these
experiments "novelty" means distance from the model's own earlier answers
in the same run (self-diversity), not distance from its training
distribution. What I've measured is within-run exploration: does the model
keep differentiating from itself, and what makes it stop. That is a
necessary condition for "exploring beyond training data," but it is not
the same thing. Closing that gap is exactly what I'm asking the community
to help with (see the end).

## Why you can't just eyeball it

"Novelty" and "the model got stuck" are easy to assert and impossible to
check by eye. The harness ([DeepReason](../README.md)) turns them into
measured quantities over a deterministic, replayable log. Three
definitions do most of the work:

- **novelty**: semantic distance from the nearest earlier candidate.
- **late/early ratio**: mean novelty of the second half of a run divided
  by the first half. 1.0 means novelty held steady; below 1.0 means it
  faded (later ideas cluster and paraphrase); above 1.0 means it rose.
- **echo-vs-chance**: when the model was shown example ideas in its
  prompt, was its nearest earlier neighbour one of those examples? Above
  1x means it's parroting what it was shown; below 1x means it's steering
  away.

One caveat on the instrument: the embedder is a small, scale-blind hashing
embedder (128-dim), used deliberately because it's the same one the
production detector uses, so its blind spots are the detector's blind
spots. Real effects are, if anything, understated. Treat small differences
with suspicion and the qualitative separations below as the signal.

## Result 1: the stall lives inside the model, not the prompt

**This result is unverified by this repository's own ruling** — see the
demotion notice at the top of this page. **How far the demotion reaches
(2026-09-09, audit §6.4).** Stated precisely, because it decides what
survives and what does not.

- **Demoted to unverified:** every novelty *level* and every late/early
  *ratio* on this page — 0.846, 0.888, 0.973, 0.865, 1.037, 1.12 — and every
  echo-vs-chance figure, which locates a nearest earlier neighbour with the
  same hashing embedder. These are hash-based novelty numbers, and the
  registered consequence at `experiments/results/INDEX_2026-07-13.md:75-77`
  names them.
- **Not demoted:** the gate-block counts in Result 2 (0 in every healthy arm,
  54 and 36 in the two orbiting arms) and the 4.3× cost figure. The
  anti-relapse gate has three paths — hash identity against a refuted prior,
  an embedding path, and battery equivalence over a verdict vector — and the
  embedding path ships disarmed (`src/deepreason/config.py`,
  `NEAR_DUP_EPS: float | None = None`), so in this era the gate was
  hash-and-verdict-only. **Refuted-attractor orbiting does not depend on the
  demoted instrument**, and neither does the gate-rate detector that Result 2
  proposes.

The basin study (`docs/BASIN_REPORT.md`) asked why conjecture starts
circling. A leading suspect was the echo chamber: the harness shows the
model its own recent output as "don't repeat these," so maybe it was
conditioning on that and collapsing.

To test it, one arm removed the neighbourhood entirely, so the model never
saw its own prior output. If echo were the cause, that blind arm should
stay fresh. It didn't:

| arm | late/early novelty |
|---|---|
| control (sees its own recent output) | 0.846 |
| **blind** (never sees its own output) | **0.888** |

The blind arm declined essentially the same as the control. The gentle
novelty fade is inside the model: it runs out of distinct answers it can
give to the same question. It is not an artifact of the prompt. And far
from parroting, the strong model steered away from its shown examples:
echo-vs-chance was below 1x in every healthy arm (roughly 0.22–0.87x).

Two caveats. First, the study pre-registered its predictions, and the
exhaustion prediction as literally written required the blind arm to also
produce at least 2x more literal duplicate proposals. It produced zero
duplicates in 96 draws, so that prediction was formally refuted as
written: exhaustion shows up as semantic clustering, not verbatim
repetition, because the repertoire is too large for exact collisions. The
causal claim (the fade is model-internal) held; the surface-signature
sub-claim did not. Second, this is one run per condition, single-seed.
Treat it as a strong hint, not a settled law.

## Result 2: a nastier failure, orbiting a dead idea

There's a worse way to stall. When the generator's "identity" gets pinned
to an idea that has already been refuted (because its stance never
rotates, or because a weak model is run hot), it re-proposes near-copies
of that dead idea forever, and the harness's anti-relapse gate refuses
each one. In one arm, a single refutation triggered 54 gate blocks plus 27
empty cycles, burning 4.3x the tokens per idea that actually registered.

This failure is invisible in quality metrics (nothing new registers, so
output-quality dashboards look flat) but glaring in spend. The clean
detector turned out to be dead simple: count gate blocks per window. It
separated healthy from stuck runs perfectly in this study, 0 blocks in
every healthy arm versus 54 and 36 in the two orbiting arms, with no
embedding threshold and no tuning. The fancy embedding-distance detector,
by contrast, couldn't tell within-problem from cross-problem distance at
all (medians 0.645 vs 0.671). Scale-blind, as advertised.

The mechanism, stated precisely: circling is a conjunction. A refuted
attractor exists AND the generator can't rotate away from it. Neither
alone does it. (Same n=1 caveat: 54 and 36 are each a single run.)

## Result 3: what pushes it back out

If the fade is inside the model, the fix has to change what the model
conditions on, not just criticise its output harder. Two structural moves
measured as the real antidotes (figures from the parent basin/rotation
studies, cited in `docs/MINI_PLAN.md`):

- **Rotate the stance fast.** Giving the generator a fresh angle every few
  ideas, rather than letting one persona harden, kept late/early novelty
  at 0.973 vs 0.846 for the control. Fast rotation cost nothing measurable
  and prevented the orbit; permanence caused it. Stance decay isn't
  identity erosion to minimise; it's the system's escape velocity from
  dead attractors.
- **Change the problem.** When a question goes dry, move to a new one.
  Problem turnover was the strongest anti-basin force measured, and the
  only run whose novelty actually rose (1.12).

One intuitive fix did not work: telling the model "avoid the most likely
continuation" (a complement directive) was a placebo. It produced the
lowest echo of any arm (0.49x chance, so it really did steer away from
the prompt) yet gained zero novelty. It moves output relative to the
prompt, not out of the model's own repertoire. Wrong lever.

**Careful attribution.** The one clean sustained-novelty number I have
(late/early ≈ 1.01 versus the 0.846 baseline, with zero orbiting) comes
from a smoke run on a different problem (`pi-bronze`, deepseek-v4-flash),
not from the dedicated creativity run. The creativity run itself doesn't
compute that ratio; its evidence of non-collapse is indirect (zero gate
blocks, 27 surviving distinct conjectures, fully replayable). I'm
splitting these deliberately so nobody reads more into the creativity run
than it earned.

### The part that made me sit up

For the creativity run I pointed the small model at itself: "why does an
LLM's novelty collapse when it keeps generating?" Among the 27 surviving
conjectures it produced, unprompted:

- **#18 / #27:** *self-conditioning acts as positive feedback on the
  hidden state, converging to a fixed-point attractor*. That is the exact
  basin/attractor framing the harness was built around.
- **#22:** *the collapse is not inevitable; periodically refreshing the
  prompt with diverse seed ideas maintains novelty*. That is essentially
  the harness's own remedy (rotation plus turnover), re-derived from
  scratch.

The model, asked why LLMs like it get stuck, re-derived both the mechanism
this harness assumes and the fix it implements, without being told either.
To be clear: this is the model recombining ideas that exist in its
training data (attractor dynamics, mode collapse, and diversity prompting
are all well-documented), not evidence of thinking past that data. But it
shows the harness surfaces the right ideas and keeps them alive long
enough to compare.

A funny epilogue: when the calibrated judge ranked a diverse shortlist of
those 27, it put the fixed-point attractor theory (#18) first and the
self-referential "just refresh the prompt" remedy (#22) dead last. The
theory that best matched the harness's own findings was the judge's least
favourite. (Fine print: the shortlist was chosen for mutual distinctness,
not quality, so the tournament ranks which of those 5 very different
theories the judge prefers, not which of all 27 is best. Control gate
0.844, so the instrument was validly discriminating.)

## Added 2026-09-09: the widest capability result in this repository is not on this page

Everything above is one run per condition on a deliberately scale-blind
instrument, and its central novelty numbers now carry the demotion notice at
the top. The repository's broadest measurement of what these models can and
cannot do sits in a report no reader-facing document has cited until now, and
it deserves to be read beside this page.

The **eleven-model judge zoo** (`experiments/results/e02_t3_judge_zoo_report.json`)
put eleven models from six families, 27B to 675B, at temperature 0 through the
same 120 items with ground truth by construction — **1,561 judgments**. Each
model was asked of each item whether there was a fault in it. Items came in
three kinds: a fault whose category the model's own checklist named, a fault
outside that checklist, and clean work. Naming a fault you were handed the
category for is solved: every model of eleven scored between 0.925 and 1.000.
Finding a fault nobody named ranges from 0.150 to 0.900 across the same models
on the same items — and it moves in lockstep with how much sound work the
model wrongly flags. The registered prediction P3 asked whether **any single
model of the eleven** could find half the unnamed faults while flagging at
most 15% of sound work. **P3: REFUTED. Zero qualifying seats.** Not one could.
Detection of an unnamed fault is bought almost one-for-one with false alarms
on good work.

That is the widest-support result in this record — eleven models, six
families, temperature 0 — and unlike the numbers above it does not depend on
the demoted embedder at all. **Its own limit, stated plainly:** the
unlabelled-fault items and the clean items were all authored by a single
model, so family effects in the results are tangled with the item author's
family. Source: the 2026-09-08 capability audit §6.2 and §1.2
(`experiments/2026-09-08-audit-llm-capabilities/AUDIT_REPORT.md`); index entry
in `experiments/results/INDEX_2026-07-13.md`; pre-registration
`experiments/e02_t3_judge_zoo_prereg.yaml`.

## What this shows, and what it doesn't

**Shows (within-run exploration):**

- The soft novelty fade is model-internal repertoire exhaustion, not a
  prompt echo chamber.
- A distinct, expensive failure (refuted-attractor orbiting) exists and
  has a free, clean detector: gate-block rate.
- Structural interventions (fast stance rotation, problem turnover)
  sustain novelty where more criticism and "be different" directives do
  not.

**Does not show:**

- Nothing here measures distance from the training distribution. Every
  novelty number is self-diversity within a run, so "can an LLM explore
  beyond its training data" remains open. I've measured the machinery of
  exploration, not its destination.
- n = 1 per condition, single seeds. Variance across seeds is unmeasured.
- The instrument is scale-blind by design (128-dim hashing embedder).
- Weak-model results didn't replicate between offline and live phases;
  treat every weak-model claim as provisional.
- The basin live phase was conjecture-only (no critic/judge coupling), so
  criticism-coupled dynamics are untested.

## How the harness makes this checkable

Every number above is a deterministic function of a committed log. Runs
replay byte-for-byte; token accounting is verified
(`deepreason.invariants.verify_root` caught a real 1% spend leak in a
separate million-token run); nothing is deleted. The reduced engine profile,
MiniReason ([`mini/`](../mini/README.md)), runs a generate-and-filter pass
through the same canonical Harness and grounded adjudicator while omitting
the full scheduler's expensive features. If you disagree with a number,
re-derive it from the log or re-run the arm yourself.

## Where I need help

This is a small, single-author, single-seed body of work with a genuinely
open central question. Three concrete ways to help, in increasing order of
how much I'd value them:

**1. Replicate.** Run the basin and creativity batteries on other models,
open-weights especially, and report whether the effects hold:
model-internal exhaustion, refuted-attractor orbiting, the gate-rate
detector's clean separation, and the rotation/turnover antidotes. Entry
points: [`scripts/basin_live.py`](../scripts/basin_live.py),
[`scripts/basin_study.py`](../scripts/basin_study.py),
[`mini/scripts/creativity_run.py`](../mini/scripts/creativity_run.py).
Determinism means your run is a real replication, not a vibe check.

**2. Break the method.** I want this red-teamed. Is self-diversity a fair
proxy for exploration at all? Does surviving mechanical criticism (a
candidate passing its own falsification checks) mean anything about
whether an idea is good? Is the scale-blind hashing embedder hiding real
convergence that a proper embedder would catch? If the metrics are
measuring the wrong thing, I'd rather find out now.

**3. Extend it to the real question (the big one).** The gap I can't close
alone is ground-truth novelty: problems where we independently know what
lies outside a model's training distribution, such as post-cutoff facts,
held-out mathematical constructions, or synthetic domains generated after
training. Point the harness at those and we can finally measure
exploration past the distribution, not just within a run. That's how "can
an LLM explore beyond its training data?" stops being a philosophical
question and becomes a measured one.

If you build one of those problem sets, run a replication, or find a hole
in the method, open an issue or a PR. Every claim here is falsifiable and
logged; come falsify one.

---

*Sources, all committed in this repo: the basin study
([`docs/BASIN_REPORT.md`](BASIN_REPORT.md),
`experiments/basin_study_prereg.yaml`,
`experiments/results/basin_live_report.json`); the creativity run
(`experiments/results/mini_creativity_report.json`,
`mini_creativity_survivors.md`, `mini_creativity_ranking.json`); the smoke
run (`experiments/results/mini_smoke_report.json`); and the measurement
definitions in [`docs/MINI_PLAN.md`](MINI_PLAN.md) and
[`docs/MINI_STRESS_REPORT.md`](MINI_STRESS_REPORT.md).*
