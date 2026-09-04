#!/usr/bin/env python3
"""M5 sharpness: the committed three-judge protocol, criteria re-fixed for criticism.

ADOPTED UNCHANGED from
`experiments/2026-09-03-change-provenance-history-channel/JUDGING_PREREG_COPIED.md`:
three judges scoring independently, 0-3 per criterion, the MEDIAN of three
totals rather than the mean, the contested flag at a spread above 4 of 15, the
blinding, the keymap-stays-shut rule, and its closing statement that this is a
ranked opinion with its criteria written down in advance rather than a
measurement.

RE-FIXED in PREREG section 6, because the copied criteria 1-5 are written about
one seed question's Popperian content and a criticism is a different object.

A judge sees a target and a criticism of it. It never sees the cell, the
layout, the school, the seat, the arm, or whether the target carries a planted
fault -- absent from the row, not blanked.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import pathlib
import statistics
import threading
import time
import uuid

HERE = pathlib.Path(__file__).resolve().parent
BLIND = HERE / "blind"
MODEL = "glm-5.2"
BASE_URL = "https://ollama.com/v1"
CONCURRENCY = 3
JUDGES = 3
CONTESTED_SPREAD = 4

PROMPT = """Score one written criticism of one claim, against five fixed criteria.

THE CLAIM:
{target}

THE CRITICISM:
{criticism}

Score each criterion 0-3.

1. SPECIFIC RATHER THAN GENERIC. Does the case turn on something in THIS
   claim's text -- a named step, a named assertion, a named condition -- rather
   than on a complaint that would fit any claim?
   0 = would fit anything; 3 = quotes or names the load-bearing part.

2. THE FAULT IS REAL. Is what it points at actually a fault, rather than a
   restatement of the claim, a preference, or a demand for more detail?
   0 = no fault identified; 3 = a defect a competent defender would have to answer.

3. THE CASE IS MADE, NOT ASSERTED. Does it say WHY the thing it names is wrong?
   0 = a verdict with no argument; 3 = an argument whose steps a reader can check.

4. IT IS ANSWERABLE. Does it state what would rebut it -- a condition, a
   counterexample, a piece of evidence?
   0 = unfalsifiable disapproval; 3 = names what would settle it.

5. NON-EVASION. Does it resist two cheap exits: attacking the claim's framing
   instead of its content, and hedging into "further work is needed"?
   0 = takes an exit; 3 = holds the point.

Reply with ONLY a JSON object:
{{"c1": 0-3, "c2": 0-3, "c3": 0-3, "c4": 0-3, "c5": 0-3,
  "why": {{"c1": "one line", "c2": "one line", "c3": "one line",
          "c4": "one line", "c5": "one line"}}}}
"""


def _api_key() -> str:
    for line in (HERE / "env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OLLAMA_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no OLLAMA_API_KEY in the tranche env file")


def build_rows():
    """Every criticism from every cell, blinded. Both arms: sharpness is a
    property of the criticism, not of whether its target was faulted."""
    calls = [json.loads(line) for line in
             (HERE / "raw" / "calls.jsonl").open(encoding="utf-8")]
    selection = json.loads((HERE / "SELECTION.json").read_text())
    key = json.loads((HERE / "DEFECT_KEY.json").read_text())
    clean = {r["target_id"]: r["body"] for r in selection["targets"]}
    planted = {p["target_id"]: p["planted"] for p in key["pairs"]}

    rows, keymap = [], {}
    for call in calls:
        if not call["form_attack"] or not call["form_case"].strip():
            continue
        target_id = call["target_id"]
        body = planted.get(target_id) if call["arm"] == "planted" else clean[target_id]
        bid = str(uuid.uuid4())
        rows.append({
            "bid": bid,
            "target": json.dumps(body, ensure_ascii=False, sort_keys=True),
            "criticism": call["form_case"],
        })
        keymap[bid] = {"cell": call["cell"], "target_id": target_id,
                       "arm": call["arm"], "school": call["school"],
                       "defect_class": call["defect_class"]}
    rows.sort(key=lambda r: r["bid"])
    return rows, keymap


def _leak(row, keymap) -> bool:
    """Residual leakage the panel cannot remove: a criticism that names the
    school it was told about. Recorded against the bid, per the copied
    protocol's own instruction, never used to drop a row."""
    school = keymap[row["bid"]]["school"]
    return bool(school) and school.lower() in row["criticism"].lower()


