#!/usr/bin/env python
"""Critic specificity — scoring and report
(pre-registered: experiments/critic_specificity_prereg.yaml).

Reads the committed critic judgments (experiments/critic_spec_run/
judgments.jsonl) plus both item files, computes sensitivity (conviction
rate on the 40 known-flawed t1 items) and the acquittal rate on the 40
verifier-anchored sound items, applies the prereg verdicts literally:

  P1 CONFIRMED iff sensitivity >= 0.85.
  P2 CONFIRMED iff acquittal >= 0.60; the falsifier fires iff
     acquittal < 0.40 (indiscriminate prosecutor -> survived-criticism
     metrics demoted record-wide).

Exploratory, non-verdict-bearing: defects named on sound-item convictions
are binned by simple ordered keyword rules into disputes-central-claim /
disputes-premise / demands-more-evidence / style-or-scope (counts only).

Writes experiments/results/critic_specificity_report.json
(schema deepreason-critic-spec-v1) and appends a line to the day's index.
Zero LLM tokens. Console output: ids/rates/counts only.

Usage: python scripts/critic_spec_score.py
"""

import datetime as dt
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PREREG = "experiments/critic_specificity_prereg.yaml"
SCHEMA = "deepreason-critic-spec-v1"
TOKEN_CEILING = 250_000

FLAWED_ITEMS = REPO / "experiments/e02_t1_items/known_flaws.json"
SOUND_ITEMS = REPO / "experiments/critic_spec_items/sound_items.json"
JUDGMENTS = REPO / "experiments/critic_spec_run/judgments.jsonl"
LEDGER = REPO / "experiments/critic_spec_run/token_usage.json"
RESULTS = REPO / "experiments/results"

# Ordered keyword rules (first match wins), exploratory only.
TAXONOMY_RULES = {
    "disputes-central-claim": [
        "miscalculat", "arithmetic", "should be", "does not equal",
        "calculation is wrong", "calculation error", "the claim is false",
        "the claim is incorrect", "the claim is wrong", "off by",
        "incorrect result", "incorrect total", "wrong answer",
    ],
    "disputes-premise": [
        "premise", "assumption", "assumes", "presuppos", "oversimplif",
        "the figure of", "given value", "definition", "conflat",
    ],
    "demands-more-evidence": [
        "no evidence", "unsupported", "unsubstantiated", "citation",
        "source", "does not provide", "lacks evidence", "not justified",
        "justification", "does not establish", "fails to show",
        "does not demonstrate", "without proof",
    ],
    "style-or-scope": [],  # fallback bin
}


def classify_defect(text: str, key_numbers: list[str]) -> str:
    low = (text or "").lower()
    # Naming the claim's primary answer number counts as engaging the
    # central claim (checked before the generic keyword lists).
    if key_numbers and key_numbers[0].lower() in low:
        return "disputes-central-claim"
    for bin_name, words in TAXONOMY_RULES.items():
        if any(w in low for w in words):
            return bin_name
    return "style-or-scope"


