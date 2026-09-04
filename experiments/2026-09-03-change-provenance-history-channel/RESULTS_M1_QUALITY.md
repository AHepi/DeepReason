# M1 quality — the blind judging, resumed and finished

`RESULTS_M1.md` closes its quality row with **"NOT MEASURED"**. This document
fills exactly that row and nothing else. It reports the blind three-judge
scores over the harvested candidates, per arm, and says whether the arm shown
its own problem's history produced conjectures judged better, worse, or
indistinguishable.

**Order of writing, which is the point.** §1 and §2 below were written and
committed BEFORE the 91st candidate was scored and BEFORE the keymap was
opened. The numbers arrive in §3, after the predictions they are measured
against are already fixed in git. The commit history is the evidence for that
claim, not this sentence.

---

## 1. The predictions, restated before any number

Quoted from the documents that carry them, unaltered.

**From `PREREG.md` §1, on M1 quality (written before any arm launched):**

> **Quality, NO DIRECTION PREDICTED.** The operator's R6 says history "might
> help LLMs craft better conjectures", and the honest state of this question is
> that nobody knows. Registering a direction here would be inventing a prior.

So there is no M1 quality prediction to score. That absence is itself
pre-registered: an outcome in either direction — better, worse, or flat — was
admissible before the first candidate existed, and none of the three can be
claimed afterwards as the thing the tranche expected.

The three M1 predictions that DO carry a direction were scored already in
`RESULTS_M1.md` and are restated here only so this document cannot be read as
re-scoring them:

| registered prediction | scored in `RESULTS_M1.md` |
|---|---|
| primary — H1 lowers the near-duplicate rate | INCONCLUSIVE (floor effect: 1 pair of 903) |
| secondary — H1's per-problem D5 is higher | HELD (0.179 vs 0.147) |
| cost — H1 spends MORE tokens per admitted artifact | FALSIFIED (21.6% FEWER) |

**From `JUDGING_PREREG_COPIED.md`, the protocol this document executes**, three
commitments that bind the numbers in §3:

> A candidate's total is the MEDIAN of the three judges' totals, not the mean —
> one judge scoring an outlier cannot carry a candidate.

> any candidate whose three totals span more than 4 points of 15 is flagged in
> the output as contested

> The pick is one reader's scored judgement against fixed criteria on blinded
> text. It is not a measurement of arm quality.

That last line is the copied protocol's own disclaimer about its own output,
and it is adopted here unchanged. It is why §4 states a verdict about what the
judges saw, not a claim about what is true of the arms.

**From `PREREG.md` §3, on the M3 arms**, whose candidates share this candidate
pool and are therefore also scored:

> **Secondary, and this is the real question:** C1's blind-judged sharpness is
> NOT higher than C0's, and may be lower.

**This document does not score that prediction, and §3.2 says why.** The
registered M3 measure is the sharpness of CRITICISM. The instrument harvests
CONJECTURES from all four roots (`judge.py::harvest` selects `conjectures(root)`
on the seed problem). The M3 rows below therefore measure the conjectures
produced in the M3 arms, which is a different quantity from the one R7 is about.
`RESULTS_M3.md`'s "blind-judged sharpness: NOT RUN" row stays NOT RUN.

---

## 2. The state inherited, verified before scoring resumed

Every check below was run before a single new call was made.

| check | result |
|---|---|
| `blind/candidates.jsonl` rows | 167, all `bid` unique, fields exactly `{bid, text}` |
| `blind/scores.json` entries | 90 |
| scored bids ⊆ candidate bids | yes |
| entries recording a scoring failure | 0 |
| scored set vs file order | exactly the first 90 rows of `candidates.jsonl`, contiguous — so resuming means the 91st row, as instructed |
| judges per scored candidate | 3 for 89 candidates; **1 for one candidate** |
| `blind/keymap.json` | not opened |

**The instrument keeps no state file apart from `blind/scores.json`.**
`judge.py::score` reloads that file and skips any `bid` already present; there
is no second ledger that could disagree with it. The instruction to stop and
report on a disagreement is therefore satisfied vacuously, and this row records
that it was checked rather than assumed.

**The one-judge candidate is kept as written.** Its median is one judge's total,
not three, which is weaker than the protocol specifies. Every existing score
stands as written, per instruction; the deviation is named here and the
candidate is flagged in §3 rather than dropped or re-scored.

---

## 3. The numbers

All 167 candidates scored, none failed, digest sealed in `blind/SCORES_SEALED.txt`
in the commit BEFORE `blind/keymap.json` was read. Candidate total = median of
three judges, 0–15.

### 3.1 M1 — the arms this document is about

