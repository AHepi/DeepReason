"""Synthetic guardrail check (CHECKLIST.md step 4): a 20-node undecided
component must report TOO_LARGE and never reach brute force. Run
directly; not part of pytest (tests/ stays byte-untouched, SPEC.md R5)."""

import pathlib
import sys
import time
import types

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from o1a_semantics_diff import TOO_LARGE_COMPONENT_NODES, analyze_root  # noqa: E402


def main():
    n = 20
    node_ids = [f"n{i}" for i in range(n)]
    # An odd attack cycle over all 20 nodes: every node stays "suspended"
    # under label0 (no attacker is ever in the empty grounded extension),
    # so the whole 20-node set lands in one undecided weakly-connected
    # component — exactly the case the TOO_LARGE gate exists for.
    edges = [(node_ids[i], node_ids[(i + 1) % n]) for i in range(n)]

    fake_state = types.SimpleNamespace(
        artifacts={a: None for a in node_ids}, att=edges
    )
    fake_harness = types.SimpleNamespace(state=fake_state)

    import o1a_semantics_diff as mod

    original_open_root = mod.open_root
    mod.open_root = lambda root: fake_harness
    start = time.monotonic()
    try:
        result = analyze_root(pathlib.Path("synthetic-20-node-odd-cycle"))
    finally:
        mod.open_root = original_open_root
    elapsed = time.monotonic() - start

    assert result["node_count"] == n
    assert len(result["components"]) == 1
    comp = result["components"][0]
    assert comp["nodes"] == n and comp["nodes"] > TOO_LARGE_COMPONENT_NODES
    assert comp["status"] == "TOO_LARGE"
    assert "preferred_extension_count" not in comp

    print(f"TOO_LARGE reported for component size {comp['nodes']} in {elapsed:.4f}s")
    assert elapsed < 5.0


if __name__ == "__main__":
    main()
