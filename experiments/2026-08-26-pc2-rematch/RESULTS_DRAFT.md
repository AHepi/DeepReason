# RESULTS — P-C2, THE REMATCH

Dated honest-ledger segments. Every number comes from a typed artifact or
from the committed checker's exact-rational output. "Accepted does not mean
true."

---

## 2026-08-26 — [VERDICT SENTENCE PENDING ARM S2]

**[HEADLINE — filled when ARM S2 completes]**

| | ARM H2 (rebuilt harness) | ARM S2 (blind sampling) |
|---|---|---|
| best valid score | **0.0** | *pending* |
| exact | `0` | *pending* |
| measured tokens | **1 193 009** | *pending* |
| valid constructions | 37 (of 213 artifacts) / 69 (of 398 blob-level) | *pending* |
| provider calls | 135 | *pending* |
| terminal | `failed` / `operational_failure`, cycle 11 of 24 | *pending* |

**Every one of ARM H2's 37 valid constructions is collinear** — they obey
every rule and are worth nothing. ARM H2 never produced a single
non-degenerate construction. P-C1 produced exactly one (0.0004075); P-C2
produced none.

---

## The report card — which organ the rebuild fixed

PREREG §7's five metrics, each from the committed instrument, each against
its stated P-C1 baseline. `report_card.py --verify-against-pc1` reproduces
every baseline exactly on P-C1's own root, so the two columns are the same
measurement and not two definitions of one word.

| # | metric | P-C1 | P-C2 | |
|---|---|---|---|---|
| C1 | construction validity | 11.28 % (15/133) | **17.34 %** (69/398) | better |
| C2 | invented-handle rate | 2 of 77 wire failures | **0 of 37** | **eliminated** |
| C3 | coupling − placebo | +0.0587 | **−0.0049** | worse |
| C4 | budget on the operator's question | 53.2 % | **96.04 %** | far better |
| C5 | tokens per valid candidate | 46 853 | **17 290** | 2.7× cheaper |

Read organ by organ, because the headline hides all of this.

### F2 — the reference menus WORKED, and the effect is total

**Zero invented handles.** Not a reduced rate: none. P-C1's root had 2 of 77
wire failures from invented references; across the 54-root population F2 was
built for, invented handles were 62.6 % of every failure the record could pin
on a field — 737 of 1 178. P-C2 has 0 of 37. Wire validity is flat (87.67 %
→ 87.41 %), so the failures did not move elsewhere; that failure class is
simply gone.

### F3 — the wander cap WORKED, and it is the largest single number here

**The run spawned ZERO problems for itself.** P-C1 invented `audit:ritual`
— "audit the critic: adjudication-ritual flags sustained" — about two cycles
in, and spent **41.2 % of the operator's budget** on it, plus a
`disc:audit:ritual` child. W6's postmortem called that the line the loss
turned on. In P-C2 the corresponding figure is **0 calls and 0 tokens**, and
the share on the seed question rises 53.2 % → **96.04 %**. The remaining 3.96 %
is 12 repair re-asks, which carry no pack and therefore no problem line.

### F1 — the channel CARRIES criticism now, and the candidate still does not move

This is the honest split, and both halves are needed.

**It carries.** P-C1's motivating measurement was that criticism went
nowhere. P-C2's exposure figures against P-C1's, same instrument:

| | P-C1 | P-C2 |
|---|---|---|
| critic artifacts shown to a conjecture dispatch | 4 | **32** |
| mechanical criticisms shown | 2 of 345 (0.6 %) | **30 of 418 (7.2 %)** |
| critic-sourced items in conjecture packs | 47 | **1 460** |

Plus the channel's own Measures, which P-C1's record could not contain at
all: **1 568 `discharge-undischarged`** and **44 `discharge-reask`**.

**And it does not couple.** `CouplingRate − Placebo` is **−0.0049**: the rate
at which the next candidate answers the criticism is, within noise,
the rate a placebo predicts. NeglectRate is **92.1 %** (P-C1: 90.6 %).
Criticism arrives, 12–31× more often than before, and nothing measurably
moves.

**One measurement caveat, stated because it cuts against the finding I just
reported.** W2's exposure instrument joins on
`workflow-context-exposure-v2.exposed_items`, which names artifact
references. F1's channel renders open criticisms as a PACK SECTION with a
capped, truncated claim — not necessarily as an exposed item. The `1 460`
figure comes from the namespace rollup and the `30 of 418` from the
artifact-ref join, and the gap between them is probably that. So W2's
coupling instrument may be partially blind to the very channel F1 built, and
C3 should be read as "not detected by this instrument" rather than "did not
happen". PARKED.md records this as a defect against the instrument, not
against F1.

### THE FINDING OF THIS TRANCHE: the channel bought honesty by SURRENDERING the objective

Registered nowhere, and it is the most important thing the record says.

**All 37 valid constructions claimed exactly `0.0`, and all 37 claims were
confirmed.** Not one valid construction claimed a positive score.

P-C1's single most reproducible behaviour was claim inflation: **114 of 132**
constructions asserted a number the checker could not confirm, and the void
run repeated it at 147 of 183. That is what F1's channel was pointed at — an
inflated claim becomes a demonstrative refutation in-cycle, and the writer
must answer it.

**It worked, in the direction it was aimed, and the model complied by giving
up.** Faced with a refutation it could not argue with, it stopped claiming
more than it could prove — and reached honesty by placing three points on a
straight line and truthfully reporting a minimum triangle area of zero. Its
own submission says so in a `counterconditions` field, in its own words:

