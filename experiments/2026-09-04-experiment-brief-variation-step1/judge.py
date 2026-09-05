"""Blind three-judge scoring of every arm's candidates, B0 included.

## What is copied and what is not

The PROTOCOL is `experiments/2026-09-03-change-provenance-history-channel/
JUDGING_PREREG_COPIED.md`, adopted unchanged: the five criteria, the 0-3
scoring, the tie-breaks (criterion 4 then 1), the three-judge MEDIAN over the
SURVIVING judges, the contested flag at a spread over 4 of 15, and the
keymap-stays-shut rule. The seed question is byte-identical to that tranche's
(`sha256 626e8f78…`), which is what lets criteria 2-5 -- written about that
question's specific machinery -- transfer verbatim rather than being rewritten.

The CRITERIA STRING and `_ask` are imported from that tranche's `judge.py`
rather than retyped. A pre-registered protocol whose wording drifts between
tranches is no longer one protocol, and a retyped 2,000-character prompt is
exactly where a drift hides.

## What differs, and it is only what PREREG.md said would differ

Arm labels. This tranche's five harness arms plus B0, harvested from the roots
`arm.sh` retires into `roots/`.

## B0 in the same pool

B0's answers are judged as candidates alongside the harness arms', blinded the
same way, so no judge can tell a one-call answer from a conjecture. PREREG.md
§4.1 registers the one place the units are not comparable -- a harness arm
contributes dozens of draws and B0 twelve -- and fixes the comparison on the
MEAN with the best reported beside it.

Usage:
    judge.py harvest   # arms + B0 -> blind/candidates.jsonl, blind/keymap.json
    judge.py score     # 3 judges per candidate -> blind/scores.json (resumable)
    judge.py reveal    # requires scores.json; joins the keymap and reports
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import statistics
import sys
import uuid

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
PARENT = REPO / "experiments" / "2026-09-03-change-provenance-history-channel"
BLIND = HERE / "blind"
JUDGES = 3


def _parent_judge():
    """The copied protocol's own module, loaded by path.

    Its `env` lookup is relative to ITS directory, so the key is read from
    this tranche's env file and handed in explicitly instead.
    """

    spec = importlib.util.spec_from_file_location("parent_judge", PARENT / "judge.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _key() -> str:
    for line in (HERE / "env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OLLAMA_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no OLLAMA_API_KEY in the tranche env file")


def _roots() -> dict[str, pathlib.Path]:
    """arm -> the root `arm.sh` retired, discovered rather than hard-coded."""

    found: dict[str, pathlib.Path] = {}
    for path in sorted((HERE / "roots").glob("*-run-*")):
        if not (path / "log.jsonl").exists():
            continue
        arm = path.name.split("-run-")[0]
        if arm in found:
            raise SystemExit(
                f"two roots for arm {arm!r}: {found[arm].name} and {path.name}. "
                "An arm with two roots would be counted twice; retire one."
            )
        found[arm] = path
    return found


def harvest() -> int:
    sys.path.insert(0, str(PARENT))
    from measure_diversity_per_problem import conjectures, _seed_problem

    BLIND.mkdir(exist_ok=True)
    rows: list[dict] = []
    keymap: dict[str, dict] = {}

    for arm, root in _roots().items():
        seed = _seed_problem(root)
        for candidate in conjectures(root):
            if candidate["problem"] != seed:
                continue
            bid = str(uuid.uuid4())
            rows.append({"bid": bid, "text": candidate["claim"]})
            keymap[bid] = {
                "arm": arm,
                "artifact": candidate["id"],
                "school": candidate["school"],
            }

    answers = HERE / "b0" / "answers.jsonl"
    if answers.exists():
        for line in answers.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            bid = str(uuid.uuid4())
            rows.append({"bid": bid, "text": record["text"]})
            keymap[bid] = {
                "arm": "B0",
                "artifact": f"b0-call-{record['index']}",
                "school": None,
            }

    # Position carries no origin signal.
    rows.sort(key=lambda row: row["bid"])
    (BLIND / "candidates.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
    )
    (BLIND / "keymap.json").write_text(json.dumps(keymap, indent=1), encoding="utf-8")
    per_arm: dict[str, int] = {}
    for entry in keymap.values():
        per_arm[entry["arm"]] = per_arm.get(entry["arm"], 0) + 1
    print(f"harvested {len(rows)} candidates")
    for arm in sorted(per_arm):
        print(f"  {arm:<5} {per_arm[arm]}")
    print("  blind/candidates.jsonl -> {bid, text} only")
    print("  blind/keymap.json      -> NOT opened until scores.json exists")
    return 0


def score() -> int:
    parent = _parent_judge()
    key = _key()
    rows = [
        json.loads(line)
        for line in (BLIND / "candidates.jsonl").read_text().splitlines()
        if line.strip()
    ]
    path = BLIND / "scores.json"
    out: dict[str, dict] = json.loads(path.read_text()) if path.exists() else {}
    import time

    for index, row in enumerate(rows, 1):
        if row["bid"] in out:
            continue
        judges = []
        for _ in range(JUDGES):
            got = parent._ask(key, row["text"])
            if got:
                judges.append(got)
            time.sleep(1.0)
        if not judges:
            out[row["bid"]] = {"failed": True}
        else:
            totals = sorted(judge["total"] for judge in judges)
            out[row["bid"]] = {
                "judges": len(judges),
                "totals": totals,
                "median": statistics.median(totals),
                "spread": totals[-1] - totals[0],
                "contested": (totals[-1] - totals[0]) > 4,
                "detail": judges,
            }
        if index % 5 == 0 or index == len(rows):
            path.write_text(json.dumps(out, indent=1), encoding="utf-8")
            usable = sum(1 for v in out.values() if not v.get("failed"))
            print(f"  scored {index}/{len(rows)} (usable {usable})", flush=True)
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"scored {len(out)} candidates -> blind/scores.json")
    return 0


def reveal() -> int:
    if not (BLIND / "scores.json").exists():
        raise SystemExit(
            "REFUSED: blind/scores.json does not exist. The keymap stays shut "
            "until the scores are written."
        )
    scores = json.loads((BLIND / "scores.json").read_text())
    keymap = json.loads((BLIND / "keymap.json").read_text())
    by_arm: dict[str, list[float]] = {}
    contested = 0
    for bid, entry in scores.items():
        if entry.get("failed"):
            continue
        contested += bool(entry.get("contested"))
        by_arm.setdefault(keymap[bid]["arm"], []).append(entry["median"])
    print("BLIND_JUDGING_RESULT_V1  (median of 3 judges per candidate, 0-15)")
    print(f"  candidates scored : {sum(len(v) for v in by_arm.values())}")
    print(f"  contested (>4 spread of 15): {contested}")
    for arm in sorted(by_arm):
        values = sorted(by_arm[arm])
        print(
            f"  {arm:<5} n={len(values):>3}  mean={statistics.mean(values):5.2f}  "
            f"median={statistics.median(values):5.2f}  best={values[-1]:.1f}"
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("harvest", "score", "reveal"))
    action = parser.parse_args().action
    return {"harvest": harvest, "score": score, "reveal": reveal}[action]()


if __name__ == "__main__":
    raise SystemExit(main())
