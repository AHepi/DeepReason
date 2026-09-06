"""NOT PRE-REGISTERED. Exploratory, run after the reveal, labelled as such.

The pre-registered unit for ARM M is one conjecture; the copied rubric scores
a complete answer (both cases, verdict, cost), which a 550-character
conjecture cannot carry. This asks the obvious follow-up without a new arm:
score ARM M's eight conjectures COMPOSED into one text, oldest first, with the
same three judges and the same criteria. One candidate, three judge calls,
no re-run of any arm. Its result is descriptive and decides nothing under
PREREG_D8 §4.
"""

from __future__ import annotations

import json
import pathlib
import statistics
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from judge_d8 import _armM_texts, _ask, _key  # noqa: E402


def main() -> int:
    texts = _armM_texts()  # record order: oldest first
    composed = "\n\n".join(f"Conjecture {i}: {t}" for i, (_, t) in enumerate(texts, 1))
    key = _key()
    judges = [j for j in (_ask(key, composed) for _ in range(3)) if j]
    totals = sorted(j["total"] for j in judges)
    out = {
        "schema": "d8-explore-composed.v1",
        "pre_registered": False,
        "unit": "all ARM M conjectures composed oldest-first",
        "conjectures": len(texts),
        "chars": len(composed),
        "judges": len(judges),
        "totals": totals,
        "median": statistics.median(totals) if totals else None,
        "detail": judges,
    }
    (HERE / "EXPLORE_COMPOSED.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "detail"}, indent=1))
    for j in judges:
        print(j["total"], j["why"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
