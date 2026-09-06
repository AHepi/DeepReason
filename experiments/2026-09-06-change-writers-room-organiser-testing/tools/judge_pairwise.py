"""Pairwise forced-choice judging of the organiser arms. PREREG Amendment 7.

WHY THIS EXISTS. The 0-3 rubric (`tools/judge_organiser.py`, PREREG §5) was
measured saturated on 2026-09-06: eighteen judge readings of the two bare arms
returned eighteen 15s, so the instrument cannot rank anything above a single
call on this question. That instrument and its scores are the record of that
ceiling and are NOT edited. This one replaces it for THIS launch only.

WHAT IT DOES. Every ARM R unit is shown against every bare unit as "Text A"
and "Text B", to three judges, in BOTH orders. Each reading is ONE forced
choice -- A or B, no tie -- plus a one-line reason, with the D8 criteria text
as the standard the choice is made against. A judge whose two readings of the
same pair disagree once the order is undone has NO PREFERENCE on that pair.

THE UNITS. ARM R: the run's composed result (`tools/compose_result.py`, the
same unit PREREG §4 fixed), refused when the run is not `completed` -- a
FAILED arm has no usable unit and its verdict is INCONCLUSIVE (PREREG §3, §7,
Amendment 6). The bare arms: ARM 0's three recorded D8 essays and ARM 0R's
three recorded room-in-the-message replies, both reused by digest and NEVER
respent (R16, Amendment 7).

BLINDING. Units are addressed by uuid4 only; `blind/pairwise_keymap.json` is
not opened until every choice exists (`reveal` refuses otherwise). A reading's
prompt carries no arm label, no id and no length statement.

    judge_pairwise.py harvest   # units + pairs -> blind/pairwise_pairs.jsonl
                                #                 blind/pairwise_keymap.json
    judge_pairwise.py choose    # 3 judges x 2 orders per pair -> choices.json
    judge_pairwise.py reveal    # requires the choices; joins and reports
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import sys
import time
import urllib.request
import uuid

HERE = pathlib.Path(__file__).resolve().parent
TRANCHE = HERE.parent
BLIND = TRANCHE / "blind"
D8 = TRANCHE.parent / "2026-09-05-change-mini-isolation-programme" / "d8"
ENDPOINT = "https://ollama.com/v1/chat/completions"
MODEL = "qwen3.5:397b"
JUDGES = 3
PAIRS = BLIND / "pairwise_pairs.jsonl"
KEYMAP = BLIND / "pairwise_keymap.json"
CHOICES = BLIND / "pairwise_choices.json"

# The standard the choice is made against: the five criteria of
# `tools/judge_organiser.py`'s CRITERIA block (itself byte-identical to D8's),
# quoted here as the STANDARD and not as a scoring instruction. The scoring
# sentences are replaced by the forced choice; the criteria themselves are
# not paraphrased -- `judge_pairwise.py --criteria-check` prints the five
# criterion bodies beside the rubric's own and exits non-zero if they differ.
QUESTION = (
    "Popper held that corroboration is not probability: a theory that has survived\n"
    "severe tests is not thereby made more probable. Yet working scientists, and\n"
    "Popper himself when choosing which theory to act on, prefer the better-\n"
    "corroborated theory. Is that preference defensible on Popper's own terms, or\n"
    "does it smuggle back in the induction he rejected? Make the strongest case for\n"
    "each answer, then say which one survives and what accepting it costs."
)


def _rubric_criteria() -> str:
    """The five criteria, lifted verbatim from the rubric instrument.

    Read from `tools/judge_organiser.py` at run time rather than retyped, so
    the standard cannot drift from the sealed one by a keystroke.
    """

    text = (HERE / "judge_organiser.py").read_text(encoding="utf-8")
    start = text.index("1. Both cases made")
    end = text.index("Return ONLY a JSON object")
    return text[start:end].rstrip()


def _prompt(text_a: str, text_b: str) -> str:
    return (
        "Two candidate answers to the same question are below. Decide which "
        "one is the better answer to it.\n\nTHE QUESTION:\n\n\"" + QUESTION +
        "\"\n\nWhat makes an answer better, in order of weight:\n\n" +
        _rubric_criteria() +
        "\n\nThe two answers differ in length. Length is not a merit: judge "
        "what each answer does against the standard above, not how much of it "
        "there is.\n\nTEXT A:\n" + text_a +
        "\n\nTEXT B:\n" + text_b +
        "\n\nReturn ONLY a JSON object, no prose around it:\n"
        "{\"choice\":\"A\" or \"B\",\"why\":\"<one line>\"}\n"
        "You MUST choose A or B. A tie is not an available answer."
    )


def _key() -> str:
    env = TRANCHE / "env"
    for line in env.read_text(encoding="utf-8").splitlines():
        if line.startswith("OLLAMA_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("no OLLAMA_API_KEY in the tranche env file")


def _arm0_units() -> list[tuple[str, str]]:
    out = []
    for path in sorted((D8 / "arm0").glob("call-*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec.get("completed") and rec.get("content", "").strip():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            out.append((f"arm0/{path.stem}@sha256:{digest}", rec["content"]))
    return out


def _arm0R_units() -> list[tuple[str, str]]:
    out = []
    for path in sorted((TRANCHE / "runs" / "arm0R").glob("call-*.json")):
        rec = json.loads(path.read_text(encoding="utf-8"))
        if rec.get("completed") and rec.get("content", "").strip():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            out.append((f"arm0R/{path.stem}@sha256:{digest}", rec["content"]))
    return out


def _armR_units() -> list[tuple[str, str]]:
    """ARM R's one composed unit -- refused when the run is not completed."""

    path = TRANCHE / "runs" / "armR" / "COMPOSED.txt"
    if not path.exists():
        raise SystemExit(f"REFUSED: {path} does not exist; the arm has not reached its terminal")
    composed = TRANCHE / "runs" / "armR" / "COMPOSED.json"
    if composed.exists():
        root = pathlib.Path(json.loads(composed.read_text(encoding="utf-8"))["root"])
        status_path = root / "run-status.json"
        status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
        if status.get("state") != "completed":
            print(
                "notice: armR is a FAILED arm "
                f"(state={status.get('state')!r}, stop_reason={status.get('stop_reason')!r}); "
                "its unit is NOT harvested (PREREG §3), and every pair it would "
                "have entered is INCONCLUSIVE (§7)"
            )
            return []
        # PREREG §3's OTHER clause, implemented here for the same reason
        # Amendment 6 implemented the state clause: a COMPLETE arm needs
        # `state: completed` AND a verification carrying 0 violations. A run
        # that reaches a clean stop over a record that does not replay is not
        # a usable unit, and composition succeeds on it regardless, so
        # without this check its positions would be scored as if the record
        # stood. This is stricter than the instrument was, never looser, and
        # it changes no rule (PREREG Amendment 9).
        validation = root / "REPLAY_VALIDATION.json"
        if validation.exists():
            report = json.loads(validation.read_text(encoding="utf-8"))
            violations = report.get("verification", {}).get("violations") or []
            if report.get("valid") is False or violations:
                print(
                    f"notice: armR's record does not verify "
                    f"(valid={report.get('valid')!r}, violations={len(violations)}); "
                    "its unit is NOT harvested (PREREG §3 requires 0 violations), "
                    "and every pair it would have entered is INCONCLUSIVE (§7)"
                )
                for violation in violations:
                    print(f"    {violation}")
                return []
    return [("armR/COMPOSED.txt", path.read_text(encoding="utf-8"))]


