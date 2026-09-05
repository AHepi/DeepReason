# M1 replicated — three pairs, and what survived

`RESULTS_M1.md` and `RESULTS_M1_QUALITY.md` each rested on **one paired run**.
Both closed by saying that nothing in a single pair separates a real effect
from ordinary variation, and both recommended the same fix: run it again.
`PREREG.md` Amendment 5 registered the predictions and the decision rule; the
operator approved; two more pairs were run.

This document reports what happened. **It corrects the headline of
`RESULTS_M1_QUALITY.md` and it withdraws the cost claim that `SPEC.md` S10
leans on.**

---

## 1. The predictions, as registered before the replicates ran

From `PREREG.md` Amendment 5, quoted, with its decision table:

> - **COST, directional: the treatment spends FEWER tokens per admitted
>   conjecture than its paired control, in each new pair.**
> - **QUALITY, directional: the treatment's blind-judged mean is LOWER than its
>   paired control's, in each new pair.**
> - **LENGTH, directional: the treatment's admitted conjectures are SHORTER on
>   average than its paired control's, in each new pair.**

| new pairs agreeing with the first | verdict |
|---|---|
| both | REPLICATED |
| one of two | UNRESOLVED |
| neither | REFUTED |

---

## 2. The three pairs

Every arm: `completed`, `budget_exhausted`, four cycles, replay validation
valid. Four for four on the replicates, matching the first pair exactly.

| | P1 control | P1 history | P2 control | P2 history | P3 control | P3 history |
|---|---|---|---|---|---|---|
| admitted conjectures | 43 | 42 | 43 | 39 | 35 | 41 |
| tokens spent | 541,666 | 414,536 | 516,589 | 372,301 | 314,220 | 454,065 |
| tokens per conjecture | 12,597 | 9,870 | 12,014 | 9,546 | 8,978 | 11,075 |
| **judged mean of 15** | **6.58** | **5.02** | **6.70** | **4.26** | **4.71** | **4.61** |
| mean chars | 376 | 345 | 418 | 311 | 318 | 283 |

**Look at the control column before anything else.** The same arm, run three
times with everything held identical, produced judged means of 6.58, 6.70 and
**4.71**, and token spends of 542k, 517k and **314k**. The control's own
run-to-run spread is comparable to every between-arm difference this experiment
has ever reported. That is not a side observation; it is the measurement the
first pair could not make, and it is why one pair could never have settled
anything.

## 3. The registered rule, applied

    cost: tokens per conjecture   P1=lower  P2=lower  P3=HIGHER   UNRESOLVED
    quality: blind-judged mean    P1=lower  P2=lower  P3=lower    REPLICATED
    length: mean chars            P1=lower  P2=lower  P3=lower    REPLICATED

### 3.1 COST — UNRESOLVED, and the headline of `RESULTS_M1.md` does not stand

The treatment was 21.6% cheaper per admitted conjecture in P1, 20.5% cheaper in
P2, and **23.4% more expensive in P3**. Under the rule fixed in advance that is
UNRESOLVED: consistent with variance, and no longer usable as a finding.

`RESULTS_M1.md` called this "the most interesting result" and recorded that it
FALSIFIED a registered prediction. That reading was correct on the evidence
then available and is now superseded: the prediction it falsified was that
history costs MORE, and P3 spent more. Two of three pairs favour the treatment,
one contradicts it, and the honest state is that **the cost effect is not
established in either direction**.

### 3.2 QUALITY — the registered direction REPLICATED, and the rule was still the wrong instrument

All three pairs put the history arm's judged mean below its control's, so the
pre-registered rule returns REPLICATED. **That verdict should not be trusted,
and this section says why in the same breath as reporting it** — the same
mistake the primary near-duplicate measure made in `RESULTS_M1.md`, where a
rule written in advance scored a 100% relative drop on a base of one pair.

Two things spoil it.

**First, P3's margin is 0.10 of 15** — 4.71 against 4.61. The rule asks only
whether one number is below another, so a tenth of a point counts the same as
two and a half. A direction test that a coin-flip-sized difference can satisfy
is not measuring what its name suggests.

**Second, and decisively: length replicated too, and the judges pay for
length.** Amendment 5 registered length as its own prediction precisely so this
could be checked. Holding candidate length constant:

| | raw gap | length gap | gap with length held constant | p |
|---|---|---|---|---|
| P1 | −1.56 | −8.2% | −0.78 | 0.138 |
| P2 | −2.44 | −25.6% | −0.38 | 0.472 |
| P3 | −0.10 | −10.9% | **+1.17** | 0.046 |
| **pooled, 243 candidates** | **−1.44** (p = 0.003) | **−16.3%** (p = 0.0005) | **+0.04** | **0.885** |

