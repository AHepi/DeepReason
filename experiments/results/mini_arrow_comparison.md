# Arrow of time: my answer vs MiniReason

A head-to-head on the chosen hard problem. All mini numbers are from live
runs committed alongside this file (`mini_arrow_report.json`,
`mini_arrow_survivors.md`, `mini_arrow_ranking.json`,
`mini_arrow_ranking_curated.json`).

## My answer (baseline)

The asymmetry is not in the laws but in a **boundary condition** — the
**Past Hypothesis** (the universe began in an extraordinarily low-entropy
macrostate). Time-symmetric dynamics + symmetric statistics cannot pick a
direction (Loschmidt/reversibility), so an asymmetric input is required;
the low-entropy past is it, and all arrows align downstream. The deep,
still-open core is *why* that initial state — sharpened by the fact that
gravity inverts entropy intuitions (smooth = low entropy), formalized by
**Penrose's Weyl Curvature Hypothesis**. My ranking of the *why*:
brute/law-like low-Weyl condition and selection-in-a-larger-structure lead;
pure inflation is insufficient alone. Decoherence gives a records arrow but
**inherits** its direction from the boundary condition.

## What mini generated

18 surviving conjectures (48 refuted, of which 45 were malformed-falsifier
rejections and 3 forbade-nothing — the v0 free-criticism signature). The
survivor set **covered my answer's full structure**: the Past Hypothesis
(#1), the Weyl-curvature / gravitational-entropy layer (twice, #13/#16),
the both-directions-from-a-fluctuation account (#5/#12, i.e. the
reversibility objection and the Carroll–Chen/Boltzmann rivals), and
inflation (#10) — plus decoherence, cosmological-horizon, memory, quantum-
tunneling, and black-hole-information accounts. Nothing major in my answer
was absent from what it proposed.

Generation invariants held on the live root: meter==log (38,641), byte-
replayable, parent `verify_root == []`.

## What mini's instrument ranked

Two gated tournaments (both control-gated valid):

**Diverse shortlist** (max-min distance, control gate 0.849): winner was
quantum **decoherence** (+3); speculative fundamental-law asymmetry last
(-3). Limitation: diversity-selection excluded the Past Hypothesis and
Weyl candidates from the bracket entirely.

**Curated quality bracket** (control gate 0.747) — the four leading
accounts head-to-head:

| rank | theory | Copeland | mean margin |
|---|---|---|---|
| 1 | quantum decoherence | +1 | +0.170 |
| 2 | Weyl-curvature / gravitational | +1 | +0.123 |
| 3 | probabilistic / both-directions fluctuation | -1 | -0.112 |
| 4 | Past Hypothesis (low-entropy initial condition) | -1 | -0.181 |

Nearly every pair tied; the only decisive edges were decoherence > fluctuation
(+0.51), Weyl > fluctuation (+0.30), and fluctuation > **Past Hypothesis**
(+0.48).

## Where we agree, where we diverge, and why

- **Agreement on the set.** Mini independently proposed every pillar of my
  answer, including the non-obvious gravitational/Weyl layer — twice.
- **Divergence on the ranking.** The instrument put decoherence and Weyl
  slightly ahead and rated the bare **Past Hypothesis lowest** — the
  opposite of my ordering.
- **Why (the honest read).** The judge scores the *written skeleton*
  against a rubric that rewards **confronting the reversibility objection**
  and **giving a mechanism rather than restating the phenomenon**. Mini's
  Past-Hypothesis skeleton was terse — it *asserted* the low-entropy
  boundary condition without spelling out the Boltzmann counting or
  rebutting Loschmidt in its own text — so it read as a restatement. The
  fluctuation and decoherence candidates explicitly engaged
  both-directions/reversibility and named a mechanism, and scored higher.
  This is the instrument rewarding **articulation quality of the artifact**,
  not adjudicating the physics — and by that standard its call is
  defensible: my own answer stresses that the Past Hypothesis is only
  compelling *once* paired with the reversibility rebuttal, which the bare
  skeleton omitted.
- **Field is genuinely close.** Ties dominated and margins were small, while
  the control gate (0.75–0.85) shows the instrument *can* discriminate
  sharply when quality differs. That it sees these four as near-comparable
  matches reality: they are all live positions in the literature.

## Takeaway

MiniReason, on a genuinely hard open problem, **reconstructed the full
solution space** a careful human answer lays out (including the subtle
gravitational-entropy insight) — but its calibrated *ranking* rewards how
well each conjecture is argued on the page, which is a different axis from
"which physical account is deepest." The lesson for the harness: the
generator is strong; the free mechanical criticism keys on falsifier
well-formedness (not substance); and the offline judge measures
articulation-against-rubric. Reading its "#1" as "the correct theory"
would over-read it — it is "the best-argued artifact in the bracket."


## Addendum: the full harness at 1M tokens (runs/arrow_full)

Same question, full machinery (live adversarial critic, defenders, 2-seat
trial protocol flash+pro, pairwise discrimination, schools, grounded
adjudication with reinstatement), hard 1M budget. Reports:
`arrow_full_report.json`, `arrow_full_frontier.md`.

What 12.5x the mini's budget bought:

- **A problem GRAPH, not a problem.** 224 problems (55+ spawned successors/
  discriminations); the mini grinds one prompt.
- **Substantive refutation.** 42 conjectures refuted, many by ARGUED cases
  (e.g. one Past-Hypothesis phrasing killed for asserting monotonic entropy
  increase, while a better-stated boundary-condition variant survived) —
  the exact capability the mini's free criticism lacks (it can only kill
  malformed falsifiers).
- **Filtered rubric verdicts.** 36 trial warrants at a 64% guard survival
  rate (13 ensemble splits, 3 paraphrase flips, 4 referential-integrity
  blocks): the trial protocol demonstrably discarded unreliable rulings.
- **A frontier that covers the field.** 20 accepted skeletons: Past
  Hypothesis (boundary-condition form), Weyl curvature, several
  decoherence/branching variants, CP violation, GRW/objective collapse,
  retrocausal two-boundary, anthropic selection, Boltzmann fluctuation —
  a superset of both the mini's survivors and my answer's pillars, with
  dependence links between related theories.
- **And the session's only invariant failure.** verify_root caught a
  10,022-token accounting delta — dedupe-swallowed decisive rulings (F4 in
  docs/MINI_STRESS_REPORT.md), fixed with regression tests the same day.
  The mini's three live runs all balanced to the token; the parent's
  richer registration paths hid one more leak class, found precisely
  BECAUSE the instrument exists.

Verdict across the three: my answer commits to a ranking the physics
community would recognize (Past Hypothesis + Weyl as the deep story); the
mini reconstructs the solution space cheaply but ranks articulation; the
full harness reconstructs the space MORE completely, criticizes it
substantively, and holds rivalries open where the evidence genuinely
doesn't discriminate - at 12.5x the cost and one uncovered accounting bug.
