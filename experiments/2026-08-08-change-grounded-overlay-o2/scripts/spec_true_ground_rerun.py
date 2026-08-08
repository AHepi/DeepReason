"""Re-run O1c's floating-foundation count under the SPEC-DERIVED
definition of "ground" (REQUEST.md Amendment 1/2), read-only, reusing
O1's own committed graph utilities (`weakly_connected_components`) and
corpus enumeration (`overlay_common.corpus`/`open_root`) rather than
re-implementing them — only the ground PREDICATE differs from O1's own
`o1c_floating_foundations.py`.

Spec-derived ground(a), cited by clause (see SPEC.md for the full
derivation):
- harness-spec-v1.3.md S11.3 (lambda / grounding-ratio definition):
  "fraction of accepted artifacts whose support chains bottom out in
  an EXOGENOUS ANCHOR (evidence, program check, user ruling) rather
  than pure conjecture" -- the three anchor kinds, unchanged by v1.4,
  v1.5, or v1.6 (none of the three amendments redefines Sec 11.3).
- evidence anchor: ADMISSION_SPEC.md S2 ("Evidence-tier default...
  user-supplied sources admit as evidence by default"), realized in
  the current tree as `Provenance.role == "import"`.
- user-ruling anchor: harness-spec-v1.3.md S10.6 ("Each ruling
  registers as a precedent artifact (provenance.role: user)").
- program-check anchor: harness-spec-v1.3.md S1 (Commitment.eval in
  {"program:...", "predicate:..."}) and S11.3's own "verdicts from
  program/observation evals vs. rubric" -- realized by reusing
  `rules.warrants.formally_backed` (already the harness's own
  substantive-program/predicate-passing predicate, reused rather than
  re-implemented, matching O1's own R11 convention).
- SEED role is EXCLUDED: every actual `role="seed"` construction site
  in the current tree (grepped fresh this tranche) mints either a
  S10.3 standard artifact, a S11.1 school-policy artifact, or a
  deterministically-composed output -- all three are S3 Refl-rule
  artifacts the spec itself calls "ordinary... attackable", never
  named as a S11.3 exogenous anchor. Treating them as unconditional
  ground would be an operational choice the spec does not make.
"""

import pathlib
import sys
from collections import defaultdict

O1_SCRIPTS = (
    pathlib.Path(__file__).parent.parent.parent
    / "2026-08-08-change-grounded-overlay-o1"
    / "scripts"
)
sys.path.insert(0, str(O1_SCRIPTS))
from o1c_floating_foundations import weakly_connected_components  # noqa: E402
from overlay_common import corpus, open_root  # noqa: E402

from deepreason.ontology.artifact import ProvenanceRole  # noqa: E402
from deepreason.ontology.state import Status  # noqa: E402
from deepreason.rules.warrants import formally_backed  # noqa: E402

# O1's own proxy (SPEC.md A5 of the O1 tranche), reproduced here ONLY
# for the side-by-side comparison this script prints -- not treated as
# authoritative by this script's own ground() predicate below.
O1_PROXY_GROUND_ROLES = {ProvenanceRole.SEED, ProvenanceRole.IMPORT, ProvenanceRole.USER}


def is_ground_o1_proxy(harness, aid) -> bool:
    art = harness.state.artifacts.get(aid)
    return art is not None and art.provenance.role in O1_PROXY_GROUND_ROLES


def is_ground_spec_true(harness, aid) -> bool:
    art = harness.state.artifacts.get(aid)
    if art is None:
        return False
    if art.provenance.role in (ProvenanceRole.IMPORT, ProvenanceRole.USER):
        return True
    return formally_backed(harness, aid)


def reaches_ground(harness, ground_fn, start, forward_deps) -> bool:
    seen: set = set()
    stack = [start]
    while stack:
        n = stack.pop()
        if n in seen:
            continue
        seen.add(n)
        if ground_fn(harness, n):
            return True
        stack.extend(forward_deps.get(n, ()))
    return False


def analyze_root(root, ground_fn) -> dict:
    harness = open_root(root)
    accepted = {
        aid for aid, status in harness.state.status.items() if status == Status.ACCEPTED
    }
    dep_a = {(x, y) for x, y in harness.state.dep if x in accepted and y in accepted}
    forward_deps: dict = defaultdict(list)
    for x, y in dep_a:
        forward_deps[x].append(y)
    connected_nodes = {n for edge in dep_a for n in edge}
    isolated = accepted - connected_nodes
    components = weakly_connected_components(accepted, dep_a) if dep_a else []
    components += [{n} for n in isolated]

    floating = []
    for comp in components:
        grounded_reach = any(
            reaches_ground(harness, ground_fn, member, forward_deps) for member in comp
        )
        if not grounded_reach:
            floating.append({"members": sorted(comp), "size": len(comp)})
    return {
        "root": str(root),
        "accepted_count": len(accepted),
        "component_count": len(components),
        "floating_components": floating,
    }


def main():
    roots = corpus()
    total_proxy_floating = total_spec_floating = 0
    total_proxy_chains = total_spec_chains = 0
    rows = []
    for root in roots:
        try:
            proxy = analyze_root(root, is_ground_o1_proxy)
            spec = analyze_root(root, is_ground_spec_true)
        except Exception as error:  # noqa: BLE001 - per-root failure must not kill the sweep
            rows.append(f"{root} ERROR {type(error).__name__}: {error}")
            continue
        proxy_fc = len(proxy["floating_components"])
        spec_fc = len(spec["floating_components"])
        proxy_chains = sum(1 for f in proxy["floating_components"] if f["size"] > 1)
        spec_chains = sum(1 for f in spec["floating_components"] if f["size"] > 1)
        total_proxy_floating += proxy_fc
        total_spec_floating += spec_fc
        total_proxy_chains += proxy_chains
        total_spec_chains += spec_chains
        flag = "" if proxy_fc == spec_fc else " <-- DIFFERS"
        rows.append(
            f"{root} accepted={proxy['accepted_count']} "
            f"proxy_floating={proxy_fc}(chains={proxy_chains}) "
            f"spec_floating={spec_fc}(chains={spec_chains}){flag}"
        )
    for r in rows:
        print(r)
    print(
        f"TOTAL proxy_floating={total_proxy_floating}(chains={total_proxy_chains}) "
        f"spec_floating={total_spec_floating}(chains={total_spec_chains})"
    )


if __name__ == "__main__":
    main()
