"""Re-score a committed root's Pareto artifact frontier under BOTH coverage
formulas, and check the shipped `pareto_scores` against the one it claims.

    python rescore.py <root> [<rows.json>]

READ-ONLY. The harness is opened `read_only=True`: a writable open REPAIRS a
root, which destroys the evidence a reader opened it to look at. Nothing here
writes to the root, and no committed root is modified by this tranche.

Both formulas are computed here from raw verdicts, so the before/after numbers
come from ONE run against ONE checkout and neither depends on which version of
`scheduler.pareto_scores` happens to be installed:

    OLD  coverage = passes / every EVALUABLE commitment   (OVERRUN counted as a
                                                           non-pass -- the defect)
    NEW  coverage = passes / every DECIDED commitment     (OVERRUN leaves; the
                                                           axis is OMITTED when
                                                           nothing was decided)

The shipped `pareto_scores` is then asserted to agree with NEW, which is what
makes this a verification rather than a re-statement.

Motivating roots (all three show the same shape):
  P-S1 9e48a36b1dec91ee  branch claude/deepreason-p-s1-commitments-wowcib
  P-A1 4565139800f5ca02  branch claude/live-reasoning-p-a1-bv65kl
  P-R1 experiments/2026-08-25-poietics-program/run  (on main)
"""
import collections
import json
import sys
from pathlib import Path

from deepreason import programs
from deepreason.capture.pareto import frontier
from deepreason.config import Config
from deepreason.harness import Harness
from deepreason.scheduler.scheduler import counts_as_survivor, pareto_scores

root = Path(sys.argv[1])
harness = Harness(root, read_only=True)
state = harness.state

addressed = collections.defaultdict(set)
for aid, pid in state.addr:
    addressed[aid].add(pid)


def problem_kinds(aid):
    kinds = sorted(
        {
            state.problems[p].provenance.trigger.value
            for p in addressed.get(aid, ())
            if p in state.problems
        }
    )
    return ",".join(kinds) if kinds else "(none)"


survivors = sorted({aid for aid, _ in state.addr if counts_as_survivor(state, aid)})
print(f"root: {root.parent.name}/{root.name}")
print(f"artifacts {len(state.artifacts)} | survivors {len(survivors)} | problems {len(state.problems)}")
print(
    f"hv entries {len(state.hv)} (nonzero {sum(1 for v in state.hv.values() if v)}) | "
    f"reach entries {len(state.reach)} (nonzero {sum(1 for v in state.reach.values() if v)})"
)

rows = []
for aid in survivors:
    artifact = state.artifacts[aid]
    verdicts, reasons, evals = [], collections.Counter(), collections.Counter()
    for cid in artifact.interface.commitments:
        if cid not in harness.commitments:
            continue
        commitment = harness.commitments[cid]
        if not programs.evaluable(commitment):
            continue
        verdict, trace = programs.evaluate(commitment, artifact, harness.blobs)
        verdicts.append(verdict)
        evals[commitment.eval] += 1
        if verdict == programs.OVERRUN:
            reasons[trace.get("reason") or trace.get("error") or "?"] += 1
    counted = collections.Counter(verdicts)
    passes = counted[programs.PASS]
    decided = passes + counted[programs.FAIL]
    base = {"hv": state.hv.get(aid, 0.0), "reach": state.reach.get(aid, 0.0)}
    old = dict(base) | ({"coverage": passes / len(verdicts)} if verdicts else {})
    new = dict(base) | ({"coverage": passes / decided} if decided else {})
    rows.append(
        dict(
            aid=aid,
            kinds=problem_kinds(aid),
            evaluable=len(verdicts),
            passes=passes,
            fails=counted[programs.FAIL],
            overruns=counted[programs.OVERRUN],
            old=old,
            new=new,
            shipped=pareto_scores(harness, aid),
            overrun_reasons=dict(reasons),
            evals=dict(evals),
        )
    )

# The point of the exercise: the installed code must implement NEW, not OLD.
mismatched = [r["aid"][:12] for r in rows if r["shipped"] != r["new"]]
agrees_with_old = all(r["shipped"] == r["old"] for r in rows) and rows
verdict_line = (
    "shipped pareto_scores == NEW (OVERRUN leaves the denominator)"
    if not mismatched
    else f"MISMATCH on {len(mismatched)} artifact(s): {mismatched[:5]}"
)
print(f"\ninstalled-code check: {verdict_line}")
if agrees_with_old and any(r["overruns"] for r in rows):
    print("  ...and it still matches OLD too -- this root cannot tell them apart")

axes = Config().PARETO_AXES
front_old = set(frontier([(r["aid"], r["old"]) for r in rows], axes))
front_new = set(frontier([(r["aid"], r["new"]) for r in rows], axes))
print(f"\nPARETO_AXES {axes}")
print(f"frontier BEFORE (OVERRUN penalised): {len(front_old)} of {len(survivors)}")
print(f"frontier AFTER  (OVERRUN excluded) : {len(front_new)} of {len(survivors)}")


def composition(members):
    return dict(collections.Counter(r["kinds"] for r in rows if r["aid"] in members))


print(f"  before -- on frontier {composition(front_old)}")
print(f"            dominated   {composition({r['aid'] for r in rows} - front_old)}")
print(f"  after  -- on frontier {composition(front_new)}")
print(f"            dominated   {composition({r['aid'] for r in rows} - front_new)}")

header = f"{'before':>7} {'after':>6}  {'artifact':<14} {'answers':<14} {'eval':>4} {'pass':>4} {'fail':>4} {'over':>4} {'cov-before':>11} {'cov-after':>10}"
print("\n" + header)
print("-" * len(header))
for r in sorted(rows, key=lambda r: (r["kinds"], r["aid"])):
    fmt = lambda s: f"{s['coverage']:.4f}" if "coverage" in s else "OMITTED"
    moved = "  <== MOVED ON" if r["aid"] in front_new and r["aid"] not in front_old else ""
    print(
        f"{'FRONT' if r['aid'] in front_old else '.':>7} {'FRONT' if r['aid'] in front_new else '.':>6}  "
        f"{r['aid'][:12]:<14} {r['kinds'][:13]:<14} {r['evaluable']:>4} {r['passes']:>4} "
        f"{r['fails']:>4} {r['overruns']:>4} {fmt(r['old']):>11} {fmt(r['new']):>10}{moved}"
    )

print("\nOVERRUN reason census (all survivors)")
census = collections.Counter()
for r in rows:
    census.update(r["overrun_reasons"])
for reason, n in census.most_common():
    print(f"  {n:>4}  {reason}")
if not census:
    print("  (none)")

if len(sys.argv) > 2:
    json.dump(rows, open(sys.argv[2], "w"), indent=1, default=str)
    print(f"\nwrote {sys.argv[2]}")

sys.exit(1 if mismatched else 0)