Pooled across all three pairs the raw quality gap looks solid — 4.64 against
6.08 of 15, and a label shuffle reproduces it 3 times in 1000. **Hold length
constant and it is +0.04 of 15 with p = 0.885: gone, and if anything pointing
the other way.** Across all 243 candidates the rank correlation between a
candidate's character count and its judged total is +0.759.

So "the history arm is judged worse" and "the history arm writes shorter
conjectures" are the same fact reported twice. The first is the second, seen
through a panel that rewards length.

### 3.3 LENGTH — REPLICATED, and it is the one solid finding here

Shorter in all three pairs (−8.2%, −25.6%, −10.9%), pooled 313 against 374
characters at p = 0.0005. **Attaching a problem's own history makes the
conjecturer write shorter conjectures.** That is the one directional effect in
this experiment that survived three paired runs, and it survives without
needing the judge panel at all — it is a property of the text, counted.

What it MEANS is not established. Shorter is not worse (the length-adjusted
scores say so) and it is not better either. Two readings remain open, and this
design cannot separate them: the history section crowds the prompt and leaves
less room; or a seat that can see what has already been refuted has less to
say. Nothing here decides between them.

---

## 4. The verdict

**On quality: history-ON conjectures are NOT judged worse. They are
indistinguishable from control once their length is accounted for.**
`RESULTS_M1_QUALITY.md`'s headline — "judged worse, suggestive of harm, not
demonstrated harm" — is superseded by this document. Its caveat was the
load-bearing half, and the replication has now cashed it: the raw gap was the
length shift wearing a merit label, exactly as that document warned it might
be, and it said so before these runs existed.

**On cost: the treatment's cheapness did not replicate, and the claim is
withdrawn.**

**On the shipped ON default: nothing measured now argues for it, and nothing
measured argues against it.** That is a THIRD position, and it is not the one
either earlier document left the operator in:

| | what S10 was told | what stands now |
|---|---|---|
| spread (D5) | up 21.8%, secondary prediction HELD | one pair only; never replicated; this tranche already records it cannot interpret D5 |
| cost per conjecture | down 21.6%, "the most interesting result" | **UNRESOLVED** — reversed in P3 |
| quality | not measured, then "judged worse" | **indistinguishable** once length is held constant |
| candidate length | not examined | **shorter, in all three pairs** — the one replicated effect |

**The default is NOT changed here, and no code, spec or config was touched.**
That remains the operator's decision. What has changed is the evidence
underneath it: `SPEC.md` S10 chose ON because "nothing measured argued against
it and the cost objection was the one concrete argument, and it failed." The
cost argument is now un-failed — it is unresolved — and the quality worry
raised yesterday has evaporated. Both movements are real and they point
opposite ways.

---

## 5. Residue

1. **Still one question and one model.** Three pairs establish that these
   effects are or are not stable across repetitions of THIS arm on THIS
   question. Nothing here generalises past that, and a second question was not
   run.
2. **The judges remain a length meter, now measured twice.** ρ = +0.797 on the
   first 167 candidates, +0.759 on all 243. Any future use of this panel should
   report length-adjusted numbers alongside raw ones, or it will keep
   rediscovering verbosity and calling it quality.
3. **The control arm's own variance is the finding nobody registered.** Judged
   means of 6.58 / 6.70 / 4.71 and spends of 542k / 517k / 314k, with every
   input identical. Any future single-pair comparison on this harness should
   expect a difference of this size from nothing at all.
4. **P3's length-adjusted term is positive at p = 0.046**, which on its own
   would read as the history arm doing BETTER per unit of text. It is one of
   several tests reported here and it is not claimed as a finding; it is
   recorded because leaving it out would make the negative result look tidier
   than it is.
5. **The unit is admitted conjectures**, as in every other measure of this
   tranche — not the discarded candidates the copied protocol also asks for.
   Stated in `RESULTS_M1_QUALITY.md` §3.3 and unchanged here.
6. **No no-harness baseline exists for this question.** Under the 2026-09-03
   law, success is progress over what the same model produces without the
   harness. All six arms here are harness arms. This document compares two
   harness configurations and says nothing about whether either beats a single
   model call.

---

## 6. Reproducing this

    python judge_replication.py reveal        # per-arm judged means, replicate set
    python analyse_replication.py            # three pairs + the registered rule
    python analyse_replication_length.py     # the length-held-constant table
    sha256sum blind/scores.json blind-r/scores.json   # must match both SCORES_SEALED.txt

Both score files were digest-sealed in commits that landed before their
respective keymaps were opened. If either digest differs, every per-arm number
derived from it is void.