| | CONTROL (H0P) | TREATMENT (H1R, history ON) |
|---|---|---|
| candidates | 43 | 42 |
| **mean total** | **6.58** | **5.02** |
| median total | 7.0 | 5.0 |
| upper quartile | 10.0 | 8.0 |
| lower quartile | 2.0 | 2.0 |
| best candidate | **14.0** | 11.0 |
| scoring ≥10 of 15 | 14 of 43 (32.6%) | 8 of 42 (19.0%) |
| scoring ≤2 of 15 | 13 of 43 (30.2%) | 16 of 42 (38.1%) |
| contested (>4 spread) | 1 | 1 |

The treatment is lower on every summary: mean, median, upper quartile, best
candidate, share of strong candidates, share of weak ones. The raw gap is
**−1.558 of 15, or −23.7% relative**.

**It is not distinguishable from chance.** Shuffling the arm labels over these
85 totals produces a gap this large or larger **8.2% of the time**
(p = 0.0816, 100 000 shuffles, seed fixed in `analyse_quality.py`). No
threshold for this comparison was pre-registered, because no direction was
pre-registered; the p-value is reported as a description of the scatter, not
as a decision rule being executed.

### 3.2 The M3 arms, and why they answer nothing about M3

| | C0P (blind) | C1I (informed) |
|---|---|---|
| candidates | 43 | 39 |
| mean total | 5.63 | 5.87 |
| best | 14.0 | 11.0 |

Flat: +0.244 of 15, p = 0.78. **This does not fill `RESULTS_M3.md`'s NOT RUN
row.** The registered M3 measure is the sharpness of CRITICISM; the instrument
harvests CONJECTURES from all four roots. These rows describe the conjectures
produced in the M3 arms, which is a different quantity from the one R7 is
about. `RESULTS_M3.md` stays as written.

### 3.3 A deviation from the copied protocol's scope, stated rather than buried

The copied protocol judges "EVERY candidate conjecture from all three arms,
**including discarded ones**". This harvest reads committed artifacts
(`judge.py::harvest` → `measure_diversity_per_problem.conjectures`, which walks
`objects/artifact/`), so the pool is **admitted conjectures only** — 43 and 42,
exactly the counts `RESULTS_M1.md` reports as admitted. Anything the admission
screen filtered differently between arms is therefore already baked into the
pool before a judge saw it. The upside is that this document and
`RESULTS_M1.md` measure the same unit (C11), so their numbers are comparable;
the cost is that the verdict is about admitted conjectures, not about
everything the arms generated.

### 3.4 The judges are substantially measuring length

This was not looked for. It was checked because CLAUDE.md's judge law records
verbosity bias as having **zero live measurements**, and the check is cheap.

Across all 167 candidates, the judged total rises with the candidate's
character count: **Spearman ρ = +0.797**, Pearson r = +0.691. A regression of
total on log(characters) alone gives **R² = 0.589** — length by itself accounts
for around three fifths of the variance in what these judges scored.

That matters here because the two M1 arms did not write to the same length. The
treatment's candidates are **8.2% shorter** (mean 345 vs 376 characters), a
difference that is itself well inside noise (p = 0.30). Adjusting for it:

| M1 comparison, history minus control | gap (of 15) | p |
|---|---|---|
| raw | −1.558 | 0.082 |
| holding length constant, log-length covariate | **−0.78** | 0.134 |
| holding length constant, within length quintiles | −1.310 | — |

So roughly half the raw gap is the treatment writing shorter, and the residue
after that adjustment points the same way but is weaker still.

**The same check applied to the M3 arms produces a sharper result, in the
opposite direction to the raw table**, and it is recorded because it was run:
the informed arm wrote **40.7% longer** candidates (p = 0.0003) yet scored only
+0.24 raw; adjusted for length its arm term is **−1.73 of 15 (p = 0.0015)**.
Per unit of text, the M3 informed arm's conjectures scored worse. This is a
finding about the M3 arms' conjectures, not about critic sharpness (§3.2), and
it is not a registered measure.

---

## 4. The verdict

**History-ON conjectures were NOT judged better. They were judged worse, and
the margin is real in this sample but not separable from chance.**

Stated at the precision the record supports, and no further:

1. **"Better" is refuted for this run.** Every summary statistic moves the
   wrong way for the treatment. R6's "history might help LLMs craft better
   conjectures" gets no support here of any strength.
2. **"Worse" is the direction but not an established result.** −23.7% raw at
   p = 0.082; −0.78 of 15 at p = 0.134 once length is held constant. A
   reasonable reader calls this *suggestive of harm, not demonstrated harm*.
3. **A large part of what was measured is length, not merit.** With ρ = +0.797
   between characters and score, this panel rewards longer candidates almost
   mechanically. That weakens the verdict in both directions: it is why the raw
   gap should not be quoted alone, and it is why the adjusted gap should not be
   treated as a clean measure of merit either.

