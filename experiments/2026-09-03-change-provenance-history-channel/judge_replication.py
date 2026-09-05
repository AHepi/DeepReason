"""Blind judging of the REPLICATE candidates (PREREG.md Amendment 5).

A separate blind set and a separate keymap from `blind/`, for the reason the
amendment gives: the first keymap is open, and a measurement whose key is
already open is not blind. This one stays shut until `blind-r/scores.json` is
written and its digest sealed.

NOTHING ABOUT THE PROTOCOL IS RE-DECIDED HERE. The criteria text, the judge
call, the three-judge count and the median aggregation are IMPORTED from
`judge.py` rather than copied, so they cannot drift by a character between the
first set and this one. If that import ever fails, the right response is to
fix the import, never to paste the criteria in.

Usage:
    judge_replication.py harvest   # 4 replicate roots -> blind-r/
    judge_replication.py score     # 3 judges per candidate -> blind-r/scores.json
    judge_replication.py reveal    # requires scores.json; joins the keymap
"""

from __future__ import annotations

import json
import pathlib
import statistics
import sys
import time
import uuid

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from judge import CRITERIA, JUDGES, _ask, _key  # noqa: E402  the point is reuse

BLIND = HERE / "blind-r"

# The two replicate pairs. Run ids repeat across homes by design (determinism),
# so the home is what names an arm here, never the id.
ARMS = {
    "R2-H0P-control": "runs/home-m1-r2/runs/run-ad41064484366337ed61a9d5a58de58f",
    "R2-H1R-history": "runs/home-m1-r2/runs/run-f23da86ddfd5ab820957221cfebe4b2e",
    "R3-H0P-control": "runs/home-m1-r3/runs/run-ad41064484366337ed61a9d5a58de58f",
    "R3-H1R-history": "runs/home-m1-r3/runs/run-f23da86ddfd5ab820957221cfebe4b2e",
}


def harvest() -> int:
    from measure_diversity_per_problem import conjectures, _seed_problem

    BLIND.mkdir(exist_ok=True)
    rows, keymap = [], {}
    for arm, rel in ARMS.items():
        root = HERE / rel
        if not root.exists():
            raise SystemExit(f"REFUSED: {rel} does not exist. All four arms "
                             "must land before the set is harvested.")
        seed = _seed_problem(root)
        for c in conjectures(root):
            if c["problem"] != seed:
                continue
            bid = str(uuid.uuid4())
            rows.append({"bid": bid, "text": c["claim"]})
            keymap[bid] = {"arm": arm, "artifact": c["id"], "school": c["school"]}
    rows.sort(key=lambda r: r["bid"])
    (BLIND / "candidates.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
    )
    (BLIND / "keymap.json").write_text(json.dumps(keymap, indent=1), encoding="utf-8")
    print(f"harvested {len(rows)} replicate candidates from {len(ARMS)} arms")
    for arm in ARMS:
        print(f"  {arm:<18} {sum(1 for v in keymap.values() if v['arm'] == arm)}")
    return 0


def score() -> int:
    key = _key()
    rows = [json.loads(l) for l in
            (BLIND / "candidates.jsonl").read_text().splitlines() if l.strip()]
    path = BLIND / "scores.json"
    out: dict[str, dict] = json.loads(path.read_text()) if path.exists() else {}
    for i, row in enumerate(rows, 1):
        if row["bid"] in out:
            continue
        judges = []
        for _ in range(JUDGES):
            got = _ask(key, row["text"])
            if got:
                judges.append(got)
            time.sleep(1.0)
        if not judges:
            out[row["bid"]] = {"failed": True}
        else:
            totals = sorted(j["total"] for j in judges)
            out[row["bid"]] = {
                "judges": len(judges),
                "totals": totals,
                "median": statistics.median(totals),
                "spread": totals[-1] - totals[0],
                "contested": (totals[-1] - totals[0]) > 4,
                "detail": judges,
            }
        if i % 5 == 0 or i == len(rows):
            path.write_text(json.dumps(out, indent=1), encoding="utf-8")
            done = sum(1 for v in out.values() if not v.get("failed"))
            print(f"  scored {i}/{len(rows)} (usable {done})", flush=True)
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"scored {len(out)} replicate candidates -> blind-r/scores.json")
    return 0


def reveal() -> int:
    if not (BLIND / "scores.json").exists():
        raise SystemExit("REFUSED: blind-r/scores.json does not exist. The "
                         "replicate keymap stays shut until the scores are written.")
    scores = json.loads((BLIND / "scores.json").read_text())
    n_cand = sum(1 for l in (BLIND / "candidates.jsonl").read_text().splitlines() if l.strip())
    if len(scores) != n_cand:
        raise SystemExit(f"REFUSED: {len(scores)} scored of {n_cand}.")
    keymap = json.loads((BLIND / "keymap.json").read_text())
    by_arm: dict[str, list[float]] = {}
    for bid, s in scores.items():
        if s.get("failed"):
            continue
        by_arm.setdefault(keymap[bid]["arm"], []).append(s["median"])
    print("REPLICATE_JUDGING_RESULT_V1  (median of 3 judges per candidate, 0-15)")
    for arm in sorted(by_arm):
        v = sorted(by_arm[arm])
        print(f"  {arm:<18} n={len(v):>3}  mean={statistics.mean(v):5.2f}  "
              f"median={statistics.median(v):5.2f}  best={v[-1]:4.1f}")
    return 0


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action not in ("harvest", "score", "reveal"):
        raise SystemExit("usage: judge_replication.py {harvest|score|reveal}")
    raise SystemExit({"harvest": harvest, "score": score, "reveal": reveal}[action]())
