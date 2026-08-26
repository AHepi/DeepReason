#!/usr/bin/env python3
"""W4 Q4, addendum: how good a PROXY is a verdict that is correctly ruled?

The 60-row sample answers "did the verdict rule correctly on the artifact"
and the answer is yes, 60 of 60. That is a statement about the RULING, not
about the CRITERION, and the two come apart. This probe measures one place
where they do, on the whole P-R1 population rather than the sample:

    `poietics-installation-mechanism@v1` requires at least one of
    ('compile.py', '1 of 9', '1/9', '3 of 26', '3/26', 'distribution',
     'every other module', 'ordinarily-guarded', 'ordinarily guarded').

    The operator's own question, verbatim in run-config.yaml, writes the
    distribution as "the 3-of-26 result ... compile.py 1/9 mutations lost".
    An artifact that echoes the question's HYPHENATED spelling and nothing
    else on that list satisfies the criterion's intent and fails its text.

The probe counts those artifacts, and how many were refuted on that exact
criterion. It rules nothing incorrect: every such verdict is correct as
specified, which is precisely why the number belongs in a separate file
from the ruling sample.

Writes criterion_proxy_probe.json.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ROOT = REPO / "experiments/2026-08-25-poietics-program/run"
W2 = REPO / "experiments/2026-08-26-run-anatomy-w2-criticism/pr1_census.json"
OUT = HERE / "criterion_proxy_probe.json"

CRITERION = "poietics-installation-mechanism@v1"
# Transcribed from the criterion's own `eval`, second clause.
LISTED = (
    "compile.py", "1 of 9", "1/9", "3 of 26", "3/26", "distribution",
    "every other module", "ordinarily-guarded", "ordinarily guarded",
)
# The question's own spellings, which the list above does not contain.
QUESTION_SPELLINGS = ("3-of-26", "1-of-9")


def contents() -> dict[str, str]:
    out: dict[str, str] = {}
    for path in sorted((ROOT / "objects" / "artifact").glob("*.json")):
        record = json.loads(path.read_text()).get("data", {})
        ref = str(record.get("content_ref") or "")
        if ref.startswith("inline:"):
            out[str(record.get("id"))] = ref[len("inline:"):]
    return out


def main() -> int:
    bodies = contents()
    census = json.loads(W2.read_text())
    refuted_on_criterion = {
        row["target"] for row in census["mechanical"] if row["commitment"] == CRITERION
    }
    invisible = []
    for aid, body in bodies.items():
        low = body.lower()
        if any(term in low for term in LISTED):
            continue
        spellings = [s for s in QUESTION_SPELLINGS if s in low]
        if spellings:
            invisible.append(
                {
                    "artifact": aid,
                    "question_spellings_present": spellings,
                    "refuted_on_this_criterion": aid in refuted_on_criterion,
                    "excerpt": body[:240],
                }
            )
    payload = {
        "schema": "w4.criterion-proxy-probe.v1",
        "criterion": CRITERION,
        "artifacts_with_inline_content": len(bodies),
        "artifacts_invisible_to_the_criterion_but_naming_the_distribution": len(
            invisible
        ),
        "of_those_refuted_on_this_criterion": sum(
            1 for row in invisible if row["refuted_on_this_criterion"]
        ),
        "verdicts_on_this_criterion_in_the_run": len(refuted_on_criterion),
        "rows": sorted(invisible, key=lambda r: r["artifact"]),
    }
    OUT.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
    print(
        json.dumps(
            {k: v for k, v in payload.items() if k != "rows"}, indent=1, sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
