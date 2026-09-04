# Results — does a blind critic perform better?

Answers the operator's question of 2026-09-04: *"Can you establish that a
blind critic, not judge, actually performs better?"*

**Short answer: no — not on this evidence, in either direction, for
either kind of blindness.** Both factors come out INCONCLUSIVE against
the rule fixed before any call. What the tranche did establish is
sharper than "no difference", and three of its findings are about the
instruments rather than about critics.

Everything below is computed from the typed record of 480 criticism
calls, sealed pre-registration
(`PREREG.sha256 3fbf7731ff93fa491fe9f6176a8a2b0cfe2349eeba0dd31df18a8a3399a2a7df`)
committed before the first call.

---

## The verdicts

### F1 — provenance labels: **INCONCLUSIVE**

Showing the critic the school and the author seat that produced the
target changes its hit rate on planted faults by nothing measurable.

| | labels OMITTED | labels PRESENT |
|---|---|---|
| planted faults named | 61 / 120 | 60 / 120 |
| rate | **0.508** | **0.500** |

    d1 = +0.0083   z = 0.13   p = 0.897
    McNemar on matched targets: 9 against 8, p = 1.0
    false attack: 1.000 both sides (saturated -- see below)

Against the rule (`d1 >= 0.20` AND `p < 0.05` AND `d2 <= 0.05`): the
threshold is missed by a factor of 24 and the test is nowhere near
significant. **INCONCLUSIVE**, and it is the strongest kind of
inconclusive available here — a flat null with 240 observations, not a
noisy one. If provenance exposure moves critic sensitivity at all, it
moves it by less than this design could see.

### F2 — prior-objection history: **INCONCLUSIVE**

Showing the critic what has already been objected to makes it find
fewer planted faults. The direction is the operator's own conjecture of
2026-09-03. The size is not enough.

| | history OMITTED | history PRESENT |
|---|---|---|
| planted faults named | 65 / 120 | 56 / 120 |
| rate | **0.542** | **0.467** |

    d1 = +0.0750   z = 1.16   p = 0.245
    McNemar on matched targets: 14 against 5, p = 0.066
    false attack: 1.000 both sides (saturated)

Against the rule: 7.5 points against a 20-point threshold, and p = 0.245
against 0.05. **INCONCLUSIVE.**

Stated plainly, because this is the number most likely to be
over-read: the matched-pairs split (14 targets where only the blind
critic caught the fault, against 5 the other way) is suggestive and its
paired p of 0.066 is close to conventional significance. The
deterministic detector, run first, put the same gap at 13.3 points with
an unpaired p of 0.034 and a paired p of 0.010. Both point the same way.
Neither clears the bar this tranche set for itself in advance, and the
bar is not being moved now that the numbers are visible.

---

## What the instruments say about themselves

Three measures could not have discriminated whatever the critics did.
Two of the three were predicted in the pre-registration; the third was
not, and it is the most useful finding here.

### The critic attacks everything — M2 is saturated

    C00 60/60   C10 60/60   C01 60/60   C11 60/60      rate 1.000

480 calls, 480 attacks. Every clean target and every planted target, in
every cell. The saturation rule fired as written, so the false-attack
clause of the verdict is unevaluable and every verdict above carries
that caveat.

This reproduces the record's own 2026-07-14 measurement — critic
objection rate 1.0 on clean and 1.0 on corrupted
(`experiments/results/court_calibration_v1_report.json`) — on a
different model, a different brief, a different domain and eighteen
months later. **That is now a twice-measured property of the
argumentative critic seat, not an artefact of one configuration.** Its
practical consequence for anyone measuring critics: "did it attack"
carries no information at all, and only "did it name the actual fault"
does.

### Nothing warranted — M3 is on its floor

    every cell: 120 calls, 120 attacks, 0 attack edges, ~120 scrutiny events

Predicted in advance: under observe-only authority an edge needs a
grounded counterexample, and none arose. M3 decides nothing, which the
pre-registration said before the run.

The check that matters is that the denominator is not the attack
relation itself: `attack_true >= att_edges` was asserted in every cell.
That is the defect that made the previous attempt at this question
undecidable, and it is closed here.

### The sharpness rubric cannot fail — M5 is a broken ruler

    C00 14.0   C10 14.0   C01 14.0   C11 14.0     (median of three, out of 15)

Four flat numbers, and they mean nothing. Of 1,436 individual
judgements:

| criterion | scored 3/3 |
|---|---|
| 1. specific rather than generic | **1436 of 1436** |
| 5. non-evasion | **1436 of 1436** |
| 2. the fault is real | 1427 of 1436 |
| 3. the case is made | 1430 of 1436 |
| 4. it is answerable | 563 of 1436 — the only one that moves |

