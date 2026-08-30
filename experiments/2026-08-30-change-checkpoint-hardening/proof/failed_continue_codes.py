"""Which refusal does `continue` actually raise on a failure terminal?

S5 first recorded `continue_refusal="CONTINUE_TYPED_STOP_REQUIRED"` as a
CONSTANT inside the terminal that cannot know it.  This measures the
population that constant spoke for: every committed root whose state is
`failed` with `stop_reason: operational_failure` -- the exact shape S5's branch
produces -- driven through `prepare_continuation` on a COPY.

The answer decided the skeptic pass: the field is not derivable at terminal
time (the code also depends on the cycles and tokens the operator later passes,
and on a resume decision an earlier continuation may have left), and it is not
even constant across the population.

    python experiments/2026-08-30-change-checkpoint-hardening/proof/failed_continue_codes.py

Copies only, always: `prepare_continuation` writes `run-stops/` before it can
refuse. Reads census.json, writes failed_continue_codes.json beside itself.
Written 2026-08-30, skeptic pass.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CENSUS = HERE / "census.json"
OUT = HERE / "failed_continue_codes.json"


def drive(root: Path) -> dict:
    from deepreason.runtime.continuation import prepare_continuation

    files = {
        name: (root / name).exists()
        for name in ("run-stop.json", "checkpoint.json", "run-result.json")
    }
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / root.name
        shutil.copytree(root, copy, symlinks=True)
        try:
            record = prepare_continuation(
                copy, cycles=1, tokens=10, check_operator_lock=False
            )
            outcome = f"ACCEPTED seq={record.get('seq')}"
        except Exception as error:  # noqa: BLE001 - the observation IS the outcome
            outcome = f"{type(error).__name__}: {error}"
    return {"files": files, "continue": outcome}


def main() -> int:
    sys.path.insert(0, str(REPO / "src"))
    census = json.loads(CENSUS.read_text())
    targets = sorted(
        row["root"]
        for row in census["rows"]
        if row.get("state") == "failed"
        and row.get("stop_reason") == "operational_failure"
    )
    rows = []
    for index, rel in enumerate(targets, 1):
        row = {"root": rel}
        row.update(drive(REPO / rel))
        rows.append(row)
        print(f"[{index}/{len(targets)}] {row['continue']}  {rel}", flush=True)
    payload = {
        "population": len(rows),
        "outcomes": dict(Counter(r["continue"] for r in rows).most_common()),
        "complete_checkpoint_file_set": sum(
            1 for r in rows if all(r["files"].values())
        ),
        "rows": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(f"population: {payload['population']}")
    print(f"outcomes: {payload['outcomes']}")
    print(f"complete checkpoint file set: {payload['complete_checkpoint_file_set']}")
    print(f"written: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
