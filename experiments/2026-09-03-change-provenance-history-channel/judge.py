"""Blind three-judge scoring of the M1/M3 candidates.

Implements `JUDGING_PREREG_COPIED.md` — the protocol copied verbatim from the
2026-09-02 episode-config tranche — against THIS tranche's four completed arms.
The criteria, the 0-3 scoring, the tie-breaks (criterion 4 then 1), the
blinding, the three-judge MEDIAN and the keymap-stays-shut rule are adopted
UNCHANGED. Only the arm labels differ, which is what `PREREG.md`'s copy header
already said would change.

WHY THIS EXISTS. D4 and D5 measure SPREAD, not merit. R6's actual verb is
"better conjectures", and nothing in `RESULTS_M1.md` or `RESULTS_M3.md` speaks
to it. This needs no new runs: the four committed arms already hold every
candidate.

## Blinding, and the specific way the source protocol got it wrong

`blind/candidates.jsonl` carries `{bid, text}` and nothing else. `bid` is a
uuid4 with no arm, cycle, root or ordering information, and rows are emitted
sorted by `bid` so file position carries no origin signal. The arm mapping goes
to `blind/keymap.json`.

The source protocol's Amendment 2 records that its own tooling defeated this:
an earlier step wrote per-arm candidate files, with the arm in the filename,
two steps before scoring — so one grep returned any candidate's arm while the
keymap sat unopened beside it. This script therefore writes NOTHING per-arm
until `--reveal`, which is refused until `blind/scores.json` exists.

Two bugs the same amendment found in the source panel are avoided here rather
than reimplemented: the median is computed over the ACTUAL surviving judge
list with even-count handling (the source returned `sorted[n//2]`, which for
two survivors returns the HIGHER — the exact inverse of the pre-registered rule
that one outlier judge cannot carry a candidate), and nothing decodes a label
out of free-form model text.

Usage:
    judge.py harvest       # arms -> blind/candidates.jsonl + blind/keymap.json
    judge.py score         # 3 judges per candidate -> blind/scores.json
    judge.py reveal        # requires scores.json; joins keymap and reports
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import statistics
import sys
import time
import urllib.error
import urllib.request
import uuid

HERE = pathlib.Path(__file__).resolve().parent
BLIND = HERE / "blind"
ENDPOINT = "https://ollama.com/v1/chat/completions"
MODEL = "qwen3.5:397b"
JUDGES = 3

ARMS = {
    "M1-H0P-control": "runs/home-m1/runs/run-ad41064484366337ed61a9d5a58de58f",
    "M1-H1R-history": "runs/home-m1/runs/run-f23da86ddfd5ab820957221cfebe4b2e",
    "M3-C0P-blind": "runs/home-m3/runs/run-5565bd1ef7011e3d25fef3197bdf1cdb",
    "M3-C1I-informed": "runs/home-m3/runs/run-7a8fc89b33f8e055a212fafa09acd83f",
}

# Verbatim from JUDGING_PREREG_COPIED.md. Not paraphrased: the whole point of
# copying a pre-registered protocol is that its wording is fixed.
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
    env = HERE / "env"
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("OLLAMA_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no OLLAMA_API_KEY in the tranche env file")


def harvest() -> int:
    sys.path.insert(0, str(HERE))
    from measure_diversity_per_problem import conjectures, _seed_problem

    BLIND.mkdir(exist_ok=True)
    rows, keymap = [], {}
    for arm, rel in ARMS.items():
        root = HERE / rel
        seed = _seed_problem(root)
        for c in conjectures(root):
            if c["problem"] != seed:
                continue
            bid = str(uuid.uuid4())
            rows.append({"bid": bid, "text": c["claim"]})
            keymap[bid] = {"arm": arm, "artifact": c["id"], "school": c["school"]}
    rows.sort(key=lambda r: r["bid"])  # position carries no origin signal
    (BLIND / "candidates.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
    )
    (BLIND / "keymap.json").write_text(json.dumps(keymap, indent=1), encoding="utf-8")
    print(f"harvested {len(rows)} candidates from {len(ARMS)} arms")
    print("  blind/candidates.jsonl  -> {bid, text} only")
    print("  blind/keymap.json       -> NOT to be opened until scores.json exists")
    return 0


def _ask(key: str, text: str, attempts: int = 4) -> dict | None:
    """One judge call, with backoff.

    The first run of this script had NO retry and no pacing, and it shows in
    its own log: usable scores stalled at 38 while rows kept being consumed --
    rows 38 to 50 failed in an unbroken block, which is a rate limit, not
    twelve unlucky candidates. Three calls per candidate with no pause is the
    same mistake, at a smaller scale, that cost two whole arms earlier in this
    tranche (PARKED P3, P4). A transport failure is now retried with
    exponential backoff and distinguished in the return value from a genuine
    parse failure, so a rate-limited call can no longer be silently recorded as
    a candidate the judges could not score.
    """
    body = json.dumps(
        {
            "model": MODEL,
            "messages": [
                {"role": "user", "content": CRITERIA + "\n\nCANDIDATE:\n" + text}
            ],
            "temperature": 1.0,
            "max_tokens": 900,
            # REASONING OFF, and this is load-bearing rather than tidy. Without
            # it every judge call returns an EMPTY content field: the model
            # spends the whole completion cap on hidden reasoning and emits
            # nothing, which is the exact failure CLAUDE.md documents for
            # reasoning models. Measured: `reasoning: none` -> 694 chars of
            # valid JSON; `think: false` -> 0; a 3000-token cap with no
            # reasoning field -> 0. It is the parameter, not the cap. It also
            # matches the arms' own profile, so judges score under the same
            # condition the candidates were written under.
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
            time.sleep(1.0)  # pace the endpoint; see _ask
        if not judges:
            out[row["bid"]] = {"failed": True}
        else:
            totals = sorted(j["total"] for j in judges)
            # MEDIAN over the SURVIVING judges, even counts handled. The source
            # protocol's helper returned sorted[n//2], which for two survivors
            # returns the higher -- the inverse of "one outlier cannot carry a
            # candidate". statistics.median averages the middle two instead.
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
            f"median={statistics.median(v):.2f}  best={v[-1]:.1f}"
        )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("harvest", "score", "reveal"))
    a = ap.parse_args()
    return {"harvest": harvest, "score": score, "reveal": reveal}[a.action]()


if __name__ == "__main__":
    sys.exit(main())