def harvest() -> int:
    BLIND.mkdir(exist_ok=True)
    arms = {
        "ARMR-organiser": _armR_units(),
        "ARM0-single-call": _arm0_units(),
        "ARM0R-room-bare": _arm0R_units(),
    }
    keymap: dict[str, dict] = {}
    units: dict[str, dict[str, str]] = collections.defaultdict(dict)
    for arm, items in arms.items():
        for ident, text in items:
            uid = str(uuid.uuid4())
            keymap[uid] = {"arm": arm, "source": ident, "chars": len(text)}
            units[arm][uid] = text
    pairs = []
    # The measured comparisons (Amendment 7): every ARM R unit against every
    # bare unit, and the CONTROL, every ARM 0R unit against every ARM 0 unit.
    for left_arm, right_arm, role in (
        ("ARMR-organiser", "ARM0-single-call", "measure"),
        ("ARMR-organiser", "ARM0R-room-bare", "measure"),
        ("ARM0R-room-bare", "ARM0-single-call", "control"),
    ):
        for left in units[left_arm]:
            for right in units[right_arm]:
                pairs.append(
                    {
                        "pair_id": str(uuid.uuid4()),
                        "role": role,
                        "left": left,
                        "right": right,
                    }
                )
    pairs.sort(key=lambda p: p["pair_id"])  # position carries no origin signal
    texts = {uid: text for arm in units.values() for uid, text in arm.items()}
    PAIRS.write_text(
        "\n".join(
            json.dumps(
                {
                    "pair_id": p["pair_id"],
                    "left": p["left"],
                    "right": p["right"],
                    "left_text": texts[p["left"]],
                    "right_text": texts[p["right"]],
                }
            )
            for p in pairs
        )
        + "\n",
        encoding="utf-8",
    )
    KEYMAP.write_text(
        json.dumps({"units": keymap, "pairs": pairs}, indent=1), encoding="utf-8"
    )
    counts = collections.Counter(p["role"] for p in pairs)
    print(f"harvested {len(texts)} units from {sum(1 for a in arms.values() if a)} arms")
    for arm, items in arms.items():
        print(f"  {arm:<18} units={len(items)}")
    print(f"pairs: {counts['measure']} measured, {counts['control']} control")
    print(f"readings to make: {len(pairs) * JUDGES * 2}  ({JUDGES} judges x 2 orders per pair)")
    print("  blind/pairwise_pairs.jsonl   -> {pair_id, left, right, texts} only")
    print("  blind/pairwise_keymap.json   -> NOT to be opened until the choices exist")
    return 0


