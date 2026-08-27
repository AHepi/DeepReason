# VERDICT — is prose penalised anywhere over formal conjectures and criticism?

The law names four outcomes. One is penalized, one is clean-but-hollow, two are
clean. Every verdict below points at a site or a count, never at a reading.

| the law's outcome | verdict | where |
|---|---|---|
| **admission** | **CLEAN** (with one gap, G4) | nothing reads kind to reduce admission; commitments are compiled from the PROBLEM's criteria |
| **rank** | **PENALIZED** | `scheduler/scheduler.py:216-234` × `capture/pareto.py:9` — the `coverage` Pareto axis |
| **criticism exposure** | **GAP** (and the gap runs against prose being TESTED, not against it surviving) | no mechanical criticism road exists for an artifact with no attack surface |
| **acceptance** | **CLEAN** (with one gap, G5) | `adjudication/grounded.py`, `adjudication/support.py` take ids and edges only |

Scale of the census behind them: 1 865 raw sweep hits over 26 terms → 1 143 in
executable code → **176 kind-reads**, every one rowed in `SITES.md`
(2 UNLAWFUL-PENALTY, 9 STRUCTURAL-GAP, 23 LAWFUL-PROTECTION, 142 NEUTRAL);
and **55 committed roots, 6 789 artifacts, 2 935 written candidates** in
`TABLES.md`.

---

## 1. Admission — CLEAN

**The load-bearing fact** (`workloads/models.py:101`, rowed NEUTRAL):

```python
commitments = [
    commitment_id
    for commitment_id in (*problem.criteria, *owned.commitments)
    if commitment_id in harness.commitments or commitment_id in drafts
]
```

An artifact's attack surface is compiled from **the problem's criteria plus
harness-owned mandatory commitments** — never from whether the model's writing
looked formal. Two candidates on one problem carry the same battery whatever
their prose looks like. There is no kind to read at admission because kind is
not yet a property of anything.

The one model-authored route that changes this — safe-skeleton compilation
(`workloads/models.py:142`) — only ever **ADDS**. And the two mandatory
well-formedness programs run the *anti*-formalism direction: `is_pure_code`
(`workloads/text.py:280`, `informal/skeleton.py:119`) FAILS a claim or
mechanism that is solely code. Prose is required; code alone is refuted.

**Record**: 2 935 candidates written across 55 roots, 2 575 minted — **87.7 %**.
Of those 2 935, **2** offered any formal backing of their own (`checker_specs`).
The candidate-side formal channel is available and essentially unused, so no
admission gap by candidate kind is measurable — and nothing in the code could
read one if it were.

**The opening case is answered.** P-C2b's dropped construction was not dropped
for being prose. It was the same kind as the four that were scored, and it was
lost to `token_budget_denied` inside an all-or-nothing decomposition. Full trace
in `EXEMPLARS.md`; parked as `PARKED.md` P1.

**G4, the one gap.** On the `reasoning.text.v1` workload,
`ReasoningCandidateProposal.counterconditions` is `min_length=1`: a candidate
must name at least one condition under which it would be false, or the wire
contract rejects it. What it must name is **prose** (`eval` defaults to
`observation`), so this forces an ENVELOPE, not a FORMALISM — but there is no
admission road on that workload for un-enveloped prose. The generic
`ConjectureCandidate.content` path has no such requirement.

---

## 2. Rank — PENALIZED

**F1.** `run_report` (`scheduler/scheduler.py:216-234`) scores every survivor on
`PARETO_AXES = ["hv", "reach", "coverage"]`, and `capture/pareto.py:9` keeps the
non-dominated set, **maximising every axis**:

```python
coverage = (sum(... == programs.PASS ...) / len(commitments)
            if commitments else 0.0)
```

`commitments` here is the artifact's **evaluable** commitments. An artifact with
none scores **0.0** on an axis a formally-backed sibling scores **1.0** on. If
they are otherwise equal, the formal one dominates and the prose one leaves the
frontier. And the frontier is not only a report: `frontier_delta` feeds
`StopMetrics`, so the axis touches when the run stops.

The law is explicit that this direction is forbidden: *"its absence grants no
disadvantage"*, and R-g names ranking.

