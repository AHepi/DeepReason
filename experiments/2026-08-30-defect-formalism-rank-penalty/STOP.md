# STOP — one decision, answerable in one word

**The decision:** should an artifact with nothing to check be scored
NOT-MEASURED on the coverage axis (road **a**), given a neutral default score
(road **b**), or left as it is with a note recording what happened (road **c**)?

Answer **a**, **b**, or **c**. If you want the note as well as the repair,
answer **a+c**.

---

## The worry first

Nothing you have already run is wrong, and nothing you have already decided is
being reopened. This is the last of the three roads you were priced on
2026-08-27 that still needs your word before code can land — and the code for
the road I recommend is already written, tested and sitting on this branch, so
"a" costs you a merge and not a tranche.

Glossary for this page, because two terms do all the work:

- **Coverage axis** — one of three numbers the harness scores every surviving
  conjecture on at the end of a run. It is "how many of this conjecture's
  mechanically checkable commitments actually passed", as a fraction.
- **Frontier** — the short list the run publishes as its answer. It is the
  *Pareto frontier*: keep a conjecture unless some other conjecture beats it on
  every one of the three numbers. Being off it is not a demotion; it means
  unfunded and unlisted.

## What is actually happening today

A conjecture written in prose has no mechanically checkable commitments, so
there is nothing to divide, and the code writes **0.0** — the same number it
writes for a conjecture that *was* checked and **failed everything**. A
formally-backed sibling that passed its checks scores **1.0**, beats the prose
one on that number, ties on the other two, and pushes it off the published
list.

Measured fresh today at this branch's head, not inherited from the audit:

| root | survivors | with nothing to check | published frontier |
|---|---|---|---|
| `experiments/2026-08-12-live-grounded-extension-expansion/run` | 233 | **146** | **87** — exactly the 87 that had something to check |
| `experiments/2026-08-25-poietics-program/run` | 58 | 0 | 40, unmoved by any road |

146 prose conjectures scored `(0.0, 0.0, 0.0)`; 87 formal ones scored
`(0.0, 0.0, 1.0)`; the published answer was the 87. Zero of the 146 made it.
Full output: `proof/footprint_2026-08-30.txt`.

This is the one thing the 2026-08-27 audit classified as an **unlawful
penalty** against your standing law — "nothing may penalize a conjecture for
being informal ... its absence grants no disadvantage."

## The three roads, in your terms

| | What you get | When | What it costs you |
|---|---|---|---|
| **a — NOT-MEASURED** | A prose conjecture is never out-ranked for having nothing to check. The axis keeps working normally between conjectures that *do* have something to check. | Already built. A merge. | Two source files (~20 lines). Runs with prose survivors will publish longer answers and may stop at a different cycle than they would have. Historical runs' *recomputed* frontiers move; their stored records do not change. |
| **b — neutral default** | Same headline effect: prose stops being out-ranked. | Would need a fresh tranche. | Cheapest to write, and it invents a measurement. See the law section: it does not actually remove the problem, it moves it. |
| **c — leave it, add a note** | You can see, per run, which conjectures were dropped for having nothing to check. | Would need a fresh tranche. | Nothing changes about which conjectures are published. The penalty stays live. |

Roads **a** and **c** are not rivals: **a+c** is a coherent answer — repair the
ranking *and* record the note.

## The law narrows this, and here is the argument rather than the assertion

The binding form of your law (`docs/proposals/DUAL_MODE_CONJECTURE_PREPLAN.md`
R-g:42-57), quoted exactly:

> no mechanism in this program — nor anywhere in the harness — may require
> formal encoding for a conjecture to enter, rank, survive, or be accepted;
> may weight ranking, scheduling, or acceptance on a conjecture's KIND ...
> Formal backing may confer PROTECTION (prose-immunity, as today); its absence
> confers no disadvantage. D3's and D4's regressions must prove kind-blindness:
> an informal conjecture's rank, criticism exposure, and acceptance path are
> byte-identical whether or not the formal channel exists in the build.

Four tests fall straight out of those words. `road_law_probe.py` runs each road
against all four and prints the frontier it computed, so this is a measurement,
not an opinion (`proof/road_law_probe_HEAD_2026-08-30.txt`):

- **L1 — equal standing.** From *"its absence confers no disadvantage"*: a prose
  and a formal survivor, equal on everything actually measured for both, must
  both be published.
- **L2 — kind-blindness.** From *"byte-identical whether or not the formal
  channel exists in the build"*: whether the prose one is published must not
  change when formally-backed siblings are present.
