# RESULTS — STEP 1 live: hold the form, vary the brief, measure against the
# no-harness baseline with length held constant

Ran 2026-09-09 on `d7c87473e`, five days and 254 commits after `PREREG.md` was
sealed. Authority: `REQUEST.md` R1-R34 and the operator's "do it" (§4).
Amendment: `PREREG_AMENDMENT_2026-09-09.md`, sealed before the first call.
Per-arm operational detail: `RUNLOG.md`. Raw instrument output: `ANALYSIS.txt`,
`ANALYSIS_WITHIN_HARNESS.txt`, `LENGTH_OVERLAP.txt`, `blind/REVEAL.txt`.

**The one-sentence result.** No harness arm was shown to beat the plain model
call, and no harness arm was shown to lose to it either, because the
pre-registered primary comparison **cannot be computed on this data** — while
inside the harness, every brief difference measured came out SMALLER than the
gap between two arms shown the identical brief.

---

## 1. The predictions, restated before the numbers (PREREG §8)

| # | registered prediction |
|---|---|
| P1 | **No direction predicted** for A1 (history) against the null arms. |
| P2 | A3 scores **LOWER** than the null arms on the length-adjusted figure. |
| P3 | A1P and A2 are each within `d_noise` of A0 — i.e. **`d_noise` is small**. |
| P4 | **At least one harness arm's mean does NOT beat B0's** on the length-adjusted figure. |
| P5 | B0's candidates are **LONGER** than any harness arm's per candidate. |

Also registered: §3.2's falsifiable clause (an accepted `code:python-prop`
artifact with a claim over 200 characters would make A2 a real treatment), and
§11's premise test (if A1 and A3 are indistinguishable from the identical-brief
arms on every measure, "the input interface materially changes outputs" is not
supported on this record).

## 2. The numbers

### 2.1 What ran

Five arms and the baseline, all clean typed terminals, no operational failure,
no arm death, no transport fault in any arm. One relaunch — arm A3, disclosed
in `RUNLOG.md`, at its own guard **before its first provider call**, with no
run root and zero tokens spent.

| arm | what varied | tokens | accepted | refuted | survivors | rounds |
|---|---|---|---|---|---|---|
| A0 | nothing (control) | 417,053 | 104 | 2 | 50 | 9 of 9 |
| A1 | history rendered | 560,500 | 150 | 4 | 68 | 12 of 12 |
| A1P | history plugin removed | 474,282 | 98 | 0 | 54 | 9 of 9 |
| A2 | `claim_chars` 200→800 | 429,432 | 110 | 0 | 53 | 9 of 9 |
| A3 | operator `.tmpl` | 430,908 | 115 | 0 | 53 | 9 of 9 |
| B0 | **no harness** | **21,284** | 12 answers | — | — | — |

### 2.2 The arms were what they claimed — from the records, not the rig

`verify_arms.py` over the five retired roots, reading the runs' own typed
section receipts:

    arm   dr.history.v1              dr.neighbourhood     op.neighbourhood.v1
    A0    never rendered      0 B    11 × 14,768 B        never rendered  0 B
    A1    RENDERED        4,228 B    11 × 14,929 B        never rendered  0 B
    A1P   never rendered      0 B    11 × 14,286 B        never rendered  0 B
    A2    never rendered      0 B    11 × 14,919 B        never rendered  0 B
    A3    never rendered      0 B    never rendered 0 B   11 ×  6,870 B

`dr.active-properties` rendered **zero bytes in every arm**.

Three things this settles, each argued from source in the sealed PREREG and now
confirmed from live records:

1. **The shipped default shows no history** (§3.1). A1 is the only arm whose
   seats saw refuted work, so the operator's amendment 3 — "A0 (history ON, the
   shipped default) vs A1'" — rested on a false premise, exactly as the sealed
   document said before any call, and the contrast that carries its meaning is
   A1 against the identical-brief arms.
2. **A2 had nothing to widen** (§3.2), and its falsifiable clause was **not
   triggered**: no accepted `code:python-prop` artifact existed.
3. **A3 is a format change WITH CONTENT LOSS** (§3.4), and the loss is now
   measured: the same section, the same 11 renders, **6,870 bytes against the
   control's 14,768 — 53% of the content gone.**

### 2.3 The blind judging

248 candidates, three judges each, 0 failed, 6 contested (spread over 4 of 15).
The judges saw `{bid, text}` and nothing else; the key set of
`blind/candidates.jsonl` was read to confirm that rather than assumed. Scores
were sealed by digest and committed **before** the keymap was opened.