**Reproduced**, `repro_coverage_rank.py`, exit 0, three legs:

- the axis arithmetic directly — `frontier` keeps `['formal']`;
- the real `scheduler.run_report` on a real root built with public
  constructors, no hand-set status — the prose survivor is absent from
  `report["frontier"]` and the formal one is present;
- a **mutation proof** — give the prose artifact one passing evaluable
  commitment and the drop disappears, so the coverage axis is what does it.

**Live footprint**, `experiments/2026-08-12-live-grounded-extension-expansion/run`:

| survivors | (hv, reach, coverage) | on the frontier |
|---|---|---|
| **146** prose conjectures | (0.0, 0.0, **0.0**) | **0 of 146** |
| **87** formal conjectures | (0.0, 0.0, **1.0**) | **87 of 87** |

Two score triples in the whole root. The frontier is exactly the 87. One
hundred and forty-six ACCEPTED, unattacked, prose conjectures are excluded from
that run's own answer, on one axis, for carrying no battery.

**But the effect is not general, and saying so is part of the finding.** Over
the 2 575 candidate-role artifacts pooled, prose is on the frontier at **36.7 %**
(92/251) against formal's **32.1 %** (747/2 324) — prose is slightly *ahead*.
Only **2 of 55 roots** carry conjectures of both kinds at once, and the other
one (P-C1 ARM H) runs the opposite way because all 163 of its formal
conjectures were mechanically refuted. So: the penalty is real, reproducible,
and has bitten hard once; it is not visible in aggregate because a conjecture
almost always inherits a battery from its problem, and where none does, its
rivals usually do not either.

Parked as `PARKED.md` P2.

---

## 3. Criticism exposure — GAP

**Nothing in the tree reduces a prose conjecture's exposure PROTECTION.** The
sockets are kind-blind by construction (`DR-CON-conjecture-kinds`'s own
re-derivable checks): `crit_program` is a data-driven no-op rather than a branch
that skips informal targets, and `crit_argumentative` runs on every target.
Every kind read here is the permitted direction — extra scrutiny on formal:
execution supremacy (`crit.py:1544`, `crit.py:2157`, `vision.py:91`), the
counterexample channel (`packs.py:200`, `packs.py:1050`), the counterexample
retry (`crit.py:1551`, `crit.py:2174`).

**The record nevertheless shows a large exposure gap, and it runs against
prose.** Candidate-role artifacts, all 55 roots:

| | formal (K1) | prose |
|---|---|---|
| attacked at least once | **550 / 2 324 (23.7 %)** | **8 / 251 (3.2 %)** |
| mean attacks received | 0.51 | 0.00 |
| carries a DEMONSTRATIVE warrant | 551 (all of them) | 0 |
| carries an ARGUMENTATIVE warrant | 0 | 8 |
| accepted | 76.3 % | **94.8 %** |

A prose conjecture in this record is roughly **seven times less likely to be
attacked at all**, and correspondingly more likely to be accepted. That is not
the law's penalty — it is the reverse — but it is not good news either, and the
scheduler's own comment names it: *"accepted-by-neglect is untested acceptance,
not corroboration."*

The cause is structural, not a rule: a DEMONSTRATIVE warrant needs a commitment
to fail, so an artifact with no attack surface has no mechanical criticism road
at all. That is **G6**, and the reconciliation ledger already states its
consequence in the operator's own worked example: *"For move 4 to be a program
verdict rather than a prose verdict, a premise artifact must carry a demarcation
criterion at registration"*
(`experiments/2026-08-14-change-calculus-reconciliation-v2/RECONCILIATION.md`).
Argument-alone refutation has no direct road; it is routed through an encoding.

**What a prose road would need**: a criticism channel that can register a
warrant against a target carrying no evaluable commitment, on evidence other
than a program verdict. One exists — the defended argumentative trial — and §4
below says why it almost never fires.