- **L3 — no weight in the other direction.** From *"may weight ranking ... on a
  conjecture's KIND"*, which is direction-neutral — note this clause is stricter
  than the headline sentence in CLAUDE.md, which only forbids the penalty on
  prose. A conjecture with nothing to check must not out-rank one that was
  checked and half-passed.
- **L4 — the axis still means something.** From your own question: *"checked and
  failed"* must still be beaten by *"checked and passed"*, or the repair has
  destroyed the axis rather than fixed it.

```
road               L1    L2    L3    L4
today (no change)  FAIL  FAIL  PASS  PASS
(a) not-measured   PASS  PASS  PASS  PASS
(b) neutral 1.0    PASS  PASS  FAIL  PASS
(b) neutral mean   PASS  FAIL  PASS  PASS
(c) disclose only  FAIL  FAIL  PASS  PASS
```

What that table says, in words:

- **Road (c) does not remove the disadvantage; it describes it.** It fails L1 and
  L2 for exactly the reason today's tree does, because road (c) *is* today's
  tree plus a note. Your law says absence of formal backing "confers no
  disadvantage", not "confers a disclosed disadvantage". So (c) cannot be the
  answer to a law violation on its own — though it is a perfectly good
  *addition* to a road that does remove it.
- **Road (b) trades one weight for another rather than removing it.** Scoring
  "nothing to check" at 1.0 makes it beat a formally-backed conjecture that was
  checked and half-passed (L3: the frontier it computes is `['prose']`, with the
  formal one gone). Your question was whether "nothing to check" should share a
  coordinate with "checked and failed"; road (b) answers it by making "nothing
  to check" share a coordinate with "checked and *fully passed*", which is the
  same conflation at the other end. The population-mean variant escapes L3 but
  fails L2 instead: its fill value is computed from how the *formal* conjectures
  in that same run happened to score, so whether a prose conjecture is published
  depends on the formal channel's contents — the exact thing "byte-identical
  whether or not the formal channel exists" forbids.
- **Road (a) is the only one of the three that passes all four.** A conjecture
  with nothing to check simply does not compete on that number: it is neither
  last nor first, it is absent. "Checked and failed" (L4) is still beaten by
  "checked and passed", so the axis keeps its discriminating power exactly where
  it has something to discriminate with.

**This narrows the fork; it does not close it.** Two things remain genuinely
yours to decide and are not law questions:

1. Whether you want the note from road (c) *as well* (answer `a+c`).
2. Whether you accept the two consequences of road (a) below.

## The two consequences of road (a) you should see before answering

1. **Runs with prose survivors can stop at a different cycle.** The frontier's
   size feeds `frontier_delta`, which is one of the inputs to the stop decision
   (`runtime/stop.py`, `frontier_delta_max` defaults to 0). A longer frontier
   means different deltas. This is a change to what *future* runs do; committed
   records are untouched and are never rewritten.
2. **A prose conjecture can now out-rank a formal one on a different number.**
   Not competing on coverage cuts both ways: if a prose conjecture scores higher
   on one of the other two numbers, the formal one can no longer defend itself
   with its coverage score. In both roots measured today the other two numbers
   are 0.0 for every survivor, so this is not reachable in any committed run —
   but it is reachable in principle, and you should hear it from me rather than
   from a run.

Not fixed here, and named so nobody thinks the class is closed: the other two
numbers (`hv` and `reach`) have the same 0.0-for-nothing-to-check shape. The
audit classified those as structural gaps rather than unlawful penalties, and
neither is measurable as a penalty in any committed run today.

## Recommendation

**Road (a), or `a+c` if you want the note too.**

The reason, in one sentence: (a) is the only road of the three that removes the
disadvantage instead of relabelling it or moving it, and it is the only one that
answers your own question — "should *nothing to check* and *checked and failed*
share a coordinate?" — with a clean **no** that does not immediately create the
mirror-image conflation at the top of the scale.

It is **built and parked, not integrated**, on branch `claude/b2-lane-C` as its
own clearly-labelled commit, with tests passing. Answering "a" is a merge.
Answering "b" or "c" discards that commit and costs a fresh tranche; nothing
about this lane's measurements or law analysis is wasted in that case, because
they apply to whichever road you pick.

---

Choosing between these is like deciding what to write in a form's box when the
question does not apply to you: road (b) writes "yes" because it looks
friendly, road (c) writes "no" and staples on a note explaining that the
question did not apply, and road (a) leaves the box blank — which is the only
one of the three that is true.
