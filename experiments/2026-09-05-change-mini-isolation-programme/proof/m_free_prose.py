"""M: what does mini do TODAY with a free-prose candidate (no skeleton)?
This is the R2/R3 baseline: relaxed form + commitments off."""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, "mini")
from deepreason.invariants import verify_root
from minireason.call import MockEndpoint
from minireason.loop import run, Session
from minireason import checks

PROSE = ("A long free-prose conjecture with no JSON skeleton at all. " * 40)
print("prose chars:", len(PROSE))
print("compile_checks(prose) ->", json.dumps(checks.compile_checks(PROSE))[:200])
print("run_checks verdict    ->", checks.run_checks(PROSE, checks.compile_checks(PROSE)))

def _conj(*c):
    return json.dumps({"candidates": [{"content": x, "typicality": 0.5} for x in c]})

with tempfile.TemporaryDirectory() as td:
    n = {"i": 0}
    def fn(p):
        n["i"] += 1
        return _conj(PROSE + f" variant {n['i']}", PROSE + f" variant {n['i']}b")
    root = Path(td) / "prose"
    s = run([("pi-0", "why?")], MockEndpoint(fn), budget=200_000, root=root,
            vs_k=2, turnover_k=3, orbit_floor=3)
    print("summary:", {k: s[k] for k in ("stop", "cycles", "problems", "refuted", "gate_blocks")})
    v = verify_root(root)
    print("verify_root violations:", len(v["violations"]))
    st = Session(root).state
    print("survivors:", [a for a, p in st.addr if p == "pi-0" and a in st.accepted])
