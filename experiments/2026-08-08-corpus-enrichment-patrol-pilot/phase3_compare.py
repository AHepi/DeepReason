"""Corpus-enrichment pilot, Phase 3: overlay re-run + old-vs-new comparison.

Runs O1's committed scripts/run_all_overlays.py UNMODIFIED (it writes to
its own tranche's overlay_results.jsonl in place -- this script copies
that output aside immediately, then restores O1's file to its committed
bytes via `git checkout`, so O1's own evidence is never disturbed).

Definitions (prereg.yaml is silent on the exact metric; recorded here as
an assumption, not a silent guess):
  - attack-edge density = sum(att_edge_count) / sum(node_count) across
    the corpus (o1a's own per-root fields).
  - cycle count = the harness's own `cycle` field in each root's
    run-status.json (the reasoning-cycle count the run actually
    consumed), NOT graph-theoretic cycles (those are already reported
    separately as o1a's controversy_sccs / o1c's component_count).

Comparisons are made on CANONICALIZED per-root summaries (counts, not
raw list order) -- a fresh run_all_overlays.py invocation is not
byte-reproducible across processes (Python's hash-randomized set
iteration order reorders list-valued fields; verified same-content,
different-order on the pre-Phase-1 baseline; see RESULTS.md).
"""

import json
import pathlib
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
TRANCHE = pathlib.Path(__file__).resolve().parent
O1_DIR = REPO / "experiments" / "2026-08-08-change-grounded-overlay-o1"
O1_SCRIPT = O1_DIR / "scripts" / "run_all_overlays.py"
O1_OUTPUT = O1_DIR / "overlay_results.jsonl"


def run_overlay_sweep(label: str) -> pathlib.Path:
    """Run O1's script unmodified, capture its output under this tranche
    as phase3/overlay_results_<label>.jsonl, then restore O1's committed
    file byte-for-byte."""
    before = subprocess.run(
        ["git", "-C", str(REPO), "status", "--short", str(O1_OUTPUT)],
        capture_output=True, text=True,
    ).stdout
    if before.strip():
        raise RuntimeError(
            f"O1's overlay_results.jsonl already has uncommitted changes -- "
            f"refusing to run (would blur what this script vs. something "
            f"else touched): {before}"
        )

    subprocess.run([sys.executable, str(O1_SCRIPT)], check=True, cwd=REPO)

    dest = TRANCHE / "phase3" / f"overlay_results_{label}.jsonl"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(O1_OUTPUT.read_text())

    subprocess.run(
        ["git", "-C", str(REPO), "checkout", "--", str(O1_OUTPUT)], check=True
    )
    restored_diff = subprocess.run(
        ["git", "-C", str(REPO), "status", "--short", str(O1_OUTPUT)],
        capture_output=True, text=True,
    ).stdout
    if restored_diff.strip():
        raise RuntimeError("O1's overlay_results.jsonl failed to restore cleanly")

    return dest


def cycle_count_for_root(root: str) -> int | None:
    status_path = pathlib.Path(root) / "run-status.json"
    if not status_path.exists():
        return None
    try:
        return json.loads(status_path.read_text()).get("cycle")
    except Exception:  # noqa: BLE001
        return None


def summarize(overlay_path: pathlib.Path) -> dict:
    nodes = 0
    edges = 0
    controversy_sccs = 0
    undecided = 0
    o1b_probes = 0
    o1c_components = 0
    o1d_rows = 0
    errors = []
    cycles = []
    root_count = 0

    for line in overlay_path.read_text().splitlines():
        row = json.loads(line)
        root_count += 1
        o1a, o1b, o1c, o1d = row.get("o1a", {}), row.get("o1b", {}), row.get("o1c", {}), row.get("o1d", {})
        for name, section in (("o1a", o1a), ("o1b", o1b), ("o1c", o1c), ("o1d", o1d)):
            if "_error" in section:
                errors.append({"root": row["root"], "overlay": name, "error": section["_error"]})

        nodes += o1a.get("node_count", 0)
        edges += o1a.get("att_edge_count", 0)
        controversy_sccs += len(o1a.get("controversy_sccs", []))
        undecided += o1a.get("undecided_count", 0)
        o1b_probes += len(o1b.get("probe_results", []))
        o1c_components += o1c.get("component_count", 0)
        if isinstance(o1d, dict) and "_error" not in o1d:
            o1d_rows += 1

        cyc = cycle_count_for_root(row["root"])
        if cyc is not None:
            cycles.append(cyc)

    return {
        "roots": root_count,
        "total_nodes": nodes,
        "total_att_edges": edges,
        "attack_edge_density": round(edges / nodes, 6) if nodes else None,
        "total_controversy_sccs": controversy_sccs,
        "total_undecided": undecided,
        "o1b_total_probe_results": o1b_probes,
        "o1c_total_floating_components": o1c_components,
        "o1d_roots_analyzed": o1d_rows,
        "mean_cycle_count": round(sum(cycles) / len(cycles), 3) if cycles else None,
        "roots_with_cycle_field": len(cycles),
        "overlay_errors": errors,
    }


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "post_enrichment"
    fresh = run_overlay_sweep(label)
    summary = summarize(fresh)
    out = TRANCHE / "phase3" / f"summary_{label}.json"
    out.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"-> {out}")


if __name__ == "__main__":
    main()
