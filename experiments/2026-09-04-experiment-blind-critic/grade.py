#!/usr/bin/env python3
"""M1 PRIMARY: a blind three-grader panel on whether a criticism NAMES the defect.

Each grader sees the clean body, the planted body, the defect note and the
criticism text. It never sees the cell, the layout, the arm, the school, or any
other grader's answer -- the fields are ABSENT from the row, not blanked, which
is the record's own finding about provenance slots applied to this panel
(`docs/RESEARCH_JUDGE_BLINDING_2026-08-22.md`: a present-but-empty slot draws
more attention than a populated one).

Majority of three decides. A grader's answer is a boolean and a one-line
reason; no grader is asked for a score, and nothing a grader says about its own
reliability is read.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import pathlib
import threading
import time
import uuid

HERE = pathlib.Path(__file__).resolve().parent
BLIND = HERE / "blind"
MODEL = "glm-5.2"
BASE_URL = "https://ollama.com/v1"
CONCURRENCY = 3
GRADERS = 3

PROMPT = """You are checking whether a written criticism identifies one SPECIFIC
known fault.

Below are two versions of the same claim: an ORIGINAL, and a MODIFIED version in
which exactly one fault was deliberately introduced. You are told what that
fault is. Then you are shown a criticism that somebody wrote about the MODIFIED
version.

Your only question: does the criticism IDENTIFY THAT SPECIFIC FAULT?

Say yes only if the criticism points at the introduced fault itself -- the
passage, the step, or the defect described. A criticism that attacks the claim
on other grounds, however well, is a NO. A criticism that names the fault
without using the same words is a YES.

ORIGINAL:
{clean}

MODIFIED (contains the introduced fault):
{planted}

THE INTRODUCED FAULT:
{note}

THE CRITICISM:
{criticism}

Reply with ONLY a JSON object: {{"names_the_fault": true or false, "reason": "one sentence"}}
"""


def _api_key() -> str:
    for line in (HERE / "env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OLLAMA_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no OLLAMA_API_KEY in the tranche env file")


def build_rows():
    """Blind rows: exactly the keys a grader needs, and no others."""
    key = json.loads((HERE / "DEFECT_KEY.json").read_text(encoding="utf-8"))
    pairs = {p["target_id"]: p for p in key["pairs"]}
    calls = [json.loads(line) for line in
             (HERE / "raw" / "calls.jsonl").open(encoding="utf-8")]

    rows, keymap = [], {}
    for call in calls:
        if call["arm"] != "planted" or not call["form_attack"]:
            continue
        pair = pairs[call["target_id"]]
        bid = str(uuid.uuid4())
        rows.append({
            "bid": bid,
            "clean": json.dumps(pair["clean"], ensure_ascii=False, sort_keys=True),
            "planted": json.dumps(pair["planted"], ensure_ascii=False, sort_keys=True),
            "note": pair["defect_note"],
            "criticism": call["form_case"],
        })
        keymap[bid] = {"cell": call["cell"], "target_id": call["target_id"],
                       "defect_class": pair["defect_class"],
                       "school": call["school"]}
    rows.sort(key=lambda r: r["bid"])
    return rows, keymap


def _one(row, grader_index, key):
    from deepreason.llm.adapter import _extract_json
    import urllib.error
    import urllib.request

    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT.format(
            clean=row["clean"], planted=row["planted"],
            note=row["note"], criticism=row["criticism"])}],
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
        # Graders differ only by a seed, so three independent readings are
        # three readings and not one cached one.
        "seed": grader_index + 1,
    }).encode()
    request = urllib.request.Request(
        f"{BASE_URL}/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}",
                 "Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                payload = json.loads(response.read())
            text = payload["choices"][0]["message"].get("content") or ""
            parsed = json.loads(_extract_json(text))
            return {"bid": row["bid"], "grader": grader_index,
                    "names_the_fault": bool(parsed.get("names_the_fault")),
                    "reason": str(parsed.get("reason") or "")[:400],
                    "usage": payload.get("usage")}
        except Exception as error:  # noqa: BLE001 - a failed grade is data
            if attempt == 2:
                return {"bid": row["bid"], "grader": grader_index,
                        "names_the_fault": None,
                        "error": f"{type(error).__name__}: {error}"[:200]}
            time.sleep(2 ** attempt)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.parse_args()

    BLIND.mkdir(exist_ok=True)
    rows, keymap = build_rows()

    # The blinding assertion: on the KEY SET, not by eye.
    allowed = {"bid", "clean", "planted", "note", "criticism"}
    for row in rows:
        assert set(row) == allowed, set(row) ^ allowed
    (BLIND / "grading_rows.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
        encoding="utf-8")
    print(f"blind rows: {len(rows)}  keys: {sorted(allowed)}")

    key = _api_key()
    lock = threading.Lock()
    grades: list[dict] = []
    jobs = [(row, g) for row in rows for g in range(GRADERS)]
    done = 0
    with concurrent.futures.ThreadPoolExecutor(CONCURRENCY) as pool:
        futures = {pool.submit(_one, row, g, key): (row, g) for row, g in jobs}
        for future in concurrent.futures.as_completed(futures):
            grade = future.result()
            with lock:
                grades.append(grade)
                done += 1
                if done % 50 == 0:
                    print(f"[grade] {done}/{len(jobs)}", flush=True)
    (BLIND / "grades.jsonl").write_text(
        "".join(json.dumps(g, ensure_ascii=False) + "\n" for g in sorted(
            grades, key=lambda g: (g["bid"], g["grader"]))), encoding="utf-8")

    # Majority of three; a bid whose graders all failed is UNGRADED and is
    # counted in the shortfall rather than guessed.
    by_bid: dict[str, list] = {}
    for grade in grades:
        if grade["names_the_fault"] is not None:
            by_bid.setdefault(grade["bid"], []).append(grade["names_the_fault"])
    verdicts = {bid: sum(votes) * 2 > len(votes)
                for bid, votes in by_bid.items() if votes}
    (BLIND / "keymap.json").write_text(json.dumps(keymap, indent=1) + "\n",
                                       encoding="utf-8")
    (BLIND / "verdicts.json").write_text(json.dumps(verdicts, indent=1) + "\n",
                                         encoding="utf-8")
    print(f"graded bids: {len(verdicts)} of {len(rows)}")
    print(f"unanimous: {sum(1 for v in by_bid.values() if len(set(v)) == 1)}")
    print("keymap and verdicts written together, after the grades")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
