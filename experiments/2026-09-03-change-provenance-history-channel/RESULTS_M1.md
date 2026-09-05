# M1 — does showing a conjecturer a problem's history change what it produces?

> **SUPERSEDED IN PART, 2026-09-05, by `RESULTS_M1_REPLICATION.md`.** The cost
> result below — the treatment spending 21.6% fewer tokens per admitted
> conjecture, called "the most interesting result" — did NOT replicate: it
> reversed to +23.4% in the third of three paired runs, which the
> pre-registered rule scores UNRESOLVED. The quality row, filled in on
> 2026-09-04 as "judged lower", is also superseded: the difference is a length
> effect and vanishes when length is held constant. Everything below is left as
> written. See `docs/ERRATA.md` E78 and E79 (minted as E75 and E76; renumbered at merge).

Answers R6 ("conjectures themselves usually have a long history, and
understanding that history might help LLMs craft better conjectures").

Predictions were registered in `PREREG.md` §1 before any arm launched and are
scored below **as written**, including the one that was wrong and the one whose
threshold turned out to be unusable.

---

## The arms as actually run

Both arms attach a history document; they differ only in whose history it is.
The channel is `reason --attach` rather than the scratchpad, because the
scratchpad cannot reach a multi-cycle run without production code (PARKED P6).
`PREREG.md` Amendment 4 records that change and its cost.

| | CONTROL (H0P) | TREATMENT (H1R) |
|---|---|---|
| attachment | history of an UNRELATED committed run (poietics), 2,603 bytes | history of THIS problem, 2,624 bytes |
| root | `run-ad41064484366337ed61a9d5a58de58f` | `run-f23da86ddfd5ab820957221cfebe4b2e` |
| terminal | completed, `budget_exhausted`, rc=0 | completed, `budget_exhausted`, rc=0 |
| cycles | 4 | 4 |

Same question, same model (`qwen3.5:397b`, `reasoning: none`), same config,
same home, one shared qualification. Run ids differ only because the dossier
digest differs, which is the intended behaviour and is what let one home hold
both arms.

## Results

Unit: the seed problem's admitted conjectures (C11), from
`measure_diversity_per_problem.py`.

| measure | CONTROL | TREATMENT | change |
|---|---|---|---|
| D1 conjectures | 43 | 42 | −1 |
| D2 schools | 4, largest 28% | 4, largest 29% | none |
| D4 lexical distinctness | 0.839 | 0.863 | **+2.9%** |
| D5 semantic distinctness | 0.147 | 0.179 | **+21.8%** |
| near-duplicate pairs | **1** of 903 | **0** of 861 | at floor |
| tokens spent | 541,666 | 414,536 | **−23.5%** |
| tokens per admitted conjecture | 12,597 | 9,870 | **−21.6%** |

## Scoring the registered predictions

**PRIMARY — "H1 lowers the near-duplicate rate": INCONCLUSIVE, and the
registered decision rule was the wrong instrument.**

The direction is right (1 near-duplicate pair → 0), and the rule as written —
"SUGGESTIVE if it exceeds 20% relative" — would score a 100% relative drop as
suggestive. That reading should be refused. The base is ONE PAIR out of 903.
Both arms sit on the floor of this measure, and a difference of one pair is
indistinguishable from noise at n=1. The rule was written without anticipating
a floor effect, and the honest report is that the primary measure could not
discriminate on this question. A question that produced more restatement would
be needed to test the anti-attractor claim on this measure at all.

**SECONDARY — "H1's per-problem D5 is HIGHER": HELD.** 0.179 vs 0.147, +21.8%
relative. D4 moves the same way (+2.9%), which is mild corroboration since the
two are computed by unrelated methods — D4 is deterministic token overlap, D5 is
neural embedding cosine.

**COST — "H1 spends MORE tokens per admitted artifact": FALSIFIED, and this is
the most interesting result.** The treatment spent **21.6% FEWER** tokens per
admitted conjecture (9,870 vs 12,597) and 23.5% fewer tokens overall. The
prediction's reasoning was that the attached section is pure prompt overhead,
so cost could only rise. It fell. The attachment is the same size in both arms,
so the difference is not in what was sent — it is in what the run did
afterwards.

Mechanism NOT established, and two readings survive:
  W — history genuinely shortens the work: a seat that can see what has already
      been refuted spends fewer calls re-deriving and re-attacking those lines;
  R — run-to-run variance. The two arms are single runs of a stochastic engine,
      and CLAUDE.md records that capability-channel use alone varies across
      identical runs.
Nothing here separates them. Distinguishing W from R needs repeated runs per
arm, which this tranche did not buy.

**QUALITY — no direction was predicted. MEASURED 2026-09-04; see
`RESULTS_M1_QUALITY.md`.** The paragraph below is left as written because it
was true when written and its reasoning still holds; the row it declares open
is now closed, and closed the other way from hope: the treatment's conjectures
were judged LOWER (mean 5.02 vs 6.58 of 15), suggestively rather than
demonstrably, on a panel that pays heavily for candidate length. What follows
is the original text.

**NOT MEASURED (as written 2026-09-03).**
The blind three-judge protocol (`JUDGING_PREREG_COPIED.md`) has not been run.
Its criteria, blinding and aggregation are committed and unchanged, so it can
be run later against predictions made before any candidate was read. Until it
is, **nothing here speaks to whether the conjectures are BETTER** — which is
the actual verb in R6. D4 and D5 measure spread, not merit, and the source
branch's own RESULTS.md already documents that a wide spread of off-topic
claims scores well on D5.

## What this shows

On this question, once: attaching a problem's own history rather than an
unrelated one produced conjectures that were **semantically more spread out and
cheaper per admitted artifact**, with no change in count or school
distribution, and with restatement already at floor in both arms.

## What this does NOT show

1. **n = 1 question, ONE run per arm.** No significance test is possible and
   none is implied. Every number above is a single paired observation.
2. **Nothing about quality.** See above. R6's "better conjectures" is
   unmeasured.
3. **Nothing about the channel SPEC.md designs.** History was delivered as
   attached EVIDENCE, which can ground a claim; the specified scratchpad
   channel is `advisory_non_grounding` and cannot. A positive result here
   licenses "history content changes what conjecturers produce". It does not
   license "the provenance channel works".
4. **Nothing about the anti-attractor rule (R8/S15) on its own terms.** The
   near-duplicate measure was at floor, so the shaping rule — show what died,
   withhold the winner — was exercised but not tested.
5. **The runs' own geometry was hashing-based** (PARKED P5): the harness's
   internal novelty and similarity used the zero-dependency embedder, while D5
   above is computed offline with the neural one. The two arms are affected
   identically so the comparison stands, but D5 measures a geometry the runs
   themselves never used.
6. **The treatment's own history came from a run of the same question** (the
   completed no-attachment control, root `fe00609058`). It is genuine prior
   history, not synthetic — but it is history of a sibling run rather than of
   the run being measured, which is what an offline prototype can produce.

## Residue worth one more measurement

The cost result is the one that would change a design decision if it held up,
and it is the one most likely to be variance. Two more runs per arm on the same
question would separate W from R for roughly the cost of M1 itself.
