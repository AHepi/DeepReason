"""Blind three-judge scoring of the organiser arms. PREREG.md §5.

A copy of `experiments/2026-09-05-change-mini-isolation-programme/d8/judge_d8.py`
(itself a copy of the 2026-09-02 protocol) whose ONLY changes are `harvest`
-- which arms, and where their units live -- and the paths. The criteria
text, the 0-3 scoring, the median-of-three over the surviving judges, the
contested flag, the blinding (uuid4 bids, rows sorted by bid, keymap shut
until scores.json exists), the judge model with reasoning off, max_tokens
900, the backoff and the pacing are adopted UNCHANGED.

The units (PREREG §4): ARM 0 = each of the three recorded D8 essays, whole;
ARM H and ARM R = ONE composed result each (`tools/compose_result.py`), read
from runs/armH/COMPOSED.txt and runs/armR/COMPOSED.txt, which the arm
scripts write from the root at the terminal.

Usage:
    judge_organiser.py harvest    # arms -> blind/candidates.jsonl + blind/keymap.json
    judge_organiser.py score      # 3 judges per unit -> blind/scores.json
    judge_organiser.py reveal     # requires scores.json; joins keymap and reports
"""

from __future__ import annotations

import argparse
import json
import pathlib
import statistics
import sys
import time
import urllib.error
import urllib.request
import uuid

HERE = pathlib.Path(__file__).resolve().parent
TRANCHE = HERE.parent
BLIND = TRANCHE / "blind"
D8 = TRANCHE.parent / "2026-09-05-change-mini-isolation-programme" / "d8"
ENDPOINT = "https://ollama.com/v1/chat/completions"
MODEL = "qwen3.5:397b"
JUDGES = 3

# Verbatim from JUDGING_PREREG_COPIED.md (sha256 ef3d4f95...). Not paraphrased.
CRITERIA = """You are scoring ONE candidate answer to this question:

"Popper held that corroboration is not probability: a theory that has survived
severe tests is not thereby made more probable. Yet working scientists, and
Popper himself when choosing which theory to act on, prefer the better-
corroborated theory. Is that preference defensible on Popper's own terms, or
does it smuggle back in the induction he rejected? Make the strongest case for
each answer, then say which one survives and what accepting it costs."

Score each criterion 0-3.

1. Both cases made, and made at strength. Is the case for "the preference is
   defensible on Popper's own terms" and the case for "it smuggles induction
   back in" each stated in its strongest form, rather than one being set up to
   lose? 0 = one side only or a straw man; 3 = both sides stated as a competent
   proponent of each would state them.

2. Engagement with the actual Popperian machinery. Does it turn on what
   corroboration IS in Popper (a report on past test performance, explicitly
   not a probability, explicitly not a prediction) and on the specific move
   that is contested (the pragmatic preference of Objective Knowledge / the
   Realism and the Aim of Science reply to Salmon)? 0 = generic
   philosophy-of-science prose that would fit any question; 3 = the
   load-bearing distinction is named and used.

3. A verdict that is actually a verdict. Does it say which one survives and
   commit to it? 0 = "both have merit"; 3 = a stated survivor with the reason
   it survives.

4. The cost is named and is a real cost. Does it say what accepting the
   surviving answer gives up - and is that a genuine loss rather than a
   restatement of the verdict? 0 = no cost, or a cost that costs nothing;
   3 = a specific concession that a defender of the surviving answer would find
   uncomfortable.

5. Non-evasion. Does it resist the two cheap exits: (a) dissolving the question
   by redefining corroboration until the tension vanishes, (b) conceding
   Salmon's point and calling the residue "pragmatic" as though naming it
   settled it. 0 = takes an exit; 3 = the tension is held and answered.

Return ONLY a JSON object, no prose around it:
{"c1":<0-3>,"c2":<0-3>,"c3":<0-3>,"c4":<0-3>,"c5":<0-3>,
 "why":{"c1":"<one line>","c2":"<one line>","c3":"<one line>",
        "c4":"<one line>","c5":"<one line>"}}
"""


def _key() -> str:
    env = TRANCHE / "env"
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("OLLAMA_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no OLLAMA_API_KEY in the tranche env file")