def main() -> int:
    flawed = json.loads(FLAWED_ITEMS.read_text())
    sound = json.loads(SOUND_ITEMS.read_text())
    assert len(flawed) == 40 and len(sound) == 40

    judgments: dict[str, dict] = {}
    for line in JUDGMENTS.read_text().splitlines():
        rec = json.loads(line)
        judgments[rec["id"]] = rec  # last write wins

    def rows(items, battery):
        out = []
        for item in sorted(items, key=lambda i: i["id"]):
            rec = judgments[item["id"]]
            assert rec["battery"] == battery, item["id"]
            out.append(rec)
        return out

    flawed_rows = rows(flawed, "flawed")
    sound_rows = rows(sound, "sound")

    n_flawed_convict = sum(r["convicts"] for r in flawed_rows)
    n_sound_convict = sum(r["convicts"] for r in sound_rows)
    sensitivity = round(n_flawed_convict / 40, 4)
    acquittal = round((40 - n_sound_convict) / 40, 4)
    parse_failures = sum(r["parse_failure"] for r in flawed_rows + sound_rows)

    p1 = "CONFIRMED" if sensitivity >= 0.85 else "REFUTED"
    p2 = "CONFIRMED" if acquittal >= 0.60 else "REFUTED"
    falsifier = acquittal < 0.40

    key_by_id = {i["id"]: i["hidden_annotation"]["key_numbers"]
                 for i in sound}
    taxonomy = {b: 0 for b in TAXONOMY_RULES}
    convicted_sound_ids = []
    for r in sound_rows:
        if r["convicts"]:
            convicted_sound_ids.append(r["id"])
            taxonomy[classify_defect(r["defect"], key_by_id[r["id"]])] += 1

    per_item = {}
    sound_by_id = {i["id"]: i for i in sound}
    for r in flawed_rows + sound_rows:
        entry = {
            "battery": r["battery"],
            "convicts": r["convicts"],
            "defect_found": r["defect_found"],
            "defect": r["defect"],
            "parse_failure": r["parse_failure"],
            "json_retries": r["json_retries"],
            "transport_retries": r["transport_retries"],
        }
        if r["battery"] == "sound":
            item = sound_by_id[r["id"]]
            entry["topic"] = item["topic"]
            entry["template"] = item["template"]
            entry["verified_true"] = item["hidden_annotation"]["verified_true"]
            if r["convicts"]:
                entry["defect_bin_exploratory"] = classify_defect(
                    r["defect"], key_by_id[r["id"]])
        per_item[r["id"]] = entry

    ledger = json.loads(LEDGER.read_text())
    total_tokens = ledger["prompt_tokens"] + ledger["completion_tokens"]
    assert total_tokens <= TOKEN_CEILING, \
        f"spend {total_tokens} over cap {TOKEN_CEILING}"

    verdicts = {
        "P1": {"verdict": p1,
               "measured": {"flawed_convictions": n_flawed_convict,
                            "n": 40, "sensitivity": sensitivity},
               "threshold": "conviction rate >= 0.85 on the flawed set"},
        "P2": {"verdict": p2,
               "falsifier_triggered": falsifier,
               "measured": {"sound_acquittals": 40 - n_sound_convict,
                            "sound_convictions": n_sound_convict,
                            "n": 40, "acquittal_rate": acquittal},
               "threshold": "acquittal rate >= 0.60 on the verified-sound "
                            "set; falsifier fires below 0.40 "
                            "(indiscriminate prosecutor -> "
                            "survived-criticism metrics demoted "
                            "record-wide, Tier 2/3 survivor counting "
                            "needs a defended-trial redesign)"},
    }

    caveats = [
        "The sound arguments are adversary-authored (deepseek-v4-pro): "
        "only each item's CENTRAL claim is mechanically verified true by a "
        "trusted local checker; the surrounding prose is model-written and "
        "could contain incidental misstatements a critic might correctly "
        "attack. Convictions on sound items are therefore an UPPER bound "
        "on false-conviction rate.",
        "The checkable-claim domain (arithmetic, combinatorial, "
        "graph-shortest-path, calendar facts on seven neutral topic pools) "
        "is much narrower than the open explanatory prose the critic "
        "faces in the harness; specificity measured here may not transfer "
        "to open-domain artifacts.",
        "Single critic model (deepseek-v4-flash), single prompt shape, "
        "temperature 0.0; no ensemble, no model-family variation.",
        "The fielded critic prompt (t2b shape, reused verbatim) tells the "
        "critic that 'an ensemble of independent judges flagged' the "
        "artifact — prosecutorial framing. It is applied identically to "
        "both batteries, so the sensitivity/specificity CONTRAST is "
        "clean, but absolute acquittal rates are measured under "
        "conviction-favouring framing.",
        "Parse failures never convict (t2b rule); they inflate acquittal "
        "on sound items and deflate sensitivity on flawed items "
        f"(observed parse failures: {parse_failures}).",
        "The defect taxonomy is exploratory and non-verdict-bearing: "
        "simple ordered keyword rules (first match wins; naming the "
        "claim's primary answer number counts as central-claim "
        "engagement), not human or model adjudication.",
        "Sensitivity anchor is the frozen t1 known-flaw battery "
        "(planted, taxonomy-style flaws); it replicates t1's measurement "
        "conditions, not open-domain flaw detection.",
    ]

    report = {
        "schema": SCHEMA,
        "prereg": PREREG,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "design": {
            "instrument": {
                "model": "deepseek-v4-flash", "temperature": 0.0,
                "schema": '{"defect_found": bool, "defect": str}',
                "prompt_shape": "scripts/e02_t2b_readjudicate.py "
                                "CRITIC_PROMPT, reused verbatim",
                "conviction": "defect_found AND named defect string >= 20 "
                              "chars, != 'none'; parse failure never "
                              "convicts",
            },
            "specificity_set": "40 verifier-anchored sound arguments; "
                               "central claims instantiated from seeded "
                               "templates and verified TRUE by trusted "
                               "local checkers "
                               "(scripts/critic_spec_corpus.py); "
                               "arguments by deepseek-v4-pro, gated to "
                               "contain the claim's exact numbers",
            "sensitivity_anchor": "40 frozen known-flawed t1 items "
                                  "(experiments/e02_t1_items/"
                                  "known_flaws.json)",
            "concurrency_max_in_flight": 3,
        },
        "rates": {
            "sensitivity_flawed_conviction_rate": sensitivity,
            "sound_conviction_rate": round(n_sound_convict / 40, 4),
            "sound_acquittal_rate": acquittal,
            "specificity": acquittal,
        },
        "verdicts": verdicts,
        "exploratory_defect_taxonomy_sound_convictions": {
            "note": "non-verdict-bearing; ordered keyword rules, counts "
                    "only",
            "rules": {k: v for k, v in TAXONOMY_RULES.items()},
            "primary_number_rule": "defect text containing the claim's "
                                   "primary answer number bins as "
                                   "disputes-central-claim before any "
                                   "keyword list",
            "counts": taxonomy,
            "convicted_sound_ids": convicted_sound_ids,
        },
        "per_item": per_item,
        "token_spend": {
            "ledger": ledger,
            "total_tokens": total_tokens,
            "ceiling": TOKEN_CEILING,
        },
        "caveats": caveats,
    }
    RESULTS.mkdir(parents=True, exist_ok=True)
    report_path = RESULTS / "critic_specificity_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n")

    index_path = RESULTS / f"INDEX_{dt.date.today().isoformat()}.md"
    tax_str = ", ".join(f"{k} {v}" for k, v in taxonomy.items())
    falsifier_note = (" — FALSIFIER TRIGGERED: survived-criticism metrics "
                      "demoted record-wide" if falsifier else "")
    index_line = (
        f"\n## Critic specificity ({dt.date.today().isoformat()})\n\n"
        f"P1 {p1} (sensitivity {sensitivity} = {n_flawed_convict}/40 "
        f"flawed convicted, bar 0.85), "
        f"P2 {p2} (acquittal {acquittal} = {40 - n_sound_convict}/40 "
        f"verified-sound acquitted, bar 0.60, falsifier 0.40"
        f"{falsifier_note}). "
        f"Exploratory sound-conviction defect bins: {tax_str}. "
        f"{total_tokens} live LLM tokens (cap {TOKEN_CEILING}). "
        f"Prereg: `{PREREG}`. Report: "
        f"`experiments/results/critic_specificity_report.json`. Corpus: "
        f"`experiments/critic_spec_items/`, judgments: "
        f"`experiments/critic_spec_run/judgments.jsonl`.\n")
    with index_path.open("a") as fh:
        fh.write(index_line)

    print(json.dumps({
        "verdicts": {"P1": p1, "P2": p2, "P2_falsifier": falsifier},
        "sensitivity": sensitivity,
        "acquittal": acquittal,
        "taxonomy": taxonomy,
        "tokens": total_tokens,
    }, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
