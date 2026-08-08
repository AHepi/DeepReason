"""Block E: aggregate O1's four overlay counts and attack-edge density,
old (preserved baseline) vs new (post-sweep), from the typed
overlay_results.jsonl records only -- no model prose.

Usage: python3 block_e_diff.py OLD_JSONL NEW_JSONL
"""

import json
import sys
from pathlib import Path


def aggregate(path: Path) -> dict:
    node_count = att_edge_count = 0
    ctrl_sccs = skeptical = 0
    fb = 0
    floating = chains = 0
    flips = 0
    errors = 0
    root_count = 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        root_count += 1
        o1a, o1b, o1c, o1d = row.get("o1a", {}), row.get("o1b", {}), row.get("o1c", {}), row.get("o1d", {})
        if "_error" in o1a or "_error" in o1b or "_error" in o1c or "_error" in o1d:
            errors += 1
            continue
        node_count += o1a.get("node_count", 0)
        att_edge_count += o1a.get("att_edge_count", 0)
        ctrl_sccs += len(o1a.get("controversy_sccs", []))
        skeptical += len(o1a.get("skeptical_accepted_not_grounded", []))
        fb += o1b.get("accepted_formally_backed_count", 0)
        floating_components = o1c.get("floating_components", [])
        floating += len(floating_components)
        chains += sum(1 for f in floating_components if f.get("kind") == "chain")
        flips += sum(v for k, v in o1d.get("flip_histogram", {}).items() if k != "0")

    return {
        "root_count": root_count,
        "error_count": errors,
        "node_count": node_count,
        "att_edge_count": att_edge_count,
        "attack_edge_density": (att_edge_count / node_count) if node_count else None,
        "o1a_controversy_sccs": ctrl_sccs,
        "o1a_skeptical_accepted_not_grounded": skeptical,
        "o1b_accepted_formally_backed": fb,
        "o1c_floating_components": floating,
        "o1c_floating_chains": chains,
        "o1d_warrant_flips": flips,
    }


old_path = Path(sys.argv[1])
new_path = Path(sys.argv[2])
old = aggregate(old_path)
new = aggregate(new_path)

out = {"old": old, "new": new, "delta": {}}
for key in old:
    if isinstance(old[key], (int, float)) and old[key] is not None and new.get(key) is not None:
        out["delta"][key] = new[key] - old[key]

print(json.dumps(out, indent=2, sort_keys=True))
