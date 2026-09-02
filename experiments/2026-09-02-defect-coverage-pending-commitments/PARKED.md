# Parked — found during this tranche, deliberately NOT done

One tranche, one goal. Each entry is written for its future runner: what it is,
then a ready-to-send prompt. Starting the follow-up should cost a paste.

---

## P1 — a `predicate:` that RAISES is recorded FAIL, so a malformed predicate refutes its own artifact

**What.** `programs.py:558-559` catches any exception from a `predicate:` body
and returns `FAIL, {"error": str(e)}`. A predicate with a typo, a bad
comprehension, or a name the sandbox namespace does not carry therefore scores
as though the artifact's claim had been refuted — and unlike OVERRUN it stays in
the coverage denominator AND out of the numerator after this tranche's fix. The
comment calls this deliberate ("a predicate error is a failed verdict"), so it
is a design decision to revisit, not an obvious bug: the argument for it is that
an unrunnable predicate is the AUTHOR's failure to state a testable condition.
The argument against is that the harness cannot tell an author's typo from a
genuine refutation, and `rules/warrants.py` can mint a real `fail` warrant from
it. Not touched here because it is a different shape from "not measured": the
predicate WAS evaluated — it ran and threw.

**Ready-to-send prompt:**

```
EXECUTOR WINDOW — DEFECT TRANCHE: a predicate: commitment whose body raises is
recorded FAIL, so an author's typo is indistinguishable from a refutation

Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness and
dr-explain-to-operator. Start at dr-set-goal. Work on your window's assigned
branch; commit and push at every phase boundary.

THE QUESTION, FROM THE RECORD (record first, code second):
- programs.py:556-559 evaluates a `predicate:` inside a restricted namespace and
  converts ANY exception into `FAIL, {"error": str(e)}`. The comment says "a
  predicate error is a failed verdict" -- a deliberate choice, so this tranche
  must first establish whether it is still the right one, not assume it is not.
- Consequence chain to measure, not assert: a FAIL verdict is admissible to
  rules/warrants.py, which can mint a demonstrative warrant, which can drive an
  attack edge and a REFUTED status (DR-CON-warrants-and-attacks: no warrant, no
  edge, no REFUTED). If that chain is live, an author's typo can refute an
  artifact -- which is an EVIDENCE defect, not merely a ranking one, and a much
  stronger finding than the ranking case that parked it.
- Census first: over every committed root, how many predicate evaluations
  carried an `error` key in their trace, and did any of them reach a warrant?
  experiments/2026-09-02-defect-coverage-pending-commitments/rescore.py is a
  working read-only tabulator to adapt. If the answer is zero across every root,
  say so and re-bound: the tranche may be regression-risk, not defect.

GOAL (for dr-set-goal to bound -- ONE goal): decide, on the record, whether a
raised predicate is a refutation or an unobtained verdict, and make the code say
which. If it is an unobtained verdict it returns OVERRUN and leaves the coverage
denominator via the 2026-09-02 rule with no further change; if it stays FAIL,
the reason belongs in the docstring where the next reader will find it.

DESIGN CONSTRAINTS: whatever is decided must not weaken
tests/test_coverage_pending_commitments.py::test_fails_still_lowers_coverage --
a genuine failure must keep lowering coverage. Distinguish the two populations
before changing anything: a predicate that evaluates False (a real refutation)
from one that RAISES (no verdict obtained). Frozen surfaces: none expected;
programs.py is not frozen. Do NOT add a fourth verdict value --
docs/map/SEAM-evaluation-x-ontology.md:202 carries a check that forbids it.

OUT OF SCOPE: the coverage denominator itself (fixed 2026-09-02,
experiments/2026-09-02-defect-coverage-pending-commitments/); the OVERRUN
families; any live reasoning run.
```

---

## P2 — `hv` and `reach` still emit 0.0 for an unmeasured artifact

