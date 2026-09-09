"""Verdict census over every committed root: check-name multiset per root."""
import json, pathlib, sys, traceback
from deepreason.invariants import verify_root

out = {}
roots = sorted(
    str(p.parent) for p in pathlib.Path(".").rglob("log.jsonl")
    if ".git" not in p.parts
)
for r in roots:
    try:
        res = verify_root(pathlib.Path(r))
        out[r] = sorted(
            f"{v['check']}::{v['detail']}" for v in res.get("violations", [])
        )
    except Exception as exc:  # unreadable by this classifier
        out[r] = [f"ERROR::{type(exc).__name__}: {exc}"]
json.dump(out, open(sys.argv[1], "w"), indent=1)
print(len(out), "roots ->", sys.argv[1])
