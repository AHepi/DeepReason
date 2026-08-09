"""CP1-M: artifact-type breakdown + depth-0/depth-k FIRST COUNT over the
1,941 hits' artifacts (CP3/CP4 seed data). Fully offline: opens each
committed root read-only once, no live calls.

"artifact-type": Provenance.role (ProvenanceRole enum -- conjecturer,
critic, variator, synthesizer, seed, import, user, controller,
experimenter) of each hit's two artifacts.

"depth": distance, in DEPENDENCE-ref hops (Interface.refs, RefRole.
DEPENDENCE -- the same edge kind CON-run-identity/SUB-ontology name for
lineage), from the nearest artifact with no DEPENDENCE ref of its own
(a root of the derivation graph within that run -- typically SEED/IMPORT/
USER provenance, but computed structurally from the refs graph itself,
not assumed from role alone, since an artifact could lack a DEPENDENCE
ref for other reasons). depth-0 = itself has no DEPENDENCE ref out.
depth-k = k hops via DEPENDENCE refs to reach a depth-0 artifact. An
artifact whose DEPENDENCE chain does not bottom out within the root's
own artifact set (cycle or dangling ref) is recorded as `depth: None`
("unresolved"), never silently folded into depth-0.
"""
from __future__ import annotations

import json
import pathlib
import sys

REPO = pathlib.Path("/home/user/DeepReason")
TRANCHE = REPO / "experiments/2026-08-09-cp1m-stratification-retrodiction"
sys.path.insert(0, str(REPO / "src"))

from deepreason.harness import Harness  # noqa: E402
from deepreason.ontology.artifact import RefRole  # noqa: E402

rows = [json.loads(l) for l in (TRANCHE / "hits_with_claims.jsonl").read_text().splitlines()]

_harness_cache: dict[str, Harness | None] = {}
_depth_cache: dict[str, dict[str, int | None]] = {}


def get_harness(root: str) -> Harness | None:
    if root not in _harness_cache:
        try:
            _harness_cache[root] = Harness(pathlib.Path(root), read_only=True)
        except Exception:
            _harness_cache[root] = None
    return _harness_cache[root]


def compute_depths(root: str) -> dict[str, int | None]:
    if root in _depth_cache:
        return _depth_cache[root]
    h = get_harness(root)
    depths: dict[str, int | None] = {}
    if h is None:
        _depth_cache[root] = depths
        return depths

    dep_of: dict[str, list[str]] = {}
    for aid, art in h.state.artifacts.items():
        targets = [
            ref.target
            for ref in art.interface.refs
            if ref.role == RefRole.DEPENDENCE
        ]
        dep_of[aid] = targets

    def resolve(aid: str, seen: set[str]) -> int | None:
        if aid in depths:
            return depths[aid]
        if aid in seen:
            return None  # cycle
        targets = dep_of.get(aid, [])
        real_targets = [t for t in targets if t in dep_of]
        if not real_targets:
            depths[aid] = 0
            return 0
        seen = seen | {aid}
        sub = [resolve(t, seen) for t in real_targets]
        sub = [d for d in sub if d is not None]
        if not sub:
            depths[aid] = None
            return None
        depths[aid] = 1 + min(sub)
        return depths[aid]

    for aid in dep_of:
        resolve(aid, set())
    _depth_cache[root] = depths
    return depths


type_counts: dict[str, int] = {}
depth_counts: dict[str, int] = {}
per_root_unopenable = set()

for r in rows:
    h = get_harness(r["root"])
    if h is None:
        per_root_unopenable.add(r["root"])
        continue
    depths = compute_depths(r["root"])
    for which in ("artifact_a", "artifact_b"):
        aid = r[which]
        art = h.state.artifacts.get(aid)
        role = art.provenance.role.value if art is not None and art.provenance else "unknown"
        type_counts[role] = type_counts.get(role, 0) + 1
        d = depths.get(aid)
        label = "unresolved" if d is None else (f"depth-{d}" if d > 0 else "depth-0")
        depth_counts[label] = depth_counts.get(label, 0) + 1

summary = {
    "hits_total": len(rows),
    "artifacts_examined": len(rows) * 2,
    "unopenable_roots_among_hits": sorted(per_root_unopenable),
    "artifact_type_breakdown": dict(sorted(type_counts.items(), key=lambda kv: -kv[1])),
    "depth_breakdown": dict(sorted(depth_counts.items(), key=lambda kv: (kv[0] != "depth-0", kv[0]))),
}
(TRANCHE / "artifact_depth_breakdown.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
print(json.dumps(summary, indent=2, sort_keys=True))
