"""Check 10, record arm (read-only): do several conjecturer samples on one
problem register as COMPATIBLE artifacts, or does registration itself create
exclusivity?"""
import sys, collections, pathlib
from deepreason.harness import Harness
from deepreason.ontology.state import Status

root = pathlib.Path(sys.argv[1])
h = Harness(root, read_only=True); st = h.state
by_problem = collections.defaultdict(list)
for aid, pid in st.addr:
    by_problem[pid].append(aid)
att_targets = collections.Counter(t for _, t in st.att)
print(f"root                       : {root}")
print(f"artifacts                  : {len(st.artifacts)}")
print(f"problems with >1 artifact  : {sum(1 for v in by_problem.values() if len(v) > 1)}")
rows = sorted(by_problem.items(), key=lambda kv: -len(kv[1]))[:5]
print(f"{'problem':<44} {'n':>4} {'accepted':>9} {'refuted':>8} {'attacked':>9}")
for pid, aids in rows:
    acc = sum(st.status.get(a) == Status.ACCEPTED for a in aids)
    ref = sum(st.status.get(a) == Status.REFUTED for a in aids)
    atk = sum(att_targets.get(a, 0) > 0 for a in aids)
    print(f"{str(pid)[:44]:<44} {len(aids):>4} {acc:>9} {ref:>8} {atk:>9}")
print()
print("Exclusivity test: is any artifact attacked WITHOUT a registered warrant "
      "naming it (i.e. does mere co-presence on a problem create an edge)?")
warranted = {w.target for w in h.warrants.values()}
unwarranted = {t for _, t in st.att if t not in warranted}
print(f"  attack edges           : {len(st.att)}")
print(f"  warrant targets        : {len(warranted)}")
print(f"  attacked-but-unwarranted targets: {len(unwarranted)}")
