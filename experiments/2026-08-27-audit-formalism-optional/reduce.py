"""Reduce the sweep's raw hits to KIND-READS: the sites that could move an outcome.

    python .../sweep.py > SWEEP_RAW.json && python .../reduce.py

A raw hit is PLUMBING unless the kind signal is used in a BOOLEAN position --
a conditional, a comprehension filter, a comparison against an `eval` string, a
membership test, or an `any`/`all`. Iterating a commitment list, passing a
registry as an argument, or serialising an interface moves no outcome, and the
audit says so mechanically rather than by eye.

The reduction is deliberately generous: a line kept here still has to be read
and classified by hand into LAWFUL-PROTECTION / UNLAWFUL-PENALTY /
STRUCTURAL-GAP / NEUTRAL.  What it guarantees is that nothing EXECUTABLE and
BOOLEAN was dropped without a reader seeing it.
"""

import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))

# The signal must be a KIND signal, not merely one of the outcome words: a line
# mentioning "attention" or "allocate" says nothing about formal vs informal.
KIND_SIGNAL = re.compile(
    r"execution_backed|formally_backed|programs\.evaluable|candidate_checker"
    r"|checker_spec|EXEC_PROGRAMS|is_pure_code|DEMONSTRATIVE|ARGUMENTATIVE"
    r"|property_oracle|exec_oracle|\.commitments|active_properties"
    r"|observation_valued|is_hv_floor|demarcat|_substantive|parse_skeleton"
    r"|\beval\b"
)

BOOLEAN = re.compile(
    r"(^|\W)(if|not|and|or|any|all|assert|while|elif)(\W|$)"
    r"|[=!]=|\bin\b|\bis\b|\bstartswith\b|\bcontinue\b|\breturn (True|False)\b"
)


def main():
    raw = json.load(open(os.path.join(HERE, "SWEEP_RAW.json")))
    kept, dropped = [], []
    for hit in raw["hits"]:
        if not hit["code"]:
            dropped.append((hit, "not-executable"))
            continue
        if not KIND_SIGNAL.search(hit["text"]):
            dropped.append((hit, "outcome-word-only-no-kind-signal"))
            continue
        if not BOOLEAN.search(hit["text"]):
            dropped.append((hit, "plumbing-not-a-boolean-position"))
            continue
        kept.append(hit)

    reasons = Counter(reason for _hit, reason in dropped)
    out = {
        "schema": "formalism-audit.kind-reads.v1",
        "raw_hits": raw["raw_hits"],
        "code_hits": raw["code_hits"],
        "kind_reads": len(kept),
        "dropped": dict(reasons),
        "per_file": dict(Counter(h["file"] for h in kept).most_common()),
        "sites": kept,
    }
    json.dump(out, open(os.path.join(HERE, "KIND_READS.json"), "w"), indent=1)
    print(f"raw={raw['raw_hits']} code={raw['code_hits']} kind_reads={len(kept)}")
    for reason, count in reasons.most_common():
        print(f"  dropped {count:5d}  {reason}")
    print()
    for path, count in Counter(h["file"] for h in kept).most_common():
        print(f"{count:4d}  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
