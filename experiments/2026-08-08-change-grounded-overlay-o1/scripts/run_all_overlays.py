"""Driver for Rung O1's four overlays (SPEC.md S10). Enumerates the
committed-root corpus once, runs O1a-O1d per root, and writes one JSON
line per root to overlay_results.jsonl — the machine-readable source
REPORT.md's own pasted commands read back from.
"""

import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import o1a_semantics_diff  # noqa: E402
import o1b_joint_execution_probe  # noqa: E402
import o1c_floating_foundations  # noqa: E402
import o1d_warrant_sensitivity  # noqa: E402
from overlay_common import corpus  # noqa: E402

OUT_PATH = pathlib.Path(__file__).parent.parent / "overlay_results.jsonl"


def _run_one(module, root):
    start = time.monotonic()
    try:
        result = module.analyze_root(root)
        result["_elapsed_s"] = round(time.monotonic() - start, 3)
        return result
    except Exception as error:  # noqa: BLE001 - a per-root, per-overlay failure is typed, not fatal
        return {
            "root": str(root),
            "_error": f"{type(error).__name__}: {error}",
            "_elapsed_s": round(time.monotonic() - start, 3),
        }


def main():
    roots = corpus()
    lines = []
    for i, root in enumerate(roots, start=1):
        row = {
            "root": str(root),
            "o1a": _run_one(o1a_semantics_diff, root),
            "o1b": _run_one(o1b_joint_execution_probe, root),
            "o1c": _run_one(o1c_floating_foundations, root),
            "o1d": _run_one(o1d_warrant_sensitivity, root),
        }
        lines.append(json.dumps(row, default=str, sort_keys=True))
        print(f"[{i}/{len(roots)}] {root} done")

    OUT_PATH.write_text("\n".join(lines) + "\n")
    print(f"SWEEP COMPLETE: {len(lines)} roots -> {OUT_PATH}")


if __name__ == "__main__":
    main()
