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
