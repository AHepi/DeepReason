# RESULTS — the formalism-optional audit

Tranche: `experiments/2026-08-27-audit-formalism-optional/`
Branch: `claude/formalism-optional-audit-mfdpdo`. Read-only on `src/` and `tests/`.
Route: `deepreason-orchestrator`. Commissioned 2026-08-27.

---

## 2026-08-27 — the answer, in four lines

**Prose is penalised in exactly one place, and it is not where the operator's
incident pointed.**

- **Admission: CLEAN.** An artifact's attack surface is compiled from the
  PROBLEM's criteria, never from how formal the model's writing was
  (`workloads/models.py:101`). There is no kind to read at admission.
- **Rank: PENALIZED.** The `coverage` Pareto axis scores an artifact with no
  evaluable commitment at `0.0`, so a formally-backed survivor dominates an
  otherwise-identical prose one and the prose one leaves the frontier. F1.
- **Criticism exposure: GAP.** Nothing reduces prose's exposure protection, but
  a demonstrative warrant needs a commitment to fail, so an artifact with no
  attack surface has no mechanical criticism road at all.
- **Acceptance: CLEAN.** The grounded extension takes ids and edges; there is
  no parameter through which a commitment could reach it.

The opening case — P-C2b's honestly-claimed construction that was written and
never scored — **was not a prose penalty**. It was lost to a token-budget
denial inside an all-or-nothing decomposition, and the four candidates that
were scored are the same kind of object as the one that was lost.

## What was measured, and how much of it

| instrument | scale |
|---|---|
| `sweep.py` — 26 kind/outcome terms over `src/deepreason` | 1 865 raw hits, 1 143 in executable code |
| `reduce.py` — kind signal in a boolean position | **176 kind-reads**, every drop reason machine-recorded |
| `classify.py` → `SITES.md` | 176 rows: 2 UNLAWFUL-PENALTY, 9 STRUCTURAL-GAP, 23 LAWFUL-PROTECTION, 142 NEUTRAL |
| `kind_census.py` → `KIND_CENSUS.json` | 55 roots read read-only, **6 789 artifacts**, 3 kind readings × 9 outcomes |
| `admission_census.py` → `ADMISSION_CENSUS.json` | **2 935 written candidates** vs 2 575 minted artifacts |
| `repro_coverage_rank.py` | F1 reproduced, 3 legs, one a mutation proof, exit 0 |

No sampling anywhere: `classify.py` exits non-zero if any kind-read is unrowed,
and `kind_census.py` records every root it failed to read (it failed none).

## F1 — the finding, and its live footprint

`scheduler/scheduler.py:216-234` × `capture/pareto.py:9`.
`PARETO_AXES = ["hv", "reach", "coverage"]`; `frontier()` maximises every axis;
`coverage` is `0.0` when the artifact's evaluable-commitment list is empty. So
absence of formal backing costs a Pareto coordinate, and the law says its
absence "grants no disadvantage". `frontier_delta` feeds `StopMetrics`, so the
axis also touches when a run stops.

In `experiments/2026-08-12-live-grounded-extension-expansion/run` there are
exactly two score triples among 233 survivors:

| survivors | (hv, reach, coverage) | on the frontier |
|---|---|---|
| **146** prose conjectures | (0.0, 0.0, **0.0**) | **0 of 146** |
| **87** formal conjectures | (0.0, 0.0, **1.0**) | **87 of 87** |

146 accepted, unattacked prose conjectures excluded from that run's own answer,
on one axis, for carrying no battery.

**And it does not generalise — which is part of the honest ledger, not a
softening.** Pooled over the 2 575 candidate-role artifacts, prose reaches the
frontier at **36.7 %** against formal's **32.1 %**: prose is slightly *ahead*.
Only **2 of 55 roots** carry conjectures of both kinds at once, and the other
one runs the opposite way because all 163 of its formal conjectures were
mechanically refuted. The penalty is real, reproduces on demand, and has bitten
hard once. It is not a pattern across the record.

## Three counts that reframe the question

- **Zero execution-backed artifacts exist in the committed record.** Not one of
  6 789 carries a commitment in `oracle.EXEC_PROGRAMS`. Both prose-immunity
  guards, the execution-supremacy branches, the counterexample channel and
  `_standing_recrit_pool`'s kind ordering are machinery that has **never fired
  in a committed run**. The tree's strongest formal-protection surface — the
  one the law explicitly permits — has no live footprint at all. Parked P5.
- **Two of 2 935 written candidates offered any formal backing of their own.**
  D2's optional formal channel is available and, in practice, not taken. So the
  admission comparison *by candidate kind* has no denominator on the formal
  side: no penalty for declining formality is observable, and none is ruled out.
- **Attention, allocation, wound counts, the discharge channel and the battery
  machinery contain no kind signal whatsoever** — 0 of 17 `wound`, 211
  `attention`, 96 `allocate`, 92 `discharge`, 66 `battery` executable lines
  carry any of the audit's kind terms. Four of the outcome classes the brief
  named are clean by measurement, not by argument.