def _one(row, judge_index, key):
    from deepreason.llm.adapter import _extract_json
    import urllib.request

    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT.format(
            target=row["target"], criticism=row["criticism"])}],
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
        "seed": judge_index + 11,
    }).encode()
    request = urllib.request.Request(
        f"{BASE_URL}/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                payload = json.loads(response.read())
            parsed = json.loads(_extract_json(
                payload["choices"][0]["message"].get("content") or ""))
            scores = [int(parsed[f"c{i}"]) for i in range(1, 6)]
            assert all(0 <= s <= 3 for s in scores), scores
            return {"bid": row["bid"], "judge": judge_index, "scores": scores,
                    "total": sum(scores), "why": parsed.get("why")}
        except Exception as error:  # noqa: BLE001 - a failed score is data
            if attempt == 2:
                return {"bid": row["bid"], "judge": judge_index, "total": None,
                        "error": f"{type(error).__name__}: {error}"[:200]}
            time.sleep(2 ** attempt)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.parse_args()

    BLIND.mkdir(exist_ok=True)
    rows, keymap = build_rows()
    allowed = {"bid", "target", "criticism"}
    for row in rows:
        assert set(row) == allowed, set(row) ^ allowed
    (BLIND / "criticisms.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8")
    print(f"blind rows: {len(rows)}  keys: {sorted(allowed)}")

    key = _api_key()
    lock = threading.Lock()
    scored: list[dict] = []
    jobs = [(row, j) for row in rows for j in range(JUDGES)]
    done = 0
    with concurrent.futures.ThreadPoolExecutor(CONCURRENCY) as pool:
        futures = [pool.submit(_one, row, j, key) for row, j in jobs]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            with lock:
                scored.append(result)
                done += 1
                if done % 100 == 0:
                    print(f"[judge] {done}/{len(jobs)}", flush=True)

    by_bid: dict[str, list[int]] = {}
    for result in scored:
        if result.get("total") is not None:
            by_bid.setdefault(result["bid"], []).append(result["total"])
    medians = {bid: statistics.median(t) for bid, t in by_bid.items() if t}
    contested = {bid for bid, t in by_bid.items()
                 if len(t) > 1 and max(t) - min(t) > CONTESTED_SPREAD}
    leaks = {row["bid"] for row in rows if _leak(row, keymap)}

    (BLIND / "scores.jsonl").write_text(
        "".join(json.dumps(s, ensure_ascii=False) + "\n"
                for s in sorted(scored, key=lambda s: (s["bid"], s["judge"]))),
        encoding="utf-8")
    (BLIND / "sharpness_keymap.json").write_text(
        json.dumps(keymap, indent=1) + "\n", encoding="utf-8")

    per_cell: dict[str, list[float]] = {}
    for bid, median in medians.items():
        per_cell.setdefault(keymap[bid]["cell"], []).append(median)
    summary = {
        "protocol": "JUDGING_PREREG_COPIED.md machinery, PREREG s6 criteria",
        "rows": len(rows), "scored_bids": len(medians),
        "contested": len(contested), "self_identifying_rows": len(leaks),
        "per_cell": {c: {"n": len(v), "median_of_medians": statistics.median(v),
                         "mean_of_medians": round(statistics.mean(v), 3)}
                     for c, v in sorted(per_cell.items())},
    }
    (HERE / "M5.json").write_text(json.dumps(summary, indent=1) + "\n",
                                  encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
