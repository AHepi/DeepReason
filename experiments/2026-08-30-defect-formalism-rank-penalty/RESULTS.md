# RESULTS — the coverage-axis formalism penalty

Honest-ledger segments. What the record shows, and the residue.

---

## 2026-08-30 — measured, narrowed, built, and PARKED

**What the record shows.**

The penalty the 2026-08-27 audit filed as finding F1 is live at this branch's
head. The committed reproduction
(`experiments/2026-08-27-audit-formalism-optional/repro_coverage_rank.py`, as it
stood before this tranche inverted it) exits 0 with "REPRODUCED": a prose
survivor and a formally-backed one that are equal on every axis the harness
measured for both, and the prose one is dropped from `run_report`'s frontier.
Its mutation control fires correctly — give the prose artifact one passing
evaluable commitment and the drop disappears — so the exclusion is the coverage
axis and nothing else.

The live footprint the audit reported was re-derived independently rather than
inherited, read-only, through the shipped `run_report`
(`measure_footprint.py`, output at `proof/footprint_2026-08-30.txt`):
`experiments/2026-08-12-live-grounded-extension-expansion/run` has **233**
survivors in **exactly two** score triples — **146** at `(0.0, 0.0, 0.0)`, every
one of them carrying no evaluable commitment, and **87** at `(0.0, 0.0, 1.0)` —
and the published frontier is **exactly those 87**, equal to the frontier stored
in that root's `run-result.json`, with **zero** of the 146 on it. The audit's
numbers are CONFIRMED in every particular. The control root
`experiments/2026-08-25-poietics-program/run` has 58 survivors, **0** with an
empty battery, and a frontier of 40 that no road moves.

**The fork was not resolved, and that is the point.** P2's own brief opens
"OPERATOR DECISION NEEDED FIRST, then the change" and routes itself to the
change family rather than a defect family, "-- the operator decides what
coverage should mean". This lane measured the question, narrowed it by law,
built the road it recommends so that a "yes" costs a merge, and parked the
choice in `STOP.md`, which is answerable with one word.

**What the law settles, and what it does not.** Four probes, each derived from a
quoted clause of `DUAL_MODE_CONJECTURE_PREPLAN.md` R-g, run against all three
priced roads (`road_law_probe.py`). Road (c) fails two of them for exactly the
reason today's tree does — it is today's tree plus a note, and a road that
changes no behaviour cannot remove a behavioural penalty. Road (b) at 1.0 fails
the direction-neutral clause: it makes "nothing to check" out-rank a formally
backed artifact whose battery half-passed, which is the same weight with its
sign flipped. Road (b) at the population mean fails the byte-identity clause
instead, because its fill value is computed from how the formal channel scored
in that same run. Road (a) passes all four. **That narrows three roads to one;
it does not close the decision**, because whether to add road (c)'s disclosure
on top, and whether the two disclosed consequences are acceptable, remain the
operator's and are not law questions.

**What was built, and parked.** Commit `fe6b29ed2`, subject line beginning
"BUILT AND PARKED, NOT INTEGRATED". `scheduler.pareto_scores` (new) OMITS an
axis the harness did not measure; `capture.pareto.frontier` drops an axis absent
from either point out of that pairwise comparison instead of reading it as 0.0.
Eleven tests in `tests/test_formalism_optional_rank.py`, proven red before
(4 failed / 6 passed, the 6 being the controls) and green after; both
architecture tests mutation-proven with source mutants built in the scratchpad.
Ring: **246 passed, 0 failed across 18 files.** Frozen surfaces: none — three
instruments agree, and `blast_radius.py`'s `CONTACT` verdict was run down to a
name collision (the word "frontier" is also a model-profile tier in
`run_manifest.py` and `invariants.py`).

**Site (b) = P3 was NOT implemented and NOT designed.** Its own brief files it
as "an operator decision, not a defect" and says "do not design before it is
answered". It is carried forward verbatim in `PARKED.md` L2, with two
corrections its next runner would otherwise have to re-derive: `trial.py`'s
`formally_backed` call has rotted from `:920` to `:963`, and the 2026-08-09
judge caution quoted inside P3's own question was AMENDED by the operator on
2026-08-28 on the record's own evidence — so the question as written quotes
superseded authority and must be put to the operator beside the amendment.

---

### The residue — what this does NOT show

- **It does not show the decision was made.** Road (a) is built and parked. If
  the operator answers "b" or "c", commit `fe6b29ed2` is discarded. The
  measurements and the law analysis survive that outcome; the code does not.

- **It does not show the 146 excluded conjectures were any good.** The finding is
  that they were excluded for their KIND, not that they deserved to be
  published. Accepted does not mean true, and neither does "on the frontier".

- **The penalty does not generalise across the record, and this tranche did not
  re-derive the aggregate that says so.** The audit's own residue
  (`VERDICT.md:106-114`) measured prose on the frontier at 36.7% (92/251) against
  formal's 32.1% (747/2 324) over 2 575 pooled candidate-role artifacts — prose
  slightly AHEAD. That is quoted, not re-measured here. The case for the repair
  is the code fact plus the one root where it bit hard; it was never an
  aggregate, and it must not be reported as one.

- **This is a behaviour change and no live run has observed it.**
  `frontier_delta` is a `StopMetrics` input (`scheduler.py:3003`,
  `runtime/stop.py:34/164`, `frontier_delta_max` defaulting to 0), so a run whose
  survivors include commitment-free artifacts publishes a longer frontier AND can
  stop at a different cycle. That is derived from the wiring and DISCLOSED; it is
  not measured. No live run was launched by this lane.

- **Historical roots' recomputed frontiers move, and their stored ones do not.**
  After the change, recomputing
  `experiments/2026-08-12-live-grounded-extension-expansion/run`'s frontier gives
  233 where its `run-result.json` stored 87. Under the 2026-08-14 operator law
  ("old runs do not need to be valid or returnable") this is not a defect, and
  P2's brief said so in advance. **No committed root's bytes were modified**;
  both roots were opened `read_only=True`.

- **Only two roots were measured**, deliberately: the root sweep is retired
  (operator ruling 2026-08-22). One is the root the brief names as the live
  footprint; the other is the root a test pins. A third root could still hold a
  shape neither shows.

- **The axis family was not closed.** `hv` and `reach` still emit 0.0 for an
  unmeasured artifact and enter the same maximising frontier. In both roots
  measured, both are 0.0 for every survivor of both kinds, so no penalty is
  measurable through them today — but a run in which a formally-backed artifact
  earns `hv > 0` reproduces the same domination on a different axis. Parked as
  `PARKED.md` L3. Do not read the coverage repair as having closed the class.

- **Road (a) cuts both ways.** Not competing on coverage also means not defending
  with it: a prose artifact scoring higher on `hv` can now dominate a formal one
  whose coverage is 1.0. Unreachable in either committed root (all `hv`/`reach`
  are 0.0), reachable in principle, and stated in `STOP.md` as consequence 2
  rather than left for a run to find.

- **The full gate and `docs_verify` were not run by this lane.** Ring only, per
  the batch's load rule — four lanes on a 4-CPU box, and a measurement taken
  under load is not a measurement. Each new or changed map `check:` was run
  individually instead (all six exit 0), and no `Verified-at:` stamp was
  advanced, because this lane did not re-run those documents' full check sets.
