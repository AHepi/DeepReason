#!/usr/bin/env python
"""Defended trial v1 — scoring and report
(pre-registered: experiments/defended_trial_v1_prereg.yaml).

Reads the committed baseline judgments (arm A, replayed — zero tokens),
the arm-B neutral-critic judgments and arm-C trial records
(experiments/defended_trial_run/), computes per-arm conviction/acquittal
rates on the 40 verified-sound and 40 known-flawed items, and applies the
prereg verdicts literally:

  P1 CONFIRMED iff arm-B sound acquittal >= 0.475
     (a >= 15pp lift over the 0.325 baseline).
  P2 CONFIRMED iff arm-C sound acquittal >= 0.70 AND arm-C flawed
     conviction >= 0.60; the falsifier fires iff arm-C sound acquittal
     < 0.50 (defense does not restore specificity).
  P3 CONFIRMED iff arm-C abstention on flawed items <= 0.40.

Outcome semantics (prereg): only a doubly-sustained objection convicts;
overrule acquits; arm-B acquittals pass through as acquittals; abstention
(order-swap disagreement, malformed reply, or a concurring abstain) is
its own outcome — NOT an acquittal. Non-conviction rates are also
reported (exploratory).

Exploratory, non-verdict-bearing: order-swap disagreement rate; defect
taxonomy (critic_spec_score keyword bins) on arm-C sustained sound
convictions.

Writes experiments/results/defended_trial_v1_report.json
(schema deepreason-defended-trial-v1) and appends a line to the day's
index. Zero LLM tokens. Console output: ids/rates/counts only.

Usage: python scripts/defended_trial_score.py
"""

import datetime as dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from critic_spec_score import TAXONOMY_RULES, classify_defect  # noqa: E402

PREREG = "experiments/defended_trial_v1_prereg.yaml"
SCHEMA = "deepreason-defended-trial-v1"
TOKEN_CEILING = 400_000

FLAWED_ITEMS = REPO / "experiments/e02_t1_items/known_flaws.json"
SOUND_ITEMS = REPO / "experiments/critic_spec_items/sound_items.json"
BASELINE_JUDGMENTS = REPO / "experiments/critic_spec_run/judgments.jsonl"
RUN_DIR = REPO / "experiments/defended_trial_run"
RESULTS = REPO / "experiments/results"