Four of five criteria never once distinguished one criticism from
another. A rubric like that reports its own definition back, exactly as
the previous tranche's sustain rate did. **M5 is recorded as a failed
instrument, not as evidence that the four briefs produce equally sharp
criticism.** It did not enter either verdict; the pre-registration had
already ruled it out of them.

Worth saying about the criteria themselves: they were written for this
tranche, in advance, and they still failed. The failure is not
carelessness in wording — it is that a competent model's criticism is
specific, non-evasive, argued and aimed at a real fault essentially
always, so those four questions have no variance left to measure. A
sharpness instrument that works on this model has to ask something that
a good critic can still fail.

---

## Cost

Mean tokens per criticism call:

| cell | prompt | completion | total | brief bytes |
|---|---|---|---|---|
| C00 blind | 1187.5 | 1504.7 | 2692.1 | 2838.9 |
| C10 labels | 1230.5 | 1397.8 | 2628.3 | 3033.9 |
| C01 history | 1478.3 | 1588.0 | 3066.3 | 4315.6 |
| C11 both | 1526.7 | 1620.1 | 3146.7 | 4510.6 |

Showing history costs about 14% more tokens per criticism and, on both
detectors, buys fewer faults found. That is the only clause of this
tranche that points at a decision, and it points weakly.

---

## The decision this puts to the operator

**Nothing here justifies changing the default, and nothing here
justifies keeping it on evidence rather than on principle.** The
default critic exposure on main is unchanged by this tranche, as the
brief required.

If a decision is wanted anyway, the numbers support leaving both
blindnesses as they are:

- **Provenance stays omitted.** Not because it was shown to hurt — it
  was shown to do nothing — but because it costs tokens, it is the
  exposure the judge research says carries bias in the neighbouring
  seat, and nothing was found that it buys.
- **History stays omitted.** Both detectors put the informed critic
  behind the blind one, at 14% more spend. Neither result is
  significant at the bar this tranche set, so this is a
  "no reason to change" rather than a "reason not to".

The strongest practical finding is not about either factor. It is that
**the argumentative critic attacks everything it is shown**, twice
measured now, so any future work on critic quality has to measure what
the criticism SAYS. Measures over whether it attacked, or over the
attack relation, cannot see the phenomenon.

---

## Residue — what remains unproven

- **n = 1 model, 1 seat, 1 domain.** Everything here is glm-5.2
  criticising mathematical conjectures from five runs of two seed
  questions. Nothing establishes that another model behaves this way.
- **F1 varied a school label, not an origin.** Every target in the set
  was written by a conjecturer seat, so the origin line read the same on
  all 120 and only the school and seat name varied. An experiment where
  seed, harness-minted and capability-origin targets are all present
  would test something this one did not.
- **F2 tested prior-objection exposure, not rebuttal history.** The
  operator's F2 names "rebuttal + discharge history". Across every
  source root there are zero recorded discharges of any kind and zero
  landed objections. The record holds what was objected to and that
  nobody answered it. The half naming rebuttals could not be tested
  because it has never been written, in any run, by any configuration.
  Testing it needs a run whose conjecturers actually discharge.
- **The 2026-09-03 hypothesis is not settled.** "Criticism without fully
  understanding the reasoning behind a conjecture" is a wider claim than
  prior-objection exposure. The reasoning behind a conjecture — its
  support chain and its derivation — is empty on every artifact in this
  pool, so it could be neither shown nor withheld.
- **No no-harness baseline.** The 2026-09-03 law asks every live
  experiment to carry or cite an arm measuring what the model does
  WITHOUT the harness. This one compares four harness briefs against
  each other. It cannot say whether critic exposure makes the harness
  better than a single model call, only which of four briefs finds more
  of a known fault. The omission was recorded as a decision in PREREG
  section 9 before the run, not discovered afterwards.
- **Planted faults are not natural faults.** Six mechanical defect
  classes, deliberately visible on their own terms. Two classes were
  found almost never — scope-contradiction at 0.0-0.2 and
  vacuous-forbidden-case at 0.00 in every cell on the blind panel —
  which may say more about what a critic looks at than about the
  factors. A critic that never inspects the scope field or the
  counterconditions will miss a fault planted there regardless of what
  else its brief carries.
- **M2, M3 and M5 contributed nothing.** Three of the five registered
  measures could not discriminate. The verdicts rest on M1 alone.
- **The graders and the judges are the same model as the critic.**
  Three seeds are three readings, not three independent readers;
  correlated error stays correlated. The copied protocol says this about
  itself and it is true here too.

## Accepted does not mean true

Two inconclusive verdicts, one twice-measured property of the critic
seat, and one instrument recorded as broken. Nothing here was
established about whether a blind critic performs better. What was
established is that the question survives, that two of the three obvious
ways to measure it are saturated, and that the third — does the
criticism name the actual fault — works and is the one to keep.