**One reading this result makes newly plausible, and does not establish.**
`PREREG.md` registered, before any arm ran, that a wide spread of off-topic
claims scores well on D5 — "the failure mode the source branch's RESULTS.md
already documented". `RESULTS_M1.md` reports the treatment's D5 **higher**
(+21.8%) and read that as the secondary prediction HELD. Judged quality in the
same arm is lower. Those two facts together are consistent with the treatment
having bought its extra spread by drifting off the question. Consistent with —
not evidence for. Nothing here separates "more spread because more varied
attack on the problem" from "more spread because further from the problem", and
the D-measures cannot make that distinction by construction.

**And one caution about the cost result, which is not this document's to
settle.** `RESULTS_M1.md`'s headline surprise was that the treatment spent
21.6% FEWER tokens per admitted conjecture. Its candidates are also 8.2%
shorter and score lower. A single explanation covering all three — the
treatment simply produced less per artifact — is available and was not
available before today. It is not established here; the token figure counts a
whole cycle's work and the character count measures one field of one artifact.
It is flagged because "cheaper" and "less" are not the same claim, and the
cost result is currently doing load-bearing work in `SPEC.md` S10.

---

## 5. What this does to the shipped ON default — and what is NOT being changed

**`SPEC.md` S10 sets the conjecturer default ON, and its stated reason no
longer holds as written.** The sentence is:

> The default is ON because nothing measured argued against it and the cost
> objection was the one concrete argument, and it failed.

Something measured now argues against it. Weakly — p = 0.082 raw, 0.134
adjusted, one paired run, one question — but the premise "nothing measured
argued against it" is false as of this document, and S10's reasoning cannot be
left standing unamended while pointing at evidence that has since arrived.

**The default is NOT changed here, and no code, spec or config was touched.**
That is the operator's decision, not the monitor's. What this document does is
put the missing row on the table:

| what S10 knew when it chose ON | what is known now |
|---|---|
| spread up (D5 +21.8%) | unchanged |
| cost down (−21.6% per artifact) | unchanged, with a caveat in §4 |
| **quality unmeasured** | **quality measured: lower, suggestive, not demonstrated** |

The honest summary for a decision-maker: the ON default was chosen on two
positives and one blank. The blank has been filled in with a mild negative. Two
readings survive, and the tranche cannot choose between them —

- **W**: history genuinely produces weaker conjectures on this kind of
  question, and the spread gain is drift;
- **R**: one paired run of a stochastic engine, and this is scatter, amplified
  by a judge panel that pays for length.

—which is the same W/R fork `RESULTS_M1.md` recorded for the cost result, and
it is unresolved for the same reason: one run per arm.

---

## 6. Residue

1. **One paired run, one question.** 43 and 42 candidates from single runs of a
   stochastic engine on one seed question. No significance test on this design
   can speak about reruns, and none above claims to.
2. **The judges share a model family with the arms** (`qwen3.5:397b`, judges
   and seats alike). The copied protocol says it plainly: three judges from one
   family are not three people, and a panel narrows variance, not bias.
   Self-preference bias remains unmeasured, and this design cannot measure it.
3. **Verbosity bias is now measured in-sample, and it is large** (ρ = +0.797,
   R² = 0.589 on length alone). CLAUDE.md's judge law records verbosity bias as
   having zero live measurements; this is one, on 167 candidates, and it should
   be read as a property of THIS panel on THIS question rather than as a
   constant of the judge configuration. It also means every arm-level number in
   this document is partly a length statistic.
4. **One candidate of 167 was scored by a single judge**, not three, and its
   total is that judge's rather than a median. It is in the M3 informed arm. It
   was inherited and kept as written per instruction.
5. **No no-harness baseline arm exists in M1.** Under the 2026-09-03 law,
   success is progress over what the same model produces WITHOUT the harness.
   Both arms here are harness arms, so this document compares two harness
   configurations and says nothing about whether either beats a single model
   call. That comparison has not been run for this question.
6. **The one measurement that would settle it.** Two more runs per arm on the
   same question, judged by the same sealed protocol, would separate W from R
   for roughly the cost of M1 itself — the same recommendation
   `RESULTS_M1.md` already made for the cost result, now doubly earned: the
   same repetition would settle both the cost surprise and this quality gap.
   A second question would be needed before anything here generalises past
   this one.

---

## 7. Reproducing this

    python judge.py reveal          # the copied protocol's own four-arm summary
    python analyse_quality.py       # per-arm distribution, best-per-arm, permutation
    python analyse_length_bias.py   # every number in section 3.4
    sha256sum blind/scores.json     # must equal the digest in blind/SCORES_SEALED.txt

If that digest differs, the score file moved after the arm mapping was opened
and every per-arm number above is void.