def _ask(key: str, text_a: str, text_b: str, attempts: int = 4) -> dict | None:
    body = json.dumps(
        {
            "model": MODEL,
            "messages": [{"role": "user", "content": _prompt(text_a, text_b)}],
            "temperature": 1.0,
            "max_tokens": 300,
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
            with urllib.request.urlopen(req, timeout=300) as r:
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
            choice = str(parsed["choice"]).strip().upper()[:1]
        except Exception:  # noqa: BLE001
            time.sleep(2 ** attempt)
            continue
        if choice not in ("A", "B"):
            return None
        return {"choice": choice, "why": parsed.get("why")}
    return None


def choose() -> int:
    key = _key()
    rows = [json.loads(l) for l in PAIRS.read_text().splitlines() if l]
    out: dict[str, dict] = {}
    if CHOICES.exists():
        out = json.loads(CHOICES.read_text())
    total = len(rows) * JUDGES * 2
    made = 0
    for i, row in enumerate(rows, 1):
        for judge in range(1, JUDGES + 1):
            for order in ("LR", "RL"):
                slot = f"{row['pair_id']}|{judge}|{order}"
                made += 1
                if slot in out:
                    continue
                if order == "LR":
                    got = _ask(key, row["left_text"], row["right_text"])
                else:
                    got = _ask(key, row["right_text"], row["left_text"])
                if got is None:
                    out[slot] = {"failed": True}
                else:
                    # Undo the position: which SIDE of the pair was chosen.
                    side = (
                        "left"
                        if (order == "LR" and got["choice"] == "A")
                        or (order == "RL" and got["choice"] == "B")
                        else "right"
                    )
                    out[slot] = {
                        "position": got["choice"],
                        "side": side,
                        "why": got["why"],
                    }
                CHOICES.write_text(json.dumps(out, indent=1), encoding="utf-8")
                print(f"  reading {made}/{total} pair {i}/{len(rows)} judge {judge} order {order}", flush=True)
                time.sleep(1.0)
    CHOICES.write_text(json.dumps(out, indent=1), encoding="utf-8")
    usable = sum(1 for v in out.values() if not v.get("failed"))
    print(f"choices {len(out)} ({usable} usable) -> blind/pairwise_choices.json")
    return 0


def _verdict(share: float | None) -> str:
    if share is None:
        return "INCONCLUSIVE"
    if share >= 2 / 3:
        return "BETTER"
    if share <= 1 / 3:
        return "WORSE"
    return "NULL"


def reveal(as_json: str | None = None) -> int:
    if not CHOICES.exists():
        raise SystemExit(
            "REFUSED: blind/pairwise_choices.json does not exist. The keymap "
            "stays shut until the choices are written."
        )
    choices = json.loads(CHOICES.read_text())
    keymap = json.loads(KEYMAP.read_text())
    units = keymap["units"]
    pairs = {p["pair_id"]: p for p in keymap["pairs"]}

    report: dict[str, dict] = {}
    rows = []
    for pair_id, pair in pairs.items():
        left, right = units[pair["left"]], units[pair["right"]]
        per_judge = []
        for judge in range(1, JUDGES + 1):
            lr = choices.get(f"{pair_id}|{judge}|LR", {})
            rl = choices.get(f"{pair_id}|{judge}|RL", {})
            if lr.get("failed") or rl.get("failed") or not lr or not rl:
                per_judge.append({"judge": judge, "outcome": "unread"})
                continue
            consistent = lr["side"] == rl["side"]
            per_judge.append(
                {
                    "judge": judge,
                    "order_LR": lr["side"],
                    "order_RL": rl["side"],
                    "consistent": consistent,
                    # A choice that flips with the order is NO PREFERENCE.
                    "outcome": (lr["side"] if consistent else "no-preference"),
                }
            )
        ratio = (left["chars"] / right["chars"]) if right["chars"] else None
        rows.append(
            {
                "pair_id": pair_id,
                "role": pair["role"],
                "treatment_arm": units[pair["left"]]["arm"],
                "control_arm": units[pair["right"]]["arm"],
                "treatment_source": left["source"],
                "control_source": right["source"],
                "treatment_chars": left["chars"],
                "control_chars": right["chars"],
                "length_ratio": ratio,
                "judges": per_judge,
            }
        )

    for row in rows:
        key = f"{row['treatment_arm']} vs {row['control_arm']}"
        bucket = report.setdefault(
            key,
            {
                "role": row["role"],
                "pairs": 0,
                "judge_pairs": 0,
                "wins": 0,
                "losses": 0,
                "no_preference": 0,
                "unread": 0,
                "length_ratios": [],
            },
        )
        bucket["pairs"] += 1
        bucket["length_ratios"].append(row["length_ratio"])
        for judge in row["judges"]:
            if judge["outcome"] == "unread":
                bucket["unread"] += 1
                continue
            bucket["judge_pairs"] += 1
            if judge["outcome"] == "left":
                bucket["wins"] += 1
            elif judge["outcome"] == "right":
                bucket["losses"] += 1
            else:
                bucket["no_preference"] += 1

    print("PAIRWISE_FORCED_CHOICE_V1  (PREREG Amendment 7)")
    print(f"  readings made : {sum(1 for v in choices.values() if not v.get('failed'))}")
    print(f"  readings lost : {sum(1 for v in choices.values() if v.get('failed'))}")
    print()
    print("  treatment unit          vs control unit           judges 1/2/3           ratio")
    for row in sorted(rows, key=lambda r: (r["role"], r["treatment_arm"], r["treatment_source"], r["control_source"])):
        outcomes = "/".join(j["outcome"][:4] for j in row["judges"])
        ratio = "n/a" if row["length_ratio"] is None else f"{row['length_ratio']:.2f}x"
        short = lambda ident: ident.split("@")[0]
        print(
            f"  {short(row['treatment_source']):<23} vs {short(row['control_source']):<23} "
            f"{outcomes:<22} {ratio}"
        )
    print()
    verdicts = {}
    for key, bucket in sorted(report.items()):
        share = (bucket["wins"] / bucket["judge_pairs"]) if bucket["judge_pairs"] else None
        verdict = _verdict(share)
        ratios = [r for r in bucket["length_ratios"] if r is not None]
        worst = max(ratios) if ratios else None
        # PREREG §6, applied to the verdict: a BETTER whose winning unit is
        # more than 1.5x the other's length is NULL (length-uncontrolled), and
        # the mirror holds for WORSE.
        downgraded = None
        if verdict == "BETTER" and worst is not None and worst > 1.5:
            downgraded, verdict = verdict, "NULL (length-uncontrolled)"
        if verdict == "WORSE" and worst is not None and worst < 1 / 1.5:
            downgraded, verdict = verdict, "NULL (length-uncontrolled)"
        bucket["consistent_win_share"] = share
        bucket["worst_length_ratio"] = worst
        bucket["verdict_before_length_rule"] = downgraded or verdict
        bucket["verdict"] = verdict
        verdicts[key] = verdict
        share_text = "n/a" if share is None else f"{bucket['wins']}/{bucket['judge_pairs']} = {share:.2f}"
        print(
            f"  [{bucket['role']}] {key}: consistent-win share {share_text}, "
            f"no preference {bucket['no_preference']}, "
            f"worst length ratio {'n/a' if worst is None else f'{worst:.2f}x'} -> {verdict}"
        )
    measured = [k for k, v in report.items() if v["role"] == "measure"]
    if len(measured) < 2 or any(report[k]["judge_pairs"] == 0 for k in measured):
        final = "INCONCLUSIVE -- an arm has no usable unit (PREREG §7 floor)"
    elif all(report[k]["verdict"] == "BETTER" for k in measured):
        final = "MATERIALLY BETTER -- BETTER than both bare arms"
    elif any(report[k]["verdict"] == "WORSE" for k in measured):
        final = "WORSE -- WORSE than a bare arm"
    else:
        final = "NULL"
    print()
    print(f"VERDICT (PREREG Amendment 7): {final}")
    if as_json:
        pathlib.Path(as_json).write_text(
            json.dumps(
                {
                    "schema": "pairwise-forced-choice.v1",
                    "verdict": final,
                    "arms": report,
                    "pairs": rows,
                },
                indent=1,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"wrote {as_json}")
    return 0


def criteria_check() -> int:
    """Prove the standard is the rubric's own five criteria, not a paraphrase."""

    text = _rubric_criteria()
    print(text)
    print(f"\nsha256 {hashlib.sha256(text.encode('utf-8')).hexdigest()}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=("harvest", "choose", "reveal", "criteria-check"))
    ap.add_argument("--json", default=None)
    a = ap.parse_args()
    if a.action == "reveal":
        return reveal(a.json)
    return {"harvest": harvest, "choose": choose, "criteria-check": criteria_check}[a.action]()


if __name__ == "__main__":
    sys.exit(main())
