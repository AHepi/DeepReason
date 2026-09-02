"""Tabulate the ACTUAL Pareto artifact frontier of a committed root and the
per-artifact commitment verdict census the coverage axis uses.

READ-ONLY: opened read_only=True (a writable open repairs, i.e. destroys, the
evidence). The artifact -> problem link is state.addr, the addressing relation.
"""
import json, sys, collections
from pathlib import Path
from deepreason.harness import Harness
from deepreason import programs
from deepreason.capture.pareto import frontier
from deepreason.scheduler.scheduler import pareto_scores, counts_as_survivor
from deepreason.config import Config

root = Path(sys.argv[1]); out = sys.argv[2]
h = Harness(root, read_only=True); st = h.state

addr = collections.defaultdict(set)
for aid, pid in st.addr:
    addr[aid].add(pid)

def kind(pid):
    p = st.problems.get(pid)
    return p.provenance.trigger.value if p is not None else "?unregistered"

def kinds(aid):
    ks = sorted({kind(p) for p in addr.get(aid, ())})
    return ",".join(ks) if ks else "(none)"

survivors = sorted({aid for aid, _ in st.addr if counts_as_survivor(st, aid)})
print(f"root: {root.parent.name}/{root.name}")
print(f"artifacts {len(st.artifacts)} | survivors {len(survivors)} | problems {len(st.problems)}")
print(f"hv entries {len(st.hv)} (nonzero {sum(1 for v in st.hv.values() if v)}) | "
      f"reach entries {len(st.reach)} (nonzero {sum(1 for v in st.reach.values() if v)})")

rows = []
for aid in survivors:
    a = st.artifacts[aid]
    known = [c for c in a.interface.commitments if c in h.commitments]
    battery = [c for c in known if programs.evaluable(h.commitments[c])]
    verd, reasons, evals = collections.Counter(), collections.Counter(), collections.Counter()
    for c in battery:
        v, tr = programs.evaluate(h.commitments[c], a, h.blobs)
        verd[v] += 1
        evals[h.commitments[c].eval] += 1
        if v == programs.OVERRUN:
            reasons[tr.get("reason") or tr.get("error") or "?"] += 1
    rows.append(dict(aid=aid, kinds=kinds(aid), problems=sorted(addr.get(aid, ())),
                     n_commit=len(a.interface.commitments), n_battery=len(battery),
                     verdicts=dict(verd), evals=dict(evals),
                     overrun_reasons=dict(reasons), scores=pareto_scores(h, aid)))

axes = Config().PARETO_AXES
front = set(frontier([(r["aid"], r["scores"]) for r in rows], axes))
print(f"PARETO_AXES {axes} -> ARTIFACT FRONTIER: {len(front)} of {len(survivors)} survivors\n")

hdr = (f"{'front':<6} {'artifact':<14} {'answers-problem-kind':<22} {'batt':>4} {'pass':>4} "
       f"{'fail':>4} {'over':>4} {'coverage':>9}")
print(hdr); print("-"*len(hdr))
for r in sorted(rows, key=lambda r: (-(r["scores"].get("coverage") or -1), r["aid"])):
    v, cov = r["verdicts"], r["scores"].get("coverage")
    print(f"{'FRONT' if r['aid'] in front else '.':<6} {r['aid'][:12]:<14} {r['kinds'][:21]:<22} "
          f"{r['n_battery']:>4} {v.get('pass',0):>4} {v.get('fail',0):>4} {v.get('overrun',0):>4} "
          f"{('%.4f'%cov) if cov is not None else 'ABSENT':>9}")

print("\n=== OVERRUN reason census (all survivors) ===")
allr = collections.Counter()
for r in rows:
    for k, n in r["overrun_reasons"].items(): allr[k] += n
for k, n in allr.most_common(): print(f"  {n:>4}  {k}")

print("\n=== eval-spelling census over every battery commitment ===")
alle = collections.Counter()
for r in rows:
    for k, n in r["evals"].items(): alle[k] += n
for k, n in alle.most_common(): print(f"  {n:>4}  {k}")

print("\n=== composition by the problem kind each artifact ANSWERS ===")
print("  on frontier :", dict(collections.Counter(r["kinds"] for r in rows if r["aid"] in front)))
print("  dominated   :", dict(collections.Counter(r["kinds"] for r in rows if r["aid"] not in front)))

print("\n=== counterfactual: coverage with pending (OVERRUN) commitments removed from the denominator ===")
cf = []
for r in rows:
    v = r["verdicts"]; ev = v.get("pass",0)+v.get("fail",0)
    c2 = (v.get("pass",0)/ev) if ev else None
    cf.append((r["aid"], {**{k: x for k, x in r["scores"].items() if k != "coverage"},
                          **({"coverage": c2} if c2 is not None else {})}))
front2 = set(frontier(cf, axes))
print(f"  frontier AFTER: {len(front2)} of {len(survivors)}")
for aid, sc in sorted(cf, key=lambda t: t[0]):
    r = next(x for x in rows if x["aid"] == aid)
    was = "FRONT" if aid in front else "  .  "; now = "FRONT" if aid in front2 else "  .  "
    mark = "  <== MOVED ON" if (aid in front2 and aid not in front) else ""
    print(f"  {aid[:12]}  {r['kinds'][:20]:<21} before {was} cov="
          f"{('%.4f'%r['scores']['coverage']) if 'coverage' in r['scores'] else 'ABSENT':<8}"
          f" -> after {now} cov={('%.4f'%sc['coverage']) if 'coverage' in sc else 'ABSENT'}{mark}")

json.dump(rows, open(out, "w"), indent=1, default=str)
print(f"\nwrote {out}")