> "If the checker finds any collinear triple, the minimum area is 0 and this
> claim is honest"

That is not a model failing to understand the task. It is a model that
understood the task, found the criticism unanswerable, and satisfied it by
retreating to the one claim it could always defend.

The arithmetic behind "collinear" is exact and independent of the checker.
The best artifact's construction is the symmetric lattice; three of its
points sit on `y = 0`:

    A = (0, 0)   B = (1, 0)   C = (1/2, 0)
    cross = (1)*(0) - (1/2)*(0) = 0   =>   area = 0

30 of that construction's 286 triples are degenerate the same way, and its
smallest NON-zero triangle is 1/16 — so this is exact zero with a wide gap
above it, not a rounding artifact. Every coordinate is parsed as a
`Fraction` and a triangle's area is one cross product, so no float enters
anywhere.

The 168 candidates that still overclaimed were refuted (`CLAIM_INFLATED`).
So the population splits cleanly: **overclaim and be refuted, or claim zero
and be accepted.** Nothing in between was ever produced.

**What this means for the criticism design, stated plainly.** A demonstrative
refutation with no reward for improvement selects for the safest claim, not
the best construction. The checker punishes overclaiming and the floor
criterion punishes underperforming, but only the first is a REFUTATION the
writer must discharge; `frontier-above-floor@v1` fires 220 times and
discharges nothing, because a candidate that scores 0.0 honestly has already
answered the only criticism addressed to its claim. That asymmetry is a
design defect in this tranche's own battery, and it is PARKED, not fixed.

### A fourth finding nobody registered: the argumentative critics produced NOTHING

**`n_llm_attacks_total: 0`.** P-C1 recorded 110. All 418 of P-C2's criticisms
are MECHANICAL — checker verdicts. Every warrant on the record is
`demonstrative`/`fail` and there is not one of any other type or verdict, so
no seat ruled on anything anywhere, which is what PREREG §4 asked for. But
the argumentative critic seats, which were configured and paid for, wrote no
attack that reached the graph at all. Unregistered, so REPORTED not scored.

### Simulation and code-testing: available, and never used

No `exec-oracle@`, `candidate-checker@` or `property-oracle@` commitment was
ever registered; no capability Measure appears; `capability_events`,
`capability_requests`, `capability_executions` are all **0** in
`verify_root`'s own stats. F3 did turn the channels on — the compiled
manifest moves `research.enabled` false → true against P-C1's, which
`preflight_pc2.py` S4 recorded before launch. **The model did not reach for
them.** On a construction problem where writing and running a search program
is the obvious move, it wrote coordinates by hand 398 times.

---

## The typed failure, and why it is not new

`state: failed`, `stop_reason: operational_failure` at cycle 11 of 24,
`conjecturer.atomic-candidate.v1` — a route seat that exhausted its smallest
authorized contract. **This is the same typed death P-C1 hit at cycle 15**,
not a new one, and PREREG §10 registered in advance that the soak cannot
reach it. The soak states its own blind spot in its own output:

    [PART] D1-seat-contract   seat contracts exercised, but zero repair
           attempts: the deterministic stub always returns a schema-valid
           response, so attempt_index never advances past 0 offline

A stub that never gets it wrong can never drive a repair, and a seat only
exhausts a contract by repairing against it. `verify_root` reports **0
violations** over 3 751 events, so the record is well-formed and the failure
is typed rather than a crash.

**Does the early stop explain the result?** ARM H2 reached best = 0.0 and
stayed there; it never had a non-zero score to lose. Unlike P-C1 — which
reached 0.0004075 by cycle 10 and did not improve for five more — there is no
trajectory here to extrapolate. The honest statement is that ARM H2 did not
complete its registered 24 cycles, and a completed run remains unmeasured.

---

## Residue — what remains unproven

1. **[ARM S2 admissibility — pending]**
2. **No repeat was run.** PREREG §8 pre-authorized one. P-C1's residue says
   the same thing about P-C1, which means the loss is now unrepeated twice.
3. **ARM H2 never completed 24 cycles**, for the second time on this
   configuration, from the same cause.
4. **C3 may be under-measured.** See the caveat above: W2's exposure join may
   not see F1's pack section. The direction of the error is unknown.
5. **PREREG §9's honesty line stands, restated as required:** this run bears
   on but does not replace F1's parked four-arm criticism A/B. ARM H2 moved
   THREE organs at once plus deviation D1, so no result here attributes
   itself to any single organ; and without the VACUOUS-CRITIQUE arm a working
   critic cannot be told from argument-shaped text. P2 remains the proof this
   tranche is not a substitute for.
6. **F-A is not closed.** The discharge channel is on because a code default
   was changed, not because a configuration can select it. A run that wanted
   it OFF still could not say so.
7. **P-C1's parked P2 reproduces exactly.** `deepreason results` printed
   `tokens spent vs budget: 0 / 3000000` after 135 provider calls. Every
   token figure here comes from W6's flow scan over the log instead.
8. **NO_SURVIVOR_RECORD again.** The run failed before writing one, so this
   tranche says nothing about survivors — the same absence P-C1 recorded, for
   the same reason.
9. **Two defects of my own are in this tranche's history**, both fixed and
   both recorded in the commits: the ladder overwrote P-C1's committed
   preflight evidence, and I edited the ladder while it was running and
   killed it. No evidence was lost — the run had already terminalized — but
   the audit steps had to be re-run by hand.
