#!/usr/bin/env python3
"""Render PREREG_LEG2.md from calibration_leg2.json.

The calibrated numbers appear in the pre-registration exactly as the
calibration produced them; no number is retyped, so the frozen document and
the committed calibration artifact cannot drift apart."""
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
c = json.loads((HERE / "calibration_leg2.json").read_text())
tau2, linkage = c["tau2"], c["linkage"]
sens = [round(tau2 - 0.02, 4), tau2, round(tau2 + 0.02, 4)]
grid = sorted({round(tau2 + d, 4) for d in (-0.04, -0.02, 0.0, 0.02, 0.04)})
ls = c["linkage_scores"]

TEXT = f"""# PREREG — LEG 2: the same experiment with a metric that can measure it

**Frozen 2026-08-28, before any leg 2 provider call.** Committed and pushed
before `raw_leg2/` contains a single response. Same standing as PREREG.md:
nothing below may be edited after the first leg 2 call, only appended to as a
dated appendix.

---

## §1 — Why there is a second leg

Leg 1 ran as registered and its result stands, including the part that went
wrong. Its primary counter **M1 saturated**: at the frozen τ\\* = 0.7454 with
single linkage, nearly every cell reported ONE cluster, for every arm.

The cause is diagnosed, not guessed. τ\\* was calibrated on paragraphs drawn
from DIFFERENT documents. Sixty conjectures answering ONE question sit in a
far tighter similarity band than that, and single linkage joins transitively:
each candidate bridges to the next until the cell fuses. The instrument was
wrong for the regime, and the fault is the instrument's — leg 1's own
registered τ curve and its threshold-free M2 both separate the arms cleanly
at the same time as M1 reports nothing.

**Leg 1 is not re-scored.** Applying a better metric to the data that
diagnosed the metric's flaw would be tuning an instrument on the very
measurements it is about to judge. Leg 1 calibrates; leg 2 measures, on data
that does not exist yet at the moment this file is frozen.

## §2 — What changes, and what does not

**Changes — exactly one thing.** M1's clustering rule.

| | leg 1 | leg 2 |
|---|---|---|
| threshold | τ\\* = 0.7454 | **τ₂ = {tau2}** |
| linkage | single | **{linkage}** |
| calibrated on | paragraphs from 40 committed `docs/*.md` | **leg 1's own candidates** |
| label used | paragraph-vs-subsample, and same-document pairs | **the named direction each B/D candidate was generated under** |

**Does not change.** Generation is IDENTICAL, and by construction rather than
by care: leg 2 runs `driver.py` unchanged with `--root raw_leg2`, so the
arms, the verbatim prompts, the three frozen question strings and their
digests, the sampling configuration (temperature 0.9, top_p 0.95,
`reasoning_effort: "none"`), the 60-candidate target, the 40,000-token cell
cap, the one-retry-on-transport-error rule and the no-top-up rule are the
same code path that produced leg 1. M2 and M3 are unchanged. §7's four
hypotheses, their SUPPORTED/REFUTED rules and the 3-cluster effect floor are
unchanged. The binding rule on self-reported probabilities is unchanged and
still enforced by the mutation-proven AST guard.

**Repetitions: 9**, matching leg 1 under its Appendix A. 108 cells.
**Envelope: 1,440,000 tokens**, the same ceiling leg 1 registered; leg 1
measured ≈1.1M at this shape, so the ceiling is not expected to bind.

## §3 — How τ₂ and the linkage were chosen (leg 1 data only)

`calibrate_leg2.py`, output `calibration_leg2.json`, committed with this
file. The label is one the experiment already contains and no model supplied:
**arms B and D generate every candidate under a named direction** from that
cell's own planning call. Two candidates from the same direction are a
same-family pair; two from different directions of the same cell are a
different-family pair. These are labelled pairs in exactly the regime the
metric must work in — candidates answering one question — which is precisely
what leg 1's calibration lacked.

Source: **{c['labelled_cells']} labelled cells**, {c['source']}.

| class | n pairs | p10 | median | p90 |
|---|---|---|---|---|
| same direction | {c['same_direction_pairs']['n']} | {c['same_direction_pairs']['p10']:.4f} | {c['same_direction_pairs']['median']:.4f} | {c['same_direction_pairs']['p90']:.4f} |
| different direction | {c['different_direction_pairs']['n']} | {c['different_direction_pairs']['p10']:.4f} | {c['different_direction_pairs']['median']:.4f} | {c['different_direction_pairs']['p90']:.4f} |

**τ₂ = {tau2}**, the cut maximizing Youden's J on those pair labels
(J = {c['youden_J']:.4f}, TPR {c['tpr']:.4f}, FPR {c['fpr']:.4f}). Chosen
linkage-free, so the threshold does not presuppose the joining rule.

**Linkage = {linkage}**, chosen at τ₂ by the adjusted Rand index between the
clustering each linkage produces and the direction partition:

| linkage | mean adjusted Rand | mean clusters per cell |
|---|---|---|
""" + "".join(
    f"| {'**' if k == linkage else ''}{k}{'**' if k == linkage else ''} | "
    f"{ls[k]['mean_adjusted_rand']:.4f} | {ls[k]['mean_clusters']:.2f} |\n"
    for k in ("single", "complete", "average")
) + f"""
**Honest limit, registered where it is made.** A direction label is a PROXY
for idea identity: two candidates inside one direction can still be genuinely
different ideas, so the same-family class is contaminated by construction.
The effect is conservative — τ₂ will under-split rather than over-split — and
it is a limit on how finely leg 2 can resolve distinctness, not a thumb on
any arm's side of the scale, because every arm is scored by the same rule.
A second limit: the label exists only in the stratified arms, so the
calibration set is drawn from B and D. It is used to fix a rule applied
identically to all four arms, never to score an arm.

## §4 — Metrics

**M1** = number of clusters at τ₂ = {tau2} under {linkage} linkage, over the
cell's valid candidates. Reported at **M1@Nmin** (adjudicating) and
**M1@60** (beside it), Nmin being the smallest valid-candidate count across
leg 2's 108 cells, subsample taken by candidate-id ascending.

**Sensitivity, registered:** τ₂ ± 0.02 = {sens[0]} / {sens[2]}. A hypothesis
counts as SUPPORTED only if its ordering holds at all three of
{sens[0]}, {tau2}, {sens[2]}. Full grid reported: {grid}.

**M2**, **M3** and the M3 failure codes: unchanged from PREREG.md §6.

**BINDING, unchanged:** self-reported probability values never enter any
metric, rank, filter, or ordering. `analyse2.py` runs the AST guard over both
its own source and `analyse.py`'s before computing anything.

## §5 — Hypotheses

Unchanged from PREREG.md §7 — H1 (B > A), H2 (C > A), H3 (D ≥ B and D ≥ C),
H4 (C's yield does not degrade by more than 5 percentage points over A) —
with the same SUPPORTED/REFUTED conditions and the same 3-cluster effect
floor, now evaluated at τ₂ under {linkage} linkage over 9 repetitions.

## §6 — Registered null result

Unchanged in form: if the four arms' M1@Nmin values all fall within 3
clusters of each other at τ₂, this instrument detected nothing, and that is
the finding — not rescued by moving τ₂, changing the linkage, or adding arms.
Leg 1 has already shown this experiment is willing to record an instrument
failure rather than repair one.
"""

(HERE / "PREREG_LEG2.md").write_text(TEXT)
print(f"PREREG_LEG2.md written: tau2={tau2} linkage={linkage}")
