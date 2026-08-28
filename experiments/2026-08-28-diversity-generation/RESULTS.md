# RESULTS — diversity of conjecture generation

**Dated ledger, 2026-08-28.** Two legs, 216 cells, 2,243,500 tokens, 7,236
provider calls, 12,794 valid candidate conjectures. Every number below is printed
by `render_tables.py` from `metrics.json` / `metrics_leg2.json`, which are
computed from the committed raw responses alone.

Authority: operator 2026-08-28, "Ok. Do it." and "Tokens are cheap. use as
many as you need". Design input: `docs/RESEARCH_TEMPERATURE_VS_VS_2026-08-28.md`
— an external note, never evidence, whose verbalized-sampling rows are graded
**C** (authors' own results, no independent replication) and which names this
as "the experiment nobody has run". Those rows are now replaced by our own
measurement.

---

## 1. The verdicts, as registered

| | claim | leg 1 | **leg 2** |
|---|---|---|---|
| **H1** | B > A on M1 — stratification (note row 5, grade B) | INCONCLUSIVE | **INCONCLUSIVE** |
| **H2** | C > A on M1 — verbalized sampling (note row 7, grade C) | INCONCLUSIVE | **INCONCLUSIVE** |
| **H3** | D ≥ B and D ≥ C on M1 | INCONCLUSIVE | **INCONCLUSIVE** |
| **H4** | C's gain costs nothing in yield (≤ 5pp over A) | SUPPORTED | **SUPPORTED** |

**The two legs' inconclusives mean completely different things, and the
difference is the main thing this experiment learned.** Leg 1's were an
instrument failure: its primary counter saturated and could not have
separated anything. Leg 2's are substantive: the counter works, the arms
separate enormously — and the registered rules required the ordering to hold
on **all three** questions, which is exactly what does not happen.

`instrument_null_result` is **false** in leg 2: the arms are not within the
3-cluster effect floor of each other. The rules were not met because the
effect is **question-dependent**, not because it is absent.

## 2. What actually happened — leg 2, the leg with a working metric

### M1: distinct ideas per 49 candidates, τ₂ = 0.76, complete linkage

Mean over 9 repetitions, (min–max) across them.

| arm | decay | geometry | technique | overall | worst question |
|---|---|---|---|---|---|
| A direct | 8.0 (7–11) | 1.7 (1–3) | 5.6 (4–7) | **5.1** | 1.7 |
| B stratified | 5.7 (5–8) | 6.0 (5–8) | 7.7 (5–11) | **6.4** | 5.7 |
| C verbalized sampling | 27.0 (23–31) | 3.4 (2–6) | 22.3 (20–25) | **17.6** | 3.4 |
| D stratified + VS | 23.7 (19–31) | 12.0 (9–17) | 24.2 (17–30) | **20.0** | **12.0** |

Read the rows, then read the `geometry` column, because they say different
things.

**By row:** verbalized sampling is transformative. On the two open prose
questions C and D return three to four times the distinct ideas that repeated
direct asking does, from the same model, at the same temperature, with
thinking off. The repetition ranges do not overlap between {A, B} and {C, D}
on either prose question — A's best decay repetition (11) is below C's worst
(23).

**By column:** the geometry construction question breaks the pattern
completely. There, C (3.4) is barely above A (1.7) and far below the
3-cluster floor, while the arms that carry a **planning call** — B (6.0) and
D (12.0) — are the only ones that lift it. Whatever verbalized sampling does,
it did not do it on a tightly constrained construction problem; explicit
direction stratification did.

That single column is why H2 is INCONCLUSIVE rather than SUPPORTED, and it is
a more useful result than a sweep would have been.

### M2: mean pairwise distance (threshold-free, so no cut-off can move it)

| arm | decay | geometry | technique | overall |
|---|---|---|---|---|
| A direct | 0.2010 | 0.1073 | 0.1781 | **0.1621** |
| B stratified | 0.2683 | 0.2359 | 0.2865 | **0.2636** |
| C verbalized sampling | 0.3199 | 0.1512 | 0.2993 | **0.2568** |
| D stratified + VS | 0.3390 | 0.2623 | 0.3425 | **0.3146** |

M2 tells the same story from a different direction, including the geometry
exception (C 0.1512 barely above A 0.1073; B and D far above both).

### M3 and cost: the diversity was not bought by breaking anything

| arm | calls | valid candidates | parse fail | empty | off-format | invalid % | tokens | tokens/candidate |
|---|---|---|---|---|---|---|---|---|
| A direct | 1620 | 1614 | 6 | 0 | 0 | 0.37% | 364,687 | 226.0 |
| B stratified | 1647 | 1611 | 9 | 0 | 0 | 0.55% | 437,457 | 271.5 |
| C verbalized sampling | 162 | 1589 | 3 | 1 | 0 | 0.25% | 150,324 | 94.6 |
| D stratified + VS | 189 | 1568 | 5 | 3 | 1 | 0.42% | 172,861 | 110.2 |

**H4 is supported with room to spare, in the wrong direction for the worry:**
C's invalid rate is **0.12 percentage points BELOW** A's, not above it. No arm
exceeded 0.55%. Nothing here was gained by degrading the output contract.

**A cost claim from the external note is refuted by measurement.** Row 7
projected VS at "~1.1× token cost". Measured here, VS is **2.4× CHEAPER per
candidate** than repeated direct asking (94.6 vs 226.0 tokens), because ten
candidates share one prompt and one framing. Per distinct idea the gap is
larger still:

| arm | distinct ideas per 1,000 tokens |
|---|---|
| A direct | 0.38 |
| B stratified | 0.40 |
| C verbalized sampling | **3.16** |
| D stratified + VS | **3.12** |

**About eight times more distinct ideas per token.** This is the single most
actionable number the experiment produced.

### τ sensitivity — the ordering is not an artifact of the cut

| arm | τ=0.72 | τ=0.74 | **τ=0.76** | τ=0.78 | τ=0.80 |
|---|---|---|---|---|---|
| A direct | 3.1 | 3.9 | 5.1 | 6.9 | 8.9 |
| B stratified | 5.2 | 5.7 | 6.4 | 7.4 | 9.0 |
| C verbalized sampling | 13.0 | 15.1 | 17.6 | 21.0 | 24.3 |
| D stratified + VS | 13.0 | 16.7 | 20.0 | 23.8 | 28.1 |

The {A, B} vs {C, D} separation holds at every cut in the registered grid.
The **absolute** counts move a lot with τ, so M1 is a relative instrument;
"20 distinct ideas" is not a claim that twenty ideas exist.

## 3. Leg 1, and the instrument failure it recorded

Leg 1 ran exactly as registered: 108 cells, 1,118,171 tokens, no cell
truncated, no planning call failed. Its M1 nevertheless reported **≈1 cluster
for nearly every cell of every arm** at the frozen τ\* = 0.7454.

The first diagnosis was wrong, and the correction is recorded rather than
quietly applied. The obvious suspect was the threshold: τ\* had been
calibrated on paragraphs drawn from **different documents**, while sixty
conjectures answering **one** question sit in a tighter band. Recalibrating in
the correct regime gave **τ₂ = 0.76 — within 0.015 of τ\***. The threshold
was very nearly right.

The fault was the **joining rule**. Single linkage merges two groups when
*any* member pair crosses the cut, so candidates chain end-to-end until the
cell fuses. On the same vectors at the same threshold, measured against the
direction labels:

| linkage | adjusted Rand vs direction partition | mean clusters per cell |
|---|---|---|
| single | 0.118 | 3.8 |
| **complete** | **0.676** | 15.0 |
| average | 0.632 | 10.9 |

Two things about leg 1 are worth keeping. First, the failure was **visible
from inside the registration**: the τ curve and the threshold-free M2 were
both registered in advance precisely so a saturated primary could not hide a
real signal, and both separated the arms while M1 reported nothing. Second,
leg 1 was **not re-scored** with the better rule. Tuning a metric on the data
that diagnosed its flaw and then reporting the result is how a
pre-registration is quietly spent; leg 1 calibrated, leg 2 measured on data
that did not exist when the new rule was frozen (`PREREG_LEG2.md`, commit
`79b9145e7`).

### An unplanned reproducibility check

The two legs are independent samples of the identical generation process —
`driver.py` unchanged, only `--root` differing. M2 is directly comparable:

| arm | leg 1 | leg 2 | Δ |
|---|---|---|---|
| A | 0.1614 | 0.1621 | +0.0008 |
| B | 0.2321 | 0.2636 | +0.0315 |
| C | 0.2550 | 0.2568 | +0.0018 |
| D | 0.2999 | 0.3146 | +0.0147 |

Three arms reproduce to within 0.002–0.015 across a full independent replay
of 1.1M tokens; B moves most (+0.03), which is consistent with B's output
depending on a single planning call per cell and therefore carrying that
call's variance.

## 4. The residue — what this does NOT show

**"More distinct" does not mean "better".** This experiment measured
distinctness and nothing else. Whether a more distinct population of
conjectures is a more *valuable* one — whether the extra ideas survive
criticism, or whether verbalized sampling buys variety by wandering further
from the question — is **not measured here**, was registered out of scope in
PREREG.md §9 before any call, and is parked in PARKED.md. Nothing in section
2 licenses a claim about conjecture quality.

**The registered rules were not met, and are not being talked around.** H1,
H2 and H3 are INCONCLUSIVE by rules frozen before the data existed. The
question-dependence in section 2 is the *explanation* for that, not a
substitute verdict. An arm's ordering is reported; a hypothesis is not
promoted.

**The self-reported probability numbers were never used.** They are recorded
raw in `raw/` and `raw_leg2/` and enter no metric, rank, filter or ordering.
The rule is enforced by an AST guard over both analyser sources, mutation-
proven to fire on three distinct leak paths (a probability parameter added to
a metric, a metric reading the string key, a verdict weighted by the number)
and to pass clean source.

**The leg-2 metric rests on a proxy label.** τ₂ and the linkage were fixed
using the named direction each B/D candidate was generated under. A direction
label is a proxy for idea identity — two candidates inside one direction can
still be different ideas — so the same-family class is contaminated by
construction and τ₂ under-splits rather than over-splits. It is applied
identically to all four arms, so it cannot favour one, but it does bound how
finely leg 2 can resolve distinctness. The labels exist only in the
stratified arms; they fixed a rule, they never scored an arm.

**Nine repetitions, and no inferential statistics.** None was registered and
none is claimed. Repetition ranges are printed so a reader can see whether a
stated difference exceeds the noise it sits in. Where a difference is small —
H1's B-vs-A, worth 1.4 clusters overall — it is reported as below the
registered 3-cluster floor and nothing more.

**Scope.** One model (glm-5.2), one provider (Ollama Cloud), one temperature
(0.9, held constant — the note's grade-A rows say temperature is not a
diversity lever, and re-measuring an A-grade finding was declined), thinking
off throughout, three questions, k=10, six directions, no divergence clause
(registered exclusion, PREREG.md §4). Nothing here generalises to other
models without measurement.

**One alternative explanation not excluded.** The geometry column may be low
for A and C partly because a construction question admits less lexical and
structural room per candidate than an open prose question, which would depress
an embedding-distance metric independently of how many genuinely different
ideas were produced. The experiment cannot separate that from a real absence
of ideas. What it does show is that stratification lifted that column
(1.7 → 6.0 → 12.0) while verbalized sampling alone did not.

## 5. Delivery obligations

- `git diff --stat origin/main -- src tests docs` — **empty**. No harness
  change, no test change, no map change; the write cone was this directory.
- No managed harness run was launched, so no soak was owed.
- Raw responses for both legs committed verbatim; every metric recomputable
  from them with `analyse.py` / `analyse2.py`.
- Total spend 2,243,500 tokens across two legs, each inside its own
  registered 1,440,000-token envelope.
