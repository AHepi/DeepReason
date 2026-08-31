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

- **It does not show the decision was made.** Road (a) is built and parked. The
  measurements and the law analysis survive an answer of "b" or "c"; the code
  does not. Dropping it is one act — `drop_road_a.sh` — and NOT one revert:
  `fe6b29ed2` holds the code, but two `docs/map/SUB-scheduler.md` `check:`
  lines that depend on it were added by the delivery commit `ce362b2e3`, so
  reverting `fe6b29ed2` alone leaves both RED. This segment claimed the
  single-commit version until a skeptic re-ran it; corrected 2026-08-30,
  evidence in `proof/drop_road_a_2026-08-30.txt`.

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
  `frontier_delta` is a `StopMetrics` input (`Scheduler._stop_metrics`, at the
  `frontier_delta=len(before["frontier"] ^ after["frontier"])` assignment;
  `runtime/stop.py:34/164`, `frontier_delta_max` defaulting to 0 — cited by
  symbol because the `scheduler.py:3003` this segment first carried was the
  PRE-fix line and was stale when written), so a run whose
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
  individually instead (SEVEN of them, all exit 0), and no `Verified-at:` stamp
  was advanced, because this lane did not re-run those documents' full check
  sets.

---

## 2026-08-30 (later the same day) — re-run by independent skeptics, and repaired

Reviewers who did not write this tranche re-ran its claims. **Two MAJOR defects
and six minor ones were confirmed, all in the TRANCHE'S OWN CLAIMS AND
INSTRUMENTS, none in the shipped behaviour of road (a).** Every one was
reproduced here before it was fixed; none was refuted. `DELIVERY.md` §11 holds
the finding-by-finding record.

**What the record shows.**

- The park was not droppable in one act. `git revert --no-edit fe6b29ed2` in a
  throwaway clone exits 0 and leaves two `docs/map/SUB-scheduler.md` `check:`
  lines RED (exit 4 and exit 1), because the delivery commit `ce362b2e3` that
  followed added a `pareto_scores` grep and a
  `tests/test_formalism_optional_rank.py` node id to them. Three documents
  claimed otherwise. Repaired by `drop_road_a.sh`, which removes both halves,
  refuses on a moved tree, and re-runs those two checks: after it,
  `docs/map/`, `src/` and `tests/` are byte-identical to the park base
  `736b50839` and both checks exit 0
  (`proof/drop_road_a_2026-08-30.txt`).

- A map Traps entry, and `capture/pareto.py`'s own docstring, blamed a guard
  that was dead code. Deleting `bool(shared)` leaves every attached check green
  (`5 passed`, exit 0), and an exhaustive enumeration over all 64 point shapes
  the three axes admit finds zero pairs where the guard changes the answer. The
  guard was deleted; the wording now names the STRICTNESS clause that actually
  carries the property, and the two mutations that turn the check RED were run
  BEFORE the sentence was written — `5 failed` and `3 failed`
  (`proof/pareto_mutation_2026-08-30.txt`).

- Both rings were re-run after the repairs: 117 + 129 = **246 passed, 0
  failed**, at load average 5.3 → 9.4 on a 4-CPU box.

- All SEVEN added-or-changed map `check:` lines were re-run verbatim from a
  mechanically enumerated diff: all exit 0
  (`proof/map_checks_2026-08-30.txt`).

**The residue this segment adds.**

- **`tests/test_mcp_run.py` is load-flaky, and no one has fixed it.** A reviewer
  measured `2 failed, 115 passed` in RING 1 under contention and reproduced the
  same failures on the PRE-FIX tree; this lane's two re-runs under comparable
  load were green, and the file alone is `7 passed`. Intermittent, not
  deterministic, and outside this lane's cone. Re-run those two node ids in
  isolation at fan-in before charging a red to any lane.

- **Two wrong statements survive in `fe6b29ed2`'s commit message** — the
  `scheduler.py:3003` pointer and the `bool(shared)` attribution — because
  editing a commit message rewrites the hash `STOP.md` hands the operator. The
  corrections live in the map, in `DELIVERY.md` §11, and here; the commit
  message cannot be corrected in place, and pretending otherwise would be worse
  than saying so.

- **The default fan-in action still integrates road (a).** A merge of this
  branch IS an answer of "a". This lane cannot decide that; what it can do, and
  now has done, is make the other answer cost one command instead of a repair
  tranche.

---

## 2026-08-30 — the park is closed, and the road is integrated

The operator answered `STOP.md` with one word: **"yes"**. Road (a) is no longer
BUILT AND PARKED; it is SHIPPED. `DELIVERY.md` §12 carries that answer as the
merge authority and states what it does and does not settle.

**What the record shows.** Re-measured on the INTEGRATED tree rather than
inherited from the lane branch, because the integrated tree is the one that
ships (`proof/INTEGRATION_2026-08-30.txt`):

| instrument | lane branch | integrated tree |
|---|---|---|
| the 11 red-before/green-after tests | 11 passed | 11 passed |
| MUTANT 1 — a fourth Pareto axis in `Config.PARETO_AXES` | 1 failed, 10 passed | 1 failed, 10 passed |
| MUTANT 2 — the penalty reintroduced on an empty battery | 4 failed, 7 passed | 4 failed, 7 passed |
| RING 1 — 12 files that recompute or consume a frontier | 117 passed | 117 passed |
| RING 2 — the stop-decision consumers | 129 passed | 129 passed |
| **ring total** | **246 passed, 0 failed** | **246 passed, 0 failed** |

Nothing was red on the integrated tree that was green on the lane branch, so
nothing was adapted, narrowed, or quietly repaired at the merge. Both mutants
were reverted before commit and the tree was clean.

`tests/test_mcp_run.py` — finding 6's load-flaky file — was GREEN here, on an
idle box running one instrument at a time. That is the condition finding 6 says
the file needs, so it confirms that diagnosis rather than refuting it; the
durable repair is still owed by a tranche that owns the file.

**The residue, unchanged by the answer.** Everything §10 records still stands:
`hv` and `reach` keep the same 0.0-default shape and were NOT fixed (parked as
L3 — do not read the coverage repair as having closed the class); this is a
BEHAVIOUR change that can move a run's stop cycle through `frontier_delta`, and
no live run has been performed to observe it; the recomputed frontier over the
2026-08-12 historical root now differs from the frontier that root stored, which
the 2026-08-14 operator law disposes of in advance and which moved no committed
byte; and the penalty does not generalise across the pooled record, where prose
was slightly AHEAD of formal.

**What the record still cannot settle**, and this is the honest close: whether
the 146 conjectures the old rule excluded were any good. What was wrong was that
they were excluded for their KIND. Accepted does not mean true, and neither does
"on the frontier".