| arm | n | mean | median | best | chars |
|---|---|---|---|---|---|
| A0 | 46 | 5.35 | 5.50 | 14.0 | 357.0 |
| A1 | 48 | **4.88** | 5.00 | 13.0 | 346.8 |
| A1P | 48 | **6.73** | 7.00 | 14.0 | 358.4 |
| A2 | 47 | 6.26 | 6.00 | 14.0 | 381.0 |
| A3 | 47 | 6.68 | 6.00 | 14.0 | 350.0 |
| B0 | 12 | **14.75** | 15.00 | 15.0 | **7,775.5** |

The panel pays heavily for length, as the parent tranche measured: Spearman
ρ(chars, total) = **+0.825** pooled, and log-length alone explains R² = 0.485.

### 2.4 THE NOISE FLOOR — the number that governs every other number

Three arms were shown **byte-identical briefs** (§2.2 confirms it from their
records). Length-adjusted gaps between them, from the committed estimators:

    A1P vs A0   +1.312  (p=0.012)      <- d_noise
    A2  vs A0   +0.193  (p=0.724)
    A2  vs A1P  -1.212  (p=0.033)

**`d_noise` = 1.312 of 15.** Two runs of the same brief differ by more than a
point and a half of fifteen, with p = 0.012 — a difference that looks
statistically convincing and means nothing, because there is nothing there to
find. On the operational side the same three arms spread 57,229 tokens (13.7%),
12 accepted artifacts, and 0 against 2 refutations.

### 2.5 The two real treatments, against the pooled identical-brief arms

| comparison | raw | **length-adjusted** | quintile-held | vs `d_noise` |
|---|---|---|---|---|
| A1 (history) vs NULL | −1.246 | **−0.803** (p=0.057) | −0.792 | **inside** |
| A3 (template) vs NULL | +0.560 | **+1.105** (p=0.011) | +1.486 | **inside** |

Both treatments moved the judged score less than two runs of the same brief
did.

### 2.6 The comparison against B0 CANNOT BE COMPUTED, and that is a result

`analyse_arms.py` printed, for A0 against B0: raw **−9.402**, quintile-held
**−5.545**, and "length-adjusted **+14.536**, p=0.0000 — THE VERDICT FIGURE,
BETTER than the single call". Then it crashed inside the committed `stratified`
with a division by zero.

**That +14.536 is an artefact and is reported as one.** It is larger than the
entire 0-15 scale; it points opposite to both other views of the same data; and
`LENGTH_OVERLAP.txt` gives the reason:

    B0       n= 12  chars 6,853 - 8,873
    harness  n=236  chars   128 -   843
    overlap: NONE. The shortest B0 answer is 8.1x the longest harness candidate.

A model of `total ~ 1 + log(chars) + arm` separates an arm effect from a length
effect only where the groups overlap. With zero overlap the arm term is pure
extrapolation, and the quintile stratification divides by zero because most
strata contain no B0 rows at all. **The pre-registered primary measure is
undefined on this data.** No verdict is stated on it.

`PREREG.md` §4.1 named half of this before any call — "the one place B0 is not
comparable" — and fixed the comparison on the mean. It under-priced it: the
deeper problem is not that the means are unfair but that **the length control
it also registered stops existing**, and §5 forbids a verdict on anything else.

The mismatch is a unit mismatch, not a length preference. A B0 candidate is a
whole answer; a harness candidate is one `claim` field. Criteria 1, 3 and 4 ask
for both cases made, a stated verdict, and a named cost — things a single
conjecture structurally cannot carry. B0's 14.75 substantially measures
"is this a complete essay", which every B0 row is and no harness row is.

## 3. One verdict per arm against B0 (R31)

Stated on the length-held-constant figure, per R15 — and where that figure does
not exist, the honest verdict is that there is none.

| arm | verdict against B0 |
|---|---|
| A0 | **NO VERDICT AVAILABLE.** The length-held-constant figure is undefined (§2.6). |
| A1 | **NO VERDICT AVAILABLE.** Same reason. |
| A1P | **NO VERDICT AVAILABLE.** Same reason. |
| A2 | **NO VERDICT AVAILABLE.** Same reason. |
| A3 | **NO VERDICT AVAILABLE.** Same reason. |

**What is defined, and stated as such rather than hidden:** on raw means and on
the quintile-held figure, every harness arm scores far below B0 (5.35-6.73
against 14.75; quintile-held −5.5 for A0). If those were admissible verdicts,
every arm would be a FAILED arm under R32. They are not admissible — R15
forbids a verdict on the raw figure, and §2.6 shows the quintile figure is
computed on strata that mostly contain no B0 rows — but the operator should
read this paragraph as the closest thing to bad news this experiment produced,
and should not be told the arms "passed".

