#!/usr/bin/env python3
"""Emit EXEMPLARS.md: the verbatim bytes behind W4's sharpest rows.

The rows are chosen by hand and named here; the BYTES are pulled from the
committed sample so nothing is retyped. Each exemplar states what a reader
should check in it, then quotes it.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SAMPLE = json.loads((HERE / "verdict_sample.json").read_text())
HAND = json.loads((HERE / "handcheck.json").read_text())
PROXY = json.loads((HERE / "criterion_proxy_probe.json").read_text())

_PC1 = [r for r in HAND["rows"] if r["root"] == "P-C1"]
_ZERO_POINT = sum(1 for r in _PC1 if r["check"].get("n_points") == 0)
_THIRTEEN_POINT = sum(1 for r in _PC1 if r["check"].get("n_points") == 13)

CHOSEN = [
    (
        "P-C1", 196, "E1",
        "A verdict a reader can check without arithmetic",
        "`frontier-wellformed@v1` demands exactly 13 distinct POINT lines. "
        "This artifact lists twelve, and says so itself: its own mechanism "
        "field calls the configuration \"4-3-2-3 Layered\", which sums to "
        "12. The verdict is `fail` and it is right, and nothing about the "
        "check depends on trusting a min-area computation.",
        1300,
    ),
    (
        "P-C1", 733, "E2",
        "A verdict against an artifact that described a construction "
        "instead of emitting one",
        "The predicate reads POINT lines out of the content. This artifact "
        "has none: it describes \"a 4x4 grid with the point (1/3, 1/3) "
        "removed, achieving a minimum triangle area of 0.013\" in prose and "
        "never writes the points down. The verdict is `fail`, and the "
        "reason is not that the construction is bad — it is that no "
        "construction was submitted. "
        + str(_ZERO_POINT)
        + " of the thirty sampled P-C1 rows are this shape, and one more "
        "(E1) submits twelve points where thirteen are demanded; only "
        + str(_THIRTEEN_POINT)
        + " submitted a well-formed thirteen-point set at all.",
        900,
    ),
    (
        "P-C1", 947, "E3",
        "A collinear triple, verifiable by eye",
        "The witness triple is (0, 0), (0.25, 0.25), (0.5, 0.5) — three "
        "points on the line y = x, so the triangle area is exactly 0 and "
        "the 0.005 floor cannot be met. No computation is needed to check "
        "this one; the three points are in the quoted bytes.",
        700,
    ),
    (
        "P-R1", 2140, "E4",
        "The verdict is correct and the criterion is wrong",
        "`poietics-installation-mechanism@v1` needs (a) two installation "
        "terms and (b) one of nine distribution spellings. This artifact "
        "clears (a) six times over and fails (b) — because it writes the "
        "distribution as \"the 3-of-26 result\", the operator's own "
        "hyphenated spelling from the question, and the criterion's list "
        "carries only '3 of 26' and '3/26'. The verdict is CORRECT as "
        "specified. The criterion is a bad proxy for what it was built to "
        "test, and "
        f"{PROXY['of_those_refuted_on_this_criterion']} of the "
        f"{PROXY['verdicts_on_this_criterion_in_the_run']} verdicts it "
        "issued in the whole run land on artifacts of exactly this kind.",
        900,
    ),
    (
        "P-R1", 1002, "E5",
        "A substantive confound argument, one term short",
        "`poietics-confound@v1` needs two of eleven terms. This artifact "
        "argues the confound directly — it proposes a control condition "
        "with the installation order reversed — and scores one ('confound' "
        "inside 'confounded'). `fail` is correct as specified; whether the "
        "artifact deserved refuting on the confound question is a different "
        "matter this census does not rule on.",
        1200,
    ),
    (
        "P-R1", 503, "E6",
        "The row that broke the checker before it passed it",
        "`relation-form@578e42df713e` is a two-conjunct predicate: "
        "'refuted if' present AND one of nine relation keywords. The "
        "artifact says \"shares a mechanism with\"; the list carries "
        "'shares mechanism' and 'shared mechanism', not 'shares a "
        "mechanism'. So conjunct one holds, conjunct two does not, and "
        "`fail` is correct. The first version of `handcheck.py` parsed only "
        "the second conjunct and silently dropped the first — the ruling "
        "survived because the dropped conjunct was the TRUE one. "
        "`terms_from_eval` now returns its conjunct count and the checker "
        "refuses to rule when the two disagree.",
        700,
    ),
]


def main() -> int:
    index = {
        (root, entry["seq"]): entry
        for root, block in SAMPLE["roots"].items()
        for entry in block["sample"]
    }
    rulings = {(r["root"], r["seq"]): r for r in HAND["rows"]}
    out = ["# W4 — exemplars, verbatim", ""]
    out.append(
        "Generated by `python3 exemplars.py`. Rows chosen by hand; bytes "
        "pulled from `verdict_sample.json`, never retyped. Excerpts are "
        "truncated at the character count named in each heading and marked "
        "where truncation happens."
    )
    out.append("")
    for root, seq, tag, title, note, limit in CHOSEN:
        entry = index[(root, seq)]
        ruling = rulings[(root, seq)]
        out.append(f"## {tag} — {title}")
        out.append("")
        out.append(
            f"`{root}` seq {seq} · commitment `{entry['commitment']}` · "
            f"recorded verdict **{entry['recorded_verdict']}** · independent "
            f"predicate **{ruling['independent_predicate_holds']}** · ruling "
            f"**{ruling['ruling']}** · target now "
            f"`{entry['target_status_final']}`"
        )
        out.append("")
        out.append(note)
        out.append("")
        body = entry["content"] or ""
        clipped = body[:limit]
        out.append("```")
        out.append(clipped)
        if len(body) > limit:
            out.append(f"… [truncated at {limit} of {len(body)} characters]")
        out.append("```")
        out.append("")
    (HERE / "EXEMPLARS.md").write_text("\n".join(out) + "\n")
    print("wrote EXEMPLARS.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