**C1, the audit's closest call, reported rather than buried.**
`Scheduler._standing_recrit_pool` (`scheduler.py:1396-1416`) returns
`backed + rest`: execution-oracle carriers queue FIRST for leftover-capacity
re-criticism. R-g's letter forbids weighting SCHEDULING on kind; D2 Amendment 1
re-anchored R-g to one direction and explicitly permits a formal conjecture
carrying MORE scrutiny, which is this direction, and the `_recrit_cursor`
rotation bounds the effect further. Classified LAWFUL-PROTECTION on that
authority. It is also the ONLY place in the tree that orders scheduling on
kind, and the count that makes it moot today is in §5: **zero** execution-backed
artifacts exist in the committed record, so this branch has never once fired.

---

## 4. Acceptance — CLEAN

The foundational computation cannot see kind, and the map proves it by
re-derivation rather than assertion:

```
python -c "import inspect; from deepreason.adjudication.grounded import label0;
 from deepreason.adjudication.support import final_labels;
 assert set(inspect.signature(label0).parameters) == {'nodes','att'};
 assert set(inspect.signature(final_labels).parameters) == {'label0','dep_edges'}"
```

Ids and edges. There is no parameter through which a commitment could reach it.
`formally_backed` (`informal/trial.py:920`) declines a prose case against a
formal target — protection, the direction the law allows — and does nothing at
all to an informal target. In the record, prose is accepted at **94.8 %**
against formal's **76.3 %**.

**G5, the gap on the other side.** For a prose case to reach a status it must
survive the defended cross-family trial, and both switches default to off:

```python
ADJUDICATION_STATUS_AUTHORITY_ENABLED: bool = False
# Demonstrative outcomes (counterexamples, program/verifier failures)
# remain status-changing under every mode.
ARGUMENTATIVE_AUTHORITY: ... = "observe_only"
```

A formal refutation always changes a status; a prose one changes none unless
the operator opts in, and then only through a judge ensemble. Measured:
**8 argumentative warrants against 551 demonstrative** across 6 789 artifacts —
prose criticism is **1.4 %** of the status-changing traffic.

This is a penalty on prose CRITICISM, which the standing law does not cover
(it speaks of conjectures) but the 2026-08-27 commissioning words explicitly do:
*"whether prose is penalised anywhere over formal conjectures **and
criticism**."* It is rowed as a GAP rather than a violation because the
asymmetry has a stated ground — a program verdict is deterministic and replays
byte-for-byte, a judge's ruling does not — and because the operator's own
2026-08-09 law is wary of judges (*"they prosecute without any discernable
discrimination"*). Naming the price is the audit's job; setting it is not.
Parked as `PARKED.md` P3, as an operator decision rather than a defect.

---

## 5. Three counts that reframe the whole question

- **Zero execution-backed artifacts exist in the committed record.** Across
  6 789 artifacts in 55 roots, not one carries a commitment in
  `oracle.EXEC_PROGRAMS`. Both prose-immunity guards, the execution-supremacy
  branches in `crit.py` and `vision.py`, the counterexample channel, and
  `_standing_recrit_pool`'s ordering are machinery that **has never fired in a
  committed run**. The strongest formal-protection surface in the tree has no
  live footprint at all.
- **Two of 2 935 written candidates offered any formal backing of their own.**
  The optional formal channel D2 built is, in practice, not taken.
- **Attention, allocation, wound counts, the discharge channel and the battery
  machinery contain no kind signal whatsoever.** Of 17 `wound`, 211 `attention`,
  96 `allocate`/`allocation`, 92 `discharge` and 66 `battery` lines in
  executable code, **zero** carry any of the audit's kind terms. Four of the
  outcome classes the brief asked about are clean by measurement, not by
  argument.

---

## 6. What this audit cannot settle

Stated here and again in `RESULTS.md`, because the numbers above are easy to
over-read.

A record census cannot separate a KIND effect from a CONTENT effect. Formal and
prose artifacts are not the same writing about the same thing: a battery-carrying
conjecture usually sits on a problem whose criteria are machine-checkable, and
such problems are harder, narrower and more attackable than the ones that draw
prose. Every gap in §3 is consistent with "prose was criticised less because the
problems that draw prose have no mechanical attack surface" and equally with
"the harness attacks prose less". The tables show which happened in the record;
they do not show why, and no census of this shape could.

What the code census CAN settle, it settles: F1 is a kind-conditional rank term
that exists in the tree today, reproduces on demand, and has excluded 146 real
prose conjectures from one real run's answer. That does not need a correlation
to be true.