## The exposure gap, which runs the other way

Candidate-role artifacts, all 55 roots:

| | formal (K1) | prose |
|---|---|---|
| attacked at least once | 550 / 2 324 (**23.7 %**) | 8 / 251 (**3.2 %**) |
| carries a DEMONSTRATIVE warrant | 551 | 0 |
| carries an ARGUMENTATIVE warrant | 0 | 8 |
| accepted | 76.3 % | **94.8 %** |

A prose conjecture in this record is roughly seven times less likely to be
attacked, and correspondingly more likely to be accepted. That is the reverse
of the operator's worry — prose is not being pushed out, it is being left alone
— but the scheduler's own comment names why that is not good news:
*"accepted-by-neglect is untested acceptance, not corroboration."*

On the criticism side the asymmetry is sharp: **8 argumentative warrants against
551 demonstrative** across 6 789 artifacts. A formal refutation changes a status
under every mode; a prose one changes none unless the operator switches judges
on. Parked P3 as an operator decision, not filed as a defect — the asymmetry has
a stated ground (a program verdict replays byte-for-byte, a judge's ruling does
not), and the operator's own 2026-08-09 law is wary of judges.

## The residue — what this audit cannot separate

Stated plainly, because the tables above are easy to over-read.

1. **A record census cannot separate a KIND effect from a CONTENT effect.**
   Formal and prose artifacts are not the same writing about the same thing. A
   battery-carrying conjecture usually sits on a problem whose criteria are
   machine-checkable, and such problems are narrower and more attackable than
   the ones that draw prose. Every gap in the exposure table is consistent with
   "prose was criticised less because the problems that draw prose have no
   mechanical attack surface" and equally with "the harness attacks prose less".
   The tables show what happened; they cannot show why, and no census of this
   shape could. **What the CODE census settles, it settles without a
   correlation**: F1 exists, reproduces, and excluded 146 real artifacts.
2. **Two of 55 roots is a thin base for any by-kind comparison.** The pooled
   frontier figures are dominated by roots that are entirely one kind, where no
   domination between kinds is even possible. The 36.7 % vs 32.1 % result should
   be read as "no penalty visible", never as "prose does better".
3. **The formal channel's non-use is measured, not explained.** Two candidates
   in 2 935 offered a checker. Whether models decline it because it is hard to
   author, because the pack does not surface it, or because prose is simply the
   natural register for these problems, this audit cannot say.
4. **`reach > 0` on 1 of 6 789 artifacts and a non-empty knowledge view on 1.**
   The STRUCTURAL-GAP rows that run through reach and the knowledge view are
   therefore almost entirely theoretical in cost today. They are rowed because
   the law's spirit says a gap must not quietly become a penalty, not because
   the record shows anyone being shut out of something others are reaching.
5. **`_standing_recrit_pool` was classified LAWFUL-PROTECTION on D2 Amendment
   1's authority, and that is a judgment call.** R-g's letter forbids weighting
   scheduling on kind; Amendment 1 permits a formal conjecture carrying more
   scrutiny. It is the only place in the tree that orders scheduling on kind. It
   is reported as the audit's closest call rather than buried in a NEUTRAL row,
   and the count in §"Three counts" makes it moot today — the branch has never
   fired.

**Accepted does not mean true.** The four verdicts are what 176 rowed sites and
6 789 rowed artifacts support. A site the sweep's 26 terms did not name is a
site this audit did not see; the terms are listed in `sweep.py` so the next
reader can widen them.

## Deliverables

| file | what |
|---|---|
| `GOAL.md` | the bounded goal, both operator texts verbatim, resolved map ids |
| `SITES.md` | all 176 kind-read sites, classified (generated) |
| `TABLES.md` | kind against outcome over the record (generated) |
| `EXEMPLARS.md` | the P-C2b dropped construction, traced end to end |
| `VERDICT.md` | the four named outcomes, with the site or the count for each |
| `PARKED.md` | five ready-to-send prompts (P1 the P-C2b defect, P2 the F1 penalty, P3 the prose-criticism decision, P4 the gap document, P5 the dead-or-unused census) |
| `sweep.py` `reduce.py` `classify.py` | the code census, re-runnable |
| `kind_census.py` `admission_census.py` `tables.py` | the record census, re-runnable |
| `repro_coverage_rank.py` | F1's reproduction, exit 0 = penalty present |
| `SWEEP_RAW.json` `KIND_READS.json` `KIND_CENSUS.json` `ADMISSION_CENSUS.json` | the raw measurements |

## Gate

Read-only, as commissioned. `git diff --stat origin/main` shows no file under
`src/` or `tests/`. No pytest gate owed (no code changed). No map document
moved, so `docs_verify` is not owed either.
