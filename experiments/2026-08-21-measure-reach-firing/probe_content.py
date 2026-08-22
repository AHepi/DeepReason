"""Control probe (READ-ONLY) for the SUB-evaluation trap:

  "A missing blob evaluates as the empty string, not as an error.
   content_text swallows KeyError and returns '', so a predicate over a
   sealed or absent artifact yields a confident `fail`."

If the candidate artifacts' bytes are unresolvable in a replayed root, then
every predicate criterion fails vacuously and the E4 column of the census
would be an artifact of the READER, not a fact about the run. This probe
measures resolvable content, so the census's 585,096 `fail` verdicts can be
attributed to content that exists.

Per root: how many candidate (ACCEPTED + addressing) artifacts resolve to
non-empty text, the length distribution, and how many contain the two
substrings `relation-form` actually tests for.
"""

import collections
import json
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
RELATION_KINDS = ("depends on", "reduces to", "shares mechanism",
                  "shared mechanism", "compatible with", "inherits",
                  "integrates", "contradicts", "abstracts")


def probe(root: pathlib.Path) -> dict:
    from deepreason.harness import Harness
    from deepreason.ontology.state import Status
    from deepreason.programs import content_text

    harness = Harness(root, read_only=True)
    state = harness.state
    addressed = {aid for aid, _pid in state.addr}
    counts = collections.Counter()
    lengths = []
    for aid, status in state.status.items():
        if status != Status.ACCEPTED or aid not in addressed:
            continue
        counts["candidates"] += 1
        text = content_text(state.artifacts[aid], harness.blobs)
        lengths.append(len(text))
        if not text:
            counts["empty_content"] += 1
            continue
        counts["nonempty_content"] += 1
        low = text.lower()
        has_refuted = "refuted if" in low
        has_kind = any(k in low for k in RELATION_KINDS)
        counts["has_refuted_if"] += has_refuted
        counts["has_relation_kind"] += has_kind
        counts["would_pass_relation_form"] += has_refuted and has_kind
    lengths.sort()
    return {
        "root": str(root.relative_to(REPO)),
        **dict(counts),
        "content_len_min": lengths[0] if lengths else None,
        "content_len_median": lengths[len(lengths) // 2] if lengths else None,
        "content_len_max": lengths[-1] if lengths else None,
    }


if __name__ == "__main__":
    args = sys.argv[1:]
    roots = (
        [REPO / a for a in args] if args
        else sorted({p.parent for p in (REPO / "experiments").rglob("log.jsonl")})
    )
    rows, totals = [], collections.Counter()
    for root in roots:
        try:
            row = probe(root)
        except Exception as error:
            row = {"root": str(root.relative_to(REPO)),
                   "open_error": f"{type(error).__name__}: {error}"}
        rows.append(row)
        for key, value in row.items():
            if isinstance(value, int) and not key.startswith("content_len"):
                totals[key] += value
        print(json.dumps(row), flush=True)
    path = pathlib.Path(__file__).with_name("probe_content.json")
    path.write_text(json.dumps(
        {"roots": rows, "totals": dict(sorted(totals.items()))}, indent=2) + "\n")
    print("\n=== TOTALS ===")
    for key, value in sorted(totals.items()):
        print(f"  {key:34} {value}")
    print(f"\nwrote {path}")