**This experiment therefore did not measure the 2026-09-03 law's criterion.**
It is not that the harness lost; it is that the comparison as designed cannot
answer the question, and the reason is now known precisely enough to fix in the
next tranche (§5).

## 4. The history default — PREREG §7's rule, applied

**What was being decided:** whether a conjecturer should be shown the refuted
artifacts of its own problem by default. Today it is not (§2.2 confirms the
shipped default renders no history). `SPEC.md` S10 of the history tranche
specifies ON and is NOT STARTED.

    d_hist  = -0.803 of 15   (p=0.057, quintile-held -0.792)
    d_noise = +1.312 of 15

`|d_hist| < d_noise`, so by the rule sealed before any call:

> **RECOMMENDATION: NO CHANGE — the evidence does not separate history from
> scatter.**

A recommendation only. R33: no default, config or source file was changed by
this tranche, and none should be changed on this evidence.

Two things worth carrying forward, neither of which changes the recommendation:

- The **direction is negative** and agrees with the parent tranche's
  independent measurement through a different channel (−1.558 raw there,
  −0.803 adjusted here). Two negative readings from different mechanisms is
  weak evidence, not none — but it is evidence AGAINST S10's ON, never for it.
- **The dose was small.** History rendered on 4 of A1's 18 conjecturer
  dispatches, because the section has content only once something has been
  refuted. This is a result about a brief that carried refuted work on roughly
  a fifth of its turns.

## 5. The residue — what remains unproven

1. **The law's own question is unanswered.** The primary measure is undefined
   (§2.6). The next experiment must compare like with like: either the
   harness's own composed answer against a B0 answer, or B0's answers split
   into claims and judged as claims. Neither exists today — these runs ended at
   `budget_exhausted` with survivors and no composed answer, so there was
   nothing of the right shape to compare.
2. **`d_noise` = 1.312 of 15 exceeds every treatment effect measured here**, so
   the pre-registered n cannot decide either treatment. This is `ERRATA` E78
   reproducing in a fresh tranche with a fresh question, and the audit named it
   as the corpus's most important methodological limit. **P3 is falsified in
   substance**: it predicted `d_noise` would be small, and it is larger than
   both treatments. As instructed, this is reported as the result; no arms were
   added to chase significance.
3. **A statistically convincing number can still be noise.** A1P beat A0 by
   1.312 of 15 at p = 0.012 on a byte-identical brief. Any future reading of a
   p-value in this tree should be checked against a same-brief floor first.
4. **The measurement instrument was the fallback**, not the neural embedder:
   every arm reports `embedder: hashing (hashing-128)` despite the weights
   being fetched at session start. Held constant across all arms rather than
   changed mid-experiment. It touches M2 and the novelty readings, not the
   blind judging that decides §4 and §7. Why it fell back was not diagnosed.
5. **The secondary measures registered in §9 — M1/M2/M3 diversity, admission
   rate per contract, criticism outcomes — were not computed.** The primary
   measure and the decision rule were, and the noise floor makes the secondary
   ones unable to decide anything the primary could not. Stated as not done
   rather than quietly dropped.
6. **A3 answered a narrower question than the parent tranche intended.** It was
   meant to be "same information, different shape"; the shipped template
   channel cannot do that for a computed section, so it became "half the
   information, different shape" (§2.2, 53% content loss). Its +1.105 — inside
   the floor — is therefore not evidence that reformatting helps.
7. **`analyse_arms.py` cannot compute its own primary comparison** on data of
   this shape, and dies rather than declining. Recorded as `PARKED.md` F5.
8. **One arm's brief-difference dose is small and unmeasured elsewhere.** No
   experiment in this tree has varied how MUCH of a section a seat sees.

## 6. What this tranche did not do

No file under `src/`, `tests/` or `mini/` was touched, no default was changed,
no gate was run (no product code changed), and no arm was added beyond the
five the operator named plus B0. The sealed `PREREG.md`, `PROVE_ARMS.txt`,
`rig/armrig.py`, `rig/sitecustomize.py` and `prove_arms.py` all still verify
against `SEALED.txt`. Two scripts that are not sealed were fixed and the fixes
are ledgered: `soak_arms.sh` (could not reproduce its own documented green A3),
`resume.sh` (would have granted a killed arm a full fresh budget), and
`arm.sh` (verified the rig by installing it twice).