def read_jsonl(path: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for line in path.read_text().splitlines():
        rec = json.loads(line)
        out[rec["id"]] = rec  # last write wins
    return out


def rate(n: int, d: int) -> float:
    return round(n / d, 4)


def main() -> int:
    flawed = json.loads(FLAWED_ITEMS.read_text())
    sound = json.loads(SOUND_ITEMS.read_text())
    assert len(flawed) == 40 and len(sound) == 40
    battery = {i["id"]: "flawed" for i in flawed}
    battery.update({i["id"]: "sound" for i in sound})
    ids = sorted(battery)

    arm_a = read_jsonl(BASELINE_JUDGMENTS)
    arm_b = read_jsonl(RUN_DIR / "arm_b.jsonl")
    arm_c_path = RUN_DIR / "arm_c.jsonl"
    arm_c = read_jsonl(arm_c_path) if arm_c_path.exists() else {}
    assert set(arm_a) == set(ids) and set(arm_b) == set(ids)
    b_convicted = {i for i in ids if arm_b[i]["convicts"]}
    assert set(arm_c) == b_convicted, "arm C must cover exactly arm-B convictions"

    # Per-item arm-C outcome: convicted / acquitted / abstained.
    def c_outcome(item_id: str) -> str:
        if item_id not in b_convicted:
            return "acquitted"  # arm-B acquittal passes through
        o = arm_c[item_id]["outcome"]
        return {"sustain": "convicted", "overrule": "acquitted",
                "abstain": "abstained"}[o]

    counts: dict[str, dict] = {}
    for bat in ("sound", "flawed"):
        bat_ids = [i for i in ids if battery[i] == bat]
        n = len(bat_ids)
        a_conv = sum(arm_a[i]["convicts"] for i in bat_ids)
        b_conv = sum(arm_b[i]["convicts"] for i in bat_ids)
        c_out = [c_outcome(i) for i in bat_ids]
        c_conv = c_out.count("convicted")
        c_acq = c_out.count("acquitted")
        c_abs = c_out.count("abstained")
        counts[bat] = {
            "n": n,
            "arm_a": {"convictions": a_conv,
                      "conviction_rate": rate(a_conv, n),
                      "acquittal_rate": rate(n - a_conv, n)},
            "arm_b": {"convictions": b_conv,
                      "conviction_rate": rate(b_conv, n),
                      "acquittal_rate": rate(n - b_conv, n)},
            "arm_c": {"convictions": c_conv, "acquittals": c_acq,
                      "abstentions": c_abs,
                      "conviction_rate": rate(c_conv, n),
                      "acquittal_rate": rate(c_acq, n),
                      "abstention_rate": rate(c_abs, n),
                      "non_conviction_rate_exploratory": rate(n - c_conv, n)},
        }

    # Verdicts, applied literally.
    b_sound_acq = counts["sound"]["arm_b"]["acquittal_rate"]
    c_sound_acq = counts["sound"]["arm_c"]["acquittal_rate"]
    c_flawed_conv = counts["flawed"]["arm_c"]["conviction_rate"]
    c_flawed_abs = counts["flawed"]["arm_c"]["abstention_rate"]
    p1 = "CONFIRMED" if b_sound_acq >= 0.475 else "REFUTED"
    p2 = ("CONFIRMED" if (c_sound_acq >= 0.70 and c_flawed_conv >= 0.60)
          else "REFUTED")
    p2_falsifier = c_sound_acq < 0.50
    p3 = "CONFIRMED" if c_flawed_abs <= 0.40 else "REFUTED"

    # Exploratory: order-swap disagreement rate over trials that reached
    # two valid adjudicator verdicts.
    swap_known = [r for r in arm_c.values()
                  if r.get("order_swap_disagreement") is not None]
    swap_disagree = sum(1 for r in swap_known if r["order_swap_disagreement"])
    abstain_reasons: dict[str, int] = {}
    for r in arm_c.values():
        if r["outcome"] == "abstain":
            k = r.get("abstain_reason") or "unspecified"
            abstain_reasons[k] = abstain_reasons.get(k, 0) + 1

    # Exploratory: defect taxonomy on arm-C SUSTAINED sound convictions.
    key_by_id = {i["id"]: i["hidden_annotation"]["key_numbers"]
                 for i in sound}
    taxonomy = {b: 0 for b in TAXONOMY_RULES}
    sustained_sound_ids = []
    for i in ids:
        if battery[i] == "sound" and c_outcome(i) == "convicted":
            sustained_sound_ids.append(i)
            taxonomy[classify_defect(arm_b[i]["defect"], key_by_id[i])] += 1

    per_item = {}
    for i in ids:
        c_rec = arm_c.get(i)
        per_item[i] = {
            "battery": battery[i],
            "arm_a": {"convicts": arm_a[i]["convicts"],
                      "parse_failure": arm_a[i]["parse_failure"]},
            "arm_b": {"convicts": arm_b[i]["convicts"],
                      "defect_found": arm_b[i]["defect_found"],
                      "defect": arm_b[i]["defect"],
                      "parse_failure": arm_b[i]["parse_failure"]},
            "arm_c": ({
                "tried": True, "outcome": c_rec["outcome"],
                "classification": c_outcome(i),
                "abstain_reason": c_rec.get("abstain_reason"),
                "order_swap_disagreement": c_rec.get("order_swap_disagreement"),
                "adjudicator_verdicts": [a["verdict"] for a in
                                         c_rec.get("adjudications", [])],
                "defender_parse_failure": c_rec.get("defender_parse_failure"),
            } if c_rec is not None else
                {"tried": False, "classification": "acquitted",
                 "note": "arm-B acquittal passes through"}),
        }

    ledger = json.loads((RUN_DIR / "token_usage.json").read_text())
    total_tokens = ledger["prompt_tokens"] + ledger["completion_tokens"]
    assert total_tokens <= TOKEN_CEILING, \
        f"spend {total_tokens} over cap {TOKEN_CEILING}"
    b_parse_failures = sum(arm_b[i]["parse_failure"] for i in ids)

    verdicts = {
        "P1": {"verdict": p1,
               "measured": {
                   "arm_b_sound_acquittals":
                       counts["sound"]["n"]
                       - counts["sound"]["arm_b"]["convictions"],
                   "n": 40,
                   "arm_b_sound_acquittal_rate": b_sound_acq,
                   "arm_a_baseline_sound_acquittal_rate":
                       counts["sound"]["arm_a"]["acquittal_rate"]},
               "threshold": "neutral framing lifts sound acquittal >= 15pp "
                            "over the 0.325 baseline (>= 0.475)"},
        "P2": {"verdict": p2,
               "falsifier_triggered": p2_falsifier,
               "measured": {
                   "arm_c_sound_acquittal_rate": c_sound_acq,
                   "arm_c_sound_acquittals":
                       counts["sound"]["arm_c"]["acquittals"],
                   "arm_c_sound_abstentions":
                       counts["sound"]["arm_c"]["abstentions"],
                   "arm_c_flawed_conviction_rate": c_flawed_conv,
                   "arm_c_flawed_convictions":
                       counts["flawed"]["arm_c"]["convictions"],
                   "n_per_battery": 40},
               "threshold": "defended sound acquittal >= 0.70 AND flawed "
                            "conviction >= 0.60; falsifier fires below "
                            "0.50 sound acquittal (defense does not "
                            "restore specificity; observe-only becomes "
                            "the default criticism policy and the v2 "
                            "build narrows to the scrutiny view plus "
                            "attention-only objections)"},
        "P3": {"verdict": p3,
               "measured": {
                   "arm_c_flawed_abstention_rate": c_flawed_abs,
                   "arm_c_flawed_abstentions":
                       counts["flawed"]["arm_c"]["abstentions"],
                   "n": 40},
               "threshold": "arm-C abstention on flawed items <= 0.40 "
                            "(the court still decides)"},
    }

    caveats = [
        "MINIMAL TRIAL, not the full spec-10 protocol: one objection per "
        "item (the arm-B critic's), one defender pass, one adjudicator "
        "model consulted twice with order swap — no multi-round exchange, "
        "no juror ensemble.",
        "Single defender (deepseek-v4-pro) and single adjudicator "
        "(mistral-large-3:675b, the 0.00-FP zoo seat); results may not "
        "transfer across model families.",
        "Checkable-claim domain only (arithmetic, combinatorial, "
        "graph-shortest-path, calendar facts) — much narrower than the "
        "open explanatory prose the harness criticises; rates may not "
        "transfer to open-domain artifacts.",
        "Sound items are adversary-authored: only each item's CENTRAL "
        "claim is mechanically verified true; convictions on sound items "
        "are an UPPER bound on false conviction.",
        "Acquittal is scored STRICTLY: arm-C abstentions (order-swap "
        "disagreement, malformed replies, concurring abstains) are "
        "neither convictions nor acquittals. Non-conviction rates are "
        "reported as exploratory context.",
        "The defender sees the artifact and the objection but not the "
        "battery label; the adjudicator sees artifact, objection, and "
        "defence only. Neither is told about prior flags or judges.",
        "Arm A is a replay of the committed critic_specificity judgments "
        "(prosecutorial prompt, same critic model); arm B changes ONLY "
        "the framing, so the A-vs-B contrast isolates framing, not "
        "model or conviction rule.",
        f"Parse failures never convict (arm-B parse failures: "
        f"{b_parse_failures}); in arm C any malformed reply forces "
        f"abstain, which deflates both conviction and acquittal rates.",
        "Defect taxonomy and order-swap disagreement rate are "
        "exploratory and non-verdict-bearing (ordered keyword rules from "
        "critic_spec_score, counts only).",
    ]

    report = {
        "schema": SCHEMA,
        "prereg": PREREG,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "design": {
            "items": "40 verified-sound (experiments/critic_spec_items/"
                     "sound_items.json) + 40 known-flawed "
                     "(experiments/e02_t1_items/known_flaws.json), frozen",
            "arm_a": "bare prosecutorial critic, REPLAYED from "
                     "experiments/critic_spec_run/judgments.jsonl "
                     "(zero new tokens)",
            "arm_b": {"model": "deepseek-v4-flash", "temperature": 0.0,
                      "prompt": "neutral 'assess for ONE material, "
                                "checkable defect' — no prosecutorial "
                                "framing, no mention of prior flags or "
                                "judges (scripts/defended_trial_run.py "
                                "NEUTRAL_CRITIC_PROMPT)",
                      "conviction_rule": "defect_found AND named defect "
                                         ">= 20 chars, != 'none'; parse "
                                         "failure never convicts (same "
                                         "as arm A)"},
            "arm_c": {"defender": "deepseek-v4-pro (artifact + objection; "
                                  "strict JSON {defence: str})",
                      "adjudicator": "mistral-large-3:675b, temp 0, run "
                                     "twice with presentation order "
                                     "swapped; strict JSON {verdict: "
                                     "sustain|overrule|abstain}",
                      "rule": "disagreement or malformed reply -> "
                              "abstain; only sustain convicts; arm-B "
                              "acquittals pass through"},
            "concurrency_max_in_flight": 3,
        },
        "rates": counts,
        "verdicts": verdicts,
        "exploratory": {
            "order_swap": {
                "trials_with_two_valid_verdicts": len(swap_known),
                "disagreements": swap_disagree,
                "disagreement_rate": (rate(swap_disagree, len(swap_known))
                                      if swap_known else None)},
            "arm_c_abstain_reasons": abstain_reasons,
            "defect_taxonomy_sustained_sound_convictions": {
                "note": "non-verdict-bearing; ordered keyword rules "
                        "(critic_spec_score), counts only",
                "counts": taxonomy,
                "sustained_sound_ids": sustained_sound_ids},
        },
        "per_item": per_item,
        "token_spend": {"ledger": ledger, "total_tokens": total_tokens,
                        "arm_a_tokens": 0, "ceiling": TOKEN_CEILING},
        "caveats": caveats,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "defended_trial_v1_report.json").write_text(
        json.dumps(report, indent=2) + "\n")

    today = dt.date.today().isoformat()
    index_path = RESULTS / f"INDEX_{today}.md"
    falsifier_note = (" — FALSIFIER TRIGGERED: observe-only becomes the "
                      "default criticism policy" if p2_falsifier else "")
    index_line = (
        f"\n## Defended trial v1 ({today})\n\n"
        f"P1 {p1} (arm-B neutral sound acquittal {b_sound_acq} vs "
        f"baseline {counts['sound']['arm_a']['acquittal_rate']}, bar "
        f"0.475), P2 {p2} (arm-C defended sound acquittal {c_sound_acq}, "
        f"bar 0.70; flawed conviction {c_flawed_conv}, bar 0.60; "
        f"falsifier 0.50{falsifier_note}), P3 {p3} (arm-C flawed "
        f"abstention {c_flawed_abs}, bar 0.40). Order-swap disagreement "
        f"{swap_disagree}/{len(swap_known)} (exploratory). "
        f"{total_tokens} live LLM tokens (cap {TOKEN_CEILING}; arm A "
        f"replayed at zero). Prereg: `{PREREG}`. Report: "
        f"`experiments/results/defended_trial_v1_report.json`. Runs: "
        f"`experiments/defended_trial_run/`.\n")
    with index_path.open("a") as fh:
        fh.write(index_line)

    print(json.dumps({
        "verdicts": {"P1": p1, "P2": p2, "P2_falsifier": p2_falsifier,
                     "P3": p3},
        "rates": {b: {a: counts[b][a] for a in ("arm_a", "arm_b", "arm_c")}
                  for b in counts},
        "order_swap_disagreement": f"{swap_disagree}/{len(swap_known)}",
        "taxonomy": taxonomy,
        "tokens": total_tokens,
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