**What.** Not new, and not this tranche's. Already parked at
`experiments/2026-08-30-defect-formalism-rank-penalty/PARKED.md` L3 and rowed
STRUCTURAL-GAP by the 2026-08-27 audit;
`tests/test_formalism_optional_rank.py`'s `COMMITMENT_FREE_CAN_REACH_THE_FLOOR`
pins both as `True` deliberately. Re-listed here only because this tranche
measured the fact that made it newly relevant: on all three roots
`len(state.hv) == 0` and `len(state.reach) == 0`, so the 0.0 default was
universal and the two axes could break no tie. With `hv` measurable on v6 since
`5f34e4d00`, a run can now carry a measured `hv` for some artifacts and a
defaulted 0.0 for others — which is the shape `pareto_scores` handles by
OMITTING, and hv does not. **Left parked, deliberately: the owning tranche is
L3 and re-opening it here would be scope creep.**

---

## P3 — the problem POPULATION skew is a separate, unmeasured question

**What.** This tranche fixed how artifacts are RANKED. It says nothing about why
the harness minted 13 of P-A1's 14 problems and 1 292 of P-S1's 1 293 for
itself. Those are spawn-rule questions (`rules/` conn/disc/succ/debt), and the
frontier inversion is fully explained without them — the counterfactual moves
every dominated seed artifact onto the frontier with the problem population
untouched. Worth its own tranche; not evidence of a second defect until measured.

**Ready-to-send prompt:**

```
EXECUTOR WINDOW — AUDIT/DEFECT TRANCHE: the harness mints almost all of its own
problems, and nothing has measured whether that is right

Read CLAUDE.md fully, then load deepreason-orchestrator, dr-drive-harness and
dr-explain-to-operator. Start at dr-set-goal.

THE OBSERVATION, FROM THE RECORD: `deepreason --root <root> frontier` prints the
PROBLEM REGISTRY (cli/main.py:998-1004, help text "show the problem frontier"),
not the Pareto frontier -- read it as the population. P-A1
(4565139800f5ca02): 14 problems, 1 seed + 13 minted (8 research, 3 connection,
2 discrimination). P-S1 (9e48a36b1dec91ee): 1 293 problems, 1 seed. P-R1
(experiments/2026-08-25-poietics-program/run): 400 problems.

This is NOT the coverage defect -- that was diagnosed and fixed on
2026-09-02 (experiments/2026-09-02-defect-coverage-pending-commitments/), and
its counterfactual moved every dominated seed artifact onto the frontier with
the problem population left exactly as it is. So begin by establishing whether
there is a defect here AT ALL: a harness that mints many sub-problems while
pursuing one question may be working correctly. The falsifiable question is not
"are there many minted problems" but "did cycles spend on minted problems that
the operator's question needed spent on it" -- which is a BUDGET attribution
question, answerable from objects/workflow-work-preparation-v1 joined to
workflow-provider-attempt-v1 by problem_ref (dr-diagnose §3).

GOAL (for dr-set-goal to bound -- ONE goal): measure, per root, the share of
provider tokens spent on seed-descended vs harness-minted problems, and state
whether any documented guarantee is violated. If none is, this is a
capability-gap tranche that STOPS after FIX.md with a proposal, per dr-set-goal.

OUT OF SCOPE: the coverage axis (fixed); strict seed domination (separately
parked -- the seed question wins rank TIES today and that is deliberate);
reach's empirical zeros; any live reasoning run.
```

---

## P4 — `pyproject.toml` still declares neither `pytest-xdist` nor `jsonschema`

**What.** Hit again this session: a fresh container running only the documented
`pip install -e .` cannot run the documented gate. Already parked and priced at
`experiments/2026-08-30-change-execution-safety-parks/PARKED.md` S5, and
documented in CLAUDE.md's Environment section. Recorded here only as a third
sighting; **no new tranche proposed, the existing park owns it.**