def _arm0_texts() -> list[tuple[str, str]]:
    """The three recorded D8 calls, reused; never respent (R16)."""
    out = []
    for path in sorted((D8 / "arm0").glob("call-*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec.get("completed") and rec.get("content", "").strip():
            out.append((path.stem, rec["content"]))
    return out


def _composed(arm_dir: str) -> list[tuple[str, str]]:
    """ONE unit per harness arm: the composed result the arm script wrote."""
    path = TRANCHE / "runs" / arm_dir / "COMPOSED.txt"
    if not path.exists():
        raise SystemExit(f"REFUSED: {path} does not exist; the arm has not reached its terminal")
    return [(f"{arm_dir}/COMPOSED.txt", path.read_text(encoding="utf-8"))]


def harvest() -> int:
    BLIND.mkdir(exist_ok=True)
    rows, keymap = [], {}
    for arm, items in (
        ("ARM0-single-call", _arm0_texts()),
        ("ARMH-harness", _composed("armH")),
        ("ARMR-organiser", _composed("armR")),
    ):
        for ident, text in items:
            bid = str(uuid.uuid4())
            rows.append({"bid": bid, "text": text})
            keymap[bid] = {"arm": arm, "source": ident, "chars": len(text)}
    rows.sort(key=lambda r: r["bid"])  # position carries no origin signal
    (BLIND / "candidates.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
    )
    (BLIND / "keymap.json").write_text(json.dumps(keymap, indent=1), encoding="utf-8")
    print(f"harvested {len(rows)} units from 3 arms")
    print("  blind/candidates.jsonl  -> {bid, text} only")
    print("  blind/keymap.json       -> NOT to be opened until scores.json exists")
    return 0


def _ask(key: str, text: str, attempts: int = 4) -> dict | None:
    """One judge call, with backoff (verbatim from the source judge.py)."""
    body = json.dumps(
        {
            "model": MODEL,
            "messages": [
                {"role": "user", "content": CRITERIA + "\n\nCANDIDATE:\n" + text}
            ],
            "temperature": 1.0,
            "max_tokens": 900,
            "reasoning": {"effort": "none"},
        }
    ).encode()
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(
                ENDPOINT,
                data=body,
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=180) as r:
                out = json.loads(r.read())
        except Exception:  # noqa: BLE001 - transport; retry
            time.sleep(2 ** attempt)
            continue
        content = (out.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        start, end = content.find("{"), content.rfind("}")
        if start < 0 or end < 0:
            time.sleep(2 ** attempt)
            continue
        try:
            parsed = json.loads(content[start : end + 1])
            scores = [int(parsed[f"c{i}"]) for i in range(1, 6)]
        except Exception:  # noqa: BLE001
            time.sleep(2 ** attempt)
            continue
        if any(s < 0 or s > 3 for s in scores):
            return None
        return {"scores": scores, "total": sum(scores), "why": parsed.get("why")}
    return None


def score() -> int:
    key = _key()
    rows = [
        json.loads(l) for l in (BLIND / "candidates.jsonl").read_text().splitlines() if l
    ]
    out: dict[str, dict] = {}
    path = BLIND / "scores.json"
    if path.exists():
        out = json.loads(path.read_text())
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
        path.write_text(json.dumps(out, indent=1), encoding="utf-8")
        done = sum(1 for v in out.values() if not v.get("failed"))
        print(f"  scored {i}/{len(rows)} (usable {done})", flush=True)
    path.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"scored {len(out)} candidates -> blind/scores.json")
    return 0


def reveal() -> int:
    if not (BLIND / "scores.json").exists():
        raise SystemExit("REFUSED: blind/scores.json does not exist. The keymap "
                         "stays shut until the scores are written.")
    scores = json.loads((BLIND / "scores.json").read_text())
    keymap = json.loads((BLIND / "keymap.json").read_text())
    by_arm: dict[str, list[float]] = {}
    contested = 0
    for bid, s in scores.items():
        if s.get("failed"):
            continue
        contested += bool(s.get("contested"))
        by_arm.setdefault(keymap[bid]["arm"], []).append(s["median"])
    print("BLIND_JUDGING_RESULT_V1  (median of 3 judges per candidate, 0-15)")
    print(f"  candidates scored : {sum(len(v) for v in by_arm.values())}")
    print(f"  contested (>4 spread of 15): {contested}")
    for arm in sorted(by_arm):
        v = sorted(by_arm[arm])
        print(
            f"  {arm:<18} n={len(v):>3}  mean={statistics.mean(v):.2f}  "
            f"median={statistics.median(v):.2f}  best={v[-1]:.1f}  worst={v[0]:.1f}"
        )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("harvest", "score", "reveal"))
    a = ap.parse_args()
    return {"harvest": harvest, "score": score, "reveal": reveal}[a.action]()


if __name__ == "__main__":
    sys.exit(main())
